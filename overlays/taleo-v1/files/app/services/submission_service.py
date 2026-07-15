"""Submission orchestrator.

Single entry point that enforces, in order: allowed starting status, the full
gate report (with an explicit, narrow force-bypass), adapter execution, and
evidence-checked state transitions. Every run is written to run_logs.
"""
from __future__ import annotations

import json
import sqlite3

from app.adapters.submit.ashby_playwright import AshbyPlaywrightAdapter
from app.adapters.submit.base import AdapterInput
from app.adapters.submit.email_smtp import EmailSmtpAdapter
from app.adapters.submit.greenhouse_playwright import GreenhousePlaywrightAdapter
from app.adapters.submit.lever_playwright import LeverPlaywrightAdapter
from app.adapters.submit.taleo_playwright import TaleoPlaywrightAdapter
from app.domain.enums import ApplicationStatus as S
from app.services import gates
from app.services.document_service import COVER_KIND, ensure_variant_pdf, latest_document
from app.services.evidence_service import add_evidence, has_confirmation_evidence
from app.services.profile_service import get_field, resolve_for_automation
from app.services.question_engine import list_answers, prepare_answers
from app.services.tracking_service import change_status, get_job, log_run

ADAPTERS = {
    adapter.name: adapter
    for adapter in (
        EmailSmtpAdapter(),
        GreenhousePlaywrightAdapter(),
        LeverPlaywrightAdapter(),
        AshbyPlaywrightAdapter(),
        TaleoPlaywrightAdapter(),
    )
}
INSPECTABLE_ADAPTERS = {"greenhouse", "lever", "ashby", "taleo"}

# `force=True` represents an explicit human request for this specific job.
# It may bypass autonomy policy gates only, never evidence, factuality,
# duplicate, cap, or delay protections.
BYPASSABLE_GATES = {"mode_autonomous", "autonomy_scope", "score_threshold"}


def resolve_contact(conn: sqlite3.Connection) -> dict[str, str]:
    contact: dict[str, str] = {}
    name_field = get_field(conn, "preferred_name") or get_field(conn, "legal_name")
    if name_field:
        contact["name"] = str(name_field["value"])
    for key in ("email", "phone", "location"):
        value, _ = resolve_for_automation(conn, key, context="application")
        if value:
            contact[key] = value
    return contact


def _build_context(
    conn: sqlite3.Connection,
    job: sqlite3.Row,
    *,
    live: bool,
    to_email: str | None = None,
) -> AdapterInput:
    cover = latest_document(conn, int(job["id"]), COVER_KIND)
    return AdapterInput(
        job=dict(job),
        contact=resolve_contact(conn),
        answers=[dict(row) for row in list_answers(conn, int(job["id"]))],
        resume_pdf=ensure_variant_pdf(conn, int(job["id"])),
        cover_letter=str(cover["content"]) if cover else "",
        to_email=to_email,
        live=live,
    )


def _store_outcome_evidence(
    conn: sqlite3.Connection, job_id: int, outcome
) -> tuple[int, list[dict]]:
    extracted: list[dict] = []
    count = 0
    for kind, content in outcome.evidence:
        add_evidence(conn, job_id, kind, content)
        count += 1
        if kind == "extracted_questions":
            try:
                payload = json.loads(content)
                if isinstance(payload, list):
                    extracted = [item for item in payload if isinstance(item, dict) and item.get("question")]
            except json.JSONDecodeError:
                pass
    for path in outcome.screenshots:
        add_evidence(conn, job_id, "screenshot", path=path)
        count += 1
    return count, extracted


def inspect_application(
    conn: sqlite3.Connection,
    job_id: int,
    adapter_name: str = "greenhouse",
) -> dict:
    """Run a browser adapter in fill-without-submit mode and prepare discovered questions."""
    job = get_job(conn, job_id)
    if job is None:
        raise KeyError(f"Unknown job id {job_id}")
    if adapter_name not in INSPECTABLE_ADAPTERS:
        raise ValueError(f"Inspection adapter must be one of {sorted(INSPECTABLE_ADAPTERS)}")
    current = S(job["status"])
    allowed = {S.DOCUMENTS_PREPARED, S.ANSWERS_PREPARED, S.READY_FOR_REVIEW, S.NEEDS_REVIEW, S.APPROVED, S.QUEUED}
    if current not in allowed:
        raise ValueError(
            f"Inspection requires documents_prepared or a later review status; job {job_id} is '{current.value}'"
        )

    outcome = ADAPTERS[adapter_name].run(_build_context(conn, job, live=False))
    evidence_count, extracted = _store_outcome_evidence(conn, job_id, outcome)
    counts = {"total": 0, "safe_auto": 0, "adapter_rule": 0, "requires_review": 0}
    if extracted:
        counts = prepare_answers(conn, job_id, [str(item["question"]) for item in extracted])
    if current is S.DOCUMENTS_PREPARED and any(kind == "extracted_questions" for kind, _ in outcome.evidence):
        target = S.ANSWERS_PREPARED if counts["requires_review"] == 0 else S.NEEDS_REVIEW
        change_status(conn, job_id, target, notes="browser inspection extracted application questions")

    final = get_job(conn, job_id)
    log_run(
        conn, "inspection",
        f"job {job_id}: adapter={adapter_name} extracted={len(extracted)} result={outcome.result}",
    )
    return {
        "executed": True,
        "adapter": adapter_name,
        "result": outcome.result,
        "message": outcome.message,
        "status": str(final["status"]),
        "questions_extracted": len(extracted),
        "answer_counts": counts,
        "evidence_added": evidence_count,
    }


def run_submission(
    conn: sqlite3.Connection,
    job_id: int,
    adapter_name: str,
    *,
    live: bool = False,
    to_email: str | None = None,
    force: bool = False,
) -> dict:
    job = get_job(conn, job_id)
    if job is None:
        raise KeyError(f"Unknown job id {job_id}")
    if adapter_name not in ADAPTERS:
        raise ValueError(f"Unknown adapter '{adapter_name}'. Available: {sorted(ADAPTERS)}")
    current = S(job["status"])
    if current not in {S.APPROVED, S.QUEUED}:
        raise ValueError(
            f"Submission requires status 'approved' or 'queued'; job {job_id} is '{current.value}'"
        )

    report = gates.evaluate(conn, job)
    blocking = [
        check.name for check in report.checks
        if not check.passed and not (force and check.name in BYPASSABLE_GATES)
    ]
    if blocking:
        log_run(conn, "submission", f"job {job_id}: blocked by gates {blocking}")
        return {"executed": False, "blocking_gates": blocking, "gates": report.to_dict(), "status": current.value}

    if current is S.APPROVED:
        change_status(conn, job_id, S.QUEUED, notes="queued for submission")
    change_status(conn, job_id, S.FILLING, notes=f"adapter '{adapter_name}' started (live={live}, force={force})")

    outcome = ADAPTERS[adapter_name].run(
        _build_context(conn, job, live=live, to_email=to_email)
    )

    evidence_count, _ = _store_outcome_evidence(conn, job_id, outcome)

    if outcome.result == "submitted":
        change_status(conn, job_id, S.AWAITING_CONFIRMATION, notes=outcome.message)
        if has_confirmation_evidence(conn, job_id):
            change_status(conn, job_id, S.SUBMITTED, notes=outcome.message)
        else:
            change_status(
                conn, job_id, S.VERIFICATION_FAILED,
                notes="adapter reported success without confirmation evidence; treat as unverified",
            )
    elif outcome.result == "awaiting_confirmation":
        change_status(conn, job_id, S.AWAITING_CONFIRMATION, notes=outcome.message)
    elif outcome.result == "manual_intervention":
        change_status(conn, job_id, S.MANUAL_INTERVENTION_REQUIRED, notes=outcome.message)
    else:
        change_status(conn, job_id, S.FAILED, notes=outcome.message)

    final = get_job(conn, job_id)
    log_run(conn, "submission", f"job {job_id}: adapter={adapter_name} result={outcome.result} status={final['status']}")
    return {
        "executed": True,
        "result": outcome.result,
        "message": outcome.message,
        "status": str(final["status"]),
        "evidence_added": evidence_count,
        "gates": report.to_dict(),
    }
