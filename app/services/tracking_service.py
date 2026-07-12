import sqlite3
from app.domain.enums import ApplicationStatus
from app.domain.schemas import JobPostingIn
from app.domain.state_machine import assert_transition
from app.services.scoring_service import score_text


def upsert_job(conn: sqlite3.Connection, job: JobPostingIn) -> int:
    score = score_text(job.title, job.description)
    conn.execute(
        """
        INSERT INTO job_postings (source, external_id, title, company, location, apply_url, description, score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source, external_id) DO UPDATE SET
          title=excluded.title, company=excluded.company, location=excluded.location,
          apply_url=excluded.apply_url, description=excluded.description, score=excluded.score,
          updated_at=CURRENT_TIMESTAMP
        """,
        (job.source, job.external_id, job.title, job.company, job.location, job.apply_url, job.description, score, ApplicationStatus.SCORED.value),
    )
    row = conn.execute("SELECT id FROM job_postings WHERE source=? AND external_id=?", (job.source, job.external_id)).fetchone()
    return int(row["id"])


def list_jobs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("SELECT * FROM job_postings ORDER BY score DESC, created_at DESC"))


def change_status(conn: sqlite3.Connection, job_id: int, target: ApplicationStatus, notes: str = "") -> None:
    row = conn.execute("SELECT status FROM job_postings WHERE id=?", (job_id,)).fetchone()
    if row is None:
        raise KeyError(f"Unknown job id {job_id}")
    current = ApplicationStatus(row["status"])
    assert_transition(current, target)
    conn.execute(
        "UPDATE job_postings SET status=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (target.value, notes, job_id),
    )
