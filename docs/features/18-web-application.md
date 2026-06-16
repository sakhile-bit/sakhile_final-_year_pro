# Feature: Flask Web Application

## Overview
The Flask web application provides a **multi-user, browser-based** interface to the Zambia Digital Hygiene Certification Programme. It supports three user roles (admin, assessor, business owner), stores all assessments and certificates in a database, and exposes a full set of management routes.

**File:** [`src/web/app.py`](../../src/web/app.py)  
**Admin blueprint:** [`src/web/admin.py`](../../src/web/admin.py)

---

## Architecture

```
Browser  →  Flask routes  →  SQLAlchemy models  →  SQLite / MySQL
                          →  DigitalHygieneAssessor
                          →  InfrastructureAssessor
                          →  ZambiaRiskAssessor
                          →  PreDeploymentChecker
                          →  ReportGenerator
```

- **Application factory:** `create_app(db_uri=None)` — creates tables, migrates MFA columns, seeds default admin, registers blueprints.
- **Module-level binding:** `db`, `login_manager`, `csrf` are bound to `app` at import time so `flask run` works without calling `create_app()`.
- **Database:** Auto-falls back to `instance/digital_hygiene.db` (SQLite) if MySQL is not configured.

---

## Database Models

| Model | Table | Purpose |
|---|---|---|
| `User` | `users` | Accounts with role + optional MFA |
| `Business` | `businesses` | Business profiles (name, reg number, industry) |
| `Assessment` | `assessments` | Completed assessments (JSON controls, score, tier) |
| `Certificate` | `certificates` | Issued certificates with validity dates |
| `AuditLog` | `audit_logs` | Security event log (login, cert issued, etc.) |
| `Remediation` | `remediations` | Remediation tasks tracked per assessment |
| `AssessmentRequest` | `assessment_requests` | Business owners request assessments |

---

## User Roles

| Role | Capabilities |
|---|---|
| **admin** | Full access — all assessments, users, audit logs, admin panel |
| **assessor** | Run assessments, see their own results, accept requests from businesses |
| **business_owner** | Register business, request assessments, view own results/certificates |

---

## Key Routes

### Public
| Route | Description |
|---|---|
| `GET /` | Landing page with desktop app download link |
| `GET /login` | Login form |
| `POST /login` | Authenticate (rate-limited: 5 attempts / 5 min) |
| `GET /register` | Self-registration (business_owner or assessor role) |
| `POST /register` | Create account (password strength enforced) |
| `GET /logout` | Log out |

### Authenticated
| Route | Description |
|---|---|
| `GET /dashboard` | Role-filtered assessment dashboard with stats and Chart.js trend |
| `GET /assess` | Start a new assessment |
| `POST /assess` | Submit assessment form → runs `DigitalHygieneAssessor` → saves to DB |
| `GET /results/<id>` | View assessment results |
| `GET /download/<id>/<fmt>` | Download report (pdf / html / json / csv) |
| `GET /remediation/<id>` | View and manage remediation tasks for an assessment |
| `POST /remediation/<id>/create` | Create a remediation task for a failed control |
| `POST /remediation/update/<id>` | Update remediation status / notes |
| `GET /zambia-assessment` | Zambia-specific risk checklist |
| `GET /infrastructure-scan` | External infrastructure scanner |
| `GET /system-scan` | Combined system + infra scan |
| `GET /my-business` | Business owner: register/edit business profile |
| `GET /request-assessment` | Business owner: submit assessment request |
| `GET /assessment-requests` | Assessors/admin: view and accept pending requests |
| `GET /profile` | User profile with recent login history |
| `GET/POST /change-password` | Change password (strength enforced) |
| `GET/POST /mfa-setup` | Enable/disable TOTP-based MFA |
| `GET/POST /mfa-verify` | Verify MFA code during login |

### API (JSON)
| Route | Description |
|---|---|
| `GET /api/stats` | Dashboard chart data (cert counts, trend scores) |
| `GET /api/assessments` | List assessments as JSON |

### Admin Blueprint (`/admin/...`)
| Route | Description |
|---|---|
| `GET /admin/` | Admin dashboard |
| `GET /admin/users` | User management |
| `GET /admin/audit-logs` | Security event audit log |
| `GET /admin/assessments` | All assessments |
| `GET /admin/businesses` | All businesses |

---

## Assessment Flow

```
POST /assess
│
├─ Parse BusinessInfo from form
├─ Collect manual answers (C06–C15) if tier = 'full'
├─ Upsert Business record in DB
├─ Run DigitalHygieneAssessor.run_assessment()
├─ Save Assessment to DB
├─ If tier != 'NOT CERTIFIED':
│    └─ Auto-issue Certificate (ZDH-YYYY-XXXXXX)
│         └─ GOLD/SILVER → 12-month validity
│         └─ BRONZE       →  6-month validity
└─ Redirect to GET /results/<id>
```

---

## Authentication & Security

| Feature | Implementation |
|---|---|
| **Password hashing** | Werkzeug PBKDF2-SHA256 |
| **Password strength** | Min 12 chars, upper, lower, digit, special char |
| **Rate limiting** | Custom `@rate_limit` decorator (5 attempts / 5 min per IP) |
| **CSRF protection** | Flask-WTF `CSRFProtect` on all POST forms |
| **Session cookies** | `SECURE` (HTTPS only in prod), `HttpOnly`, `SameSite=Lax`, 1-hour lifetime |
| **TOTP MFA** | `pyotp` + `qrcode` (optional dependency) |
| **Audit logging** | Every login, cert issue, remediation create/update written to `audit_logs` |
| **Role-based access** | Every route filters queries by `current_user.role` |
| **Admin decorator** | `@admin_required` — returns HTTP 403 for non-admins |

---

## Certificate Numbering

Certificates use the format `ZDH-YYYY-XXXXXX`:
- `ZDH` = Zambia Digital Hygiene
- `YYYY` = 4-digit year
- `XXXXXX` = 6-char random hex token (e.g. `A3F1C8`)

Example: `ZDH-2026-A3F1C8`

---

## MFA (Multi-Factor Authentication)

When `pyotp` and `qrcode` are installed:
1. User visits `/mfa-setup` → clicks **Enable**
2. A TOTP secret is generated and stored in `User.mfa_secret`
3. A QR code is displayed — user scans with Google Authenticator or similar
4. User enters a 6-digit code to verify and activate MFA
5. On next login, after password validation the user is redirected to `/mfa-verify`
6. A valid TOTP code completes the login

---

## Dashboard Stats

`GET /api/stats` returns JSON powering Chart.js widgets on the dashboard:

```json
{
  "cert_counts":  { "GOLD": 3, "SILVER": 5, "BRONZE": 2, "NOT CERTIFIED": 1 },
  "trend_labels": ["01 Jan", "15 Feb", ...],
  "trend_scores": [42, 67, 78, ...],
  "total":        11,
  "avg_score":    72.3
}
```

Business owners see only their own data; assessors see only their assessments; admins see everything.

---

## Running the Web App

### Development (SQLite)
```bash
python src/web/app.py
```
Or:
```bash
flask --app src/web/app run --debug
```

### Production (MySQL)
Set in `config.yml` or environment:
```
DB_HOST=localhost
DB_NAME=digital_hygiene
DB_USER=app_user
DB_PASSWORD=strongpassword
```

---

## Default Admin Account

Seeded automatically on first run:
- **Username:** `admin`
- **Password:** `admin123`

Change this immediately in production via `/change-password`.

---

## Related Features
- [Digital Hygiene Assessment](01-digital-hygiene-assessment.md) — assessment engine
- [Results & Certification](03-results-certification.md) — desktop GUI equivalent
- [Report Generation](17-report-generation.md) — download endpoint
- [Zambia Risk Assessment](08-zambia-risk-assessment.md) — `/zambia-assessment` route
- [Infrastructure Scanner](06-infra-scanner.md) — `/infrastructure-scan` route
