from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_VERSION = "0.2.0"


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def get_db_path() -> Path:
    return resolve_project_path(os.getenv("JOBSNIFFING_DB", "data/jobsniffing.sqlite3"))
