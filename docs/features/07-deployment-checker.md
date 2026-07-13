# Feature: Pre-Deployment Digital Hygiene Checker

## Overview
The Deployment Checker lets developers verify that a machine (dev workstation, CI runner, staging server) meets baseline digital-hygiene requirements **before code ships to production**. It runs **15 checks** across five categories and produces a `READY` / `NOT READY` verdict. Not restricted to Python — checks are tech-agnostic system/network/secrets checks.

**GUI file:** [`src/gui/screens/deployment_screen.py`](../../src/gui/screens/deployment_screen.py)  
**Engine file:** [`src/security/deployment/checker.py`](../../src/security/deployment/checker.py)

---

## Verdict Logic

```
READY     when:  critical_failures == 0  AND  total_failures ≤ 2
NOT READY when:  critical_failures ≥ 1  OR   total_failures > 2
```

Colours: **CLEARED** (green) · **CAUTION** (amber) · **BLOCKED** (red)

---

## The 15 Checks

### System (PDC-01 to PDC-05, PDC-14, PDC-15)

| ID | Name | Severity | What it does |
|---|---|---|---|
| PDC-01 | OS Updates | CRITICAL | PowerShell `Get-HotFix` → last patch date, registry reboot-pending keys |
| PDC-02 | Firewall | CRITICAL | `netsh advfirewall show allprofiles` — all 3 profiles ON |
| PDC-03 | Antivirus / Defender | HIGH | `Get-MpComputerStatus.RealTimeProtectionEnabled` |
| PDC-04 | Disk Encryption | MEDIUM | `manage-bde -status C:` → BitLocker fully encrypted |
| PDC-14 | Software Inventory | LOW | Registry `Uninstall` keys → installed product list |
| PDC-15 | Monitoring Hygiene | MEDIUM | Windows Event Log + log-forwarding agent detection |

### Network (PDC-05 to PDC-07)

| ID | Name | Severity | What it does |
|---|---|---|---|
| PDC-05 | Open Ports | HIGH | TCP probe to 127.0.0.1 on 8 risky ports (FTP, Telnet, SMB, databases) |
| PDC-06 | DNS Resolution | MEDIUM | `socket.getaddrinfo('pypi.org', 443)` — outbound DNS works |
| PDC-07 | TLS / OpenSSL | MEDIUM | `ssl.OPENSSL_VERSION` — Python TLS library present |

### Application (PDC-08 to PDC-10)

| ID | Name | Severity | What it does |
|---|---|---|---|
| PDC-08 | Python Version | HIGH | `sys.version_info` ≥ 3.8 |
| PDC-09 | Dependency Vulnerabilities | CRITICAL | `python -m pip audit --desc` — known CVEs in installed packages |
| PDC-10 | Debug Mode | HIGH | Checks `DEBUG`, `FLASK_DEBUG`, `DJANGO_DEBUG` env vars |

### Secrets (PDC-11 to PDC-13)

| ID | Name | Severity | What it does |
|---|---|---|---|
| PDC-11 | .env File Exposure | HIGH | `.env` exists but not in `.gitignore` |
| PDC-12 | Hard-coded Secrets | CRITICAL | Regex scan of `src/` Python files for real credential assignments |
| PDC-13 | Git Secret Hygiene | MEDIUM | `git ls-files` — sensitive files tracked in git (`.env`, `.pem`, `id_rsa`) |

### Monitoring (PDC-15)
Already listed above under System.

---

## Hard-coded Secrets Detection (PDC-12)
Uses a regex to find real assigned credentials — not search-pattern strings:

```python
_PAT = re.compile(
    r'^\s*(?:password|secret_key|api_key|aws_secret|private_key)\s*=\s*'
    r'["\']([^"\']{4,})["\']',
    re.IGNORECASE,
)
```

**Exclusions:**
- Files inside `src/security/` (contain patterns as string literals)
- Files inside `tests/`
- Placeholder values: `your-secret-here`, `example`, `<...>`, `changeme`, `xxx`

---

## ApplicationHygieneChecker & CodeSecurityChecker

In addition to system checks, the GUI (`deployment_screen.py`) also runs:

### ApplicationHygieneChecker (APP-01 to APP-05)
Tech-agnostic application-level checks:
- APP-01: `requirements.txt` / `package.json` / `Gemfile` present
- APP-02: `README.md` present
- APP-03: Tests directory present (`tests/`, `spec/`, `__tests__/`)
- APP-04: CI config present (`.github/workflows/`, `Jenkinsfile`, `.travis.yml`)
- APP-05: Logging configured (log config file or `import logging` in code)

### CodeSecurityChecker (CCS-01 to CCS-06)
- CCS-01: No `eval()` calls in source
- CCS-02: No `exec()` calls in source
- CCS-03: No `shell=True` in subprocess calls
- CCS-04: SQL queries use parameterised form (no string concatenation)
- CCS-05: `assert` not used for security checks
- CCS-06: No hardcoded IP addresses in source

---

## SIEM Integration
The checker optionally forwards its report to a SIEM webhook:

```python
checker = PreDeploymentChecker(
    project_root='/path/to/project',
    siem_url='https://your-siem/webhook'
)
report = checker.run_all()
# → DeploymentReadiness.to_dict() POSTed to siem_url as JSON
```

Powered by [`src/security/siem/forwarder.py`](../../src/security/siem/forwarder.py).

---

## Report Output

```python
report = checker.run_all()
print(report.verdict)          # "READY" or "NOT READY"
print(report.passed)           # int
print(report.critical_failures)# int
print(report.to_dict())        # full JSON-serialisable dict
```

`to_dict()` structure:
```json
{
  "verdict": "NOT READY",
  "timestamp": "2026-05-27T10:00:00",
  "hostname": "WEZULU",
  "os_info": "Windows 11",
  "summary": { "total": 15, "passed": 9, "failed": 6, "critical_failures": 2 },
  "checks": [ { "check_id": "PDC-01", "name": "OS Updates", "passed": false, ... } ]
}
```

---

## CLI Usage

```bash
python -m src.utils.agent_cli agent --name "My Project"
```

Runs the full pre-deployment check and writes a JSON report to `instance/agent_reports/`.

---

## Related Features
- [Windows Agent](09-windows-agent.md) — calls `PreDeploymentChecker` as part of full report
- [SIEM Forwarder](11-siem-forwarder.md) — forwards reports to external SIEM
- [Monitoring Checks](10-monitoring-checks.md) — powers PDC-15
- [Remediation Guidance](12-remediation-guidance.md) — fix scripts for PDC-01 to PDC-05

## Controls Reference
- [pre-deployment-checks.md](../controls/pre-deployment-checks.md) — full definitions of PDC-01…PDC-15 with severity, category and remediation.
