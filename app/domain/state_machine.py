from app.domain.enums import ApplicationStatus, TERMINAL_STATUSES

ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.DISCOVERED: {ApplicationStatus.SCORED, ApplicationStatus.BLOCKED},
    ApplicationStatus.SCORED: {ApplicationStatus.SHORTLISTED, ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.BLOCKED},
    ApplicationStatus.SHORTLISTED: {ApplicationStatus.APPROVED, ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.BLOCKED},
    ApplicationStatus.APPROVED: {ApplicationStatus.QUEUED, ApplicationStatus.BLOCKED},
    ApplicationStatus.QUEUED: {ApplicationStatus.FILLING, ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.BLOCKED},
    ApplicationStatus.FILLING: {ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.SUBMITTED, ApplicationStatus.BLOCKED, ApplicationStatus.FAILED},
    ApplicationStatus.NEEDS_REVIEW: {ApplicationStatus.APPROVED, ApplicationStatus.QUEUED, ApplicationStatus.BLOCKED, ApplicationStatus.FAILED},
    ApplicationStatus.SUBMITTED: set(),
    ApplicationStatus.BLOCKED: set(),
    ApplicationStatus.FAILED: {ApplicationStatus.NEEDS_REVIEW},
}


def can_transition(current: ApplicationStatus, target: ApplicationStatus) -> bool:
    return current == target or target in ALLOWED_TRANSITIONS[current]


def assert_transition(current: ApplicationStatus, target: ApplicationStatus) -> None:
    if not can_transition(current, target):
        raise ValueError(f"Invalid application status transition: {current.value} -> {target.value}")


def is_terminal(status: ApplicationStatus) -> bool:
    return status in TERMINAL_STATUSES
