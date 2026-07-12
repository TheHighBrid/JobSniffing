from app.domain.schemas import JobPostingIn


def normalize_greenhouse(payload: dict, board_token: str) -> list[JobPostingIn]:
    jobs = payload.get("jobs", [])
    normalized: list[JobPostingIn] = []
    for job in jobs:
        location = job.get("location") or {}
        normalized.append(JobPostingIn(
            source="greenhouse",
            external_id=str(job["id"]),
            title=job.get("title", "Untitled"),
            company=board_token,
            location=location.get("name", ""),
            apply_url=job.get("absolute_url", ""),
            description=job.get("content", ""),
        ))
    return normalized
