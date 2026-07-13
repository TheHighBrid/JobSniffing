from app.adapters.discovery.common import strip_html
from app.domain.schemas import JobPostingIn


def normalize_lever(payload: list[dict], company: str) -> list[JobPostingIn]:
    if not isinstance(payload, list):
        raise ValueError("Lever payload must be a list")
    result: list[JobPostingIn] = []
    for job in payload:
        if not isinstance(job, dict):
            continue
        try:
            external_id = job.get("id")
            apply_url = job.get("hostedUrl") or job.get("applyUrl") or ""
            if external_id in (None, "") or not apply_url:
                continue
            categories = job.get("categories") or {}
            sections = " ".join(
                strip_html(section.get("content", ""))
                for section in (job.get("lists") or [])
                if isinstance(section, dict)
            )
            description = job.get("descriptionPlain") or strip_html(
                job.get("description", "")
            )
            result.append(
                JobPostingIn(
                    source="lever",
                    external_id=str(external_id),
                    title=job.get("text") or "Untitled",
                    company=company,
                    location=(
                        categories.get("location", "")
                        if isinstance(categories, dict)
                        else ""
                    ),
                    apply_url=apply_url,
                    description=f"{description} {sections}".strip(),
                )
            )
        except (TypeError, ValueError):
            continue
    return result
