"""Adapter-neutral bounded browser wizard engine.

The engine owns traversal rather than ATS-specific selectors. It separates safe
step navigation from final submission, fingerprints the post-fill page state,
records redacted step evidence, traverses accessible iframe scopes, retries
recoverable validation once, and fails closed at every human-only boundary.

It is intentionally synchronous because JobSniffing's Playwright adapters use
``playwright.sync_api`` and Android/Termux operation stays single-process.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Literal
from urllib.parse import urlsplit, urlunsplit

from app.adapters.submit.base import AdapterInput, AdapterOutcome
from app.adapters.submit.confirmation import detect_confirmation
from app.adapters.submit.dom_kit import QuestionSpec, count, extract_questions, normalize_text, scopes
from app.adapters.submit.handoff import detect_handoff

NavigationKind = Literal["next", "review", "final_submit", "none"]


@dataclass(frozen=True)
class WizardLimits:
    max_steps: int = 8
    max_structure_repeats: int = 2
    max_url_visits: int = 3
    validation_retries: int = 1
    settle_ms: int = 500


@dataclass(frozen=True)
class WizardConfig:
    adapter_name: str
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
    submit_selectors: tuple[str, ...] = ()
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
    form_error_keywords: tuple[str, ...] = (
        "is required", "please complete", "field is required", "required field",
    )
    limits: WizardLimits = field(default_factory=WizardLimits)


@dataclass(frozen=True)
class StepFillResult:
    questions: tuple[QuestionSpec, ...] = ()
    fill_report: tuple[dict[str, str | bool], ...] = ()
    blocked_reason: str = ""
    filled_count: int = 0


@dataclass(frozen=True)
class ActionControl:
    kind: NavigationKind
    selector: str
    locator: Any
    label: str


_SENSITIVE_QUESTION_PATTERNS: tuple[tuple[str, str], ...] = (
    ("demographic_self_identification", r"\b(gender|gender identity|race|ethnicity|veteran|disability|sexual orientation|pronouns?)\b"),
    ("legal_declaration", r"\b(i certify|i attest|legal declaration|electronic signature|type your signature|criminal (?:record|history)|conflict of interest)\b"),
    ("legal_consent", r"\b(consent to|agree to the terms|terms and conditions|privacy policy acknowledgement|background check authorization)\b"),
)


def _redact_text(value: str) -> str:
    text = str(value or "")
    text = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "[redacted-email]", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<!\w)(?:\+?\d[\d .()\-]{7,}\d)(?!\w)", "[redacted-phone]", text)
    return " ".join(text.split())[:300]


def _redacted_url(value: str) -> str:
    try:
        parts = urlsplit(str(value or ""))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except Exception:  # noqa: BLE001
        return ""


def human_only_question(question: str) -> str | None:
    normalized = normalize_text(question)
    for reason, pattern in _SENSITIVE_QUESTION_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return reason
    return None


def _safe_content(page: Any) -> str:
    try:
        return str(page.content())
    except Exception:  # noqa: BLE001
        return ""


def _safe_url(page: Any) -> str:
    try:
        return _redacted_url(str(getattr(page, "url", "") or ""))
    except Exception:  # noqa: BLE001
        return ""


def _locator_text(locator: Any) -> str:
    for reader in (
        lambda: locator.inner_text(),
        lambda: locator.get_attribute("value"),
        lambda: locator.get_attribute("aria-label"),
        lambda: locator.get_attribute("title"),
    ):
        try:
            value = str(reader() or "").strip()
            if value:
                return value
        except Exception:  # noqa: BLE001
            continue
    return ""


def _first_visible(scope: Any, selectors: Iterable[str]) -> tuple[str, Any] | None:
    for selector in selectors:
        try:
            locator = scope.locator(selector).first
            if locator.count() <= 0:
                continue
            try:
                if hasattr(locator, "is_visible") and not locator.is_visible():
                    continue
            except Exception:  # noqa: BLE001
                pass
            try:
                if hasattr(locator, "is_enabled") and not locator.is_enabled():
                    continue
            except Exception:  # noqa: BLE001
                pass
            return selector, locator
        except Exception:  # noqa: BLE001
            continue
    return None


def find_action(scope: Any, config: WizardConfig) -> ActionControl | None:
    """Find a step action without confusing navigation with final submission."""
    for kind, selectors in (
        ("next", config.next_selectors),
        ("review", config.review_selectors),
        ("final_submit", config.submit_selectors),
    ):
        found = _first_visible(scope, selectors)
        if found is None:
            continue
        selector, locator = found
        label = _locator_text(locator) or selector
        normalized = normalize_text(label)
        if kind == "final_submit" and any(term in normalized for term in ("next", "continue", "review", "save and continue")):
            return ActionControl("review" if "review" in normalized else "next", selector, locator, label)
        if kind in {"next", "review"} and any(term in normalized for term in ("submit application", "submit your application", "finish application", "send application")):
            return ActionControl("final_submit", selector, locator, label)
        return ActionControl(kind, selector, locator, label)
    return None


def validation_messages(scope: Any, selectors: Iterable[str]) -> list[str]:
    messages: list[str] = []
    for selector in selectors:
        try:
            locator = scope.locator(selector)
        except Exception:  # noqa: BLE001
            continue
        try:
            values = locator.all_inner_texts()
        except Exception:  # noqa: BLE001
            values = []
            try:
                if locator.count() > 0:
                    values = [_locator_text(locator.first)]
            except Exception:  # noqa: BLE001
                pass
        for value in values:
            text = _redact_text(str(value))
            if text and text not in messages:
                messages.append(text)
    return messages[:12]


def _scope_signature(scope: Any) -> str:
    try:
        url = str(getattr(scope, "url", "") or "")
    except Exception:  # noqa: BLE001
        url = ""
    return url


def page_fingerprint(page: Any, scope: Any, config: WizardConfig) -> str:
    """Create a value-free fingerprint after filling and before navigation."""
    questions = [
        {
            "q": normalize_text(spec.question),
            "type": spec.field_type,
            "required": spec.required,
            "options": [normalize_text(option) for option in spec.options],
        }
        for spec in extract_questions(scope)
    ]
    action = find_action(scope, config)
    payload = {
        "url": _safe_url(page),
        "scope": _scope_signature(scope),
        "questions": questions,
        "controls": {
            "input": count(scope, "input"),
            "textarea": count(scope, "textarea"),
            "select": count(scope, "select"),
            "button": count(scope, "button"),
        },
        "action": {
            "kind": action.kind if action else "none",
            "label": normalize_text(action.label) if action else "",
        },
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:20]


def _take_shot(page: Any, directory: Path | None, label: str, screenshots: list[str]) -> None:
    if directory is None:
        return
    redacted_scopes: list[Any] = []
    redaction_script = """() => {
      if (document.getElementById('jobsniffing-redaction-style')) return;
      const style = document.createElement('style');
      style.id = 'jobsniffing-redaction-style';
      style.textContent = `
        input:not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit]),
        textarea, [contenteditable=true] {
          color: transparent !important;
          text-shadow: 0 0 9px #111 !important;
          caret-color: transparent !important;
        }
        input[type=file] { font-size: 0 !important; }
      `;
      document.documentElement.appendChild(style);
    }"""
    try:
        for scope in scopes(page):
            try:
                scope.evaluate(redaction_script)
                redacted_scopes.append(scope)
            except Exception:  # noqa: BLE001
                continue
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{len(screenshots) + 1:02d}-{label}.png"
        page.screenshot(path=str(path), full_page=True)
        screenshots.append(str(path))
    except Exception:  # noqa: BLE001
        pass
    finally:
        for scope in redacted_scopes:
            try:
                scope.evaluate("() => document.getElementById('jobsniffing-redaction-style')?.remove()")
            except Exception:  # noqa: BLE001
                pass


def _redacted_step(
    *,
    step: int,
    url: str,
    fingerprint: str,
    fill: StepFillResult,
    action: ActionControl | None,
    validation: list[str] | None = None,
    event: str = "filled",
) -> dict:
    return {
        "step": step,
        "event": event,
        "url": _redacted_url(url),
        "fingerprint": fingerprint,
        "questions": [
            {
                "question": spec.question,
                "field_type": spec.field_type,
                "required": spec.required,
                "options": list(spec.options),
            }
            for spec in fill.questions
        ],
        "filled_count": fill.filled_count,
        "fill_results": [
            {
                "question": str(item.get("question", "")),
                "field_type": str(item.get("field_type", "unknown")),
                "success": bool(item.get("success", False)),
            }
            for item in fill.fill_report
        ],
        "action": {
            "kind": action.kind if action else "none",
            "label": action.label[:160] if action else "",
            "selector": action.selector[:200] if action else "",
        },
        "validation": list(validation or []),
    }


def _evidence(journal: list[dict], all_questions: dict[str, dict], fill_reports: list[dict]) -> list[tuple[str, str]]:
    return [
        ("extracted_questions", json.dumps(list(all_questions.values()), ensure_ascii=False, sort_keys=True)),
        ("field_fill_report", json.dumps([
            {
                "step": item.get("step"),
                "question": item.get("question", ""),
                "field_type": item.get("field_type", "unknown"),
                "success": bool(item.get("success", False)),
            }
            for item in fill_reports
        ], ensure_ascii=False, sort_keys=True)),
        ("wizard_journal", json.dumps(journal, ensure_ascii=False, sort_keys=True)),
    ]


def run_wizard(
    page: Any,
    ctx: AdapterInput,
    config: WizardConfig,
    *,
    locate_scope: Callable[[], Any | None],
    fill_step: Callable[[Any, int], StepFillResult],
    screenshots_dir: Path | None = None,
) -> AdapterOutcome:
    """Traverse a bounded ATS wizard and stop safely at uncertain boundaries."""
    screenshots: list[str] = []
    journal: list[dict] = []
    all_questions: dict[str, dict] = {}
    fill_reports: list[dict] = []
    fingerprint_visits: Counter[str] = Counter()
    url_visits: Counter[str] = Counter()
    limits = config.limits
    before_content = _safe_content(page)
    before_url = _safe_url(page)

    for step in range(1, limits.max_steps + 1):
        page_content = _safe_content(page)
        handoff = detect_handoff(page_content)
        if handoff:
            _take_shot(page, screenshots_dir, f"step-{step}-{handoff.kind}", screenshots)
            evidence = _evidence(journal, all_questions, fill_reports)
            evidence.append(("handoff_reason", json.dumps(handoff.__dict__, sort_keys=True)))
            return AdapterOutcome(
                "manual_intervention",
                f"{handoff.reason} (matched {handoff.keyword!r})",
                evidence=evidence,
                screenshots=screenshots,
            )

        scope = locate_scope()
        if scope is None:
            _take_shot(page, screenshots_dir, f"step-{step}-no-form", screenshots)
            return AdapterOutcome(
                "manual_intervention",
                f"could not locate an accessible {config.adapter_name} application step",
                evidence=_evidence(journal, all_questions, fill_reports),
                screenshots=screenshots,
            )

        fill = fill_step(scope, step)
        for spec in fill.questions:
            key = normalize_text(spec.question)
            if key:
                all_questions[key] = spec.to_dict()
        fill_reports.extend(dict(item, step=step) for item in fill.fill_report)
        action = find_action(scope, config)
        fingerprint = page_fingerprint(page, scope, config)
        fingerprint_visits[fingerprint] += 1
        current_url = _safe_url(page)
        url_visits[current_url] += 1
        journal.append(
            _redacted_step(
                step=step,
                url=current_url,
                fingerprint=fingerprint,
                fill=fill,
                action=action,
            )
        )
        _take_shot(page, screenshots_dir, f"step-{step}-filled", screenshots)

        if fill.blocked_reason:
            return AdapterOutcome(
                "manual_intervention",
                fill.blocked_reason,
                evidence=_evidence(journal, all_questions, fill_reports),
                screenshots=screenshots,
            )

        handoff = detect_handoff(_safe_content(page))
        if handoff:
            _take_shot(page, screenshots_dir, f"step-{step}-post-fill-{handoff.kind}", screenshots)
            evidence = _evidence(journal, all_questions, fill_reports)
            evidence.append(("handoff_reason", json.dumps(handoff.__dict__, sort_keys=True)))
            return AdapterOutcome(
                "manual_intervention",
                f"{handoff.reason} after safe field filling (matched {handoff.keyword!r})",
                evidence=evidence,
                screenshots=screenshots,
            )

        if fingerprint_visits[fingerprint] > limits.max_structure_repeats:
            return AdapterOutcome(
                "manual_intervention",
                "wizard structure loop detected; the same redacted step fingerprint repeated",
                evidence=_evidence(journal, all_questions, fill_reports),
                screenshots=screenshots,
            )
        if current_url and url_visits[current_url] > limits.max_url_visits:
            return AdapterOutcome(
                "manual_intervention",
                "wizard URL loop detected; the same application URL repeated too many times",
                evidence=_evidence(journal, all_questions, fill_reports),
                screenshots=screenshots,
            )

        if action is None:
            return AdapterOutcome(
                "manual_intervention",
                "no safe Next, Review, or final Submit control was found",
                evidence=_evidence(journal, all_questions, fill_reports),
                screenshots=screenshots,
            )

        if action.kind == "final_submit":
            evidence = _evidence(journal, all_questions, fill_reports)
            if not ctx.live:
                evidence.append(("dry_run", "submit button intentionally not clicked"))
                return AdapterOutcome(
                    "manual_intervention",
                    f"dry-run preview completed through {step} wizard step(s): final submit was not clicked",
                    evidence=evidence,
                    screenshots=screenshots,
                )

            try:
                action.locator.click()
            except Exception as exc:  # noqa: BLE001
                return AdapterOutcome(
                    "manual_intervention",
                    f"final submit control could not be activated safely: {exc}",
                    evidence=evidence,
                    screenshots=screenshots,
                )
            try:
                page.wait_for_timeout(1800)
            except Exception:  # noqa: BLE001
                pass
            after_content = _safe_content(page)
            after_url = _safe_url(page)
            _take_shot(page, screenshots_dir, "after-submit", screenshots)
            handoff = detect_handoff(after_content)
            if handoff:
                evidence.append(("handoff_reason", json.dumps(handoff.__dict__, sort_keys=True)))
                return AdapterOutcome(
                    "manual_intervention",
                    f"{handoff.reason} after submit (matched {handoff.keyword!r})",
                    evidence=evidence,
                    screenshots=screenshots,
                )
            after_scope = locate_scope()
            confirmation = detect_confirmation(
                before_content=before_content,
                after_content=after_content,
                before_url=before_url,
                after_url=after_url,
                form_present_before=True,
                form_present_after=after_scope is not None,
            )
            if confirmation.confirmed:
                return AdapterOutcome(
                    "submitted",
                    confirmation.reason,
                    evidence=evidence + confirmation.evidence,
                    screenshots=screenshots,
                )
            lowered = after_content.casefold()
            post_errors: list[str] = []
            if after_scope is not None:
                post_errors = validation_messages(after_scope, config.validation_selectors)
            if post_errors or any(keyword in lowered for keyword in config.form_error_keywords):
                return AdapterOutcome(
                    "manual_intervention",
                    "the final form reported required or invalid fields the adapter could not safely resolve",
                    evidence=evidence + [("validation_errors", json.dumps(post_errors, ensure_ascii=False))],
                    screenshots=screenshots,
                )
            detail = confirmation.reason
            if confirmation.weak_signals:
                detail += "; weak signals: " + "; ".join(confirmation.weak_signals)
            return AdapterOutcome("awaiting_confirmation", detail, evidence=evidence, screenshots=screenshots)

        before_nav_fingerprint = fingerprint
        retry = 0
        while True:
            try:
                action.locator.click()
            except Exception as exc:  # noqa: BLE001
                return AdapterOutcome(
                    "manual_intervention",
                    f"wizard {action.kind} control could not be activated safely: {exc}",
                    evidence=_evidence(journal, all_questions, fill_reports),
                    screenshots=screenshots,
                )
            try:
                page.wait_for_timeout(limits.settle_ms)
            except Exception:  # noqa: BLE001
                pass
            next_scope = locate_scope()
            if next_scope is None:
                break
            errors = validation_messages(next_scope, config.validation_selectors)
            if not errors:
                break
            if retry >= limits.validation_retries:
                journal.append(
                    _redacted_step(
                        step=step,
                        url=_safe_url(page),
                        fingerprint=page_fingerprint(page, next_scope, config),
                        fill=fill,
                        action=action,
                        validation=errors,
                        event="validation_blocked",
                    )
                )
                return AdapterOutcome(
                    "manual_intervention",
                    "wizard validation remained after the bounded recovery attempt",
                    evidence=_evidence(journal, all_questions, fill_reports)
                    + [("validation_errors", json.dumps(errors, ensure_ascii=False))],
                    screenshots=screenshots,
                )
            retry += 1
            recovery = fill_step(next_scope, step)
            if recovery.blocked_reason:
                return AdapterOutcome(
                    "manual_intervention",
                    recovery.blocked_reason,
                    evidence=_evidence(journal, all_questions, fill_reports)
                    + [("validation_errors", json.dumps(errors, ensure_ascii=False))],
                    screenshots=screenshots,
                )
            action = find_action(next_scope, config) or action

        _take_shot(page, screenshots_dir, f"step-{step}-after-{action.kind}", screenshots)
        next_scope = locate_scope()
        if next_scope is not None:
            after_nav_fingerprint = page_fingerprint(page, next_scope, config)
            if after_nav_fingerprint == before_nav_fingerprint:
                journal.append(
                    {
                        "step": step,
                        "event": "navigation_no_structure_change",
                        "url": _safe_url(page),
                        "fingerprint": after_nav_fingerprint,
                        "action": {"kind": action.kind, "label": action.label[:160]},
                    }
                )
        continue

    return AdapterOutcome(
        "manual_intervention",
        f"wizard step limit reached after {limits.max_steps} steps",
        evidence=_evidence(journal, all_questions, fill_reports),
        screenshots=screenshots,
    )
