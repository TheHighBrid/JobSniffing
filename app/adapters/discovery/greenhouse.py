from app.adapters.discovery.common import strip_html
from app.domain.schemas import JobPostingIn


def normalize_greenhouse(
    payload: dict,
    board_token: str,
    company: str | None = None,
) -> list[JobPostingIn]:
    jobs = payload.get("jobs", [])
    if not isinstance(jobs, list):
        raise ValueError("Greenhouse payload must contain a jobs list")
    result: list[JobPostingIn] = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        try:
            external_id = job.get("id")
            apply_url = job.get("absolute_url") or ""
            if external_id in (None, "") or not apply_url:
                continue
            location = job.get("location") or {}
            result.append(
                JobPostingIn(
                    source="greenhouse",
                    external_id=str(external_id),
                    title=job.get("title") or "Untitled",
                    company=company or board_token,
                    location=(
                        location.get("name", "")
                        if isinstance(location, dict)
                        else str(location)
                    ),
                    apply_url=apply_url,
                    description=strip_html(job.get("content", "")),
                )
            )
        except (TypeError, ValueError):
            continue
    return result
