# Feature: Remediation Guidance

## Overview
The Remediation Guidance module provides a **lookup table** of human-readable fix instructions and optional PowerShell remediation scripts for each failed pre-deployment check. Operators can copy the PowerShell snippet directly into an elevated terminal to remediate the finding.

**File:** [`src/security/remediation/guidance.py`](../../src/security/remediation/guidance.py)

---

## Available Remediations

| Check ID | Title | PowerShell Snippet |
|---|---|---|
| **PDC-01** | Apply OS Updates | `Install-Module -Name PSWindowsUpdate; Get-WindowsUpdate -Install -AcceptAll -AutoReboot` |
| **PDC-02** | Enable Firewall | `netsh advfirewall set allprofiles state on` |
| **PDC-03** | Enable Real-time Antivirus | `Set-MpPreference -DisableRealtimeMonitoring $false` |
| **PDC-05** | Close Risky Ports | `New-NetFirewallRule -DisplayName 'Block SMB' -Direction Inbound -LocalPort 445 -Action Block -Protocol TCP` |

---

## API

### `get_remediation(check_id: str)`

```python
from src.security.remediation.guidance import get_remediation

info = get_remediation('PDC-01')
# Returns:
# {
#   'title':      'Apply OS Updates',
#   'advice':     'Run Windows Update or configure WSUS/Windows Update for Business.',
#   'powershell': 'Install-Module -Name PSWindowsUpdate; ...'
# }

info = get_remediation('PDC-99')  # Unknown ID
# Returns: None
```

### `REMEDIATIONS` dict

The raw lookup dict is importable for bulk access:

```python
from src.security.remediation.guidance import REMEDIATIONS

for check_id, info in REMEDIATIONS.items():
    print(f"{check_id}: {info['title']}")
```

---

## Data Structure

Each entry in `REMEDIATIONS`:

```python
{
    'title':      str,  # Short human-readable fix title
    'advice':     str,  # Plain-English description of what to do
    'powershell': str,  # Optional PowerShell snippet (may be absent for some checks)
}
```

---

## Integration with GUI

The Deployment Checker GUI (`deployment_screen.py`) calls `get_remediation()` for every failed check and displays the advice and PowerShell snippet inline in the results panel. Users can click a **Copy** button to copy the PowerShell command to the clipboard.

---

## Adding New Remediations

To add a new entry, append to the `REMEDIATIONS` dict in `guidance.py`:

```python
'PDC-04': {
    'title': 'Enable BitLocker',
    'advice': 'Enable BitLocker disk encryption on the C: drive.',
    'powershell': 'Enable-BitLocker -MountPoint "C:" -EncryptionMethod Aes256 -UsedSpaceOnly',
},
```

---

## Related Features
- [Deployment Checker](07-deployment-checker.md) — checks that produce PDC-XX findings
- [Windows Agent](10-windows-agent.md) — agent reports include remediation hints
- [Automated Scanning](02-automated-scanning.md) — one-click fix buttons in the desktop GUI
