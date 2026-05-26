"""SIEM forwarding helpers."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


class WebhookForwarder:
    def __init__(self, url: Optional[str] = None) -> None:
        self.url = url or os.environ.get('SIEM_WEBHOOK_URL')

    def send(self, event: Dict[str, Any]) -> bool:
        if not self.url:
            return False
        if not _HAS_REQUESTS:
            return False
        try:
            response = requests.post(self.url, json=event, timeout=10)
            return response.status_code in (200, 201, 202)
        except Exception:
            return False


def build_siem_event(report: Dict[str, Any], source: str = 'deployment_checker') -> Dict[str, Any]:
    return {
        'source': source,
        'timestamp': report.get('timestamp'),
        'hostname': report.get('hostname'),
        'verdict': report.get('verdict'),
        'summary': report.get('summary', {}),
        'checks': report.get('checks', []),
    }
