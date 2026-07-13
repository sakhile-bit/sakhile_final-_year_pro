# Endpoint Core Controls — `C01` … `C05` + `EX-01` … `EX-05`

**Source:** `src/gui/screens/scanning.py` (drives
`src/security/assessment` assessor methods)
**Remediation text:** `src/gui/screens/remediation_guidance.py`
**Layer:** Endpoint (the user's Windows workstation / laptop)

These are the **automated** controls run during the certification scan. `C01`–`C05`
are the *core* controls shown in the certificate; `EX-01`–`EX-05` are *extended*
checks run in parallel and displayed separately. Each control returns
`PASS` / `WARNING` / `FAIL` and, where possible, a one-click fix.

## Core controls (`C01`–`C05`)

| ID | Control | What it checks | One-click fix |
|----|---------|----------------|---------------|
| `C01` | OS Updates | Windows Update service state and last patch date. | Set `wuauserv` to Automatic and start it. |
| `C02` | Antivirus / Defender | Real-time protection and definition age. | Enable Defender real-time & behaviour monitoring. |
| `C03` | Firewall | Domain, Private and Public profile status. | `netsh advfirewall set allprofiles state on`. |
| `C04` | Password Policy | Minimum length, expiry and lockout threshold. | Apply 8-char min / 90-day expiry / 5-attempt lockout. |
| `C05` | Backup System | Backup software, VSS, cloud sync. | Open Windows Backup settings (`ms-settings:backup`). |

`C01`–`C05` map respectively to `⚡ Quick Fix` (C01–C03) and `📅 This Week`
(C04–C05) remediation urgency in the results view.

## Extended checks (`EX-01`–`EX-05`)

| ID | Control | What it checks |
|----|---------|----------------|
| `EX-01` | Ransomware Protection | Controlled Folder Access status. |
| `EX-02` | Local Account Audit | Guest account disabled, built-in admin review. |
| `EX-03` | AutoRun Policy | USB / CD AutoRun disabled. |
| `EX-04` | Windows Hello / PIN | Modern phishing-resistant authentication present. |
| `EX-05` | Pending Updates | Count of outstanding Windows updates. |

## Relationship to the certificate

`C01`–`C05` combine with the governance controls (`C06`–`C15`) and any selected
tool-specific controls (`C16`–`C22`) into the overall **Core Controls (C01–C15)**
score shown on the certificate. Certification is **integrity-aware**: an
incomplete or failed automated scan gates the certificate to *provisional*.

---
**Feature docs:** [02 Automated Scanning](../features/02-automated-scanning.md) · [03 Results & Certification](../features/03-results-certification.md) · [controls catalogue](README.md)
