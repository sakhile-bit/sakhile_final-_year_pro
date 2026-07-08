# Feature: Server Hardening Audit

## Overview
End-user awareness is pointless when the infrastructure serving those users is soft — *"charity begins at home"* applies to the service provider too. The Server Hardening Audit assesses the **Windows host that provides services to end users** (file server, application server, POS back office, domain controller) against **14 server-grade hardening baselines** and produces a `HARDENED` / `NEEDS ATTENTION` / `AT RISK` grade.

All checks are **read-only and registry-first**, so they work without administrator rights wherever Windows allows it; checks that need elevation degrade to a `WARNING` instead of crashing.

**GUI file:** [`src/gui/screens/server_hardening.py`](../../src/gui/screens/server_hardening.py)
**Engine file:** [`src/security/hardening/checks.py`](../../src/security/hardening/checks.py)
**CLI:** `python cli.py harden [--json-out] [--output report.json]`
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

## GUI

Welcome screen → **🛡️ Server Hardening** tile. Runs all 14 checks in a
background thread with live progress, then shows:

- **Grade hero** (HARDENED / NEEDS ATTENTION / AT RISK) with score percentage
- **Summary strip** — passed / warnings / failed / critical / hostname
- **Check cards** sorted failures-first, each with severity badge, plain-English
  details and a "Fix:" panel containing the PowerShell remediation
- **Export Report** — standalone dark-theme HTML report

## Tests

[`tests/test_hardening.py`](../../tests/test_hardening.py) — 29 tests covering
grade/scoring logic, per-check PASS/WARNING/FAIL branches with mocked registry
and service state, non-Windows degradation, and remediation-catalogue coverage.
