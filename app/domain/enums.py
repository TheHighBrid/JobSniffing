from enum import StrEnum


class ApplicationStatus(StrEnum):
    DISCOVERED = "discovered"
    SCORED = "scored"
    SHORTLISTED = "shortlisted"
    DOCUMENTS_PREPARED = "documents_prepared"
    APPROVED = "approved"
    QUEUED = "queued"
    FILLING = "filling"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    NEEDS_REVIEW = "needs_review"
    MANUAL_INTERVENTION_REQUIRED = "manual_intervention_required"
    VERIFICATION_FAILED = "verification_failed"
    SUBMITTED = "submitted"
    BLOCKED = "blocked"
    FAILED = "failed"
    WITHDRAWN = "withdrawn"


TERMINAL_STATUSES = {ApplicationStatus.SUBMITTED, ApplicationStatus.BLOCKED, ApplicationStatus.WITHDRAWN}


class AutomationMode(StrEnum):
    MANUAL = "manual"
    ASSISTED = "assisted"
    AUTO = "auto"
