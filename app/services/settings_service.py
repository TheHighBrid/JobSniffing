from __future__ import annotations

import json
import sqlite3

from app.domain.enums import AutomationMode
from app.domain.schemas import AutomationSettings, ScoringSettings
from app.services.scoring_service import DEFAULT_EXCLUDED_TERMS, DEFAULT_PREFERRED_TERMS

DEFAULT_SETTINGS = ScoringSettings(preferred_terms=DEFAULT_PREFERRED_TERMS, excluded_terms=DEFAULT_EXCLUDED_TERMS, blacklisted_companies=[], minimum_score=0)


def _read(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM settings_kv WHERE key=?", (key,)).fetchone()
    return str(row["value"]) if row else None


def _write(conn: sqlite3.Connection, key: str, value: object) -> None:
    conn.execute("INSERT INTO settings_kv(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP", (key, json.dumps(value, ensure_ascii=False, sort_keys=True)))


def load_scoring_settings(conn: sqlite3.Connection) -> ScoringSettings:
    preferred, excluded = _read(conn, "preferred_terms"), _read(conn, "excluded_terms")
    blocked, minimum = _read(conn, "blacklisted_companies"), _read(conn, "minimum_score")
    return ScoringSettings(
        preferred_terms=json.loads(preferred) if preferred else DEFAULT_SETTINGS.preferred_terms,
        excluded_terms=json.loads(excluded) if excluded else DEFAULT_SETTINGS.excluded_terms,
        blacklisted_companies=json.loads(blocked) if blocked else [],
        minimum_score=json.loads(minimum) if minimum else 0,
    )


def save_scoring_settings(conn: sqlite3.Connection, settings: ScoringSettings) -> None:
    _write(conn, "preferred_terms", settings.preferred_terms)
    _write(conn, "excluded_terms", settings.excluded_terms)
    _write(conn, "blacklisted_companies", settings.blacklisted_companies)
    _write(conn, "minimum_score", settings.minimum_score)


def is_blacklisted(company: str, settings: ScoringSettings) -> bool:
    normalized = company.strip().lower()
    return any(entry == normalized or entry in normalized for entry in settings.blacklisted_companies)


def load_automation_settings(conn: sqlite3.Connection) -> AutomationSettings:
    mode = _read(conn, "automation_mode")
    daily_cap = _read(conn, "automation_daily_cap")
    delay = _read(conn, "automation_min_delay_seconds")
    return AutomationSettings(
        mode=AutomationMode(json.loads(mode)) if mode else AutomationMode.MANUAL,
        daily_cap=json.loads(daily_cap) if daily_cap else 0,
        min_delay_seconds=json.loads(delay) if delay else 0,
    )


def save_automation_settings(conn: sqlite3.Connection, settings: AutomationSettings) -> None:
    _write(conn, "automation_mode", settings.mode.value)
    _write(conn, "automation_daily_cap", settings.daily_cap)
    _write(conn, "automation_min_delay_seconds", settings.min_delay_seconds)
