#!/usr/bin/env python3
"""
Zambia Digital Hygiene Assessment Tool
Automated assessment script for SME cybersecurity certification
Version: 1.0
Author: [Your Name]
"""

import os
import sys
import subprocess
import json
import platform
import datetime
import winreg  # Windows registry access
import smtplib  # For email notifications
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import socket
import psutil  # You'll need to install: pip install psutil
import wmi  # You'll need to install: pip install wmi

class DigitalHygieneAssessor:
    def __init__(self, business_name="", business_id=""):
        self.business_name = business_name
        self.business_id = business_id
        self.results = {
            "business_info": {
                "name": business_name,
                "id": business_id,
                "assessment_date": datetime.datetime.now().isoformat(),
                "system": platform.system(),
                "system_version": platform.version()
            },
            "controls": {},
            "score": 0,
            "total_possible": 50,
            "certification_level": "Not Certified",
            "recommendations": []
        }
        
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
    
    def check_windows_updates(self):
        """Check Windows Update settings and last update time"""
        try:
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
        
        self.results["controls"]["os_updates"] = {
            "score": score,
            "status": status,
            "details": details,
            "weight": self.controls["os_updates"]["weight"]
        }
        return score
    
    def check_antivirus(self):
        """Check for antivirus installation and status using WMI"""
        try:
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
            av_enabled = False
            av_name = "Unknown"
            
            try:
                for av in c.Win32_ComputerSystem():
                    # This is a simplified check
                    pass
                
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
        
        self.results["controls"]["antivirus"] = {
            "score": score,
            "status": status,
            "details": details,
            "weight": self.controls["antivirus"]["weight"]
        }
        return score
    
    def check_firewall(self):
        """Check Windows Firewall status"""
        try:
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
        
        self.results["controls"]["firewall"] = {
            "score": score,
            "status": status,
            "details": details,
            "weight": self.controls["firewall"]["weight"]
        }
        return score
    
    def check_password_policy(self):
        """Check password policy settings"""
        try:
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
        
        self.results["controls"]["password_policy"] = {
            "score": score,
            "status": status,
            "details": details,
            "weight": self.controls["password_policy"]["weight"]
        }
        return score
    
    def check_backup_system(self):
        """Check for backup software or recent backup files"""
        try:
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
        
        self.results["controls"]["backup_system"] = {
            "score": score,
            "status": status,
            "details": details,
            "weight": self.controls["backup_system"]["weight"]
        }
        return score
    
    def run_assessment(self):
        """Run all assessments"""
        print("=" * 60)
        print("ZAMBIA DIGITAL HYGIENE ASSESSMENT TOOL")
        print("=" * 60)
        
        print(f"\nAssessing: {self.business_name or 'Unknown Business'}")
        print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"System: {platform.system()} {platform.version()}")
        print("\n" + "=" * 60)
        
        # Run individual checks
        total_score = 0
        
        print("\n1. Checking Operating System Updates...")
        total_score += self.check_windows_updates()
        
        print("2. Checking Antivirus Protection...")
        total_score += self.check_antivirus()
        
        print("3. Checking Firewall Configuration...")
        total_score += self.check_firewall()
        
        print("4. Checking Password Policy...")
        total_score += self.check_password_policy()
        
        print("5. Checking Backup System...")
        total_score += self.check_backup_system()
        
        # Calculate overall score
        self.results["score"] = total_score
        percentage = (total_score / self.results["total_possible"]) * 100
        
        # Determine certification level
        if percentage >= 80:
            level = "GOLD"
        elif percentage >= 60:
            level = "SILVER"
        elif percentage >= 40:
            level = "BRONZE"
        else:
            level = "NOT CERTIFIED"
        
        self.results["certification_level"] = level
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self.results
    
    def _generate_recommendations(self):
        """Generate recommendations based on assessment results"""
        recommendations = []
        
        # OS Updates recommendations
        os_result = self.results["controls"].get("os_updates", {})
        if os_result.get("status") in ["FAIL", "WARNING"]:
            recommendations.append("Enable Windows Automatic Updates and ensure updates are installed regularly")
        
        # Antivirus recommendations
        av_result = self.results["controls"].get("antivirus", {})
        if av_result.get("status") in ["FAIL"]:
            recommendations.append("Install reputable antivirus software and keep it updated")
        
        # Firewall recommendations
        fw_result = self.results["controls"].get("firewall", {})
        if fw_result.get("status") in ["FAIL", "WARNING"]:
            recommendations.append("Enable Windows Firewall for all network profiles")
        
        # Password policy recommendations
        pw_result = self.results["controls"].get("password_policy", {})
        if pw_result.get("score", 0) < 8:
            recommendations.append("Strengthen password policy: Minimum 8 characters, expiry every 90 days, account lockout after 5 failures")
        
        # Backup recommendations
        backup_result = self.results["controls"].get("backup_system", {})
        if backup_result.get("status") in ["FAIL", "WARNING"]:
            recommendations.append("Implement regular backup system with off-site storage")
        
        self.results["recommendations"] = recommendations
    
    def display_results(self):
        """Display assessment results in console"""
        print("\n" + "=" * 60)
        print("ASSESSMENT RESULTS")
        print("=" * 60)
        
        for control_id, control_info in self.results["controls"].items():
            control_name = self.controls[control_id]["name"]
            status = control_info["status"]
            score = control_info["score"]
            max_score = control_info["weight"]
            
            status_symbol = {
                "PASS": "✓",
                "WARNING": "⚠",
                "FAIL": "✗",
                "ERROR": "!"
            }.get(status, "?")
            
            print(f"\n{status_symbol} {control_name}: {score}/{max_score} - {status}")
            print(f"   Details: {control_info['details']}")
        
        print("\n" + "=" * 60)
        print(f"\nOVERALL SCORE: {self.results['score']}/{self.results['total_possible']}")
        print(f"CERTIFICATION LEVEL: {self.results['certification_level']}")
        
        if self.results["recommendations"]:
            print("\nRECOMMENDATIONS:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "=" * 60)
    
    def save_report(self, filename=None):
        """Save assessment report to JSON file"""
        if filename is None:
            filename = f"digital_hygiene_assessment_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nReport saved to: {filename}")
        return filename
    
    def generate_certificate(self):
        """Generate a simple text certificate"""
        if self.results["certification_level"] == "NOT CERTIFIED":
            print("\nBusiness does not qualify for certification")
            return None
        
        cert_text = f"""
{'=' * 60}
         ZAMBIA DIGITAL HYGIENE CERTIFICATE
{'=' * 60}

This certifies that:

{self.business_name or 'Business Name Not Provided'}

has achieved

{self.results['certification_level']} LEVEL CERTIFICATION

in the Zambia Digital Hygiene Program

Assessment Date: {self.results['business_info']['assessment_date'][:10]}
Score: {self.results['score']}/{self.results['total_possible']}

Certificate ID: ZDH-{datetime.datetime.now().strftime('%Y%m')}-{self.business_id or '0000'}

This certification is valid for one year from the date of issue.

{'=' * 60}
        """
        
        cert_filename = f"certificate_{self.business_id or 'unknown'}_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        with open(cert_filename, 'w') as f:
            f.write(cert_text)
        
        print(f"\nCertificate generated: {cert_filename}")
        return cert_text

def main():
    """Main function"""
    print("Zambia Digital Hygiene Certification Program")
    print("Automated Assessment Tool")
    print("\nThis tool assesses your business's cybersecurity hygiene.")
    print("Note: This tool requires administrator privileges for some checks.")
    print("\n" + "=" * 60)
    
    # Get business information
    business_name = input("Enter business name: ").strip()
    business_id = input("Enter business ID/registration number: ").strip()
    
    # Create assessor
    assessor = DigitalHygieneAssessor(business_name, business_id)
    
    # Run assessment
    print("\nStarting assessment...")
    results = assessor.run_assessment()
    
    # Display results
    assessor.display_results()
    
    # Save report
    report_file = assessor.save_report()
    
    # Generate certificate if qualified
    if results["certification_level"] != "NOT CERTIFIED":
        certificate = assessor.generate_certificate()
        if certificate:
            print("\n" + certificate)
    
    # Offer to save detailed report
    save_csv = input("\nSave detailed report as CSV? (y/n): ").lower()
    if save_csv == 'y':
        save_csv_report(assessor)
    
    print("\nAssessment complete!")
    print(f"\nNext steps:")
    print(f"1. Review the recommendations above")
    print(f"2. Implement improvements")
    print(f"3. Contact Zambia Digital Hygiene Program for formal certification")
    print(f"4. Schedule follow-up assessment in 30 days")

def save_csv_report(assessor):
    """Save detailed report as CSV"""
    import csv
    
    filename = f"detailed_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['Zambia Digital Hygiene Assessment Report'])
        writer.writerow(['Business Name', assessor.business_name])
        writer.writerow(['Business ID', assessor.business_id])
        writer.writerow(['Assessment Date', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])
        
        # Write control results
        writer.writerow(['Control', 'Status', 'Score', 'Max Score', 'Details'])
        for control_id, control_info in assessor.results["controls"].items():
            control_name = assessor.controls[control_id]["name"]
            writer.writerow([
                control_name,
                control_info["status"],
                control_info["score"],
                control_info["weight"],
                control_info["details"]
            ])
        
        writer.writerow([])
        writer.writerow(['Total Score', assessor.results["score"]])
        writer.writerow(['Certification Level', assessor.results["certification_level"]])
        writer.writerow([])
        
        # Write recommendations
        writer.writerow(['Recommendations'])
        for i, rec in enumerate(assessor.results["recommendations"], 1):
            writer.writerow([f"{i}. {rec}"])
    
    print(f"Detailed report saved as: {filename}")

def check_dependencies():
    """Check if required Python packages are installed"""
    missing_packages = []
    
    try:
        import psutil
    except ImportError:
        missing_packages.append("psutil")
    
    try:
        import wmi
    except ImportError:
        missing_packages.append("wmi")
    
    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

if __name__ == "__main__":
    # Check if running on Windows
    if platform.system() != "Windows":
        print("ERROR: This tool is designed for Windows systems only.")
        print("For Linux/macOS, please use the manual assessment guide.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\nPlease install missing dependencies and run again.")
        sys.exit(1)
    
    # Check for admin privileges
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    
    if not is_admin:
        print("\nWARNING: Some checks require administrator privileges.")
        print("For best results, run this tool as Administrator.")
        print("\nContinue anyway? (y/n): ", end="")
        response = input().lower()
        if response != 'y':
            print("Please run as Administrator and try again.")
            sys.exit(0)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAssessment cancelled by user.")
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {str(e)}")
        print("Please ensure all dependencies are installed.")