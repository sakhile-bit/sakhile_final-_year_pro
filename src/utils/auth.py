"""Local credential store for the desktop app.

Credentials are stored as a hashed password in instance/credentials.json.
werkzeug.security handles the hashing — same library used by the web app.
"""
from __future__ import annotations

import json
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

_CRED_FILE = Path(__file__).resolve().parent.parent.parent / "instance" / "credentials.json"


def is_setup() -> bool:
    """Return True if root credentials have already been created."""
    return _CRED_FILE.exists()


def save_credentials(username: str, password: str) -> None:
    """Hash and persist credentials. Creates instance/ if needed."""
    _CRED_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "username": username,
        "password_hash": generate_password_hash(password),
    }
    _CRED_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def verify(username: str, password: str) -> bool:
    """Return True if username + password match stored credentials."""
    if not _CRED_FILE.exists():
        return False
    try:
        data = json.loads(_CRED_FILE.read_text(encoding="utf-8"))
        return (
            data.get("username") == username
            and check_password_hash(data["password_hash"], password)
        )
    except Exception:
        return False


def get_username() -> str:
    """Return the stored username, or empty string if not set up."""
    if not _CRED_FILE.exists():
        return ""
    try:
        return json.loads(_CRED_FILE.read_text(encoding="utf-8")).get("username", "")
    except Exception:
        return ""
