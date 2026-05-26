"""Monitoring and log hygiene checks."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from typing import Dict, Any


def _has_command(name: str) -> bool:
    return shutil.which(name) is not None


def get_logging_hygiene() -> Dict[str, Any]:
    """Return logging/monitoring hygiene status for the current host."""
    result: Dict[str, Any] = {
        'status': 'unknown',
        'details': [],
        'passed': False,
        'severity': 'LOW',
    }

    if platform.system() == 'Windows':
        # Check Windows Event Log service status via wevtutil
        try:
            r = subprocess.run(
                ['wevtutil', 'gl', 'Application'],
                capture_output=True, text=True, timeout=8,
            )
            if r.returncode == 0 and 'channel' in r.stdout.lower():
                result['details'].append('Windows Event Log service is available')
            else:
                result['details'].append('Unable to verify Windows Event Log configuration')
        except Exception:
            result['details'].append('Windows Event Log service could not be queried')

        # Detect common log-forwarding agents
        agents = ['nxlog', 'snare', 'winlogbeat', 'syslog-ng']
        found = [name for name in agents if _has_command(name)]
        if found:
            result['details'].append(f'Log forwarding agent installed: {", ".join(found)}')
        else:
            result['details'].append('No common log forwarding agent detected')

    else:
        if _has_command('journalctl'):
            result['details'].append('systemd journal available')
        elif _has_command('rsyslogd') or _has_command('syslog-ng'):
            result['details'].append('Syslog daemon detected')
        else:
            result['details'].append('No journal or syslog daemon detected')

        try:
            r = subprocess.run(['logger', '-p', 'user.info', 'test log'], timeout=5)
            if r.returncode == 0:
                result['details'].append('Local syslog logging is functional')
        except Exception:
            result['details'].append('Unable to validate local syslog logging')

    result['passed'] = any('available' in detail or 'functional' in detail for detail in result['details'])
    result['status'] = 'PASS' if result['passed'] else 'FAIL'
    result['severity'] = 'MEDIUM' if not result['passed'] else 'LOW'
    return result
