"""Remote report collector

Helpers to load agent reports stored in the local SQLite database and convert
them into structures that can be merged with the `DigitalHygieneAssessor`
or presented in the web UI.
"""
from __future__ import annotations

from typing import Dict, Any

from src.utils.local_db import (
    load_agent_report as _db_load,
    list_agent_reports as _db_list,
)


def load_agent_report(report_id: int) -> Dict[str, Any]:
    report = _db_load(report_id)
    if report is None:
        raise KeyError(f"No agent report with id {report_id}")
    return report


def list_agent_reports(limit: int = 50) -> list[Dict[str, Any]]:
    return _db_list(limit)


def summarize_agent_report(report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'hostname': report.get('hostname'),
        'collected_at': report.get('collected_at'),
        'assessment_score': report.get('assessment', {}).get('score'),
        'cert_level': report.get('assessment', {}).get('certification_level'),
        'readiness_verdict': report.get('readiness', {}).get('verdict'),
    }
