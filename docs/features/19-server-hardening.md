# Feature: Server Hardening Audit

## Overview
End-user awareness is pointless when the infrastructure serving those users is soft — *"charity begins at home"* applies to the service provider too. The Server Hardening Audit assesses the **Windows host that provides services to end users** (file server, application server, POS back office, domain controller) against **14 server-grade hardening baselines** and produces a `HARDENED` / `NEEDS ATTENTION` / `AT RISK` grade.

All checks are **read-only and registry-first**, so they work without administrator rights wherever Windows allows it; checks that need elevation degrade to a `WARNING` instead of crashing.

Since July 2026 the audit is no longer read-only advice: **one-click auto-remediation** can apply and later undo the fixes for most findings (see below).

**GUI file:** [`src/gui/screens/server_hardening.py`](../../src/gui/screens/server_hardening.py)
**Engine file:** [`src/security/hardening/checks.py`](../../src/security/hardening/checks.py)
**Fix engine:** [`src/security/hardening/fixes.py`](../../src/security/hardening/fixes.py)
**CLI:** `python cli.py harden [--json-out] [--output report.json] [--fix HRD-XX] [--fix-all-safe] [--include-caution] [--undo-last] [--list-fixes]`
**Agent:** included automatically in `windows_agent.collect_local_report()` under the `hardening` key

---

## Grade Logic

```
Score:  PASS = 1 point · WARNING/ERROR = ½ point · FAIL = 0
        score_percent = points / applicable_checks × 100

HARDENED         when  score ≥ 85%  AND  critical_failures == 0
NEEDS ATTENTION  when  score ≥ 60%  AND  critical_failures ≤ 1
AT RISK          otherwise
```

`NOT_APPLICABLE` checks (non-Windows hosts) are excluded from scoring.
CLI exit code: `0` = HARDENED, `1` otherwise — usable as a CI/CD or scheduled-task gate.

---

## The 14 Checks

| ID | Name | Severity | Attack it blocks | How it checks |
|---|---|---|---|---|
| HRD-01 | SMBv1 Disabled | CRITICAL | WannaCry / EternalBlue | `LanmanServer\Parameters\SMB1` registry, PowerShell `Get-SmbServerConfiguration` fallback |
| HRD-02 | SMB Signing Required | HIGH | NTLM relay, SMB tampering | `RequireSecuritySignature` on LanmanServer + LanmanWorkstation |
| HRD-03 | RDP Hardening | HIGH | BlueKeep, RDP brute-force | `fDenyTSConnections`, `UserAuthentication` (NLA), `SecurityLayer` |
| HRD-04 | UAC Enabled | HIGH | Silent privilege escalation | `EnableLUA`, `ConsentPromptBehaviorAdmin` |
| HRD-05 | LLMNR / NetBIOS-NS Disabled | HIGH | Responder-style hash capture | `DNSClient\EnableMulticast`, per-interface `NetbiosOptions` |
| HRD-06 | PowerShell Logging | MEDIUM | Untraceable attacker activity | `ScriptBlockLogging`, `ModuleLogging` policy keys |
| HRD-07 | Legacy TLS Disabled (Server) | MEDIUM | Protocol downgrade | Schannel `TLS 1.0/1.1\Server\Enabled` |
| HRD-08 | No Unquoted Service Paths | HIGH | Local SYSTEM escalation | Enumerates `Services\*\ImagePath` for unquoted paths with spaces |
| HRD-09 | Print Spooler Exposure | MEDIUM | PrintNightmare | `sc query Spooler` + server-edition detection |
| HRD-10 | Remote Registry Disabled | MEDIUM | Remote recon/tampering | `sc query/qc RemoteRegistry` |
| HRD-11 | Logon Audit Policy | MEDIUM | Invisible brute-force | `auditpol /get /subcategory:Logon` (WARNING without admin) |
| HRD-12 | Local Account Hygiene | HIGH | Default-account abuse | `Get-LocalUser` (built-in Administrator/Guest), Administrators group size |
| HRD-13 | LSA Credential Protections | HIGH | Mimikatz credential dumping | `RunAsPPL`, `NoLMHash`, `LmCompatibilityLevel` |
| HRD-14 | Anonymous Enumeration Restricted | MEDIUM | Username harvesting | `RestrictAnonymous`, `RestrictAnonymousSAM` |

---

## Data Structures

```python
@dataclass
class HardeningCheckResult:
    check_id: str      # HRD-01 .. HRD-14
    name: str
    status: str        # PASS, WARNING, FAIL, ERROR, NOT_APPLICABLE
    severity: str      # CRITICAL, HIGH, MEDIUM, LOW
    details: str       # plain-English finding
    remediation: str   # actionable fix with PowerShell snippet
    category: str      # protocol | remote-access | credentials | services | logging

@dataclass
class HardeningReport:
    checks: List[HardeningCheckResult]
    # computed: total, passed, warnings, failed, critical_failures,
    #           score_percent, grade — plus to_dict() for JSON export
```

---

## Remediation

Every check carries an inline PowerShell fix, and each `HRD-xx` ID is also
registered in the central remediation catalogue
([`src/security/remediation/guidance.py`](../../src/security/remediation/guidance.py))
via `get_remediation("HRD-05")` → `{title, advice, powershell}`.

## One-Click Auto-Remediation

The audit can now *fix* what it finds, not just report it — aimed at
non-technical SME owners who cannot translate a PowerShell snippet into action.

**Engine:** [`src/security/hardening/fixes.py`](../../src/security/hardening/fixes.py)
provides a `FixAction` registry keyed by check ID. Each fix writes exactly the
registry value / service state its check reads, so a re-audit immediately
reflects the repair.

Fixes are classified into two tiers:

- **safe** — no impact on normal SME workflows (SMBv1, SMB signing, RDP/NLA,
  UAC, LLMNR/NetBIOS, PowerShell logging, Remote Registry, logon auditing, LSA,
  anonymous enumeration). Applied in bulk by *Fix All Safe Issues*.
- **caution** — may affect printing or very old clients (Print Spooler,
  legacy TLS). Applied only after the user reads and confirms the warning.

Two checks have **no** auto-fix because they need human judgement:
`HRD-08` (unquoted service paths — quoting must be verified per service) and
`HRD-12` (local accounts — disabling accounts can lock users out).

**Safety guarantees**

- Requires Administrator rights (`fixes.is_admin()`); buttons/commands are
  disabled otherwise with a clear "Run as administrator" message.
- Every change is recorded in an **undo journal** at
  `%APPDATA%/ZambiaDigitalHygiene/fix_journal.json` *before* it is applied.
  `revert_last()` (GUI **Undo Last Fix**, CLI `--undo-last`) restores the
  previous registry values / service states — including deleting values that
  did not exist before.
- Idempotent: applying a fix that is already compliant makes no change and
  writes no journal entry.

**CLI examples**

```
harden --list-fixes                 # show every fixable finding + tier
harden --fix-all-safe               # audit, then apply all safe fixes (admin)
harden --fix HRD-05 --fix HRD-10    # fix specific findings
harden --fix-all-safe --include-caution   # also apply caution-tier fixes
harden --undo-last                  # roll back the most recent fix run
```

After applying fixes the CLI re-audits and prints the new grade; the exit code
reflects the post-fix state.

## GUI

Welcome screen → **🛡️ Server Hardening** tile. Runs all 14 checks in a
background thread with live progress, then shows:

- **Grade hero** (HARDENED / NEEDS ATTENTION / AT RISK) with score percentage
- **Summary strip** — passed / warnings / failed / critical / hostname
- **One-click fix bar** — *Fix All Safe Issues (N)*, *Review Advanced Fixes*
  (caution tier, behind a confirmation modal) and *Undo Last Fix*; disabled
  with guidance when not running as Administrator
- **Check cards** sorted failures-first, each with severity badge, plain-English
  details, a "Fix:" panel with the PowerShell remediation, and a **🔧 Fix Now**
  button when an auto-fix exists. Applying a fix re-runs the audit automatically.
- **Export Report** — standalone dark-theme HTML report

## Tests

[`tests/test_hardening.py`](../../tests/test_hardening.py) — 29 tests covering
grade/scoring logic, per-check PASS/WARNING/FAIL branches with mocked registry
and service state, non-Windows degradation, and remediation-catalogue coverage.

[`tests/test_fixes.py`](../../tests/test_fixes.py) — 17 tests covering the
auto-fix engine with in-memory registry/service fakes: safe/caution tiering,
registry and service application, journal recording, idempotency, admin and
non-Windows refusal, and full undo (including value-deletion and service-state
restore). Runs on any OS.
