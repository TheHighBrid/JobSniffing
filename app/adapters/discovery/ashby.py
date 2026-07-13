from app.domain.schemas import JobPostingIn, JsonObject


def normalize_ashby(payload: JsonObject, company: str) -> list[JobPostingIn]:
    postings = payload.get("jobs", [])
    if not isinstance(postings, list):
        raise ValueError("Ashby payload must contain a jobs list")
    normalized: list[JobPostingIn] = []
    for job in postings:
        if not isinstance(job, dict):
            continue
        external_id = job.get("id") or job.get("jobUrl") or job.get("applyUrl")
        if not external_id:
            continue
        normalized.append(
            JobPostingIn(
                source="ashby",
                external_id=str(external_id),
                title=job.get("title") or "Untitled",
                company=company,
                location=job.get("location") or "",
                apply_url=job.get("jobUrl") or job.get("applyUrl") or "",
                description=job.get("descriptionHtml") or job.get("descriptionPlain") or "",
            )
        )
    return normalized
