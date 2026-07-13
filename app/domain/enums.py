from enum import StrEnum


class ApplicationStatus(StrEnum):
    DISCOVERED = "discovered"
    SCORED = "scored"
    SHORTLISTED = "shortlisted"
    APPROVED = "approved"
    QUEUED = "queued"
    FILLING = "filling"
    NEEDS_REVIEW = "needs_review"
    SUBMITTED = "submitted"
    BLOCKED = "blocked"
    FAILED = "failed"


TERMINAL_STATUSES = {ApplicationStatus.SUBMITTED, ApplicationStatus.BLOCKED}
