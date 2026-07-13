from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from app.domain.enums import ApplicationStatus
from app.domain.schemas import JobPostingIn, ScoringSettings
from app.domain.state_machine import assert_transition
from app.services.scoring_service import score_text
from app.services.settings_service import is_blacklisted, load_scoring_settings


def upsert_job(conn: sqlite3.Connection, job: JobPostingIn, settings: ScoringSettings | None = None) -> int:
    settings = settings or load_scoring_settings(conn)
    score = score_text(job.title, job.description, job.location, settings.preferred_terms, settings.excluded_terms)
    initial = ApplicationStatus.BLOCKED if is_blacklisted(job.company, settings) else ApplicationStatus.SCORED
    conn.execute("""
      INSERT INTO job_postings(source,external_id,title,company,location,apply_url,description,score,status)
      VALUES(?,?,?,?,?,?,?,?,?)
      ON CONFLICT(source,external_id) DO UPDATE SET title=excluded.title,company=excluded.company,
      location=excluded.location,apply_url=excluded.apply_url,description=excluded.description,
      score=excluded.score,updated_at=CURRENT_TIMESTAMP
    """, (job.source, job.external_id, job.title, job.company, job.location, job.apply_url, job.description, score, initial.value))
    row = conn.execute("SELECT id FROM job_postings WHERE source=? AND external_id=?", (job.source, job.external_id)).fetchone()
    return int(row["id"])


def bulk_upsert(conn: sqlite3.Connection, jobs: Iterable[JobPostingIn]) -> list[int]:
    settings = load_scoring_settings(conn)
    return [upsert_job(conn, job, settings) for job in jobs]


def list_jobs(conn: sqlite3.Connection, *, status: ApplicationStatus | None = None, query: str = "", min_score: int = 0, limit: int = 250) -> list[sqlite3.Row]:
    clauses, params = ["score>=?"], [min_score]
    if status is not None:
        clauses.append("status=?"); params.append(status.value)
    if query.strip():
        like = f"%{query.strip()}%"
        clauses.append("(title LIKE ? OR company LIKE ? OR location LIKE ? OR description LIKE ?)")
        params.extend([like] * 4)
    params.append(limit)
    return list(conn.execute(f"SELECT * FROM job_postings WHERE {' AND '.join(clauses)} ORDER BY score DESC,updated_at DESC,id DESC LIMIT ?", params))


def get_job(conn: sqlite3.Connection, job_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM job_postings WHERE id=?", (job_id,)).fetchone()


def delete_job(conn: sqlite3.Connection, job_id: int) -> bool:
    return conn.execute("DELETE FROM job_postings WHERE id=?", (job_id,)).rowcount > 0


def change_status(conn: sqlite3.Connection, job_id: int, target: ApplicationStatus, notes: str = "") -> None:
    row = conn.execute("SELECT status FROM job_postings WHERE id=?", (job_id,)).fetchone()
    if row is None:
        raise KeyError(f"Unknown job id {job_id}")
    assert_transition(ApplicationStatus(row["status"]), target)
    conn.execute("UPDATE job_postings SET status=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (target.value, notes, job_id))


def rescore_all(conn: sqlite3.Connection, settings: ScoringSettings | None = None) -> int:
    settings = settings or load_scoring_settings(conn)
    rows = conn.execute("SELECT id,title,description,location FROM job_postings").fetchall()
    for row in rows:
        score = score_text(row["title"], row["description"], row["location"], settings.preferred_terms, settings.excluded_terms)
        conn.execute("UPDATE job_postings SET score=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (score, row["id"]))
    return len(rows)


def stats(conn: sqlite3.Connection) -> dict[str, object]:
    total = int(conn.execute("SELECT COUNT(*) FROM job_postings").fetchone()[0])
    by_status = {row["status"]: int(row["count"]) for row in conn.execute("SELECT status,COUNT(*) count FROM job_postings GROUP BY status")}
    average = conn.execute("SELECT COALESCE(ROUND(AVG(score),1),0) FROM job_postings").fetchone()[0]
    return {"total": total, "average_score": average, "by_status": by_status}


def log_run(conn: sqlite3.Connection, kind: str, message: str) -> None:
    conn.execute("INSERT INTO run_logs(kind,message) VALUES(?,?)", (kind, message))
