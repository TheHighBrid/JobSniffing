import sqlite3

from app.domain.enums import ApplicationStatus
from app.domain.schemas import JobPostingIn
from app.domain.state_machine import assert_transition
from app.services.scoring_service import score_text


class JobNotFoundError(LookupError):
    pass


class InvalidTransitionError(ValueError):
    pass


def upsert_job(conn: sqlite3.Connection, job: JobPostingIn) -> int:
    score = score_text(job.title, job.description)
    conn.execute(
        """
        INSERT INTO job_postings (
          source, external_id, title, company, location, apply_url,
          description, score, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source, external_id) DO UPDATE SET
          title=excluded.title,
          company=excluded.company,
          location=excluded.location,
          apply_url=excluded.apply_url,
          description=excluded.description,
          score=excluded.score,
          updated_at=CURRENT_TIMESTAMP
        """,
        (
            job.source,
            job.external_id,
            job.title,
            job.company,
            job.location,
            str(job.apply_url),
            job.description,
            score,
            ApplicationStatus.SCORED.value,
        ),
    )
    row = conn.execute(
        "SELECT id FROM job_postings WHERE source=? AND external_id=?",
        (job.source, job.external_id),
    ).fetchone()
    if row is None:
        raise RuntimeError("Job upsert completed without returning an id")
    return int(row["id"])


def list_jobs(
    conn: sqlite3.Connection,
    *,
    status: ApplicationStatus | None = None,
    min_score: int = 0,
    limit: int = 200,
) -> list[sqlite3.Row]:
    clauses = ["score >= ?"]
    params: list[object] = [min_score]
    if status is not None:
        clauses.append("status = ?")
        params.append(status.value)
    params.append(limit)
    sql = (
        "SELECT * FROM job_postings WHERE "
        + " AND ".join(clauses)
        + " ORDER BY score DESC, created_at DESC LIMIT ?"
    )
    return list(conn.execute(sql, params))


def get_job(conn: sqlite3.Connection, job_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM job_postings WHERE id=?", (job_id,)).fetchone()
    if row is None:
        raise JobNotFoundError(f"Unknown job id {job_id}")
    return row


def change_status(
    conn: sqlite3.Connection,
    job_id: int,
    target: ApplicationStatus,
    notes: str = "",
) -> sqlite3.Row:
    row = get_job(conn, job_id)
    current = ApplicationStatus(row["status"])
    try:
        assert_transition(current, target)
    except ValueError as exc:
        raise InvalidTransitionError(str(exc)) from exc
    conn.execute(
        """
        UPDATE job_postings
        SET status=?, notes=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        """,
        (target.value, notes, job_id),
    )
    return get_job(conn, job_id)


def log_run(conn: sqlite3.Connection, kind: str, message: str) -> None:
    conn.execute(
        "INSERT INTO run_logs (kind, message) VALUES (?, ?)",
        (kind, message),
    )
