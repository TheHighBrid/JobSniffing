from app.services.scoring_service import score_text


def test_default_score_is_tuned_for_target_search():
    score = score_text("Bilingual Fraud Investigator", "AML KYC banking investigations and client service", "Ottawa")
    assert score >= 80


def test_irrelevant_role_scores_zero():
    assert score_text("Retail Associate", "Cash handling", "Calgary") == 0


def test_exclusion_reduces_score():
    clean = score_text("Fraud Investigator", "AML banking", "Remote")
    excluded = score_text("Fraud Investigator", "AML banking commission only", "Remote")
    assert excluded < clean


def test_custom_terms_replace_defaults():
    assert score_text("Python Engineer", "FastAPI", preferred_terms={"python": 20}, excluded_terms=[]) == 40
