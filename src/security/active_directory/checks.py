"""
Active Directory hygiene checks
===============================
Read-only LDAP checks against a Windows Active Directory domain, aimed at
the common misconfigurations that let attackers move laterally or escalate:
stale accounts, oversized Domain Admins, an open machine-account quota, an
ageing krbtgt key, anonymous LDAP binds and risky account flags.

Everything degrades gracefully: no ``ldap3`` installed, a non-domain-joined
host, or a failed bind all produce SKIP/ERROR findings rather than crashing,
so the screen is safe to run anywhere.

The aggregate :class:`ADReport` yields a HEALTHY / NEEDS ATTENTION / AT RISK
grade, mirroring the Server Hardening audit.
"""
from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

try:
    from ldap3 import ALL, Connection, NTLM, Server, SUBTREE
    _HAS_LDAP = True
except ImportError:  # pragma: no cover - exercised only without ldap3
    _HAS_LDAP = False

# Statuses
PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
SKIP = "SKIP"
ERROR = "ERROR"

# userAccountControl bit flags we care about
_UAC = {
    "ACCOUNTDISABLE": 0x0002,
    "PASSWD_NOTREQD": 0x0020,
    "ENCRYPTED_TEXT_PWD_ALLOWED": 0x0080,
    "DONT_EXPIRE_PASSWORD": 0x10000,
    "TRUSTED_FOR_DELEGATION": 0x80000,
}


@dataclass
class ADFinding:
    check_id: str
    name: str
    status: str            # PASS, WARN, FAIL, SKIP, ERROR
    severity: str          # CRITICAL, HIGH, MEDIUM, LOW
    details: str
    remediation: str = ""

    @property
    def passed(self) -> bool:
        return self.status == PASS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id, "name": self.name,
            "status": self.status, "passed": self.passed,
            "severity": self.severity, "details": self.details,
            "remediation": self.remediation,
        }


@dataclass
class ADReport:
    domain: str = ""
    findings: List[ADFinding] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        self.timestamp = self.timestamp or datetime.now().isoformat()

    @property
    def applicable(self) -> List[ADFinding]:
        return [f for f in self.findings if f.status != SKIP]

    @property
    def failed(self) -> int:
        return sum(1 for f in self.applicable if f.status == FAIL)

    @property
    def warnings(self) -> int:
        return sum(1 for f in self.applicable if f.status in (WARN, ERROR))

    @property
    def passed(self) -> int:
        return sum(1 for f in self.applicable if f.status == PASS)

    @property
    def critical_failures(self) -> int:
        return sum(1 for f in self.applicable
                   if f.status == FAIL and f.severity == "CRITICAL")

    @property
    def score_percent(self) -> int:
        total = len(self.applicable)
        if not total:
            return 0
        points = self.passed + 0.5 * self.warnings
        return round(points / total * 100)

    @property
    def grade(self) -> str:
        if not self.applicable:
            return "NOT APPLICABLE"
        if self.critical_failures:
            return "AT RISK"
        if self.score_percent >= 85:
            return "HEALTHY"
        if self.score_percent >= 55:
            return "NEEDS ATTENTION"
        return "AT RISK"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "grade": self.grade,
            "score_percent": self.score_percent,
            "timestamp": self.timestamp,
            "summary": {
                "passed": self.passed, "warnings": self.warnings,
                "failed": self.failed,
                "critical_failures": self.critical_failures,
                "total": len(self.applicable),
            },
            "findings": [f.to_dict() for f in self.findings],
        }


# ---------------------------------------------------------------------------
# Domain / helpers
# ---------------------------------------------------------------------------


def get_domain_name() -> Optional[str]:
    """Best-effort DNS domain of a domain-joined Windows host."""
    if platform.system() != "Windows":
        return None
    # PowerShell CIM first (wmic is gone on Win11 24H2+).
    try:
        r = subprocess.run(
            ["powershell", "-NonInteractive", "-Command",
             "(Get-CimInstance Win32_ComputerSystem).Domain"],
            capture_output=True, text=True, timeout=15,
        )
        domain = r.stdout.strip()
        if domain and domain.upper() != "WORKGROUP":
            return domain
    except Exception:
        logger.debug("CIM domain lookup failed", exc_info=True)
    try:
        r = subprocess.run(
            ["wmic", "computersystem", "get", "domain"],
            capture_output=True, text=True, timeout=8,
        )
        lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
        if len(lines) >= 2 and lines[1].upper() != "WORKGROUP":
            return lines[1]
    except Exception:
        logger.debug("wmic domain lookup failed", exc_info=True)
    return None


def build_base_dn(domain: str) -> str:
    return ",".join(f"DC={part}" for part in domain.split(".") if part)


def _filetime_to_dt(value: Any) -> Optional[datetime]:
    """Convert a Windows FILETIME (or datetime) to an aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        ft = int(value)
    except (TypeError, ValueError):
        return None
    if ft <= 0:                     # 0 / 0x7FFFFFFFFFFFFFFF == "never"
        return None
    try:
        return (datetime(1601, 1, 1, tzinfo=timezone.utc)
                + timedelta(microseconds=ft / 10))
    except (OverflowError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Auditor
# ---------------------------------------------------------------------------


class ADAuditor:
    """Runs the AD hygiene checks against one domain over LDAP.

    Parameters
    ----------
    domain      : DNS domain (auto-detected when omitted on a joined host)
    user        : ``DOMAIN\\user`` (NTLM) or a UPN/DN (simple bind); blank
                  attempts an unauthenticated bind
    password    : bind password
    use_ssl     : bind over LDAPS (636) instead of LDAP (389)
    stale_days  : accounts idle longer than this are flagged (default 90)
    max_domain_admins : Domain Admins above this count fail the check
    """

    def __init__(self, domain: Optional[str] = None, user: str = "",
                 password: str = "", use_ssl: bool = False,
                 stale_days: int = 90, max_domain_admins: int = 5):
        self.domain = (domain or get_domain_name() or "").strip()
        self.user = user.strip()
        self.password = password
        self.use_ssl = use_ssl
        self.stale_days = stale_days
        self.max_domain_admins = max_domain_admins
        self._conn = None

    # -- connection ------------------------------------------------------
    def _connect(self):
        """Open a reusable LDAP connection. Raises on failure."""
        if self._conn is not None:
            return self._conn
        auth = NTLM if "\\" in self.user else None
        server = Server(self.domain, use_ssl=self.use_ssl, get_info=ALL)
        conn = Connection(
            server,
            user=self.user or None,
            password=self.password or None,
            authentication=auth,
            auto_bind=True,
            receive_timeout=15,
        )
        self._conn = conn
        return conn

    def _paged(self, conn, ldap_filter: str, attributes: List[str]):
        """Paged subtree search under the domain base DN."""
        base = build_base_dn(self.domain)
        return conn.extend.standard.paged_search(
            search_base=base, search_filter=ldap_filter,
            search_scope=SUBTREE, attributes=attributes,
            paged_size=500, generator=False)

    # -- orchestration ---------------------------------------------------
    def run(self) -> ADReport:
        report = ADReport(domain=self.domain)
        if not _HAS_LDAP:
            report.findings.append(ADFinding(
                "AD-00", "LDAP client available", SKIP, "LOW",
                "The ldap3 library is not installed, so live AD checks were "
                "skipped.",
                "Install it with: pip install ldap3"))
            return report
        if not self.domain:
            report.findings.append(ADFinding(
                "AD-00", "Domain-joined host", SKIP, "LOW",
                "This host is not domain-joined or the domain could not be "
                "determined.",
                "Run this on a domain member or a domain controller, or type "
                "the domain name manually."))
            return report

        try:
            self._connect()
        except Exception as exc:
            report.findings.append(ADFinding(
                "AD-01", "Directory Connectivity", ERROR, "HIGH",
                f"Could not bind to {self.domain}: {exc}",
                "Check network access to the domain controller and the bind "
                "credentials (use DOMAIN\\\\user for NTLM)."))
            return report

        report.findings.append(ADFinding(
            "AD-01", "Directory Connectivity", PASS, "HIGH",
            f"Connected to Active Directory domain {self.domain}."))

        for check in (self._check_stale_accounts,
                      self._check_domain_admins,
                      self._check_machine_account_quota,
                      self._check_krbtgt_age,
                      self._check_risky_account_flags,
                      self._check_anonymous_bind):
            try:
                report.findings.append(check())
            except Exception as exc:
                report.findings.append(ADFinding(
                    getattr(check, "_cid", "AD-??"),
                    check.__name__.replace("_check_", "").replace("_", " ").title(),
                    ERROR, "MEDIUM", f"Check error: {exc}",
                    "Verify the bind account can read the directory."))
        try:
            if self._conn is not None:
                self._conn.unbind()
        except Exception:
            pass
        return report

    # -- individual checks ----------------------------------------------
    def _check_stale_accounts(self) -> ADFinding:
        """Enabled user accounts idle beyond ``stale_days``."""
        conn = self._connect()
        # Enabled users only (exclude ACCOUNTDISABLE bit).
        flt = ("(&(objectCategory=person)(objectClass=user)"
               "(!(userAccountControl:1.2.840.113556.1.4.803:=2)))")
        entries = self._paged(conn, flt,
                              ["sAMAccountName", "lastLogonTimestamp"])
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.stale_days)
        stale: List[str] = []
        total = 0
        for e in entries:
            attrs = e.get("attributes", {}) if isinstance(e, dict) else {}
            if not attrs:
                continue
            total += 1
            last = _filetime_to_dt(attrs.get("lastLogonTimestamp"))
            if last is None or last < cutoff:
                name = attrs.get("sAMAccountName", "?")
                stale.append(name if isinstance(name, str) else str(name))
        if total == 0:
            return ADFinding(
                "AD-02", "Stale Accounts", WARN, "MEDIUM",
                "No user accounts were returned — the bind account may lack "
                "read permission.",
                "Use an account allowed to read user objects.")
        if stale:
            sample = ", ".join(stale[:8]) + ("…" if len(stale) > 8 else "")
            return ADFinding(
                "AD-02", "Stale Accounts", FAIL, "MEDIUM",
                f"{len(stale)} of {total} enabled accounts have not signed in "
                f"for {self.stale_days}+ days: {sample}",
                "Disable or remove accounts that are no longer used — dormant "
                "enabled accounts are prime targets for password attacks.")
        return ADFinding(
            "AD-02", "Stale Accounts", PASS, "MEDIUM",
            f"All {total} enabled accounts have signed in within "
            f"{self.stale_days} days.")

    def _check_domain_admins(self) -> ADFinding:
        conn = self._connect()
        flt = "(&(objectClass=group)(cn=Domain Admins))"
        entries = self._paged(conn, flt, ["member"])
        members: List[str] = []
        for e in entries:
            attrs = e.get("attributes", {}) if isinstance(e, dict) else {}
            m = attrs.get("member")
            if m:
                members = list(m) if isinstance(m, (list, tuple)) else [m]
                break
        count = len(members)
        if count == 0:
            return ADFinding(
                "AD-03", "Domain Admins Size", WARN, "HIGH",
                "Could not read Domain Admins membership.",
                "Grant the bind account permission to read the group, or "
                "review membership manually.")
        if count > self.max_domain_admins:
            return ADFinding(
                "AD-03", "Domain Admins Size", FAIL, "CRITICAL",
                f"Domain Admins has {count} members (recommended "
                f"≤ {self.max_domain_admins}). Every extra admin widens the "
                "blast radius of a single compromised account.",
                "Remove standing membership; use just-in-time / tiered admin "
                "and separate day-to-day accounts from admin accounts.")
        return ADFinding(
            "AD-03", "Domain Admins Size", PASS, "CRITICAL",
            f"Domain Admins has {count} member(s) — within the recommended "
            f"limit of {self.max_domain_admins}.")

    def _check_machine_account_quota(self) -> ADFinding:
        conn = self._connect()
        base = build_base_dn(self.domain)
        conn.search(base, "(objectClass=domain)", search_scope="BASE",
                    attributes=["ms-DS-MachineAccountQuota"])
        quota = None
        if conn.entries:
            raw = conn.entries[0].entry_attributes_as_dict.get(
                "ms-DS-MachineAccountQuota")
            if raw:
                try:
                    quota = int(raw[0])
                except (ValueError, TypeError):
                    quota = None
        if quota is None:
            return ADFinding(
                "AD-04", "Machine Account Quota", WARN, "HIGH",
                "Could not read ms-DS-MachineAccountQuota.",
                "Verify read access; the default of 10 should be set to 0.")
        if quota > 0:
            return ADFinding(
                "AD-04", "Machine Account Quota", FAIL, "HIGH",
                f"ms-DS-MachineAccountQuota is {quota}: any authenticated user "
                "can join up to that many computers to the domain — abused in "
                "resource-based constrained delegation attacks.",
                "Set the quota to 0: only administrators should create "
                "computer accounts.")
        return ADFinding(
            "AD-04", "Machine Account Quota", PASS, "HIGH",
            "ms-DS-MachineAccountQuota is 0 — only admins can join computers.")

    def _check_krbtgt_age(self) -> ADFinding:
        conn = self._connect()
        flt = "(&(objectClass=user)(sAMAccountName=krbtgt))"
        entries = self._paged(conn, flt, ["pwdLastSet"])
        last = None
        for e in entries:
            attrs = e.get("attributes", {}) if isinstance(e, dict) else {}
            last = _filetime_to_dt(attrs.get("pwdLastSet"))
            break
        if last is None:
            return ADFinding(
                "AD-05", "krbtgt Password Age", WARN, "MEDIUM",
                "Could not read the krbtgt account's password age.",
                "Verify read access to the krbtgt account.")
        age_days = (datetime.now(timezone.utc) - last).days
        if age_days > 180:
            return ADFinding(
                "AD-05", "krbtgt Password Age", WARN, "MEDIUM",
                f"The krbtgt password is {age_days} days old. A very old key "
                "makes forged Kerberos 'golden tickets' valid indefinitely if "
                "the hash was ever stolen.",
                "Rotate the krbtgt password twice (per Microsoft guidance), "
                "at least every 180 days.")
        return ADFinding(
            "AD-05", "krbtgt Password Age", PASS, "MEDIUM",
            f"The krbtgt password was rotated {age_days} days ago.")

    def _check_risky_account_flags(self) -> ADFinding:
        conn = self._connect()
        flt = "(&(objectCategory=person)(objectClass=user))"
        entries = self._paged(conn, flt,
                              ["sAMAccountName", "userAccountControl"])
        no_pw, cleartext, no_expire = [], [], []
        for e in entries:
            attrs = e.get("attributes", {}) if isinstance(e, dict) else {}
            try:
                uac = int(attrs.get("userAccountControl", 0) or 0)
            except (ValueError, TypeError):
                continue
            name = attrs.get("sAMAccountName", "?")
            name = name if isinstance(name, str) else str(name)
            if uac & _UAC["ACCOUNTDISABLE"]:
                continue
            if uac & _UAC["PASSWD_NOTREQD"]:
                no_pw.append(name)
            if uac & _UAC["ENCRYPTED_TEXT_PWD_ALLOWED"]:
                cleartext.append(name)
            if uac & _UAC["DONT_EXPIRE_PASSWORD"]:
                no_expire.append(name)
        problems = []
        if no_pw:
            problems.append(f"{len(no_pw)} with 'password not required'")
        if cleartext:
            problems.append(f"{len(cleartext)} storing reversible-encryption "
                            "passwords")
        if no_expire:
            problems.append(f"{len(no_expire)} with non-expiring passwords")
        if no_pw or cleartext:
            return ADFinding(
                "AD-06", "Risky Account Flags", FAIL, "HIGH",
                "Enabled accounts with dangerous flags: " + "; ".join(problems)
                + ".",
                "Clear PASSWD_NOTREQD and reversible-encryption flags; review "
                "non-expiring-password accounts.")
        if no_expire:
            return ADFinding(
                "AD-06", "Risky Account Flags", WARN, "MEDIUM",
                "Enabled accounts with non-expiring passwords: "
                f"{len(no_expire)}.",
                "Limit non-expiring passwords to well-managed service accounts "
                "(prefer group Managed Service Accounts).")
        return ADFinding(
            "AD-06", "Risky Account Flags", PASS, "HIGH",
            "No enabled accounts carry password-not-required or "
            "reversible-encryption flags.")

    def _open_anonymous(self):
        """Open a fresh unauthenticated LDAP connection (raises if refused)."""
        server = Server(self.domain, use_ssl=self.use_ssl, get_info=ALL)
        return Connection(server, auto_bind=True, receive_timeout=10)

    def _check_anonymous_bind(self) -> ADFinding:
        """A fresh unauthenticated bind that can read objects is a problem."""
        base = build_base_dn(self.domain)
        try:
            anon = self._open_anonymous()
            ok = anon.search(base, "(objectClass=domain)",
                             search_scope="BASE", attributes=["dc"])
            got = bool(anon.entries)
            anon.unbind()
        except Exception:
            # Anonymous bind refused — that is the secure outcome.
            return ADFinding(
                "AD-07", "Anonymous LDAP Bind", PASS, "MEDIUM",
                "The directory refused an anonymous LDAP bind.")
        if ok and got:
            return ADFinding(
                "AD-07", "Anonymous LDAP Bind", FAIL, "MEDIUM",
                "The directory allowed an anonymous bind to read objects — "
                "attackers can enumerate the domain without credentials.",
                "Disable anonymous LDAP access (dsHeuristics) and require "
                "authenticated binds.")
        return ADFinding(
            "AD-07", "Anonymous LDAP Bind", PASS, "MEDIUM",
            "Anonymous bind returned no readable objects.")


def run_ad_audit(domain: Optional[str] = None, user: str = "",
                 password: str = "", **kwargs) -> ADReport:
    """Convenience wrapper: build an :class:`ADAuditor` and run it."""
    return ADAuditor(domain=domain, user=user, password=password,
                     **kwargs).run()


# ---------------------------------------------------------------------------
# Backwards-compatible thin wrappers (dict-returning, single checks)
# ---------------------------------------------------------------------------


def check_ad_connectivity(domain: str, user: str = "",
                          password: str = "") -> Dict[str, Any]:
    auditor = ADAuditor(domain=domain, user=user, password=password)
    if not _HAS_LDAP:
        return ADFinding("AD-01", "AD Connectivity", SKIP, "LOW",
                         "ldap3 not installed; AD checks skipped",
                         "Install ldap3 (pip install ldap3)").to_dict()
    if not auditor.domain:
        return ADFinding("AD-01", "AD Connectivity", SKIP, "LOW",
                         "Host is not domain-joined or domain unavailable",
                         "Run on a domain member or domain controller").to_dict()
    try:
        conn = auditor._connect()
        conn.unbind()
        return ADFinding("AD-01", "AD Connectivity", PASS, "HIGH",
                         f"Connected to Active Directory domain "
                         f"{auditor.domain}").to_dict()
    except Exception as exc:
        return ADFinding("AD-01", "AD Connectivity", ERROR, "HIGH",
                         f"AD connectivity failed: {exc}",
                         "Verify AD network access and credentials").to_dict()
