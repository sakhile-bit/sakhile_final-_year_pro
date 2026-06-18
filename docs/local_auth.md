# Local Authentication — Desktop App Login Gate

**Feature:** Root account setup and login gate for the Windows desktop app  
**Files added:**
- `src/utils/auth.py` — credential storage and verification
- `src/gui/screens/setup_screen.py` — first-run account creation screen
- `src/gui/screens/login_screen.py` — login screen for subsequent launches

**Files modified:**
- `src/gui/app.py` — routes through auth before showing the welcome screen
- `devops/build.spec` — bundles new modules into the `.exe`

---

## Overview

On first launch, instead of opening directly into the app, users are required to create a **root account** (username + password). Every subsequent launch shows a **login screen** — the app only opens after successful authentication.

This mirrors the MySQL first-run setup model: credentials are created once and required on every session.

---

## User Flow

### First Launch — Setup Screen

```
ZambiaDigitalHygiene.exe launched
        │
        ▼
  credentials row in SQLite?
        │
       NO
        │
        ▼
  ┌─────────────────────────────┐
  │   First-Time Setup Screen   │
  │                             │
  │  Username:  [____________]  │
  │  Password:  [············]  │
  │             ████░░  Good    │  ← live strength meter
  │  Confirm:   [············]  │
  │                             │
  │  [Create Account & Continue]│
  └─────────────────────────────┘
        │
        ▼
  Credentials saved to SQLite
  (hashed password stored)
        │
        ▼
  Welcome screen opens
```

### Subsequent Launches — Login Screen

```
ZambiaDigitalHygiene.exe launched
        │
        ▼
  credentials row in SQLite?
        │
       YES
        │
        ▼
  ┌─────────────────────────────┐
  │       Login Screen          │
  │                             │
  │  Username:  [admin    ] ←disabled (pre-filled)  │
  │  Password:  [············]  │
  │                             │
  │        [Sign In →]          │
  └─────────────────────────────┘
        │
   ┌────┴─────────────┐
  PASS              FAIL (×5 max)
   │                    │
   ▼                    ▼
  Welcome screen    App closes automatically
```

---

## Security Details

### Password Requirements (Setup)

| Rule | Minimum |
|------|---------|
| Length | 8 characters |
| Username length | 3 characters |
| Strength feedback | Live meter (Too short / Weak / Fair / Good / Strong) |

### Password Strength Scoring

The strength meter scores 0–4 based on:

| Criterion | Points |
|-----------|--------|
| Length ≥ 8 characters | +1 |
| Contains uppercase letter (A–Z) | +1 |
| Contains digit (0–9) | +1 |
| Contains special character (!@#$ etc.) | +1 |

| Score | Label | Colour |
|-------|-------|--------|
| 0 | Too short | Red |
| 1 | Weak | Red |
| 2 | Fair | Orange |
| 3 | Good | Yellow |
| 4 | Strong | Green |

### Login Lockout

- Maximum **5 failed attempts** before the app closes automatically
- Remaining attempts are shown after each wrong password
- Password field is cleared after each failed attempt

### Credential Storage

Credentials are saved to the local SQLite database in the `credentials` table:

```
%APPDATA%\ZambiaDigitalHygiene\history.db
```

| key | value |
|---|---|
| `username` | Plain username string |
| `password_hash` | PBKDF2-SHA256 hash |

- **Location:** `history.db` — `credentials` table (same database used for assessment history)
- **Hashing:** `werkzeug.security.generate_password_hash` — PBKDF2-SHA256
- **Plain text:** Never stored — only the hash is persisted
- **Scope:** Local machine only — not synced, not sent anywhere

---

## File Reference

### `src/utils/auth.py`

| Function | Description |
|----------|-------------|
| `is_setup() → bool` | Returns `True` if a credentials row exists in SQLite |
| `save_credentials(username, password)` | Hashes password and upserts into SQLite |
| `verify(username, password) → bool` | Returns `True` if credentials match stored hash |
| `get_username() → str` | Returns stored username for display on login screen |

### `src/gui/screens/setup_screen.py`

`SetupScreen(master, on_done: callable)`

Displayed when `is_setup()` is `False`. Calls `on_done()` after credentials are created successfully.

### `src/gui/screens/login_screen.py`

`LoginScreen(master, on_success: callable)`

Displayed when `is_setup()` is `True`. Calls `on_success()` after the correct password is entered. Closes the app after 5 failed attempts.

### `src/gui/app.py` — Auth routing (added to `__init__`)

```python
from src.utils.auth import is_setup

if is_setup():
    self._show_login()   # credentials exist → ask for password
else:
    self._show_setup()   # first run → create root account
```

---

## Resetting the Root Password

If a user forgets their password, delete the credentials rows from `history.db` and the app will restart in first-run setup mode:

```python
from src.utils.local_db import _connect

with _connect() as conn:
    conn.execute("DELETE FROM credentials")
    conn.commit()
```

Or delete the entire database file to reset all local state (assessments, credentials, agent reports, settings):

**Windows path:**
```
%APPDATA%\ZambiaDigitalHygiene\history.db
```

After deletion, the next launch shows the setup screen again.

---

## Adding a "Change Password" Option

To let users change their password from inside the app (e.g. from the Settings screen), call:

```python
from src.utils.auth import save_credentials

# Overwrites the existing credentials.json with new hash
save_credentials(new_username, new_password)
```

The `save_credentials()` function always overwrites — calling it with new values is all that's needed.

---

## References

- [werkzeug.security — Password Hashing](https://werkzeug.palletsprojects.com/en/latest/utils/#werkzeug.security.generate_password_hash)
- [PBKDF2 — NIST SP 800-132](https://csrc.nist.gov/publications/detail/sp/800-132/final)
- CIS Controls v8 — Control 5: Account Management
- NIST CSF — PR.AC-1: Identities and credentials are managed
