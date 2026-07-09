"""
Windows Infrastructure Hardening Auditor
========================================
Server-grade digital-hygiene checks for the Windows hosts that *provide*
services to end users (file servers, application servers, domain controllers,
point-of-sale back offices).  End-user awareness is pointless when the
infrastructure serving those users is soft — this module audits the
infrastructure side of the equation.

Each check returns a ``HardeningCheckResult`` with a status, severity,
plain-English details and an actionable remediation (with a PowerShell
snippet where possible).  The aggregate ``HardeningReport`` yields a
score and a HARDENED / NEEDS ATTENTION / AT RISK grade.

All checks are read-only and registry-first so they work without
administrator rights wherever Windows allows it; checks that need
elevation degrade to a WARNING instead of crashing.

Usage
-----
    from src.security.hardening import WindowsHardeningAuditor

    auditor = WindowsHardeningAuditor()
    report = auditor.run_all()
    print(report.grade)       # "HARDENED" / "NEEDS ATTENTION" / "AT RISK"
    print(report.to_dict())   # full JSON-serialisable report
"""

from __future__ import annotations

import platform
import socket
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

IS_WINDOWS = platform.system() == "Windows"

# Statuses a check can report
PASS = "PASS"
WARNING = "WARNING"
FAIL = "FAIL"
ERROR = "ERROR"
NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class HardeningCheckResult:
    """Result of a single hardening check."""
    check_id: str          # HRD-01 .. HRD-14
    name: str
    status: str            # PASS, WARNING, FAIL, ERROR, NOT_APPLICABLE
    severity: str          # CRITICAL, HIGH, MEDIUM, LOW
    details: str
    remediation: str = ""
    category: str = ""     # protocol, remote-access, credentials, services, logging

    @property
    def passed(self) -> bool:
        return self.status == PASS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "status": self.status,
            "passed": self.passed,
            "severity": self.severity,
            "details": self.details,
            "remediation": self.remediation,
            "category": self.category,
        }


@dataclass
class HardeningReport:
    """Aggregate result of a full hardening audit."""
    checks: List[HardeningCheckResult] = field(default_factory=list)
    timestamp: str = ""
    hostname: str = ""
    os_info: str = ""

    def __post_init__(self):
        self.timestamp = self.timestamp or datetime.now().isoformat()
        self.hostname = self.hostname or socket.gethostname()
        self.os_info = self.os_info or f"{platform.system()} {platform.release()}"

    @property
    def applicable(self) -> List[HardeningCheckResult]:
        return [c for c in self.checks if c.status != NOT_APPLICABLE]

    @property
    def total(self) -> int:
        return len(self.applicable)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.applicable if c.status == PASS)

    @property
    def warnings(self) -> int:
        return sum(1 for c in self.applicable if c.status in (WARNING, ERROR))

    @property
    def failed(self) -> int:
        return sum(1 for c in self.applicable if c.status == FAIL)

    @property
    def critical_failures(self) -> int:
        return sum(
            1 for c in self.applicable
            if c.status == FAIL and c.severity == "CRITICAL"
        )

    @property
    def score_percent(self) -> int:
        """PASS = 1 point, WARNING/ERROR = half point, FAIL = 0."""
        if not self.total:
            return 0
        points = self.passed + 0.5 * self.warnings
        return round(points / self.total * 100)

    @property
    def grade(self) -> str:
        if not self.total:
            return "NOT APPLICABLE"
        if self.score_percent >= 85 and self.critical_failures == 0:
            return "HARDENED"
        if self.score_percent >= 60 and self.critical_failures <= 1:
            return "NEEDS ATTENTION"
        return "AT RISK"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grade": self.grade,
            "score_percent": self.score_percent,
            "timestamp": self.timestamp,
            "hostname": self.hostname,
            "os_info": self.os_info,
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "warnings": self.warnings,
                "failed": self.failed,
                "critical_failures": self.critical_failures,
            },
            "checks": [c.to_dict() for c in self.checks],
        }


# ---------------------------------------------------------------------------
# Registry / service helpers
# ---------------------------------------------------------------------------


def _reg_value(path: str, name: str, hive: Optional[int] = None) -> Any:
    """Read a registry value from HKLM (default). Returns None when absent."""
    if not IS_WINDOWS:
        return None
    import winreg  # type: ignore[import]
    hive = hive if hive is not None else winreg.HKEY_LOCAL_MACHINE
    try:
        with winreg.OpenKey(hive, path) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return value
    except OSError:
        return None


def _reg_subkeys(path: str) -> List[str]:
    """List subkey names under an HKLM path. Empty list when absent."""
    if not IS_WINDOWS:
        return []
    import winreg  # type: ignore[import]
    names: List[str] = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            count = winreg.QueryInfoKey(key)[0]
            for i in range(count):
                try:
                    names.append(winreg.EnumKey(key, i))
                except OSError:
                    break
    except OSError:
        pass
    return names


def _service_state(name: str) -> str:
    """Return RUNNING / STOPPED / DISABLED / UNKNOWN for a Windows service."""
    try:
        query = subprocess.run(
            ["sc", "query", name],
            capture_output=True, text=True, timeout=8, shell=False,
        )
        out = query.stdout.upper()
        if "RUNNING" in out:
            return "RUNNING"
        if "STOPPED" in out:
            # Distinguish stopped-but-startable from disabled
            qc = subprocess.run(
                ["sc", "qc", name],
                capture_output=True, text=True, timeout=8, shell=False,
            )
            if "DISABLED" in qc.stdout.upper():
                return "DISABLED"
            return "STOPPED"
        if "1060" in query.stdout or "DOES NOT EXIST" in out:
            return "ABSENT"
    except Exception:
        logger.debug("service state query failed for %s", name,
                     exc_info=True)
    return "UNKNOWN"


def _run_powershell(command: str, timeout: int = 20) -> str:
    """Run a PowerShell command, returning stdout ('' on any failure)."""
    try:
        result = subprocess.run(
            ["powershell", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=timeout, shell=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        logger.debug("PowerShell command failed", exc_info=True)
    return ""


def _not_applicable(check_id: str, name: str, category: str) -> HardeningCheckResult:
    return HardeningCheckResult(
        check_id=check_id, name=name,
        status=NOT_APPLICABLE, severity="LOW",
        details="Non-Windows host — check skipped",
        category=category,
    )


# ---------------------------------------------------------------------------
# Auditor
# ---------------------------------------------------------------------------


class WindowsHardeningAuditor:
    """Runs all infrastructure hardening checks on the local Windows host."""

    def run_all(self) -> HardeningReport:
        logger.info("Starting Windows infrastructure hardening audit")
        checks = [
            self.check_smb1(),
            self.check_smb_signing(),
            self.check_rdp_hardening(),
            self.check_uac(),
            self.check_llmnr_netbios(),
            self.check_powershell_logging(),
            self.check_legacy_tls(),
            self.check_unquoted_service_paths(),
            self.check_print_spooler(),
            self.check_remote_registry(),
            self.check_audit_policy(),
            self.check_local_accounts(),
            self.check_lsa_protections(),
            self.check_anonymous_enumeration(),
        ]
        report = HardeningReport(checks=checks)
        logger.info(
            "Hardening audit complete: %s%% — %s (%d/%d passed, %d critical failures)",
            report.score_percent, report.grade,
            report.passed, report.total, report.critical_failures,
        )
        return report

    # ── HRD-01 ────────────────────────────────────────────────────────
    def check_smb1(self) -> HardeningCheckResult:
        """SMBv1 must be disabled — it is the WannaCry/EternalBlue vector."""
        cid, name, cat = "HRD-01", "SMBv1 Protocol Disabled", "protocol"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Disable SMBv1: "
            "Set-SmbServerConfiguration -EnableSMB1Protocol $false; "
            "Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart"
        )
        try:
            smb1 = _reg_value(
                r"SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters", "SMB1")
            if smb1 == 0:
                return HardeningCheckResult(
                    cid, name, PASS, "CRITICAL",
                    "SMBv1 server protocol is disabled (registry SMB1=0)",
                    remediation, cat)
            if smb1 == 1:
                return HardeningCheckResult(
                    cid, name, FAIL, "CRITICAL",
                    "SMBv1 is ENABLED — vulnerable to EternalBlue/WannaCry class attacks",
                    remediation, cat)
            # Registry value absent — ask PowerShell for the effective config
            out = _run_powershell(
                "(Get-SmbServerConfiguration).EnableSMB1Protocol")
            if out.lower() == "false":
                return HardeningCheckResult(
                    cid, name, PASS, "CRITICAL",
                    "SMBv1 server protocol is disabled",
                    remediation, cat)
            if out.lower() == "true":
                return HardeningCheckResult(
                    cid, name, FAIL, "CRITICAL",
                    "SMBv1 is ENABLED — vulnerable to EternalBlue/WannaCry class attacks",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, WARNING, "CRITICAL",
                "Could not determine SMBv1 state — verify manually",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "CRITICAL", f"SMBv1 check error: {exc}",
                remediation, cat)

    # ── HRD-02 ────────────────────────────────────────────────────────
    def check_smb_signing(self) -> HardeningCheckResult:
        """SMB signing prevents NTLM-relay and man-in-the-middle attacks."""
        cid, name, cat = "HRD-02", "SMB Signing Required", "protocol"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Require SMB signing: "
            "Set-SmbServerConfiguration -RequireSecuritySignature $true; "
            "Set-SmbClientConfiguration -RequireSecuritySignature $true"
        )
        try:
            server = _reg_value(
                r"SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters",
                "RequireSecuritySignature")
            client = _reg_value(
                r"SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters",
                "RequireSecuritySignature")
            parts = []
            ok = 0
            for label, val in (("server", server), ("client", client)):
                if val == 1:
                    ok += 1
                    parts.append(f"{label}: required")
                else:
                    parts.append(f"{label}: NOT required")
            details = "SMB signing — " + ", ".join(parts)
            if ok == 2:
                return HardeningCheckResult(cid, name, PASS, "HIGH", details,
                                            remediation, cat)
            if ok == 1:
                return HardeningCheckResult(
                    cid, name, WARNING, "HIGH",
                    details + " — NTLM relay attacks remain possible",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, FAIL, "HIGH",
                details + " — host is exposed to SMB relay/tampering",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "HIGH", f"SMB signing check error: {exc}",
                remediation, cat)

    # ── HRD-03 ────────────────────────────────────────────────────────
    def check_rdp_hardening(self) -> HardeningCheckResult:
        """RDP should be off, or require Network Level Authentication."""
        cid, name, cat = "HRD-03", "Remote Desktop Hardening", "remote-access"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Require NLA for RDP: Set-ItemProperty "
            "'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' "
            "-Name UserAuthentication -Value 1 — or disable RDP entirely if unused."
        )
        try:
            deny = _reg_value(
                r"SYSTEM\CurrentControlSet\Control\Terminal Server",
                "fDenyTSConnections")
            if deny == 1:
                return HardeningCheckResult(
                    cid, name, PASS, "HIGH",
                    "Remote Desktop is disabled — no RDP attack surface",
                    remediation, cat)
            nla = _reg_value(
                r"SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp",
                "UserAuthentication")
            sec_layer = _reg_value(
                r"SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp",
                "SecurityLayer")
            issues = []
            if nla != 1:
                issues.append("Network Level Authentication is OFF")
            if sec_layer is not None and sec_layer == 0:
                issues.append("legacy RDP security layer in use (SecurityLayer=0)")
            if not issues:
                return HardeningCheckResult(
                    cid, name, PASS, "HIGH",
                    "RDP enabled with Network Level Authentication required",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, FAIL, "HIGH",
                "RDP is enabled and " + "; ".join(issues) +
                " — exposed to credential brute-force and BlueKeep-class exploits",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "HIGH", f"RDP check error: {exc}",
                remediation, cat)

    # ── HRD-04 ────────────────────────────────────────────────────────
    def check_uac(self) -> HardeningCheckResult:
        """User Account Control must be enabled and actually prompting."""
        cid, name, cat = "HRD-04", "User Account Control (UAC)", "credentials"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Re-enable UAC: Set-ItemProperty "
            "'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' "
            "-Name EnableLUA -Value 1 (restart required)."
        )
        try:
            path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
            enable_lua = _reg_value(path, "EnableLUA")
            prompt = _reg_value(path, "ConsentPromptBehaviorAdmin")
            if enable_lua != 1:
                return HardeningCheckResult(
                    cid, name, FAIL, "HIGH",
                    "UAC is DISABLED — every process runs with full admin rights",
                    remediation, cat)
            if prompt == 0:
                return HardeningCheckResult(
                    cid, name, WARNING, "HIGH",
                    "UAC enabled but set to 'elevate without prompting' — "
                    "malware can silently gain admin rights",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, PASS, "HIGH",
                "UAC is enabled and prompts for elevation",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "HIGH", f"UAC check error: {exc}",
                remediation, cat)

    # ── HRD-05 ────────────────────────────────────────────────────────
    def check_llmnr_netbios(self) -> HardeningCheckResult:
        """LLMNR / NetBIOS name resolution enables credential-capture attacks."""
        cid, name, cat = "HRD-05", "LLMNR / NetBIOS-NS Disabled", "protocol"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Disable LLMNR via GPO (Computer Config > Admin Templates > Network > "
            "DNS Client > Turn off multicast name resolution) and set NetBIOS over "
            "TCP/IP to 'Disabled' on each network adapter."
        )
        try:
            llmnr = _reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows NT\DNSClient",
                "EnableMulticast")
            llmnr_off = (llmnr == 0)

            # NetBIOS: NetbiosOptions=2 (disabled) per interface
            ifaces_path = r"SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces"
            ifaces = _reg_subkeys(ifaces_path)
            nb_states = []
            for iface in ifaces:
                val = _reg_value(f"{ifaces_path}\\{iface}", "NetbiosOptions")
                if val is not None:
                    nb_states.append(val)
            nb_all_off = bool(nb_states) and all(v == 2 for v in nb_states)

            parts = [
                "LLMNR: " + ("disabled" if llmnr_off else "ENABLED"),
                "NetBIOS-NS: " + (
                    "disabled on all adapters" if nb_all_off
                    else "enabled on one or more adapters" if nb_states
                    else "state unknown"),
            ]
            details = ", ".join(parts)
            if llmnr_off and nb_all_off:
                return HardeningCheckResult(cid, name, PASS, "HIGH", details,
                                            remediation, cat)
            if llmnr_off or nb_all_off:
                return HardeningCheckResult(
                    cid, name, WARNING, "HIGH",
                    details + " — Responder-style credential capture partially possible",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, FAIL, "HIGH",
                details + " — attackers on the LAN can capture password hashes "
                "with tools like Responder",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "HIGH", f"LLMNR/NetBIOS check error: {exc}",
                remediation, cat)

    # ── HRD-06 ────────────────────────────────────────────────────────
    def check_powershell_logging(self) -> HardeningCheckResult:
        """Script-block logging is the key forensic trail for intrusions."""
        cid, name, cat = "HRD-06", "PowerShell Logging Enabled", "logging"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Enable script block logging: New-Item -Force "
            "'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\PowerShell\\ScriptBlockLogging'; "
            "Set-ItemProperty that key -Name EnableScriptBlockLogging -Value 1"
        )
        try:
            sbl = _reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging",
                "EnableScriptBlockLogging")
            module = _reg_value(
                r"SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging",
                "EnableModuleLogging")
            parts = [
                "script block logging: " + ("on" if sbl == 1 else "off"),
                "module logging: " + ("on" if module == 1 else "off"),
            ]
            details = "PowerShell " + ", ".join(parts)
            if sbl == 1:
                return HardeningCheckResult(cid, name, PASS, "MEDIUM", details,
                                            remediation, cat)
            return HardeningCheckResult(
                cid, name, FAIL, "MEDIUM",
                details + " — attacker PowerShell activity will leave no trail",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "MEDIUM", f"PowerShell logging check error: {exc}",
                remediation, cat)

    # ── HRD-07 ────────────────────────────────────────────────────────
    def check_legacy_tls(self) -> HardeningCheckResult:
        """TLS 1.0/1.1 server-side must be explicitly disabled on servers."""
        cid, name, cat = "HRD-07", "Legacy TLS Disabled (Server)", "protocol"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Disable legacy TLS in Schannel: create "
            "'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\Schannel\\"
            "Protocols\\TLS 1.0\\Server' with Enabled=0 and DisabledByDefault=1 "
            "(repeat for TLS 1.1)."
        )
        try:
            base = (r"SYSTEM\CurrentControlSet\Control\SecurityProviders"
                    r"\Schannel\Protocols")
            states = {}
            for proto in ("TLS 1.0", "TLS 1.1"):
                enabled = _reg_value(f"{base}\\{proto}\\Server", "Enabled")
                if enabled == 0:
                    states[proto] = "disabled"
                elif enabled is None:
                    states[proto] = "OS default"
                else:
                    states[proto] = "ENABLED"
            details = ", ".join(f"{p}: {s}" for p, s in states.items())
            if any(s == "ENABLED" for s in states.values()):
                return HardeningCheckResult(
                    cid, name, FAIL, "MEDIUM",
                    details + " — deprecated protocols explicitly enabled",
                    remediation, cat)
            if all(s == "disabled" for s in states.values()):
                return HardeningCheckResult(
                    cid, name, PASS, "MEDIUM",
                    details + " — legacy TLS explicitly disabled",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, WARNING, "MEDIUM",
                details + " — relying on OS defaults; disable explicitly on "
                "servers that terminate TLS",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "MEDIUM", f"Legacy TLS check error: {exc}",
                remediation, cat)

    # ── HRD-08 ────────────────────────────────────────────────────────
    def check_unquoted_service_paths(self) -> HardeningCheckResult:
        """Unquoted service paths with spaces allow privilege escalation."""
        cid, name, cat = "HRD-08", "No Unquoted Service Paths", "services"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Quote the ImagePath of each flagged service: Set-ItemProperty "
            "'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\<name>' "
            "-Name ImagePath -Value '\"C:\\Program Files\\App\\svc.exe\"'"
        )
        try:
            services_path = r"SYSTEM\CurrentControlSet\Services"
            vulnerable: List[str] = []
            for svc in _reg_subkeys(services_path):
                image = _reg_value(f"{services_path}\\{svc}", "ImagePath")
                if not isinstance(image, str):
                    continue
                path = image.strip()
                if not path or path.startswith('"'):
                    continue
                # Ignore kernel drivers and system-root binaries without spaces
                exe_part = path.split(" -", 1)[0].split(" /", 1)[0]
                if " " not in exe_part:
                    continue
                lower = exe_part.lower()
                if lower.startswith((r"c:\windows", "system32", r"\systemroot")):
                    continue
                vulnerable.append(svc)
                if len(vulnerable) >= 10:
                    break
            if vulnerable:
                return HardeningCheckResult(
                    cid, name, FAIL, "HIGH",
                    f"{len(vulnerable)} service(s) with unquoted paths containing "
                    f"spaces: {', '.join(vulnerable[:5])}"
                    f"{'…' if len(vulnerable) > 5 else ''} — "
                    "local users may plant binaries to escalate to SYSTEM",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, PASS, "HIGH",
                "No unquoted service paths with spaces detected",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "HIGH",
                f"Unquoted service path check error: {exc}",
                remediation, cat)

    # ── HRD-09 ────────────────────────────────────────────────────────
    def check_print_spooler(self) -> HardeningCheckResult:
        """Print Spooler on servers is a known escalation vector (PrintNightmare)."""
        cid, name, cat = "HRD-09", "Print Spooler Exposure", "services"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "If this host does not print, disable the spooler: "
            "Stop-Service Spooler; Set-Service Spooler -StartupType Disabled"
        )
        try:
            state = _service_state("Spooler")
            is_server = "server" in platform.win32_edition().lower() if hasattr(
                platform, "win32_edition") else False
            if state in ("DISABLED", "STOPPED", "ABSENT"):
                return HardeningCheckResult(
                    cid, name, PASS, "MEDIUM",
                    f"Print Spooler service is {state.lower()}",
                    remediation, cat)
            if state == "RUNNING" and is_server:
                return HardeningCheckResult(
                    cid, name, FAIL, "MEDIUM",
                    "Print Spooler is RUNNING on a Windows Server edition — "
                    "PrintNightmare-class exploitation risk; disable if not needed",
                    remediation, cat)
            if state == "RUNNING":
                return HardeningCheckResult(
                    cid, name, WARNING, "MEDIUM",
                    "Print Spooler is running — acceptable on workstations that "
                    "print, but disable it on servers",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, WARNING, "MEDIUM",
                "Could not determine Print Spooler state",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "MEDIUM", f"Print Spooler check error: {exc}",
                remediation, cat)

    # ── HRD-10 ────────────────────────────────────────────────────────
    def check_remote_registry(self) -> HardeningCheckResult:
        """Remote Registry service lets remote attackers read/modify the registry."""
        cid, name, cat = "HRD-10", "Remote Registry Disabled", "services"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Disable the service: Stop-Service RemoteRegistry; "
            "Set-Service RemoteRegistry -StartupType Disabled"
        )
        try:
            state = _service_state("RemoteRegistry")
            if state in ("DISABLED", "ABSENT"):
                return HardeningCheckResult(
                    cid, name, PASS, "MEDIUM",
                    f"Remote Registry service is {state.lower()}",
                    remediation, cat)
            if state == "STOPPED":
                return HardeningCheckResult(
                    cid, name, WARNING, "MEDIUM",
                    "Remote Registry is stopped but not disabled — it can be "
                    "started remotely by an attacker with credentials",
                    remediation, cat)
            if state == "RUNNING":
                return HardeningCheckResult(
                    cid, name, FAIL, "MEDIUM",
                    "Remote Registry service is RUNNING — remote reconnaissance "
                    "and tampering risk",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, WARNING, "MEDIUM",
                "Could not determine Remote Registry state",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "MEDIUM", f"Remote Registry check error: {exc}",
                remediation, cat)

    # ── HRD-11 ────────────────────────────────────────────────────────
    def check_audit_policy(self) -> HardeningCheckResult:
        """Logon auditing must capture both success and failure events."""
        cid, name, cat = "HRD-11", "Logon Audit Policy", "logging"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Enable logon auditing: auditpol /set /subcategory:\"Logon\" "
            "/success:enable /failure:enable (run as Administrator)"
        )
        try:
            result = subprocess.run(
                ["auditpol", "/get", "/subcategory:Logon"],
                capture_output=True, text=True, timeout=10, shell=False,
            )
            if result.returncode != 0:
                return HardeningCheckResult(
                    cid, name, WARNING, "MEDIUM",
                    "Could not read audit policy (requires Administrator) — "
                    "verify logon auditing manually",
                    remediation, cat)
            out = result.stdout
            if "Success and Failure" in out:
                return HardeningCheckResult(
                    cid, name, PASS, "MEDIUM",
                    "Logon events audited for success and failure",
                    remediation, cat)
            if "Success" in out or "Failure" in out:
                return HardeningCheckResult(
                    cid, name, WARNING, "MEDIUM",
                    "Logon auditing only partially enabled — capture both "
                    "success and failure",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, FAIL, "MEDIUM",
                "Logon auditing is disabled — brute-force attempts and "
                "successful intrusions leave no record",
                remediation, cat)
        except FileNotFoundError:
            return HardeningCheckResult(
                cid, name, WARNING, "MEDIUM",
                "auditpol not available — verify audit policy manually",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "MEDIUM", f"Audit policy check error: {exc}",
                remediation, cat)

    # ── HRD-12 ────────────────────────────────────────────────────────
    def check_local_accounts(self) -> HardeningCheckResult:
        """Built-in Administrator/Guest must be disabled; few local admins."""
        cid, name, cat = "HRD-12", "Local Account Hygiene", "credentials"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Disable built-in accounts: Disable-LocalUser Administrator; "
            "Disable-LocalUser Guest — and remove day-to-day users from the "
            "Administrators group."
        )
        try:
            import json as _json
            out = _run_powershell(
                "Get-LocalUser | Select-Object Name,Enabled | ConvertTo-Json")
            if not out:
                return HardeningCheckResult(
                    cid, name, WARNING, "HIGH",
                    "Could not enumerate local accounts",
                    remediation, cat)
            raw = _json.loads(out)
            users = raw if isinstance(raw, list) else [raw]
            issues: List[str] = []
            for u in users:
                uname = str(u.get("Name", "")).lower()
                if uname == "administrator" and u.get("Enabled"):
                    issues.append("built-in Administrator account is enabled")
                if uname == "guest" and u.get("Enabled"):
                    issues.append("Guest account is enabled")

            admins_out = _run_powershell(
                "(Get-LocalGroupMember -Group Administrators -EA SilentlyContinue "
                "| Measure-Object).Count")
            try:
                admin_count = int(admins_out)
            except ValueError:
                admin_count = -1
            if admin_count > 3:
                issues.append(
                    f"{admin_count} members in the Administrators group — "
                    "apply least privilege")

            enabled = sum(1 for u in users if u.get("Enabled"))
            summary = f"{enabled} enabled local account(s)"
            if admin_count >= 0:
                summary += f", {admin_count} local administrator(s)"
            if not issues:
                return HardeningCheckResult(
                    cid, name, PASS, "HIGH",
                    summary + " — no built-in account risks",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, FAIL, "HIGH",
                summary + "; " + "; ".join(issues),
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "HIGH", f"Local accounts check error: {exc}",
                remediation, cat)

    # ── HRD-13 ────────────────────────────────────────────────────────
    def check_lsa_protections(self) -> HardeningCheckResult:
        """LSA hardening blocks Mimikatz-style credential theft."""
        cid, name, cat = "HRD-13", "LSA Credential Protections", "credentials"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Harden LSA: Set-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' "
            "-Name RunAsPPL -Value 1; -Name NoLMHash -Value 1; "
            "-Name LmCompatibilityLevel -Value 5 (restart required)."
        )
        try:
            lsa = r"SYSTEM\CurrentControlSet\Control\Lsa"
            run_as_ppl = _reg_value(lsa, "RunAsPPL")
            no_lm_hash = _reg_value(lsa, "NoLMHash")
            lm_compat = _reg_value(lsa, "LmCompatibilityLevel")

            good, bad = [], []
            if run_as_ppl in (1, 2):
                good.append("LSA runs as protected process (RunAsPPL)")
            else:
                bad.append("LSA not protected (RunAsPPL off) — credential "
                           "dumping tools can read passwords from memory")
            if no_lm_hash in (None, 1):
                good.append("LM hashes not stored")
            else:
                bad.append("weak LM password hashes are stored")
            if lm_compat is None or lm_compat >= 3:
                good.append("NTLMv2 required or OS default")
            else:
                bad.append(f"weak NTLM level ({lm_compat}) permits LM/NTLMv1")

            details = "; ".join(good + bad)
            if not bad:
                return HardeningCheckResult(cid, name, PASS, "HIGH", details,
                                            remediation, cat)
            if len(bad) == 1 and run_as_ppl not in (1, 2):
                return HardeningCheckResult(cid, name, WARNING, "HIGH", details,
                                            remediation, cat)
            return HardeningCheckResult(cid, name, FAIL, "HIGH", details,
                                        remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "HIGH", f"LSA protections check error: {exc}",
                remediation, cat)

    # ── HRD-14 ────────────────────────────────────────────────────────
    def check_anonymous_enumeration(self) -> HardeningCheckResult:
        """Anonymous SAM/share enumeration leaks usernames to attackers."""
        cid, name, cat = "HRD-14", "Anonymous Enumeration Restricted", "credentials"
        if not IS_WINDOWS:
            return _not_applicable(cid, name, cat)
        remediation = (
            "Restrict anonymous access: Set-ItemProperty "
            "'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' "
            "-Name RestrictAnonymous -Value 1; -Name RestrictAnonymousSAM -Value 1"
        )
        try:
            lsa = r"SYSTEM\CurrentControlSet\Control\Lsa"
            anon = _reg_value(lsa, "RestrictAnonymous")
            anon_sam = _reg_value(lsa, "RestrictAnonymousSAM")
            sam_ok = anon_sam in (None, 1)   # default is 1 on modern Windows
            anon_ok = anon == 1
            if sam_ok and anon_ok:
                return HardeningCheckResult(
                    cid, name, PASS, "MEDIUM",
                    "Anonymous SAM and share enumeration are restricted",
                    remediation, cat)
            if sam_ok:
                return HardeningCheckResult(
                    cid, name, WARNING, "MEDIUM",
                    "SAM enumeration restricted but anonymous share/pipe "
                    "enumeration is allowed (RestrictAnonymous=0)",
                    remediation, cat)
            return HardeningCheckResult(
                cid, name, FAIL, "MEDIUM",
                "Anonymous users can enumerate accounts — attackers can "
                "harvest usernames for password attacks",
                remediation, cat)
        except Exception as exc:
            return HardeningCheckResult(
                cid, name, ERROR, "MEDIUM",
                f"Anonymous enumeration check error: {exc}",
                remediation, cat)
