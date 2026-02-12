"""Quick smoke test: verify every key route works with the MySQL backend."""
import requests
import sys

BASE = 'http://127.0.0.1:5000'
s = requests.Session()
ok = True

def check(label, condition):
    global ok
    status = "PASS" if condition else "FAIL"
    if not condition:
        ok = False
    print(f"  [{status}] {label}")

# 1. Home page
r = s.get(f'{BASE}/')
check('Home page loads (200)', r.status_code == 200)
check('Home page has title', 'Zambia Digital Hygiene' in r.text)

# 2. Login
r = s.post(f'{BASE}/login', data={'username': 'admin', 'password': 'admin123'}, allow_redirects=False)
check('Login redirects (302)', r.status_code == 302)

# Follow redirect
r = s.get(f'{BASE}/dashboard')
check('Dashboard loads (200)', r.status_code == 200)
check('Dashboard has content', 'dashboard' in r.text.lower() or 'assessment' in r.text.lower())

# 3. Assessment page
r = s.get(f'{BASE}/assess')
check('Assessment page loads (200)', r.status_code == 200)
check('Assessment form present', 'business_name' in r.text)

# 4. Pre-deploy check page
r = s.get(f'{BASE}/predeploy-check')
check('Pre-Deploy Check page loads (200)', r.status_code == 200)
check('Pre-Deploy has content', 'Pre-Deployment' in r.text)

# 5. Zambia assessment
r = s.get(f'{BASE}/zambia-assessment')
check('Zambia Assessment loads (200)', r.status_code == 200)

# 6. System scan
r = s.get(f'{BASE}/system-scan')
check('System Scan loads (200)', r.status_code == 200)

# 7. API endpoint
r = s.get(f'{BASE}/api/assessments')
check('API returns 200', r.status_code == 200)
data = r.json()
check('API returns list', isinstance(data, list))
check('API has 3 sample assessments', len(data) == 3)

# 8. Profile
r = s.get(f'{BASE}/profile')
check('Profile loads (200)', r.status_code == 200)

# 9. Logout
r = s.get(f'{BASE}/logout', allow_redirects=False)
check('Logout redirects (302)', r.status_code == 302)

# 10. Protected route after logout
r = s.get(f'{BASE}/dashboard', allow_redirects=False)
check('Dashboard requires login after logout (302)', r.status_code == 302)

print()
if ok:
    print("ALL CHECKS PASSED")
else:
    print("SOME CHECKS FAILED")
    sys.exit(1)
