# Security Controls Catalogue

This directory documents **every security control implemented by the Zambia
Digital Hygiene Certification Tool**. Each control has a stable identifier
(e.g. `C01`, `HRD-05`, `AD-03`, `PDC-11`, `TLS-CERT`), a severity, what it
checks, and how it is remediated.

The tool assesses digital hygiene at three layers, reflecting the project
thesis that *end-user awareness is worthless if the infrastructure serving
those users has poor hygiene*:

1. **The endpoint** the user works on (workstation / laptop).
2. **The business and its people** (governance, policy, awareness).
3. **The infrastructure** that provides services (servers, directory, public web).

## Control families

| Family | IDs | Count | Layer | Source | Doc |
|--------|-----|-------|-------|--------|-----|
| Endpoint Core Controls | `C01`–`C05` | 5 | Endpoint | `src/gui/screens/scanning.py` + assessor | [endpoint-core-controls.md](endpoint-core-controls.md) |
| Endpoint Extended Checks | `EX-01`–`EX-05` | 5 | Endpoint | `src/gui/screens/scanning.py` | [endpoint-core-controls.md](endpoint-core-controls.md) |
| Governance / Manual Controls | `C06`–`C15` | 10 | Business | `src/gui/screens/manual_checks.py` | [governance-controls.md](governance-controls.md) |
| Tool-Specific Controls | `C16`–`C22` (+ sub-parts) | 7 groups | Business | `src/gui/screens/manual_checks.py` | [tool-specific-controls.md](tool-specific-controls.md) |
| Pre-Deployment Checks | `PDC-01`–`PDC-15` | 15 | Endpoint / Host | `src/security/deployment/checker.py` | [pre-deployment-checks.md](pre-deployment-checks.md) |
| Windows Hardening Audit | `HRD-01`–`HRD-14` | 14 | Infrastructure | `src/security/hardening/checks.py` | [windows-hardening.md](windows-hardening.md) |
| Active Directory Hygiene | `AD-01`–`AD-07` | 7 | Infrastructure | `src/security/active_directory/checks.py` | [active-directory.md](active-directory.md) |
| Infrastructure Scanner | `TLS-*`, `HTTP-*`, `HDR-*`, `DNS-*`, `PORT` | 14 | Infrastructure | `src/security/assessment/assessor.py` | [infrastructure-scanner.md](infrastructure-scanner.md) |
| Zambia Local Threat Assessment | 16 items in 4 categories | — | Business | `src/gui/screens/zambia_risk.py` | [zambia-threat-assessment.md](zambia-threat-assessment.md) |

## Severity levels

All automated families use the same four-level severity scale:

| Severity | Meaning |
|----------|---------|
| **CRITICAL** | Direct, exploitable exposure. A single CRITICAL failure forces the worst overall grade. |
| **HIGH** | Serious weakness that materially increases attack surface. |
| **MEDIUM** | Meaningful hygiene gap; should be fixed but not immediately dangerous. |
| **LOW** | Best-practice / informational. |

## Grading

Each scanner aggregates its control results into a letter grade. The exact
band differs per family (documented in each file), but they share a pattern:

- A percentage **score** (PASS = 1 point, WARNING/partial = ½ point, FAIL = 0).
- A **critical-failure override**: any CRITICAL failure caps the grade at the
  worst band (`AT RISK` / `NOT READY`), regardless of score.

Grade vocabulary by family:

| Family | Best → Worst |
|--------|--------------|
| Endpoint / Certification | `CERTIFIED` → `PROVISIONAL` → `NOT CERTIFIED` |
| Pre-Deployment | `READY` → `NOT READY` |
| Windows Hardening | `HARDENED` → `NEEDS ATTENTION` → `AT RISK` |
| Active Directory | `HEALTHY` → `NEEDS ATTENTION` → `AT RISK` |
| Infrastructure Scanner | `SECURE` → `NEEDS ATTENTION` → `AT RISK` |
| Zambia Threat | `LOW RISK` → `MEDIUM RISK` → `HIGH RISK` |
