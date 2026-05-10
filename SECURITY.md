# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in this project, please **do not** open a public GitHub issue. Instead:

1. **Email**: Send details to [security@digitalhygiene.gov.zm](mailto:security@digitalhygiene.gov.zm)
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)
3. **Timeline**: We'll acknowledge receipt within 48 hours and provide an estimated patch timeline

**Important**: Please give us 90 days to fix the issue before public disclosure.

---

## Security Best Practices

### For Users

1. **Download Verification**
   - Download .exe only from official GitHub Releases
   - Verify file hash (SHA256) when provided
   - Keep your Windows OS updated

2. **Environment Configuration**
   - Use strong database passwords (minimum 16 characters)
   - Store `.env` file securely (not in version control)
   - Use HTTPS for all web communications
   - Rotate API keys regularly

3. **Assessment Privacy**
   - Assessment results contain sensitive business information
   - Store reports securely
   - Limit access to authorized personnel

### For Developers

#### Input Validation

Always validate and sanitize user input:

```python
from pathlib import Path
import re

def validate_business_name(name: str) -> str:
    """Validate business name input."""
    if not isinstance(name, str):
        raise TypeError("Business name must be string")
    if len(name) > 255:
        raise ValueError("Business name too long (max 255 characters)")
    if not name.strip():
        raise ValueError("Business name cannot be empty")
    return name.strip()

def validate_registration_id(reg_id: str) -> str:
    """Validate registration ID format."""
    if not re.match(r'^[A-Z0-9\-]{3,50}$', reg_id):
        raise ValueError("Invalid registration ID format")
    return reg_id

def validate_file_path(base_dir: str, user_path: str) -> Path:
    """Prevent directory traversal attacks."""
    base = Path(base_dir).resolve()
    target = (base / user_path).resolve()
    
    if not str(target).startswith(str(base)):
        raise ValueError("Path traversal attempt detected")
    
    return target
```

#### SQL Injection Prevention

Use parameterized queries (SQLAlchemy ORM automatically handles this):

```python
# Good: Using SQLAlchemy ORM
from src.database.connection import Business

businesses = Business.query.filter_by(name=user_input).all()

# Good: Using raw SQL with parameters
db.session.execute(
    text("SELECT * FROM businesses WHERE name = :name"),
    {"name": user_input}
)

# Bad: String concatenation (vulnerable!)
db.session.execute(f"SELECT * FROM businesses WHERE name = '{user_input}'")
```

#### XSS Protection

Escape user input in templates:

```html
<!-- Good: Jinja2 auto-escapes by default -->
<h1>{{ business.name }}</h1>
<p>{{ assessment.recommendations | join(', ') }}</p>

<!-- Good: Explicit escaping if needed -->
<div>{{ user_input | escape }}</div>

<!-- Bad: Manually raw-ing unsafe data -->
<div>{{ user_input | safe }}</div>
```

#### Sensitive Data Logging

Never log passwords, tokens, or PII:

```python
import logging

logger = logging.getLogger(__name__)

# Good: Log non-sensitive info
logger.info(f"Assessment started for business_id: {business.id}")
logger.debug(f"Check {control_id} completed with score {score}")

# Bad: Don't log sensitive data
logger.info(f"Database credentials: {db_user}:{db_password}")  # Never!
logger.debug(f"User submitted form: {form_data}")  # Could have email

# Better: Log safely
logger.debug(f"User submitted form with {len(form_data)} fields")
```

#### Dependency Security

Regularly check for vulnerable dependencies:

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Update dependencies
pip list --outdated
pip install --upgrade package_name

# Lock dependencies for reproducibility
pip freeze > requirements.lock
```

---

## Secure Configuration

### Environment Variables

Store sensitive data in environment variables, never in code:

```python
# Good: Use environment variables
import os
from dotenv import load_dotenv

load_dotenv()

DB_PASSWORD = os.getenv("DB_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")

if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD environment variable not set")

# Bad: Hardcoded secrets
DB_PASSWORD = "super_secret_123"  # Never!
API_KEY = "sk-1234567890"  # Never!
```

### .env File Security

```bash
# .env file
DB_PASSWORD=strong-random-password-64-chars-minimum
SECRET_KEY=another-strong-random-key
DEBUG=false
```

Add to `.gitignore`:
```
.env
.env.local
.env.*.local
```

---

## Windows Application Security

### Code Signing

For production releases, sign the .exe file:

```bash
# Using Signtool (Windows SDK)
signtool sign /f cert.pfx /p password \
    /t http://timestamp.comodoca.com/authenticode \
    dist\ZambiaDigitalHygiene.exe
```

### Admin Privileges

The app should warn when admin privileges are needed:

```python
import ctypes
import os

def requires_admin():
    """Check if running with admin privileges."""
    try:
        return bool(ctypes.windll.shell.IsUserAnAdmin())
    except:
        return False

if not requires_admin():
    logger.warning("Some checks require administrator privileges")
    # Gracefully degrade functionality
```

---

## Database Security (Phase 2)

### Connection Security

```python
# Use connection pooling and timeouts
from sqlalchemy import create_engine

engine = create_engine(
    "mysql+pymysql://user:password@host/db",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    connect_args={
        "connect_timeout": 10,
        "ssl_disabled": False,  # Use SSL
    }
)
```

### User Permissions

Create database users with least privilege:

```sql
-- For application
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE ON digital_hygiene.* TO 'app_user'@'localhost';

-- For backups
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT ON digital_hygiene.* TO 'backup_user'@'localhost';

-- Don't use root for application!
```

---

## API Security (Phase 2)

### Authentication & Authorization

```python
from functools import wraps
from flask import request, jsonify
import jwt

def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        
        if not token:
            return jsonify({"error": "Missing token"}), 401
        
        try:
            payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])
            request.user = payload
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    
    return decorated
```

### Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/assess', methods=['POST'])
@limiter.limit("10 per hour")
def assess():
    """Rate limit to 10 assessments per hour per IP."""
    pass
```

### CORS Configuration

```python
from flask_cors import CORS

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": os.getenv("CORS_ORIGINS", "localhost").split(","),
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Range"],
            "max_age": 3600
        }
    }
)
```

---

## Cryptography

### Password Hashing

Use strong hashing (not MD5 or SHA-1):

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password (Phase 2 user auth)
hashed = generate_password_hash("user_password", method='pbkdf2:sha256', salt_length=32)

# Verify password
if check_password_hash(hashed, "user_input"):
    # Password matches
    pass
```

### Data Encryption

For sensitive stored data (Phase 2):

```python
from cryptography.fernet import Fernet
import os

key = os.getenv("ENCRYPTION_KEY").encode()
cipher = Fernet(key)

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive business data."""
    return cipher.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted: str) -> str:
    """Decrypt sensitive business data."""
    return cipher.decrypt(encrypted.encode()).decode()
```

---

## Secure Development Practices

### Pre-commit Hooks

Prevent accidental secrets submission:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml (see repo)
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Review

- All code changes require peer review
- Focus on security implications
- Check dependencies for vulnerabilities
- Verify input validation

### Testing

- Include security-focused tests
- Test with malicious input
- Test authorization boundaries
- Test rate limiting

```python
def test_sql_injection_protection():
    """Test that SQL injection is prevented."""
    malicious_input = "'; DROP TABLE businesses; --"
    
    # Should not raise and should not delete data
    results = Business.query.filter_by(name=malicious_input).all()
    assert results == []
    
    # Verify table still exists
    assert db.session.execute(text("SELECT COUNT(*) FROM businesses")).scalar() >= 0
```

---

## Monitoring & Alerting

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log security events
logger.warning(f"Failed authentication attempt from {ip_address}")
logger.error(f"SQL error detected: potential injection attempt")
logger.info(f"User admin accessed sensitive data")
```

### Intrusion Detection

Monitor for:
- Failed login attempts (>5 in 1 hour = block)
- SQL injection attempts
- Path traversal attempts
- Unusual data access patterns

---

## Incident Response

If a vulnerability is discovered in production:

1. **Immediately patch** and deploy fix
2. **Notify affected users**
3. **Post-mortem** and improvement plan
4. **Security audit** of related code
5. **Update documentation** with lessons learned

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [Python Security](https://python.readthedocs.io/en/latest/library/security_warnings.html)

---

## Security Checklist

Before releasing to production:

- [ ] All user input validated and sanitized
- [ ] No hardcoded secrets or credentials
- [ ] SQL injection prevention verified
- [ ] XSS protection enabled
- [ ] CORS properly configured
- [ ] Authentication/authorization tested
- [ ] Rate limiting implemented
- [ ] HTTPS enforced
- [ ] Logging doesn't expose sensitive data
- [ ] Dependencies security checked
- [ ] Code signed (for .exe)
- [ ] Security headers configured
- [ ] Error messages don't leak info
- [ ] Backup and recovery tested
- [ ] Security documentation updated

---

**Last Updated**: May 10, 2026

For security updates and advisories, subscribe to [GitHub Security Advisories](https://github.com/sakhile-bit/sakhile_final-_year_pro/security/advisories).
