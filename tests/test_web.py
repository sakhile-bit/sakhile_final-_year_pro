"""
Unit tests for the web application (landing page)
"""

import pytest
from src.web.app import create_app


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    return app


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

    def test_download_redirect(self, client):
        """Test that /download redirects to the exe URL"""
        response = client.get('/download', follow_redirects=False)
        assert response.status_code == 302
        assert 'github.com' in response.headers['Location']

    def test_about_page(self, client):
        """Test about page loads"""
        response = client.get('/about')
        assert response.status_code == 200
        assert b'About the Program' in response.data

    def test_verify_page(self, client):
        """Test certificate verification page"""
        response = client.get('/verify/TEST-CERT-001')
        assert response.status_code == 200
        assert b'Certificate Verification' in response.data

    def test_404_error(self, client):
        """Test 404 error page"""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_500_error_handler(self, client):
        """Test 500 error handler is registered"""
        # The app has the error handler registered
        app = client.application
        assert app is not None
        # Verify error handler exists
        assert 500 in app.error_handler_spec[None]

