"""
Assessment Module
Core assessment logic for digital hygiene controls
"""

import platform
import datetime
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional
from pathlib import Path

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


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


@dataclass
class ControlResult:
    """Result of a single control assessment"""
    name: str
    score: int
    weight: int
    status: str  # PASS, WARNING, FAIL, ERROR
    details: str


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


class DigitalHygieneAssessor:
    """Main assessment class for digital hygiene controls"""

    def __init__(self, business_info: BusinessInfo):
        self.business_info = business_info
        self.logger = logger

        # Control definitions with weights
        self.controls = {
            "os_updates": {
                "name": "Operating System Updates",
                "weight": 10,
                "description": "Checks if Windows updates are enabled and current"
            },
            "antivirus": {
                "name": "Antivirus Protection",
                "weight": 15,
                "description": "Verifies antivirus installation and status"
            },
            "firewall": {
                "name": "Firewall Configuration",
                "weight": 10,
                "description": "Checks Windows Firewall status"
            },
            "password_policy": {
                "name": "Password Policy",
                "weight": 10,
                "description": "Validates password policy settings"
            },
            "backup_system": {
                "name": "Backup System",
                "weight": 5,
                "description": "Checks for backup software or recent backups"
            }
        }

    def run_assessment(self) -> AssessmentResults:
        """Run complete assessment"""
        self.logger.info(f"Starting assessment for {self.business_info.name}")

        results = {}

        # Run individual control checks
        results["os_updates"] = self._check_os_updates()
        results["antivirus"] = self._check_antivirus()
        results["firewall"] = self._check_firewall()
        results["password_policy"] = self._check_password_policy()
        results["backup_system"] = self._check_backup_system()

        # Calculate total score
        total_score = sum(control.score for control in results.values())
        total_possible = sum(control.weight for control in results.values())

        # Determine certification level
        percentage = (total_score / total_possible) * 100
        if percentage >= 80:
            level = "GOLD"
        elif percentage >= 60:
            level = "SILVER"
        elif percentage >= 40:
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
            assessment_date=datetime.datetime.now()
        )

        self.logger.info(f"Assessment completed: {total_score}/{total_possible} - {level}")
        return assessment_results

    def _check_os_updates(self) -> ControlResult:
        """Check Windows Update settings and last update time"""
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

                # Calculate days since last update
                last_update_date = datetime.datetime.fromtimestamp(last_update)
                days_since_update = (datetime.datetime.now() - last_update_date).days

                # Determine score
                if service_running and days_since_update < 30:
                    score = 10
                    status = "PASS"
                    details = f"Windows Update service is running. Last update: {last_update_date.strftime('%Y-%m-%d')} ({days_since_update} days ago)"
                elif service_running and days_since_update < 90:
                    score = 5
                    status = "WARNING"
                    details = f"Updates are somewhat old. Last update: {last_update_date.strftime('%Y-%m-%d')} ({days_since_update} days ago)"
                else:
                    score = 0
                    status = "FAIL"
                    details = "Windows Update not properly configured or updates too old"

            except:
                score = 0
                status = "FAIL"
                details = "Cannot determine last update time"

        except Exception as e:
            score = 0
            status = "ERROR"
            details = f"Error checking updates: {str(e)}"

        return ControlResult(
            name=self.controls["os_updates"]["name"],
            score=score,
            weight=self.controls["os_updates"]["weight"],
            status=status,
            details=details
        )

    def _check_antivirus(self) -> ControlResult:
        """Check for antivirus installation and status using WMI"""
        try:
            import wmi
            import winreg

            c = wmi.WMI()
            antivirus_products = []

            # Query WMI for antivirus products
            for product in c.Win32_Product():
                if any(term in product.Name.lower() for term in ['avast', 'avg', 'bitdefender', 'kaspersky',
                                                                 'mcafee', 'norton', 'eset', 'windows defender',
                                                                 'antivirus', 'security', 'endpoint']):
                    antivirus_products.append({
                        "name": product.Name,
                        "version": product.Version,
                        "installed": product.InstallDate
                    })

            # Also check Windows Security Center
            av_installed = False
            av_name = "Unknown"

            try:
                # Check via registry
                key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    if any(term in display_name.lower() for term in ['antivirus', 'security', 'defender']):
                                        av_installed = True
                                        av_name = display_name
                                except:
                                    pass
                        except:
                            pass
            except:
                pass

            # Determine score
            if av_installed:
                score = 15
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
            name=self.controls["antivirus"]["name"],
            score=score,
            weight=self.controls["antivirus"]["weight"],
            status=status,
            details=details
        )

    def _check_firewall(self) -> ControlResult:
        """Check Windows Firewall status"""
        try:
            import subprocess

            # Use netsh to check firewall status
            result = subprocess.run(
                ['netsh', 'advfirewall', 'show', 'allprofiles', 'state'],
                capture_output=True,
                text=True,
                shell=True
            )

            firewall_enabled = False
            profiles = []

            for line in result.stdout.split('\n'):
                if 'ON' in line.upper() and 'STATE' in line.upper():
                    firewall_enabled = True
                    profile = line.split()[0] if line.split() else ""
                    profiles.append(profile)

            if firewall_enabled and len(profiles) >= 2:  # At least 2 profiles enabled
                score = 10
                status = "PASS"
                details = f"Firewall enabled for profiles: {', '.join(profiles)}"
            elif firewall_enabled:
                score = 5
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
            name=self.controls["firewall"]["name"],
            score=score,
            weight=self.controls["firewall"]["weight"],
            status=status,
            details=details
        )

    def _check_password_policy(self) -> ControlResult:
        """Check password policy settings"""
        try:
            import subprocess

            # Check password policy via net accounts
            result = subprocess.run(
                ['net', 'accounts'],
                capture_output=True,
                text=True,
                shell=True
            )

            min_length = 0
            max_age = 0
            lockout_threshold = 0

            for line in result.stdout.split('\n'):
                if 'Minimum password length' in line:
                    try:
                        min_length = int(line.split()[-1])
                    except:
                        min_length = 0
                elif 'Maximum password age' in line:
                    try:
                        max_age = int(line.split()[-2])
                    except:
                        max_age = 0
                elif 'Lockout threshold' in line:
                    try:
                        lockout_threshold = int(line.split()[-1])
                    except:
                        lockout_threshold = 0

            # Calculate score based on policy strength
            score = 0
            details_parts = []

            if min_length >= 8:
                score += 3
                details_parts.append(f"Password length: {min_length} chars")
            else:
                details_parts.append(f"Password length too short: {min_length} chars")

            if max_age <= 90 and max_age > 0:
                score += 3
                details_parts.append(f"Password expires: {max_age} days")
            elif max_age == 0:
                details_parts.append("Passwords never expire (NOT RECOMMENDED)")
            else:
                details_parts.append(f"Password expiry too long: {max_age} days")

            if lockout_threshold > 0:
                score += 4
                details_parts.append(f"Account lockout after {lockout_threshold} failures")
            else:
                details_parts.append("No account lockout policy")

            # Determine status
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
            name=self.controls["password_policy"]["name"],
            score=score,
            weight=self.controls["password_policy"]["weight"],
            status=status,
            details=details
        )

    def _check_backup_system(self) -> ControlResult:
        """Check for backup software or recent backup files"""
        try:
            import os
            import winreg

            backup_software = False
            backup_files = False
            backup_details = []

            # Check for common backup software in registry
            software_keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]

            for key_path in software_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        if any(term in display_name.lower() for term in
                                               ['backup', 'acronis', 'veeam', 'carbonite',
                                                'backblaze', 'crashplan', 'time machine']):
                                            backup_software = True
                                            backup_details.append(f"Software: {display_name}")
                                    except:
                                        pass
                            except:
                                pass
                except:
                    pass

            # Check common backup locations for recent files
            backup_dirs = [
                Path("C:/Backup"),
                Path("D:/Backup"),
                Path(os.environ.get('USERPROFILE', '') + "/Backup"),
                Path(os.environ.get('USERPROFILE', '') + "/Documents/Backup")
            ]

            recent_backup = False
            for backup_dir in backup_dirs:
                if backup_dir.exists():
                    # Look for files modified in last 7 days
                    for file_path in backup_dir.rglob("*"):
                        if file_path.is_file():
                            mod_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                            if (datetime.datetime.now() - mod_time).days < 7:
                                recent_backup = True
                                backup_details.append(f"Recent backup: {file_path.name} ({mod_time.date()})")
                                break

            # Determine score
            if backup_software and recent_backup:
                score = 5
                status = "PASS"
                details = "Backup system detected and recent backups found"
            elif backup_software:
                score = 3
                status = "WARNING"
                details = "Backup software installed but no recent backups found"
            elif recent_backup:
                score = 3
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
            name=self.controls["backup_system"]["name"],
            score=score,
            weight=self.controls["backup_system"]["weight"],
            status=status,
            details=details
        )

    def _generate_recommendations(self, results: Dict[str, ControlResult]) -> List[str]:
        """Generate recommendations based on assessment results"""
        recommendations = []

        # OS Updates recommendations
        if results["os_updates"].status in ["FAIL", "WARNING"]:
            recommendations.append("Enable Windows Automatic Updates and ensure updates are installed regularly")

        # Antivirus recommendations
        if results["antivirus"].status in ["FAIL"]:
            recommendations.append("Install reputable antivirus software and keep it updated")

        # Firewall recommendations
        if results["firewall"].status in ["FAIL", "WARNING"]:
            recommendations.append("Enable Windows Firewall for all network profiles")

        # Password policy recommendations
        if results["password_policy"].score < 8:
            recommendations.append("Strengthen password policy: Minimum 8 characters, expiry every 90 days, account lockout after 5 failures")

        # Backup recommendations
        if results["backup_system"].status in ["FAIL", "WARNING"]:
            recommendations.append("Implement regular backup system with off-site storage")

        return recommendations


class ZambiaRiskAssessor:
    """Assesses digital hygiene risks specific to Zambian businesses."""
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
        score = 0
        findings = []
        for threat in self.LOCAL_THREATS:
            if not answers.get(threat.replace(' ', '_').lower(), False):
                findings.append(f"Risk: {threat} detected.")
                score -= 10
        for law in self.COMPLIANCE_LAWS:
            if not answers.get(law.replace(' ', '_').lower(), False):
                findings.append(f"Compliance gap: {law} not met.")
                score -= 15
        return {'score': score, 'findings': findings}
