from app.services.scoring_service import score_text


def test_score_text_is_deterministic_and_local():
    assert score_text("Android FastAPI Engineer", "Python SQLite backend") > 30
    assert score_text("Retail Associate", "Cash handling") == 0
