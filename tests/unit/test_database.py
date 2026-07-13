from app.db.sqlite import connect, init_db


def test_database_env_is_resolved_at_call_time(tmp_path, monkeypatch):
    first, second = tmp_path / "first.sqlite3", tmp_path / "second.sqlite3"
    monkeypatch.setenv("JOBSNIFFING_DB", str(first)); assert init_db() == first
    monkeypatch.setenv("JOBSNIFFING_DB", str(second)); assert init_db() == second
    assert first.exists() and second.exists()


def test_relative_database_is_project_anchored(monkeypatch):
    monkeypatch.setenv("JOBSNIFFING_DB", "data/test-relative.sqlite3")
    path = init_db()
    try:
        assert path.is_absolute()
        with connect() as conn: assert conn.execute("SELECT 1").fetchone()[0] == 1
    finally:
        path.unlink(missing_ok=True)
