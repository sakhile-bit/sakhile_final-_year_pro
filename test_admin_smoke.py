"""Quick smoke test for admin dashboard pages."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from src.web.app import create_app, db, User

app = create_app(db_uri='sqlite:///:memory:')
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@test.com', role='admin', is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

client = app.test_client()

# Login
with client.session_transaction() as sess:
    pass
r = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
logged_in = r.status_code == 200 and b'Dashboard' in r.data
print(f'Login: {"OK" if logged_in else "FAIL"} (status={r.status_code})')
if not logged_in:
    print('Cannot test admin pages without login. Exiting.')
    sys.exit(1)

# Test each admin page
pages = {
    '/admin/':             b'Admin Dashboard',
    '/admin/users':        b'User Management',
    '/admin/businesses':   b'Business Management',
    '/admin/assessments':  b'Assessments',
    '/admin/certificates': b'Certificates',
    '/admin/audit-logs':   b'Audit Logs',
    '/admin/system':       b'System Health',
}

ok = 0
for path, expected in pages.items():
    r = client.get(path)
    found = expected in r.data
    print(f'  {path:30s} -> {r.status_code} {"OK" if found else "FAIL"}')
    if found:
        ok += 1

# API stats
r = client.get('/admin/api/stats')
is_json = r.content_type.startswith('application/json')
print(f'  /admin/api/stats              -> {r.status_code} {"JSON OK" if is_json else "FAIL"}')
if is_json:
    ok += 1

print(f'\nResult: {ok}/{len(pages)+1} pages OK')
