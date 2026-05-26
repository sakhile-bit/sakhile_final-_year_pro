"""Remote report collector

Helpers to load agent JSON reports produced by the Windows agent and convert
them into structures that can be merged with the `DigitalHygieneAssessor`
or presented in the web UI.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


def load_agent_report(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text())


def summarize_agent_report(report: Dict[str, Any]) -> Dict[str, Any]:
    # Minimal summarisation for UI ingestion
    return {
        'hostname': report.get('hostname'),
        'collected_at': report.get('collected_at'),
        'assessment_score': report.get('assessment', {}).get('score'),
        'cert_level': report.get('assessment', {}).get('certification_level'),
        'readiness_verdict': report.get('readiness', {}).get('verdict'),
    }
