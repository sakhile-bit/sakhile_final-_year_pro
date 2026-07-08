#!/usr/bin/env python3
"""
Convenience CLI entry-point for the Zambia Digital Hygiene Assessment Tool.

Run from the project root:
    python cli.py --help
    python cli.py assess --business-name "Acme Ltd" --business-id REG-001
    python cli.py scan
    python cli.py zambia
    python cli.py predeploy
    python cli.py harden                       # infrastructure hardening audit
    python cli.py web --debug
    python cli.py users list
    python cli.py users create
    python cli.py init-db
    python cli.py manual
    python cli.py status

Agents (distributed / local scanning):
    python cli.py agent                        # scan THIS host once (assessment + hardening)
    python cli.py agent --json-out -o host.json
    python cli.py agent-reports                # list saved agent reports
    python cli.py agent-reports --show 3       # print one report as JSON

    # On each node you want a master to scan:
    python cli.py node-agent --port 8765 --token <secret>

    # On the master node, scan the whole fleet:
    python cli.py fleet-scan --nodes nodes.yaml
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
