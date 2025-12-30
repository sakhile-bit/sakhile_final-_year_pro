#!/usr/bin/env python3
"""
Main entry point for Zambia Digital Hygiene Assessment Tool
"""

import sys
from pathlib import Path

# Add src directory to path for proper imports
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from utils.cli import cli

if __name__ == "__main__":
    cli()
