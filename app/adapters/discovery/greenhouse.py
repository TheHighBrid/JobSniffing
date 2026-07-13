from app.domain.schemas import JobPostingIn, JsonObject


def normalize_greenhouse(payload: JsonObject, board_token: str) -> list[JobPostingIn]:
    jobs = payload.get("jobs", [])
    if not isinstance(jobs, list):
        raise ValueError("Greenhouse payload must contain a jobs list")
    normalized: list[JobPostingIn] = []
    for job in jobs:
        if not isinstance(job, dict) or "id" not in job:
            continue
        location = job.get("location") or {}
        normalized.append(
            JobPostingIn(
                source="greenhouse",
                external_id=str(job["id"]),
                title=job.get("title") or "Untitled",
                company=board_token,
                location=location.get("name", "") if isinstance(location, dict) else str(location),
                apply_url=job.get("absolute_url") or job.get("url") or "",
                description=job.get("content") or "",
            )
        )
    return normalized
