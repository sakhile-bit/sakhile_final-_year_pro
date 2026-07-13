# Windows Hardening Audit — `HRD-01` … `HRD-14`

**Source:** `src/security/hardening/checks.py` (`WindowsHardeningAuditor`)
**Auto-fix:** `src/security/hardening/fixes.py`
**Layer:** Infrastructure (the Windows host that *provides* services)
**Grade:** `HARDENED` (score ≥ 85 % and 0 critical failures) → `NEEDS ATTENTION`
(score ≥ 60 % and ≤ 1 critical failure) → `AT RISK`.

All checks are **read-only and registry-first**, so they work without
administrator rights wherever Windows allows it. Checks that need elevation
degrade to a `WARNING` rather than crashing. Non-Windows hosts return
`NOT_APPLICABLE`.

| ID | Control | Severity | Category | What it verifies |
|----|---------|----------|----------|------------------|
| `HRD-01` | SMBv1 Protocol Disabled | CRITICAL | protocol | SMBv1 server protocol is off (the WannaCry / EternalBlue vector). |
| `HRD-02` | SMB Signing Required | HIGH | protocol | SMB signing required on server **and** client (blocks NTLM relay / MITM). |
| `HRD-03` | Remote Desktop Hardening | HIGH | remote-access | RDP disabled, or Network Level Authentication required and no legacy security layer. |
| `HRD-04` | User Account Control (UAC) | HIGH | credentials | `EnableLUA` on and not set to elevate-without-prompting. |
| `HRD-05` | LLMNR / NetBIOS-NS Disabled | HIGH | protocol | Multicast name resolution off (defeats Responder-style hash capture). |
| `HRD-06` | PowerShell Logging Enabled | MEDIUM | logging | Script-block logging enabled (forensic trail for intrusions). |
| `HRD-07` | Legacy TLS Disabled (Server) | MEDIUM | protocol | TLS 1.0 / 1.1 explicitly disabled in Schannel server keys. |
| `HRD-08` | No Unquoted Service Paths | HIGH | services | No service `ImagePath` with spaces is left unquoted (SYSTEM privilege-escalation). |
| `HRD-09` | Print Spooler Exposure | MEDIUM | services | Spooler disabled on servers (PrintNightmare). |
| `HRD-10` | Remote Registry Disabled | MEDIUM | services | RemoteRegistry service disabled/absent (remote recon & tampering). |
| `HRD-11` | Logon Audit Policy | MEDIUM | logging | Logon events audited for **both** success and failure. |
| `HRD-12` | Local Account Hygiene | HIGH | credentials | Built-in Administrator/Guest disabled; few members of the Administrators group. |
| `HRD-13` | LSA Credential Protections | HIGH | credentials | LSA runs as a protected process; no LM hashes; NTLMv2 enforced (blocks Mimikatz). |
| `HRD-14` | Anonymous Enumeration Restricted | MEDIUM | credentials | `RestrictAnonymous` / `RestrictAnonymousSAM` set (no anonymous account harvesting). |

## Remediation & auto-fix

Every finding carries a PowerShell remediation snippet (see
`src/security/remediation/guidance.py`). The auto-fix engine
(`fixes.py`) offers **one-click remediation** for HRD findings, classified:

- **safe** — no impact on normal SME workflows.
- **caution** — may affect printing or very old devices; applied only with
  explicit user consent.

Every fix records the previous registry value / service state in an undo
journal (`%APPDATA%/ZambiaDigitalHygiene/fix_journal.json`) so any run can be
reverted with `revert_last()`. Fixes require administrator rights
(`fixes.is_admin()`).

**CLI:** `harden` (exit 0 = HARDENED, 1 otherwise), `harden --fix`,
`harden --undo-last`.

---
**Feature docs:** [19 Server Hardening Audit](../features/19-server-hardening.md) · [13 Remediation Guidance](../features/13-remediation-guidance.md) · [controls catalogue](README.md)
