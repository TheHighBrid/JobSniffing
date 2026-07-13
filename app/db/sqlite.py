import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DB_PATH = "data/jobsniffing.sqlite3"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS job_postings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  location TEXT NOT NULL DEFAULT '',
  apply_url TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  score INTEGER NOT NULL DEFAULT 0 CHECK(score BETWEEN 0 AND 100),
  status TEXT NOT NULL DEFAULT 'discovered',
  notes TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source, external_id)
);
CREATE INDEX IF NOT EXISTS idx_job_postings_status_score
  ON job_postings(status, score DESC);
CREATE TABLE IF NOT EXISTS answer_bank (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question TEXT NOT NULL UNIQUE,
  answer TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS run_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def configured_db_path() -> Path:
    return Path(os.getenv("JOBSNIFFING_DB", DEFAULT_DB_PATH)).expanduser()


def connect(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or configured_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db(path: Path | None = None) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def session(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    conn = connect(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
