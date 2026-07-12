from dataclasses import dataclass
from app.domain.enums import ApplicationStatus


@dataclass(slots=True)
class JobPostingIn:
    source: str
    external_id: str
    title: str
    company: str
    apply_url: str
    location: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        for field in ("source", "external_id", "title", "company", "apply_url"):
            if not getattr(self, field):
                raise ValueError(f"{field} is required")


@dataclass(slots=True)
class JobPostingOut(JobPostingIn):
    id: int = 0
    score: int = 0
    status: ApplicationStatus = ApplicationStatus.DISCOVERED


@dataclass(slots=True)
class StatusChange:
    status: ApplicationStatus
    notes: str = ""
