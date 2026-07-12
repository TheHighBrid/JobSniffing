IMPORTANT_TERMS = {
    "android": 14,
    "python": 10,
    "fastapi": 10,
    "sqlite": 8,
    "remote": 6,
    "backend": 5,
    "mobile": 5,
}


def score_text(title: str, description: str, preferred_terms: dict[str, int] | None = None) -> int:
    terms = preferred_terms or IMPORTANT_TERMS
    haystack = f"{title} {description}".lower()
    return min(100, sum(weight for term, weight in terms.items() if term.lower() in haystack))
