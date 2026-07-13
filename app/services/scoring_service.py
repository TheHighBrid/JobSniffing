import re
from collections.abc import Mapping

IMPORTANT_TERMS: dict[str, int] = {
    "android": 14,
    "python": 10,
    "fastapi": 10,
    "sqlite": 8,
    "remote": 6,
    "backend": 5,
    "mobile": 5,
}


def _contains_term(text: str, term: str) -> bool:
    pattern = rf"(?<![\w-]){re.escape(term.lower())}(?![\w-])"
    return re.search(pattern, text) is not None


def score_text(
    title: str,
    description: str,
    preferred_terms: Mapping[str, int] | None = None,
) -> int:
    terms = preferred_terms or IMPORTANT_TERMS
    haystack = f"{title} {description}".lower()
    score = sum(weight for term, weight in terms.items() if _contains_term(haystack, term))
    return max(0, min(100, score))
