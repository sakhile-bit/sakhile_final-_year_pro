#!/usr/bin/env python3
"""
Windows desktop entry point.

Run from the project root:
    python windows_app.py

Or as a compiled .exe built by PyInstaller:
    dist\\ZambiaDigitalHygiene.exe
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so all src.* imports resolve.
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.gui.app import DigitalHygieneApp

if __name__ == "__main__":
    app = DigitalHygieneApp()
    app.mainloop()
