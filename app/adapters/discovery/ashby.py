from app.domain.schemas import JobPostingIn


def normalize_ashby(payload: dict, company: str) -> list[JobPostingIn]:
    postings = payload.get("jobs", [])
    return [JobPostingIn(
        source="ashby",
        external_id=str(job["id"]),
        title=job.get("title", "Untitled"),
        company=company,
        location=(job.get("location") or ""),
        apply_url=job.get("jobUrl") or job.get("applyUrl") or "",
        description=job.get("descriptionHtml", ""),
    ) for job in postings]
