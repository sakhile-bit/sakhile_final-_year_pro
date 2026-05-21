"""Local SQLite persistence for the desktop assessment tool.

Stores completed assessments in a small database under the user's home
directory so results survive between sessions without requiring a server.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def _db_path() -> Path:
    """Return platform-appropriate path for the local database."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".local" / "share"
    folder = base / "ZambiaDigitalHygiene"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "history.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    return conn


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
