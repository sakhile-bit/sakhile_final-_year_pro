# Security Audit Report
**Project:** Zambia Digital Hygiene Certification Tool  
**Date:** 2026-06-19  
**Auditor:** Claude Sonnet 4.6 (Automated Security Review)  
**Scope:** Full codebase — all Python source files under `src/`, `database/`, and root-level scripts  

---

## Executive Summary

A full-codebase security audit was performed across all Python source files. **5 vulnerabilities were patched** in this session. 3 additional items require manual action outside the codebase (credential rotation and deployment configuration).

| Severity | Found | Patched | Requires Manual Action |
|----------|-------|---------|------------------------|
| Critical | 1 | 0 | 1 (git history + credential rotation) |
| High | 4 | 4 | 1 (SECRET_KEY) |
| Medium | 4 | 1 | 1 (rate limiter) |
| Low | 3 | 0 | — |
| **Total** | **12** | **5** | **3** |

---

## Patched Vulnerabilities

### 1. Command Injection — `database/setup_mysql.py`
**Severity:** High  
**Lines affected:** 92–93, 119, 137, 156 (original)

**Root cause:** All `mysql` subprocess calls used `shell=True` with user-supplied values (`db_host`, `db_port`, `db_user`, `db_password`, `app_user`, `app_password`) directly interpolated into f-strings.

**Exploit scenario:** An attacker entering `localhost; del /f /s /q C:\` as the host field would have the shell execute that second command with the privileges of the running process.

**Fix applied:** Every subprocess call was rewritten to use an argument list (`['mysql', f'-h{db_host}', f'-P{db_port}', ...]`). The SQL schema file is now passed via `stdin=` instead of a shell `<` redirect. Passwords are read with `getpass` to avoid terminal echo.

---

### 2. Hardcoded Default Admin Password — `src/web/app.py`, `src/utils/cli.py`, `reset_admin.py`
**Severity:** High  
**Lines affected:** `app.py:459`, `cli.py:485`, `reset_admin.py:8–13` (original)

**Root cause:** The literal strings `'Admin@12345!'` and `'admin123'` were baked into source code. Any deployment that skipped a password change exposed a fully authenticated admin account with a publicly known password.

**Exploit scenario:** An attacker with network access to the Flask web interface logs in as `admin` / `admin123` and gains full administrative control over all assessments, certificates, and user accounts.

**Fix applied:**
- `app.py` and `cli.py` now read `ADMIN_DEFAULT_PASSWORD` from the environment. If the variable is absent, a cryptographically random password is generated via `secrets.token_urlsafe(16)` and printed as a startup warning — a known static default is never used.
- `reset_admin.py` was rewritten to read from the environment variable or fall back to an interactive `getpass` prompt.

---

### 3. MFA Brute-Force (No Rate Limit on `/mfa-verify`) — `src/web/app.py`
**Severity:** High  
**Lines affected:** 1382–1413 (original)

**Root cause:** The `/login` route was protected by `@rate_limit(max_attempts=5, window=300)` but the `/mfa-verify` route had no rate limiting at all. TOTP with `valid_window=1` allows 3 valid codes at a time (previous, current, next). A 6-digit code space has 1,000,000 possibilities, but with a 30-second window an attacker has up to ~30,000 attempts before the valid code rotates out.

**Exploit scenario:** An attacker who has stolen a user's credentials but does not know the TOTP secret can submit automated requests to `/mfa-verify`, cycling through all possible 6-digit codes. Without rate limiting, this can succeed within minutes.

**Fix applied:** Added `@rate_limit(max_attempts=5, window=300)` to the `mfa_verify` route, matching the same policy applied to the login route.

---

### 4. Internal Exception Details Exposed to Users — `src/web/app.py`
**Severity:** Medium  
**Lines affected:** 1056–1058 (original)

**Root cause:** `flash(f'Assessment failed: {str(e)}', 'error')` echoed raw exception messages (potentially including SQLAlchemy stack traces, internal file paths, or database schema details) directly to the browser.

**Exploit scenario:** A deliberately malformed request that triggers a database error reveals table names, column names, or file system paths that help an attacker map the application's internals.

**Fix applied:** User-facing message changed to a generic `'Assessment failed. Please try again or contact support.'`. The full exception is still logged server-side via `logger.error()` for debugging.

---

### 5. `os.system()` Leaking Command Output to Server Console — `src/web/app.py`
**Severity:** Medium  
**Lines affected:** 1803 (original)

**Root cause:** `os.system('netsh advfirewall show allprofiles')` prints raw Windows command output directly to the server process's standard output. On cloud or shared hosting platforms this leaks system configuration details into server logs visible to operators or log aggregation systems.

**Fix applied:** Replaced with `subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'], capture_output=True)`. Output is captured and discarded; only the return code is used. No shell interpreter is involved.

---

## Open Items — Manual Action Required

### CRITICAL — Committed Credentials in Git History
**File:** `.env.example`  
**Issue:** `.env.example` was committed to git containing a real `DB_PASSWORD` value (now redacted) alongside `ADMIN_DEFAULT_PASSWORD=admin123`. These credentials exist in the repository's full git history even though the file has since been sanitized.

**Required actions:**
1. **Rotate `DB_PASSWORD` immediately** — change the MySQL user password on the database server.
2. **Scrub git history** (replaces the old password everywhere it appears):
   ```bash
   pip install git-filter-repo
   echo "OLD_PASSWORD_HERE==>REDACTED" > replacements.txt
   git filter-repo --replace-text replacements.txt
   git push --force
   ```
3. **Add `.env` to `.gitignore`** if not already present.
4. **Notify all collaborators** to re-clone — their local copies still contain the old history.

---

### HIGH — Weak Flask `SECRET_KEY` Default
**File:** `src/utils/config.py:58`, `src/web/app.py:78`  
**Issue:** The application falls back to `'dev-secret-key-change-in-production'` if `SECRET_KEY` is not set in the environment. Flask uses this key to sign session cookies. An attacker who knows the key can forge arbitrary session cookies and impersonate any user — including the admin.

**Additionally:** `SESSION_COOKIE_SECURE` defaults to `false`, so session cookies are transmitted over plain HTTP.

**Required actions:**
1. Generate a real secret key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
2. Set it in your deployment environment (not in `.env` committed to git).
3. Set `SESSION_COOKIE_SECURE=true` in production.

---

### MEDIUM — In-Memory Rate Limiter Not Process-Safe
**File:** `src/web/app.py:489–507`  
**Issue:** The rate limiter stores attempt counts in a plain Python `dict` in module scope. This means:
- Limits reset every time the process restarts (trivially bypassed by killing/restarting the worker).
- Under multi-worker deployments (Gunicorn with `--workers N`), each worker has its own counter, giving an attacker `N × 5` attempts per window.

**Required actions:**
1. Replace the in-memory dict with [Flask-Limiter](https://flask-limiter.readthedocs.io/) backed by Redis:
   ```python
   from flask_limiter import Limiter
   from flask_limiter.util import get_remote_address

   limiter = Limiter(get_remote_address, app=app, storage_uri="redis://localhost:6379")

   @app.route('/login', methods=['GET', 'POST'])
   @limiter.limit("5 per 5 minutes")
   def login(): ...
   ```

---

## Low Severity — Informational

| # | File | Finding | Recommendation |
|---|------|---------|----------------|
| L1 | `src/web/app.py:1109` | `send_file()` called with path returned by report generators — no explicit bounds check that the path stays within the reports directory | Add `Path(report_path).resolve().is_relative_to(REPORTS_DIR)` check before `send_file()` |
| L2 | `src/web/app.py:2337` | Open redirect: `DOWNLOAD_URL` env var is passed directly to `redirect()` with no validation | Validate the URL is an allowed domain before redirecting |
| L3 | `src/web/app.py:1550` | CSRF protection on the remediation update form depends on whether the Jinja template includes `{{ csrf_token() }}` — verify all POST forms include the token | Audit all templates; use `flask_wtf.FlaskForm` for consistent CSRF enforcement |

---

## Findings Confirmed Safe

| File | What was checked | Result |
|------|-----------------|--------|
| `src/utils/config.py:87` | YAML deserialization | `yaml.safe_load()` used — safe |
| All `.py` files | Pickle deserialization | No `pickle` usage found |
| All `.py` files | `eval()` / `exec()` injection | No dynamic code execution on user input |
| `src/web/app.py` | SQL queries via SQLAlchemy ORM | Parameterised queries throughout — no raw string injection |

---

## Files Modified by This Audit

| File | Change |
|------|--------|
| `database/setup_mysql.py` | Rewrote all subprocess calls to use argument lists; added `getpass` for password input |
| `src/web/app.py` | Replaced hardcoded admin password with env var; added `@rate_limit` to `mfa_verify`; generic exception flash; `subprocess.run` for firewall check |
| `src/utils/cli.py` | Replaced hardcoded `admin123` with env var / generated password |
| `reset_admin.py` | Rewrote to use env var or interactive prompt; removed hardcoded password |
