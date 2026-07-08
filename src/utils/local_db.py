"""Local SQLite persistence for the desktop assessment tool.

Stores completed assessments in a small database under the user's home
directory so results survive between sessions without requiring a server.
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional

# Env override for the database location. Tests set this to a temp file so
# they never touch the real user database; leave it unset in normal use.
DB_PATH_ENV = "ZDH_DB_PATH"


def _db_path() -> Path:
    """Return the path for the local database.

    Honours the ``ZDH_DB_PATH`` environment variable (used by tests) and
    otherwise falls back to a per-user location under the OS data directory.
    """
    override = os.environ.get(DB_PATH_ENV)
    if override:
        p = Path(override)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".local" / "share"
    folder = base / "ZambiaDigitalHygiene"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "history.db"


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, and ALWAYS close it.

    ``with sqlite3.connect(...) as conn`` only manages the transaction — it
    does not close the connection, which leaks handles. This wrapper closes
    the connection in every case.
    """
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the assessments table if it does not exist."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                saved_at    TEXT    NOT NULL,
                biz_name    TEXT    NOT NULL,
                biz_id      TEXT    NOT NULL,
                province    TEXT,
                industry    TEXT,
                score       INTEGER NOT NULL,
                total       INTEGER NOT NULL,
                pct         INTEGER NOT NULL,
                tier        TEXT    NOT NULL,
                payload     TEXT    NOT NULL
            )
        """)
        conn.commit()


def save_assessment(result: Any) -> int:
    """Persist a completed AssessmentResult and return the new row id."""
    init_db()
    pct = round((result.score / result.total_possible) * 100) if result.total_possible else 0
    payload = {
        "business": {
            "name": result.business_info.name,
            "id": result.business_info.id,
            "province": getattr(result.business_info, "province", ""),
            "industry": getattr(result.business_info, "industry", ""),
            "contact_person": getattr(result.business_info, "contact_person", None),
        },
        "assessment_date": result.assessment_date.isoformat(),
        "score": result.score,
        "total_possible": result.total_possible,
        "percentage": pct,
        "certification_level": result.certification_level,
        "critical_failures": result.critical_failures,
        "controls": {
            k: {
                "id": v.control_id,
                "name": v.name,
                "status": v.status,
                "score": v.score,
                "weight": v.weight,
                "details": v.details,
            }
            for k, v in result.controls.items()
        },
        "recommendations": result.recommendations,
    }
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO assessments
               (saved_at, biz_name, biz_id, province, industry,
                score, total, pct, tier, payload)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                datetime.now().isoformat(timespec="seconds"),
                result.business_info.name,
                result.business_info.id,
                getattr(result.business_info, "province", ""),
                getattr(result.business_info, "industry", ""),
                result.score,
                result.total_possible,
                pct,
                result.certification_level,
                json.dumps(payload),
            ),
        )
        conn.commit()
        return cur.lastrowid or 0


def list_assessments(limit: int = 50) -> list[dict[str, Any]]:
    """Return summary rows (no full payload) ordered newest first."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """SELECT id, saved_at, biz_name, biz_id, province,
                      industry, score, total, pct, tier
               FROM assessments
               ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_assessment(row_id: int) -> Optional[dict[str, Any]]:
    """Return the full payload for a single assessment row."""
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT payload FROM assessments WHERE id = ?", (row_id,)
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["payload"])


def delete_assessment(row_id: int) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM assessments WHERE id = ?", (row_id,))
        conn.commit()


def assessment_count() -> int:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) FROM assessments").fetchone()
    return row[0] if row else 0


# ── Credentials ──────────────────────────────────────────────────────────────

def _ensure_credentials_table() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.commit()


def is_credentials_setup() -> bool:
    """Return True if root credentials have been saved."""
    try:
        _ensure_credentials_table()
        with _connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM credentials WHERE key = 'username'"
            ).fetchone()
        return row is not None
    except Exception:
        return False


def store_credentials(username: str, password_hash: str) -> None:
    """Persist username and pre-hashed password."""
    _ensure_credentials_table()
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO credentials (key, value) VALUES ('username', ?)",
            (username,),
        )
        conn.execute(
            "INSERT OR REPLACE INTO credentials (key, value) VALUES ('password_hash', ?)",
            (password_hash,),
        )
        conn.commit()


def get_credential(key: str) -> str:
    """Return a stored credential value by key, or empty string."""
    try:
        _ensure_credentials_table()
        with _connect() as conn:
            row = conn.execute(
                "SELECT value FROM credentials WHERE key = ?", (key,)
            ).fetchone()
        return row[0] if row else ""
    except Exception:
        return ""


# ── Agent reports ─────────────────────────────────────────────────────────────

def _ensure_agent_reports_table() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_reports (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname     TEXT    NOT NULL,
                collected_at TEXT    NOT NULL,
                payload      TEXT    NOT NULL
            )
        """)
        conn.commit()


def save_agent_report(report: dict) -> int:
    """Persist an agent report and return the new row id."""
    _ensure_agent_reports_table()
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO agent_reports (hostname, collected_at, payload)
               VALUES (?, ?, ?)""",
            (
                report.get("hostname", ""),
                report.get("collected_at", ""),
                json.dumps(report),
            ),
        )
        conn.commit()
        return cur.lastrowid or 0


def load_agent_report(report_id: int) -> Optional[dict]:
    """Return the full agent report for the given id, or None."""
    _ensure_agent_reports_table()
    with _connect() as conn:
        row = conn.execute(
            "SELECT payload FROM agent_reports WHERE id = ?", (report_id,)
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["payload"])


def list_agent_reports(limit: int = 50) -> list[dict]:
    """Return summary rows ordered newest first."""
    _ensure_agent_reports_table()
    with _connect() as conn:
        rows = conn.execute(
            """SELECT id, hostname, collected_at
               FROM agent_reports ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Fleet reports (distributed multi-node scans) ─────────────────────────────

def _ensure_fleet_reports_table() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fleet_reports (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                scanned_at  TEXT    NOT NULL,
                fleet_grade TEXT    NOT NULL,
                total_nodes INTEGER NOT NULL,
                online      INTEGER NOT NULL,
                payload     TEXT    NOT NULL
            )
        """)
        conn.commit()


def save_fleet_report(report: dict) -> int:
    """Persist a fleet report (already a to_dict() mapping) and return row id."""
    _ensure_fleet_reports_table()
    summary = report.get("summary", {})
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO fleet_reports
               (scanned_at, fleet_grade, total_nodes, online, payload)
               VALUES (?, ?, ?, ?, ?)""",
            (
                report.get("scanned_at", ""),
                report.get("fleet_grade", ""),
                summary.get("total_nodes", 0),
                summary.get("online", 0),
                json.dumps(report),
            ),
        )
        conn.commit()
        return cur.lastrowid or 0


def load_fleet_report(report_id: int) -> Optional[dict]:
    """Return the full fleet report for the given id, or None."""
    _ensure_fleet_reports_table()
    with _connect() as conn:
        row = conn.execute(
            "SELECT payload FROM fleet_reports WHERE id = ?", (report_id,)
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["payload"])


def list_fleet_reports(limit: int = 50) -> list[dict]:
    """Return fleet report summary rows ordered newest first."""
    _ensure_fleet_reports_table()
    with _connect() as conn:
        rows = conn.execute(
            """SELECT id, scanned_at, fleet_grade, total_nodes, online
               FROM fleet_reports ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Reassessment reminder ────────────────────────────────────────────────────

def _ensure_settings_table() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.commit()


def set_reassessment_date(date_str: str) -> None:
    """Store a reassessment due date (ISO format YYYY-MM-DD)."""
    _ensure_settings_table()
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('reassessment_due', ?)",
            (date_str,),
        )
        conn.commit()


def get_reassessment_date():
    """Return the reassessment due date as a datetime.date, or None."""
    import datetime
    try:
        _ensure_settings_table()
        with _connect() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = 'reassessment_due'"
            ).fetchone()
        if row:
            return datetime.date.fromisoformat(row[0])
    except Exception:
        pass
    return None


# ── Generic application settings (key/value) ─────────────────────────────────

def set_setting(key: str, value: Any) -> None:
    """Persist an application setting. Booleans/ints are stored as text."""
    _ensure_settings_table()
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, "" if value is None else str(value)),
        )


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Return a stored setting as a string, or ``default`` if unset."""
    try:
        _ensure_settings_table()
        with _connect() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        return row[0] if row is not None else default
    except Exception:
        return default


def get_bool_setting(key: str, default: bool = False) -> bool:
    raw = get_setting(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def get_int_setting(key: str, default: int = 0) -> int:
    raw = get_setting(key)
    try:
        return int(raw) if raw is not None and raw != "" else default
    except (TypeError, ValueError):
        return default


def get_all_settings() -> dict[str, str]:
    """Return every stored setting as a dict."""
    try:
        _ensure_settings_table()
        with _connect() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}
    except Exception:
        return {}


def agent_report_count() -> int:
    _ensure_agent_reports_table()
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) FROM agent_reports").fetchone()
    return row[0] if row else 0


def fleet_report_count() -> int:
    _ensure_fleet_reports_table()
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) FROM fleet_reports").fetchone()
    return row[0] if row else 0


def clear_history() -> None:
    """Delete all saved assessments, agent reports and fleet reports.

    Credentials and settings are preserved. Used by Settings → Storage.
    """
    init_db()
    _ensure_agent_reports_table()
    _ensure_fleet_reports_table()
    with _connect() as conn:
        conn.execute("DELETE FROM assessments")
        conn.execute("DELETE FROM agent_reports")
        conn.execute("DELETE FROM fleet_reports")


def db_location() -> str:
    """Return the filesystem path of the local database."""
    return str(_db_path())
