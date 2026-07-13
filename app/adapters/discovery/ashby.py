from app.adapters.discovery.common import strip_html
from app.domain.schemas import JobPostingIn


def normalize_ashby(payload: dict, company: str) -> list[JobPostingIn]:
    return [JobPostingIn(
        source="ashby", external_id=str(job["id"]), title=job.get("title", "Untitled"), company=company,
        location=job.get("location") or "", apply_url=job.get("jobUrl") or job.get("applyUrl") or "",
        description=strip_html(job.get("descriptionHtml", "")),
    ) for job in payload.get("jobs", [])]
