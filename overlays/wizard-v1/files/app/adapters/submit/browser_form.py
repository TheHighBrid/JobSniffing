"""Reusable ATS browser form runner.

The original single-page runner now delegates traversal to the shared bounded
wizard engine. Existing Greenhouse, Lever, and Ashby adapters keep their small
selector configs while gaining multi-step navigation, iframe traversal,
validation recovery, redacted journals, and strict final-submit separation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.adapters.submit.base import AdapterInput, AdapterOutcome
from app.adapters.submit.dom_kit import count, extract_questions, fill_answer, normalize_text, scopes, try_fill
from app.adapters.submit.wizard import StepFillResult, WizardConfig, human_only_question, run_wizard


@dataclass(frozen=True)
class SinglePageFormConfig:
    adapter_name: str
    email_selectors: tuple[str, ...]
    resume_selectors: tuple[str, ...]
    submit_selectors: tuple[str, ...]
    first_name_selectors: tuple[str, ...] = ()
    last_name_selectors: tuple[str, ...] = ()
    full_name_selectors: tuple[str, ...] = ()
    phone_selectors: tuple[str, ...] = ()
    cover_selectors: tuple[str, ...] = ()
    next_selectors: tuple[str, ...] = (
        "button:has-text('Next')",
        "button:has-text('Continue')",
        "button:has-text('Save and continue')",
        "button:has-text('Save & Continue')",
        "input[type='button'][value*='Next' i]",
        "input[type='button'][value*='Continue' i]",
        "[data-testid*='next' i]",
        "[data-qa*='next' i]",
    )
    review_selectors: tuple[str, ...] = (
        "button:has-text('Review')",
        "button:has-text('Review application')",
        "button:has-text('Continue to review')",
        "[data-testid*='review' i]",
        "[data-qa*='review' i]",
    )
    validation_selectors: tuple[str, ...] = (
        "[aria-invalid='true']",
        "[role='alert']",
        ".field-error",
        ".error-message",
        ".validation-error",
        ".application-field-error",
        "[data-testid*='error' i]",
        "[data-qa*='error' i]",
    )
    standard_label_terms: tuple[str, ...] = (
        "first name", "last name", "full name", "email", "phone", "telephone",
        "resume", "cover letter", "upload", "linkedin profile", "website",
    )
    form_error_keywords: tuple[str, ...] = (
        "is required", "please complete", "field is required", "required field",
    )


def resume_selector(scope: Any, selectors: tuple[str, ...]) -> str | None:
    for selector in selectors:
        if count(scope, selector) > 0:
            return selector
    if count(scope, "input[type='file']") == 1:
        return "input[type='file']"
    return None


def _has_any_action(scope: Any, config: SinglePageFormConfig) -> bool:
    return any(
        count(scope, selector) > 0
        for selector in config.next_selectors + config.review_selectors + config.submit_selectors
    )


def find_form_scope(page: Any, config: SinglePageFormConfig) -> Any | None:
    candidates = scopes(page)
    # Prefer the first-page signature because it avoids unrelated navigation or
    # cookie frames when several scopes are present.
    for scope in candidates:
        if any(count(scope, selector) for selector in config.email_selectors) and resume_selector(scope, config.resume_selectors):
            return scope
    # Later wizard pages frequently contain only custom questions and a Next or
    # Review control. Accessible labels plus a known action are sufficient.
    for scope in candidates:
        try:
            if extract_questions(scope) and _has_any_action(scope, config):
                return scope
        except Exception:  # noqa: BLE001
            continue
    for scope in candidates:
        if _has_any_action(scope, config):
            return scope
    return None


def prepared_answers(ctx: AdapterInput) -> tuple[list[dict], list[str]]:
    usable: list[dict] = []
    blocked: list[str] = []
    for row in ctx.answers:
        question = str(row.get("question", "")).strip()
        answer = str(row.get("answer", "")).strip()
        classification = str(row.get("classification", ""))
        approved = bool(row.get("approved", 0))
        if not question:
            continue
        if not answer:
            blocked.append(f"{question}: no approved answer")
            continue
        if classification == "requires_review" and not approved:
            blocked.append(f"{question}: still requires human approval")
            continue
        usable.append(row)
    return usable, blocked


def answer_matches_question(answer_row: dict, question: str) -> bool:
    prepared = normalize_text(str(answer_row.get("question", "")))
    target = normalize_text(question)
    return bool(prepared and target and (prepared == target or prepared in target or target in prepared))


def is_standard_question(question: str, config: SinglePageFormConfig) -> bool:
    normalized = normalize_text(question)
    return any(term in normalized for term in config.standard_label_terms)


def _fill_scope(scope: Any, step: int, ctx: AdapterInput, config: SinglePageFormConfig) -> StepFillResult:
    name = ctx.contact.get("name", "").strip()
    first, _, last = name.partition(" ")
    filled_count = 0
    for selectors, value in (
        (config.full_name_selectors, name),
        (config.first_name_selectors, first),
        (config.last_name_selectors, last or first),
        (config.phone_selectors, ctx.contact.get("phone", "")),
        (config.cover_selectors, ctx.cover_letter),
    ):
        if try_fill(scope, selectors, value):
            filled_count += 1

    email_present = any(count(scope, selector) > 0 for selector in config.email_selectors)
    if email_present:
        email = ctx.contact.get("email", "").strip()
        if not email or not try_fill(scope, config.email_selectors, email):
            return StepFillResult(blocked_reason="email address is unknown or the email field could not be filled")
        filled_count += 1

    # The resume is required on the first application surface but may not be
    # present on later pages. Upload exactly where the control exists.
    selector = resume_selector(scope, config.resume_selectors)
    if selector:
        if not ctx.resume_pdf:
            return StepFillResult(blocked_reason="resume PDF is missing; prepare documents first")
        try:
            scope.locator(selector).first.set_input_files(str(ctx.resume_pdf))
            filled_count += 1
        except Exception as exc:  # noqa: BLE001
            return StepFillResult(blocked_reason=f"could not attach resume: {exc}")

    extracted = tuple(
        spec for spec in extract_questions(scope)
        if not is_standard_question(spec.question, config)
    )

    for spec in extracted:
        boundary = human_only_question(spec.question)
        if boundary:
            return StepFillResult(
                questions=extracted,
                blocked_reason=(
                    f"human attestation required for '{spec.question}' ({boundary}); "
                    "the wizard will not answer or skip this boundary autonomously"
                ),
                filled_count=filled_count,
            )

    usable_answers, blocked_answers = prepared_answers(ctx)
    relevant_blocked = [
        item for item in blocked_answers
        if any(normalize_text(item.split(":", 1)[0]) in normalize_text(spec.question) for spec in extracted)
    ]
    if relevant_blocked:
        return StepFillResult(
            questions=extracted,
            blocked_reason="prepared answers are incomplete or still require approval: " + "; ".join(relevant_blocked[:5]),
            filled_count=filled_count,
        )

    unanswered = [
        spec.question for spec in extracted
        if not any(answer_matches_question(row, spec.question) for row in usable_answers)
    ]
    if unanswered:
        return StepFillResult(
            questions=extracted,
            blocked_reason=(
                f"inspection discovered {len(unanswered)} unanswered application question(s); "
                "prepare or approve them before continuing"
            ),
            filled_count=filled_count,
        )

    fill_report: list[dict[str, str | bool]] = []
    unresolved: list[str] = []
    for spec in extracted:
        row = next((candidate for candidate in usable_answers if answer_matches_question(candidate, spec.question)), None)
        if row is None:
            continue
        result = fill_answer(scope, spec.question, str(row["answer"]))
        fill_report.append(
            {
                "question": spec.question,
                "field_type": result.field_type,
                "success": result.success,
                "detail": result.detail,
            }
        )
        if result.success:
            filled_count += 1
        else:
            unresolved.append(spec.question)

    if unresolved:
        return StepFillResult(
            questions=extracted,
            fill_report=tuple(fill_report),
            blocked_reason="could not safely map prepared answers to these form fields: " + "; ".join(unresolved[:8]),
            filled_count=filled_count,
        )

    return StepFillResult(
        questions=extracted,
        fill_report=tuple(fill_report),
        filled_count=filled_count,
    )


def run_single_page_form(
    page: Any,
    ctx: AdapterInput,
    config: SinglePageFormConfig,
    shots_dir: Path | None = None,
) -> AdapterOutcome:
    """Backward-compatible entry point powered by the shared wizard engine."""
    wizard_config = WizardConfig(
        adapter_name=config.adapter_name,
        next_selectors=config.next_selectors,
        review_selectors=config.review_selectors,
        submit_selectors=config.submit_selectors,
        validation_selectors=config.validation_selectors,
        form_error_keywords=config.form_error_keywords,
    )
    return run_wizard(
        page,
        ctx,
        wizard_config,
        locate_scope=lambda: find_form_scope(page, config),
        fill_step=lambda scope, step: _fill_scope(scope, step, ctx, config),
        screenshots_dir=shots_dir,
    )
