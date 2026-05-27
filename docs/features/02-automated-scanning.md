# Feature: Automated Security Scanning

## Overview
The scanning screen runs **10 automated checks** on the local Windows machine in a background thread: five core controls (C01–C05) plus five extended checks (EX-01–EX-05). Every check displays a live status icon, a details line and — where remediable — a one-click **Fix** button that runs a PowerShell command.

**File:** [`src/gui/screens/scanning.py`](../../src/gui/screens/scanning.py)  
**Engine:** [`src/security/assessment/assessor.py`](../../src/security/assessment/assessor.py)

---

## Core Checks (C01–C05)

| ID | Name | What is inspected | Severity |
|---|---|---|---|
| C01 | OS Updates | Windows Update service state, last patch date (registry + PowerShell Get-HotFix), pending restart keys | CRITICAL |
| C02 | Antivirus / Defender | `Get-MpComputerStatus` — enabled, real-time on, definition age ≤ 3 days | CRITICAL |
| C03 | Firewall | `netsh advfirewall show allprofiles` — Domain / Private / Public profile state | CRITICAL |
| C04 | Password Policy | `net accounts` — minimum length, max age, lockout threshold | CRITICAL |
| C05 | Backup System | Registry: backup software; `sc query fhsvc` File History; `vssadmin list shadows`; OneDrive/Dropbox folders | CRITICAL |

---

## Extended Checks (EX-01–EX-05)

| ID | Name | What is inspected | Method |
|---|---|---|---|
| EX-01 | Ransomware Protection | Controlled Folder Access (`Get-MpPreference.EnableControlledFolderAccess`) | PowerShell |
| EX-02 | Local Account Audit | `Get-LocalUser` — guest and built-in Administrator enabled state | PowerShell |
| EX-03 | AutoRun Policy | `NoDriveTypeAutoRun` registry value in HKLM and HKCU Explorer policies | Registry |
| EX-04 | Windows Hello / PIN | NGC credentials folder + `PassportForWork` policy key | File + Registry |
| EX-05 | Pending Updates | Registry reboot keys + Event Log ID 19 (last successful install) + WUA service state | Registry + Event Log |

---

## One-Click Fix Actions

Each failed core check exposes a **Fix** button that:
1. Shows a description of what will be changed
2. Runs one or more PowerShell/cmd commands via `subprocess`
3. Displays a success or failure toast notification

| Check | Fix command |
|---|---|
| C01 | `Set-Service wuauserv -StartupType Automatic; Start-Service wuauserv` |
| C02 | `Set-MpPreference -DisableRealtimeMonitoring $false` |
| C03 | `netsh advfirewall set allprofiles state on` |
| C04 | `net accounts /minpwlen:8 /maxpwage:90 /lockoutthreshold:5` |
| C05 | `Enable-ComputerRestore -Drive "C:\"; vssadmin create shadow /for=C:` |

---

## Execution Flow

```
User clicks "Start Scan"
        ↓
Background thread starts (threading.Thread)
        ↓
  ┌─────────────────────────────────┐
  │  For each of C01–C05:           │
  │    assessor.<check_method>()    │
  │    self.after(0, _update_row)   │  ← thread-safe UI update
  └─────────────────────────────────┘
        ↓
  ┌─────────────────────────────────┐
  │  For each of EX-01–EX-05:      │
  │    assessor.<ext_method>()      │
  │    self.after(0, _update_ext_row) │
  └─────────────────────────────────┘
        ↓
  self.after(0, _scan_complete)
        ↓
  Progress bar → 100%
  "Next →" button becomes active
```

All UI mutations are dispatched via `self.after(0, ...)` to stay on the main tkinter thread.

---

## Status Indicators

| Status | Icon | Colour |
|---|---|---|
| PASS | ✔ | Green `#6EC16B` |
| WARNING | ⚠ | Amber `#F0A500` |
| FAIL | ✖ | Red `#E84040` |
| ERROR | ! | Amber `#F0A500` |
| Pending | … | Grey `#5A7490` |

---

## Skip to Results
A **"Skip to Results →"** button is available for automated-only mode: skips the manual interview and goes directly to the results screen using only the C01–C05 scores.

---

## Thread Safety
All background work runs in a `daemon=True` thread. UI updates use `widget.after(0, callback)` — this posts the call to the tkinter main-loop event queue instead of calling it directly, preventing race conditions and `RuntimeError: main thread is not in main loop`.

---

## Related Features
- [Digital Hygiene Assessment](01-digital-hygiene-assessment.md) — controls definition
- [Results & Certification](03-results-certification.md) — next screen after scanning
- [Remediation Guidance](12-remediation-guidance.md) — PowerShell fix scripts
