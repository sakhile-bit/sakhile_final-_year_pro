# Feature: Windows Agent

## Overview
A lightweight, self-contained data-collection agent that runs the full digital-hygiene assessment and pre-deployment checks on a Windows host and writes a **JSON report** to disk. Designed so operators can deploy it across multiple machines and collect the reports centrally for ingestion into a SIEM or web dashboard.

**Files:**  
- [`src/agents/windows_agent.py`](../../src/agents/windows_agent.py) — agent entry point  
- [`src/utils/agent_cli.py`](../../src/utils/agent_cli.py) — CLI wrapper  
- [`src/security/assessment/remote_collector.py`](../../src/security/assessment/remote_collector.py) — report loader

---

## What the Agent Does

1. **Creates the report directory** — `instance/agent_reports/` (created if missing)
2. **Runs pre-deployment checks** — `PreDeploymentChecker.run_all()` (15 checks, READY / NOT READY)
3. **Runs the digital hygiene assessment** — `DigitalHygieneAssessor.run_assessment()` (15 controls, 120 pts)
4. **Builds a combined report dict** containing both result sets plus hostname and timestamp
5. **Writes a JSON file** named `<hostname>-<unix_timestamp>.json` to the reports directory
6. **Returns** the report path and data to the caller

---

## Report Structure

```json
{
  "collected_at": "2026-05-27T10:30:00Z",
  "hostname":     "WORKSTATION-01",
  "readiness": {
    "verdict": "NOT READY",
    "timestamp": "2026-05-27T10:30:00",
    "os_info": "Windows 11",
    "summary": {
      "total": 15,
      "passed": 9,
      "failed": 6,
      "critical_failures": 2
    },
    "checks": [
      {
        "check_id": "PDC-01",
        "name": "OS Updates",
        "passed": false,
        "severity": "CRITICAL",
        "details": "Last patch was 45 days ago – overdue",
        "remediation": "Run Windows Update immediately",
        "category": "system"
      }
    ]
  },
  "assessment": {
    "score": 26,
    "total_possible": 120,
    "certification_level": "NOT CERTIFIED",
    "controls": {
      "C01_os_updates": {
        "control_id": "C01",
        "name": "Operating System Updates",
        "score": 3,
        "weight": 10,
        "status": "FAIL",
        "details": "..."
      }
    }
  }
}
```

---

## Running the Agent

### Direct Python execution
```bash
python src/agents/windows_agent.py --name "My Business"
```

### Via CLI utility
```bash
python -m src.utils.agent_cli agent --name "My Business"
```

### Programmatic
```python
from src.agents.windows_agent import collect_local_report

result = collect_local_report('Acme Ltd')
print(result['report_path'])   # e.g. instance/agent_reports/WEZULU-1748339978.json
print(result['report']['readiness']['verdict'])   # READY or NOT READY
print(result['report']['assessment']['certification_level'])  # GOLD / SILVER / BRONZE / NOT CERTIFIED
```

---

## Remote Collector

The `remote_collector.py` module loads agent reports back for processing:

```python
from src.security.assessment.remote_collector import load_agent_report, summarize_agent_report

report = load_agent_report('instance/agent_reports/WEZULU-1748339978.json')
summary = summarize_agent_report(report)
# Returns:
# {
#   'hostname': 'WEZULU',
#   'collected_at': '2026-05-27T10:30:00Z',
#   'assessment_score': 26,
#   'cert_level': 'NOT CERTIFIED',
#   'readiness_verdict': 'NOT READY'
# }
```

---

## Scheduled Collection

The `SimpleScheduler` from `src/utils/scheduler.py` can run the agent on a recurring interval:

```python
from src.agents.windows_agent import collect_local_report
from src.utils.scheduler import SimpleScheduler

sched = SimpleScheduler()
sched.add_job(lambda: collect_local_report('nightly-check'), interval_seconds=3600)
sched.start()
```

Reports accumulate in `instance/agent_reports/` and can be ingested by the web dashboard or forwarded to a SIEM.

---

## File Naming Convention
```
instance/agent_reports/<HOSTNAME>-<UNIX_TIMESTAMP>.json
```
Example: `instance/agent_reports/WORKSTATION-01-1748339978.json`

Multiple reports per host are preserved; they accumulate over time for trend analysis.

---

## Related Features
- [Deployment Checker](07-deployment-checker.md) — provides the readiness half of the report
- [Digital Hygiene Assessment](01-digital-hygiene-assessment.md) — provides the assessment half
- [Scheduler](15-scheduler.md) — runs the agent on a schedule
- [SIEM Forwarder](11-siem-forwarder.md) — forwards reports to a SIEM webhook
- [Active Directory Checks](16-active-directory-checks.md) — can be added to agent reports
