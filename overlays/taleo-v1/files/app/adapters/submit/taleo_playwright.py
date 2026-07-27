"""Oracle Taleo browser adapter built on JobSniffing's shared wizard.

Taleo commonly places a job detail page, an Apply Online action, an optional
candidate-login wall, and the actual application wizard in separate surfaces.
This module owns only that bounded preflight. Once an application form is
reachable, all traversal, validation, question extraction, screenshots,
submission separation, and confirmation evidence are delegated to
``browser_form.run_single_page_form``.

Existing-account credentials are resolved exclusively through
``credential_service``. Account creation, CAPTCHA, MFA, assessments, legal
attestation, demographic self-identification, and unknown required questions
always remain human boundaries.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from app.adapters.submit.base import LIVE_ENV_FLAG, AdapterInput, AdapterOutcome
from app.adapters.submit.browser_form import SinglePageFormConfig, find_form_scope, run_single_page_form
from app.adapters.submit.dom_kit import first_present, scopes, try_fill
from app.adapters.submit.handoff import detect_handoff, visible_text
from app.config import resolve_project_path
from app.services.credential_service import CredentialError, CredentialResolution, resolve_job_credentials

_TALEO_PATH_MARKERS = (
    "/careersection/",
    "/ats/careers/",
    "jobdetail.ftl",
    "application.ftl",
    "login.jsf",
    "viewrequisition",
)

CONFIG = SinglePageFormConfig(
    adapter_name="Taleo",
    email_selectors=(
        "input[name='email']",
        "input[name*='email' i]",
        "input[id*='email' i]",
        "input[type='email']",
        "input[autocomplete='email']",
    ),
    full_name_selectors=(
        "input[name='name']",
        "input[name*='fullName' i]",
        "input[id*='fullName' i]",
        "input[autocomplete='name']",
    ),
    first_name_selectors=(
        "input[name*='firstName' i]",
        "input[name*='first_name' i]",
        "input[id*='firstName' i]",
        "input[id*='first_name' i]",
        "input[autocomplete='given-name']",
    ),
    last_name_selectors=(
        "input[name*='lastName' i]",
        "input[name*='last_name' i]",
        "input[id*='lastName' i]",
        "input[id*='last_name' i]",
        "input[autocomplete='family-name']",
    ),
    phone_selectors=(
        "input[name*='phone' i]",
        "input[id*='phone' i]",
        "input[type='tel']",
        "input[autocomplete='tel']",
    ),
    resume_selectors=(
        "input[type='file'][name*='resume' i]",
        "input[type='file'][id*='resume' i]",
        "input[type='file'][name*='attach' i]",
        "input[type='file'][id*='attach' i]",
        "input[type='file'][aria-label*='resume' i]",
        "input[type='file'][aria-label*='cv' i]",
    ),
    cover_selectors=(
        "textarea[name*='cover' i]",
        "textarea[id*='cover' i]",
        "textarea[aria-label*='cover letter' i]",
    ),
    next_selectors=(
        "button:has-text('Next')",
        "button:has-text('Continue')",
        "button:has-text('Save and Continue')",
        "button:has-text('Save & Continue')",
        "input[type='button'][value*='Next' i]",
        "input[type='button'][value*='Continue' i]",
        "input[type='submit'][value*='Next' i]",
        "input[type='submit'][value*='Continue' i]",
        "input[type='submit'][value*='Save and Continue' i]",
        "input[type='submit'][value*='Save & Continue' i]",
        "button[name*='next' i]",
        "input[name*='next' i]",
        "button[id*='next' i]",
        "input[id*='next' i]",
        "[data-testid*='next' i]",
        "[data-qa*='next' i]",
    ),
    review_selectors=(
        "button:has-text('Review')",
        "button:has-text('Review application')",
        "button:has-text('Review and Submit')",
        "button:has-text('Continue to review')",
        "input[type='submit'][value*='Review' i]",
        "input[type='button'][value*='Review' i]",
        "button[name*='review' i]",
        "input[name*='review' i]",
        "button[id*='review' i]",
        "input[id*='review' i]",
        "[data-testid*='review' i]",
        "[data-qa*='review' i]",
    ),
    submit_selectors=(
        "button:has-text('Submit Application')",
        "button:has-text('Submit application')",
        "button:has-text('Submit')",
        "input[type='submit'][value='Submit']",
        "input[type='submit'][value*='Submit Application' i]",
        "button[name*='submit' i]",
        "input[name*='submit' i]",
        "button[id*='submit' i]",
        "input[id*='submit' i]",
        "[data-testid*='submit' i]",
        "[data-qa*='submit' i]",
    ),
    validation_selectors=(
        "[aria-invalid='true']",
        "[role='alert']",
        ".error",
        ".errorMessage",
        ".validation-error",
        ".field-error",
        "[id*='error' i]",
        "[class*='error' i]",
    ),
)

_APPLY_SELECTORS = (
    "a:has-text('Apply Online')",
    "button:has-text('Apply Online')",
    "input[type='button'][value*='Apply Online' i]",
    "input[type='submit'][value*='Apply Online' i]",
    "a:has-text('Apply for this job')",
    "button:has-text('Apply for this job')",
    "a[title*='Apply Online' i]",
    "[data-testid*='apply' i]",
)
_USERNAME_SELECTORS = (
    "input[name='username']",
    "input[name*='userName' i]",
    "input[name*='login' i]",
    "input[id*='username' i]",
    "input[id*='login' i]",
    "input[type='email']",
    "input[autocomplete='username']",
)
_PASSWORD_SELECTORS = (
    "input[type='password']",
    "input[name*='password' i]",
    "input[id*='password' i]",
    "input[autocomplete='current-password']",
)
_LOGIN_SUBMIT_SELECTORS = (
    "button:has-text('Sign In')",
    "button:has-text('Log In')",
    "button:has-text('Login')",
    "input[type='submit'][value*='Sign In' i]",
    "input[type='submit'][value*='Log In' i]",
    "input[type='submit'][value*='Login' i]",
    "button[type='submit']",
)
_LOGIN_ERROR_SELECTORS = (
    "[role='alert']",
    ".error",
    ".errorMessage",
    "[id*='error' i]",
    "[class*='error' i]",
)
_CREATE_ACCOUNT_PHRASES = (
    "create an account to apply",
    "create your candidate account",
    "new candidate registration",
    "register as a new candidate",
)


@dataclass(frozen=True)
class TaleoPreflight:
    outcome: AdapterOutcome | None = None
    evidence: tuple[tuple[str, str], ...] = ()


def _host_is_taleo(host: str) -> bool:
    value = (host or "").lower().split(":", 1)[0]
    return value == "taleo.net" or value.endswith(".taleo.net")


def is_taleo_url(url: str) -> bool:
    """Recognize Taleo-hosted career URLs without accepting generic Oracle URLs."""
    parsed = urlparse(str(url or ""))
    if not _host_is_taleo(parsed.hostname or ""):
        return False
    path = (parsed.path or "").lower()
    return any(marker in path for marker in _TALEO_PATH_MARKERS)


def _scope_url(scope: Any) -> str:
    try:
        return str(getattr(scope, "url", "") or "")
    except Exception:  # noqa: BLE001
        return ""


def is_taleo_page(page: Any, url: str = "") -> bool:
    """Recognize direct, framed, or explicitly linked Taleo application surfaces."""
    candidates = [url, _scope_url(page), *(_scope_url(scope) for scope in scopes(page))]
    if any(is_taleo_url(candidate) for candidate in candidates if candidate):
        return True
    selectors = (
        "iframe[src*='.taleo.net' i]",
        "form[action*='.taleo.net' i]",
        "a[href*='.taleo.net/careersection/' i]",
        "a[href*='.taleo.net/ats/careers/' i]",
    )
    return any(first_present(scope, selectors) is not None for scope in scopes(page))


def _first_scope_with(page: Any, selectors: Iterable[str]) -> tuple[Any, Any] | None:
    for scope in scopes(page):
        locator = first_present(scope, selectors)
        if locator is not None:
            return scope, locator
    return None


def _content(page: Any) -> str:
    try:
        return str(page.content() or "")
    except Exception:  # noqa: BLE001
        return ""


def _wait(page: Any, milliseconds: int = 900) -> None:
    try:
        page.wait_for_timeout(milliseconds)
    except Exception:  # noqa: BLE001
        pass


def _credential_text(resolution: CredentialResolution, names: tuple[str, ...]) -> str:
    for name in names:
        value = resolution.values.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _login_error_text(scope: Any) -> str:
    messages: list[str] = []
    for selector in _LOGIN_ERROR_SELECTORS:
        try:
            values = scope.locator(selector).all_inner_texts()
        except Exception:  # noqa: BLE001
            values = []
        for value in values:
            text = " ".join(str(value).split())[:240]
            if text and text not in messages:
                messages.append(text)
    return "; ".join(messages[:4])


def _authenticate_existing_account(page: Any, ctx: AdapterInput) -> TaleoPreflight:
    login = _first_scope_with(page, _PASSWORD_SELECTORS)
    if login is None:
        return TaleoPreflight(
            AdapterOutcome(
                "manual_intervention",
                "Taleo requires candidate account creation or authentication, but no safe existing-account login form was found",
            )
        )
    scope, _ = login
    try:
        resolution = resolve_job_credentials("taleo", ctx.job, required=False)
    except CredentialError as exc:
        return TaleoPreflight(AdapterOutcome("manual_intervention", f"Taleo credentials are not usable: {exc}"))
    if resolution is None:
        return TaleoPreflight(
            AdapterOutcome(
                "manual_intervention",
                "Taleo sign-in is required; add an external taleo credential profile or authenticate manually",
            )
        )

    username = _credential_text(resolution, ("username", "email", "login"))
    password = _credential_text(resolution, ("password",))
    if not username or not password:
        return TaleoPreflight(
            AdapterOutcome(
                "manual_intervention",
                f"Taleo credential profile '{resolution.profile}' must contain username or email and password",
            )
        )
    if not try_fill(scope, _USERNAME_SELECTORS, username) or not try_fill(scope, _PASSWORD_SELECTORS, password):
        return TaleoPreflight(
            AdapterOutcome(
                "manual_intervention",
                "Taleo existing-account credentials could not be mapped to unambiguous login fields",
            )
        )
    submit = first_present(scope, _LOGIN_SUBMIT_SELECTORS)
    if submit is None:
        return TaleoPreflight(AdapterOutcome("manual_intervention", "Taleo sign-in control could not be identified safely"))
    try:
        submit.click()
    except Exception as exc:  # noqa: BLE001
        return TaleoPreflight(AdapterOutcome("manual_intervention", f"Taleo sign-in control could not be activated safely: {exc}"))
    _wait(page, 1200)

    handoff = detect_handoff(_content(page))
    if handoff and handoff.kind != "account_wall":
        return TaleoPreflight(
            AdapterOutcome(
                "manual_intervention",
                f"{handoff.reason} after Taleo sign-in (matched {handoff.keyword!r})",
                evidence=[("credential_profile", f"taleo/{resolution.profile}")],
            )
        )
    remaining_login = _first_scope_with(page, _PASSWORD_SELECTORS)
    if remaining_login is not None and find_form_scope(page, CONFIG) is None:
        error_text = _login_error_text(remaining_login[0])
        detail = "Taleo sign-in did not complete; verify the external credential profile or authenticate manually"
        if error_text:
            detail += f" ({error_text})"
        return TaleoPreflight(
            AdapterOutcome(
                "manual_intervention",
                detail,
                evidence=[("credential_profile", f"taleo/{resolution.profile}")],
            )
        )
    return TaleoPreflight(evidence=(("credential_profile", f"taleo/{resolution.profile}"),))


def _prepare_taleo(page: Any, ctx: AdapterInput) -> TaleoPreflight:
    if not is_taleo_page(page, str(ctx.job.get("apply_url", ""))):
        return TaleoPreflight(
            AdapterOutcome(
                "manual_intervention",
                "the page was not verified as a Taleo career-section or Taleo-hosted application surface",
            )
        )

    if find_form_scope(page, CONFIG) is not None:
        return TaleoPreflight()

    apply_action = _first_scope_with(page, _APPLY_SELECTORS)
    if apply_action is not None:
        try:
            apply_action[1].click()
        except Exception as exc:  # noqa: BLE001
            return TaleoPreflight(AdapterOutcome("manual_intervention", f"Taleo Apply Online control could not be activated safely: {exc}"))
        _wait(page)

    page_text = visible_text(_content(page))
    if _first_scope_with(page, _PASSWORD_SELECTORS) is not None:
        authentication = _authenticate_existing_account(page, ctx)
        if authentication.outcome is not None:
            return authentication
        if find_form_scope(page, CONFIG) is not None:
            return authentication

    if any(phrase in page_text for phrase in _CREATE_ACCOUNT_PHRASES):
        return TaleoPreflight(
            AdapterOutcome(
                "manual_intervention",
                "Taleo candidate account creation is required; create and verify the account manually before resuming",
            )
        )

    handoff = detect_handoff(_content(page))
    if handoff:
        return TaleoPreflight(AdapterOutcome("manual_intervention", f"{handoff.reason} (matched {handoff.keyword!r})"))
    if find_form_scope(page, CONFIG) is None:
        return TaleoPreflight(
            AdapterOutcome(
                "manual_intervention",
                "a Taleo page was verified, but no accessible application form was found after the bounded preflight",
            )
        )
    return TaleoPreflight()


def _run_on_page(page: Any, ctx: AdapterInput, shots_dir: Path | None = None) -> AdapterOutcome:
    preflight = _prepare_taleo(page, ctx)
    if preflight.outcome is not None:
        return preflight.outcome
    outcome = run_single_page_form(page, ctx, CONFIG, shots_dir)
    if not preflight.evidence:
        return outcome
    return AdapterOutcome(
        outcome.result,
        outcome.message,
        evidence=[*preflight.evidence, *outcome.evidence],
        screenshots=list(outcome.screenshots),
    )


class TaleoPlaywrightAdapter:
    name = "taleo"

    def run(self, ctx: AdapterInput) -> AdapterOutcome:
        if ctx.live and os.getenv(LIVE_ENV_FLAG, "0") != "1":
            return AdapterOutcome(
                "manual_intervention",
                f"live submission is disabled; set {LIVE_ENV_FLAG}=1 only after reviewing a successful dry run",
            )
        if not ctx.resume_pdf or not Path(ctx.resume_pdf).exists():
            return AdapterOutcome("manual_intervention", "resume PDF is missing; prepare documents first")
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return AdapterOutcome(
                "failed",
                "Playwright is not installed. Run: pip install 'jobsniffing[automation]' && playwright install chromium",
            )

        shots_dir = resolve_project_path(f"data/screenshots/{ctx.job.get('id', 'unknown')}")
        headless = os.getenv("JOBSNIFFING_PLAYWRIGHT_HEADLESS", "1") != "0"
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=headless)
                page = browser.new_page()
                page.goto(str(ctx.job.get("apply_url", "")), wait_until="domcontentloaded")
                outcome = _run_on_page(page, ctx, shots_dir)
                browser.close()
                return outcome
        except Exception as exc:  # noqa: BLE001
            return AdapterOutcome("failed", f"browser automation failed: {exc}")
