import pytest
from app.domain.enums import ApplicationStatus
from app.domain.state_machine import assert_transition, can_transition, is_terminal


def test_safe_progression_and_noop():
    assert can_transition(ApplicationStatus.SCORED, ApplicationStatus.SHORTLISTED)
    assert can_transition(ApplicationStatus.SCORED, ApplicationStatus.SCORED)
    assert can_transition(ApplicationStatus.FILLING, ApplicationStatus.NEEDS_REVIEW)


def test_submitted_is_terminal():
    assert is_terminal(ApplicationStatus.SUBMITTED)
    with pytest.raises(ValueError):
        assert_transition(ApplicationStatus.SUBMITTED, ApplicationStatus.FAILED)
