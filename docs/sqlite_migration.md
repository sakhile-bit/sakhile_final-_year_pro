# SQLite Migration — Replacing JSON File Storage

**Date:** 2026-06-18
**Author:** Development Session (Claude Code)
**Branch:** main

---

## Overview

All persistent local state that was previously written to JSON files on disk has been moved into the existing local SQLite database (`history.db`). Every read and write that previously touched a `.json` file in the `instance/` directory now goes through `src/utils/local_db.py` instead.

---

## What Changed

### Before

| Data | Location | Format |
|---|---|---|
| Desktop login credentials | `instance/credentials.json` | JSON file |
| Windows agent scan reports | `instance/agent_reports/<hostname>-<timestamp>.json` | JSON files |

### After

| Data | Location | Format |
|---|---|---|
| Desktop login credentials | `history.db` → `credentials` table | SQLite |
| Windows agent scan reports | `history.db` → `agent_reports` table | SQLite |

The `instance/agent_reports/` directory and `instance/credentials.json` file are no longer created or read by the application.

---

## Database Schema Additions

Two new tables are added to `history.db` on first use (auto-created by `CREATE TABLE IF NOT EXISTS`):

### `credentials`

```sql
CREATE TABLE IF NOT EXISTS credentials (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

Rows stored:

| key | value |
|---|---|
| `username` | Plain username string |
| `password_hash` | PBKDF2-SHA256 hash from `werkzeug.security` |

### `agent_reports`

```sql
CREATE TABLE IF NOT EXISTS agent_reports (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname     TEXT    NOT NULL,
    collected_at TEXT    NOT NULL,
    payload      TEXT    NOT NULL
);
```

`payload` stores the full report dict serialised as JSON. The `hostname` and `collected_at` columns are promoted as top-level fields for fast listing without deserialising the payload.

---

## File-by-File Changes

### `src/utils/local_db.py` — New functions added

**Credentials:**

| Function | Description |
|---|---|
| `is_credentials_setup() → bool` | Returns `True` if a `username` row exists in `credentials` |
| `store_credentials(username, password_hash)` | Upserts both rows in `credentials` |
| `get_credential(key) → str` | Returns a single credential value by key, or `""` |

**Agent reports:**

| Function | Description |
|---|---|
| `save_agent_report(report: dict) → int` | Inserts a report and returns the new row id |
| `load_agent_report(report_id: int) → dict \| None` | Returns the full report by id, or `None` |
| `list_agent_reports(limit=50) → list[dict]` | Returns summary rows (id, hostname, collected_at) newest first |

---

### `src/utils/auth.py` — Rewritten

Credential persistence delegated entirely to `local_db`. The JSON file path logic, `pathlib`, and `json` imports have been removed.

| Function | Before | After |
|---|---|---|
| `is_setup()` | Checked `instance/credentials.json` exists | Calls `local_db.is_credentials_setup()` |
| `save_credentials(u, p)` | Wrote `credentials.json` | Calls `local_db.store_credentials(u, hash)` |
| `verify(u, p)` | Read and parsed `credentials.json` | Calls `local_db.get_credential(...)` |
| `get_username()` | Read and parsed `credentials.json` | Calls `local_db.get_credential("username")` |

---

### `src/agents/windows_agent.py` — Report storage updated

The `REPORT_DIR` constant and all directory/file creation logic have been removed. After building the report dict, the agent now calls `local_db.save_agent_report(out)` and returns the integer row id.

**Return value change:**

```python
# Before
{"report_path": "instance/agent_reports/HOSTNAME-1234567890.json", "report": {...}}

# After
{"report_id": 42, "report": {...}}
```

---

### `src/security/assessment/remote_collector.py` — Signature updated

`load_agent_report` now takes an integer id instead of a file path string.

```python
# Before
def load_agent_report(path: str) -> Dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text())

# After
def load_agent_report(report_id: int) -> Dict[str, Any]:
    report = _db_load(report_id)
    if report is None:
        raise KeyError(f"No agent report with id {report_id}")
    return report
```

`list_agent_reports(limit=50)` has also been added as a new helper.

---

### `tests/test_windows_agent.py` — Assertion updated

```python
# Before
assert 'report_path' in r

# After
assert 'report_id' in r
```

---

## Resetting Credentials

Previously, resetting credentials meant deleting `instance/credentials.json`. With SQLite, delete the relevant rows from `history.db`:

```python
from src.utils.local_db import _connect

with _connect() as conn:
    conn.execute("DELETE FROM credentials")
    conn.commit()
```

Or delete the entire database file to reset all local state (assessments, credentials, agent reports, settings):

```
%APPDATA%\ZambiaDigitalHygiene\history.db
```

After deletion the next launch shows the first-run setup screen.

---

## Migration from Existing Installations

If an existing installation has `instance/credentials.json` on disk, it will be silently ignored — the app will show the first-run setup screen and the user will need to create a new root account. The old JSON file can be deleted manually.

Existing assessment history in `history.db` is unaffected — only new tables were added.

---

## References

- `src/utils/local_db.py` — central SQLite module
- `src/utils/auth.py` — credential API (no file I/O)
- `src/agents/windows_agent.py` — agent report collection
- `src/security/assessment/remote_collector.py` — report loading
- `docs/local_auth.md` — auth flow documentation (updated)
