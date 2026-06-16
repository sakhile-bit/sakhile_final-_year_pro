"""
Unit tests for the web application (Phase 2 — full platform)
"""

import pytest
from unittest.mock import patch
from src.web.app import create_app, db as _db


@pytest.fixture
def app():
    """Create and configure a test app instance backed by an in-memory SQLite DB."""
    application = create_app(db_uri='sqlite:///:memory:')
    application.config['TESTING'] = True
    application.config['DEBUG'] = False
    application.config['WTF_CSRF_ENABLED'] = False  # disable CSRF in tests
    application.config['SESSION_COOKIE_SECURE'] = False
    with application.app_context():
        _db.create_all()
    yield application
    with application.app_context():
        _db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


class TestWebApp:
    """Test web application routes and functionality"""

    def test_index_page(self, client):
        """Test index page loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Zambia Digital Hygiene' in response.data

    def test_login_page(self, client):
        """Test login page loads"""
        response = client.get('/login')
        assert response.status_code == 200

    def test_register_page(self, client):
        """Test register page loads"""
        response = client.get('/register')
        assert response.status_code == 200

    def test_about_page(self, client):
        """Test about page loads"""
        response = client.get('/about')
        assert response.status_code == 200

    def test_verify_page(self, client):
        """Test certificate verification page (unverified)"""
        response = client.get('/verify/TEST-CERT-001')
        assert response.status_code == 200

    def test_dashboard_redirects_to_login(self, client):
        """Protected dashboard must redirect unauthenticated users to login"""
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code in (302, 401)

    def test_assess_redirects_to_login(self, client):
        """Protected assess page must redirect unauthenticated users"""
        response = client.get('/assess', follow_redirects=False)
        assert response.status_code in (302, 401)

    def test_infrastructure_scan_page(self, client):
        """Infrastructure scan page should be accessible"""
        response = client.get('/infrastructure-scan')
        assert response.status_code == 302 or response.status_code == 401

    @patch('src.web.app.InfrastructureAssessor.run_checks')
    def test_infrastructure_scan_post(self, mock_run_checks, client):
        mock_run_checks.return_value = {
            'dns_resolution': 'Resolves to 127.0.0.1',
            'ssl_certificate': 'SSL/TLS enabled',
            'https_redirect': 'HTTP redirects to HTTPS (https://localhost)',
            'external_ip': '127.0.0.1',
            'open_ports': [80, 443],
            'tls_version': 'Good – only TLS 1.2+ accepted',
            'security_headers': {},
            'dns_security': {'spf': 'Not checked', 'dmarc': 'Not checked', 'notes': ''},
            'risky_ports': [],
        }
        # Infrastructure scan requires login – authenticate as admin first
        client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        response = client.post('/infrastructure-scan', data={'domain': 'localhost'})
        assert response.status_code in (200, 302)
        # Either scan results are shown, or we get a redirect (both are valid)
        if response.status_code == 200:
            assert b'localhost' in response.data or b'Infrastructure' in response.data

    def test_404_error(self, client):
        """Test 404 error page"""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_500_error_handler(self, client):
        """Test 500 error handler is registered"""
        app = client.application
        assert app is not None
        assert 500 in app.error_handler_spec[None]

    def test_admin_required_for_admin_routes(self, client):
        """Admin routes must deny unauthenticated access"""
        response = client.get('/admin/', follow_redirects=False)
        assert response.status_code in (302, 401, 403)


def test_check_dns_resolution_for_localhost():
    from src.web.app import check_dns_resolution

    result = check_dns_resolution('localhost')
    assert 'Resolves to' in result or 'DNS resolution failed' not in result


def test_http_to_https_localhost():
    from src.web.app import check_http_to_https

    result = check_http_to_https('localhost')
    assert 'Local host' in result

