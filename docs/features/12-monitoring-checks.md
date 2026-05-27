# Feature: Monitoring & Log Hygiene Checks

## Overview
The Monitoring Checks module inspects whether a Windows (or Linux) host has functional **logging infrastructure** in place — a critical security baseline requirement. It powers check **PDC-15 (Monitoring Hygiene)** in the Pre-Deployment Checker.

**File:** [`src/security/monitoring/checks.py`](../../src/security/monitoring/checks.py)

---

## What It Checks

### On Windows
1. **Windows Event Log availability** — runs `wevtutil gl Application` to confirm the Windows Event Log service is active and queryable.
2. **Log-forwarding agent detection** — scans `PATH` for any of these common agents:
   - `nxlog` — NXLog Community Edition
   - `snare` — Snare for Windows
   - `winlogbeat` — Elastic Beats for Windows event logs
   - `syslog-ng` — syslog-ng for Windows

### On Linux / macOS
1. **Journal availability** — checks for `journalctl` (systemd journal).
2. **Syslog daemon** — falls back to detecting `rsyslogd` or `syslog-ng`.
3. **Functional logging test** — runs `logger -p user.info 'test log'` to confirm local syslog accepts writes.

---

## Function: `get_logging_hygiene()`

```python
from src.security.monitoring.checks import get_logging_hygiene

result = get_logging_hygiene()
```

Returns a dict:

```python
{
    'status':   'PASS',        # 'PASS' or 'FAIL'
    'passed':   True,          # bool
    'severity': 'LOW',         # 'LOW' (pass) or 'MEDIUM' (fail)
    'details':  [
        'Windows Event Log service is available',
        'Log forwarding agent installed: winlogbeat',
    ]
}
```

---

## Pass / Fail Logic

```
PASS  when:  'available' or 'functional' appears in any detail string
FAIL  when:  no detail contains 'available' or 'functional'

Severity escalates from LOW (pass) to MEDIUM (fail)
```

---

## PDC-15 Integration

`PreDeploymentChecker` calls `get_logging_hygiene()` as part of its 15-check suite:

```python
# Inside checker.py
from src.security.monitoring.checks import get_logging_hygiene

def _check_monitoring_hygiene(self):
    result = get_logging_hygiene()
    return CheckResult(
        check_id='PDC-15',
        name='Monitoring Hygiene',
        passed=result['passed'],
        severity=result['severity'],
        details=' | '.join(result['details']),
        remediation=(
            'Install a log-forwarding agent (winlogbeat, nxlog) '
            'and ensure Windows Event Log is running'
        ) if not result['passed'] else '',
        category='monitoring',
    )
```

---

## Remediation

If PDC-15 fails, operators should:
1. **Verify Event Log is running:** `Services.msc` → `Windows Event Log` → Start
2. **Install a log forwarder:**
   - Winlogbeat (free, Elastic): [elastic.co/beats/winlogbeat](https://www.elastic.co/beats/winlogbeat)
   - NXLog CE (free): [nxlog.co/products/nxlog-community-edition](https://nxlog.co/products/nxlog-community-edition)
3. **Configure forwarding** to a SIEM endpoint (see [SIEM Forwarder](11-siem-forwarder.md))

---

## Related Features
- [Deployment Checker](07-deployment-checker.md) — PDC-15 Monitoring Hygiene
- [SIEM Forwarder](11-siem-forwarder.md) — where logs are forwarded
- [Windows Agent](10-windows-agent.md) — runs monitoring checks as part of full report
