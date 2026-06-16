"""
Pre-Deployment Digital Hygiene Checker
======================================
Lets developers verify that a machine (dev workstation, CI runner, staging
server) satisfies baseline digital-hygiene requirements before code is
deployed to production.

Each check returns a ``CheckResult`` with a pass/fail verdict, severity,
and actionable remediation advice.  The aggregate ``DeploymentReadiness``
object provides a single **READY / NOT READY** gate that CI/CD pipelines
or developers can act on.

Usage
-----
    from src.security.deployment.checker import PreDeploymentChecker

    checker = PreDeploymentChecker()
    report  = checker.run_all()
    print(report.verdict)          # "READY" or "NOT READY"
    print(report.to_dict())        # full JSON-serialisable report
"""

import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.security.monitoring.checks import get_logging_hygiene
from src.security.siem.forwarder import WebhookForwarder, build_siem_event


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Result of a single pre-deployment check."""
    check_id: str
    name: str
    passed: bool
    severity: str          # CRITICAL, HIGH, MEDIUM, LOW
    details: str
    remediation: str = ''
    category: str = ''     # system, network, application, secrets, monitoring

    def to_dict(self) -> Dict[str, Any]:
        return {
            'check_id': self.check_id,
            'name': self.name,
            'passed': self.passed,
            'severity': self.severity,
            'details': self.details,
            'remediation': self.remediation,
            'category': self.category,
        }


@dataclass
class DeploymentReadiness:
    """Aggregate result for all pre-deployment checks."""
    checks: List[CheckResult] = field(default_factory=list)
    timestamp: str = ''
    hostname: str = ''
    os_info: str = ''

    def __post_init__(self):
        self.timestamp = self.timestamp or datetime.now().isoformat()
        self.hostname = self.hostname or socket.gethostname()
        self.os_info = self.os_info or f"{platform.system()} {platform.release()}"

    # ---- computed properties ----
    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def critical_failures(self) -> int:
        return sum(1 for c in self.checks if not c.passed and c.severity == 'CRITICAL')

    @property
    def verdict(self) -> str:
        """READY when 0 critical failures and <=2 non-critical failures."""
        if self.critical_failures > 0:
            return 'NOT READY'
        if self.failed > 2:
            return 'NOT READY'
        return 'READY'

    @property
    def verdict_colour(self) -> str:
        return 'success' if self.verdict == 'READY' else 'danger'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'verdict': self.verdict,
            'timestamp': self.timestamp,
            'hostname': self.hostname,
            'os_info': self.os_info,
            'summary': {
                'total': self.total,
                'passed': self.passed,
                'failed': self.failed,
                'critical_failures': self.critical_failures,
            },
            'checks': [c.to_dict() for c in self.checks],
        }


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------

class PreDeploymentChecker:
    """Run a battery of digital-hygiene checks on the current system.

    Checks cover five categories:
    * **system**      – OS patches, firewall, antivirus, disk encryption, inventory
    * **network**     – dangerous open ports, DNS resolution, HTTPS readiness
    * **application** – Python env, dependency vulnerabilities, debug flags
    * **secrets**     – env-var leaks, hard-coded credentials, .env exposure
    * **monitoring**  – event logging and log-forwarding/agent hygiene
    """

    def __init__(self, project_root: Optional[str] = None, siem_url: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.siem_url = siem_url

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_all(self) -> DeploymentReadiness:
        """Execute every check and return an aggregate report."""
        report = DeploymentReadiness()

        # System checks
        report.checks.append(self._check_os_updates())
        report.checks.append(self._check_firewall())
        report.checks.append(self._check_antivirus())
        report.checks.append(self._check_disk_encryption())
        # Inventory checks
        report.checks.append(self._check_software_inventory())
        report.checks.append(self._check_monitoring_hygiene())

        # Network checks
        report.checks.append(self._check_open_ports())
        report.checks.append(self._check_dns_resolution())
        report.checks.append(self._check_ssl_tools())

        # Application checks
        report.checks.append(self._check_python_version())
        report.checks.append(self._check_dependency_vulnerabilities())
        report.checks.append(self._check_debug_mode())

        # Secrets / credential hygiene checks
        report.checks.append(self._check_env_file_exposure())
        report.checks.append(self._check_hardcoded_secrets())
        report.checks.append(self._check_git_secrets())

        self._maybe_forward_siem(report)
        return report

    def _maybe_forward_siem(self, report: DeploymentReadiness) -> bool:
        """Optionally forward the aggregated report to a SIEM webhook."""
        forwarder = WebhookForwarder(self.siem_url)
        if not forwarder.url:
            return False

        event = build_siem_event(report.to_dict(), source='deployment_checker')
        return forwarder.send(event)

    # ------------------------------------------------------------------
    # SYSTEM checks
    # ------------------------------------------------------------------

    def _check_os_updates(self) -> CheckResult:
        """PDC-01: Verify OS patches are reasonably current.

        On Windows uses PowerShell to get the most recent hotfix date; tries
        multiple locale-aware date formats and falls back to a WSUS registry
        query.  Returns PASS if patched within 30 days, FAIL otherwise.
        """
        try:
            if platform.system() == 'Windows':
                # Ask PowerShell for the most recently installed hotfix,
                # formatted as a sortable ISO string to avoid locale differences.
                ps_cmd = (
                    r"$hf = Get-HotFix | Where-Object {$_.InstalledOn} | "
                    r"Sort-Object InstalledOn -Descending | Select-Object -First 1; "
                    r"if ($hf) { $hf.InstalledOn.ToString('yyyy-MM-dd') } else { '' }"
                )
                r = subprocess.run(
                    ['powershell', '-NonInteractive', '-Command', ps_cmd],
                    capture_output=True, text=True, timeout=20,
                )
                output = r.stdout.strip()
                if output and len(output) >= 10:
                    from datetime import datetime as _dt
                    try:
                        last = _dt.strptime(output[:10], '%Y-%m-%d')
                        days_ago = (datetime.now() - last).days
                        if days_ago <= 30:
                            return CheckResult('PDC-01', 'OS Updates', True, 'CRITICAL',
                                               f'Last patch installed {days_ago} day(s) ago ({output[:10]})',
                                               category='system')
                        return CheckResult('PDC-01', 'OS Updates', False, 'CRITICAL',
                                           f'Last patch was {days_ago} days ago – overdue',
                                           'Run Windows Update: Settings > Update & Security',
                                           'system')
                    except ValueError:
                        pass
                # Fallback: check Windows Update service state as a partial signal
                svc = subprocess.run(
                    ['sc', 'query', 'wuauserv'],
                    capture_output=True, text=True, timeout=8,
                )
                svc_running = 'RUNNING' in svc.stdout.upper()
                detail = ('Windows Update service is running but patch date could not be '
                          'determined – run Windows Update manually.'
                          if svc_running else
                          'Windows Update service is not running and patch date unknown.')
                return CheckResult('PDC-01', 'OS Updates', False, 'CRITICAL',
                                   detail,
                                   'Open Settings > Update & Security and check for updates',
                                   'system')
            else:
                r = subprocess.run(['apt', 'list', '--upgradable'],
                                   capture_output=True, text=True, timeout=15)
                upgradable = [ln for ln in r.stdout.splitlines() if 'upgradable' in ln.lower()]
                if len(upgradable) == 0:
                    return CheckResult('PDC-01', 'OS Updates', True, 'CRITICAL',
                                       'All packages up to date', category='system')
                return CheckResult('PDC-01', 'OS Updates', False, 'CRITICAL',
                                   f'{len(upgradable)} package(s) need updating',
                                   'Run: sudo apt update && sudo apt upgrade', 'system')
        except Exception as e:
            return CheckResult('PDC-01', 'OS Updates', False, 'CRITICAL',
                               f'Check failed: {e}',
                               'Manually verify OS is patched', 'system')

    def _check_firewall(self) -> CheckResult:
        """PDC-02: Verify host firewall is enabled."""
        try:
            if platform.system() == 'Windows':
                r = subprocess.run(
                    'netsh advfirewall show allprofiles state',
                    capture_output=True, text=True, timeout=10, shell=True,
                )
                on_count = r.stdout.lower().count('on')
                if on_count >= 3:
                    return CheckResult('PDC-02', 'Firewall', True, 'CRITICAL',
                                       'Windows Firewall enabled on all profiles',
                                       category='system')
                return CheckResult('PDC-02', 'Firewall', False, 'CRITICAL',
                                   f'Firewall not fully enabled ({on_count}/3 profiles)',
                                   'Run: netsh advfirewall set allprofiles state on', 'system')
            else:
                r = subprocess.run(['ufw', 'status'], capture_output=True, text=True, timeout=10)
                if 'active' in r.stdout.lower():
                    return CheckResult('PDC-02', 'Firewall', True, 'CRITICAL',
                                       'UFW firewall is active', category='system')
                return CheckResult('PDC-02', 'Firewall', False, 'CRITICAL',
                                   'UFW firewall is inactive',
                                   'Run: sudo ufw enable', 'system')
        except Exception as e:
            return CheckResult('PDC-02', 'Firewall', False, 'CRITICAL',
                               f'Check failed: {e}',
                               'Verify firewall manually', 'system')

    def _check_antivirus(self) -> CheckResult:
        """PDC-03: Detect running antivirus / Windows Defender."""
        try:
            if platform.system() == 'Windows':
                ps_av = (
                    'powershell -Command "Get-MpComputerStatus'
                    ' | Select-Object -ExpandProperty RealTimeProtectionEnabled"'
                )
                r = subprocess.run(
                    ps_av,
                    capture_output=True, text=True, timeout=10, shell=True,
                )
                if 'true' in r.stdout.strip().lower():
                    return CheckResult('PDC-03', 'Antivirus / Defender', True, 'HIGH',
                                       'Real-time protection is ON', category='system')
                return CheckResult('PDC-03', 'Antivirus / Defender', False, 'HIGH',
                                   'Real-time protection is OFF',
                                   'Enable Windows Defender real-time protection', 'system')
            else:
                for av in ['clamav', 'clamd', 'sophos']:
                    if shutil.which(av):
                        return CheckResult('PDC-03', 'Antivirus', True, 'HIGH',
                                           f'{av} detected', category='system')
                return CheckResult('PDC-03', 'Antivirus', False, 'HIGH',
                                   'No antivirus detected',
                                   'Install ClamAV: sudo apt install clamav', 'system')
        except Exception as e:
            return CheckResult('PDC-03', 'Antivirus', False, 'HIGH',
                               f'Check failed: {e}', 'Verify AV manually', 'system')

    def _check_disk_encryption(self) -> CheckResult:
        """PDC-04: Check if disk encryption is enabled."""
        try:
            if platform.system() == 'Windows':
                r = subprocess.run(
                    'manage-bde -status C:',
                    capture_output=True, text=True, timeout=10, shell=True,
                )
                if 'fully encrypted' in r.stdout.lower() or 'percentage encrypted: 100' in r.stdout.lower():
                    return CheckResult('PDC-04', 'Disk Encryption', True, 'MEDIUM',
                                       'BitLocker is fully enabled on C:', category='system')
                return CheckResult('PDC-04', 'Disk Encryption', False, 'MEDIUM',
                                   'BitLocker not fully enabled',
                                   'Enable BitLocker via Control Panel > BitLocker Drive Encryption', 'system')
            else:
                r = subprocess.run(['lsblk', '-o', 'NAME,TYPE'], capture_output=True, text=True, timeout=5)
                if 'crypt' in r.stdout:
                    return CheckResult('PDC-04', 'Disk Encryption', True, 'MEDIUM',
                                       'LUKS encryption detected', category='system')
                return CheckResult('PDC-04', 'Disk Encryption', False, 'MEDIUM',
                                   'No disk encryption detected',
                                   'Consider enabling LUKS encryption', 'system')
        except Exception as e:
            return CheckResult('PDC-04', 'Disk Encryption', False, 'MEDIUM',
                               f'Check failed: {e}', 'Verify disk encryption manually', 'system')

    def _check_software_inventory(self) -> CheckResult:
        """PDC-14: Produce a short software inventory summary for the host.

        On Windows this reads common registry uninstall keys; on Unix it lists
        installed packages where available. This check returns LOW severity and
        is informational for assessors.
        """
        try:
            if platform.system() == 'Windows':
                import winreg  # type: ignore[import]

                products = []
                for key_path in [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
                ]:
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:  # type: ignore[attr-defined]
                            for i in range(winreg.QueryInfoKey(key)[0]):  # type: ignore[attr-defined]
                                try:
                                    sk = winreg.EnumKey(key, i)  # type: ignore[attr-defined]
                                    with winreg.OpenKey(key, sk) as sub:  # type: ignore[attr-defined]
                                        try:
                                            name = winreg.QueryValueEx(  # type: ignore[attr-defined]
                                                sub, 'DisplayName')[0]
                                            products.append(name)
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                    except Exception:
                        pass

                if not products:
                    return CheckResult('PDC-14', 'Software Inventory', True, 'LOW',
                                       'No installed-program entries discovered (or access denied)',
                                       category='system')
                sample = ', '.join(sorted(set(products))[:8])
                return CheckResult('PDC-14', 'Software Inventory', True, 'LOW',
                                   f'Detected packages: {sample} (+more)',
                                   category='system')
            else:
                # Attempt dpkg or rpm list
                try:
                    r = subprocess.run(
                        ['dpkg-query', '-W', '-f', '${Package}\n'],
                        capture_output=True, text=True, timeout=10,
                    )
                    pkgs = r.stdout.splitlines()
                    sample = ', '.join(pkgs[:8]) if pkgs else 'none'
                    return CheckResult('PDC-14', 'Software Inventory', True, 'LOW',
                                       f'Detected packages: {sample}', category='system')
                except Exception:
                    return CheckResult('PDC-14', 'Software Inventory', True, 'LOW',
                                       'Unable to enumerate packages; check manually', category='system')
        except Exception as e:
            return CheckResult('PDC-14', 'Software Inventory', False, 'LOW',
                               f'Inventory check failed: {e}', 'Inspect installed software manually', 'system')

    def _check_monitoring_hygiene(self) -> CheckResult:
        """PDC-15: Check logging and monitoring hygiene on the host."""
        status = get_logging_hygiene()
        details = '; '.join(status.get('details', [])) or 'Monitoring status could not be determined'
        if status.get('passed'):
            return CheckResult('PDC-15', 'Monitoring Hygiene', True, status.get('severity', 'LOW'),
                               details, category='monitoring')

        remediation = 'Install or configure a log forwarder and ensure event logging is available.'
        if status.get('severity') == 'MEDIUM':
            remediation = 'Confirm Windows Event Log or syslog logging is active and forwarding agent is installed.'

        return CheckResult('PDC-15', 'Monitoring Hygiene', False, status.get('severity', 'MEDIUM'),
                           details, remediation, 'monitoring')

    # ------------------------------------------------------------------
    # NETWORK checks
    # ------------------------------------------------------------------

    def _check_open_ports(self) -> CheckResult:
        """PDC-05: Detect risky open ports on localhost."""
        risky_ports = {
            21: 'FTP', 23: 'Telnet', 445: 'SMB', 1433: 'MSSQL',
            3306: 'MySQL', 5432: 'PostgreSQL', 6379: 'Redis',
            27017: 'MongoDB',
        }
        open_found: List[str] = []
        for port, name in risky_ports.items():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.3)
                    if s.connect_ex(('127.0.0.1', port)) == 0:
                        open_found.append(f'{name}({port})')
            except Exception:
                pass

        if not open_found:
            return CheckResult('PDC-05', 'Open Ports', True, 'HIGH',
                               'No risky database/service ports exposed',
                               category='network')
        return CheckResult('PDC-05', 'Open Ports', False, 'HIGH',
                           f'Risky ports open: {", ".join(open_found)}',
                           'Bind services to 127.0.0.1 and restrict with firewall rules',
                           'network')

    def _check_dns_resolution(self) -> CheckResult:
        """PDC-06: Verify outbound DNS works (needed for package registries)."""
        try:
            socket.getaddrinfo('pypi.org', 443, socket.AF_INET)
            return CheckResult('PDC-06', 'DNS Resolution', True, 'MEDIUM',
                               'DNS resolves pypi.org correctly', category='network')
        except socket.gaierror:
            return CheckResult('PDC-06', 'DNS Resolution', False, 'MEDIUM',
                               'Cannot resolve pypi.org – DNS may be broken',
                               'Check /etc/resolv.conf or network settings', 'network')

    def _check_ssl_tools(self) -> CheckResult:
        """PDC-07: Ensure OpenSSL / TLS libraries are available."""
        import ssl
        ver = ssl.OPENSSL_VERSION
        if 'OpenSSL' in ver:
            return CheckResult('PDC-07', 'TLS / OpenSSL', True, 'MEDIUM',
                               f'{ver} available', category='network')
        return CheckResult('PDC-07', 'TLS / OpenSSL', False, 'MEDIUM',
                           f'Unexpected SSL lib: {ver}',
                           'Install or update OpenSSL', 'network')

    # ------------------------------------------------------------------
    # APPLICATION checks
    # ------------------------------------------------------------------

    def _check_python_version(self) -> CheckResult:
        """PDC-08: Python >= 3.8 required."""
        major, minor = sys.version_info[:2]
        if major >= 3 and minor >= 8:
            return CheckResult('PDC-08', 'Python Version', True, 'HIGH',
                               f'Python {major}.{minor} detected', category='application')
        return CheckResult('PDC-08', 'Python Version', False, 'HIGH',
                           f'Python {major}.{minor} is below minimum 3.8',
                           'Upgrade to Python 3.8+', 'application')

    def _check_dependency_vulnerabilities(self) -> CheckResult:
        """PDC-09: Run pip audit (if available) to find vulnerable packages."""
        try:
            r = subprocess.run(
                [sys.executable, '-m', 'pip', 'audit', '--desc'],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode == 0:
                return CheckResult('PDC-09', 'Dependency Vulnerabilities', True, 'CRITICAL',
                                   'No known vulnerabilities in installed packages',
                                   category='application')
            # pip-audit exits non-zero when vulnerabilities are found.
            # Count occurrences of 'name:' in stdout; fall back to stderr line count.
            vuln_count = r.stdout.lower().count('name:')
            if vuln_count == 0:
                output_lines = (r.stdout + r.stderr).splitlines()
                vuln_count = max(1, len([ln for ln in output_lines if ln.strip()]))
            return CheckResult('PDC-09', 'Dependency Vulnerabilities', False, 'CRITICAL',
                               f'{vuln_count} vulnerable package(s) found; run pip-audit for details',
                               'Run: pip install pip-audit && pip-audit --fix',
                               'application')
        except FileNotFoundError:
            return CheckResult('PDC-09', 'Dependency Vulnerabilities', True, 'CRITICAL',
                               'pip-audit not installed – skipped (install for full check)',
                               'Install pip-audit: pip install pip-audit', 'application')
        except Exception as e:
            return CheckResult('PDC-09', 'Dependency Vulnerabilities', False, 'CRITICAL',
                               f'Check failed: {e}',
                               'Run pip-audit manually', 'application')

    def _check_debug_mode(self) -> CheckResult:
        """PDC-10: Warn if DEBUG or FLASK_DEBUG is set to a truthy value."""
        debug_vars = ['DEBUG', 'FLASK_DEBUG', 'DJANGO_DEBUG']
        active = [v for v in debug_vars if os.getenv(v, '').lower() in ('1', 'true', 'yes')]
        if not active:
            return CheckResult('PDC-10', 'Debug Mode', True, 'HIGH',
                               'No debug environment variables set',
                               category='application')
        return CheckResult('PDC-10', 'Debug Mode', False, 'HIGH',
                           f'Debug enabled via: {", ".join(active)}',
                           'Unset debug vars before deploying: set DEBUG=false',
                           'application')

    # ------------------------------------------------------------------
    # SECRETS / CREDENTIAL checks
    # ------------------------------------------------------------------

    def _check_env_file_exposure(self) -> CheckResult:
        """PDC-11: Ensure .env is listed in .gitignore."""
        gitignore = self.project_root / '.gitignore'
        env_file = self.project_root / '.env'
        if not env_file.exists():
            return CheckResult('PDC-11', '.env File Exposure', True, 'HIGH',
                               'No .env file found in project root',
                               category='secrets')

        if gitignore.exists():
            content = gitignore.read_text(errors='ignore')
            if '.env' in content:
                return CheckResult('PDC-11', '.env File Exposure', True, 'HIGH',
                                   '.env is listed in .gitignore', category='secrets')
        return CheckResult('PDC-11', '.env File Exposure', False, 'HIGH',
                           '.env exists but is NOT in .gitignore – credentials may leak',
                           'Add ".env" to your .gitignore file immediately', 'secrets')

    def _check_hardcoded_secrets(self) -> CheckResult:
        """PDC-12: Scan Python source files for obvious hard-coded passwords/keys.

        Only flags lines where a quoted non-placeholder value is actually assigned —
        skips comment lines, empty-string assignments, and placeholder values like
        'your-secret-here'.  Also skips the security module itself (it contains
        the patterns as search strings) and test files.
        """
        import re

        # Regex: captures  key = "real_value"  or  key = 'real_value'
        # The value must be non-empty and not an obvious placeholder.
        _PAT = re.compile(
            r'^\s*(?:password|secret_key|api_key|aws_secret|private_key)\s*=\s*'
            r'["\']([^"\']{4,})["\']',
            re.IGNORECASE,
        )
        _PLACEHOLDER = re.compile(
            r'(?:your[-_]|example|placeholder|changeme|<|>|xxx|todo|insert)',
            re.IGNORECASE,
        )

        hits: List[str] = []
        src_dir = self.project_root / 'src'
        if not src_dir.exists():
            src_dir = self.project_root

        # Files to skip: security module patterns (meta), test fixtures
        skip_dirs = {'security', 'tests', '__pycache__'}

        for pyfile in src_dir.rglob('*.py'):
            # Skip security scanner source and test files
            parts = {p.lower() for p in pyfile.parts}
            if parts & skip_dirs:
                continue
            try:
                for lineno, line in enumerate(
                    pyfile.read_text(errors='ignore').splitlines(), 1
                ):
                    stripped = line.strip()
                    if stripped.startswith('#'):
                        continue  # comment line
                    m = _PAT.match(line)
                    if m:
                        value = m.group(1)
                        if not _PLACEHOLDER.search(value):
                            rel = pyfile.relative_to(self.project_root)
                            hits.append(f'{rel}:{lineno}')
                            break  # one hit per file is enough
            except Exception:
                pass

        if not hits:
            return CheckResult('PDC-12', 'Hard-coded Secrets', True, 'CRITICAL',
                               'No obvious hard-coded credentials found',
                               category='secrets')
        return CheckResult('PDC-12', 'Hard-coded Secrets', False, 'CRITICAL',
                           f'Potential secrets in: {"; ".join(hits[:5])}',
                           'Move credentials to environment variables or a secrets manager',
                           'secrets')

    def _check_git_secrets(self) -> CheckResult:
        """PDC-13: Check for sensitive files staged in git."""
        git_dir = self.project_root / '.git'
        if not git_dir.exists():
            return CheckResult('PDC-13', 'Git Secret Hygiene', True, 'MEDIUM',
                               'Not a git repository – check skipped',
                               category='secrets')
        try:
            r = subprocess.run(
                ['git', 'ls-files'],
                capture_output=True, text=True, timeout=10,
                cwd=str(self.project_root),
            )
            tracked = r.stdout.splitlines()
            bad_patterns = ['.env', 'id_rsa', 'id_ed25519', '.pem', '.key',
                            'credentials.json', 'service-account.json']
            # Exclude safe template/example files that intentionally live in the repo
            safe_suffixes = ('.example', '.sample', '.template', '.dist')
            found = [
                f for f in tracked
                if any(p in f.lower() for p in bad_patterns)
                and not any(f.lower().endswith(s) for s in safe_suffixes)
            ]
            if not found:
                return CheckResult('PDC-13', 'Git Secret Hygiene', True, 'MEDIUM',
                                   'No sensitive files tracked by git',
                                   category='secrets')
            return CheckResult('PDC-13', 'Git Secret Hygiene', False, 'MEDIUM',
                               f'Sensitive files in git: {", ".join(found[:5])}',
                               'Remove with git rm --cached and add to .gitignore',
                               'secrets')
        except Exception as e:
            return CheckResult('PDC-13', 'Git Secret Hygiene', False, 'MEDIUM',
                               f'Check failed: {e}', 'Run git ls-files manually',
                               'secrets')
