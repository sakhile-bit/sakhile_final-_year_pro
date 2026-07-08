# Feature Documentation — Zambia Digital Hygiene Certification Programme

All 20 features of the project are documented below. Each file covers the feature's purpose, implementation details, data structures, and API.

---

## Core Assessment

| # | File | Feature |
|---|---|---|
| 01 | [01-digital-hygiene-assessment.md](01-digital-hygiene-assessment.md) | **Digital Hygiene Assessment** — 15-control framework, scoring, certification tiers |
| 02 | [02-automated-scanning.md](02-automated-scanning.md) | **Automated Scanning** — C01-C05 + 5 extended checks, one-click remediation |
| 03 | [03-results-certification.md](03-results-certification.md) | **Results & Certification** — ring chart, GOLD/SILVER/BRONZE badge, exports |
| 04 | [04-assessment-history.md](04-assessment-history.md) | **Assessment History** — history list, detail view, side-by-side comparison |

## Security Tools

| # | File | Feature |
|---|---|---|
| 05 | [05-network-scanner.md](05-network-scanner.md) | **Network Scanner** — ARP/ping discovery, port scan, topology map |
| 06 | [06-infra-scanner.md](06-infra-scanner.md) | **Infrastructure Scanner** — external host SSL/TLS/ports/headers |
| 07 | [07-deployment-checker.md](07-deployment-checker.md) | **Pre-Deployment Checker** — 15 checks PDC-01 to PDC-15 |
| 08 | [08-zambia-risk-assessment.md](08-zambia-risk-assessment.md) | **Zambia Risk Assessment** — SIM swap, mobile money, DPA 2021 compliance |
| 09 | [09-policy-templates.md](09-policy-templates.md) | **Policy Templates** — 6 downloadable policy documents |
| 19 | [19-server-hardening.md](19-server-hardening.md) | **Server Hardening Audit** — 14 Windows infrastructure checks HRD-01 to HRD-14, HARDENED/AT RISK grade |

## Agent & Automation

| # | File | Feature |
|---|---|---|
| 10 | [10-windows-agent.md](10-windows-agent.md) | **Windows Agent** — standalone collector, JSON report, CLI |
| 11 | [11-siem-forwarder.md](11-siem-forwarder.md) | **SIEM Forwarder** — webhook forwarding to Splunk/Elastic/Wazuh |
| 20 | [20-fleet-scanning.md](20-fleet-scanning.md) | **Distributed Fleet Scanning** — master node scans many connected nodes, weakest-link fleet grade |
| 12 | [12-monitoring-checks.md](12-monitoring-checks.md) | **Monitoring Checks** — Windows Event Log + log-forwarding hygiene (PDC-15) |
| 13 | [13-remediation-guidance.md](13-remediation-guidance.md) | **Remediation Guidance** — PowerShell fix scripts per check ID |
| 15 | [15-scheduler.md](15-scheduler.md) | **Scheduler** — interval-based job runner for recurring agent runs |

## Platform

| # | File | Feature |
|---|---|---|
| 14 | [14-welcome-dashboard.md](14-welcome-dashboard.md) | **Welcome Dashboard** — desktop home screen with last-assessment card |
| 16 | [16-active-directory-checks.md](16-active-directory-checks.md) | **Active Directory Checks** — LDAP connectivity, stale accounts, admin groups |
| 17 | [17-report-generation.md](17-report-generation.md) | **Report Generation** — JSON/HTML/PDF/CSV export + HTML certificate |
| 18 | [18-web-application.md](18-web-application.md) | **Flask Web Application** — multi-user portal, roles, MFA, audit logs |

---

## Framework Alignment

| Assessment Control | CIS | NIST CSF | ISO 27001 | Zambia DPA |
|---|---|---|---|---|
| C01 OS Updates | CIS 7 | PR.IP-12 | A.12.6 | — |
| C02 Antivirus | CIS 10 | DE.CM-4 | A.12.2 | — |
| C03 Firewall | CIS 4 | PR.AC-5 | A.13.1 | — |
| C04 Password Policy | CIS 5 | PR.AC-1 | A.9.4 | — |
| C05 Backups | CIS 11 | PR.IP-4 | A.12.3 | — |
| C06-C15 (manual) | Various | Various | Various | Art. 17, 18, 23 |

---

*Generated: 2026-05-27 · University of Zambia, Dept. of Computing & Informatics*
