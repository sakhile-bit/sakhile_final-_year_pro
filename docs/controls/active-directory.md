# Active Directory Hygiene — `AD-01` … `AD-07`

**Source:** `src/security/active_directory/checks.py` (`ADAuditor`)
**Layer:** Infrastructure (Windows Active Directory domain)
**Grade:** `HEALTHY` (score ≥ 85 %, no critical failures) → `NEEDS ATTENTION`
(score ≥ 55 %) → `AT RISK`. Any CRITICAL failure forces `AT RISK`.

Read-only LDAP checks against a domain, targeting the misconfigurations that
let attackers move laterally or escalate. Everything degrades gracefully: no
`ldap3` installed, a non-domain-joined host, or a failed bind all produce
`SKIP`/`ERROR` findings (reported under `AD-00` / `AD-01`) rather than crashing.

| ID | Control | Severity | What it verifies |
|----|---------|----------|------------------|
| `AD-01` | Directory Connectivity | HIGH | An authenticated LDAP bind to the domain succeeds. Gate for all later checks. |
| `AD-02` | Stale Accounts | MEDIUM | No enabled user account has been idle beyond `stale_days` (default 90) — measured from `lastLogonTimestamp`. |
| `AD-03` | Domain Admins Size | CRITICAL | `Domain Admins` membership ≤ `max_domain_admins` (default 5). Excess standing admins widen the blast radius. |
| `AD-04` | Machine Account Quota | HIGH | `ms-DS-MachineAccountQuota` is 0 — any authenticated user joining computers enables resource-based constrained delegation (RBCD) attacks. |
| `AD-05` | krbtgt Password Age | MEDIUM | The `krbtgt` key was rotated within 180 days (old keys make forged golden tickets valid indefinitely). |
| `AD-06` | Risky Account Flags | HIGH | No enabled account carries `PASSWD_NOTREQD` or reversible-encryption (`ENCRYPTED_TEXT_PWD_ALLOWED`); non-expiring passwords flagged as a warning. |
| `AD-07` | Anonymous LDAP Bind | MEDIUM | The directory refuses an unauthenticated bind that can read objects (no credential-free domain enumeration). |

> `AD-00` is a **SKIP placeholder** emitted when the `ldap3` library is missing
> or the host is not domain-joined — it is not a check, just an explanation.

## Configuration

`ADAuditor(domain, user, password, use_ssl=False, stale_days=90,
max_domain_admins=5)`:

- `user` as `DOMAIN\user` triggers NTLM auth; a UPN/DN uses simple bind; blank
  attempts an anonymous bind.
- `use_ssl=True` binds over LDAPS (636) instead of LDAP (389).
- The domain is auto-detected on a joined Windows host when omitted.

A single connection is reused across checks; each check is individually
defensive so one failure cannot abort the run.

---
**Feature docs:** [16 Active Directory Checks](../features/16-active-directory-checks.md) · [controls catalogue](README.md)
