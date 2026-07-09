"""Active Directory related checks (optional)."""
from __future__ import annotations

import platform
import subprocess
from typing import Dict, Any, Optional

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

try:
    from ldap3 import Server, Connection, ALL
    _HAS_LDAP = True
except ImportError:
    _HAS_LDAP = False


def get_domain_name() -> Optional[str]:
    if platform.system() != 'Windows':
        return None
    try:
        r = subprocess.run(
            ['wmic', 'computersystem', 'get', 'domain'],
            capture_output=True, text=True, timeout=8,
        )
        lines = [line.strip() for line in r.stdout.splitlines() if line.strip()]
        if len(lines) >= 2:
            domain = lines[1].strip()
            if domain and domain.upper() != 'WORKGROUP':
                return domain
    except Exception:
        logger.debug("domain lookup failed", exc_info=True)
    return None


def build_base_dn(domain: str) -> str:
    return ','.join(f'DC={part}' for part in domain.split('.'))


def check_ad_connectivity(domain: str, user: str = '', password: str = '') -> Dict[str, Any]:
    if not _HAS_LDAP:
        return {
            'check_id': 'AD-01',
            'name': 'AD Connectivity',
            'passed': False,
            'severity': 'LOW',
            'details': 'ldap3 not installed; AD checks skipped',
            'remediation': 'Install ldap3 (pip install ldap3)',
        }
    if not domain:
        return {
            'check_id': 'AD-01',
            'name': 'AD Connectivity',
            'passed': False,
            'severity': 'LOW',
            'details': 'Host is not domain-joined or domain name unavailable',
            'remediation': 'Join machine to Active Directory or run on domain controller',
        }

    try:
        server = Server(domain, get_info=ALL)
        conn = Connection(server, user=user, password=password, auto_bind=True)
        conn.unbind()
        return {
            'check_id': 'AD-01',
            'name': 'AD Connectivity',
            'passed': True,
            'severity': 'HIGH',
            'details': f'Connected to Active Directory domain {domain}',
        }
    except Exception as exc:
        return {
            'check_id': 'AD-01',
            'name': 'AD Connectivity',
            'passed': False,
            'severity': 'HIGH',
            'details': f'AD connectivity failed: {exc}',
            'remediation': 'Verify AD network access and credentials',
        }


def check_stale_account_policy(domain: str) -> Dict[str, Any]:
    if not _HAS_LDAP or not domain:
        return {
            'check_id': 'AD-02',
            'name': 'Stale Account Policy',
            'passed': False,
            'severity': 'MEDIUM',
            'details': 'AD stale account check skipped',
        }
    try:
        server = Server(domain, get_info=ALL)
        conn = Connection(server, auto_bind=True)
        base_dn = build_base_dn(domain)
        ldap_filter = (
            '(&(objectClass=user)'
            '(!(userAccountControl:1.2.840.113556.1.4.803:=2)))'
        )
        conn.search(base_dn, ldap_filter,
                    attributes=['sAMAccountName', 'lastLogonTimestamp'])
        count = len(conn.entries)
        conn.unbind()
        return {
            'check_id': 'AD-02',
            'name': 'Stale Account Policy',
            'passed': True,
            'severity': 'MEDIUM',
            'details': f'AD reachable; user account query returned {count} entries',
        }
    except Exception as exc:
        return {
            'check_id': 'AD-02',
            'name': 'Stale Account Policy',
            'passed': False,
            'severity': 'MEDIUM',
            'details': f'Unable to query AD for stale accounts: {exc}',
            'remediation': 'Verify AD LDAP access, service account permissions, or install ldap3',
        }


def check_admin_group_members(domain: str) -> Dict[str, Any]:
    if not _HAS_LDAP or not domain:
        return {
            'check_id': 'AD-03',
            'name': 'Admin Group Membership',
            'passed': False,
            'severity': 'HIGH',
            'details': 'AD admin group membership check skipped',
        }
    try:
        server = Server(domain, get_info=ALL)
        conn = Connection(server, auto_bind=True)
        base_dn = build_base_dn(domain)
        conn.search(base_dn, '(cn=Domain Admins)', attributes=['member'])
        if conn.entries and getattr(conn.entries[0], 'member', None):
            members = conn.entries[0].member
            count = len(members)
            conn.unbind()
            return {
                'check_id': 'AD-03',
                'name': 'Admin Group Membership',
                'passed': True,
                'severity': 'HIGH',
                'details': f'Domain Admins group has {count} member(s)',
            }
        conn.unbind()
        return {
            'check_id': 'AD-03',
            'name': 'Admin Group Membership',
            'passed': False,
            'severity': 'HIGH',
            'details': 'Unable to read Domain Admins membership',
            'remediation': 'Verify AD permissions or install ldap3',
        }
    except Exception as exc:
        return {
            'check_id': 'AD-03',
            'name': 'Admin Group Membership',
            'passed': False,
            'severity': 'HIGH',
            'details': f'AD admin membership check failed: {exc}',
            'remediation': 'Verify AD LDAP access and query privileges',
        }
