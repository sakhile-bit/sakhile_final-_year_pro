#!/usr/bin/env python3
"""
Convenience CLI entry-point for the Zambia Digital Hygiene Assessment Tool.

Run from the project root:
    python cli.py --help
    python cli.py assess --business-name "Acme Ltd" --business-id REG-001
    python cli.py scan
    python cli.py zambia
    python cli.py predeploy
    python cli.py web --debug
    python cli.py users list
    python cli.py users create
    python cli.py init-db
    python cli.py manual
    python cli.py status
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.cli import cli

if __name__ == "__main__":
    cli()
