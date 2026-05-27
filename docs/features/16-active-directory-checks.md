# Feature: Active Directory Checks

## Overview
The Active Directory module performs LDAP-based security checks against a Windows Active Directory domain. It is an **optional** feature — checks are gracefully skipped when the host is not domain-joined or when the `ldap3` library is not installed.

**File:** [`src/security/active_directory/checks.py`](../../src/security/active_directory/checks.py)

---

## Prerequisites

```bash
pip install ldap3
```

The module uses `ldap3` v2.9.1+ for all LDAP operations. If the library is absent, all check functions still return valid result dicts with `passed=False` and a clear explanation message — the application never crashes.

---

## Helper Functions

### `get_domain_name() -> Optional[str]`

Reads the current machine's domain name via:
```powershell
wmic computersystem get domain
```
Returns `None` if the host is in `WORKGROUP` or if WMI fails.

### `build_base_dn(domain: str) -> str`

Converts a domain FQDN to an LDAP base DN:
```python
build_base_dn('corp.example.com')
# → 'DC=corp,DC=example,DC=com'
```

---

## Check Functions

### AD-01 — AD Connectivity (`check_ad_connectivity`)

```python
from src.security.active_directory.checks import check_ad_connectivity, get_domain_name

domain = get_domain_name()
result = check_ad_connectivity(domain, user='svc-account@corp.example.com', password='...')
```

**What it does:**
1. Creates a `Server` object pointing at the domain controller
2. Opens an `auto_bind` connection (Kerberos or simple auth)
3. Unbinds and reports success

**Result:**
```python
{
    'check_id':    'AD-01',
    'name':        'AD Connectivity',
    'passed':      True,
    'severity':    'HIGH',
    'details':     'Connected to Active Directory domain corp.example.com',
}
```

---

### AD-02 — Stale Account Policy (`check_stale_account_policy`)

```python
result = check_stale_account_policy(domain)
```

**What it does:**  
Searches the domain for all **enabled user accounts** using the LDAP filter:
```
(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))
```
Returns the count of enabled accounts. In a full implementation this would also compare `lastLogonTimestamp` against a 90-day threshold to surface stale accounts.

**Severity:** MEDIUM

---

### AD-03 — Admin Group Membership (`check_admin_group_members`)

```python
result = check_admin_group_members(domain)
```

**What it does:**  
Searches for the `Domain Admins` group and returns its member count.

```python
{
    'check_id': 'AD-03',
    'name':     'Admin Group Membership',
    'passed':   True,
    'severity': 'HIGH',
    'details':  'Domain Admins group has 3 member(s)',
}
```

**Severity:** HIGH — excessive Domain Admin membership is a critical finding.

---

## Graceful Fallback

When `ldap3` is not installed or the host is not domain-joined, all three functions return a standardised skip result:

```python
{
    'check_id':    'AD-01',
    'name':        'AD Connectivity',
    'passed':      False,
    'severity':    'LOW',
    'details':     'ldap3 not installed; AD checks skipped',
    'remediation': 'Install ldap3 (pip install ldap3)',
}
```

Severity is lowered to `LOW` for skipped checks so they don't inflate failure counts on workgroup machines.

---

## Including AD Checks in Agent Reports

```python
from src.agents.windows_agent import collect_local_report
from src.security.active_directory.checks import (
    get_domain_name,
    check_ad_connectivity,
    check_stale_account_policy,
    check_admin_group_members,
)

result = collect_local_report('Acme Ltd')
domain = get_domain_name()

if domain:
    result['report']['ad_checks'] = {
        'connectivity':  check_ad_connectivity(domain),
        'stale_accounts': check_stale_account_policy(domain),
        'admin_members': check_admin_group_members(domain),
    }
```

---

## Security Note

AD checks require **read-level LDAP access**. Use a dedicated **read-only service account** rather than a Domain Admin account. The account needs:
- `Read` permission on the domain root
- No write or admin permissions

---

## Related Features
- [Windows Agent](10-windows-agent.md) — can include AD checks in reports
- [Deployment Checker](07-deployment-checker.md) — system-level checks companion
