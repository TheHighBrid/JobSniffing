from dataclasses import dataclass, field
from datetime import datetime, UTC
from app.domain.enums import ApplicationStatus


@dataclass(slots=True)
class JobPosting:
    source: str
    external_id: str
    title: str
    company: str
    location: str
    apply_url: str
    description: str = ""
    score: int = 0

    @property
    def dedupe_key(self) -> str:
        return f"{self.source}:{self.external_id}".lower()


@dataclass(slots=True)
class Application:
    job: JobPosting
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
