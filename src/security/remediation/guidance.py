"""Remediation guidance mapping for common checks.

Provides human-friendly remediation text and optional PowerShell snippets
operators can use to remediate common findings on Windows hosts.

Covers the pre-deployment checks (PDC-xx) and the infrastructure
hardening audit (HRD-xx).
"""
from __future__ import annotations

from typing import Dict, Any


REMEDIATIONS: Dict[str, Dict[str, Any]] = {
    # ── Pre-deployment checks ─────────────────────────────────────────
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
    'PDC-04': {
        'title': 'Enable Disk Encryption',
        'advice': 'Enable BitLocker on the system drive so data is protected if the device is stolen.',
        'powershell': 'Enable-BitLocker -MountPoint C: -EncryptionMethod XtsAes256 -UsedSpaceOnly',
    },
    'PDC-05': {
        'title': 'Close Risky Ports',
        'advice': 'Restrict access to database and management ports using firewall rules.',
        'powershell': (
            "New-NetFirewallRule -DisplayName 'Block SMB'"
            " -Direction Inbound -LocalPort 445 -Action Block -Protocol TCP"
        ),
    },
    'PDC-06': {
        'title': 'Protect Secrets',
        'advice': 'Move credentials out of source files into environment variables or a secrets manager; '
                  'rotate any secret that was committed to version control.',
        'powershell': None,
    },

    # ── Infrastructure hardening checks ───────────────────────────────
    'HRD-01': {
        'title': 'Disable SMBv1',
        'advice': 'SMBv1 is the protocol exploited by WannaCry/EternalBlue. No modern system needs it.',
        'powershell': 'Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force; '
                      'Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart',
    },
    'HRD-02': {
        'title': 'Require SMB Signing',
        'advice': 'SMB signing stops NTLM-relay and man-in-the-middle attacks on file sharing.',
        'powershell': 'Set-SmbServerConfiguration -RequireSecuritySignature $true -Force; '
                      'Set-SmbClientConfiguration -RequireSecuritySignature $true -Force',
    },
    'HRD-03': {
        'title': 'Harden Remote Desktop',
        'advice': 'Require Network Level Authentication for RDP, or disable RDP entirely if unused. '
                  'Never expose port 3389 directly to the internet — use a VPN.',
        'powershell': "Set-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' "
                      "-Name UserAuthentication -Value 1",
    },
    'HRD-04': {
        'title': 'Enable User Account Control',
        'advice': 'UAC stops malware from silently gaining administrator rights.',
        'powershell': "Set-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' "
                      "-Name EnableLUA -Value 1  # restart required",
    },
    'HRD-05': {
        'title': 'Disable LLMNR and NetBIOS-NS',
        'advice': 'These legacy name-resolution protocols let attackers on your network capture '
                  'password hashes with tools like Responder.',
        'powershell': "New-Item -Force 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient' | Out-Null; "
                      "Set-ItemProperty 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient' "
                      "-Name EnableMulticast -Value 0",
    },
    'HRD-06': {
        'title': 'Enable PowerShell Logging',
        'advice': 'Script-block logging records attacker PowerShell activity — essential evidence '
                  'for incident response.',
        'powershell': "New-Item -Force 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\PowerShell\\ScriptBlockLogging' | Out-Null; "
                      "Set-ItemProperty 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\PowerShell\\ScriptBlockLogging' "
                      "-Name EnableScriptBlockLogging -Value 1",
    },
    'HRD-07': {
        'title': 'Disable Legacy TLS (Server)',
        'advice': 'TLS 1.0/1.1 are deprecated. Servers that terminate TLS should disable them explicitly.',
        'powershell': "New-Item -Force 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\Schannel\\Protocols\\TLS 1.0\\Server' | Out-Null; "
                      "Set-ItemProperty that key -Name Enabled -Value 0  # repeat for 'TLS 1.1\\Server'",
    },
    'HRD-08': {
        'title': 'Quote Service Paths',
        'advice': 'Unquoted service paths containing spaces let local users plant a binary that '
                  'runs as SYSTEM. Wrap each flagged ImagePath in quotes.',
        'powershell': "Set-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\<name>' "
                      "-Name ImagePath -Value '\"C:\\Program Files\\App\\service.exe\"'",
    },
    'HRD-09': {
        'title': 'Disable Print Spooler (Servers)',
        'advice': 'The Print Spooler service (PrintNightmare) should be disabled on any server '
                  'that does not print.',
        'powershell': 'Stop-Service Spooler; Set-Service Spooler -StartupType Disabled',
    },
    'HRD-10': {
        'title': 'Disable Remote Registry',
        'advice': 'The Remote Registry service allows remote reconnaissance and tampering.',
        'powershell': 'Stop-Service RemoteRegistry; Set-Service RemoteRegistry -StartupType Disabled',
    },
    'HRD-11': {
        'title': 'Enable Logon Auditing',
        'advice': 'Audit both successful and failed logons so brute-force attempts and intrusions '
                  'leave a record in the event log.',
        'powershell': 'auditpol /set /subcategory:"Logon" /success:enable /failure:enable',
    },
    'HRD-12': {
        'title': 'Clean Up Local Accounts',
        'advice': 'Disable the built-in Administrator and Guest accounts, and remove day-to-day '
                  'users from the Administrators group (least privilege).',
        'powershell': 'Disable-LocalUser Administrator; Disable-LocalUser Guest',
    },
    'HRD-13': {
        'title': 'Harden LSA Credential Protection',
        'advice': 'Running LSA as a protected process and refusing LM/NTLMv1 blocks '
                  'Mimikatz-style credential theft.',
        'powershell': "Set-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' -Name RunAsPPL -Value 1; "
                      "Set-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' -Name LmCompatibilityLevel -Value 5",
    },
    'HRD-14': {
        'title': 'Restrict Anonymous Enumeration',
        'advice': 'Stop anonymous users from listing accounts and shares — attackers use this '
                  'to harvest usernames for password attacks.',
        'powershell': "Set-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' -Name RestrictAnonymous -Value 1; "
                      "Set-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' -Name RestrictAnonymousSAM -Value 1",
    },
}


def get_remediation(check_id: str) -> Dict[str, Any] | None:
    return REMEDIATIONS.get(check_id)
