"""Local credential store for the desktop app.

Credentials are stored in the local SQLite database (local_db) rather than a
JSON file so all persistent state lives in one place.
"""
from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

from src.utils.local_db import (
    get_credential,
    is_credentials_setup,
    store_credentials,
)


def is_setup() -> bool:
    """Return True if root credentials have already been created."""
    return is_credentials_setup()


def save_credentials(username: str, password: str) -> None:
    """Hash and persist credentials."""
    store_credentials(username, generate_password_hash(password))


def verify(username: str, password: str) -> bool:
    """Return True if username + password match stored credentials."""
    try:
        stored_user = get_credential("username")
        stored_hash = get_credential("password_hash")
        if not stored_user or not stored_hash:
            return False
        return stored_user == username and check_password_hash(stored_hash, password)
    except Exception:
        return False


def get_username() -> str:
    """Return the stored username, or empty string if not set up."""
    return get_credential("username")
