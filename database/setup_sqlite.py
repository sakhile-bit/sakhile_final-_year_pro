#!/usr/bin/env python3
"""
Self-contained SQLite database setup for the Zambia Digital Hygiene tool.

This is the SQLite counterpart to ``setup_mysql.py``. It creates the web
portal's SQLite database (``instance/digital_hygiene.db``) from
``schema_sqlite.sql`` — no server required.

Usage
-----
    python database/setup_sqlite.py            # create/verify the schema
    python database/setup_sqlite.py --reset    # delete and recreate

After running this, create the admin account (with a strong random password)::

    python cli.py init-db

Note: the *desktop* application's local store
(``%APPDATA%\\ZambiaDigitalHygiene\\history.db``) is created automatically at
runtime by ``src/utils/local_db.py`` and needs no setup — see
``schema_sqlite_local.sql`` for its reference schema.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

# Project root = parent of the database/ directory
ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = Path(__file__).resolve().parent / "schema_sqlite.sql"
DB_DIR = ROOT / "instance"
DB_PATH = DB_DIR / "digital_hygiene.db"


def setup(reset: bool = False) -> int:
    if not SCHEMA_FILE.exists():
        print(f"[ERROR] Schema file not found: {SCHEMA_FILE}")
        return 1

    DB_DIR.mkdir(parents=True, exist_ok=True)

    if reset and DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[reset] Removed existing database: {DB_PATH}")

    schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")

    print("Setting up self-contained SQLite database…")
    print(f"  Schema:   {SCHEMA_FILE.name}")
    print(f"  Database: {DB_PATH}")

    try:
        conn = sqlite3.connect(str(DB_PATH))
        try:
            conn.executescript(schema_sql)
            conn.commit()
            tables = [
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "ORDER BY name"
                ).fetchall()
            ]
        finally:
            conn.close()
    except sqlite3.Error as exc:
        print(f"[ERROR] Failed to apply schema: {exc}")
        return 1

    print(f"  Tables:   {', '.join(tables)}")
    print("\n[OK] SQLite database ready.")
    print("     Next: run  python cli.py init-db  to create the admin user.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create the self-contained SQLite database")
    parser.add_argument("--reset", action="store_true",
                        help="Delete and recreate the database")
    args = parser.parse_args()
    return setup(reset=args.reset)


if __name__ == "__main__":
    sys.exit(main())
