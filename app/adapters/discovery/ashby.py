from app.adapters.discovery.common import strip_html
from app.domain.schemas import JobPostingIn


def normalize_ashby(payload: dict, company: str) -> list[JobPostingIn]:
    jobs = payload.get("jobs", [])
    if not isinstance(jobs, list):
        raise ValueError("Ashby payload must contain a jobs list")
    result: list[JobPostingIn] = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        try:
            external_id = job.get("id")
            apply_url = job.get("jobUrl") or job.get("applyUrl") or ""
            if external_id in (None, "") or not apply_url:
                continue
            result.append(
                JobPostingIn(
                    source="ashby",
                    external_id=str(external_id),
                    title=job.get("title") or "Untitled",
                    company=company,
                    location=job.get("location") or "",
                    apply_url=apply_url,
                    description=strip_html(job.get("descriptionHtml", "")),
                )
            )
        except (TypeError, ValueError):
            continue
    return result
