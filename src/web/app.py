"""
Flask web application for the Zambia Digital Hygiene Assessment Tool
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import json
import csv
import io

from assessment.assessor import DigitalHygieneAssessor, BusinessInfo
from reporting.generator import ReportGenerator
from database.connection import DatabaseManager
from utils.logging_config import get_logger
from utils.config import config

logger = get_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.app.secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = config.database.connection_string
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Assessment model
class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(200), nullable=False)
    business_id = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    industry = db.Column(db.String(100))
    address = db.Column(db.Text)
    score = db.Column(db.Integer, nullable=False)
    total_possible = db.Column(db.Integer, nullable=False)
    certification_level = db.Column(db.String(20), nullable=False)
    assessment_data = db.Column(db.Text, nullable=False)  # JSON data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    """Create and configure the Flask application"""
    # Create database tables
    with app.app_context():
        db.create_all()

        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@zambia.gov.zm', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

    return app

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
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
    assessments = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.created_at.desc()).all()

    # Calculate statistics
    total_assessments = len(assessments)
    avg_score = sum(a.score for a in assessments) / total_assessments if total_assessments > 0 else 0
    certification_counts = {}
    for assessment in assessments:
        cert = assessment.certification_level
        certification_counts[cert] = certification_counts.get(cert, 0) + 1

    stats = {
        'total_assessments': total_assessments,
        'average_score': round(avg_score, 1),
        'certification_counts': certification_counts
    }

    return render_template('dashboard.html', assessments=assessments, stats=stats)

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

            # Run assessment
            assessor = DigitalHygieneAssessor(business_info)
            results = assessor.run_assessment()

            # Save to database
            assessment = Assessment(
                business_name=business_info.name,
                business_id=business_info.id,
                contact_person=business_info.contact_person,
                contact_email=business_info.contact_email,
                contact_phone=business_info.contact_phone,
                industry=business_info.industry,
                address=business_info.address,
                score=results.score,
                total_possible=results.total_possible,
                certification_level=results.certification_level,
                assessment_data=json.dumps({
                    'controls': {k: v.__dict__ for k, v in results.controls.items()},
                    'recommendations': results.recommendations
                }),
                user_id=current_user.id
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
    assessment = Assessment.query.filter_by(id=assessment_id, user_id=current_user.id).first_or_404()

    # Parse assessment data
    data = json.loads(assessment.assessment_data)
    results = type('Results', (), {
        'score': assessment.score,
        'total_possible': assessment.total_possible,
        'certification_level': assessment.certification_level,
        'controls': {k: type('Control', (), v) for k, v in data['controls'].items()},
        'recommendations': data['recommendations']
    })()

    business_info = BusinessInfo(
        name=assessment.business_name,
        id=assessment.business_id,
        contact_person=assessment.contact_person,
        contact_email=assessment.contact_email,
        contact_phone=assessment.contact_phone,
        industry=assessment.industry,
        address=assessment.address
    )

    return render_template('results.html', results=results, business_info=business_info, assessment_id=assessment_id)

@app.route('/download/<int:assessment_id>/<format>')
@login_required
def download_report(assessment_id, format):
    """Download assessment report"""
    assessment = Assessment.query.filter_by(id=assessment_id, user_id=current_user.id).first_or_404()

    # Parse assessment data
    data = json.loads(assessment.assessment_data)
    results = type('Results', (), {
        'score': assessment.score,
        'total_possible': assessment.total_possible,
        'certification_level': assessment.certification_level,
        'controls': {k: type('Control', (), v) for k, v in data['controls'].items()},
        'recommendations': data['recommendations']
    })()

    business_info = BusinessInfo(
        name=assessment.business_name,
        id=assessment.business_id,
        contact_person=assessment.contact_person,
        contact_email=assessment.contact_email,
        contact_phone=assessment.contact_phone,
        industry=assessment.industry,
        address=assessment.address
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
    assessments = Assessment.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': a.id,
        'business_name': a.business_name,
        'score': a.score,
        'certification_level': a.certification_level,
        'created_at': a.created_at.isoformat()
    } for a in assessments])

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    create_app().run(debug=True)
