from app.services.scoring_service import score_text


def test_score_text_is_deterministic_and_local():
    assert score_text("Android FastAPI Engineer", "Python SQLite backend") > 30
    assert score_text("Retail Associate", "Cash handling") == 0


def test_scoring_uses_word_boundaries():
    assert score_text("Pythonista", "") == 0
    assert score_text("Python Engineer", "") == 10
