"""
Unit tests for the pre-deployment digital hygiene checker
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from src.security.deployment.checker import (
    CheckResult,
    DeploymentReadiness,
    PreDeploymentChecker,
)


# ---------------------------------------------------------------
# CheckResult tests
# ---------------------------------------------------------------

class TestCheckResult:
    def test_creation(self):
        cr = CheckResult(
            check_id='PDC-01', name='OS Updates', passed=True,
            severity='CRITICAL', details='All good', category='system',
        )
        assert cr.passed is True
        assert cr.severity == 'CRITICAL'

    def test_to_dict(self):
        cr = CheckResult(
            check_id='PDC-02', name='Firewall', passed=False,
            severity='CRITICAL', details='Off',
            remediation='Turn it on', category='system',
        )
        d = cr.to_dict()
        assert d['check_id'] == 'PDC-02'
        assert d['passed'] is False
        assert d['remediation'] == 'Turn it on'


# ---------------------------------------------------------------
# DeploymentReadiness tests
# ---------------------------------------------------------------

class TestDeploymentReadiness:
    def test_all_pass_is_ready(self):
        report = DeploymentReadiness(checks=[
            CheckResult('A', 'A', True, 'CRITICAL', 'ok', category='system'),
            CheckResult('B', 'B', True, 'HIGH', 'ok', category='network'),
        ])
        assert report.verdict == 'READY'
        assert report.passed == 2
        assert report.failed == 0

    def test_critical_failure_means_not_ready(self):
        report = DeploymentReadiness(checks=[
            CheckResult('A', 'A', False, 'CRITICAL', 'bad', category='system'),
            CheckResult('B', 'B', True, 'HIGH', 'ok', category='network'),
        ])
        assert report.verdict == 'NOT READY'
        assert report.critical_failures == 1

    def test_more_than_two_non_critical_failures_means_not_ready(self):
        report = DeploymentReadiness(checks=[
            CheckResult('A', 'A', False, 'HIGH', '', category='system'),
            CheckResult('B', 'B', False, 'MEDIUM', '', category='system'),
            CheckResult('C', 'C', False, 'LOW', '', category='system'),
        ])
        assert report.verdict == 'NOT READY'

    def test_two_non_critical_failures_is_ready(self):
        report = DeploymentReadiness(checks=[
            CheckResult('A', 'A', False, 'HIGH', '', category='system'),
            CheckResult('B', 'B', False, 'MEDIUM', '', category='network'),
            CheckResult('C', 'C', True, 'LOW', '', category='secrets'),
        ])
        assert report.verdict == 'READY'

    def test_to_dict_structure(self):
        report = DeploymentReadiness(checks=[
            CheckResult('A', 'A', True, 'LOW', 'ok', category='system'),
        ])
        d = report.to_dict()
        assert 'verdict' in d
        assert 'summary' in d
        assert d['summary']['total'] == 1
        assert d['summary']['passed'] == 1

    def test_verdict_colour(self):
        ready = DeploymentReadiness(checks=[
            CheckResult('A', 'A', True, 'LOW', 'ok', category='system'),
        ])
        assert ready.verdict_colour == 'success'

        not_ready = DeploymentReadiness(checks=[
            CheckResult('A', 'A', False, 'CRITICAL', 'bad', category='system'),
        ])
        assert not_ready.verdict_colour == 'danger'


# ---------------------------------------------------------------
# PreDeploymentChecker tests
# ---------------------------------------------------------------

class TestPreDeploymentChecker:
    @pytest.fixture
    def checker(self, tmp_path):
        """Checker pointed at a temp project directory."""
        return PreDeploymentChecker(project_root=str(tmp_path))

    def test_run_all_returns_report(self, checker):
        """run_all() must return a DeploymentReadiness with 15 checks."""
        with patch('src.security.deployment.checker.subprocess.run',
                   return_value=MagicMock(stdout='', stderr='', returncode=0)):
            report = checker.run_all()
        assert isinstance(report, DeploymentReadiness)
        assert report.total == 15

    def test_all_checks_have_ids(self, checker):
        with patch('src.security.deployment.checker.subprocess.run',
                   return_value=MagicMock(stdout='', stderr='', returncode=0)):
            report = checker.run_all()
        ids = [c.check_id for c in report.checks]
        assert len(ids) == 15
        assert set(ids) == {f'PDC-{i:02d}' for i in range(1, 16)}

    def test_all_checks_have_category(self, checker):
        with patch('src.security.deployment.checker.subprocess.run',
                   return_value=MagicMock(stdout='', stderr='', returncode=0)):
            report = checker.run_all()
        for c in report.checks:
            assert c.category in ('system', 'network', 'application', 'secrets', 'monitoring'), \
                f'{c.check_id} has unexpected category {c.category!r}'

    # -- individual check unit tests --

    def test_python_version_passes(self, checker):
        """We're running on >= 3.8, so this should pass."""
        result = checker._check_python_version()
        assert result.passed is True
        assert result.check_id == 'PDC-08'

    def test_debug_mode_clean(self, checker):
        """With no debug vars set, check should pass."""
        for v in ('DEBUG', 'FLASK_DEBUG', 'DJANGO_DEBUG'):
            os.environ.pop(v, None)
        result = checker._check_debug_mode()
        assert result.passed is True

    def test_debug_mode_detected(self, checker):
        os.environ['FLASK_DEBUG'] = '1'
        try:
            result = checker._check_debug_mode()
            assert result.passed is False
            assert 'FLASK_DEBUG' in result.details
        finally:
            os.environ.pop('FLASK_DEBUG', None)

    def test_monitoring_hygiene_check(self, checker):
        with patch('src.security.deployment.checker.get_logging_hygiene',
                   return_value={'passed': True, 'details': ['Event log available'], 'severity': 'LOW'}):
            result = checker._check_monitoring_hygiene()
        assert result.check_id == 'PDC-15'
        assert result.category == 'monitoring'
        assert result.passed is True

    def test_env_file_no_env(self, checker, tmp_path):
        """No .env file → pass."""
        result = checker._check_env_file_exposure()
        assert result.passed is True

    def test_env_file_not_gitignored(self, tmp_path):
        (tmp_path / '.env').write_text('SECRET=abc')
        checker = PreDeploymentChecker(project_root=str(tmp_path))
        result = checker._check_env_file_exposure()
        assert result.passed is False

    def test_env_file_gitignored(self, tmp_path):
        (tmp_path / '.env').write_text('SECRET=abc')
        (tmp_path / '.gitignore').write_text('.env\n')
        checker = PreDeploymentChecker(project_root=str(tmp_path))
        result = checker._check_env_file_exposure()
        assert result.passed is True

    def test_hardcoded_secrets_clean(self, tmp_path):
        src = tmp_path / 'src'
        src.mkdir()
        (src / 'app.py').write_text('x = 1\n')
        checker = PreDeploymentChecker(project_root=str(tmp_path))
        result = checker._check_hardcoded_secrets()
        assert result.passed is True

    def test_hardcoded_secrets_detected(self, tmp_path):
        src = tmp_path / 'src'
        src.mkdir()
        (src / 'app.py').write_text('password = "hunter2"\n')
        checker = PreDeploymentChecker(project_root=str(tmp_path))
        result = checker._check_hardcoded_secrets()
        assert result.passed is False

    def test_hardcoded_secrets_skips_security_dir(self, tmp_path):
        """Security module source files contain patterns as strings; they must not
        trigger false positives."""
        src = tmp_path / 'src'
        sec = src / 'security'
        sec.mkdir(parents=True)
        (sec / 'checker.py').write_text("patterns = ['password = \"']\n")
        checker = PreDeploymentChecker(project_root=str(tmp_path))
        result = checker._check_hardcoded_secrets()
        assert result.passed is True, 'Security dir should be skipped'

    def test_hardcoded_secrets_ignores_placeholders(self, tmp_path):
        src = tmp_path / 'src'
        src.mkdir()
        (src / 'config.py').write_text('secret_key = "your-secret-here"\n')
        checker = PreDeploymentChecker(project_root=str(tmp_path))
        result = checker._check_hardcoded_secrets()
        assert result.passed is True, 'Placeholder values must not trigger a hit'

    def test_git_secrets_ignores_env_example(self, tmp_path):
        """'.env.example' is a template; it must not flag as a git secret."""
        (tmp_path / '.git').mkdir()
        (tmp_path / '.env.example').write_text('SECRET=placeholder\n')
        with patch('src.security.deployment.checker.subprocess.run',
                   return_value=MagicMock(
                       stdout='.env.example\nREADME.md\n', returncode=0)):
            checker = PreDeploymentChecker(project_root=str(tmp_path))
            result = checker._check_git_secrets()
        assert result.passed is True, '.env.example should not be flagged'

    def test_git_secrets_detects_real_env(self, tmp_path):
        """A real '.env' file tracked in git should be flagged."""
        (tmp_path / '.git').mkdir()
        with patch('src.security.deployment.checker.subprocess.run',
                   return_value=MagicMock(stdout='.env\napp.py\n', returncode=0)):
            checker = PreDeploymentChecker(project_root=str(tmp_path))
            result = checker._check_git_secrets()
        assert result.passed is False, '.env in git should be flagged'

    def test_vuln_count_not_unknown(self, tmp_path):
        """PDC-09 must never report 'unknown number of' vulnerable packages."""
        checker = PreDeploymentChecker(project_root=str(tmp_path))
        with patch('src.security.deployment.checker.subprocess.run',
                   return_value=MagicMock(stdout='CVE-2023-001\n', stderr='', returncode=1)):
            result = checker._check_dependency_vulnerabilities()
        assert 'unknown number of' not in result.details
        assert result.passed is False

    def test_dns_resolution(self, checker):
        result = checker._check_dns_resolution()
        # May fail in offline CI; just ensure it returns a CheckResult
        assert isinstance(result, CheckResult)
        assert result.check_id == 'PDC-06'

    def test_ssl_tools(self, checker):
        result = checker._check_ssl_tools()
        assert result.check_id == 'PDC-07'
        assert result.passed is True  # CPython always has OpenSSL


# ---------------------------------------------------------------
# Web route tests for pre-deploy (Phase 2)
# ---------------------------------------------------------------
# Note: Web interface tests for pre-deployment are part of Phase 2.
# The current landing page (src/web/app.py) is minimal. Full dashboard
# features including pre-deployment checker routes will be added in Phase 2.
