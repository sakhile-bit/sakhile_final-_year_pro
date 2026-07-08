"""
Flask web application for the Zambia Digital Hygiene Assessment Tool
"""

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, jsonify, abort, Response, session,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import json
import csv
import io
import re
import secrets
from functools import wraps
from pathlib import Path
from typing import Any, Optional
import ssl
import socket
import platform
import subprocess
import time

# Optional heavy dependencies — imported lazily where used
try:
    import requests as _requests
except ImportError:  # pragma: no cover
    _requests = None

try:
    import nmap as _nmap
except ImportError:  # pragma: no cover
    _nmap = None

try:
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    BackgroundScheduler = None

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:  # pragma: no cover
    letter = SimpleDocTemplate = Paragraph = Spacer = getSampleStyleSheet = None  # type: ignore[misc]

try:
    import pyotp
    import qrcode
    import qrcode.image.svg
    _MFA_AVAILABLE = True
except ImportError:  # pragma: no cover
    pyotp = qrcode = None
    _MFA_AVAILABLE = False

from src.security.assessment.assessor import (
    DigitalHygieneAssessor,
    BusinessInfo,
    InfrastructureAssessor,
    ZambiaRiskAssessor,
)
from src.security.deployment.checker import PreDeploymentChecker
from src.reporting.generator import ReportGenerator
from src.utils.logging_config import get_logger
from src.utils.config import config, load_env_file

# Load environment variables from .env file if it exists
load_env_file('.env')

logger = get_logger(__name__)

# Initialize Flask app and extensions (application factory pattern)
app = Flask(__name__)
_secret_key = os.environ.get('SECRET_KEY') or config.web.get('secret_key')
if not _secret_key:
    # No configured key: generate an ephemeral one instead of a guessable
    # constant. Sessions won't survive restarts — set SECRET_KEY in production.
    _secret_key = secrets.token_hex(32)
    logger.warning(
        "SECRET_KEY not configured — using a random ephemeral key. "
        "Set the SECRET_KEY environment variable for production."
    )
app.config['SECRET_KEY'] = _secret_key
# Session cookies — read directly from env so dev (.env) and prod can differ
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
# Use MySQL via config or fall back to SQLite for dev/tests
app.config['SQLALCHEMY_DATABASE_URI'] = config.get_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions and bind to app immediately so that
# `flask run` (which imports the module and uses `app` directly)
# gets Flask-Login's current_user context processor registered.
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # type: ignore[assignment]
csrf = CSRFProtect(app)

# Initialize scheduler for automation (optional dependency)
scheduler = None
if BackgroundScheduler is not None:
    try:
        scheduler = BackgroundScheduler()
        scheduler.start()
    except Exception:
        scheduler = None

# User model aligned to schema (users table)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='assessor', nullable=False)  # admin | assessor | business_owner
    is_active = db.Column(db.Boolean, default=True)
    mfa_secret = db.Column(db.String(32), nullable=True)
    mfa_enabled = db.Column(db.Boolean, default=False)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = db.relationship('Business', backref=db.backref('owners', lazy='dynamic'))

    def __init__(self, username: str, email: str, role: str = 'assessor',
                 is_active: bool = True, mfa_secret: Optional[str] = None,
                 mfa_enabled: bool = False, business_id: Optional[int] = None,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.username = username
        self.email = email
        self.role = role
        self.is_active = is_active  # type: ignore[assignment]
        self.mfa_secret = mfa_secret
        self.mfa_enabled = mfa_enabled
        self.business_id = business_id

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Business(db.Model):
    __tablename__ = 'businesses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    registration_number = db.Column(db.String(50), unique=True)
    address = db.Column(db.Text)
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    industry = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, name: str, registration_number: Optional[str] = None,
                 contact_person: Optional[str] = None, contact_email: Optional[str] = None,
                 contact_phone: Optional[str] = None, industry: Optional[str] = None,
                 address: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.name = name
        self.registration_number = registration_number
        self.contact_person = contact_person
        self.contact_email = contact_email
        self.contact_phone = contact_phone
        self.industry = industry
        self.address = address


class Assessment(db.Model):
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    assessor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow)
    system_info = db.Column(db.JSON)
    controls_results = db.Column(db.JSON, nullable=False)
    total_score = db.Column(db.Integer, nullable=False)
    certification_level = db.Column(db.String(20), nullable=False)
    recommendations = db.Column(db.JSON)
    status = db.Column(db.String(20), default='completed', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = db.relationship('Business')
    assessor = db.relationship('User')

    def __init__(self, business_id: int, controls_results: Any, total_score: int,
                 certification_level: str, assessor_id: Optional[int] = None,
                 recommendations: Optional[Any] = None, status: str = 'completed',
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.business_id = business_id
        self.controls_results = controls_results
        self.total_score = total_score
        self.certification_level = certification_level
        self.assessor_id = assessor_id
        self.recommendations = recommendations
        self.status = status


class Certificate(db.Model):
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    certificate_number = db.Column(db.String(50), unique=True, nullable=False)
    issued_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    certificate_data = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assessment = db.relationship('Assessment')

    def __init__(self, assessment_id: int, certificate_number: str,
                 issued_date: Optional[Any] = None, expiry_date: Optional[Any] = None,
                 certificate_data: Optional[Any] = None, is_active: bool = True,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.assessment_id = assessment_id
        self.certificate_number = certificate_number
        self.issued_date = issued_date
        self.expiry_date = expiry_date
        self.certificate_data = certificate_data
        self.is_active = is_active

    # Backwards-compatible view helpers for templates
    @property
    def _biz(self):  # pragma: no cover
        return self.assessment.business if self.assessment else None

    @property
    def business_name(self) -> str:  # pragma: no cover - presentational
        return self._biz.name if self._biz else ''

    @property
    def business_registration(self) -> str:  # pragma: no cover - presentational
        return self._biz.registration_number if self._biz else ''

    @property
    def contact_person(self) -> str:  # pragma: no cover - presentational
        return self._biz.contact_person if self._biz else ''

    @property
    def contact_email(self) -> str:  # pragma: no cover - presentational
        return self._biz.contact_email if self._biz else ''

    @property
    def contact_phone(self) -> str:  # pragma: no cover - presentational
        return self._biz.contact_phone if self._biz else ''

    @property
    def industry(self) -> str:  # pragma: no cover - presentational
        return self._biz.industry if self._biz else ''

    @property
    def address(self) -> str:  # pragma: no cover - presentational
        return self._biz.address if self._biz else ''

    @property
    def score(self):  # pragma: no cover - compatibility alias
        return self.assessment.total_score if self.assessment else 0

    @property
    def total_possible(self):  # pragma: no cover - compatibility alias
        data = (self.assessment.controls_results if self.assessment else None) or {}
        return data.get('total_possible', 0)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')

    def __init__(self, user_id: Optional[int] = None, action: str = '',
                 resource_type: Optional[str] = None, resource_id: Optional[int] = None,
                 details: Optional[Any] = None, ip_address: Optional[str] = None,
                 user_agent: Optional[str] = None,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details = details
        self.ip_address = ip_address
        self.user_agent = user_agent


class Remediation(db.Model):
    """Tracks remediation actions for failed/warning controls in an assessment."""
    __tablename__ = 'remediations'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    control_id = db.Column(db.String(10), nullable=False)   # e.g. C03
    control_name = db.Column(db.String(100))
    status = db.Column(db.String(20), default='open')       # open | in_progress | resolved
    priority = db.Column(db.String(10), default='medium')   # low | medium | high | critical
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assessment = db.relationship('Assessment', backref=db.backref('remediations', lazy='dynamic'))
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    creator = db.relationship('User', foreign_keys=[created_by])

    def __init__(self, assessment_id: int, control_id: str, created_by: int,
                 control_name: Optional[str] = None, status: str = 'open',
                 priority: str = 'medium', assigned_to: Optional[int] = None,
                 notes: Optional[str] = None, due_date: Optional[Any] = None,
                 resolved_at: Optional[Any] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.assessment_id = assessment_id
        self.control_id = control_id
        self.created_by = created_by
        self.control_name = control_name
        self.status = status
        self.priority = priority
        self.assigned_to = assigned_to
        self.notes = notes
        self.due_date = due_date
        self.resolved_at = resolved_at


class AssessmentRequest(db.Model):
    """Business owners request assessments; assessors pick them up."""
    __tablename__ = 'assessment_requests'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assessment_tier = db.Column(db.String(20), default='full')
    status = db.Column(db.String(20), default='pending')  # pending | assigned | in_progress | completed | cancelled
    notes = db.Column(db.Text)
    preferred_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = db.relationship('Business')
    requester = db.relationship('User', foreign_keys=[requested_by])
    assessor = db.relationship('User', foreign_keys=[assigned_to])

    def __init__(self, business_id: int, requested_by: int, assessment_tier: str = 'full',
                 notes: Optional[str] = None, preferred_date: Optional[Any] = None,
                 status: str = 'pending', **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.business_id = business_id
        self.requested_by = requested_by
        self.assessment_tier = assessment_tier
        self.notes = notes
        self.preferred_date = preferred_date
        self.status = status


def _generate_cert_number() -> str:
    """Generate a unique certificate number: ZDH-YYYY-XXXXXX."""
    year = datetime.utcnow().year
    token = secrets.token_hex(3).upper()
    return f"ZDH-{year}-{token}"


def check_password_strength(password):
    """Check if password meets strength requirements."""
    if len(password) < 12:
        return False, "Password must be at least 12 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character."
    return True, "Password is strong."


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}


def create_app(db_uri: str | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        db_uri: Override the database URI (useful for tests with SQLite).
    """
    # Extensions are already bound at module level.
    # When a custom URI is supplied (e.g. SQLite in tests) we must also dispose
    # the existing engine so SQLAlchemy recreates it with the new URL on the
    # next connection — otherwise the old MySQL pool is reused even though the
    # config key has changed.
    if db_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        try:
            db.engine.dispose()
        except Exception:
            pass  # engine may not exist yet on first call

    # Session security — disable secure cookie flag in test/local mode
    if app.config.get('TESTING'):
        app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 min

    # WTF CSRF is handled by CSRFProtect extension above

    # Ensure tables exist and seed a default admin if missing (MySQL production path)
    with app.app_context():
        db.create_all()

        # Migrate existing tables: add MFA columns if missing
        try:
            from sqlalchemy import inspect as sa_inspect, text
            inspector = sa_inspect(db.engine)
            if 'users' in inspector.get_table_names():
                existing_cols = {c['name'] for c in inspector.get_columns('users')}
                if 'mfa_secret' not in existing_cols:
                    db.session.execute(text('ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(32)'))
                if 'mfa_enabled' not in existing_cols:
                    db.session.execute(text('ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT 0'))
                if 'business_id' not in existing_cols:
                    db.session.execute(text('ALTER TABLE users ADD COLUMN business_id INTEGER'))
                db.session.commit()
        except Exception as e:
            logger.warning(f'Column migration: {e}')
            db.session.rollback()

        # Read admin password from env; generate a one-time random password if
        # the variable is absent so a known default is never baked in.
        _DEFAULT_ADMIN_PW = os.environ.get('ADMIN_DEFAULT_PASSWORD', '').strip()
        if not _DEFAULT_ADMIN_PW:
            import secrets as _secrets
            _DEFAULT_ADMIN_PW = _secrets.token_urlsafe(16)
            logger.warning(
                'ADMIN_DEFAULT_PASSWORD not set — generated temporary admin password: %s  '
                '(set the env var to a strong password and restart)',
                _DEFAULT_ADMIN_PW,
            )
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@digitalhygiene.gov.zm',
                role='admin',
                is_active=True,
            )
            admin.set_password(_DEFAULT_ADMIN_PW)
            db.session.add(admin)
            db.session.commit()
            logger.info('Default admin user created')
        else:
            # Normalize hash if legacy bcrypt hash present.
            if not admin.password_hash.startswith('pbkdf2:'):
                admin.set_password(_DEFAULT_ADMIN_PW)
                db.session.commit()
                logger.info('Default admin password reset to pbkdf2 hash')

    # Register admin dashboard blueprint (only once)
    from src.web.admin import admin_bp
    if 'admin' not in app.blueprints:
        app.register_blueprint(admin_bp)

    return app


# Simple rate limiting for login
login_attempts: dict[str, list[float]] = {}


def rate_limit(max_attempts=5, window=300):  # 5 attempts per 5 minutes
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr or '0.0.0.0'
            now = time.time()
            if ip not in login_attempts:
                login_attempts[ip] = []
            login_attempts[ip] = [t for t in login_attempts[ip] if now - t < window]
            if len(login_attempts[ip]) >= max_attempts:
                flash('Too many login attempts. Try again later.', 'error')
                return render_template('login.html')
            login_attempts[ip].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/')
def index():
    """Home page — pass download URL so template can render correctly."""
    dl_url = os.environ.get(
        'DOWNLOAD_URL',
        'https://github.com/sakhile-bit/sakhile_final-_year_pro'
        '/releases/download/v1.0.0/ZambiaDigitalHygiene.exe',
    )
    return render_template('index.html', download_url=dl_url)


@app.route('/api/stats')
@login_required
def api_stats():
    """JSON stats used by the dashboard Chart.js widgets."""
    query = Assessment.query
    if current_user.role == 'business_owner' and current_user.business_id:
        query = query.filter_by(business_id=current_user.business_id)
    elif current_user.role != 'admin':
        query = query.filter_by(assessor_id=current_user.id)

    assessments = query.order_by(Assessment.assessment_date.asc()).all()

    cert_counts = {'GOLD': 0, 'SILVER': 0, 'BRONZE': 0, 'NOT CERTIFIED': 0}
    trend_labels = []
    trend_scores = []
    for a in assessments:
        cert_counts[a.certification_level] = (
            cert_counts.get(a.certification_level, 0) + 1)
        trend_labels.append(a.assessment_date.strftime('%d %b'))
        pct = round(a.total_score / 120 * 100) if a.total_score else 0
        trend_scores.append(pct)

    return jsonify({
        'cert_counts': cert_counts,
        'trend_labels': trend_labels[-12:],
        'trend_scores': trend_scores[-12:],
        'total': len(assessments),
        'avg_score': round(
            sum(a.total_score for a in assessments) / len(assessments), 1
        ) if assessments else 0,
    })


@app.route('/login', methods=['GET', 'POST'])
@rate_limit()
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Password hygiene: check for strong password
        def is_strong_password(pw):
            return (
                len(pw) >= 10 and
                re.search(r'[A-Z]', pw) and
                re.search(r'[a-z]', pw) and
                re.search(r'\d', pw) and
                re.search(r'[^A-Za-z0-9]', pw)
            )

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Account is disabled. Contact an administrator.', 'error')
                return render_template('login.html')

            # MFA gate: if user has MFA enabled, redirect to verification
            if getattr(user, 'mfa_enabled', False) and _MFA_AVAILABLE:
                session['mfa_user_id'] = user.id
                return redirect(url_for('mfa_verify'))

            login_user(user)
            # Log login event
            _ua = request.user_agent.string or ''
            log = AuditLog(
                user_id=user.id, action='login',
                resource_type='user', resource_id=user.id,
                details={'ip': request.remote_addr, 'ua': _ua},
                ip_address=request.remote_addr,
                user_agent=_ua,
            )
            db.session.add(log)
            db.session.commit()

            # Check if first login for admin
            # if user.role == 'admin' and user.first_login:
            #     flash('Please change your default password.', 'warning')
            #     return redirect(url_for('change_password'))

            return redirect(url_for('dashboard'))

        flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('index'))


# ------------------------------------------------------------------
# Self-Registration
# ------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Public self-registration for business owners and assessors."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        role = request.form.get('role', 'business_owner')

        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        is_strong, msg = check_password_strength(password)
        if not is_strong:
            flash(msg, 'error')
            return render_template('register.html')
        if role not in ('business_owner', 'assessor'):
            role = 'business_owner'
        if User.query.filter((User.username == username) | (User.email == email)).first():  # type: ignore[arg-type]
            flash('Username or email already taken.', 'error')
            return render_template('register.html')

        user = User(username=username, email=email, role=role, is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        log = AuditLog(user_id=user.id, action='register', resource_type='user',
                       resource_id=user.id, details={'role': role, 'ip': request.remote_addr})
        db.session.add(log)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# ------------------------------------------------------------------
# Business Onboarding – business owners manage their business profile
# ------------------------------------------------------------------
@app.route('/my-business', methods=['GET', 'POST'])
@login_required
def my_business():
    """Business owner registers / edits their business profile."""
    if current_user.role not in ('business_owner', 'admin'):
        flash('Only business owners can access this page.', 'error')
        return redirect(url_for('dashboard'))

    business = None
    if current_user.business_id:
        business = Business.query.get(current_user.business_id)

    if request.method == 'POST':
        name = request.form.get('business_name', '').strip()
        reg_number = request.form.get('registration_number', '').strip()
        contact_person = request.form.get('contact_person', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        industry = request.form.get('industry', '')
        address = request.form.get('address', '').strip()

        if not name or not reg_number:
            flash('Business name and registration number are required.', 'error')
            return render_template('my_business.html', business=business)

        if business:
            # Update existing
            business.name = name
            business.registration_number = reg_number
            business.contact_person = contact_person
            business.contact_email = contact_email
            business.contact_phone = contact_phone
            business.industry = industry
            business.address = address
        else:
            # Check for duplicate registration number
            existing = Business.query.filter_by(registration_number=reg_number).first()
            if existing:
                flash('A business with this registration number already exists.', 'error')
                return render_template('my_business.html', business=business)
            business = Business(
                name=name, registration_number=reg_number,
                contact_person=contact_person, contact_email=contact_email,
                contact_phone=contact_phone, industry=industry, address=address)
            db.session.add(business)
            db.session.flush()
            current_user.business_id = business.id

        db.session.commit()
        flash('Business profile saved successfully!', 'success')
        return redirect(url_for('my_business'))

    # Gather assessments & certificates for this business
    assessments = []
    certificates = []
    if business:
        assessments = (
            Assessment.query
            .filter_by(business_id=business.id)
            .order_by(Assessment.created_at.desc())
            .all()
        )
        certificates = (
            Certificate.query.join(Assessment)
            .filter(
                Assessment.business_id == business.id,
                Certificate.is_active.is_(True),  # type: ignore[union-attr]
            )
            .all()
        )

    return render_template(
        'my_business.html',
        business=business,
        assessments=assessments,
        certificates=certificates,
    )


# ------------------------------------------------------------------
# Assessment Request Flow
# ------------------------------------------------------------------
@app.route('/request-assessment', methods=['GET', 'POST'])
@login_required
def request_assessment():
    """Business owners request an assessment for their business."""
    if current_user.role != 'business_owner':
        flash('Only business owners can request assessments.', 'error')
        return redirect(url_for('dashboard'))

    if not current_user.business_id:
        flash('Please register your business first.', 'warning')
        return redirect(url_for('my_business'))

    business = Business.query.get(current_user.business_id)
    if not business:
        flash('Business not found. Please register your business first.', 'warning')
        return redirect(url_for('my_business'))

    if request.method == 'POST':
        tier = request.form.get('assessment_tier', 'full')
        notes = request.form.get('notes', '').strip()
        preferred_date_str = request.form.get('preferred_date', '')
        preferred_date = None
        if preferred_date_str:
            try:
                preferred_date = datetime.strptime(preferred_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        ar = AssessmentRequest(
            business_id=business.id,
            requested_by=current_user.id,
            assessment_tier=tier,
            notes=notes,
            preferred_date=preferred_date,
            status='pending')
        db.session.add(ar)
        db.session.commit()

        flash('Assessment request submitted! An assessor will be assigned soon.', 'success')
        return redirect(url_for('my_business'))

    return render_template('request_assessment.html', business=business)


@app.route('/assessment-requests')
@login_required
def assessment_requests():
    """Assessors and admins view pending assessment requests."""
    if current_user.role not in ('assessor', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    if current_user.role == 'admin':
        requests_list = AssessmentRequest.query.order_by(AssessmentRequest.created_at.desc()).all()
    else:
        # Assessors see pending + their assigned requests
        requests_list = AssessmentRequest.query.filter(
            (AssessmentRequest.status == 'pending') |
            (AssessmentRequest.assigned_to == current_user.id)
        ).order_by(AssessmentRequest.created_at.desc()).all()

    return render_template('assessment_requests.html', requests=requests_list)


@app.route('/accept-request/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    """Assessor accepts a pending assessment request."""
    if current_user.role not in ('assessor', 'admin'):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    ar = AssessmentRequest.query.get_or_404(request_id)
    if ar.status != 'pending':
        flash('This request has already been processed.', 'warning')
        return redirect(url_for('assessment_requests'))

    ar.assigned_to = current_user.id
    ar.status = 'assigned'
    db.session.commit()

    flash(f'You have been assigned to assess {ar.business.name}.', 'success')
    return redirect(url_for('assessment_requests'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Role-based assessment dashboard"""
    query = Assessment.query
    pending_requests = []

    if current_user.role == 'admin':
        # Admins see everything
        pass
    elif current_user.role == 'business_owner':
        # Business owners see their own business assessments
        if current_user.business_id:
            query = query.filter_by(business_id=current_user.business_id)
        else:
            query = query.filter_by(id=-1)  # no results
        # Show their pending requests
        pending_requests = AssessmentRequest.query.filter_by(
            requested_by=current_user.id
        ).order_by(AssessmentRequest.created_at.desc()).limit(5).all()
    else:
        # Assessors see assessments they performed
        query = query.filter_by(assessor_id=current_user.id)
    assessments = query.order_by(Assessment.created_at.desc()).all()

    # Digital hygiene tips
    tips = [
        "Use strong, unique passwords for every account.",
        "Enable multi-factor authentication wherever possible.",
        "Keep your software and operating system up to date.",
        "Regularly back up important data to secure locations.",
        "Be cautious of phishing emails and suspicious links.",
        "Review your account activity and audit logs frequently.",
        "Limit admin access and use least privilege.",
        "Encrypt sensitive data at rest and in transit.",
        "Log out of unused sessions and devices.",
        "Report any security incidents promptly."
    ]
    import random
    tip = random.choice(tips)

    # Mobile device security tips
    MOBILE_DEVICE_TIPS = [
        'Always use a screen lock (PIN, password, or fingerprint).',
        'Install apps only from trusted sources (Google Play Store).',
        'Keep your device OS and apps updated.',
        'Enable device encryption if available.',
        'Do not share sensitive business info over unsecured apps.',
        'Regularly review app permissions.',
        'Avoid using public Wi-Fi for business transactions.',
        'Install reputable mobile security apps.',
        'Backup important data to secure cloud or offline storage.',
        'Be cautious of SMS/WhatsApp phishing links.'
    ]

    # Calculate statistics
    total_assessments = len(assessments)
    avg_score = sum(a.total_score for a in assessments) / total_assessments if total_assessments > 0 else 0
    certification_counts = {}
    for assessment in assessments:
        cert = assessment.certification_level
        certification_counts[cert] = certification_counts.get(cert, 0) + 1

    stats = {
        'total_assessments': total_assessments,
        'average_score': round(avg_score, 1),
        'certification_counts': certification_counts
    }

    reminders = []
    # Expiring certificates
    soon = datetime.utcnow() + timedelta(days=30)
    expiring = (
        Certificate.query
        .filter(
            Certificate.expiry_date <= soon,  # type: ignore[operator]
            Certificate.is_active.is_(True),  # type: ignore[union-attr]
        )
        .all()
    )
    if expiring:
        reminders.append(f"{len(expiring)} certificate(s) expiring within 30 days.")
    # Periodic reassessment (every 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    old_assessments = Assessment.query.filter(
        Assessment.assessment_date <= six_months_ago,
        Assessment.assessor_id == current_user.id,
    ).count()
    if old_assessments:
        reminders.append(f"{old_assessments} assessment(s) due for reassessment.")

    return render_template(
        'dashboard.html',
        assessments=assessments,
        stats=stats,
        tip=tip,
        reminders=reminders,
        mobile_device_tips=MOBILE_DEVICE_TIPS,
        pending_requests=pending_requests,
    )


@app.route('/assess', methods=['GET', 'POST'])
@login_required
def assess():
    """Assessment form"""
    if request.method == 'POST':
        try:
            # Get form data
            business_info = BusinessInfo(
                name=request.form['business_name'],
                id=request.form['business_id'],
                contact_person=request.form.get('contact_person'),
                contact_email=request.form.get('contact_email'),
                contact_phone=request.form.get('contact_phone'),
                industry=request.form.get('industry'),
                address=request.form.get('address'),
                province=request.form.get('province'),
                num_employees=int(request.form.get('num_employees') or 0),
            )

            # Collect manual answers (C06-C15) from form
            manual_keys = [
                'C06_security_training', 'C07_access_control',
                'C08_incident_response', 'C09_encryption',
                'C10_mobile_security', 'C11_physical_security',
                'C12_network_security', 'C13_acceptable_use',
                'C14_vendor_risk', 'C15_regulatory_compliance',
            ]
            assessment_tier = request.form.get('assessment_tier', 'automated')
            manual_answers = {}
            if assessment_tier in ('full', 'manual_only'):
                for key in manual_keys:
                    val = request.form.get(key)
                    if val is not None:
                        manual_answers[key] = int(val)

            # Upsert business record
            business = Business.query.filter_by(registration_number=business_info.id).first()
            if not business:
                business = Business(
                    name=business_info.name,
                    registration_number=business_info.id,
                    contact_person=business_info.contact_person,
                    contact_email=business_info.contact_email,
                    contact_phone=business_info.contact_phone,
                    industry=business_info.industry,
                    address=business_info.address,
                )
                db.session.add(business)
                db.session.flush()
            else:
                business.name = business_info.name
                business.contact_person = business_info.contact_person
                business.contact_email = business_info.contact_email
                business.contact_phone = business_info.contact_phone
                business.industry = business_info.industry
                business.address = business_info.address

            # Run assessment with manual answers and tier
            assessor = DigitalHygieneAssessor(
                business_info,
                manual_answers=manual_answers if manual_answers else None,
                assessment_tier=assessment_tier,
            )
            results = assessor.run_assessment()

            # Save to database
            controls_payload = {k: v.__dict__ for k, v in results.controls.items()}
            assessment = Assessment(
                business_id=business.id,
                assessor_id=current_user.id,
                controls_results={
                    'controls': controls_payload,
                    'total_possible': results.total_possible,
                    'critical_failures': getattr(results, 'critical_failures', 0),
                    'assessment_tier': getattr(results, 'assessment_tier', assessment_tier),
                },
                total_score=results.score,
                certification_level=results.certification_level,
                recommendations=results.recommendations,
                status='completed'
            )

            db.session.add(assessment)
            db.session.commit()

            # Auto-issue certificate for passing assessments
            if results.certification_level != 'NOT CERTIFIED':
                cert_num = _generate_cert_number()
                months = 6 if results.certification_level == 'BRONZE' else 12
                from datetime import date
                cert = Certificate(
                    assessment_id=assessment.id,
                    certificate_number=cert_num,
                    issued_date=date.today(),
                    expiry_date=(datetime.utcnow() + timedelta(days=months * 30)).date(),
                    certificate_data={
                        'business_name': business.name,
                        'level': results.certification_level,
                        'score': results.score,
                        'total_possible': results.total_possible,
                        'assessor': current_user.username,
                    },
                    is_active=True,
                )
                db.session.add(cert)
                db.session.commit()
                log = AuditLog(
                    user_id=current_user.id, action='certificate_issued',
                    resource_type='certificate', resource_id=cert.id,
                    details={'cert_number': cert_num, 'level': results.certification_level,
                             'business': business.name, 'ip': request.remote_addr},
                )
                db.session.add(log)
                db.session.commit()
                flash(f'Certificate {cert_num} issued ({results.certification_level})!', 'success')

            flash('Assessment completed successfully!', 'success')
            return redirect(url_for('results', assessment_id=assessment.id))

        except Exception as e:
            logger.error(f"Assessment error: {e}")
            flash('Assessment failed. Please try again or contact support.', 'error')

    return render_template('assess.html')


@app.route('/results/<int:assessment_id>')
@login_required
def results(assessment_id):
    """Assessment results"""
    query = Assessment.query
    if current_user.role == 'admin':
        query = query.filter_by(id=assessment_id)
    elif current_user.role == 'business_owner' and current_user.business_id:
        query = query.filter_by(id=assessment_id, business_id=current_user.business_id)
    else:
        query = query.filter_by(id=assessment_id, assessor_id=current_user.id)
    assessment = query.first_or_404()

    # Parse assessment data
    data = assessment.controls_results or {}
    controls = data.get('controls', {})
    total_possible = data.get('total_possible', 0)
    critical_failures = data.get('critical_failures', 0)
    assessment_tier = data.get('assessment_tier', 'automated')
    result_obj = type('Results', (), {
        'score': assessment.total_score,
        'total_possible': total_possible,
        'certification_level': assessment.certification_level,
        'controls': {k: type('Control', (), v) for k, v in controls.items()},
        'recommendations': assessment.recommendations or [],
        'critical_failures': critical_failures,
        'assessment_tier': assessment_tier,
    })()

    business_info = BusinessInfo(
        name=assessment.business.name if assessment.business else '',
        id=assessment.business.registration_number if assessment.business else '',
        contact_person=assessment.business.contact_person if assessment.business else '',
        contact_email=assessment.business.contact_email if assessment.business else '',
        contact_phone=assessment.business.contact_phone if assessment.business else '',
        industry=assessment.business.industry if assessment.business else '',
        address=assessment.business.address if assessment.business else ''
    )

    # Fetch associated certificate (if any)
    certificate = Certificate.query.filter_by(assessment_id=assessment_id, is_active=True).first()

    return render_template('results.html', results=result_obj, business_info=business_info,
                           assessment_id=assessment_id, certificate=certificate)


@app.route('/download/<int:assessment_id>/<format>')
@login_required
def download_report(assessment_id, format):
    """Download assessment report"""
    query = Assessment.query
    if current_user.role == 'admin':
        query = query.filter_by(id=assessment_id)
    elif current_user.role == 'business_owner' and current_user.business_id:
        query = query.filter_by(id=assessment_id, business_id=current_user.business_id)
    else:
        query = query.filter_by(id=assessment_id, assessor_id=current_user.id)
    assessment = query.first_or_404()

    # Parse assessment data
    data = assessment.controls_results or {}
    controls = data.get('controls', {})
    total_possible = data.get('total_possible', 0)
    critical_failures = data.get('critical_failures', 0)
    results = type('Results', (), {
        'score': assessment.total_score,
        'total_possible': total_possible,
        'certification_level': assessment.certification_level,
        'controls': {k: type('Control', (), v) for k, v in controls.items()},
        'recommendations': assessment.recommendations or [],
        'critical_failures': critical_failures,
    })()

    business_info = BusinessInfo(
        name=assessment.business.name if assessment.business else '',
        id=assessment.business.registration_number if assessment.business else '',
        contact_person=assessment.business.contact_person if assessment.business else '',
        contact_email=assessment.business.contact_email if assessment.business else '',
        contact_phone=assessment.business.contact_phone if assessment.business else '',
        industry=assessment.business.industry if assessment.business else '',
        address=assessment.business.address if assessment.business else ''
    )

    # Generate report
    generator = ReportGenerator()

    def _safe_report_path(path_str):
        # Serve only files that resolve inside the reports output directory
        resolved = Path(path_str).resolve()
        reports_root = generator.output_dir.resolve()
        if reports_root not in resolved.parents and resolved != reports_root:
            logger.error("Report path escaped reports directory: %s", resolved)
            abort(404)
        return resolved

    if format == 'pdf':
        report_path = generator.generate_pdf_report(results, business_info, f"assessment_{assessment_id}")
        return send_file(_safe_report_path(report_path), as_attachment=True,
                         download_name=f"assessment_{assessment_id}.pdf")
    elif format == 'html':
        report_path = generator.generate_html_report(results, business_info, f"assessment_{assessment_id}")
        return send_file(_safe_report_path(report_path), as_attachment=True,
                         download_name=f"assessment_{assessment_id}.html")
    elif format == 'json':
        report_data = generator.generate_json_report(results, business_info)
        buffer = io.BytesIO()
        buffer.write(json.dumps(report_data, indent=2).encode())
        buffer.seek(0)
        return send_file(
            buffer, as_attachment=True,
            download_name=f"assessment_{assessment_id}.json",
            mimetype='application/json',
        )
    elif format == 'csv':
        report_data = generator.generate_csv_report(results, business_info)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerows(report_data)
        buffer.seek(0)
        return send_file(
            io.BytesIO(buffer.getvalue().encode()),
            as_attachment=True,
            download_name=f"assessment_{assessment_id}.csv",
            mimetype='text/csv',
        )

    flash('Invalid format requested', 'error')
    return redirect(url_for('results', assessment_id=assessment_id))


@app.route('/api/assessments')
@login_required
def api_assessments():
    """API endpoint for assessments"""
    query = Assessment.query
    if current_user.role != 'admin':
        query = query.filter_by(assessor_id=current_user.id)
    assessments = query.all()
    return jsonify([{
        'id': a.id,
        'business_name': a.business.name if a.business else '',
        'score': a.total_score,
        'certification_level': a.certification_level,
        'created_at': a.created_at.isoformat()
    } for a in assessments])


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated

# Legacy audit-logs route removed – now served by the admin blueprint at /admin/audit-logs


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_pw = request.form.get('old_password')
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')
        if not current_user.check_password(old_pw):
            flash('Old password incorrect.', 'error')
        elif new_pw != confirm_pw:
            flash('New passwords do not match.', 'error')
        elif (
            not new_pw
            or len(new_pw) < 10
            or not re.search(r'[A-Z]', new_pw)
            or not re.search(r'[a-z]', new_pw)
            or not re.search(r'\d', new_pw)
            or not re.search(r'[^A-Za-z0-9]', new_pw)
        ):
            flash('New password does not meet hygiene requirements.', 'error')
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            log = AuditLog(
                user_id=current_user.id, action='change_password',
                resource_type='user', resource_id=current_user.id,
                details={'ip': request.remote_addr},
            )
            db.session.add(log)
            db.session.commit()
            return redirect(url_for('dashboard'))
    return render_template('change_password.html')


@app.route('/profile')
@login_required
def profile():
    recent_logins = (
        AuditLog.query
        .filter_by(user_id=current_user.id, action='login')
        .order_by(AuditLog.timestamp.desc())
        .limit(5).all()
    )
    return render_template('profile.html', user=current_user, recent_logins=recent_logins)


@app.route('/export-data/<format>')
@login_required
def export_data(format):
    assessments = Assessment.query.filter_by(assessor_id=current_user.id).all()
    if format == 'json':
        data = [{
            'id': a.id,
            'business': a.business.name if a.business else '',
            'score': a.total_score,
            'certification_level': a.certification_level,
            'date': a.assessment_date.isoformat()
        } for a in assessments]
        return jsonify(data)
    elif format == 'csv':
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['ID', 'Business', 'Score', 'Level', 'Date'])
        for a in assessments:
            biz_name = a.business.name if a.business else ''
            writer.writerow([
                a.id, biz_name, a.total_score,
                a.certification_level,
                a.assessment_date.strftime('%Y-%m-%d'),
            ])
        buffer.seek(0)
        return send_file(
            io.BytesIO(buffer.getvalue().encode()),
            as_attachment=True,
            download_name='my_assessments.csv',
            mimetype='text/csv',
        )
    else:
        abort(400)


@app.route('/report-incident', methods=['GET', 'POST'])
@login_required
def report_incident():
    if request.method == 'POST':
        desc = request.form.get('description')
        log = AuditLog(
            user_id=current_user.id, action='report_incident',
            resource_type='incident',
            details={
                'description': desc,
                'ip': request.remote_addr,
                'ua': request.user_agent.string,
            },
        )
        db.session.add(log)
        db.session.commit()
        flash('Incident reported. Thank you!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('report_incident.html')


@app.route('/mfa-setup', methods=['GET', 'POST'])
@login_required
def mfa_setup():
    """Set up TOTP-based multi-factor authentication."""
    if not _MFA_AVAILABLE:
        flash('MFA requires pyotp and qrcode packages. Install them via: pip install pyotp qrcode[pil]', 'warning')
        return render_template('mfa_setup.html', mfa_available=False, mfa_enabled=current_user.mfa_enabled)

    assert pyotp is not None
    assert qrcode is not None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'enable':
            # Generate a new secret and store it (not yet enabled until verified)
            secret = pyotp.random_base32()
            current_user.mfa_secret = secret
            db.session.commit()
            # Generate QR code
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=current_user.username,
                issuer_name='Zambia Digital Hygiene'
            )
            # Create QR code as base64 PNG
            import base64
            qr = qrcode.QRCode(version=1, box_size=6, border=4)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            buf = io.BytesIO()
            img.save(buf, format='PNG')  # type: ignore[call-arg]
            qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return render_template('mfa_setup.html', mfa_available=True, mfa_enabled=False,
                                   qr_code=qr_b64, secret=secret, step='verify')
        elif action == 'verify':
            code = request.form.get('mfa_code', '').strip()
            if current_user.mfa_secret:
                totp = pyotp.TOTP(current_user.mfa_secret)
                if totp.verify(code, valid_window=1):
                    current_user.mfa_enabled = True
                    db.session.commit()
                    log = AuditLog(user_id=current_user.id, action='mfa_enabled',
                                   resource_type='user', resource_id=current_user.id,
                                   details={'ip': request.remote_addr})
                    db.session.add(log)
                    db.session.commit()
                    flash('MFA enabled successfully!', 'success')
                    return redirect(url_for('profile'))
                else:
                    flash('Invalid MFA code. Please try again.', 'error')
                    return redirect(url_for('mfa_setup'))
            else:
                flash('No MFA secret found. Please start setup again.', 'error')
                return redirect(url_for('mfa_setup'))
        elif action == 'disable':
            current_user.mfa_enabled = False
            current_user.mfa_secret = None
            db.session.commit()
            log = AuditLog(user_id=current_user.id, action='mfa_disabled',
                           resource_type='user', resource_id=current_user.id,
                           details={'ip': request.remote_addr})
            db.session.add(log)
            db.session.commit()
            flash('MFA has been disabled.', 'info')
            return redirect(url_for('profile'))

    return render_template('mfa_setup.html', mfa_available=True, mfa_enabled=current_user.mfa_enabled)


@app.route('/mfa-verify', methods=['GET', 'POST'])
@rate_limit(max_attempts=5, window=300)
def mfa_verify():
    """Verify MFA code during login."""
    user_id = session.get('mfa_user_id')
    if not user_id:
        return redirect(url_for('login'))

    if request.method == 'POST':
        code = request.form.get('mfa_code', '').strip()
        user = User.query.get(user_id)
        if user and user.mfa_secret and _MFA_AVAILABLE and pyotp is not None:
            totp = pyotp.TOTP(user.mfa_secret)
            if totp.verify(code, valid_window=1):
                session.pop('mfa_user_id', None)
                login_user(user)
                _mfa_ua = request.user_agent.string or ''
                log = AuditLog(user_id=user.id, action='login', resource_type='user',
                               resource_id=user.id,
                               details={'ip': request.remote_addr, 'ua': _mfa_ua, 'mfa': True},
                               ip_address=request.remote_addr,
                               user_agent=_mfa_ua)
                db.session.add(log)
                db.session.commit()
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid MFA code. Please try again.', 'error')
        else:
            flash('MFA verification failed.', 'error')
            return redirect(url_for('login'))

    return render_template('mfa_verify.html')


@app.route('/zambia-assessment', methods=['GET', 'POST'])
@login_required
def zambia_assessment():
    sectors = ['SME', 'Mobile Money Agent', 'Retail', 'Agriculture', 'Other']
    languages = ['English', 'Bemba', 'Nyanja', 'Tonga', 'Lozi']
    tips = [
        'Use strong passwords and enable MFA.',
        'Beware of SIM swap and mobile money scams.',
        'Regularly backup business data.',
        'Follow ZICTA and Zambia CERT advisories.',
        'Comply with Data Protection Act, 2021.'
    ] + [
        'Always use a screen lock (PIN, password, or fingerprint).',
        'Install apps only from trusted sources (Google Play Store).',
        'Keep your device OS and apps updated.',
        'Enable device encryption if available.',
        'Do not share sensitive business info over unsecured apps.',
        'Regularly review app permissions.',
        'Avoid using public Wi-Fi for business transactions.',
        'Install reputable mobile security apps.',
        'Backup important data to secure cloud or offline storage.',
        'Be cautious of SMS/WhatsApp phishing links.'
    ]
    if request.method == 'POST':
        answers = request.form.to_dict()
        assessor = ZambiaRiskAssessor()
        result = assessor.assess(answers)
        # Save assessment, log device/location, etc.
        flash('Assessment completed. See findings below.', 'success')
        return render_template('zambia_assessment_results.html', result=result, tips=tips)
    return render_template('zambia_assessment.html', sectors=sectors, languages=languages, tips=tips)


@app.route('/report-zambia-incident', methods=['GET', 'POST'])
@login_required
def report_zambia_incident():
    zicta_url = 'https://www.zicta.zm/'
    cert_url = 'https://www.cert.gov.zm/'
    if request.method == 'POST':
        # In future: send report to ZICTA/CERT
        flash('Incident report submitted. For urgent cases, contact ZICTA or CERT.', 'info')
        return redirect(zicta_url)
    return render_template('report_zambia_incident.html', zicta_url=zicta_url, cert_url=cert_url)

# ------------------------------------------------------------------
# Remediation Tracking
# ------------------------------------------------------------------


@app.route('/remediation/<int:assessment_id>')
@login_required
def remediation_list(assessment_id):
    """View and manage remediation tasks for an assessment."""
    query = Assessment.query
    if current_user.role == 'admin':
        query = query.filter_by(id=assessment_id)
    elif current_user.role == 'business_owner' and current_user.business_id:
        query = query.filter_by(id=assessment_id, business_id=current_user.business_id)
    else:
        query = query.filter_by(id=assessment_id, assessor_id=current_user.id)
    assessment = query.first_or_404()

    remediations = Remediation.query.filter_by(assessment_id=assessment_id).order_by(
        Remediation.created_at.desc()
    ).all()

    # Controls that failed or had warnings – auto-suggest remediations
    data = assessment.controls_results or {}
    controls = data.get('controls', {})
    gap_controls = [
        (k, v) for k, v in controls.items()
        if v.get('status') in ('FAIL', 'WARNING', 'ERROR')
    ]

    return render_template(
        'remediation.html',
        assessment=assessment,
        remediations=remediations,
        gap_controls=gap_controls,
        now=datetime.utcnow(),
    )


@app.route('/remediation/<int:assessment_id>/create', methods=['POST'])
@login_required
def remediation_create(assessment_id):
    """Create a remediation task for a failed/warning control."""
    query = Assessment.query
    if current_user.role == 'admin':
        query = query.filter_by(id=assessment_id)
    elif current_user.role == 'business_owner' and current_user.business_id:
        query = query.filter_by(id=assessment_id, business_id=current_user.business_id)
    else:
        query = query.filter_by(id=assessment_id, assessor_id=current_user.id)
    _ = query.first_or_404()  # raises 404 if not found / no access

    control_id = request.form.get('control_id', '').strip()
    control_name = request.form.get('control_name', '').strip()
    notes = request.form.get('notes', '').strip()
    priority = request.form.get('priority', 'medium')
    due_str = request.form.get('due_date', '')
    due_date = None
    if due_str:
        try:
            due_date = datetime.strptime(due_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    if not control_id:
        flash('Control ID is required.', 'error')
        return redirect(url_for('remediation_list', assessment_id=assessment_id))

    rem = Remediation(
        assessment_id=assessment_id,
        control_id=control_id,
        control_name=control_name,
        notes=notes,
        priority=priority,
        due_date=due_date,
        status='open',
        created_by=current_user.id,
    )
    db.session.add(rem)
    log = AuditLog(
        user_id=current_user.id, action='remediation_created',
        resource_type='remediation', resource_id=None,
        details={'control_id': control_id, 'assessment_id': assessment_id, 'ip': request.remote_addr},
    )
    db.session.add(log)
    db.session.commit()
    flash(f'Remediation task created for {control_id}.', 'success')
    return redirect(url_for('remediation_list', assessment_id=assessment_id))


@app.route('/remediation/update/<int:rem_id>', methods=['POST'])
@login_required
def remediation_update(rem_id):
    """Update status/notes of a remediation task."""
    rem = Remediation.query.get_or_404(rem_id)
    new_status = request.form.get('status', rem.status)
    new_notes = request.form.get('notes', rem.notes)
    rem.status = new_status
    rem.notes = new_notes
    if new_status == 'resolved' and not rem.resolved_at:
        rem.resolved_at = datetime.utcnow()
    log = AuditLog(
        user_id=current_user.id, action='remediation_updated',
        resource_type='remediation', resource_id=rem.id,
        details={'status': new_status, 'ip': request.remote_addr},
    )
    db.session.add(log)
    db.session.commit()
    flash('Remediation task updated.', 'success')
    return redirect(url_for('remediation_list', assessment_id=rem.assessment_id))


def check_outdated_software():
    """Check for outdated Python packages."""
    try:
        result = subprocess.run(
            [platform.system() == 'Windows' and 'pip' or 'pip3', 'list', '--outdated', '--format=json'],
            capture_output=True, text=True, timeout=30, shell=(platform.system() == 'Windows')
        )
        if result.returncode == 0 and result.stdout.strip():
            packages = json.loads(result.stdout)
            return [f"{p['name']} ({p['version']} → {p['latest_version']})" for p in packages[:10]]
        return []
    except Exception:
        return ['Unable to check — pip not available']


def check_weak_passwords():
    """Check for user accounts with weak/default passwords."""
    weak = []
    try:
        users = User.query.all()
        common = ['admin123', 'password', '123456', 'password123', 'admin', 'test', 'letmein']
        for u in users:
            for pw in common:
                if u.check_password(pw):
                    weak.append(u.username)
                    break
    except Exception:
        pass
    return weak if weak else []


def check_antivirus_status():
    """Query OS for antivirus status."""
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                'powershell -Command "Get-MpComputerStatus | Select-Object -ExpandProperty AntivirusEnabled"',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and 'True' in result.stdout:
                return 'Windows Defender enabled'
            return 'Antivirus may not be active'
        elif platform.system() == 'Linux':
            for av in ['clamav', 'clamd']:
                r = subprocess.run(['which', av], capture_output=True, text=True)
                if r.returncode == 0:
                    return f'{av} detected'
            return 'No known antivirus detected'
        return 'Check manually for your OS'
    except Exception as e:
        return f'Check error: {e}'


def check_disk_encryption():
    """Check disk encryption status."""
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                'manage-bde -status C:',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and 'Fully Encrypted' in result.stdout:
                return 'BitLocker enabled on C:'
            elif result.returncode == 0:
                return 'BitLocker not fully enabled'
            return 'Unable to determine BitLocker status'
        elif platform.system() == 'Linux':
            result = subprocess.run('lsblk -o NAME,TYPE,MOUNTPOINT', shell=True, capture_output=True, text=True)
            if 'crypt' in result.stdout:
                return 'LUKS encryption detected'
            return 'No disk encryption detected'
        return 'Check manually for your OS'
    except Exception as e:
        return f'Check error: {e}'


def check_admin_accounts():
    """List admin accounts in the application."""
    try:
        admins = User.query.filter_by(role='admin').all()
        return [u.username for u in admins]
    except Exception:
        return ['Unable to query accounts']


def check_suspicious_processes():
    """Check for potentially suspicious processes."""
    suspicious = []
    try:
        import psutil
        known_suspicious = ['cryptominer', 'xmrig', 'coinhive', 'keylogger', 'trojan']
        for proc in psutil.process_iter(['name']):
            name = (proc.info['name'] or '').lower()
            for s in known_suspicious:
                if s in name:
                    suspicious.append(proc.info['name'])
        return suspicious if suspicious else []
    except ImportError:
        return ['psutil not installed — cannot scan processes']
    except Exception:
        return []


def check_ssl_tls(domain='localhost'):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=2) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                expiry = cert['notAfter'] if cert else 'unknown'
                return f"SSL/TLS enabled, expires: {expiry}"
    except Exception as e:
        return f"SSL/TLS not detected: {e}"


def check_dns_resolution(domain='localhost'):
    if not domain:
        return 'No domain provided'
    try:
        infos = socket.getaddrinfo(domain, None)
        addresses = sorted({item[4][0] for item in infos})
        if not addresses:
            return 'No DNS records found'
        return f"Resolves to {', '.join(str(a) for a in addresses)}"
    except Exception as e:
        return f"DNS resolution failed: {e}"


def check_http_to_https(domain='localhost'):
    if not domain:
        return 'No domain provided'
    if domain in ('localhost', '127.0.0.1'):
        return 'Local host — skip HTTPS redirect check'
    if _requests is None:
        return 'requests library not available'
    try:
        url = f'http://{domain}'
        response = _requests.get(url, allow_redirects=True, timeout=5)
        final = response.url
        if final.startswith('https://'):
            return f'HTTP redirects to HTTPS ({final})'
        return f'HTTP does not redirect to HTTPS (final: {final})'
    except Exception as e:
        return f'HTTPS redirect check failed: {e}'


def check_backup_status(path='/backups'):
    try:
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            if files:
                latest = max([os.path.getmtime(os.path.join(path, f)) for f in files])
                last_backup = datetime.fromtimestamp(latest)
                return f"Last backup: {last_backup.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                return "No backup files found"
        else:
            return "Backup folder not found"
    except Exception as e:
        return f"Backup check error: {e}"


def check_patch_status():
    try:
        if platform.system() == 'Windows':
            result = subprocess.run('wmic qfe get HotFixID,InstalledOn', shell=True, capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else "Patch status unavailable"
        else:
            result = subprocess.run('apt list --upgradable', shell=True, capture_output=True, text=True)
            upgradable = [line for line in result.stdout.split('\n') if 'upgradable' in line]
            return f"Upgradable: {len(upgradable)} packages" if upgradable else "All packages up to date"
    except Exception as e:
        return f"Patch check error: {e}"


def get_external_ip():
    try:
        if _requests is None:
            return 'requests library not available'
        r = _requests.get('https://api.ipify.org?format=json', timeout=2)
        return r.json().get('ip', 'Unknown')
    except Exception as e:
        return f"IP check error: {e}"


def run_vulnerability_scan(target='localhost'):
    try:
        if _nmap is None:
            return ['nmap library not available — install python-nmap and nmap binary']
        nm = _nmap.PortScanner()
        nm.scan(target, arguments='-sV --top-ports 10')
        vulns = []
        for host in nm.all_hosts():
            for proto in nm[host].all_protocols():
                for port in nm[host][proto]:
                    service = nm[host][proto][port]['name']
                    vulns.append(f"{service} on port {port}")
        return vulns if vulns else ["No common vulnerabilities detected"]
    except Exception as e:
        return [f"Vulnerability scan error: {e}"]


def check_shodan_exposure(ip=None):
    # Free tier: Only check if IP is public, no API call
    if not ip or ip.startswith('192.') or ip.startswith('10.') or ip.startswith('127.'):
        return "No public exposure detected (private IP)"
    return f"Public IP: {ip} (check Shodan for details)"


@app.route('/system-scan', methods=['GET', 'POST'])
@login_required
def system_scan():
    scan_results: dict[str, Any] = {}
    recommendations: list[str] = []
    advanced_results: dict[str, Any] = {}
    technical_results: dict[str, Any] = {}
    if request.method == 'POST':
        # Basic checks: OS, open ports, firewall, updates, antivirus
        scan_results['os'] = platform.system() + ' ' + platform.release()
        scan_results['hostname'] = socket.gethostname()
        # Check open ports (common ones)
        common_ports = [22, 80, 443, 3306, 8080]
        open_ports = []
        for port in common_ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex((scan_results['hostname'], port)) == 0:
                    open_ports.append(port)
        scan_results['open_ports'] = open_ports
        # Check for firewall (Windows only)
        if platform.system() == 'Windows':
            _fw = subprocess.run(
                ['netsh', 'advfirewall', 'show', 'allprofiles'],
                capture_output=True,
            )
            scan_results['firewall'] = 'Enabled' if _fw.returncode == 0 else 'Disabled/Unknown'
        else:
            scan_results['firewall'] = 'Check manually'
        # Recommend actions
        if not open_ports:
            recommendations.append('No common open ports detected. Good!')
        else:
            recommendations.append(f'Open ports detected: {open_ports}. Restrict unused ports.')
        if scan_results['firewall'] != 'Enabled':
            recommendations.append('Enable and configure your firewall.')
        recommendations.append('Ensure your OS and software are up to date.')
        recommendations.append('Install and update antivirus software.')
        recommendations.append('Regularly backup your data.')
        recommendations.append('Review user access and permissions.')
        recommendations.append('Enable multi-factor authentication where possible.')
        # Advanced checks
        advanced_results['outdated_software'] = check_outdated_software()
        advanced_results['weak_passwords'] = check_weak_passwords()
        advanced_results['antivirus_status'] = check_antivirus_status()
        advanced_results['disk_encryption'] = check_disk_encryption()
        advanced_results['admin_accounts'] = check_admin_accounts()
        advanced_results['suspicious_processes'] = check_suspicious_processes()
        # Advanced recommendations
        if advanced_results['outdated_software']:
            recommendations.append(f"Update software: {', '.join(advanced_results['outdated_software'])}.")
        if advanced_results['weak_passwords']:
            recommendations.append(f"Change weak passwords for: {', '.join(advanced_results['weak_passwords'])}.")
        if advanced_results['antivirus_status'] != 'Enabled':
            recommendations.append('Install and enable antivirus software.')
        if advanced_results['disk_encryption'] != 'Enabled':
            recommendations.append('Enable disk encryption for sensitive data.')
        if advanced_results['suspicious_processes']:
            proc_list = ', '.join(advanced_results['suspicious_processes'])
            recommendations.append(f"Investigate suspicious processes: {proc_list}.")
        recommendations.append('Review admin/root accounts and restrict access.')
        # Technical checks
        domain = request.form.get('domain', 'localhost')
        infra = InfrastructureAssessor(domain)
        infra_results = infra.run_checks()
        technical_results['ssl_tls'] = infra_results['ssl_certificate']
        technical_results['dns_resolution'] = infra_results['dns_resolution']
        technical_results['https_redirect'] = infra_results['https_redirect']
        technical_results['external_ip'] = infra_results['external_ip']
        technical_results['target_open_ports'] = infra_results['open_ports']
        technical_results['backup_status'] = check_backup_status()
        technical_results['patch_status'] = check_patch_status()
        technical_results['vulnerabilities'] = run_vulnerability_scan(domain)
        technical_results['shodan_exposure'] = check_shodan_exposure(technical_results['external_ip'])
        # Technical recommendations
        if 'SSL/TLS enabled' not in technical_results['ssl_tls']:
            recommendations.append('Enable SSL/TLS for all public-facing services.')
        dns_res = technical_results['dns_resolution']
        if 'DNS resolution failed' in dns_res or 'No DNS records found' in dns_res:
            recommendations.append('Fix DNS records for the target domain.')
        https_status = technical_results['https_redirect']
        if 'redirects to HTTPS' not in https_status and 'Local host' not in https_status:
            recommendations.append('Ensure HTTP redirects to HTTPS for public domains.')
        if technical_results['target_open_ports']:
            open_ports_str = ', '.join(str(p) for p in technical_results['target_open_ports'])
            recommendations.append(f"Review open target ports: {open_ports_str}.")
        if 'Last backup' not in technical_results['backup_status']:
            recommendations.append('Set up regular, secure backups.')
        if 'up to date' not in technical_results['patch_status']:
            recommendations.append('Apply all missing OS and software patches.')
        found_vulnerabilities = technical_results['vulnerabilities']
        if found_vulnerabilities and 'No common vulnerabilities detected' not in found_vulnerabilities[0]:
            recommendations.append(f"Review open services: {', '.join(found_vulnerabilities)}.")
        if 'No public exposure detected' not in technical_results['shodan_exposure']:
            recommendations.append('Review public exposure and restrict unnecessary services.')
        return render_template(
            'system_scan_results.html',
            scan_results=scan_results,
            recommendations=recommendations,
            advanced_results=advanced_results,
            technical_results=technical_results,
        )
    return render_template('system_scan.html')


@app.route('/infrastructure-scan', methods=['GET', 'POST'])
@login_required
def infrastructure_scan():
    recommendations = []
    infra_results: dict[str, Any] = {}
    if request.method == 'POST':
        target = request.form.get('domain', 'localhost')
        assessor = InfrastructureAssessor(target)
        infra_results = assessor.run_checks()

        if 'SSL/TLS enabled' not in infra_results.get('ssl_certificate', ''):
            recommendations.append('Enable SSL/TLS for the target service.')
        dns_result = infra_results.get('dns_resolution', '')
        if 'DNS resolution failed' in dns_result or 'No DNS records found' in dns_result:
            recommendations.append('Fix DNS records for the target domain.')
        if 'redirects to HTTPS' not in infra_results.get('https_redirect', ''):
            recommendations.append('Ensure HTTP redirects to HTTPS for public domains.')
        if infra_results.get('open_ports'):
            open_ports = infra_results['open_ports']
            if any(port not in (80, 443) for port in open_ports):
                extra = ', '.join(str(p) for p in open_ports if p not in (80, 443))
                recommendations.append(f"Restrict unnecessary open ports: {extra}.")

        return render_template(
            'infrastructure_scan_results.html',
            target=target,
            infra_results=infra_results,
            recommendations=recommendations,
        )

    return render_template('infrastructure_scan.html')


def automated_scan():
    """Automated system scan for scheduled runs."""
    # Simulate scan and log results
    scan_results = {'os': platform.system(), 'hostname': socket.gethostname()}
    # In real implementation, save to DB or send email
    print(f"Automated scan completed: {scan_results}")
    return scan_results


def generate_pdf_report(scan_results, recommendations, advanced_results, technical_results):
    """Generate PDF report from scan results."""
    try:
        from reportlab.lib.pagesizes import letter as _letter
        from reportlab.platypus import SimpleDocTemplate as _Doc, Paragraph as _P, Spacer as _S
        from reportlab.lib.styles import getSampleStyleSheet as _styles
    except ImportError:
        return io.BytesIO(b'PDF generation requires the reportlab package.')

    buffer = io.BytesIO()
    doc = _Doc(buffer, pagesize=_letter)
    styles = _styles()
    story = []

    story.append(_P("Digital Hygiene Scan Report", styles['Title']))
    story.append(_S(1, 12))

    story.append(_P("Basic Results", styles['Heading2']))
    for key, value in scan_results.items():
        story.append(_P(f"{key}: {value}", styles['Normal']))
    story.append(_S(1, 12))

    story.append(_P("Advanced Results", styles['Heading2']))
    for key, value in advanced_results.items():
        story.append(_P(f"{key}: {value}", styles['Normal']))
    story.append(_S(1, 12))

    story.append(_P("Technical Results", styles['Heading2']))
    for key, value in technical_results.items():
        story.append(_P(f"{key}: {value}", styles['Normal']))
    story.append(_S(1, 12))

    story.append(_P("Recommendations", styles['Heading2']))
    for rec in recommendations:
        story.append(_P(f"- {rec}", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer


@app.route('/schedule-scan', methods=['GET', 'POST'])
@login_required
def schedule_scan():
    if request.method == 'POST':
        interval = int(request.form.get('interval', 24))  # hours
        if scheduler is not None:
            scheduler.add_job(func=automated_scan, trigger="interval", hours=interval, id='automated_scan')
            flash(f'Scan scheduled every {interval} hours.', 'success')
        else:
            flash('Scheduler not available. Install APScheduler.', 'warning')
        return redirect(url_for('dashboard'))
    return render_template('schedule_scan.html')


@app.route('/download-pdf')
@login_required
def download_pdf():
    # Dummy data for demo; in real, get from session or DB
    scan_results = {'os': 'Windows', 'hostname': 'localhost'}
    recommendations = ['Enable firewall', 'Update software']
    advanced_results = {'outdated_software': ['Python']}
    technical_results = {'ssl_tls': 'Enabled'}
    pdf_buffer = generate_pdf_report(scan_results, recommendations, advanced_results, technical_results)
    return send_file(pdf_buffer, as_attachment=True, download_name='scan_report.pdf', mimetype='application/pdf')

# Install script serving routes


@app.route('/install.ps1')
def install_ps1():
    """Serve PowerShell install script"""
    script_content = '''# Zambia Digital Hygiene Assessment Tool - PowerShell Quick Install
# Usage: irm https://your-domain.com/install.ps1 | iex

param(
    [switch]$NoWeb,
    [switch]$NoDB,
    [string]$Branch = "main"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Zambia Digital Hygiene Assessment Tool" -ForegroundColor Cyan
Write-Host "PowerShell Quick Install & Run Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check Python installation
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create temp directory
$tempDir = Join-Path $env:TEMP "digital_hygiene_install"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null
Set-Location $tempDir

# Download the repository
Write-Host "Downloading repository..." -ForegroundColor Yellow
try {
    $zipUrl = "https://github.com/yourusername/digital-hygiene-tool/archive/$Branch.zip"
    $zipPath = Join-Path $tempDir "repo.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing

    # Extract ZIP
    Expand-Archive -Path $zipPath -DestinationPath $tempDir
    $extractedDir = Get-ChildItem -Directory | Select-Object -First 1
    Set-Location $extractedDir.FullName

    Write-Host "✓ Repository downloaded and extracted" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to download repository: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
try {
    & python -m pip install --upgrade pip
    & pip install -r requirements.txt
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Setup database (unless skipped)
if (-not $NoDB) {
    Write-Host "Setting up database..." -ForegroundColor Yellow
    try {
        & python database/setup_mysql.py
        Write-Host "✓ Database setup completed" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Database setup failed or was cancelled" -ForegroundColor Yellow
        Write-Host "You can run it manually later: python database/setup_mysql.py" -ForegroundColor Yellow
    }
}

# Run the tool
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

if (-not $NoWeb) {
    Write-Host "`nStarting web interface..." -ForegroundColor Yellow
    Write-Host "Visit: http://localhost:5000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow

    try {
        & python src/web/app.py
    } catch {
        Write-Host "❌ Failed to start web interface" -ForegroundColor Red
        Write-Host "You can start it manually: python src/web/app.py" -ForegroundColor Yellow
    }
} else {
    Write-Host "`nTo start the web interface manually:" -ForegroundColor Cyan
    Write-Host "  python src/web/app.py" -ForegroundColor White
}

Write-Host "`nTo use the CLI:" -ForegroundColor Cyan
Write-Host "  python src/utils/cli.py --help" -ForegroundColor White

Write-Host "`nInstallation directory: $((Get-Location).Path)" -ForegroundColor Gray
'''
    return Response(script_content, mimetype='text/plain')

# ------------------------------------------------------------------
# Pre-Deployment Digital Hygiene Check
# ------------------------------------------------------------------


# Keep the last report in memory so the JSON download works after a scan
_predeploy_last_report: dict = {}


@app.route('/predeploy-check', methods=['GET', 'POST'])
@login_required
def predeploy_check():
    """Run 13-point pre-deployment digital hygiene check."""
    global _predeploy_last_report
    report = None
    if request.method == 'POST':
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        checker = PreDeploymentChecker(project_root=project_root)
        report = checker.run_all()
        _predeploy_last_report = report.to_dict()
        flash(f'Pre-deployment scan complete – verdict: {report.verdict}',
              'success' if report.verdict == 'READY' else 'danger')
    return render_template('predeploy_check.html', report=report)


@app.route('/predeploy-check/json')
@login_required
def predeploy_json():
    """Return the last pre-deployment report as downloadable JSON."""
    if not _predeploy_last_report:
        flash('Run a pre-deployment check first.', 'warning')
        return redirect(url_for('predeploy_check'))
    return jsonify(_predeploy_last_report)


@app.route('/install.bat')
def install_bat():
    """Serve Windows batch install script"""
    script_content = '''@echo off
REM Zambia Digital Hygiene Assessment Tool - Quick Install & Run
REM Usage: curl -s https://your-domain.com/install.bat | cmd

echo ========================================
echo Zambia Digital Hygiene Assessment Tool
echo Quick Install & Run Script
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Git not found. Will try to download as ZIP...
    goto :download_zip
)

REM Clone the repository
echo Cloning repository...
git clone https://github.com/yourusername/digital-hygiene-tool.git temp_digital_hygiene
cd temp_digital_hygiene
goto :setup

:download_zip
echo Downloading as ZIP...
set "REPO=https://github.com/yourusername/digital-hygiene-tool"
powershell -Command "Invoke-WebRequest -Uri '%REPO%/archive/main.zip' -OutFile 'temp_digital_hygiene.zip'"
powershell -Command "Expand-Archive -Path 'temp_digital_hygiene.zip' -DestinationPath '.'"
cd digital-hygiene-tool-main

:setup
REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Setup database
echo Setting up database...
python database/setup_mysql.py

REM Run the tool
echo.
echo ========================================
echo Installation complete!
echo.
echo To run the web interface:
echo   python src/web/app.py
echo.
echo To use the CLI:
echo   python src/utils/cli.py [command]
echo.
echo Visit: http://localhost:5000
echo ========================================

pause
'''
    return Response(script_content, mimetype='text/plain')


@app.route('/install.sh')
def install_sh():
    """Serve Linux/macOS bash install script"""
    script_content = '''#!/bin/bash
# Zambia Digital Hygiene Assessment Tool - Quick Install & Run
# Usage: curl -s https://your-domain.com/install.sh | bash

set -e

echo "========================================"
echo "Zambia Digital Hygiene Assessment Tool"
echo "Quick Install & Run Script"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ ERROR: Python is not installed"
    echo "Please install Python 3.8+ first"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "✓ Python found: $($PYTHON_CMD --version)"

# Create temp directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Try to clone repository first, fallback to download ZIP
echo "Downloading repository..."
if command -v git &> /dev/null; then
    git clone https://github.com/yourusername/digital-hygiene-tool.git .
else
    echo "Git not found, downloading ZIP..."
    curl -L -o repo.zip https://github.com/yourusername/digital-hygiene-tool/archive/main.zip
    unzip repo.zip
    cd digital-hygiene-tool-main
fi

# Install dependencies
echo "Installing dependencies..."
$PYTHON_CMD -m pip install --user --upgrade pip
$PYTHON_CMD -m pip install --user -r requirements.txt

# Setup database
echo "Setting up database..."
if $PYTHON_CMD database/setup_mysql.py; then
    echo "✓ Database setup completed"
else
    echo "⚠️  Database setup failed or was cancelled"
    echo "You can run it manually later: $PYTHON_CMD database/setup_mysql.py"
fi

# Run the tool
echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
echo ""
echo "To run the web interface:"
echo "  $PYTHON_CMD src/web/app.py"
echo ""
echo "To use the CLI:"
echo "  $PYTHON_CMD src/utils/cli.py --help"
echo ""
echo "Visit: http://localhost:5000"
echo ""

# Ask if user wants to start the web interface
read -p "Start web interface now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting web interface..."
    echo "Press Ctrl+C to stop"
    $PYTHON_CMD src/web/app.py
fi

echo ""
echo "Installation directory: $(pwd)"
echo "You can safely delete this directory after copying the files elsewhere."
'''
    return Response(script_content, mimetype='text/plain')


@app.route('/verify/<certificate_number>')
def verify(certificate_number):
    """Public certificate verification — queries the Certificate table."""
    cert = Certificate.query.filter_by(
        certificate_number=certificate_number, is_active=True
    ).first()
    verified = cert is not None
    business_name = None
    issued_date = None
    expiry_date = None
    level = None
    if cert:
        try:
            business_name = cert.assessment.business.name if cert.assessment and cert.assessment.business else None
        except Exception:
            pass
        issued_date = cert.issued_date
        expiry_date = cert.expiry_date
        level = cert.assessment.certification_level if cert.assessment else None
    return render_template(
        'verify.html',
        cert_id=certificate_number,
        verified=verified,
        business_name=business_name,
        issued_date=issued_date,
        expiry_date=expiry_date,
        certification_level=level,
    )


@app.route('/about')
def about():
    """About the program."""
    return render_template('about.html')


@app.route('/download')
def download():
    """Redirect to the latest Windows .exe on GitHub Releases."""
    download_url = os.environ.get(
        'DOWNLOAD_URL',
        'https://github.com/sakhile-bit/sakhile_final-_year_pro/releases/download/v1.0.0/ZambiaDigitalHygiene.exe',
    )
    return redirect(download_url)


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# ------------------------------------------------------------------
# Health check (no auth — for load balancers / hosting platforms)
# ------------------------------------------------------------------
@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'zdh-web'})


# ------------------------------------------------------------------
# Network Scanner
# ------------------------------------------------------------------
_NET_SCAN_PORTS = [21, 22, 23, 25, 53, 80, 135, 139, 443, 445,
                   1433, 3306, 3389, 5432, 8080, 8443]

_NET_PORT_INFO: dict[int, tuple[str, str, str]] = {
    21:   ("FTP",        "HIGH",     "Unencrypted file transfer — use SFTP"),
    22:   ("SSH",        "INFO",     "Secure remote access"),
    23:   ("Telnet",     "CRITICAL", "Unencrypted remote access — disable now"),
    25:   ("SMTP",       "MEDIUM",   "Mail relay — verify not open to internet"),
    53:   ("DNS",        "INFO",     "DNS resolver"),
    80:   ("HTTP",       "LOW",      "Unencrypted web — redirect to HTTPS"),
    135:  ("MS-RPC",     "HIGH",     "Windows RPC — restrict to internal only"),
    139:  ("NetBIOS",    "HIGH",     "Legacy Windows sharing — disable if unused"),
    443:  ("HTTPS",      "INFO",     "Secure web server"),
    445:  ("SMB",        "CRITICAL", "Windows file sharing — prime ransomware vector"),
    1433: ("MS-SQL",     "HIGH",     "SQL Server exposed — restrict access"),
    3306: ("MySQL",      "HIGH",     "MySQL database exposed to network"),
    3389: ("RDP",        "CRITICAL", "Remote Desktop — critical ransomware risk"),
    5432: ("PostgreSQL", "HIGH",     "PostgreSQL database exposed"),
    8080: ("HTTP-alt",   "LOW",      "Alternative web server"),
    8443: ("HTTPS-alt",  "INFO",     "Alternative HTTPS server"),
}

_NET_RISK_ORDER = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "INFO": 1, "SAFE": 0}


def _net_scan_port(ip: str, port: int, timeout: float = 0.5) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((ip, port))
        s.close()
        return r == 0
    except Exception:
        return False


def _net_scan_device(ip: str) -> dict:
    from concurrent.futures import ThreadPoolExecutor, as_completed as _ac
    open_ports: list[int] = []
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(_net_scan_port, ip, p): p for p in _NET_SCAN_PORTS}
        for fut in _ac(futs):
            if fut.result():
                open_ports.append(futs[fut])
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except Exception:
        hostname = ip
    risk_level = "SAFE"
    for p in open_ports:
        lvl = _NET_PORT_INFO.get(p, ("", "INFO", ""))[1]
        if _NET_RISK_ORDER.get(lvl, 0) > _NET_RISK_ORDER.get(risk_level, 0):
            risk_level = lvl
    port_details = []
    for p in sorted(open_ports):
        name, risk, desc = _NET_PORT_INFO.get(p, (str(p), "INFO", ""))
        port_details.append({"port": p, "name": name, "risk": risk, "desc": desc})
    return {"ip": ip, "hostname": hostname, "open_ports": open_ports,
            "port_details": port_details, "risk_level": risk_level}


def _net_arp_hosts(prefix: str) -> list[str]:
    hosts: set[str] = set()
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.splitlines():
            m = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
            if m and m.group(1).startswith(prefix):
                hosts.add(m.group(1))
    except Exception:
        pass
    return sorted(hosts)


@app.route('/network-scan', methods=['GET', 'POST'])
@login_required
def network_scan():
    results: list[dict] = []
    subnet = ""
    error = None
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 53))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    if request.method == 'POST':
        subnet = request.form.get('subnet', '.'.join(local_ip.split('.')[:3])).strip()
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}$', subnet):
            error = "Invalid subnet prefix — enter like: 192.168.1"
        else:
            hosts = list(set(_net_arp_hosts(subnet) + (
                [local_ip] if local_ip.startswith(subnet) else [])))
            if not hosts:
                error = (f"No devices found on {subnet}.0/24 in the ARP cache. "
                         "Try pinging a few devices first, then re-scan.")
            else:
                from concurrent.futures import ThreadPoolExecutor, as_completed as _ac
                with ThreadPoolExecutor(max_workers=8) as ex:
                    futs = {ex.submit(_net_scan_device, ip): ip for ip in hosts[:50]}
                    for fut in _ac(futs):
                        results.append(fut.result())
                results.sort(
                    key=lambda d: _NET_RISK_ORDER.get(d['risk_level'], 0),
                    reverse=True)

    default_subnet = '.'.join(local_ip.split('.')[:3])
    return render_template('network_scan.html', results=results, subnet=subnet,
                           local_ip=local_ip, default_subnet=default_subnet,
                           error=error, port_info=_NET_PORT_INFO)


# ------------------------------------------------------------------
# Policy Template Library
# ------------------------------------------------------------------
_POLICY_TEMPLATES = [
    {
        "id": "aup",
        "icon": "fa-file-contract",
        "title": "Acceptable Use Policy (AUP)",
        "description": "Rules governing how staff may use company computers, internet, and devices.",
        "framework": "CIS Control 14 · ISO 27001 A.8",
        "content": """\
ACCEPTABLE USE POLICY
=====================
[BUSINESS NAME]
Effective Date: [DATE]
Version: 1.0
Approved by: [MANAGEMENT NAME / TITLE]

1. PURPOSE
   This policy defines acceptable use of [BUSINESS NAME]'s information technology
   resources to protect the organisation, its employees, partners, and customers.

2. SCOPE
   This policy applies to ALL employees, contractors, and third parties who access
   [BUSINESS NAME]'s IT systems, networks, or data.

3. ACCEPTABLE USE
   3.1 IT resources shall be used primarily for legitimate business purposes.
   3.2 Limited personal use is permitted provided it does not interfere with work.
   3.3 Users must keep passwords confidential and not share them with others.
   3.4 Users must lock their computer screen when leaving their workstation.

4. PROHIBITED ACTIVITIES
   4.1 Accessing, downloading, or distributing illegal or inappropriate content.
   4.2 Installing unlicensed software on company devices.
   4.3 Sharing company data or credentials with unauthorised persons.
   4.4 Using company email for personal business or chain letters.
   4.5 Attempting to bypass security controls or access unauthorised systems.
   4.6 Using company systems for cryptocurrency mining or personal financial gain.
   4.7 Connecting personal USB drives without IT approval.

5. MOBILE DEVICES
   5.1 All company mobile devices must have a PIN/password lock.
   5.2 Employees must report lost or stolen devices to management immediately.
   5.3 Only apps from official app stores may be installed.

6. DATA PROTECTION
   6.1 Customer data must be handled in accordance with the Zambia Data Protection
       Act No. 3 of 2021.
   6.2 Sensitive data must not be stored on personal devices or unapproved cloud services.

7. INCIDENT REPORTING
   All suspected security incidents must be reported to [IT CONTACT NAME] at [EMAIL/PHONE].
   ZICTA: +260 211 369 000 | CERT-ZM: cert@zicta.zm

8. CONSEQUENCES
   Violations may result in disciplinary action up to and including termination,
   and referral to law enforcement under the Cyber Security and Cyber Crimes Act, 2021.

9. ACKNOWLEDGEMENT
   I, [EMPLOYEE NAME], have read, understood, and agree to comply with this policy.

   Signature: ___________________________   Date: _______________
   Printed Name: ________________________   Department: __________
""",
    },
    {
        "id": "irp",
        "icon": "fa-triangle-exclamation",
        "title": "Incident Response Plan (IRP)",
        "description": "Step-by-step plan for responding to cybersecurity incidents.",
        "framework": "CIS Control 17 · NIST RS.RP-1 · ISO 27001 A.16",
        "content": """\
INCIDENT RESPONSE PLAN
=======================
[BUSINESS NAME]
Effective Date: [DATE]
Version: 1.0
Plan Owner: [IT MANAGER / OWNER NAME]

1. PURPOSE
   This plan defines how [BUSINESS NAME] will detect, respond to, and recover from
   cybersecurity incidents to minimise damage and restore normal operations quickly.

2. INCIDENT TYPES COVERED
   - Data breach or unauthorised access
   - Ransomware or malware infection
   - Phishing attack (successful or attempted)
   - Loss or theft of devices containing company data
   - System outage caused by a cyberattack

3. RESPONSE TEAM
   Incident Commander:  [NAME] — [PHONE] — [EMAIL]
   IT Support Contact:  [NAME / COMPANY] — [PHONE]
   Management Notifier: [NAME] — [PHONE]

4. EXTERNAL CONTACTS
   ZICTA:  +260 211 369 000  |  info@zicta.zm
   CERT-ZM: cert@zicta.zm
   Zambia Police (Cybercrime): +260 211 251 222

5. RESPONSE STEPS

   STEP 1 — IDENTIFY (First 15 minutes)
   [ ] Who noticed the incident? _______________  Time: _________
   [ ] What systems/data are affected?
   [ ] Is the incident still ongoing?

   STEP 2 — CONTAIN (First 1 hour)
   [ ] Disconnect affected computers from the network.
   [ ] Do NOT turn off the computer unless ransomware is actively encrypting files.
   [ ] Preserve evidence — take photos of error messages.
   [ ] Change passwords for affected accounts from a clean device.

   STEP 3 — ERADICATE (Hours 1–24)
   [ ] Run a full antivirus scan on affected systems.
   [ ] Remove malware identified.
   [ ] Patch any vulnerability that was exploited.
   [ ] Reset all potentially compromised credentials.

   STEP 4 — RECOVER (Hours 24–72)
   [ ] Restore data from the most recent clean backup.
   [ ] Verify systems are clean before reconnecting to the network.

   STEP 5 — REPORT & LEARN (Within 7 days)
   [ ] Report to ZICTA / CERT-ZM if customer data was breached.
   [ ] Notify affected customers if their data was exposed (required by DPA 2021).
   [ ] Document what happened, timeline, impact, and actions taken.

6. DATA BREACH NOTIFICATION (Zambia DPA 2021)
   - Notify the Data Protection Commissioner within 72 hours.
   - Notify affected individuals without undue delay.

7. PLAN REVIEW
   This plan is reviewed annually or after any significant incident.
   Last reviewed: [DATE]   Next review: [DATE]
""",
    },
    {
        "id": "acp",
        "icon": "fa-key",
        "title": "Access Control Policy",
        "description": "Policy for managing who can access company systems and data.",
        "framework": "CIS Control 5 · NIST PR.AC-4 · ISO 27001 A.9",
        "content": """\
ACCESS CONTROL POLICY
======================
[BUSINESS NAME]
Effective Date: [DATE]
Version: 1.0

1. PURPOSE
   To ensure access to information systems and data is granted on a
   least-privilege, need-to-know basis.

2. ACCESS PRINCIPLES
   2.1 Least Privilege: Users receive only the minimum access required.
   2.2 Need to Know: Sensitive data restricted to those with a legitimate need.
   2.3 Separation of Duties: Critical tasks require more than one approver.

3. USER ACCOUNT MANAGEMENT
   3.1 New accounts require written manager approval.
   3.2 When an employee leaves, access is revoked on their LAST DAY.
   3.3 Shared passwords must be changed when an employee with that access leaves.

4. PASSWORD REQUIREMENTS
   [ ] Minimum 8 characters (12 recommended)
   [ ] Uppercase, lowercase, numbers, and special characters
   [ ] Passwords expire every 90 days
   [ ] Accounts lock after 5 failed attempts
   [ ] MFA required for: [LIST SYSTEMS]

5. PRIVILEGED ACCESS
   5.1 Admin accounts must be separate from regular accounts.
   5.2 Privileged access must be logged and reviewed monthly.
   5.3 Remote privileged access requires MFA and VPN.

6. ACCESS REVIEWS
   Access rights for all users shall be reviewed every 6 months.
   Next review due: [DATE]

7. VIOLATIONS
   Unauthorised access or credential sharing is a disciplinary offence
   under the Cyber Security and Cyber Crimes Act, 2021.
""",
    },
    {
        "id": "pwd",
        "icon": "fa-lock",
        "title": "Password & MFA Policy",
        "description": "Rules for creating strong passwords and using multi-factor authentication.",
        "framework": "CIS Control 5 · NIST PR.AC-1 · ISO 27001 A.9.4",
        "content": """\
PASSWORD AND MULTI-FACTOR AUTHENTICATION (MFA) POLICY
=======================================================
[BUSINESS NAME]
Effective Date: [DATE]
Version: 1.0

1. PASSWORD REQUIREMENTS
   MINIMUM LENGTH:   8 characters (12+ recommended)
   COMPLEXITY:       Uppercase, lowercase, number, and special character
   MAXIMUM AGE:      90 days
   HISTORY:          Cannot reuse last 5 passwords
   LOCKOUT:          Account locked after 5 consecutive failed attempts

2. PASSPHRASE APPROACH
   Consider using 4+ random words, e.g. "ZambiaCloud2024Secure!"
   Use a free password manager (Bitwarden, KeePass) to store passwords.

3. PROHIBITED PASSWORDS
   [ ] Passwords containing your name, business name, or username
   [ ] Common passwords: "password", "123456", "zambia", "lusaka"
   [ ] Keyboard patterns: "qwerty", "asdfgh"

4. MULTI-FACTOR AUTHENTICATION (MFA)
   MFA is MANDATORY for:
   [ ] Email accounts
   [ ] Banking and mobile money applications
   [ ] Cloud storage (Google Drive, OneDrive, Dropbox)
   [ ] Any VPN or remote access system
   Recommended apps: Google Authenticator, Microsoft Authenticator, Authy.

5. PASSWORD SHARING
   Passwords must NEVER be:
   [ ] Shared with colleagues or IT staff
   [ ] Written on paper and left visible
   [ ] Sent via WhatsApp or SMS in plain text

6. SUSPECTED COMPROMISE
   1. Change the password immediately on all affected accounts.
   2. Enable MFA on the account if not already done.
   3. Report to [IT CONTACT] at [EMAIL/PHONE].
   4. Check https://haveibeenpwned.com for data breach exposure.
""",
    },
    {
        "id": "dpp",
        "icon": "fa-shield-halved",
        "title": "Data Protection Policy",
        "description": "How the business collects, stores, and protects personal data under Zambia's DPA 2021.",
        "framework": "Zambia DPA 2021 · GDPR-aligned · ISO 27001 A.18",
        "content": """\
DATA PROTECTION POLICY
=======================
[BUSINESS NAME]
Effective Date: [DATE]
Version: 1.0

1. COMMITMENT
   [BUSINESS NAME] is committed to protecting personal data in compliance with the
   Zambia Data Protection Act No. 3 of 2021.

2. WHAT DATA WE COLLECT
   [ ] Name, contact details (phone, email, address)
   [ ] National Registration Card (NRC) number where required by law
   [ ] Financial information — for payment purposes only
   [ ] Employment records (for employees)
   [ ] [LIST ANY OTHER DATA YOUR BUSINESS COLLECTS]

3. HOW WE PROTECT DATA
   [ ] Data is stored on password-protected systems.
   [ ] Sensitive data is encrypted at rest where feasible.
   [ ] Access is restricted to authorised staff only.
   [ ] Paper records are kept in locked storage.

4. DATA RETENTION
   Customer records:   [X] years after last transaction
   Employee records:   [X] years after employment ends
   Financial records:  [7] years (ZRA requirements)

5. DATA SUBJECT RIGHTS (Zambia DPA 2021)
   Individuals have the right to access, correct, and request deletion of their data.
   Contact: [EMAIL / PHONE] — we will respond within 14 days.

6. DATA BREACH RESPONSE
   1. Report to management immediately.
   2. Notify the Data Protection Commissioner within 72 hours if required.
   3. Notify affected individuals without undue delay.

7. REGISTRATION
   [BUSINESS NAME] is registered with the Data Protection Commission (DPC) Zambia.
   Registration Number: [DPC REG NUMBER]

8. REVIEW
   This policy is reviewed annually. Last reviewed: [DATE]
""",
    },
]


@app.route('/policy-templates')
@login_required
def policy_templates():
    return render_template('policy_templates.html', templates=_POLICY_TEMPLATES)


@app.route('/policy-templates/<template_id>/download')
@login_required
def policy_template_download(template_id):
    tmpl = next((t for t in _POLICY_TEMPLATES if t['id'] == template_id), None)
    if not tmpl:
        abort(404)
    buf = io.BytesIO(tmpl['content'].encode('utf-8'))
    return send_file(buf, as_attachment=True,
                     download_name=f"{template_id}_policy_template.txt",
                     mimetype='text/plain')


# ------------------------------------------------------------------
# User Settings
# ------------------------------------------------------------------
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        new_email = request.form.get('email', '').strip()
        if new_email and new_email != current_user.email:
            if (User.query
                    .filter_by(email=new_email)
                    .filter(User.id != int(current_user.id))
                    .first()):
                flash('That email address is already in use.', 'error')
            elif not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', new_email):
                flash('Invalid email address.', 'error')
            else:
                current_user.email = new_email
                db.session.commit()
                log = AuditLog(user_id=current_user.id, action='settings_update',
                               resource_type='user', resource_id=current_user.id,
                               details={'field': 'email', 'ip': request.remote_addr})
                db.session.add(log)
                db.session.commit()
                flash('Email updated successfully.', 'success')
        elif not new_email:
            flash('Email address cannot be empty.', 'error')
    return render_template('settings.html', user=current_user)


if __name__ == '__main__':
    create_app().run(debug=True)
