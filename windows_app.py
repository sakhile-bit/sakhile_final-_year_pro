#!/usr/bin/env python3
"""
Windows desktop entry point.

Run from the project root:
    python windows_app.py

Or as a compiled .exe built by PyInstaller:
    dist\\ZambiaDigitalHygiene.exe
"""

import subprocess
import sys
import traceback
import tkinter.messagebox as _mb
from pathlib import Path

# This is a windowed app: every console child process (powershell, netsh,
# ping, sc, …) would otherwise flash its own console window during scans.
# Force CREATE_NO_WINDOW on all subprocesses so features show only their
# own progress UI.
if sys.platform == "win32":
    _orig_popen_init = subprocess.Popen.__init__

    def _no_window_init(self, *args, **kwargs):
        kwargs["creationflags"] = (kwargs.get("creationflags") or 0) \
            | subprocess.CREATE_NO_WINDOW
        _orig_popen_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = _no_window_init

# Ensure the src package is importable in both modes:
#  - frozen .exe: PyInstaller extracts the bundle (incl. src/) to _MEIPASS
#  - from source: the project root is this file's directory
if getattr(sys, "frozen", False):
    project_root = getattr(sys, "_MEIPASS", str(Path(sys.executable).parent))
else:
    project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def _show_error(exc_type, exc_value, exc_tb):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        _mb.showerror("Unhandled Error", msg)
    except Exception:
        # No display available (e.g. Tk already torn down) — log instead.
        import logging
        logging.getLogger("windows_app").error("Unhandled error:\n%s", msg)


sys.excepthook = _show_error

from src.gui.app import DigitalHygieneApp  # noqa: E402 — needs sys.path set up first

if __name__ == "__main__":
    app = DigitalHygieneApp()
    app.report_callback_exception = lambda *args: _show_error(*args)
    app.mainloop()
