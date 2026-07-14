from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.enums import AutomationMode


@dataclass(frozen=True)
class SafetyPolicy:
    """Fail-closed automation guardrails for application preparation/submission."""

    mode: AutomationMode = AutomationMode.MANUAL
    daily_cap: int = 0
    min_delay_seconds: int = 0
    blacklisted_companies: tuple[str, ...] = ()
    blocked_domains: tuple[str, ...] = ("linkedin.com", "indeed.com", "upwork.com")

    def allows_submission(self) -> bool:
        return self.mode is AutomationMode.AUTO and self.daily_cap > 0


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str


def evaluate_submission(
    policy: SafetyPolicy,
    *,
    company: str,
    apply_url: str,
    submissions_today: int,
    today: date | None = None,
) -> SafetyDecision:
    """Return whether an automated submission may proceed under local guardrails.

    The optional date parameter keeps tests deterministic and documents that caps are
    daily. This guard does not solve CAPTCHAs or override adapter-specific checks.
    """

    _ = today or date.today()
    lowered_company = company.casefold()
    lowered_url = apply_url.casefold()
    for blocked in policy.blacklisted_companies:
        if blocked.casefold() in lowered_company:
            return SafetyDecision(False, f"company blacklisted: {blocked}")
    for domain in policy.blocked_domains:
        if domain.casefold() in lowered_url:
            return SafetyDecision(False, f"domain blocked: {domain}")
    if policy.mode is AutomationMode.MANUAL:
        return SafetyDecision(False, "manual mode allows preparation only")
    if policy.mode is AutomationMode.ASSISTED:
        return SafetyDecision(False, "assisted mode requires human confirmation before submit")
    if submissions_today >= policy.daily_cap:
        return SafetyDecision(False, "daily submission cap reached")
    return SafetyDecision(True, "allowed by automation mode and safety policy")
