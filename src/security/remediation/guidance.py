"""Remediation guidance mapping for common checks.

Provides human-friendly remediation text and optional PowerShell snippets
operators can use to remediate common findings on Windows hosts.
"""
from __future__ import annotations

from typing import Dict, Any


REMEDIATIONS: Dict[str, Dict[str, Any]] = {
    'PDC-01': {
        'title': 'Apply OS Updates',
        'advice': 'Run Windows Update or configure WSUS/Windows Update for Business.',
        'powershell': 'Install-Module -Name PSWindowsUpdate; Get-WindowsUpdate -Install -AcceptAll -AutoReboot',
    },
    'PDC-02': {
        'title': 'Enable Firewall',
        'advice': 'Enable Windows Firewall for all profiles.',
        'powershell': 'netsh advfirewall set allprofiles state on',
    },
    'PDC-03': {
        'title': 'Enable Real-time Antivirus',
        'advice': 'Ensure Windows Defender (or endpoint AV) real-time protection is enabled.',
        'powershell': 'Set-MpPreference -DisableRealtimeMonitoring $false',
    },
    'PDC-05': {
        'title': 'Close Risky Ports',
        'advice': 'Restrict access to database and management ports using firewall rules.',
        'powershell': "New-NetFirewallRule -DisplayName 'Block SMB' -Direction Inbound -LocalPort 445 -Action Block -Protocol TCP",
    },
}


def get_remediation(check_id: str) -> Dict[str, Any] | None:
    return REMEDIATIONS.get(check_id)
