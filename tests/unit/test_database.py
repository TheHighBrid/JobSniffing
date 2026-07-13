from app.db.sqlite import configured_db_path, init_db, session


def test_database_path_is_read_at_call_time(tmp_path, monkeypatch):
    first = tmp_path / "first.sqlite3"
    second = tmp_path / "second.sqlite3"
    monkeypatch.setenv("JOBSNIFFING_DB", str(first))
    assert configured_db_path() == first
    init_db()
    monkeypatch.setenv("JOBSNIFFING_DB", str(second))
    assert configured_db_path() == second
    init_db()
    assert first.exists() and second.exists()


def test_session_rolls_back_on_error(tmp_path):
    db = tmp_path / "rollback.sqlite3"
    init_db(db)
    try:
        with session(db) as conn:
            conn.execute("INSERT INTO run_logs(kind, message) VALUES ('test', 'nope')")
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    with session(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM run_logs").fetchone()[0] == 0
