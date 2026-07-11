"""
Windows Hardening Auto-Fix Engine
=================================
One-click remediation for the hardening audit (HRD-xx) findings.

Every fix:
  * mirrors exactly the registry value / service state its check reads,
    so a re-audit immediately reflects the repair;
  * records the previous state in an undo journal
    (%APPDATA%/ZambiaDigitalHygiene/fix_journal.json) before changing
    anything, so every run can be reverted with ``revert_last()``;
  * is classified **safe** (no impact on normal SME workflows) or
    **caution** (may affect printing / very old devices) — callers apply
    caution fixes only with explicit user consent.

All writes target HKLM or service configuration and therefore require
administrator rights — ``is_admin()`` lets callers check before offering
the buttons.

Usage
-----
    from src.security.hardening import fixes

    fixes.is_admin()                    # -> bool
    fixes.available_fixes()             # -> {check_id: FixAction}
    results = fixes.apply_fixes(["HRD-01", "HRD-05"])
    ok, msg, details = fixes.revert_last()
"""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

IS_WINDOWS = platform.system() == "Windows"


# ---------------------------------------------------------------------------
# Low-level primitives — kept as module functions so tests can monkeypatch
# ---------------------------------------------------------------------------


def is_admin() -> bool:
    """True when the current process has administrator rights."""
    if not IS_WINDOWS:
        return False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _reg_read(path: str, name: str) -> Any:
    """Read an HKLM value. None when absent."""
    if not IS_WINDOWS:
        return None
    import winreg  # type: ignore[import]
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return value
    except OSError:
        return None


def _reg_write(path: str, name: str, value: int) -> None:
    """Write a DWORD to HKLM, creating the key path if needed."""
    import winreg  # type: ignore[import]
    with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0,
                            winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(value))


def _reg_delete(path: str, name: str) -> None:
    """Delete an HKLM value; silently ignore if already gone."""
    import winreg  # type: ignore[import]
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0,
                            winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, name)
    except OSError:
        pass


def _reg_subkeys(path: str) -> List[str]:
    if not IS_WINDOWS:
        return []
    import winreg  # type: ignore[import]
    names: List[str] = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    names.append(winreg.EnumKey(key, i))
                except OSError:
                    break
    except OSError:
        pass
    return names


def _sc(*args: str, timeout: int = 15) -> Tuple[int, str]:
    """Run an ``sc`` command; returns (returncode, stdout)."""
    try:
        r = subprocess.run(["sc", *args], capture_output=True, text=True,
                           timeout=timeout, shell=False)
        return r.returncode, r.stdout or ""
    except Exception as exc:
        logger.debug("sc %s failed", args, exc_info=True)
        return 1, str(exc)


def _svc_startup_type(name: str) -> str:
    """auto / demand / disabled / delayed-auto / unknown."""
    code, out = _sc("qc", name)
    if code != 0:
        return "unknown"
    m = re.search(r"START_TYPE\s*:\s*\d+\s+(\w+)", out)
    if not m:
        return "unknown"
    return {
        "AUTO_START": "auto",
        "DEMAND_START": "demand",
        "DISABLED": "disabled",
    }.get(m.group(1).upper(), "unknown")


def _svc_running(name: str) -> bool:
    code, out = _sc("query", name)
    return code == 0 and "RUNNING" in out.upper()


def _svc_set_startup(name: str, startup: str) -> bool:
    # sc requires the space after "start="
    code, _ = _sc("config", name, "start=", startup)
    return code == 0


def _svc_stop(name: str) -> bool:
    code, out = _sc("stop", name)
    # 1062 = already stopped — that is fine
    return code == 0 or "1062" in out


def _svc_start(name: str) -> bool:
    code, _ = _sc("start", name)
    return code == 0


def _auditpol_get_logon() -> str:
    """Current Logon subcategory setting, e.g. 'Success and Failure'."""
    try:
        r = subprocess.run(["auditpol", "/get", "/subcategory:Logon"],
                           capture_output=True, text=True, timeout=10,
                           shell=False)
        if r.returncode != 0:
            return "unknown"
        for token in ("Success and Failure", "Success", "Failure",
                      "No Auditing"):
            if token in r.stdout:
                return token
    except Exception:
        logger.debug("auditpol get failed", exc_info=True)
    return "unknown"


def _auditpol_set_logon(success: bool, failure: bool) -> bool:
    try:
        r = subprocess.run(
            ["auditpol", "/set", "/subcategory:Logon",
             f"/success:{'enable' if success else 'disable'}",
             f"/failure:{'enable' if failure else 'disable'}"],
            capture_output=True, text=True, timeout=10, shell=False)
        return r.returncode == 0
    except Exception:
        logger.debug("auditpol set failed", exc_info=True)
        return False


# ---------------------------------------------------------------------------
# Undo journal
# ---------------------------------------------------------------------------


def _journal_path() -> Path:
    base = Path(os.environ.get("APPDATA", str(Path.home())))
    return base / "ZambiaDigitalHygiene" / "fix_journal.json"


def _load_journal() -> List[Dict[str, Any]]:
    path = _journal_path()
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("fix journal unreadable — starting fresh",
                       exc_info=True)
    return []


def _save_journal(entries: List[Dict[str, Any]]) -> None:
    path = _journal_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def last_journal_entry() -> Optional[Dict[str, Any]]:
    """The most recent fix run that has not been reverted, if any."""
    for entry in reversed(_load_journal()):
        if not entry.get("reverted"):
            return entry
    return None


# ---------------------------------------------------------------------------
# Change helpers — apply a change AND record how to undo it
# ---------------------------------------------------------------------------


def _change_dword(path: str, name: str, value: int,
                  undo: List[Dict[str, Any]],
                  notes: List[str], note: str) -> None:
    old = _reg_read(path, name)
    if old == value:
        return
    _reg_write(path, name, value)
    undo.append({"kind": "reg", "path": path, "name": name,
                 "old": old, "new": value})
    notes.append(note)


def _change_service(name: str, undo: List[Dict[str, Any]],
                    notes: List[str], note: str) -> None:
    """Stop a service and set it to disabled, recording the previous state."""
    old_start = _svc_startup_type(name)
    was_running = _svc_running(name)
    if old_start == "disabled" and not was_running:
        return
    if was_running:
        _svc_stop(name)
    if not _svc_set_startup(name, "disabled"):
        raise RuntimeError(f"could not disable service {name}")
    undo.append({"kind": "service", "name": name,
                 "old_start": old_start, "was_running": was_running})
    notes.append(note)


# ---------------------------------------------------------------------------
# Individual fixes — each returns (undo_records, human_readable_changes)
# ---------------------------------------------------------------------------

_LANMAN_SRV = r"SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
_LANMAN_WKS = r"SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters"
_RDP_TCP = r"SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp"
_UAC = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
_DNSCLIENT = r"SOFTWARE\Policies\Microsoft\Windows NT\DNSClient"
_NETBT_IF = r"SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces"
_SBL = r"SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
_SCHANNEL = (r"SYSTEM\CurrentControlSet\Control\SecurityProviders"
             r"\Schannel\Protocols")
_LSA = r"SYSTEM\CurrentControlSet\Control\Lsa"


def _fix_smb1(undo, notes):
    _change_dword(_LANMAN_SRV, "SMB1", 0, undo, notes,
                  "SMBv1 server protocol disabled (registry SMB1=0)")


def _fix_smb_signing(undo, notes):
    _change_dword(_LANMAN_SRV, "RequireSecuritySignature", 1, undo, notes,
                  "SMB signing now required for the server side")
    _change_dword(_LANMAN_WKS, "RequireSecuritySignature", 1, undo, notes,
                  "SMB signing now required for the client side")


def _fix_rdp_nla(undo, notes):
    deny = _reg_read(r"SYSTEM\CurrentControlSet\Control\Terminal Server",
                     "fDenyTSConnections")
    if deny == 1:
        notes.append("Remote Desktop is already disabled — nothing to change")
        return
    _change_dword(_RDP_TCP, "UserAuthentication", 1, undo, notes,
                  "Network Level Authentication now required for RDP")
    if _reg_read(_RDP_TCP, "SecurityLayer") == 0:
        _change_dword(_RDP_TCP, "SecurityLayer", 2, undo, notes,
                      "RDP switched from legacy security layer to TLS")


def _fix_uac(undo, notes):
    _change_dword(_UAC, "EnableLUA", 1, undo, notes,
                  "User Account Control enabled")
    if _reg_read(_UAC, "ConsentPromptBehaviorAdmin") == 0:
        _change_dword(_UAC, "ConsentPromptBehaviorAdmin", 5, undo, notes,
                      "UAC will prompt instead of elevating silently")


def _fix_llmnr_netbios(undo, notes):
    _change_dword(_DNSCLIENT, "EnableMulticast", 0, undo, notes,
                  "LLMNR multicast name resolution disabled")
    for iface in _reg_subkeys(_NETBT_IF):
        if _reg_read(f"{_NETBT_IF}\\{iface}", "NetbiosOptions") != 2:
            _change_dword(f"{_NETBT_IF}\\{iface}", "NetbiosOptions", 2,
                          undo, notes,
                          f"NetBIOS name service disabled on adapter {iface}")


def _fix_ps_logging(undo, notes):
    _change_dword(_SBL, "EnableScriptBlockLogging", 1, undo, notes,
                  "PowerShell script-block logging enabled")


def _fix_legacy_tls(undo, notes):
    for proto in ("TLS 1.0", "TLS 1.1"):
        _change_dword(f"{_SCHANNEL}\\{proto}\\Server", "Enabled", 0,
                      undo, notes, f"{proto} server-side disabled")
        _change_dword(f"{_SCHANNEL}\\{proto}\\Server", "DisabledByDefault", 1,
                      undo, notes, f"{proto} marked disabled-by-default")


def _fix_print_spooler(undo, notes):
    _change_service("Spooler", undo, notes,
                    "Print Spooler service stopped and disabled")


def _fix_remote_registry(undo, notes):
    _change_service("RemoteRegistry", undo, notes,
                    "Remote Registry service stopped and disabled")


def _fix_audit_policy(undo, notes):
    old = _auditpol_get_logon()
    if old == "Success and Failure":
        return
    if not _auditpol_set_logon(True, True):
        raise RuntimeError("auditpol refused the change (needs Administrator)")
    undo.append({"kind": "auditpol", "subcategory": "Logon", "old": old})
    notes.append("Logon auditing enabled for success and failure events")


def _fix_lsa(undo, notes):
    _change_dword(_LSA, "RunAsPPL", 1, undo, notes,
                  "LSA now runs as a protected process (blocks Mimikatz-style "
                  "credential dumping)")
    _change_dword(_LSA, "NoLMHash", 1, undo, notes,
                  "Weak LM password hashes will no longer be stored")
    lm = _reg_read(_LSA, "LmCompatibilityLevel")
    if lm is not None and lm < 3:
        _change_dword(_LSA, "LmCompatibilityLevel", 5, undo, notes,
                      "NTLMv2 now required (weak LM/NTLMv1 refused)")


def _fix_anonymous_enum(undo, notes):
    _change_dword(_LSA, "RestrictAnonymous", 1, undo, notes,
                  "Anonymous share/pipe enumeration restricted")
    _change_dword(_LSA, "RestrictAnonymousSAM", 1, undo, notes,
                  "Anonymous SAM account enumeration restricted")


# ---------------------------------------------------------------------------
# Fix registry
# ---------------------------------------------------------------------------


@dataclass
class FixAction:
    """A one-click remediation for a hardening check."""
    check_id: str
    title: str
    description: str            # plain language, shown to end users
    caution: Optional[str] = None   # None = safe to bulk-apply
    reboot_required: bool = False
    _apply: Callable[[List[Dict[str, Any]], List[str]], None] = None  # type: ignore[assignment]

    @property
    def safe(self) -> bool:
        return self.caution is None


_FIXES: Dict[str, FixAction] = {
    "HRD-01": FixAction(
        "HRD-01", "Disable SMBv1",
        "Turns off the 30-year-old file-sharing protocol exploited by "
        "WannaCry. Modern Windows, printers and NAS devices do not use it.",
        _apply=_fix_smb1),
    "HRD-02": FixAction(
        "HRD-02", "Require SMB signing",
        "Makes file-sharing traffic tamper-proof so attackers on the network "
        "cannot hijack it. Standard on all modern Windows versions.",
        _apply=_fix_smb_signing),
    "HRD-03": FixAction(
        "HRD-03", "Require secure sign-in for Remote Desktop",
        "Remote Desktop will demand valid credentials before showing a "
        "logon screen, blocking brute-force and BlueKeep-class attacks.",
        _apply=_fix_rdp_nla),
    "HRD-04": FixAction(
        "HRD-04", "Enable User Account Control",
        "Restores the safety prompt that stops malware from silently "
        "gaining administrator rights.",
        reboot_required=True,
        _apply=_fix_uac),
    "HRD-05": FixAction(
        "HRD-05", "Disable LLMNR and NetBIOS name resolution",
        "Switches off two legacy protocols that let attackers on your "
        "network capture password hashes. Normal browsing, file shares by "
        "DNS name and printing are unaffected.",
        _apply=_fix_llmnr_netbios),
    "HRD-06": FixAction(
        "HRD-06", "Enable PowerShell logging",
        "Records what scripts run on this machine so an intrusion leaves "
        "evidence investigators can use.",
        _apply=_fix_ps_logging),
    "HRD-07": FixAction(
        "HRD-07", "Disable legacy TLS 1.0 / 1.1 (server side)",
        "Stops this machine offering deprecated encryption to clients.",
        caution="Only apply if no Windows XP/7-era clients or very old "
                "devices still connect to services on this machine — they "
                "would no longer be able to connect.",
        _apply=_fix_legacy_tls),
    "HRD-09": FixAction(
        "HRD-09", "Disable the Print Spooler service",
        "Removes the PrintNightmare attack surface on hosts that never "
        "print.",
        caution="This machine will NOT be able to print until the service "
                "is re-enabled (Undo restores it).",
        _apply=_fix_print_spooler),
    "HRD-10": FixAction(
        "HRD-10", "Disable the Remote Registry service",
        "Stops remote computers reading or changing this machine's "
        "settings. Almost nothing legitimate uses it on an SME network.",
        _apply=_fix_remote_registry),
    "HRD-11": FixAction(
        "HRD-11", "Enable logon auditing",
        "Records every successful and failed sign-in so break-in attempts "
        "leave a trail in the event log.",
        _apply=_fix_audit_policy),
    "HRD-13": FixAction(
        "HRD-13", "Protect stored credentials (LSA hardening)",
        "Blocks the memory-scraping technique credential-theft tools use "
        "and stops Windows keeping weak password hashes.",
        reboot_required=True,
        _apply=_fix_lsa),
    "HRD-14": FixAction(
        "HRD-14", "Restrict anonymous account enumeration",
        "Stops unauthenticated network users listing this machine's "
        "account names to target with password attacks.",
        _apply=_fix_anonymous_enum),
}

# Checks with no auto-fix (need human judgment):
#   HRD-08 unquoted service paths — quoting must be verified per service
#   HRD-12 local account hygiene — disabling accounts risks locking users out


def available_fixes() -> Dict[str, FixAction]:
    """All auto-fixes, keyed by check id."""
    return dict(_FIXES)


def fix_for(check_id: str) -> Optional[FixAction]:
    return _FIXES.get(check_id)


# ---------------------------------------------------------------------------
# Apply / revert
# ---------------------------------------------------------------------------


@dataclass
class FixResult:
    check_id: str
    title: str
    success: bool
    message: str
    changes: List[str] = field(default_factory=list)
    reboot_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id, "title": self.title,
            "success": self.success, "message": self.message,
            "changes": self.changes, "reboot_required": self.reboot_required,
        }


def apply_fixes(check_ids: List[str]) -> List[FixResult]:
    """Apply the fixes for the given check ids, journaling every change.

    Caution-tier fixes are applied only when explicitly listed — callers
    are responsible for having shown the user the fix's ``caution`` text.
    """
    if not IS_WINDOWS:
        return [FixResult(cid, _FIXES[cid].title if cid in _FIXES else cid,
                          False, "Fixes require a Windows host")
                for cid in check_ids]
    if not is_admin():
        return [FixResult(cid, _FIXES[cid].title if cid in _FIXES else cid,
                          False, "Administrator rights required — restart "
                                 "the app as Administrator")
                for cid in check_ids]

    results: List[FixResult] = []
    undo: List[Dict[str, Any]] = []
    applied_ids: List[str] = []

    for cid in check_ids:
        action = _FIXES.get(cid)
        if action is None:
            results.append(FixResult(
                cid, cid, False,
                "No automatic fix exists for this check — follow the "
                "remediation guidance instead"))
            continue
        notes: List[str] = []
        before = len(undo)
        try:
            action._apply(undo, notes)
            changed = notes or ["Already configured correctly — no change "
                                "was needed"]
            results.append(FixResult(
                cid, action.title, True,
                "Fixed" if len(undo) > before else "Already compliant",
                changed, action.reboot_required and len(undo) > before))
            if len(undo) > before:
                applied_ids.append(cid)
            logger.info("fix %s applied: %s", cid, "; ".join(notes) or "noop")
        except Exception as exc:
            results.append(FixResult(cid, action.title, False, str(exc),
                                     notes))
            logger.warning("fix %s failed", cid, exc_info=True)

    if undo:
        journal = _load_journal()
        journal.append({
            "id": len(journal) + 1,
            "timestamp": datetime.now().isoformat(),
            "check_ids": applied_ids,
            "changes": undo,
            "reverted": False,
        })
        _save_journal(journal)
    return results


def revert_last() -> Tuple[bool, str, List[str]]:
    """Undo the most recent fix run. Returns (ok, message, details)."""
    if not IS_WINDOWS:
        return False, "Undo requires a Windows host", []
    if not is_admin():
        return False, "Administrator rights required to undo", []

    journal = _load_journal()
    entry = None
    for e in reversed(journal):
        if not e.get("reverted"):
            entry = e
            break
    if entry is None:
        return False, "Nothing to undo — no fixes have been applied", []

    details: List[str] = []
    ok = True
    # Restore in reverse order of application
    for change in reversed(entry["changes"]):
        try:
            kind = change.get("kind")
            if kind == "reg":
                if change["old"] is None:
                    _reg_delete(change["path"], change["name"])
                    details.append(
                        f"Removed {change['name']} (was not set before)")
                else:
                    _reg_write(change["path"], change["name"], change["old"])
                    details.append(
                        f"Restored {change['name']} to {change['old']}")
            elif kind == "service":
                name = change["name"]
                startup = change.get("old_start", "demand")
                if startup == "unknown":
                    startup = "demand"
                _svc_set_startup(name, startup)
                if change.get("was_running"):
                    _svc_start(name)
                details.append(f"Service {name} restored "
                               f"({startup}{', started' if change.get('was_running') else ''})")
            elif kind == "auditpol":
                old = change.get("old", "unknown")
                _auditpol_set_logon("Success" in old, "Failure" in old)
                details.append(f"Logon auditing restored to '{old}'")
        except Exception as exc:
            ok = False
            details.append(f"Could not revert one change: {exc}")
            logger.warning("revert step failed", exc_info=True)

    entry["reverted"] = True
    entry["reverted_at"] = datetime.now().isoformat()
    _save_journal(journal)
    when = entry.get("timestamp", "")[:16].replace("T", " ")
    return ok, (f"Reverted fix run from {when}" if ok
                else "Undo finished with some errors — re-run the audit"), details
