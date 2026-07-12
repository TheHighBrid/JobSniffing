from dataclasses import dataclass
from app.domain.enums import ApplicationStatus


@dataclass(frozen=True, slots=True)
class SubmitResult:
    status: ApplicationStatus
    message: str


def prepare_manual_handoff(apply_url: str) -> SubmitResult:
    return SubmitResult(
        status=ApplicationStatus.NEEDS_REVIEW,
        message=f"Manual review required. Open apply page: {apply_url}",
    )
