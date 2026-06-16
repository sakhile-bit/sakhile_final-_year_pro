# Feature: SIEM Forwarder

## Overview
The SIEM Forwarder sends assessment and deployment-checker results to an external **Security Information and Event Management (SIEM)** system via an HTTP webhook. Any SIEM that accepts JSON POST payloads (Splunk HEC, Elastic, Wazuh, Graylog, etc.) is supported.

**File:** [`src/security/siem/forwarder.py`](../../src/security/siem/forwarder.py)

---

## Classes & Functions

### `WebhookForwarder`

```python
class WebhookForwarder:
    def __init__(self, url: Optional[str] = None) -> None
    def send(self, event: Dict[str, Any]) -> bool
```

| Parameter | Description |
|---|---|
| `url` | Webhook endpoint URL. Falls back to `SIEM_WEBHOOK_URL` environment variable if omitted. |

`send()` returns `True` when the SIEM responds with HTTP `200`, `201`, or `202`. Returns `False` on any network error, timeout, or if `requests` is not installed.

---

### `build_siem_event`

```python
def build_siem_event(report: Dict[str, Any], source: str = 'deployment_checker') -> Dict[str, Any]
```

Flattens a full deployment report dict into a standard SIEM event envelope:

```json
{
  "source":    "deployment_checker",
  "timestamp": "2026-05-27T10:00:00",
  "hostname":  "WORKSTATION-01",
  "verdict":   "NOT READY",
  "summary":   { "total": 15, "passed": 9, "failed": 6, "critical_failures": 2 },
  "checks":    [ ... ]
}
```

---

## Configuration

### Environment Variable
```bash
SIEM_WEBHOOK_URL=https://your-siem.example.com/api/events
```

Set this in `.env` or as a system environment variable. The `WebhookForwarder` reads it automatically when no URL is passed to the constructor.

### Programmatic
```python
from src.security.siem.forwarder import WebhookForwarder, build_siem_event

forwarder = WebhookForwarder(url='https://splunk-hec.company.com:8088/services/collector')
event = build_siem_event(report.to_dict(), source='windows_agent')
sent = forwarder.send(event)
print("Forwarded:", sent)
```

---

## Integration with PreDeploymentChecker

The deployment checker accepts an optional `siem_url` parameter:

```python
from src.security.deployment.checker import PreDeploymentChecker

checker = PreDeploymentChecker(
    project_root='/path/to/project',
    siem_url='https://your-siem/webhook'
)
report = checker.run_all()
# → report.to_dict() is automatically built into a SIEM event and POSTed
```

---

## Graceful Degradation

- If the `requests` library is not installed, `send()` silently returns `False` — the assessment continues normally.
- If the webhook URL is not configured, `send()` returns `False` immediately — no error is raised.
- Network errors and timeouts (default: 10 s) are caught; `send()` returns `False`.

This means SIEM forwarding is **optional** — the tool works completely without it.

---

## Supported SIEM Targets

| SIEM | Endpoint pattern |
|---|---|
| **Splunk HEC** | `https://splunk:8088/services/collector` with `Authorization: Splunk <token>` header |
| **Elastic / Logstash** | `https://logstash:5044` or Elastic ingest pipeline endpoint |
| **Wazuh** | Wazuh REST API `/active-response` or custom integration |
| **Graylog GELF HTTP** | `http://graylog:12201/gelf` |
| **Custom webhook** | Any endpoint that accepts `application/json` POST |

> **Note:** Custom headers (e.g., API keys) are not yet supported in `WebhookForwarder.send()`. For SIEM systems requiring authentication headers, subclass `WebhookForwarder` and override `send()`.

---

## Related Features
- [Windows Agent](10-windows-agent.md) — generates reports that can be forwarded
- [Deployment Checker](07-deployment-checker.md) — integrates SIEM forwarding directly
- [Monitoring Checks](12-monitoring-checks.md) — PDC-15 log hygiene check
