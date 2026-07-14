from app.domain.enums import ApplicationStatus, TERMINAL_STATUSES

ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.DISCOVERED: {ApplicationStatus.SCORED, ApplicationStatus.BLOCKED},
    ApplicationStatus.SCORED: {ApplicationStatus.SHORTLISTED, ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.BLOCKED},
    ApplicationStatus.SHORTLISTED: {ApplicationStatus.DOCUMENTS_PREPARED, ApplicationStatus.APPROVED, ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.BLOCKED},
    ApplicationStatus.DOCUMENTS_PREPARED: {ApplicationStatus.APPROVED, ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.VERIFICATION_FAILED, ApplicationStatus.BLOCKED},
    ApplicationStatus.APPROVED: {ApplicationStatus.QUEUED, ApplicationStatus.DOCUMENTS_PREPARED, ApplicationStatus.BLOCKED},
    ApplicationStatus.QUEUED: {ApplicationStatus.FILLING, ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.MANUAL_INTERVENTION_REQUIRED, ApplicationStatus.BLOCKED},
    ApplicationStatus.FILLING: {ApplicationStatus.AWAITING_CONFIRMATION, ApplicationStatus.SUBMITTED, ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.MANUAL_INTERVENTION_REQUIRED, ApplicationStatus.BLOCKED, ApplicationStatus.FAILED},
    ApplicationStatus.AWAITING_CONFIRMATION: {ApplicationStatus.SUBMITTED, ApplicationStatus.VERIFICATION_FAILED, ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.MANUAL_INTERVENTION_REQUIRED, ApplicationStatus.FAILED},
    ApplicationStatus.NEEDS_REVIEW: {ApplicationStatus.APPROVED, ApplicationStatus.QUEUED, ApplicationStatus.DOCUMENTS_PREPARED, ApplicationStatus.MANUAL_INTERVENTION_REQUIRED, ApplicationStatus.BLOCKED, ApplicationStatus.FAILED},
    ApplicationStatus.MANUAL_INTERVENTION_REQUIRED: {ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.APPROVED, ApplicationStatus.QUEUED, ApplicationStatus.BLOCKED, ApplicationStatus.FAILED},
    ApplicationStatus.VERIFICATION_FAILED: {ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.DOCUMENTS_PREPARED, ApplicationStatus.BLOCKED, ApplicationStatus.FAILED},
    ApplicationStatus.SUBMITTED: {ApplicationStatus.WITHDRAWN},
    ApplicationStatus.BLOCKED: set(),
    ApplicationStatus.FAILED: {ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.MANUAL_INTERVENTION_REQUIRED},
    ApplicationStatus.WITHDRAWN: set(),
}


def can_transition(current: ApplicationStatus, target: ApplicationStatus) -> bool:
    return current == target or target in ALLOWED_TRANSITIONS[current]


def assert_transition(current: ApplicationStatus, target: ApplicationStatus) -> None:
    if not can_transition(current, target):
        raise ValueError(f"Invalid application status transition: {current.value} -> {target.value}")


def is_terminal(status: ApplicationStatus) -> bool:
    return status in TERMINAL_STATUSES
