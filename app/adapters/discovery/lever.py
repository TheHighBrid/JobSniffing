from app.domain.schemas import JobPostingIn


def normalize_lever(payload: list[dict], company: str) -> list[JobPostingIn]:
    if not isinstance(payload, list):
        raise ValueError("Lever payload must be a list")
    normalized: list[JobPostingIn] = []
    for job in payload:
        if not isinstance(job, dict) or "id" not in job:
            continue
        categories = job.get("categories") or {}
        normalized.append(
            JobPostingIn(
                source="lever",
                external_id=str(job["id"]),
                title=job.get("text") or "Untitled",
                company=company,
                location=categories.get("location", "") if isinstance(categories, dict) else "",
                apply_url=job.get("hostedUrl") or job.get("applyUrl") or "",
                description=job.get("descriptionPlain") or job.get("description") or "",
            )
        )
    return normalized
