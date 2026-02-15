"""Smoke test for the new user/business workflow features."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.web.app import create_app, db, login_attempts

def get_csrf(response):
    m = re.search(r'name="csrf_token" value="([^"]+)"', response.data.decode())
    return m.group(1) if m else ''

def main():
    app = create_app('sqlite://')
    with app.test_client() as c:
        # 1. Register page renders
        r = c.get('/register')
        assert r.status_code == 200 and b'Create Account' in r.data
        print('[OK] /register GET')

        # 2. Register as business_owner
        token = get_csrf(r)
        r = c.post('/register', data={
            'csrf_token': token,
            'username': 'testowner', 'email': 'owner@test.com',
            'password': 'TestPass123!@#', 'confirm_password': 'TestPass123!@#',
            'role': 'business_owner'
        }, follow_redirects=True)
        assert r.status_code == 200 and b'Registration successful' in r.data
        print('[OK] /register POST - business_owner created')

        # 3. Login as business owner
        token = get_csrf(c.get('/login'))
        r = c.post('/login', data={
            'csrf_token': token, 'username': 'testowner', 'password': 'TestPass123!@#'
        }, follow_redirects=True)
        assert r.status_code == 200 and b'Business Dashboard' in r.data
        print('[OK] login + dashboard for business_owner')

        # 4. My Business page
        r = c.get('/my-business')
        assert r.status_code == 200 and b'Register Your Business' in r.data
        print('[OK] /my-business GET (empty)')

        # 5. Register a business
        token = get_csrf(r)
        r = c.post('/my-business', data={
            'csrf_token': token,
            'business_name': 'Test Corp Zambia', 'registration_number': 'ZM-12345',
            'contact_person': 'John Doe', 'contact_email': 'john@test.com',
            'contact_phone': '+260 123456', 'industry': 'Technology',
            'province': 'Lusaka', 'num_employees': '50', 'address': '123 Cairo Road'
        }, follow_redirects=True)
        assert r.status_code == 200 and b'Business profile saved' in r.data
        print('[OK] /my-business POST - business registered')

        # 6. Request Assessment page
        r = c.get('/request-assessment')
        assert r.status_code == 200 and b'Request Assessment' in r.data
        print('[OK] /request-assessment GET')

        # 7. Submit assessment request
        token = get_csrf(r)
        r = c.post('/request-assessment', data={
            'csrf_token': token,
            'assessment_tier': 'full', 'notes': 'First assessment', 'preferred_date': '2025-02-01'
        }, follow_redirects=True)
        assert r.status_code == 200 and b'Assessment request submitted' in r.data
        print('[OK] /request-assessment POST')

        # 8. Dashboard shows pending requests
        r = c.get('/dashboard')
        assert r.status_code == 200 and b'Your Assessment Requests' in r.data
        print('[OK] dashboard shows pending requests')

        # 9. Logout and login as admin
        c.get('/logout')
        token = get_csrf(c.get('/login'))
        r = c.post('/login', data={
            'csrf_token': token, 'username': 'admin', 'password': 'admin123'
        }, follow_redirects=True)
        assert r.status_code == 200
        print('[OK] admin login')

        # 10. Assessment requests page
        r = c.get('/assessment-requests')
        assert r.status_code == 200 and b'Test Corp Zambia' in r.data
        print('[OK] /assessment-requests - shows pending request')

        # 11. Accept request
        token = get_csrf(r)
        r = c.post('/accept-request/1', data={'csrf_token': token}, follow_redirects=True)
        assert r.status_code == 200
        print('[OK] /accept-request POST')

        # 12. Register as assessor
        c.get('/logout')
        r = c.get('/register')
        token = get_csrf(r)
        r = c.post('/register', data={
            'csrf_token': token,
            'username': 'testassessor', 'email': 'assessor@test.com',
            'password': 'AssessPass123!@', 'confirm_password': 'AssessPass123!@',
            'role': 'assessor'
        }, follow_redirects=True)
        assert r.status_code == 200 and b'Registration successful' in r.data
        print('[OK] register as assessor')

        # 13. Login as assessor - sees requests page
        login_attempts.clear()
        r = c.get('/login')
        token = get_csrf(r)
        r = c.post('/login', data={
            'csrf_token': token, 'username': 'testassessor', 'password': 'AssessPass123!@'
        }, follow_redirects=True)
        assert r.status_code == 200 and b'Assessor Dashboard' in r.data
        r = c.get('/assessment-requests')
        assert r.status_code == 200 and b'Assessment Requests' in r.data
        print('[OK] assessor sees assessment requests page')

        # 14. Landing page for unauthenticated shows register CTA
        c.get('/logout')
        r = c.get('/')
        assert r.status_code == 200 and b'Get Started' in r.data and b'How It Works' in r.data
        print('[OK] landing page has registration CTA and How It Works')

        print('\n=== ALL 14 SMOKE TESTS PASSED ===')

if __name__ == '__main__':
    main()
