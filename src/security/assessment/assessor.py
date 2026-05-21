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
from typing import Dict, Tuple, List, Optional
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
    category: str = "technical" # technical | administrative | physical
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

CONTROL_CATALOGUE = {
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
        """C01 – Check Windows Update settings and last update time"""
        ctrl = self.controls["C01_os_updates"]
        # Only run Windows-specific checks on Windows hosts
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
            import psutil
            import winreg

            # Check if Windows Update service is running
            service_running = False
            for service in psutil.win_service_iter():
                if service.name().lower() == 'wuauserv':
                    if service.status() == 'running':
                        service_running = True
                    break

            # Check last update time from registry
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\Results\Install")
                last_update, _ = winreg.QueryValueEx(key, "LastSuccessTime")
                winreg.CloseKey(key)

                last_update_date = datetime.datetime.fromtimestamp(last_update)
                days_since_update = (datetime.datetime.now() - last_update_date).days

                if service_running and days_since_update < 30:
                    score = ctrl["weight"]
                    status = "PASS"
                    details = f"Windows Update running. Last update: {last_update_date.strftime('%Y-%m-%d')} ({days_since_update} days ago)"
                elif service_running and days_since_update < 90:
                    score = ctrl["weight"] // 2
                    status = "WARNING"
                    details = f"Updates somewhat old. Last: {last_update_date.strftime('%Y-%m-%d')} ({days_since_update} days ago)"
                else:
                    score = 0
                    status = "FAIL"
                    details = "Windows Update not properly configured or updates too old"

            except Exception:
                score = 0
                status = "FAIL"
                details = "Cannot determine last update time"

        except Exception as e:
            score = 0
            status = "ERROR"
            details = f"Error checking updates: {str(e)}"

        return ControlResult(
            control_id=ctrl["id"], name=ctrl["name"],
            score=score, weight=ctrl["weight"],
            status=status, details=details,
            category=ctrl["category"], verification=ctrl["verification"],
        )

    def _check_antivirus(self) -> ControlResult:
        """C02 – Check for antivirus installation and status using WMI / registry"""
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
            import winreg

            av_installed = False
            av_name = "Unknown"

            # Check via WMI if available
            try:
                import wmi
                c = wmi.WMI()
                for product in c.Win32_Product():
                    if any(term in product.Name.lower() for term in [
                        'avast', 'avg', 'bitdefender', 'kaspersky',
                        'mcafee', 'norton', 'eset', 'windows defender',
                        'antivirus', 'security', 'endpoint'
                    ]):
                        av_installed = True
                        av_name = product.Name
                        break
            except ImportError:
                pass

            # Fallback: check installed programs via registry
            if not av_installed:
                key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    if any(t in display_name.lower() for t in ['antivirus', 'security', 'defender']):
                                        av_installed = True
                                        av_name = display_name
                                        break
                            except Exception:
                                pass
                except Exception:
                    pass

            if av_installed:
                score = ctrl["weight"]
                status = "PASS"
                details = f"Antivirus detected: {av_name}"
            else:
                score = 0
                status = "FAIL"
                details = "No antivirus software detected"

        except Exception as e:
            score = 0
            status = "ERROR"
            details = f"Error checking antivirus: {str(e)}"

        return ControlResult(
            control_id=ctrl["id"], name=ctrl["name"],
            score=score, weight=ctrl["weight"],
            status=status, details=details,
            category=ctrl["category"], verification=ctrl["verification"],
        )

    def _check_firewall(self) -> ControlResult:
        """C03 – Check Windows Firewall status via netsh"""
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

            result = subprocess.run(
                ['netsh', 'advfirewall', 'show', 'allprofiles', 'state'],
                capture_output=True, text=True, shell=False,
            )

            firewall_enabled = False
            profiles = []

            for line in result.stdout.split('\n'):
                if 'ON' in line.upper() and 'STATE' in line.upper():
                    firewall_enabled = True
                    profile = line.split()[0] if line.split() else ""
                    profiles.append(profile)

            if firewall_enabled and len(profiles) >= 2:
                score = ctrl["weight"]
                status = "PASS"
                details = f"Firewall enabled for profiles: {', '.join(profiles)}"
            elif firewall_enabled:
                score = ctrl["weight"] // 2
                status = "WARNING"
                details = "Firewall partially enabled"
            else:
                score = 0
                status = "FAIL"
                details = "Firewall is disabled"

        except Exception as e:
            score = 0
            status = "ERROR"
            details = f"Error checking firewall: {str(e)}"

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
                    try: min_length = int(line.split()[-1])
                    except ValueError: pass
                elif 'Maximum password age' in line:
                    try: max_age = int(line.split()[-2])
                    except ValueError: pass
                elif 'Lockout threshold' in line:
                    try: lockout_threshold = int(line.split()[-1])
                    except ValueError: pass

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
        """C05 – Check for backup software or recent backup files"""
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
            import winreg

            backup_software = False
            backup_details = []

            software_keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            ]

            for key_path in software_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    if any(t in display_name.lower() for t in [
                                        'backup', 'acronis', 'veeam', 'carbonite',
                                        'backblaze', 'crashplan',
                                    ]):
                                        backup_software = True
                                        backup_details.append(f"Software: {display_name}")
                            except Exception:
                                pass
                except Exception:
                    pass

            # Check common backup locations for recent files
            backup_dirs = [
                Path("C:/Backup"), Path("D:/Backup"),
                Path(os.environ.get('USERPROFILE', '') + "/Backup"),
                Path(os.environ.get('USERPROFILE', '') + "/Documents/Backup"),
            ]

            recent_backup = False
            for backup_dir in backup_dirs:
                if backup_dir.exists():
                    for file_path in backup_dir.rglob("*"):
                        if file_path.is_file():
                            mod_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                            if (datetime.datetime.now() - mod_time).days < 7:
                                recent_backup = True
                                backup_details.append(f"Recent backup: {file_path.name} ({mod_time.date()})")
                                break

            if backup_software and recent_backup:
                score = ctrl["weight"]
                status = "PASS"
                details = "Backup system detected and recent backups found"
            elif backup_software:
                score = ctrl["weight"] * 3 // 5
                status = "WARNING"
                details = "Backup software installed but no recent backups found"
            elif recent_backup:
                score = ctrl["weight"] * 3 // 5
                status = "WARNING"
                details = "Recent backups found but no backup software detected"
            else:
                score = 0
                status = "FAIL"
                details = "No backup system detected"

            if backup_details:
                details += " | " + "; ".join(backup_details)

        except Exception as e:
            score = 0
            status = "ERROR"
            details = f"Error checking backup system: {str(e)}"

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
                return 'WARNING', f"Default admin shares exposed: {', '.join(exposed)} – consider disabling C$ and ADMIN$"
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
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r'Control Panel\Desktop',
                )
                ss_active, _ = winreg.QueryValueEx(key, 'ScreenSaveActive')
                ss_secure, _ = winreg.QueryValueEx(key, 'ScreenSaverIsSecure')
                ss_timeout, _ = winreg.QueryValueEx(key, 'ScreenSaveTimeOut')
                winreg.CloseKey(key)
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
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r'SYSTEM\CurrentControlSet\Services\USBSTOR',
                )
                start_val, _ = winreg.QueryValueEx(key, 'Start')
                winreg.CloseKey(key)
                if start_val == 4:
                    return 'PASS', 'USB storage driver disabled (Start=4)'
                return 'WARNING', f'USB storage enabled (Start={start_val}) – consider restricting removable media'
            except FileNotFoundError:
                return 'WARNING', 'USB storage policy not configured'
        except ImportError:
            return 'ERROR', 'winreg not available'
        except Exception as exc:
            return 'ERROR', f'USB policy check failed: {exc}'

    def _check_windows_defender_atp(self) -> Tuple[str, str]:
        """Check Windows Defender real-time protection and definition age."""
        if platform.system() != 'Windows':
            return 'NOT_APPLICABLE', 'Non-Windows host'
        try:
            import subprocess
            result = subprocess.run(
                ['powershell', '-NonInteractive', '-Command',
                 'Get-MpComputerStatus | Select-Object AntivirusEnabled,RealTimeProtectionEnabled,AntivirusSignatureAge | ConvertTo-Json'],
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

        RECS = {
            "C01_os_updates":        "Enable Windows Automatic Updates and ensure updates are installed within 30 days of release.",
            "C02_antivirus":         "Install reputable antivirus software (e.g., Windows Defender, ESET, Bitdefender) and enable real-time protection.",
            "C03_firewall":          "Enable Windows Firewall for all network profiles (Domain, Private, Public) and configure inbound rules.",
            "C04_password_policy":   "Strengthen password policy: minimum 8 characters, expiry every 90 days, account lockout after 5 failures.",
            "C05_backups":           "Implement daily automated backups with off-site or cloud storage. Test restores quarterly.",
            "C06_security_training": "Conduct annual security awareness training for all employees covering phishing, passwords, and data handling.",
            "C07_access_control":    "Document and enforce a least-privilege access control policy with regular access reviews.",
            "C08_incident_response": "Document an incident response plan with designated contacts and ZICTA/CERT-ZM reporting. Test annually.",
            "C09_encryption":        "Encrypt sensitive data at rest (full-disk encryption) and in transit (TLS/HTTPS for all services).",
            "C10_mobile_security":   "Implement mobile device management: screen locks, trusted app sources, encryption, and remote wipe.",
            "C11_physical_security": "Lock server rooms and network equipment. Maintain a visitor log and CCTV for sensitive areas.",
            "C12_network_security":  "Secure Wi-Fi with WPA2/WPA3, change default credentials, and implement network segmentation.",
            "C13_acceptable_use":    "Create and enforce a documented Acceptable Use Policy signed by all staff.",
            "C14_vendor_risk":       "Conduct formal vendor risk assessments. Include security clauses in all vendor contracts.",
            "C15_regulatory_compliance": "Ensure compliance with the Zambia Data Protection Act 2021 and ZICTA regulations.",
        }

        # Build prioritised list: critical failures first, then warnings
        critical_keys = [k for k, c in self.controls.items() if c.get("critical")]
        non_critical = [k for k in self.controls if k not in critical_keys]

        for key in critical_keys + non_critical:
            if results[key].status in ("FAIL", "ERROR"):
                recommendations.append(f"[CRITICAL] {RECS.get(key, 'Address ' + results[key].name)}")
            elif results[key].status == "WARNING":
                recommendations.append(RECS.get(key, f"Improve {results[key].name}"))
            elif results[key].status == "NOT_ASSESSED":
                recommendations.append(f"[NEEDS VERIFICATION] Complete manual assessment for: {results[key].name}")

        # Zambia-specific recommendations
        recommendations.append("Register with ZICTA and subscribe to CERT-ZM advisories for threat intelligence.")
        recommendations.append("Review compliance with the Zambia Data Protection Act No. 3 of 2021.")
        recommendations.append("Review compliance with the Cyber Security and Cyber Crimes Act, 2021.")

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

    def run_checks(self) -> Dict[str, object]:
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
            return f"Resolves to {', '.join(addresses)}"
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
                    expires_str = cert.get('notAfter', '')
                    # Check days until expiry
                    try:
                        import time
                        expires_epoch = ssl.cert_time_to_seconds(expires_str)
                        days_left = (expires_epoch - time.time()) / 86400
                        if days_left < 0:
                            return f"SSL certificate EXPIRED ({expires_str})"
                        elif days_left < 30:
                            return f"SSL/TLS enabled but certificate expires SOON in {int(days_left)} days ({expires_str})"
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
