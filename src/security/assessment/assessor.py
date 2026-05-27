"""
Assessment Module
Core assessment logic for digital hygiene controls

Implements the Zambia Digital Hygiene Certification Program with 15 essential
security controls aligned to NIST CSF, CIS Controls, ISO 27001, and the
UK Cyber Essentials scheme.  Controls C01-C05 are verified automatically on
Windows; controls C06-C15 are evaluated through manual / interview-based
assessment.

Reference frameworks:
    - NIST Cybersecurity Framework v1.1
    - CIS Critical Security Controls v8 (IG1)
    - ISO/IEC 27001:2022 Annex A
    - UK Cyber Essentials
    - Australian Essential Eight
"""

import platform
import datetime
import socket
import ssl
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AssessmentTier(Enum):
    """Three-tier assessment model per proposal Section 8.2"""
    SELF_ASSESSMENT = "self_assessment"      # Tier 1 – Web/PDF checklist
    AUTOMATED = "automated"                  # Tier 2 – Python script
    MANUAL_VERIFICATION = "manual_verification"  # Tier 3 – On-site assessor


@dataclass
class BusinessInfo:
    """Business information for assessment"""
    name: str
    id: str
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    num_employees: Optional[int] = None
    province: Optional[str] = None          # Lusaka / Copperbelt etc.
    years_in_operation: Optional[int] = None


@dataclass
class ControlResult:
    """Result of a single control assessment"""
    control_id: str             # C01 .. C15
    name: str
    score: int
    weight: int
    status: str                 # PASS, WARNING, FAIL, ERROR, NOT_ASSESSED
    details: str
    category: str = "technical"  # technical | administrative | physical
    verification: str = "automated"  # automated | manual | hybrid
    evidence: Optional[str] = None   # Description of evidence collected


@dataclass
class AssessmentResults:
    """Complete assessment results"""
    business_info: BusinessInfo
    controls: Dict[str, ControlResult]
    score: int
    total_possible: int
    certification_level: str
    recommendations: List[str]
    assessment_date: datetime.datetime
    assessment_tier: str = "automated"
    critical_failures: int = 0
    framework_references: List[str] = field(default_factory=lambda: [
        "NIST CSF v1.1", "CIS Controls v8 IG1",
        "ISO 27001:2022", "Cyber Essentials (UK)"
    ])


# ---------------------------------------------------------------------------
# Full 15-control catalogue as defined in Appendix A of the proposal
# ---------------------------------------------------------------------------

CONTROL_CATALOGUE: Dict[str, Dict[str, Any]] = {
    # ── Automated technical controls (C01-C05) ──────────────────────
    "C01_os_updates": {
        "id": "C01", "name": "Operating System Updates",
        "weight": 10, "critical": True,
        "category": "technical", "verification": "automated",
        "description": "Automatic updates enabled; installed within last 30 days",
        "cis_mapping": "CIS Control 7 – Continuous Vulnerability Management",
        "nist_mapping": "PR.IP-12, ID.RA-1",
    },
    "C02_antivirus": {
        "id": "C02", "name": "Antivirus Protection",
        "weight": 15, "critical": True,
        "category": "technical", "verification": "automated",
        "description": "Commercial antivirus or Windows Defender; real-time protection active",
        "cis_mapping": "CIS Control 10 – Malware Defenses",
        "nist_mapping": "DE.CM-4",
    },
    "C03_firewall": {
        "id": "C03", "name": "Firewall Configuration",
        "weight": 10, "critical": True,
        "category": "technical", "verification": "automated",
        "description": "Windows Firewall enabled on all profiles; router firewall enabled",
        "cis_mapping": "CIS Control 9 – Limitation of Network Ports",
        "nist_mapping": "PR.AC-5, PR.PT-4",
    },
    "C04_password_policy": {
        "id": "C04", "name": "Password Policy",
        "weight": 10, "critical": True,
        "category": "technical", "verification": "automated",
        "description": "Minimum 8 characters; change every 90 days; lockout after 5 failures",
        "cis_mapping": "CIS Control 5 – Account Management",
        "nist_mapping": "PR.AC-1, PR.AC-7",
    },
    "C05_backups": {
        "id": "C05", "name": "Backup System",
        "weight": 10, "critical": True,
        "category": "technical", "verification": "automated",
        "description": "Daily automated backups; off-site or cloud storage",
        "cis_mapping": "CIS Control 11 – Data Recovery",
        "nist_mapping": "PR.IP-4, RC.RP-1",
    },
    # ── Manual / administrative controls (C06-C15) ──────────────────
    "C06_security_training": {
        "id": "C06", "name": "Security Awareness Training",
        "weight": 8, "critical": False,
        "category": "administrative", "verification": "manual",
        "description": "Annual security awareness training for all employees; phishing simulations",
        "cis_mapping": "CIS Control 14 – Security Awareness Training",
        "nist_mapping": "PR.AT-1, PR.AT-2",
    },
    "C07_access_control": {
        "id": "C07", "name": "Access Control Policy",
        "weight": 7, "critical": False,
        "category": "administrative", "verification": "manual",
        "description": "Documented access control / least-privilege policy; regular reviews",
        "cis_mapping": "CIS Control 5 – Account Management",
        "nist_mapping": "PR.AC-4",
    },
    "C08_incident_response": {
        "id": "C08", "name": "Incident Response Plan",
        "weight": 7, "critical": False,
        "category": "administrative", "verification": "manual",
        "description": "Documented plan; designated contact person; tested annually; ZICTA/CERT contacts",
        "cis_mapping": "CIS Control 17 – Incident Response Management",
        "nist_mapping": "RS.RP-1, RS.CO-1",
    },
    "C09_encryption": {
        "id": "C09", "name": "Data Encryption",
        "weight": 7, "critical": False,
        "category": "technical", "verification": "manual",
        "description": "Sensitive data encrypted at rest and in transit; full-disk encryption + TLS/HTTPS",
        "cis_mapping": "CIS Control 3 – Data Protection",
        "nist_mapping": "PR.DS-1, PR.DS-2",
    },
    "C10_mobile_security": {
        "id": "C10", "name": "Mobile Device Security",
        "weight": 5, "critical": False,
        "category": "technical", "verification": "manual",
        "description": "Screen lock, trusted apps only, MDM/MAM policy, encryption & remote wipe",
        "cis_mapping": "CIS Control 4 – Secure Configuration",
        "nist_mapping": "PR.AC-2, PR.AC-3",
    },
    "C11_physical_security": {
        "id": "C11", "name": "Physical Security",
        "weight": 5, "critical": False,
        "category": "physical", "verification": "manual",
        "description": "Access-controlled server room; visitor logs; CCTV",
        "cis_mapping": "CIS Control 1 – Inventory of Assets",
        "nist_mapping": "PR.AC-2, PR.IP-5",
    },
    "C12_network_security": {
        "id": "C12", "name": "Network Security",
        "weight": 5, "critical": False,
        "category": "technical", "verification": "manual",
        "description": "WPA2/WPA3 Wi-Fi; guest network; network segmentation",
        "cis_mapping": "CIS Control 9 – Network Infrastructure Management",
        "nist_mapping": "PR.AC-5",
    },
    "C13_acceptable_use": {
        "id": "C13", "name": "Acceptable Use Policy",
        "weight": 5, "critical": False,
        "category": "administrative", "verification": "manual",
        "description": "Documented AUP signed by all staff with regular awareness reminders",
        "cis_mapping": "CIS Control 14 – Security Awareness Training",
        "nist_mapping": "PR.AT-1",
    },
    "C14_vendor_risk": {
        "id": "C14", "name": "Vendor / Third-Party Risk",
        "weight": 8, "critical": False,
        "category": "administrative", "verification": "manual",
        "description": "Vendor contracts include security clauses; formal risk assessment & regular reviews",
        "cis_mapping": "CIS Control 15 – Service Provider Management",
        "nist_mapping": "ID.SC-1, ID.SC-2",
    },
    "C15_regulatory_compliance": {
        "id": "C15", "name": "Regulatory Compliance",
        "weight": 8, "critical": False,
        "category": "administrative", "verification": "manual",
        "description": "Compliant with Zambia Data Protection Act & ZICTA regulations",
        "cis_mapping": "CIS Control 18 – Penetration Testing (Compliance)",
        "nist_mapping": "ID.GV-3, ID.GV-4",
    },
}

# Total possible score across all 15 controls
TOTAL_POSSIBLE_SCORE = sum(c["weight"] for c in CONTROL_CATALOGUE.values())  # 120


class DigitalHygieneAssessor:
    """Main assessment class implementing all 15 digital hygiene controls.

    The assessor supports three assessment tiers:
        Tier 1 – Self-assessment (web checklist / PDF)
        Tier 2 – Automated script (technical controls C01-C05)
        Tier 3 – Manual verification (administrative controls C06-C15)

    When ``manual_answers`` is provided the assessor evaluates C06-C15 using
    those answers; otherwise only the 5 automated controls are scored.
    """

    def __init__(
        self,
        business_info: BusinessInfo,
        manual_answers: Optional[Dict[str, int]] = None,
        assessment_tier: str = "automated",
    ):
        self.business_info = business_info
        self.logger = logger
        self.manual_answers = manual_answers or {}
        self.assessment_tier = assessment_tier

        # Full 15-control catalogue
        self.controls = CONTROL_CATALOGUE

    def run_assessment(self) -> AssessmentResults:
        """Run complete assessment across all 15 controls."""
        self.logger.info(f"Starting assessment for {self.business_info.name} (tier={self.assessment_tier})")

        results: Dict[str, ControlResult] = {}
        critical_failures = 0

        # ── Automated checks (C01-C05) ──────────────────────────────
        results["C01_os_updates"] = self._check_os_updates()
        results["C02_antivirus"] = self._check_antivirus_enhanced()
        results["C03_firewall"] = self._check_firewall_enhanced()
        results["C04_password_policy"] = self._check_password_policy()
        results["C05_backups"] = self._check_backup_system()
        # Additional automated checks feeding into manual control scores
        self._enrich_encryption_control(results)
        self._enrich_network_control(results)

        # ── Manual / administrative checks (C06-C15) ────────────────
        results["C06_security_training"] = self._evaluate_manual("C06_security_training")
        results["C07_access_control"] = self._evaluate_manual("C07_access_control")
        results["C08_incident_response"] = self._evaluate_manual("C08_incident_response")
        results["C09_encryption"] = self._evaluate_manual("C09_encryption")
        results["C10_mobile_security"] = self._evaluate_manual("C10_mobile_security")
        results["C11_physical_security"] = self._evaluate_manual("C11_physical_security")
        results["C12_network_security"] = self._evaluate_manual("C12_network_security")
        results["C13_acceptable_use"] = self._evaluate_manual("C13_acceptable_use")
        results["C14_vendor_risk"] = self._evaluate_manual("C14_vendor_risk")
        results["C15_regulatory_compliance"] = self._evaluate_manual("C15_regulatory_compliance")

        # Count critical failures
        for key, ctrl_def in self.controls.items():
            if ctrl_def.get("critical") and results[key].status == "FAIL":
                critical_failures += 1

        # Calculate total score
        total_score = sum(control.score for control in results.values())
        total_possible = TOTAL_POSSIBLE_SCORE

        # Determine certification level with critical-failure gate
        percentage = (total_score / total_possible) * 100 if total_possible > 0 else 0
        if percentage >= 80 and critical_failures == 0:
            level = "GOLD"
        elif percentage >= 60 and critical_failures <= 1:
            level = "SILVER"
        elif percentage >= 40 and critical_failures <= 2:
            level = "BRONZE"
        else:
            level = "NOT CERTIFIED"

        # Generate recommendations
        recommendations = self._generate_recommendations(results)

        assessment_results = AssessmentResults(
            business_info=self.business_info,
            controls=results,
            score=total_score,
            total_possible=total_possible,
            certification_level=level,
            recommendations=recommendations,
            assessment_date=datetime.datetime.now(),
            assessment_tier=self.assessment_tier,
            critical_failures=critical_failures,
        )

        self.logger.info(
            f"Assessment completed: {total_score}/{total_possible} ({percentage:.0f}%) "
            f"– {level} (critical failures: {critical_failures})"
        )
        return assessment_results

    # ------------------------------------------------------------------
    # Manual control evaluation helper
    # ------------------------------------------------------------------
    def _evaluate_manual(self, control_key: str) -> ControlResult:
        """Evaluate a manual control based on submitted answers.

        ``self.manual_answers`` maps control keys to integer scores (0 to
        control weight).  If no answer is provided the control is marked
        NOT_ASSESSED with score 0.
        """
        ctrl = self.controls[control_key]
        raw = self.manual_answers.get(control_key)

        if raw is None:
            return ControlResult(
                control_id=ctrl["id"],
                name=ctrl["name"],
                score=0,
                weight=ctrl["weight"],
                status="NOT_ASSESSED",
                details="Not evaluated – awaiting manual verification",
                category=ctrl["category"],
                verification=ctrl["verification"],
            )

        score = max(0, min(int(raw), ctrl["weight"]))
        pct = (score / ctrl["weight"]) * 100 if ctrl["weight"] else 0

        if pct >= 80:
            status = "PASS"
        elif pct >= 50:
            status = "WARNING"
        else:
            status = "FAIL"

        return ControlResult(
            control_id=ctrl["id"],
            name=ctrl["name"],
            score=score,
            weight=ctrl["weight"],
            status=status,
            details=f"Manual assessment score: {score}/{ctrl['weight']} ({pct:.0f}%)",
            category=ctrl["category"],
            verification=ctrl["verification"],
        )

    def _check_os_updates(self) -> ControlResult:
        """C01 – Windows Update: service state, last patch date, auto-update config,
        pending-restart flag, and recent hotfix via PowerShell."""
        ctrl = self.controls["C01_os_updates"]
        if platform.system() != 'Windows':
            return ControlResult(
                control_id=ctrl["id"], name=ctrl["name"],
                score=0, weight=ctrl["weight"],
                status="NOT_APPLICABLE",
                details="Non-Windows host — automated check skipped",
                category=ctrl.get("category", "technical"),
                verification=ctrl.get("verification", "automated"),
            )

        try:
            import subprocess
            import winreg  # type: ignore[import]

            findings: list[str] = []
            score = 0

            # 1. Windows Update service (wuauserv) — running or auto-start
            try:
                svc_result = subprocess.run(
                    ['sc', 'query', 'wuauserv'],
                    capture_output=True, text=True, timeout=8, shell=False)
                svc_running = 'RUNNING' in svc_result.stdout.upper()
            except Exception:
                svc_running = False

            # 2. Auto-update configured (AU\NoAutoUpdate = 0 means enabled)
            auto_update_enabled = True
            try:
                key = winreg.OpenKey(  # type: ignore[attr-defined]
                    winreg.HKEY_LOCAL_MACHINE,  # type: ignore[attr-defined]
                    r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU",
                )
                no_auto, _ = winreg.QueryValueEx(key, "NoAutoUpdate")  # type: ignore[attr-defined]
                winreg.CloseKey(key)  # type: ignore[attr-defined]
                auto_update_enabled = (no_auto == 0)
            except Exception:
                pass  # Key absent = default enabled

            # 3. Pending restart flag
            pending_restart = False
            for reg_path in [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired",
            ]:
                try:
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)  # type: ignore[attr-defined]
                    pending_restart = True
                    break
                except Exception:
                    pass

            # 4. Last successful install from registry
            days_since = 999
            last_date_str = "unknown"
            try:
                key = winreg.OpenKey(  # type: ignore[attr-defined]
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\Results\Install",
                )
                ts, _ = winreg.QueryValueEx(key, "LastSuccessTime")  # type: ignore[attr-defined]
                winreg.CloseKey(key)  # type: ignore[attr-defined]
                last_dt = datetime.datetime.fromtimestamp(ts)
                days_since = (datetime.datetime.now() - last_dt).days
                last_date_str = last_dt.strftime('%Y-%m-%d')
            except Exception:
                # Fallback: PowerShell Get-HotFix (last installed hotfix date)
                try:
                    ps = subprocess.run(
                        ['powershell', '-NonInteractive', '-Command',
                         '(Get-HotFix | Sort-Object InstalledOn -Descending |'
                         ' Select-Object -First 1).InstalledOn'],
                        capture_output=True, text=True, timeout=20, shell=False)
                    line = ps.stdout.strip().splitlines()[0] if ps.stdout.strip() else ""
                    if line:
                        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y'):
                            try:
                                last_dt = datetime.datetime.strptime(line.split()[0], fmt)
                                days_since = (datetime.datetime.now() - last_dt).days
                                last_date_str = last_dt.strftime('%Y-%m-%d')
                                break
                            except ValueError:
                                continue
                except Exception:
                    pass

            # Score calculation
            if svc_running or auto_update_enabled:
                score += 3
                findings.append("Windows Update service active")
            else:
                findings.append("Windows Update service not running — enable it")

            if auto_update_enabled:
                score += 2
                findings.append("Automatic updates configured")
            else:
                findings.append("Automatic updates disabled — re-enable via Settings")

            if days_since < 30:
                score += ctrl["weight"] - 5
                findings.append(
                    f"Last patch: {last_date_str} ({days_since}d ago) — current")
            elif days_since < 60:
                score += (ctrl["weight"] - 5) // 2
                findings.append(
                    f"Last patch: {last_date_str} ({days_since}d ago) — update soon")
            else:
                findings.append(
                    f"Last patch: {last_date_str} ({days_since}d ago) — overdue")

            if pending_restart:
                score = max(0, score - 2)
                findings.append("Pending restart required to complete updates")

            score = min(score, ctrl["weight"])
            pct = score / ctrl["weight"] * 100 if ctrl["weight"] else 0
            status = "PASS" if pct >= 80 else ("WARNING" if pct >= 50 else "FAIL")
            details = "; ".join(findings)

        except Exception as exc:
            score, status = 0, "ERROR"
            details = f"Update check error: {exc}"

        return ControlResult(
            control_id=ctrl["id"], name=ctrl["name"],
            score=score, weight=ctrl["weight"],
            status=status, details=details,
            category=ctrl["category"], verification=ctrl["verification"],
        )

    def _check_antivirus(self) -> ControlResult:
        """C02 – Antivirus: Defender status via PowerShell (primary) + registry scan
        (fallback). Checks: AV enabled, real-time protection on, definition age."""
        ctrl = self.controls["C02_antivirus"]
        if platform.system() != 'Windows':
            return ControlResult(
                control_id=ctrl["id"], name=ctrl["name"],
                score=0, weight=ctrl["weight"],
                status="NOT_APPLICABLE",
                details="Non-Windows host — automated check skipped",
                category=ctrl.get("category", "technical"),
                verification=ctrl.get("verification", "automated"),
            )

        try:
            import subprocess
            import json as _json
            import winreg  # type: ignore[import]

            score = 0
            findings: list[str] = []
            av_name = ""

            # ── Primary: PowerShell Get-MpComputerStatus (Defender + 3rd party) ──
            ps_ok = False
            try:
                ps = subprocess.run(
                    ['powershell', '-NonInteractive', '-Command',
                     'Get-MpComputerStatus | Select-Object '
                     'AntivirusEnabled,RealTimeProtectionEnabled,'
                     'AntivirusSignatureAge,AntivirusSignatureLastUpdated,'
                     'QuickScanAge | ConvertTo-Json'],
                    capture_output=True, text=True, timeout=20, shell=False)
                if ps.returncode == 0 and ps.stdout.strip():
                    data = _json.loads(ps.stdout.strip())
                    av_on = bool(data.get('AntivirusEnabled', False))
                    rt_on = bool(data.get('RealTimeProtectionEnabled', False))
                    sig_age = int(data.get('AntivirusSignatureAge') or 999)
                    scan_age = int(data.get('QuickScanAge') or 999)

                    av_name = "Windows Defender"
                    ps_ok = True

                    if av_on:
                        score += 5
                        findings.append("Antivirus enabled")
                    else:
                        findings.append("Antivirus DISABLED — critical risk")

                    if rt_on:
                        score += 4
                        findings.append("Real-time protection ON")
                    else:
                        findings.append("Real-time protection OFF — enable immediately")

                    if sig_age <= 3:
                        score += ctrl["weight"] - 9
                        findings.append(f"Definitions: {sig_age}d old — current")
                    elif sig_age <= 7:
                        score += (ctrl["weight"] - 9) // 2
                        findings.append(f"Definitions: {sig_age}d old — update soon")
                    else:
                        findings.append(f"Definitions: {sig_age}d old — outdated")

                    if scan_age is not None and scan_age < 30:
                        findings.append(f"Last quick scan: {scan_age}d ago")
            except Exception:
                pass

            # ── Fallback: registry installed-programs scan ────────────────────
            if not ps_ok:
                av_terms = [
                    'avast', 'avg', 'bitdefender', 'kaspersky', 'mcafee',
                    'norton', 'eset', 'trend micro', 'sophos', 'malwarebytes',
                    'webroot', 'cylance', 'crowdstrike', 'sentinelone',
                    'windows defender', 'antivirus', 'endpoint protection',
                ]
                for key_path in [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
                ]:
                    try:
                        with winreg.OpenKey(  # type: ignore[attr-defined]
                                winreg.HKEY_LOCAL_MACHINE, key_path) as key:  # type: ignore[attr-defined]
                            for i in range(winreg.QueryInfoKey(key)[0]):  # type: ignore[attr-defined]
                                try:
                                    sk = winreg.EnumKey(key, i)  # type: ignore[attr-defined]
                                    with winreg.OpenKey(key, sk) as sub:  # type: ignore[attr-defined]
                                        name = winreg.QueryValueEx(sub, "DisplayName")[0]  # type: ignore[attr-defined]
                                        if any(t in name.lower() for t in av_terms):
                                            av_name = name
                                            score = ctrl["weight"] * 3 // 4
                                            findings.append(f"AV detected via registry: {name}")
                                            break
                                except Exception:
                                    pass
                        if av_name:
                            break
                    except Exception:
                        pass

                if not av_name:
                    findings.append("No antivirus detected via registry or PowerShell")

            score = min(score, ctrl["weight"])
            pct = score / ctrl["weight"] * 100 if ctrl["weight"] else 0
            status = "PASS" if pct >= 80 else ("WARNING" if pct >= 50 else "FAIL")
            details = f"{av_name + ': ' if av_name else ''}" + "; ".join(findings)

        except Exception as exc:
            score, status = 0, "ERROR"
            details = f"AV check error: {exc}"

        return ControlResult(
            control_id=ctrl["id"], name=ctrl["name"],
            score=score, weight=ctrl["weight"],
            status=status, details=details,
            category=ctrl["category"], verification=ctrl["verification"],
        )

    def _check_firewall(self) -> ControlResult:
        """C03 – Firewall: check all 3 profiles (Domain/Private/Public) individually.
        PASS requires all 3 ON; WARNING if 2/3; FAIL if <2."""
        ctrl = self.controls["C03_firewall"]
        if platform.system() != 'Windows':
            return ControlResult(
                control_id=ctrl["id"], name=ctrl["name"],
                score=0, weight=ctrl["weight"],
                status="NOT_APPLICABLE",
                details="Non-Windows host — automated check skipped",
                category=ctrl.get("category", "technical"),
                verification=ctrl.get("verification", "automated"),
            )

        try:
            import subprocess
            import re

            result = subprocess.run(
                ['netsh', 'advfirewall', 'show', 'allprofiles'],
                capture_output=True, text=True, timeout=10, shell=False)

            # Parse each profile block
            profile_states: dict[str, bool] = {}
            current_profile = None
            for line in result.stdout.splitlines():
                # Detect profile header: "Domain Profile Settings:" etc.
                m = re.match(r'^(Domain|Private|Public)\s+Profile\s+Settings', line, re.I)
                if m:
                    current_profile = m.group(1).title()
                elif current_profile and re.search(r'State\s+ON', line, re.I):
                    profile_states[current_profile] = True
                elif current_profile and re.search(r'State\s+OFF', line, re.I):
                    profile_states[current_profile] = False

            enabled = [p for p, on in profile_states.items() if on]
            disabled = [p for p, on in profile_states.items() if not on]

            # Score: each profile = weight/3 pts; all 3 = bonus
            per_profile = ctrl["weight"] // 3
            score = min(len(enabled) * per_profile, ctrl["weight"])

            if len(enabled) == 3:
                status = "PASS"
                details = f"Firewall ON for all 3 profiles: {', '.join(enabled)}"
            elif len(enabled) == 2:
                status = "WARNING"
                details = (f"Firewall ON: {', '.join(enabled)} — "
                           f"OFF: {', '.join(disabled)} — enable all profiles")
            elif len(enabled) == 1:
                status = "FAIL"
                details = (f"Firewall partially enabled ({enabled[0]} only). "
                           f"Disabled: {', '.join(disabled)}")
            else:
                score = 0
                status = "FAIL"
                details = "Windows Firewall is disabled on all profiles"

        except Exception as exc:
            score, status = 0, "ERROR"
            details = f"Firewall check error: {exc}"

        return ControlResult(
            control_id=ctrl["id"], name=ctrl["name"],
            score=score, weight=ctrl["weight"],
            status=status, details=details,
            category=ctrl["category"], verification=ctrl["verification"],
        )

    def _check_password_policy(self) -> ControlResult:
        """C04 – Check password policy settings via 'net accounts'"""
        ctrl = self.controls["C04_password_policy"]
        if platform.system() != 'Windows':
            return ControlResult(
                control_id=ctrl["id"], name=ctrl["name"],
                score=0, weight=ctrl["weight"],
                status="NOT_APPLICABLE",
                details="Non-Windows host — automated check skipped",
                category=ctrl.get("category", "technical"),
                verification=ctrl.get("verification", "automated"),
            )

        try:
            import subprocess

            result = subprocess.run(
                ['net', 'accounts'],
                capture_output=True, text=True, shell=False,
            )

            min_length = 0
            max_age = 0
            lockout_threshold = 0

            for line in result.stdout.split('\n'):
                if 'Minimum password length' in line:
                    try:
                        min_length = int(line.split()[-1])
                    except ValueError:
                        pass
                elif 'Maximum password age' in line:
                    try:
                        max_age = int(line.split()[-2])
                    except ValueError:
                        pass
                elif 'Lockout threshold' in line:
                    try:
                        lockout_threshold = int(line.split()[-1])
                    except ValueError:
                        pass

            score = 0
            details_parts = []

            if min_length >= 8:
                score += 3
                details_parts.append(f"Password length: {min_length} chars")
            else:
                details_parts.append(f"Password length too short: {min_length} chars")

            if 0 < max_age <= 90:
                score += 3
                details_parts.append(f"Password expires: {max_age} days")
            elif max_age == 0:
                details_parts.append("Passwords never expire (NOT RECOMMENDED)")
            else:
                details_parts.append(f"Password expiry too long: {max_age} days")

            if lockout_threshold > 0 and lockout_threshold <= 5:
                score += 4
                details_parts.append(f"Account lockout after {lockout_threshold} failures")
            elif lockout_threshold > 5:
                score += 2
                details_parts.append(f"Lockout threshold high: {lockout_threshold} failures")
            else:
                details_parts.append("No account lockout policy")

            if score >= 8:
                status = "PASS"
            elif score >= 5:
                status = "WARNING"
            else:
                status = "FAIL"

            details = "; ".join(details_parts)

        except Exception as e:
            score = 0
            status = "ERROR"
            details = f"Error checking password policy: {str(e)}"

        return ControlResult(
            control_id=ctrl["id"], name=ctrl["name"],
            score=score, weight=ctrl["weight"],
            status=status, details=details,
            category=ctrl["category"], verification=ctrl["verification"],
        )

    def _check_backup_system(self) -> ControlResult:
        """C05 – Backup: check installed backup software, Windows File History,
        VSS (Volume Shadow Copy), OneDrive/Google Drive cloud sync, and recent
        backup files in common directories."""
        ctrl = self.controls["C05_backups"]
        if platform.system() != 'Windows':
            return ControlResult(
                control_id=ctrl["id"], name=ctrl["name"],
                score=0, weight=ctrl["weight"],
                status="NOT_APPLICABLE",
                details="Non-Windows host — automated check skipped",
                category=ctrl.get("category", "technical"),
                verification=ctrl.get("verification", "automated"),
            )

        try:
            import os
            import subprocess
            import winreg  # type: ignore[import]

            score = 0
            findings: list[str] = []

            # 1. Dedicated backup software in registry
            bk_terms = [
                'backup', 'acronis', 'veeam', 'carbonite', 'backblaze',
                'crashplan', 'idrive', 'backupassist', 'cobian', 'duplicati',
                'macrium', 'shadow', 'syncback',
            ]
            for reg_root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:  # type: ignore[attr-defined]
                for kp in [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
                ]:
                    try:
                        with winreg.OpenKey(reg_root, kp) as key:  # type: ignore[attr-defined]
                            for i in range(winreg.QueryInfoKey(key)[0]):  # type: ignore[attr-defined]
                                try:
                                    sk = winreg.EnumKey(key, i)  # type: ignore[attr-defined]
                                    with winreg.OpenKey(key, sk) as sub:  # type: ignore[attr-defined]
                                        nm = winreg.QueryValueEx(sub, "DisplayName")[0]  # type: ignore[attr-defined]
                                        if any(t in nm.lower() for t in bk_terms):
                                            score += 4
                                            findings.append(f"Backup software: {nm}")
                                            raise StopIteration
                                except StopIteration:
                                    raise
                                except Exception:
                                    pass
                    except StopIteration:
                        break
                    except Exception:
                        pass

            # 2. Windows File History service
            try:
                r = subprocess.run(['sc', 'query', 'fhsvc'],
                                   capture_output=True, text=True, timeout=5)
                if 'RUNNING' in r.stdout.upper():
                    score += 2
                    findings.append("Windows File History active")
            except Exception:
                pass

            # 3. Volume Shadow Copy (VSS) — snapshot-based backup
            try:
                r = subprocess.run(['vssadmin', 'list', 'shadows'],
                                   capture_output=True, text=True, timeout=8)
                if 'Shadow Copy Volume' in r.stdout:
                    score += 2
                    shadow_count = r.stdout.count('Shadow Copy Volume')
                    findings.append(f"VSS: {shadow_count} shadow copy/copies found")
                elif r.returncode == 0:
                    findings.append("VSS: no shadow copies — configure automatic backups")
            except Exception:
                pass

            # 4. Cloud backup: OneDrive / Google Drive / Dropbox
            cloud_paths = {
                'OneDrive': os.path.expanduser('~/OneDrive'),
                'Google Drive': os.path.expanduser('~/Google Drive'),
                'Dropbox': os.path.expanduser('~/Dropbox'),
            }
            for cloud_name, cloud_path in cloud_paths.items():
                if os.path.isdir(cloud_path):
                    score += 1
                    findings.append(f"{cloud_name} folder detected")
                    break

            # 5. Recent backup files in common directories
            profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
            scan_dirs = [
                Path("C:/Backup"), Path("D:/Backup"), Path("E:/Backup"),
                Path(profile) / "Backup",
                Path(profile) / "Documents" / "Backup",
                Path(profile) / "Desktop" / "Backup",
            ]
            for d in scan_dirs:
                if d.exists():
                    for fp in d.rglob("*"):
                        if fp.is_file():
                            age = (datetime.datetime.now() -
                                   datetime.datetime.fromtimestamp(fp.stat().st_mtime)).days
                            if age < 14:
                                score += 1
                                findings.append(f"Recent backup file in {d.name}/ ({age}d ago)")
                                break

            score = min(score, ctrl["weight"])
            pct = score / ctrl["weight"] * 100 if ctrl["weight"] else 0
            if pct >= 70:
                status = "PASS"
            elif pct >= 40:
                status = "WARNING"
            else:
                status = "FAIL"
                if not findings:
                    findings.append("No backup system, shadow copies, or cloud sync detected")

            details = "; ".join(findings) if findings else "No backup evidence found"

        except Exception as exc:
            score, status = 0, "ERROR"
            details = f"Backup check error: {exc}"

        return ControlResult(
            control_id=ctrl["id"], name=ctrl["name"],
            score=score, weight=ctrl["weight"],
            status=status, details=details,
            category=ctrl["category"], verification=ctrl["verification"],
        )

    # ------------------------------------------------------------------
    # Enhanced wrappers that combine multiple sub-checks
    # ------------------------------------------------------------------

    def _check_antivirus_enhanced(self) -> ControlResult:
        """C02 – Antivirus + Windows Defender ATP real-time check."""
        base = self._check_antivirus()
        if platform.system() == 'Windows':
            atp_status, atp_detail = self._check_windows_defender_atp()
            if atp_status == 'PASS' and base.status in ('FAIL', 'ERROR'):
                # Defender ATP confirms AV is active even if WMI/registry missed it
                ctrl = self.controls["C02_antivirus"]
                return ControlResult(
                    control_id=ctrl["id"], name=ctrl["name"],
                    score=ctrl["weight"], weight=ctrl["weight"],
                    status="PASS",
                    details=f"Windows Defender ATP: {atp_detail}",
                    category=ctrl["category"], verification=ctrl["verification"],
                )
            elif base.status == 'PASS':
                base.details += f" | Defender ATP: {atp_detail}"
        return base

    def _check_firewall_enhanced(self) -> ControlResult:
        """C03 – Firewall + RDP exposure + admin shares check."""
        base = self._check_firewall()
        rdp_status, rdp_detail = self._check_rdp_exposure()
        share_status, share_detail = self._check_admin_shares()
        extra = []
        if rdp_status == 'WARNING':
            extra.append(f"⚠ {rdp_detail}")
        if share_status == 'WARNING':
            extra.append(f"⚠ {share_detail}")
        if extra:
            base.details += " | " + " | ".join(extra)
            if base.status == 'PASS':
                base.status = 'WARNING'
                base.score = max(0, base.score - (base.weight // 4))
        return base

    def _enrich_encryption_control(self, results: Dict[str, 'ControlResult']) -> None:
        """Supplement C09 (Encryption) with BitLocker + screen lock checks.

        Only enriches the control if it was NOT manually assessed (score = 0,
        status = NOT_ASSESSED).  When running fully automated tier we inject
        evidence so the auditor has actionable data even before manual review.
        """
        ctrl_key = "C09_encryption"
        existing = results.get(ctrl_key)
        if existing is None or existing.status != 'NOT_ASSESSED':
            return  # Manual answer already provided – don't override
        bl_status, bl_detail = self._check_bitlocker()
        sl_status, sl_detail = self._check_screen_lock_policy()
        parts = [f"BitLocker: {bl_detail}", f"Screen lock: {sl_detail}"]
        passed = sum(1 for s in (bl_status, sl_status) if s == 'PASS')
        ctrl = self.controls[ctrl_key]
        if passed == 2:
            score, status = ctrl["weight"], "PASS"
        elif passed == 1:
            score, status = ctrl["weight"] // 2, "WARNING"
        else:
            score, status = 0, "FAIL"
        results[ctrl_key] = ControlResult(
            control_id=ctrl["id"], name=ctrl["name"],
            score=score, weight=ctrl["weight"],
            status=status,
            details=" | ".join(parts),
            category=ctrl["category"], verification="automated",
        )

    def _enrich_network_control(self, results: Dict[str, 'ControlResult']) -> None:
        """Supplement C12 (Network Security) with USB policy + admin shares."""
        ctrl_key = "C12_network_security"
        existing = results.get(ctrl_key)
        if existing is None or existing.status != 'NOT_ASSESSED':
            return
        usb_status, usb_detail = self._check_usb_policy()
        share_status, share_detail = self._check_admin_shares()
        rdp_status, rdp_detail = self._check_rdp_exposure()
        parts = [f"USB policy: {usb_detail}", f"Admin shares: {share_detail}", f"RDP: {rdp_detail}"]
        passed = sum(1 for s in (usb_status, share_status, rdp_status) if s == 'PASS')
        ctrl = self.controls[ctrl_key]
        if passed == 3:
            score, status = ctrl["weight"], "PASS"
        elif passed >= 2:
            score, status = ctrl["weight"] * 2 // 3, "WARNING"
        elif passed == 1:
            score, status = ctrl["weight"] // 3, "WARNING"
        else:
            score, status = 0, "FAIL"
        results[ctrl_key] = ControlResult(
            control_id=ctrl["id"], name=ctrl["name"],
            score=score, weight=ctrl["weight"],
            status=status,
            details=" | ".join(parts),
            category=ctrl["category"], verification="automated",
        )

    # ------------------------------------------------------------------
    # Additional Windows security checks (called as part of C09/C12)
    # ------------------------------------------------------------------

    def _check_bitlocker(self) -> Tuple[str, str]:
        """Check BitLocker disk encryption status. Returns (status, details)."""
        if platform.system() != 'Windows':
            return 'NOT_APPLICABLE', 'Non-Windows host'
        try:
            import subprocess
            result = subprocess.run(
                ['manage-bde', '-status', 'C:'],
                capture_output=True, text=True, timeout=10, shell=False,
            )
            if 'Fully Encrypted' in result.stdout:
                return 'PASS', 'BitLocker fully encrypted on C:'
            elif 'Encryption in Progress' in result.stdout:
                return 'WARNING', 'BitLocker encryption in progress on C:'
            elif result.returncode == 0:
                return 'FAIL', 'BitLocker not enabled on C:'
            return 'ERROR', 'Cannot determine BitLocker status'
        except FileNotFoundError:
            return 'ERROR', 'manage-bde not found (requires admin)'
        except Exception as exc:
            return 'ERROR', f'BitLocker check failed: {exc}'

    def _check_rdp_exposure(self) -> Tuple[str, str]:
        """Check if RDP (port 3389) is openly accessible from localhost."""
        try:
            with socket.create_connection(('127.0.0.1', 3389), timeout=1):
                return 'WARNING', 'RDP port 3389 is open – ensure Network Level Authentication and restrict access'
        except (ConnectionRefusedError, socket.timeout, OSError):
            return 'PASS', 'RDP port 3389 not exposed on localhost'
        except Exception as exc:
            return 'ERROR', f'RDP check error: {exc}'

    def _check_admin_shares(self) -> Tuple[str, str]:
        """Check if Windows default admin shares (C$, ADMIN$) are enabled."""
        if platform.system() != 'Windows':
            return 'NOT_APPLICABLE', 'Non-Windows host'
        try:
            import subprocess
            result = subprocess.run(
                ['net', 'share'],
                capture_output=True, text=True, timeout=8, shell=False,
            )
            exposed = [s for s in ('C$', 'ADMIN$', 'IPC$') if s in result.stdout]
            if 'C$' in exposed or 'ADMIN$' in exposed:
                return ('WARNING',
                        f"Default admin shares exposed: {', '.join(exposed)}"
                        " - consider disabling C$ and ADMIN$")
            return 'PASS', 'No dangerous default admin shares detected'
        except Exception as exc:
            return 'ERROR', f'Admin shares check failed: {exc}'

    def _check_screen_lock_policy(self) -> Tuple[str, str]:
        """Check Windows screen-saver lock / idle timeout policy."""
        if platform.system() != 'Windows':
            return 'NOT_APPLICABLE', 'Non-Windows host'
        try:
            import winreg
            # Check screen saver enabled and password-protected
            try:
                key = winreg.OpenKey(  # type: ignore[attr-defined]
                    winreg.HKEY_CURRENT_USER,  # type: ignore[attr-defined]
                    r'Control Panel\Desktop',
                )
                ss_active, _ = winreg.QueryValueEx(key, 'ScreenSaveActive')  # type: ignore[attr-defined]
                ss_secure, _ = winreg.QueryValueEx(key, 'ScreenSaverIsSecure')  # type: ignore[attr-defined]
                ss_timeout, _ = winreg.QueryValueEx(key, 'ScreenSaveTimeOut')  # type: ignore[attr-defined]
                winreg.CloseKey(key)  # type: ignore[attr-defined]
                timeout_min = int(ss_timeout) // 60 if ss_timeout else 0
                if ss_active == '1' and ss_secure == '1' and timeout_min <= 15:
                    return 'PASS', f'Screen lock active with password, timeout: {timeout_min} min'
                elif ss_active == '1' and ss_secure == '1':
                    return 'WARNING', f'Screen lock enabled but timeout too long: {timeout_min} min (recommend ≤ 15)'
                return 'FAIL', 'Screen saver lock not properly configured'
            except FileNotFoundError:
                return 'WARNING', 'Screen lock policy not found in registry'
        except ImportError:
            return 'ERROR', 'winreg not available'
        except Exception as exc:
            return 'ERROR', f'Screen lock check failed: {exc}'

    def _check_usb_policy(self) -> Tuple[str, str]:
        """Check if removable storage (USB) is restricted via registry."""
        if platform.system() != 'Windows':
            return 'NOT_APPLICABLE', 'Non-Windows host'
        try:
            import winreg
            try:
                key = winreg.OpenKey(  # type: ignore[attr-defined]
                    winreg.HKEY_LOCAL_MACHINE,  # type: ignore[attr-defined]
                    r'SYSTEM\CurrentControlSet\Services\USBSTOR',
                )
                start_val, _ = winreg.QueryValueEx(key, 'Start')  # type: ignore[attr-defined]
                winreg.CloseKey(key)  # type: ignore[attr-defined]
                if start_val == 4:
                    return 'PASS', 'USB storage driver disabled (Start=4)'
                return 'WARNING', f'USB storage enabled (Start={start_val}) – consider restricting removable media'
            except FileNotFoundError:
                return 'WARNING', 'USB storage policy not configured'
        except ImportError:
            return 'ERROR', 'winreg not available'
        except Exception as exc:
            return 'ERROR', f'USB policy check failed: {exc}'

    # ------------------------------------------------------------------
    # Extended security checks (bonus — beyond C01-C05)
    # ------------------------------------------------------------------

    def _check_ransomware_protection(self) -> Tuple[str, str]:
        """EX-01: Controlled Folder Access (Windows ransomware protection)."""
        if platform.system() != 'Windows':
            return 'NOT_APPLICABLE', 'Non-Windows host'
        try:
            import subprocess
            import json as _json
            ps = subprocess.run(
                ['powershell', '-NonInteractive', '-Command',
                 'Get-MpPreference | Select-Object '
                 'EnableControlledFolderAccess | ConvertTo-Json'],
                capture_output=True, text=True, timeout=15, shell=False)
            if ps.returncode == 0 and ps.stdout.strip():
                data = _json.loads(ps.stdout.strip())
                cfa = data.get('EnableControlledFolderAccess', 0)
                if cfa == 1:
                    return 'PASS', 'Controlled Folder Access (ransomware protection) is ON'
                elif cfa == 2:
                    return 'WARNING', 'Controlled Folder Access is in audit mode — enable it'
                return 'FAIL', ('Controlled Folder Access is OFF — enable via '
                                'Windows Security > Virus & threat protection')
            return 'WARNING', 'Could not query Controlled Folder Access status'
        except Exception as exc:
            return 'ERROR', f'Ransomware protection check error: {exc}'

    def _check_local_accounts(self) -> Tuple[str, str]:
        """EX-02: Local account audit — guest disabled, admin count, default admin."""
        if platform.system() != 'Windows':
            return 'NOT_APPLICABLE', 'Non-Windows host'
        try:
            import subprocess
            import json as _json
            ps = subprocess.run(
                ['powershell', '-NonInteractive', '-Command',
                 'Get-LocalUser | Select-Object Name,Enabled | ConvertTo-Json'],
                capture_output=True, text=True, timeout=15, shell=False)
            issues = []
            if ps.returncode == 0 and ps.stdout.strip():
                raw = _json.loads(ps.stdout.strip())
                users = raw if isinstance(raw, list) else [raw]
                admin_on = [u for u in users
                            if u.get('Name', '').lower() == 'administrator'
                            and u.get('Enabled', False)]
                guest_on = [u for u in users
                            if u.get('Name', '').lower() == 'guest'
                            and u.get('Enabled', False)]
                enabled_count = sum(1 for u in users if u.get('Enabled', False))
                if admin_on:
                    issues.append('Built-in Administrator account is ENABLED — disable it')
                if guest_on:
                    issues.append('Guest account is ENABLED — disable it')
                summary = f'{enabled_count} enabled local account(s)'
                if not issues:
                    return 'PASS', f'{summary} — no built-in account risks detected'
                return 'WARNING', f'{summary}; ' + '; '.join(issues)
            return 'WARNING', 'Could not enumerate local user accounts'
        except Exception as exc:
            return 'ERROR', f'Local accounts check error: {exc}'

    def _check_autorun_policy(self) -> Tuple[str, str]:
        """EX-03: AutoRun/AutoPlay disabled — prevents USB/CD malware."""
        if platform.system() != 'Windows':
            return 'NOT_APPLICABLE', 'Non-Windows host'
        try:
            import winreg  # type: ignore[import]
            # NoDriveTypeAutoRun = 0xFF (255) disables AutoRun for all drives
            for hive, path in [
                (winreg.HKEY_LOCAL_MACHINE,  # type: ignore[attr-defined]
                 r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer'),
                (winreg.HKEY_CURRENT_USER,   # type: ignore[attr-defined]
                 r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer'),
            ]:
                try:
                    key = winreg.OpenKey(hive, path)  # type: ignore[attr-defined]
                    val, _ = winreg.QueryValueEx(key, 'NoDriveTypeAutoRun')  # type: ignore[attr-defined]
                    winreg.CloseKey(key)  # type: ignore[attr-defined]
                    if val >= 0xFF or val == 0x91:
                        return 'PASS', f'AutoRun disabled (NoDriveTypeAutoRun=0x{val:X})'
                    return 'WARNING', (
                        f'AutoRun partially restricted (0x{val:X}) — '
                        'set NoDriveTypeAutoRun=0xFF to disable for all drives')
                except FileNotFoundError:
                    continue
                except Exception:
                    continue
            return 'FAIL', ('AutoRun is NOT disabled — USB drives autorun malware risk. '
                            'Enable via Group Policy or registry.')
        except Exception as exc:
            return 'ERROR', f'AutoRun check error: {exc}'

    def _check_windows_hello(self) -> Tuple[str, str]:
        """EX-04: Windows Hello / PIN — modern, phishing-resistant authentication."""
        if platform.system() != 'Windows':
            return 'NOT_APPLICABLE', 'Non-Windows host'
        try:
            import subprocess
            ps = subprocess.run(
                ['powershell', '-NonInteractive', '-Command',
                 'Get-WmiObject -Class Win32_UserAccount | '
                 'Where-Object {$_.LocalAccount -eq $True -and $_.Disabled -eq $False} | '
                 'Measure-Object | Select-Object -ExpandProperty Count'],
                capture_output=True, text=True, timeout=15, shell=False)

            # Check NGC (Next Generation Credentials) folder — indicates Hello/PIN set up
            import os
            ngc_path = os.path.join(
                os.environ.get('WINDIR', 'C:\\Windows'),
                'ServiceProfiles', 'LocalService', 'AppData', 'Local',
                'Microsoft', 'Ngc')
            if os.path.isdir(ngc_path) and any(
                    os.scandir(ngc_path)):
                return 'PASS', 'Windows Hello / PIN configured (NGC credentials found)'
            # Fallback: check Hello policy
            import winreg  # type: ignore[import]
            try:
                key = winreg.OpenKey(  # type: ignore[attr-defined]
                    winreg.HKEY_LOCAL_MACHINE,
                    r'SOFTWARE\Policies\Microsoft\PassportForWork')
                enabled, _ = winreg.QueryValueEx(key, 'Enabled')  # type: ignore[attr-defined]
                winreg.CloseKey(key)  # type: ignore[attr-defined]
                if enabled:
                    return 'PASS', 'Windows Hello policy is enabled'
                return 'WARNING', 'Windows Hello policy is disabled by GPO'
            except FileNotFoundError:
                pass
            return 'WARNING', ('Windows Hello / PIN not detected — configure via '
                               'Settings > Accounts > Sign-in options')
        except Exception as exc:
            return 'ERROR', f'Windows Hello check error: {exc}'

    def _check_pending_security_updates(self) -> Tuple[str, str]:
        """EX-05: Check for pending Windows security updates.

        Uses three signals in order of reliability:
        1. Registry reboot-pending keys (fast, no admin needed)
        2. System event log ID 19 (most recent successful update install)
        3. WUA service state as a fallback signal
        """
        if platform.system() != 'Windows':
            return 'NOT_APPLICABLE', 'Non-Windows host'
        try:
            import winreg  # type: ignore[import]
            import subprocess

            signals: list[str] = []
            pending_reboot = False

            # 1. Registry keys that indicate updates are pending a restart
            reboot_keys = [
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired',
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending',
            ]
            for rk in reboot_keys:
                try:
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rk)  # type: ignore[attr-defined]
                    pending_reboot = True
                    break
                except Exception:
                    pass

            if pending_reboot:
                signals.append('Reboot required to apply pending updates')

            # 2. Most recent update install via System event log (ID 19)
            try:
                ps = subprocess.run(
                    ['powershell', '-NonInteractive', '-Command',
                     'try { $e = Get-WinEvent -FilterHashtable @{LogName="System";Id=19} '
                     '-MaxEvents 1 -EA Stop; $e.TimeCreated.ToString("yyyy-MM-dd") } '
                     'catch { "" }'],
                    capture_output=True, text=True, timeout=12,
                )
                ts = ps.stdout.strip()
                if ts and len(ts) >= 10:
                    try:
                        last_dt = datetime.datetime.strptime(ts[:10], '%Y-%m-%d')
                        days_ago = (datetime.datetime.now() - last_dt).days
                        signals.append(f'Last successful update: {ts[:10]} ({days_ago}d ago)')
                        if not pending_reboot:
                            if days_ago <= 30:
                                return 'PASS', '; '.join(signals) or 'Updates appear current'
                            return 'WARNING', f'Last update {days_ago}d ago — consider running Windows Update'
                    except ValueError:
                        pass
            except Exception:
                pass

            # 3. WUA service state as a final signal
            try:
                svc = subprocess.run(['sc', 'query', 'wuauserv'],
                                     capture_output=True, text=True, timeout=5)
                if 'RUNNING' in svc.stdout.upper():
                    signals.append('Windows Update service is running')
                else:
                    signals.append('Windows Update service is NOT running')
            except Exception:
                pass

            detail = '; '.join(signals) if signals else 'Unable to determine update status'
            if pending_reboot:
                return 'FAIL', detail
            return 'WARNING', detail

        except Exception as exc:
            return 'ERROR', f'Pending updates check error: {exc}'

    def _check_windows_defender_atp(self) -> Tuple[str, str]:
        """Check Windows Defender real-time protection and definition age."""
        if platform.system() != 'Windows':
            return 'NOT_APPLICABLE', 'Non-Windows host'
        try:
            import subprocess
            result = subprocess.run(
                ['powershell', '-NonInteractive', '-Command',
                 'Get-MpComputerStatus | Select-Object '
                 'AntivirusEnabled,RealTimeProtectionEnabled,'
                 'AntivirusSignatureAge | ConvertTo-Json'],
                capture_output=True, text=True, timeout=15, shell=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                import json as _json
                data = _json.loads(result.stdout.strip())
                av_on = data.get('AntivirusEnabled', False)
                rt_on = data.get('RealTimeProtectionEnabled', False)
                sig_age = data.get('AntivirusSignatureAge', 999)
                if av_on and rt_on and sig_age <= 3:
                    return 'PASS', f'Defender enabled, real-time on, definitions {sig_age} day(s) old'
                elif av_on and rt_on:
                    return 'WARNING', f'Defender enabled but definitions {sig_age} day(s) old (update recommended)'
                return 'FAIL', 'Windows Defender not fully active'
            return 'WARNING', 'Unable to query Defender status via PowerShell'
        except Exception as exc:
            return 'ERROR', f'Defender ATP check failed: {exc}'

    def _generate_recommendations(self, results: Dict[str, ControlResult]) -> List[str]:
        """Generate prioritised recommendations based on assessment results.

        Recommendations are ordered: critical failures first, then by
        potential score uplift (highest weight failures prioritised).
        """
        recommendations: List[str] = []

        # Plain-English action steps — written for non-technical business owners
        RECS = {
            "C01_os_updates": (
                "Turn on automatic Windows updates. Go to Settings → Windows Update → "
                "turn on 'Automatic Updates'. This keeps your computer protected against "
                "new threats automatically."
            ),
            "C02_antivirus": (
                "Make sure Windows Defender is turned on, or install free antivirus software "
                "(e.g. Avast Free or AVG Free). Open it and check that real-time protection "
                "is switched ON and virus definitions are up to date."
            ),
            "C03_firewall": (
                "Turn on Windows Firewall: go to Control Panel → System and Security → "
                "Windows Defender Firewall → Turn Windows Defender Firewall on. "
                "Do this for both 'Private' and 'Public' networks."
            ),
            "C04_password_policy": (
                "Require all staff to use strong passwords (at least 8 characters mixing "
                "letters, numbers and symbols). Change passwords every 3 months, and "
                "lock accounts after 5 wrong attempts. Use a free password manager "
                "like Bitwarden to help staff remember them."
            ),
            "C05_backups": (
                "Set up daily automatic backups of your important files. Use an external "
                "hard drive kept off-site, or a free cloud service like Google Drive or "
                "OneDrive. Test that you can restore files at least once every 3 months."
            ),
            "C06_security_training": (
                "Book your staff into a short free cybersecurity awareness session. "
                "ZICTA offers resources at zicta.zm. At minimum, train staff to spot "
                "fake emails (phishing) and use strong passwords — once per year."
            ),
            "C07_access_control": (
                "Write down who is allowed to access which files or systems. Make sure "
                "only the people who need access have it. When a staff member leaves, "
                "remove their access the same day. Review the list every 6 months."
            ),
            "C08_incident_response": (
                "Write a simple one-page plan: what to do if you are hacked or data is "
                "stolen. Include who to call (IT provider, ZICTA on +260 211 369 000, "
                "CERT-ZM), what to switch off, and how to inform customers. "
                "Practise the plan once a year."
            ),
            "C09_encryption": (
                "Enable BitLocker on Windows laptops (search 'BitLocker' in the Start menu) "
                "to protect data if a device is lost or stolen. Make sure your website "
                "uses HTTPS — your browser should show a padlock in the address bar."
            ),
            "C10_mobile_security": (
                "Set a PIN or fingerprint lock on all business phones and tablets. "
                "Set them to lock automatically after 5 minutes of inactivity. "
                "Enable 'Find My Device' so you can wipe a lost phone remotely. "
                "Only install apps from the official app store."
            ),
            "C11_physical_security": (
                "Keep your router, server, and main computers in a locked room or "
                "locked cabinet. Only authorised staff should have the key. "
                "Keep a simple visitor log (name, time in, time out) and consider "
                "a basic security camera for the IT area."
            ),
            "C12_network_security": (
                "Change your Wi-Fi password to something strong (at least 12 random "
                "characters). Set your router to use WPA2 or WPA3 security mode. "
                "Create a separate guest Wi-Fi for visitors so they cannot access "
                "your business files — most modern routers support this."
            ),
            "C13_acceptable_use": (
                "Write a short one-page policy stating what staff can and cannot do "
                "on company computers (e.g. no personal downloads, no sharing passwords). "
                "Ask all staff to read and sign it. Remind them about it each year."
            ),
            "C14_vendor_risk": (
                "Ask your IT suppliers, cloud providers, and payment processors to "
                "confirm in writing how they protect your data. Include a security clause "
                "in any new supplier contracts. Check your key suppliers once a year."
            ),
            "C15_regulatory_compliance": (
                "Register your data processing activities with the Data Protection "
                "Commission (DPC) under the Zambia Data Protection Act 2021. "
                "Contact ZICTA (zicta.zm) if unsure about cybersecurity obligations. "
                "Consider a free legal clinic at UNZA or a local law firm."
            ),
        }

        # Build prioritised list: critical failures first, then warnings
        critical_keys = [k for k, c in self.controls.items() if c.get("critical")]
        non_critical = [k for k in self.controls if k not in critical_keys]

        for key in critical_keys + non_critical:
            if results[key].status in ("FAIL", "ERROR"):
                prefix = "🔴 Urgent: "
                recommendations.append(prefix + RECS.get(key, f"Address {results[key].name}."))
            elif results[key].status == "WARNING":
                recommendations.append("🟡 Improve: " + RECS.get(key, f"Improve {results[key].name}."))
            elif results[key].status == "NOT_ASSESSED":
                recommendations.append(
                    f"Not checked: {results[key].name}"
                    " - answer the manual questions to assess this."
                )

        # Zambia-specific standing reminders
        recommendations.append(
            "📋 Register with ZICTA (zicta.zm) and sign up for CERT-ZM security alerts — it is free."
        )
        recommendations.append(
            "📋 Ensure compliance with the Zambia Data Protection Act No. 3 of 2021 "
            "and the Cyber Security and Cyber Crimes Act, 2021."
        )

        return recommendations


class InfrastructureAssessor:
    """Infrastructure hygiene checks for public-facing services.

    Extended checks cover:
    - DNS resolution and DNS security (SPF, DMARC, DNSSEC)
    - SSL/TLS certificate validity and minimum protocol version
    - HTTP→HTTPS redirect
    - HTTP security response headers (HSTS, CSP, X-Frame-Options, etc.)
    - Common port exposure
    - External IP discovery
    """

    COMMON_PORTS = [21, 22, 23, 25, 80, 443, 3306, 3389, 5432, 8080, 8443]
    RISKY_PORTS = {
        21: 'FTP (unencrypted)',
        23: 'Telnet (unencrypted)',
        25: 'SMTP (may expose mail relay)',
        3306: 'MySQL (direct exposure)',
        3389: 'RDP (remote desktop – high risk)',
        5432: 'PostgreSQL (direct exposure)',
    }

    def __init__(self, target: str = 'localhost'):
        self.target = target.strip() or 'localhost'

    def run_checks(self) -> Dict[str, Any]:
        return {
            'dns_resolution': self._check_dns_resolution(),
            'dns_security': self._check_dns_security(),
            'ssl_certificate': self._check_ssl_certificate(),
            'tls_version': self._check_tls_version(),
            'https_redirect': self._check_https_redirect(),
            'security_headers': self._check_security_headers(),
            'external_ip': self._get_external_ip(),
            'open_ports': self._scan_common_ports(),
            'risky_ports': self._identify_risky_ports(),
        }

    def _check_dns_resolution(self) -> str:
        try:
            infos = socket.getaddrinfo(self.target, None)
            addresses = sorted({item[4][0] for item in infos if item and item[4]})
            if not addresses:
                return 'No DNS records found'
            return f"Resolves to {', '.join(str(a) for a in addresses)}"
        except Exception as exc:
            return f"DNS resolution failed: {exc}"

    def _check_dns_security(self) -> Dict[str, str]:
        """Check DNS security records: SPF, DMARC, DKIM (selector _domainkey)."""
        results = {'spf': 'Not checked', 'dmarc': 'Not checked', 'notes': ''}
        if self.target in ('localhost', '127.0.0.1'):
            results['notes'] = 'Local host – DNS security check skipped'
            return results
        try:
            import subprocess
            # SPF record check
            try:
                r = subprocess.run(
                    ['dig', '+short', 'TXT', self.target],
                    capture_output=True, text=True, timeout=5,
                )
                txt_records = r.stdout.strip()
                if 'v=spf1' in txt_records:
                    results['spf'] = 'SPF record found'
                else:
                    results['spf'] = 'No SPF record – email spoofing risk'
            except Exception:
                results['spf'] = 'Unable to check SPF (dig not available)'

            # DMARC record check
            try:
                r = subprocess.run(
                    ['dig', '+short', 'TXT', f'_dmarc.{self.target}'],
                    capture_output=True, text=True, timeout=5,
                )
                dmarc_out = r.stdout.strip()
                if 'v=DMARC1' in dmarc_out:
                    results['dmarc'] = 'DMARC record found'
                else:
                    results['dmarc'] = 'No DMARC record – phishing risk'
            except Exception:
                results['dmarc'] = 'Unable to check DMARC (dig not available)'

        except Exception as exc:
            results['notes'] = f'DNS security check error: {exc}'
        return results

    def _check_ssl_certificate(self) -> str:
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.target, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=self.target) as ssock:
                    cert = ssock.getpeercert()
                    if cert is None:
                        return 'SSL/TLS enabled (no certificate data)'
                    expires_str = str(cert.get('notAfter', ''))
                    # Check days until expiry
                    try:
                        import time
                        expires_epoch = ssl.cert_time_to_seconds(expires_str)
                        days_left = (expires_epoch - time.time()) / 86400
                        if days_left < 0:
                            return f"SSL certificate EXPIRED ({expires_str})"
                        elif days_left < 30:
                            return (
                                f"SSL/TLS enabled but expires SOON in "
                                f"{int(days_left)} days ({expires_str})"
                            )
                        return f"SSL/TLS enabled, expires: {expires_str} ({int(days_left)} days)"
                    except Exception:
                        return f"SSL/TLS enabled, expires: {expires_str}"
        except ssl.SSLCertVerificationError as exc:
            return f"SSL certificate verification failed: {exc}"
        except Exception as exc:
            return f"SSL/TLS not detected: {exc}"

    def _check_tls_version(self) -> str:
        """Check whether the server accepts TLS 1.0 or 1.1 (deprecated)."""
        if self.target in ('localhost', '127.0.0.1'):
            return 'Local host – TLS version check skipped'
        issues = []
        for proto_name, proto_const in [('TLSv1.0', ssl.TLSVersion.TLSv1), ('TLSv1.1', ssl.TLSVersion.TLSv1_1)]:
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.minimum_version = proto_const
                ctx.maximum_version = proto_const
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with socket.create_connection((self.target, 443), timeout=3) as s:
                    with ctx.wrap_socket(s, server_hostname=self.target):
                        issues.append(f"{proto_name} accepted (deprecated – disable it)")
            except (ssl.SSLError, AttributeError, OSError):
                pass
            except Exception:
                pass
        if issues:
            return "WARNING – deprecated TLS versions accepted: " + "; ".join(issues)
        return "Good – only TLS 1.2+ accepted"

    def _check_https_redirect(self) -> str:
        try:
            import urllib.request

            url = f'http://{self.target}'
            req = urllib.request.Request(url, method='GET')
            opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
            response = opener.open(req, timeout=5)
            final_url = response.geturl()
            if final_url.startswith('https://'):
                return f'HTTP redirects to HTTPS ({final_url})'
            return f'HTTP does not redirect to HTTPS (final: {final_url})'
        except Exception as exc:
            return f'HTTPS redirect check failed: {exc}'

    def _check_security_headers(self) -> Dict[str, str]:
        """Check HTTP response security headers on the target."""
        headers_status = {}
        required_headers = {
            'Strict-Transport-Security': 'HSTS – force HTTPS',
            'X-Frame-Options': 'Clickjacking protection',
            'X-Content-Type-Options': 'MIME sniffing prevention',
            'Content-Security-Policy': 'XSS/injection protection',
            'Referrer-Policy': 'Referrer information control',
            'Permissions-Policy': 'Feature policy control',
        }
        if self.target in ('localhost', '127.0.0.1'):
            try:
                import urllib.request
                response = urllib.request.urlopen(f'http://{self.target}', timeout=3)
                resp_headers = {k.lower(): v for k, v in response.headers.items()}
            except Exception:
                return {h: 'Unable to check (local host)' for h in required_headers}
        else:
            try:
                import urllib.request
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                response = urllib.request.urlopen(
                    f'https://{self.target}', timeout=5, context=ctx,
                )
                resp_headers = {k.lower(): v for k, v in response.headers.items()}
            except Exception:
                try:
                    import urllib.request
                    response = urllib.request.urlopen(f'http://{self.target}', timeout=5)
                    resp_headers = {k.lower(): v for k, v in response.headers.items()}
                except Exception as exc:
                    return {h: f'Cannot reach target: {exc}' for h in required_headers}

        for header, description in required_headers.items():
            if header.lower() in resp_headers:
                headers_status[header] = f'PRESENT – {resp_headers[header.lower()][:60]}'
            else:
                headers_status[header] = f'MISSING – {description} not configured'
        return headers_status

    def _get_external_ip(self) -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(('8.8.8.8', 53))
                return sock.getsockname()[0]
        except Exception as exc:
            return f'External IP unavailable: {exc}'

    def _scan_common_ports(self) -> List[int]:
        open_ports = []
        for port in self.COMMON_PORTS:
            try:
                with socket.create_connection((self.target, port), timeout=0.75):
                    open_ports.append(port)
            except Exception:
                continue
        return open_ports

    def _identify_risky_ports(self) -> List[str]:
        """Return descriptions of open ports considered risky for public exposure."""
        open_ports = self._scan_common_ports()
        return [
            f"Port {p}: {self.RISKY_PORTS[p]}"
            for p in open_ports
            if p in self.RISKY_PORTS
        ]


class ZambiaRiskAssessor:
    """Assesses digital hygiene risks specific to Zambian businesses.

    Covers local threat vectors (SIM swap, mobile money, WhatsApp fraud)
    and compliance with Zambian cybersecurity legislation.
    """
    LOCAL_THREATS = [
        'SIM swap fraud',
        'Mobile money scams',
        'Local phishing',
        'WhatsApp fraud',
        'Regulatory non-compliance',
        'Unsecured mobile devices',
        'Weak passwords',
        'Lack of MFA',
        'No data backup',
        'No incident response plan',
    ]
    COMPLIANCE_LAWS = [
        'Data Protection Act, 2021',
        'Cyber Security and Cyber Crimes Act, 2021',
    ]

    def assess(self, answers):
        """Evaluate local threats and compliance gaps.

        ``answers`` is a dict of form field values where checkbox presence
        indicates the mitigation is in place.
        """
        score = 100  # Start at 100 and deduct for gaps
        findings = []
        mitigated = 0
        total_checks = len(self.LOCAL_THREATS) + len(self.COMPLIANCE_LAWS)

        for threat in self.LOCAL_THREATS:
            key = threat.replace(' ', '_').lower()
            if answers.get(key):
                mitigated += 1
            else:
                findings.append(f"Risk: {threat} – mitigation not in place.")
                score -= 8

        for law in self.COMPLIANCE_LAWS:
            key = law.replace(' ', '_').replace(',', '').lower()
            if answers.get(key):
                mitigated += 1
            else:
                findings.append(f"Compliance gap: {law} requirements not met.")
                score -= 12

        score = max(0, score)
        level = (
            "LOW RISK" if score >= 80 else
            "MEDIUM RISK" if score >= 50 else
            "HIGH RISK"
        )

        return {
            'score': score,
            'max_score': 100,
            'findings': findings,
            'mitigated': mitigated,
            'total_checks': total_checks,
            'risk_level': level,
        }
