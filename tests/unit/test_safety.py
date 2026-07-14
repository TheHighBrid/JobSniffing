from app.domain.enums import AutomationMode
from app.domain.safety import SafetyPolicy, evaluate_submission


def test_manual_and_assisted_modes_fail_closed():
    manual = evaluate_submission(SafetyPolicy(), company="Example", apply_url="https://example.com", submissions_today=0)
    assisted = evaluate_submission(SafetyPolicy(mode=AutomationMode.ASSISTED, daily_cap=5), company="Example", apply_url="https://example.com", submissions_today=0)
    assert not manual.allowed and "manual" in manual.reason
    assert not assisted.allowed and "confirmation" in assisted.reason


def test_auto_mode_obeys_cap_and_blocklists():
    policy = SafetyPolicy(mode=AutomationMode.AUTO, daily_cap=1, blacklisted_companies=("BadCo",))
    assert evaluate_submission(policy, company="Example", apply_url="https://example.com", submissions_today=0).allowed
    assert not evaluate_submission(policy, company="BadCo Canada", apply_url="https://example.com", submissions_today=0).allowed
    assert not evaluate_submission(policy, company="Example", apply_url="https://linkedin.com/jobs/1", submissions_today=0).allowed
    assert not evaluate_submission(policy, company="Example", apply_url="https://example.com", submissions_today=1).allowed
