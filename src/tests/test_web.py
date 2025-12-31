"""
Unit tests for the web application
"""

import pytest
from unittest.mock import patch, MagicMock
from src.web.app import create_app, db


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


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
        assert b'Zambia Digital Hygiene Assessment' in response.data

    def test_login_required_redirect(self, client):
        """Test that protected routes redirect to login"""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect
        assert '/login' in response.headers['Location']

    def test_login_page(self, client):
        """Test login page loads"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_invalid_login(self, client):
        """Test invalid login attempt"""
        response = client.post('/login', data={
            'username': 'invalid',
            'password': 'invalid'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data

    def test_valid_login(self, client, app):
        """Test valid login"""
        with app.app_context():
            # Create test user
            from src.web.app import User
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()

        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'dashboard' in response.data.lower()

    def test_api_assessments(self, client, app):
        """Test assessments API endpoint"""
        with app.app_context():
            # Create test user and login
            from src.web.app import User
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()

            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })

            response = client.get('/api/assessments')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)

    def test_404_error(self, client):
        """Test 404 error page"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        assert b'404' in response.data


class TestAssessmentWorkflow:
    """Test the complete assessment workflow"""

    @patch('src.web.app.DigitalHygieneAssessor')
    def test_assessment_creation(self, mock_assessor_class, client, app):
        """Test creating an assessment through the web interface"""
        with app.app_context():
            # Create and login test user
            from src.web.app import User
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()

            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            })

            # Mock the assessor
            mock_assessor = MagicMock()
            mock_results = MagicMock()
            mock_results.score = 40
            mock_results.total_possible = 50
            mock_results.certification_level = 'GOLD'
            mock_results.controls = {}
            mock_results.recommendations = ['Keep up the good work!']
            mock_assessor.run_assessment.return_value = mock_results
            mock_assessor_class.return_value = mock_assessor

            # Submit assessment form
            response = client.post('/assess', data={
                'business_name': 'Test Business',
                'business_id': 'TB001',
                'contact_person': 'John Doe',
                'contact_email': 'john@test.com',
                'industry': 'Technology'
            }, follow_redirects=True)

            assert response.status_code == 200
            assert b'Assessment completed successfully' in response.data

            # Verify assessment was saved to database
            from src.web.app import Assessment
            assessment = Assessment.query.filter_by(business_name='Test Business').first()
            assert assessment is not None
            assert assessment.score == 40
            assert assessment.certification_level == 'GOLD'
