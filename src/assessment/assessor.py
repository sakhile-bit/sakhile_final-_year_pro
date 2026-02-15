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
        results["C02_antivirus"] = self._check_antivirus()
        results["C03_firewall"] = self._check_firewall()
        results["C04_password_policy"] = self._check_password_policy()
        results["C05_backups"] = self._check_backup_system()

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
        try:
            import subprocess

            result = subprocess.run(
                ['netsh', 'advfirewall', 'show', 'allprofiles', 'state'],
                capture_output=True, text=True, shell=True,
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
        try:
            import subprocess

            result = subprocess.run(
                ['net', 'accounts'],
                capture_output=True, text=True, shell=True,
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
