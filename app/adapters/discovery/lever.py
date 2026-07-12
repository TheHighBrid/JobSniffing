from app.domain.schemas import JobPostingIn


def normalize_lever(payload: list[dict], company: str) -> list[JobPostingIn]:
    return [JobPostingIn(
        source="lever",
        external_id=str(job["id"]),
        title=job.get("text", "Untitled"),
        company=company,
        location=(job.get("categories") or {}).get("location", ""),
        apply_url=job.get("hostedUrl") or job.get("applyUrl") or "",
        description=job.get("descriptionPlain", ""),
    ) for job in payload]
