"""Unified detection of flows that must be handed to the user."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class HandoffDetection:
    kind: str
    keyword: str
    reason: str


_PATTERNS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "anti_bot",
        "anti-bot challenge detected; it must be completed manually",
        (
            "recaptcha", "hcaptcha", "cf-turnstile", "cloudflare challenge",
            "verify you are human", "are you a robot", "unusual traffic",
            "security check to access", "press and hold to confirm",
        ),
    ),
    (
        "two_factor",
        "two-factor or identity verification is required; enter the code manually",
        (
            "two-factor authentication", "multi-factor authentication", "mfa code",
            "one-time passcode", "one time passcode", "verification code",
            "authenticator app", "check your email for a code", "texted you a code",
            "code sent to your phone",
        ),
    ),
    (
        "assessment",
        "an employer assessment was detected; complete it personally",
        (
            "hirevue", "hackerrank", "codility", "pymetrics", "criteria cognitive",
            "coding assessment", "personality assessment", "cognitive assessment",
            "recorded video interview", "skills assessment", "pre-employment assessment",
        ),
    ),
    (
        "account_wall",
        "an account or login wall was detected; authenticate manually before resuming",
        (
            "sign in to continue your application", "log in to continue your application",
            "create an account to apply", "create your candidate account",
            "enter your password to continue", "candidate login required",
        ),
    ),
)


def visible_text(content: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", str(content)).casefold().split())


def detect_handoff(content: str) -> HandoffDetection | None:
    text = visible_text(content)
    for kind, reason, keywords in _PATTERNS:
        for keyword in keywords:
            if keyword in text:
                return HandoffDetection(kind, keyword, reason)
    return None
