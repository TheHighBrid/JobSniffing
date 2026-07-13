from app.adapters.discovery.common import strip_html
from app.domain.schemas import JobPostingIn


def normalize_greenhouse(payload: dict, board_token: str, company: str | None = None) -> list[JobPostingIn]:
    result = []
    for job in payload.get("jobs", []):
        location = job.get("location") or {}
        result.append(JobPostingIn(
            source="greenhouse", external_id=str(job["id"]), title=job.get("title", "Untitled"),
            company=company or board_token,
            location=location.get("name", "") if isinstance(location, dict) else str(location),
            apply_url=job.get("absolute_url", ""), description=strip_html(job.get("content", "")),
        ))
    return result
