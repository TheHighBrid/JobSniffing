from app.adapters.discovery.common import strip_html
from app.domain.schemas import JobPostingIn


def normalize_lever(payload: list[dict], company: str) -> list[JobPostingIn]:
    result = []
    for job in payload:
        categories = job.get("categories") or {}
        sections = " ".join(strip_html(s.get("content", "")) for s in (job.get("lists") or []))
        description = job.get("descriptionPlain") or strip_html(job.get("description", ""))
        result.append(JobPostingIn(
            source="lever", external_id=str(job["id"]), title=job.get("text", "Untitled"), company=company,
            location=categories.get("location", ""), apply_url=job.get("hostedUrl") or job.get("applyUrl") or "",
            description=f"{description} {sections}".strip(),
        ))
    return result
