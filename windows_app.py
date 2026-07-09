#!/usr/bin/env python3
"""
Windows desktop entry point.

Run from the project root:
    python windows_app.py

Or as a compiled .exe built by PyInstaller:
    dist\\ZambiaDigitalHygiene.exe
"""

import sys
import traceback
import tkinter.messagebox as _mb
from pathlib import Path

# Ensure project root is on sys.path so all src.* imports resolve.
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
