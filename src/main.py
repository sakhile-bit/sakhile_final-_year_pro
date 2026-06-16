#!/usr/bin/env python3
"""
Main entry point for Zambia Digital Hygiene Assessment Tool

Usage (from project root):
    python src/main.py [COMMAND] [OPTIONS]
    python cli.py [COMMAND] [OPTIONS]      (convenience wrapper)
"""

import sys
from pathlib import Path

# Add the PROJECT ROOT (parent of src/) to sys.path so that
# ``import src.assessment.assessor`` etc. resolve correctly everywhere.
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.cli import cli  # noqa: E402

if __name__ == "__main__":
    cli()
