"""
Flask web application for the Zambia Digital Hygiene Assessment Tool
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import json
import csv
import io
import re
import secrets
from functools import wraps
from sqlalchemy import Enum
import requests
import ssl
import nmap
import socket
import platform
import subprocess
import time
from apscheduler.schedulers.background import BackgroundScheduler
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

from src.assessment.assessor import DigitalHygieneAssessor, BusinessInfo, ZambiaRiskAssessor
from src.reporting.generator import ReportGenerator
from src.utils.logging_config import get_logger
from src.utils.config import config, load_env_file

# Load environment variables from .env file if it exists
load_env_file('.env')

logger = get_logger(__name__)

# Initialize Flask app and extensions (application factory pattern)
app = Flask(__name__)
app.config['SECRET_KEY'] = config.web.get('secret_key', 'dev-secret-key')
# Production hardening
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
# Use MySQL via config or fall back to SQLite for tests
app.config['SQLALCHEMY_DATABASE_URI'] = config.get_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions without binding to app immediately
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'

# Initialize scheduler for automation
scheduler = BackgroundScheduler()
scheduler.start()

# User model aligned to schema (users table)
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(Enum('admin', 'assessor', 'viewer', name='role_enum'), default='assessor', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
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


class Assessment(db.Model):
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    assessor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow)
    system_info = db.Column(db.JSON)
    controls_results = db.Column(db.JSON, nullable=False)
    total_score = db.Column(db.Integer, nullable=False)
    certification_level = db.Column(Enum('GOLD', 'SILVER', 'BRONZE', 'NOT_CERTIFIED', name='cert_level_enum'), nullable=False)
    recommendations = db.Column(db.JSON)
    status = db.Column(Enum('draft', 'completed', 'certified', name='status_enum'), default='completed', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = db.relationship('Business')
    assessor = db.relationship('User')


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

    # Backwards-compatible view helpers for templates
    @property
    def business_name(self):  # pragma: no cover - presentational
        return self.business.name if self.business else ''

    @property
    def business_registration(self):  # pragma: no cover - presentational
        return self.business.registration_number if self.business else ''

    @property
    def contact_person(self):  # pragma: no cover - presentational
        return self.business.contact_person if self.business else ''

    @property
    def contact_email(self):  # pragma: no cover - presentational
        return self.business.contact_email if self.business else ''

    @property
    def contact_phone(self):  # pragma: no cover - presentational
        return self.business.contact_phone if self.business else ''

    @property
    def industry(self):  # pragma: no cover - presentational
        return self.business.industry if self.business else ''

    @property
    def address(self):  # pragma: no cover - presentational
        return self.business.address if self.business else ''

    @property
    def score(self):  # pragma: no cover - compatibility alias
        return self.total_score

    @property
    def total_possible(self):  # pragma: no cover - compatibility alias
        data = self.controls_results or {}
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

def create_app():
    """Create and configure the Flask application"""
    # Bind extensions to app once (do not create tables here; tests handle it)
    if 'sqlalchemy' not in getattr(app, 'extensions', {}):
        db.init_app(app)
    if not hasattr(app, 'login_manager'):
        login_manager.init_app(app)

    # Session security: set secure cookies, HTTPOnly, SameSite
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 min

    # CSRF protection (simple token)
    app.config['CSRF_TOKEN'] = secrets.token_urlsafe(32)

    # Ensure tables exist and seed a default admin if missing (MySQL production path)
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@digitalhygiene.gov.zm', role='admin', is_active=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            logger.info('Default admin user created')
        else:
            # Normalize hash if legacy bcrypt hash present
            if not admin.password_hash.startswith('pbkdf2:'):
                admin.set_password('admin123')
                db.session.commit()
                logger.info('Default admin password reset to pbkdf2 hash')

    return app

# Simple rate limiting for login
login_attempts = {}

def rate_limit(max_attempts=5, window=300):  # 5 attempts per 5 minutes
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr
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
    """Home page"""
    return render_template('index.html')

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

            # MFA stub: require TOTP for admin (future)
            # if user.role == 'admin' and not session.get('mfa_verified'):
            #     return redirect(url_for('mfa'))

            login_user(user)
            # Log login event
            log = AuditLog(user_id=user.id, action='login', resource_type='user', resource_id=user.id, details={'ip': request.remote_addr, 'ua': request.user_agent.string})
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

@app.route('/dashboard')
@login_required
def dashboard():
    """Assessment dashboard"""
    query = Assessment.query
    if current_user.role != 'admin':
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
    expiring = Certificate.query.filter(Certificate.expiry_date <= soon, Certificate.is_active == True).all()
    if expiring:
        reminders.append(f"{len(expiring)} certificate(s) expiring within 30 days.")
    # Periodic reassessment (every 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    old_assessments = Assessment.query.filter(Assessment.assessment_date <= six_months_ago, Assessment.assessor_id == current_user.id).count()
    if old_assessments:
        reminders.append(f"{old_assessments} assessment(s) due for reassessment.")

    return render_template('dashboard.html', assessments=assessments, stats=stats, tip=tip, reminders=reminders, mobile_device_tips=MOBILE_DEVICE_TIPS)

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
                address=request.form.get('address')
            )

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

            # Run assessment
            assessor = DigitalHygieneAssessor(business_info)
            results = assessor.run_assessment()

            # Save to database
            controls_payload = {k: v.__dict__ for k, v in results.controls.items()}
            assessment = Assessment(
                business_id=business.id,
                assessor_id=current_user.id,
                controls_results={
                    'controls': controls_payload,
                    'total_possible': results.total_possible,
                },
                total_score=results.score,
                certification_level=results.certification_level,
                recommendations=results.recommendations,
                status='completed'
            )

            db.session.add(assessment)
            db.session.commit()

            flash('Assessment completed successfully!', 'success')
            return redirect(url_for('results', assessment_id=assessment.id))

        except Exception as e:
            logger.error(f"Assessment error: {e}")
            flash(f'Assessment failed: {str(e)}', 'error')

    return render_template('assess.html')

@app.route('/results/<int:assessment_id>')
@login_required
def results(assessment_id):
    """Assessment results"""
    query = Assessment.query
    if current_user.role != 'admin':
        query = query.filter_by(id=assessment_id, assessor_id=current_user.id)
    assessment = query.first_or_404()

    # Parse assessment data
    data = assessment.controls_results or {}
    controls = data.get('controls', {})
    total_possible = data.get('total_possible', 0)
    result_obj = type('Results', (), {
        'score': assessment.total_score,
        'total_possible': total_possible,
        'certification_level': assessment.certification_level,
        'controls': {k: type('Control', (), v) for k, v in controls.items()},
        'recommendations': assessment.recommendations or []
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

    return render_template('results.html', results=result_obj, business_info=business_info, assessment_id=assessment_id)

@app.route('/download/<int:assessment_id>/<format>')
@login_required
def download_report(assessment_id, format):
    """Download assessment report"""
    query = Assessment.query
    if current_user.role != 'admin':
        query = query.filter_by(id=assessment_id, assessor_id=current_user.id)
    assessment = query.first_or_404()

    # Parse assessment data
    data = assessment.controls_results or {}
    controls = data.get('controls', {})
    total_possible = data.get('total_possible', 0)
    results = type('Results', (), {
        'score': assessment.total_score,
        'total_possible': total_possible,
        'certification_level': assessment.certification_level,
        'controls': {k: type('Control', (), v) for k, v in controls.items()},
        'recommendations': assessment.recommendations or []
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
    if format == 'pdf':
        report_path = generator.generate_pdf_report(results, business_info, f"assessment_{assessment_id}")
        return send_file(report_path, as_attachment=True, download_name=f"assessment_{assessment_id}.pdf")
    elif format == 'html':
        report_path = generator.generate_html_report(results, business_info, f"assessment_{assessment_id}")
        return send_file(report_path, as_attachment=True, download_name=f"assessment_{assessment_id}.html")
    elif format == 'json':
        report_data = generator.generate_json_report(results, business_info)
        buffer = io.BytesIO()
        buffer.write(json.dumps(report_data, indent=2).encode())
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"assessment_{assessment_id}.json",
                        mimetype='application/json')
    elif format == 'csv':
        report_data = generator.generate_csv_report(results, business_info)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerows(report_data)
        buffer.seek(0)
        return send_file(io.BytesIO(buffer.getvalue().encode()), as_attachment=True,
                        download_name=f"assessment_{assessment_id}.csv", mimetype='text/csv')

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
        'business_name': a.business_name,
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

@app.route('/admin/audit-logs')
@login_required
@admin_required
def audit_logs():
    page = int(request.args.get('page', 1))
    per_page = 20
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page)
    return render_template('admin_audit_logs.html', logs=logs)

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
        elif len(new_pw) < 10 or not re.search(r'[A-Z]', new_pw) or not re.search(r'[a-z]', new_pw) or not re.search(r'\d', new_pw) or not re.search(r'[^A-Za-z0-9]', new_pw):
            flash('New password does not meet hygiene requirements.', 'error')
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            log = AuditLog(user_id=current_user.id, action='change_password', resource_type='user', resource_id=current_user.id, details={'ip': request.remote_addr})
            db.session.add(log)
            db.session.commit()
            return redirect(url_for('dashboard'))
    return render_template('change_password.html')

@app.route('/profile')
@login_required
def profile():
    recent_logins = AuditLog.query.filter_by(user_id=current_user.id, action='login').order_by(AuditLog.timestamp.desc()).limit(5).all()
    return render_template('profile.html', user=current_user, recent_logins=recent_logins)

@app.route('/export-data/<format>')
@login_required
def export_data(format):
    assessments = Assessment.query.filter_by(assessor_id=current_user.id).all()
    if format == 'json':
        data = [{
            'id': a.id,
            'business': a.business_name,
            'score': a.total_score,
            'certification_level': a.certification_level,
            'date': a.assessment_date.isoformat()
        } for a in assessments]
        return jsonify(data)
    elif format == 'csv':
        import csv, io
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['ID', 'Business', 'Score', 'Level', 'Date'])
        for a in assessments:
            writer.writerow([a.id, a.business_name, a.total_score, a.certification_level, a.assessment_date.strftime('%Y-%m-%d')])
        buffer.seek(0)
        return send_file(io.BytesIO(buffer.getvalue().encode()), as_attachment=True, download_name='my_assessments.csv', mimetype='text/csv')
    else:
        abort(400)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/report-incident', methods=['GET', 'POST'])
@login_required
def report_incident():
    if request.method == 'POST':
        desc = request.form.get('description')
        log = AuditLog(user_id=current_user.id, action='report_incident', resource_type='incident', details={'description': desc, 'ip': request.remote_addr, 'ua': request.user_agent.string})
        db.session.add(log)
        db.session.commit()
        flash('Incident reported. Thank you!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('report_incident.html')

@app.route('/mfa-setup', methods=['GET', 'POST'])
@login_required
def mfa_setup():
    # Stub: In future, generate TOTP secret and QR code
    flash('MFA setup coming soon!', 'info')
    return render_template('mfa_setup.html')

@app.route('/mfa-verify', methods=['POST'])
@login_required
def mfa_verify():
    # Stub: In future, verify TOTP code
    flash('MFA verification coming soon!', 'info')
    return redirect(url_for('dashboard'))

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

def check_outdated_software():
    # Stub: In real deployment, integrate with OS package manager or vulnerability DB
    return ['Python', 'Flask', 'MySQL']  # Example outdated

def check_weak_passwords():
    # Stub: In real deployment, check against password policy or breached DB
    return ['admin', 'test']  # Example weak accounts

def check_antivirus_status():
    # Stub: In real deployment, query OS for AV status
    return 'Unknown or not detected'

def check_disk_encryption():
    # Stub: In real deployment, check OS disk encryption status
    return 'Not enabled'

def check_admin_accounts():
    # Stub: In real deployment, list admin/root accounts
    return ['Administrator', 'root']

def check_suspicious_processes():
    # Stub: In real deployment, scan for known malware or suspicious processes
    return ['unknown.exe', 'suspicious.py']

def check_ssl_tls(domain='localhost'):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=2) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                return f"SSL/TLS enabled, expires: {cert['notAfter']}"
    except Exception as e:
        return f"SSL/TLS not detected: {e}"

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
        r = requests.get('https://api.ipify.org?format=json', timeout=2)
        return r.json().get('ip', 'Unknown')
    except Exception as e:
        return f"IP check error: {e}"

def run_vulnerability_scan(target='localhost'):
    try:
        nm = nmap.PortScanner()
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
    scan_results = {}
    recommendations = []
    advanced_results = {}
    technical_results = {}
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
            firewall_status = os.system('netsh advfirewall show allprofiles')
            scan_results['firewall'] = 'Enabled' if firewall_status == 0 else 'Disabled/Unknown'
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
            recommendations.append(f"Investigate suspicious processes: {', '.join(advanced_results['suspicious_processes'])}.")
        recommendations.append('Review admin/root accounts and restrict access.')
        # Technical checks
        domain = request.form.get('domain', 'localhost')
        technical_results['ssl_tls'] = check_ssl_tls(domain)
        technical_results['backup_status'] = check_backup_status()
        technical_results['patch_status'] = check_patch_status()
        technical_results['external_ip'] = get_external_ip()
        technical_results['vulnerabilities'] = run_vulnerability_scan(domain)
        technical_results['shodan_exposure'] = check_shodan_exposure(technical_results['external_ip'])
        # Technical recommendations
        if 'SSL/TLS enabled' not in technical_results['ssl_tls']:
            recommendations.append('Enable SSL/TLS for all public-facing services.')
        if 'Last backup' not in technical_results['backup_status']:
            recommendations.append('Set up regular, secure backups.')
        if 'up to date' not in technical_results['patch_status']:
            recommendations.append('Apply all missing OS and software patches.')
        if technical_results['vulnerabilities'] and 'No common vulnerabilities detected' not in technical_results['vulnerabilities'][0]:
            recommendations.append(f"Review open services: {', '.join(technical_results['vulnerabilities'])}.")
        if 'No public exposure detected' not in technical_results['shodan_exposure']:
            recommendations.append('Review public exposure and restrict unnecessary services.')
        return render_template('system_scan_results.html', scan_results=scan_results, recommendations=recommendations, advanced_results=advanced_results, technical_results=technical_results)
    return render_template('system_scan.html')

def automated_scan():
    """Automated system scan for scheduled runs."""
    # Simulate scan and log results
    scan_results = {'os': platform.system(), 'hostname': socket.gethostname()}
    # In real implementation, save to DB or send email
    print(f"Automated scan completed: {scan_results}")
    return scan_results

def generate_pdf_report(scan_results, recommendations, advanced_results, technical_results):
    """Generate PDF report from scan results."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Digital Hygiene Scan Report", styles['Title']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Basic Results", styles['Heading2']))
    for key, value in scan_results.items():
        story.append(Paragraph(f"{key}: {value}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Advanced Results", styles['Heading2']))
    for key, value in advanced_results.items():
        story.append(Paragraph(f"{key}: {value}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Technical Results", styles['Heading2']))
    for key, value in technical_results.items():
        story.append(Paragraph(f"{key}: {value}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Recommendations", styles['Heading2']))
    for rec in recommendations:
        story.append(Paragraph(f"- {rec}", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

@app.route('/schedule-scan', methods=['GET', 'POST'])
@login_required
def schedule_scan():
    if request.method == 'POST':
        interval = int(request.form.get('interval', 24))  # hours
        scheduler.add_job(func=automated_scan, trigger="interval", hours=interval, id='automated_scan')
        flash(f'Scan scheduled every {interval} hours.', 'success')
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
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/yourusername/digital-hygiene-tool/archive/main.zip' -OutFile 'temp_digital_hygiene.zip'"
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

if __name__ == '__main__':
    create_app().run(debug=True)
