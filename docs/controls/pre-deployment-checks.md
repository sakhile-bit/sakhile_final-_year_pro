# Pre-Deployment Checks — `PDC-01` … `PDC-15`

**Source:** `src/security/deployment/checker.py` (`PreDeploymentChecker`)
**Remediation text:** `src/security/remediation/guidance.py` (`PDC-01`–`PDC-06`)
**Layer:** Endpoint / host readiness (dev workstation, CI runner, staging server)
**Verdict:** `READY` when there are 0 critical failures **and** ≤ 2 non-critical
failures; otherwise `NOT READY`. Designed as a single gate a CI/CD pipeline can act on.

Checks are grouped into five categories: **system, network, application,
secrets, monitoring**. Each returns a pass/fail verdict, severity, and
remediation advice. Windows and Unix code paths are both implemented.
Results can optionally be forwarded to a SIEM webhook.

| ID | Control | Severity | Category | What it verifies |
|----|---------|----------|----------|------------------|
| `PDC-01` | OS Updates | CRITICAL | system | Last OS patch installed within 30 days (Windows hotfix date / `apt` upgradable list). |
| `PDC-02` | Firewall | CRITICAL | system | Host firewall enabled on all profiles (Windows Firewall / UFW). |
| `PDC-03` | Antivirus / Defender | HIGH | system | Real-time AV protection is on (Defender `RealTimeProtectionEnabled` / known Unix AV). |
| `PDC-04` | Disk Encryption | MEDIUM | system | System drive encrypted (BitLocker fully enabled / LUKS present). |
| `PDC-05` | Open Ports | HIGH | network | No risky DB/service ports open on localhost (FTP, Telnet, SMB, MSSQL, MySQL, PostgreSQL, Redis, MongoDB). |
| `PDC-06` | DNS Resolution | MEDIUM | network | Outbound DNS resolves (needed for package registries). |
| `PDC-07` | TLS / OpenSSL | MEDIUM | network | A working OpenSSL / TLS library is available. |
| `PDC-08` | Python Version | HIGH | application | Python ≥ 3.8. |
| `PDC-09` | Dependency Vulnerabilities | CRITICAL | application | `pip-audit` reports no known-vulnerable packages (skipped with advice if not installed). |
| `PDC-10` | Debug Mode | HIGH | application | No `DEBUG` / `FLASK_DEBUG` / `DJANGO_DEBUG` env var set truthy. |
| `PDC-11` | .env File Exposure | HIGH | secrets | Any `.env` in the project root is listed in `.gitignore`. |
| `PDC-12` | Hard-coded Secrets | CRITICAL | secrets | Source files contain no obvious hard-coded passwords/keys (placeholders & test/security dirs excluded). |
| `PDC-13` | Git Secret Hygiene | MEDIUM | secrets | No sensitive files tracked by git (`.env`, `id_rsa`, `.pem`, `.key`, `credentials.json`, …; `.example`/`.sample` excluded). |
| `PDC-14` | Software Inventory | LOW | system | Informational host software inventory (registry uninstall keys / `dpkg`/`rpm`). |
| `PDC-15` | Monitoring Hygiene | MEDIUM (dynamic) | monitoring | Event logging is available and a log-forwarding agent is present (see `src/security/monitoring/checks.py`). |

> `PDC-01`–`PDC-06` additionally have curated remediation entries (advice +
> PowerShell snippet) in `remediation/guidance.py`, shared with the host
> assessment. `PDC-07`–`PDC-15` carry their remediation inline in each check.

---
**Feature docs:** [07 Pre-Deployment Checker](../features/07-deployment-checker.md) · [12 Monitoring Checks](../features/12-monitoring-checks.md) · [13 Remediation Guidance](../features/13-remediation-guidance.md) · [controls catalogue](README.md)
