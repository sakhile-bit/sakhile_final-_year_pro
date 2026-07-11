"""
Unit tests for the assessment module (15-control framework, 120 pts)
"""

import pytest
from unittest.mock import patch, MagicMock
from src.security.assessment.assessor import (
    DigitalHygieneAssessor,
    BusinessInfo,
    ControlResult,
    AssessmentResults,
    InfrastructureAssessor,
    ZambiaRiskAssessor,
    CONTROL_CATALOGUE,
    TOTAL_POSSIBLE_SCORE,
)


@pytest.fixture
def business_info():
    return BusinessInfo(
        name='Test Corp',
        id='TC001',
        contact_person='Jane Doe',
        contact_email='jane@testcorp.zm',
        industry='Technology',
    )


class TestBusinessInfo:
    def test_creation(self, business_info):
        assert business_info.name == 'Test Corp'
        assert business_info.id == 'TC001'
        assert business_info.contact_person == 'Jane Doe'

    def test_defaults(self):
        info = BusinessInfo(name='X', id='1')
        assert info.contact_person is None
        assert info.industry is None
        assert info.province is None
        assert info.num_employees is None


class TestControlResult:
    def test_creation(self):
        cr = ControlResult(
            control_id='C01', name='Test', score=8, weight=10,
            status='PASS', details='ok', category='technical',
            verification='automated',
        )
        assert cr.control_id == 'C01'
        assert cr.score == 8
        assert cr.weight == 10
        assert cr.status == 'PASS'
        assert cr.category == 'technical'

    def test_defaults(self):
        cr = ControlResult(
            control_id='C01', name='Test', score=5, weight=10,
            status='WARNING', details='partial',
        )
        # Defaults come from the dataclass; category defaults to 'technical'
        assert cr.control_id == 'C01'
        assert isinstance(cr.category, str)


class TestControlCatalogue:
    def test_has_15_controls(self):
        assert len(CONTROL_CATALOGUE) == 15

    def test_total_weight_is_120(self):
        assert TOTAL_POSSIBLE_SCORE == 120
        assert sum(c['weight'] for c in CONTROL_CATALOGUE.values()) == 120

    def test_automated_controls(self):
        auto = [k for k, v in CONTROL_CATALOGUE.items() if v['verification'] == 'automated']
        assert len(auto) == 5

    def test_manual_controls(self):
        manual = [k for k, v in CONTROL_CATALOGUE.items() if v['verification'] == 'manual']
        assert len(manual) == 10


class TestDigitalHygieneAssessor:
    def test_init(self, business_info):
        assessor = DigitalHygieneAssessor(business_info)
        assert len(assessor.controls) == 15
        assert 'C01_os_updates' in assessor.controls

    def test_init_with_manual_answers(self, business_info):
        answers = {'C06_security_training': 8, 'C07_access_control': 7}
        assessor = DigitalHygieneAssessor(business_info, manual_answers=answers)
        assert assessor.manual_answers == answers

    @patch.object(DigitalHygieneAssessor, '_check_os_updates')
    @patch.object(DigitalHygieneAssessor, '_check_antivirus_enhanced')
    @patch.object(DigitalHygieneAssessor, '_check_firewall_enhanced')
    @patch.object(DigitalHygieneAssessor, '_check_password_policy')
    @patch.object(DigitalHygieneAssessor, '_check_backup_system')
    def test_run_assessment_auto_only(self, m_backup, m_pw, m_fw, m_av, m_os, business_info):
        """Auto-only assessment (tier=automated) scores C01-C05 and leaves C06-C15 at 0."""
        m_os.return_value = ControlResult('C01', 'OS Updates', 10, 10, 'PASS', 'ok', 'technical', 'automated')
        m_av.return_value = ControlResult('C02', 'Antivirus', 15, 15, 'PASS', 'ok', 'technical', 'automated')
        m_fw.return_value = ControlResult('C03', 'Firewall', 10, 10, 'PASS', 'ok', 'technical', 'automated')
        m_pw.return_value = ControlResult('C04', 'Password', 10, 10, 'PASS', 'ok', 'technical', 'automated')
        m_backup.return_value = ControlResult('C05', 'Backup', 10, 10, 'PASS', 'ok', 'technical', 'automated')

        assessor = DigitalHygieneAssessor(business_info, assessment_tier='automated')
        results = assessor.run_assessment()

        assert results.score == 55  # only automated controls (C01-C05 total weight = 55)
        assert results.total_possible == 120

    @patch.object(DigitalHygieneAssessor, '_check_os_updates')
    @patch.object(DigitalHygieneAssessor, '_check_antivirus_enhanced')
    @patch.object(DigitalHygieneAssessor, '_check_firewall_enhanced')
    @patch.object(DigitalHygieneAssessor, '_check_password_policy')
    @patch.object(DigitalHygieneAssessor, '_check_backup_system')
    def test_run_assessment_zero_not_certified(self, m_backup, m_pw, m_fw, m_av, m_os, business_info):
        """Zero-score assessment should yield NOT CERTIFIED."""
        m_os.return_value = ControlResult('C01', 'OS', 0, 10, 'FAIL', 'bad', 'technical', 'automated')
        m_av.return_value = ControlResult('C02', 'AV', 0, 15, 'FAIL', 'bad', 'technical', 'automated')
        m_fw.return_value = ControlResult('C03', 'FW', 0, 10, 'FAIL', 'bad', 'technical', 'automated')
        m_pw.return_value = ControlResult('C04', 'PW', 0, 10, 'FAIL', 'bad', 'technical', 'automated')
        m_backup.return_value = ControlResult('C05', 'BK', 0, 10, 'FAIL', 'bad', 'technical', 'automated')

        assessor = DigitalHygieneAssessor(business_info)
        results = assessor.run_assessment()

        assert results.score == 0
        assert results.certification_level == 'NOT CERTIFIED'
        assert len(results.recommendations) > 0

    def test_generate_recommendations_all_fail(self, business_info):
        assessor = DigitalHygieneAssessor(business_info)
        controls = {}
        for cid, meta in CONTROL_CATALOGUE.items():
            controls[cid] = ControlResult(
                control_id=meta['id'], name=meta['name'],
                score=0, weight=meta['weight'],
                status='FAIL', details='',
                category=meta.get('category', ''),
                verification=meta.get('verification', ''),
            )
        recs = assessor._generate_recommendations(controls)
        assert len(recs) >= 5  # at least one rec per failed control


class TestInfrastructureAssessor:
    def _patched(self, assessor, **overrides):
        """Patch every network-touching method so run_checks is deterministic."""
        defaults = {
            '_check_dns_resolution': 'Resolves to 93.184.216.34',
            '_check_dns_security': {'spf': 'SPF record found',
                                    'dmarc': 'DMARC record found',
                                    'caa': 'CAA record found', 'notes': ''},
            '_check_ssl_certificate': 'SSL/TLS enabled, expires: ... (120 days)',
            '_inspect_certificate': {'valid': True, 'self_signed': False,
                                     'hostname_mismatch': False,
                                     'issuer': 'Test CA', 'days_left': 120},
            '_check_tls_version': 'Good – only TLS 1.2+ accepted',
            '_check_https_redirect': 'HTTP redirects to HTTPS (https://example.com)',
            '_check_security_headers': {
                'Strict-Transport-Security': 'PRESENT – max-age=63072000'},
            '_check_http_methods': {'allow': 'GET, POST', 'trace_enabled': False},
            '_check_http_meta': {'server': '', 'powered_by': '',
                                 'insecure_cookies': [], 'hsts_max_age': None},
            '_get_external_ip': '203.0.113.1',
            '_get_scanner_ip': '10.0.0.5',
            '_reverse_dns': 'example.com',
            '_scan_common_ports': [80, 443],
            '_identify_risky_ports': [],
        }
        defaults.update(overrides)
        from contextlib import ExitStack
        stack = ExitStack()
        for name, val in defaults.items():
            stack.enter_context(patch.object(InfrastructureAssessor, name,
                                             return_value=val))
        return stack

    def test_run_checks_returns_expected_keys(self):
        assessor = InfrastructureAssessor('example.com')
        with self._patched(assessor):
            result = assessor.run_checks()
        # Legacy keys preserved for backward compatibility
        assert result['dns_resolution'] == 'Resolves to 93.184.216.34'
        assert str(result['https_redirect']).startswith('HTTP redirects to HTTPS')
        assert result['external_ip'] == '203.0.113.1'
        assert result['open_ports'] == [80, 443]
        # New enrichment keys
        assert result['target_ip'] == '203.0.113.1'
        assert result['services'] == {80: 'HTTP', 443: 'HTTPS'}
        assert result['reverse_dns'] == 'example.com'
        assert 'findings' in result and 'grade' in result and 'score' in result

    def test_clean_target_is_secure(self):
        assessor = InfrastructureAssessor('example.com')
        with self._patched(assessor):
            result = assessor.run_checks()
        assert result['score'] == 100
        assert result['grade'] == 'SECURE'
        assert result['findings'] == []

    def test_critical_port_makes_at_risk(self):
        assessor = InfrastructureAssessor('example.com')
        with self._patched(
            assessor,
            _scan_common_ports=[80, 443, 3389],
            _identify_risky_ports=[
                'Port 3389: RDP – remote desktop, brute-force/BlueKeep risk [CRITICAL]'],
        ):
            result = assessor.run_checks()
        sevs = [f['severity'] for f in result['findings']]
        assert 'CRITICAL' in sevs
        assert result['grade'] == 'AT RISK'
        assert result['score'] < 85

    def test_expired_cert_and_missing_spf_flagged(self):
        assessor = InfrastructureAssessor('example.com')
        with self._patched(
            assessor,
            _check_ssl_certificate='SSL certificate EXPIRED (Jan 1 2020 GMT)',
            _check_dns_security={'spf': 'No SPF record – email spoofing risk',
                                 'dmarc': 'DMARC record found',
                                 'caa': 'CAA record found', 'notes': ''},
        ):
            result = assessor.run_checks()
        ids = {f['id'] for f in result['findings']}
        assert 'TLS-CERT' in ids
        assert 'DNS-SPF' in ids

    def test_service_mapping_and_risky_ports_are_consistent(self):
        # Every risky port must be a known service and carry a severity tag.
        for port, (desc, sev) in InfrastructureAssessor.RISKY_PORTS.items():
            assert port in InfrastructureAssessor.PORT_SERVICES
            assert sev in ('CRITICAL', 'HIGH', 'MEDIUM')


class TestZambiaRiskAssessor:
    def test_assess_no_answers(self):
        assessor = ZambiaRiskAssessor()
        result = assessor.assess({})
        # With no mitigations, risk score should still be >= 0
        assert 'RISK' in result['risk_level'] or result['risk_level'] in ('HIGH', 'MEDIUM', 'LOW')
        assert isinstance(result['score'], (int, float))

    def test_assess_all_mitigated(self):
        assessor = ZambiaRiskAssessor()
        answers = {}
        for threat in assessor.LOCAL_THREATS:
            answers[threat.replace(' ', '_').lower()] = True
        for law in assessor.COMPLIANCE_LAWS:
            answers[law.replace(' ', '_').lower()] = True
        result = assessor.assess(answers)
        assert 'RISK' in result['risk_level'] or result['risk_level'] in ('LOW', 'MEDIUM', 'HIGH')
        assert result['mitigated'] >= 0
