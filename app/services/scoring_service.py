from __future__ import annotations

import re

DEFAULT_PREFERRED_TERMS = {
    "fraud": 18, "fraude": 18, "anti-money laundering": 18, "aml": 18,
    "kyc": 16, "compliance": 15, "conformité": 15, "investigation": 14,
    "enquête": 14, "bilingual": 13, "bilingue": 13, "banking": 11,
    "financial services": 11, "risk": 10, "client service": 8,
    "government": 8, "ottawa": 6, "gatineau": 6, "remote": 5,
}
DEFAULT_EXCLUDED_TERMS = ["commission only", "door to door", "unpaid internship"]


def _contains(text: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term.lower())}(?!\w)", text) is not None


def score_text(title: str, description: str, location: str = "", preferred_terms: dict[str, int] | None = None, excluded_terms: list[str] | None = None) -> int:
    terms = preferred_terms or DEFAULT_PREFERRED_TERMS
    exclusions = DEFAULT_EXCLUDED_TERMS if excluded_terms is None else excluded_terms
    title_text = title.lower()
    body_text = f"{description} {location}".lower()
    score = 0
    for term, weight in terms.items():
        if _contains(title_text, term):
            score += int(weight) * 2
        elif _contains(body_text, term):
            score += int(weight)
    combined = f"{title_text} {body_text}"
    score -= 35 * sum(1 for term in exclusions if _contains(combined, term))
    return max(0, min(100, score))
