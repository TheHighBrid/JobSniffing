import pytest

from app.domain.enums import ApplicationStatus
from app.domain.state_machine import assert_transition, can_transition, is_terminal


def test_review_gate_path_allows_safe_queue_progression():
    assert can_transition(ApplicationStatus.DISCOVERED, ApplicationStatus.SCORED)
    assert can_transition(ApplicationStatus.APPROVED, ApplicationStatus.QUEUED)
    assert can_transition(ApplicationStatus.FILLING, ApplicationStatus.NEEDS_REVIEW)


def test_submitted_is_terminal():
    assert is_terminal(ApplicationStatus.SUBMITTED)
    with pytest.raises(ValueError):
        assert_transition(ApplicationStatus.SUBMITTED, ApplicationStatus.FAILED)


def test_failed_can_be_requeued_after_review():
    assert can_transition(ApplicationStatus.FAILED, ApplicationStatus.NEEDS_REVIEW)
    assert can_transition(ApplicationStatus.FAILED, ApplicationStatus.QUEUED)
