# Feature: Active Directory Hygiene

## Overview
The Active Directory module runs read-only LDAP checks against a Windows AD
domain and rolls them into a **HEALTHY / NEEDS ATTENTION / AT RISK** grade —
the same verdict model as the Server Hardening audit. It targets the
misconfigurations attackers actually abuse for lateral movement and privilege
escalation. It is **optional and safe to run anywhere**: no `ldap3`, a
non-domain-joined host, or a failed bind all yield SKIP/ERROR findings rather
than crashing.

**Engine:** [`src/security/active_directory/checks.py`](../../src/security/active_directory/checks.py) — `ADAuditor` / `run_ad_audit()`
**GUI:** [`src/gui/screens/active_directory.py`](../../src/gui/screens/active_directory.py)

> Note (July 2026): this replaced an earlier version where the GUI was a static
> mock-up whose "Run" button only printed to the console, and the engine's
> "stale account" check never actually measured staleness. Both are now real.

---

## Prerequisites
```bash
pip install ldap3
```
Bundled in the packaged `.exe`. The bind account needs only **read** access to
the directory — use a dedicated read-only service account, never a Domain
Admin. Credentials are optional in the UI: `DOMAIN\user` uses NTLM, a UPN/DN
uses a simple bind, and blank attempts an unauthenticated bind.

---

## The checks

| ID | Check | Severity | What it catches |
|---|---|---|---|
| AD-01 | Directory Connectivity | HIGH | Can we bind to the domain at all |
| AD-02 | Stale Accounts | MEDIUM | Enabled accounts idle **> stale_days** (default 90) — computed from `lastLogonTimestamp`, paged search |
| AD-03 | Domain Admins Size | CRITICAL | More than `max_domain_admins` (default 5) standing Domain Admins — widens blast radius |
| AD-04 | Machine Account Quota | HIGH | `ms-DS-MachineAccountQuota > 0` — any user can join computers (RBCD attacks) |
| AD-05 | krbtgt Password Age | MEDIUM | krbtgt key older than 180 days — long-lived golden-ticket risk |
| AD-06 | Risky Account Flags | HIGH | Enabled accounts with `PASSWD_NOTREQD`, reversible-encryption, or non-expiring passwords |
| AD-07 | Anonymous LDAP Bind | MEDIUM | The directory lets an unauthenticated client read objects |

`ADAuditor` opens one reused connection, runs each check defensively (one
failure never aborts the rest), and uses **paged search** so counts aren't
capped at the AD 1000-object limit. Windows FILETIME values are converted to
real datetimes via `_filetime_to_dt`.

---

## Grade logic
```
Score:  PASS = 1 · WARN/ERROR = ½ · FAIL = 0   (SKIP excluded)

AT RISK          when any CRITICAL finding fails, OR score < 55
HEALTHY          when score ≥ 85 and no CRITICAL failure
NEEDS ATTENTION  otherwise
```

---

## API
```python
from src.security.active_directory import run_ad_audit

report = run_ad_audit(domain="corp.example.com",
                      user="CORP\\svc-audit", password="…",
                      stale_days=90, max_domain_admins=5)
print(report.grade, report.score_percent)      # e.g. "NEEDS ATTENTION" 71
for f in report.findings:
    print(f.check_id, f.status, f.name)
report.to_dict()                               # JSON-serialisable
```

`get_domain_name()` (auto-detects the joined domain via CIM, wmic fallback) and
`build_base_dn()` remain available, plus a backward-compatible
`check_ad_connectivity()` returning a single result dict.

---

## GUI
Tools → **Active Directory Hygiene**. A connection bar (domain — auto-prefilled
in the background — username, password) drives a threaded audit that renders a
grade hero, a passed/warnings/failed summary, and prioritised finding cards with
plain-language "Fix:" remediation. Progress and results animate
([UI Motion](21-ui-motion.md)).

---

## Testing
[`tests/test_active_directory.py`](../../tests/test_active_directory.py) — 15
tests with an in-memory fake `ldap3` connection (runs on any OS): grade/score
model, ldap3-missing and non-domain-joined SKIP paths, bind-failure ERROR, and
each check's PASS/FAIL branch (stale accounts, oversized Domain Admins, open
machine-account quota, old krbtgt, risky flags, anonymous bind).

---

## Related Features
- [Server Hardening Audit](19-server-hardening.md) — host-level companion with the same grade model
- [Windows Agent](10-windows-agent.md)
