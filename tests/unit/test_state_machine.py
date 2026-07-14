import pytest
from app.domain.enums import ApplicationStatus
from app.domain.state_machine import assert_transition, can_transition, is_terminal


def test_safe_progression_and_noop():
    assert can_transition(ApplicationStatus.SCORED, ApplicationStatus.SHORTLISTED)
    assert can_transition(ApplicationStatus.SCORED, ApplicationStatus.SCORED)
    assert can_transition(ApplicationStatus.FILLING, ApplicationStatus.AWAITING_CONFIRMATION)
    assert can_transition(ApplicationStatus.AWAITING_CONFIRMATION, ApplicationStatus.SUBMITTED)
    assert can_transition(ApplicationStatus.DOCUMENTS_PREPARED, ApplicationStatus.VERIFICATION_FAILED)


def test_submitted_is_terminal():
    assert is_terminal(ApplicationStatus.SUBMITTED)
    assert is_terminal(ApplicationStatus.WITHDRAWN)
    with pytest.raises(ValueError):
        assert_transition(ApplicationStatus.SUBMITTED, ApplicationStatus.FAILED)
