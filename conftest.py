"""
Pytest session bootstrap — isolate the test run from real data.

This module is imported by pytest before any test (or application) module,
so the environment is prepared *first*:

* The desktop SQLite store is redirected to a throwaway temp file via
  ``ZDH_DB_PATH`` — tests never read or write the developer's real
  ``%APPDATA%/ZambiaDigitalHygiene/history.db``.
* The web application is pinned to a throwaway SQLite database via
  ``DATABASE_URL`` — importing ``src.web.app`` never probes or mutates the
  developer's MySQL server.

Without this, running the suite would pollute the real local database (e.g.
a ``test-local`` agent report) and depend on a live MySQL instance.
"""
import atexit
import os
import shutil
import tempfile
from pathlib import Path

_TMP_DIR = Path(tempfile.mkdtemp(prefix="zdh_tests_"))

# Desktop local store → temp file (honoured by src/utils/local_db._db_path)
os.environ["ZDH_DB_PATH"] = str(_TMP_DIR / "history.db")

# Web app → throwaway SQLite so importing src.web.app never touches MySQL
os.environ["DATABASE_URL"] = "sqlite:///" + str(_TMP_DIR / "web.db")


@atexit.register
def _cleanup_tmp() -> None:
    shutil.rmtree(_TMP_DIR, ignore_errors=True)
