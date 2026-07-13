"""
Admin dashboard routes.

All routes are prefixed with /admin and require the admin role.
"""

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, abort, send_file,
)
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
import io
import csv
import platform

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

admin_bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates',
    url_prefix='/admin',
)


# ------------------------------------------------------------------
# Decorator – every admin route must pass this
# ------------------------------------------------------------------
def admin_required(f):
    """Decorator that restricts access to admin users."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ------------------------------------------------------------------
# Helper – lazily import models from the main app module
# ------------------------------------------------------------------
def _models():
    """Return (db, User, Business, Assessment, Certificate, AuditLog)."""
    from src.web.app import db, User, Business, Assessment, Certificate, AuditLog
    return db, User, Business, Assessment, Certificate, AuditLog


# ══════════════════════════════════════════════════════════════════
# 1.  ADMIN DASHBOARD  (overview / landing page)
# ══════════════════════════════════════════════════════════════════
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin overview – KPIs, charts data, recent activity."""
    db, User, Business, Assessment, Certificate, AuditLog = _models()

    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)

    # ---- KPI cards ----
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_businesses = Business.query.count()
    total_assessments = Assessment.query.count()
    assessments_this_month = Assessment.query.filter(
        Assessment.created_at >= thirty_days_ago
    ).count()

    total_certs = Certificate.query.filter_by(is_active=True).count()
    expiring_soon = Certificate.query.filter(
        Certificate.expiry_date <= now + timedelta(days=30),  # type: ignore[operator]
        Certificate.is_active.is_(True),  # type: ignore[union-attr]
    ).count()

    # ---- Certification distribution ----
    cert_levels = {}
    for a in Assessment.query.with_entities(
        Assessment.certification_level,  # type: ignore[arg-type]
        db.func.count(Assessment.id),
    ).group_by(Assessment.certification_level).all():
        cert_levels[a[0]] = a[1]

    # ---- Score trend (last 12 months) ----
    score_trend = []
    for i in range(11, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        if i > 0:
            month_end = (now.replace(day=1) - timedelta(days=30 * (i - 1))).replace(day=1)
        else:
            month_end = now
        avg = db.session.query(db.func.avg(Assessment.total_score)).filter(
            Assessment.created_at >= month_start,
            Assessment.created_at < month_end,
        ).scalar()
        score_trend.append({
            'label': month_start.strftime('%b %Y'),
            'avg': round(avg, 1) if avg else 0,
        })

    # ---- Recent activity ----
    recent_logs = AuditLog.query.order_by(
        AuditLog.timestamp.desc()
    ).limit(10).all()

    recent_assessments = Assessment.query.order_by(
        Assessment.created_at.desc()
    ).limit(5).all()

    # ---- System info ----
    system_info = {
        'os': f"{platform.system()} {platform.release()}",
        'python': platform.python_version(),
        'db_uri': _mask_db_uri(),
    }

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        active_users=active_users,
        total_businesses=total_businesses,
        total_assessments=total_assessments,
        assessments_this_month=assessments_this_month,
        total_certs=total_certs,
        expiring_soon=expiring_soon,
        cert_levels=cert_levels,
        score_trend=score_trend,
        recent_logs=recent_logs,
        recent_assessments=recent_assessments,
        system_info=system_info,
    )


# ══════════════════════════════════════════════════════════════════
# 2.  USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all user accounts."""
    db, User, *_ = _models()
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    query = User.query
    if q:
        query = query.filter(  # type: ignore[arg-type]
            User.username.ilike(f'%{q}%') | User.email.ilike(f'%{q}%')  # type: ignore[attr-defined]
        )
    users_page = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20
    )
    return render_template('admin/users.html', users=users_page, q=q)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def user_create():
    """Create a new user."""
    db, User, *_ = _models()
    _, _, _, _, _, AuditLog = _models()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'assessor')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('admin/user_form.html', mode='create')

        if User.query.filter(
            (User.username == username) | (User.email == email)  # type: ignore[arg-type]
        ).first():
            flash('Username or email already exists.', 'error')
            return render_template('admin/user_form.html', mode='create')

        user = User(username=username, email=email, role=role, is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        log = AuditLog(
            user_id=current_user.id, action='admin_create_user',
            resource_type='user', resource_id=user.id,
            details={'target': username, 'ip': request.remote_addr},
        )
        db.session.add(log)
        db.session.commit()
        flash(f'User "{username}" created.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', mode='create')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(user_id):
    """Edit an existing user."""
    db, User, *_ = _models()
    _, _, _, _, _, AuditLog = _models()
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form.get('username', user.username).strip()
        user.email = request.form.get('email', user.email).strip()
        user.role = request.form.get('role', user.role)
        user.is_active = request.form.get('is_active') == 'on'
        new_pw = request.form.get('password', '').strip()
        if new_pw:
            user.set_password(new_pw)
        db.session.flush()
        log = AuditLog(
            user_id=current_user.id, action='admin_edit_user',
            resource_type='user', resource_id=user.id,
            details={'target': user.username, 'ip': request.remote_addr},
        )
        db.session.add(log)
        db.session.commit()
        flash(f'User "{user.username}" updated.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', mode='edit', user=user)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def user_toggle(user_id):
    """Enable / disable a user account."""
    db, User, *_ = _models()
    _, _, _, _, _, AuditLog = _models()
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot disable your own account.', 'error')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    action = 'admin_enable_user' if user.is_active else 'admin_disable_user'
    log = AuditLog(
        user_id=current_user.id, action=action,
        resource_type='user', resource_id=user.id,
        details={'target': user.username, 'ip': request.remote_addr},
    )
    db.session.add(log)
    db.session.commit()
    flash(f'User "{user.username}" {"enabled" if user.is_active else "disabled"}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def user_delete(user_id):
    """Delete a user account."""
    db, User, *_ = _models()
    _, _, _, _, _, AuditLog = _models()
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    username = user.username
    log = AuditLog(
        user_id=current_user.id, action='admin_delete_user',
        resource_type='user', resource_id=user.id,
        details={'target': username, 'ip': request.remote_addr},
    )
    db.session.add(log)
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{username}" deleted.', 'success')
    return redirect(url_for('admin.users'))


# ══════════════════════════════════════════════════════════════════
# 3.  BUSINESS MANAGEMENT
# ══════════════════════════════════════════════════════════════════
@admin_bp.route('/businesses')
@login_required
@admin_required
def businesses():
    """List registered businesses."""
    db, _, Business, *_ = _models()
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    query = Business.query
    if q:
        query = query.filter(  # type: ignore[arg-type]
            Business.name.ilike(f'%{q}%') |  # type: ignore[attr-defined]
            Business.registration_number.ilike(f'%{q}%')  # type: ignore[attr-defined]
        )
    page_data = query.order_by(Business.created_at.desc()).paginate(
        page=page, per_page=20
    )
    return render_template('admin/businesses.html', businesses=page_data, q=q)


@admin_bp.route('/businesses/<int:biz_id>')
@login_required
@admin_required
def business_detail(biz_id):
    """Business detail with assessment history."""
    db, _, Business, Assessment, *_ = _models()
    biz = Business.query.get_or_404(biz_id)
    assessments = Assessment.query.filter_by(business_id=biz.id).order_by(
        Assessment.created_at.desc()
    ).all()
    return render_template('admin/business_detail.html', business=biz, assessments=assessments)


# ══════════════════════════════════════════════════════════════════
# 4.  ASSESSMENTS OVERVIEW
# ══════════════════════════════════════════════════════════════════
@admin_bp.route('/assessments')
@login_required
@admin_required
def assessments():
    """View all assessments across the platform."""
    db, _, _, Assessment, *_ = _models()
    page = request.args.get('page', 1, type=int)
    level = request.args.get('level', '').strip()
    query = Assessment.query
    if level:
        query = query.filter_by(certification_level=level)
    page_data = query.order_by(Assessment.created_at.desc()).paginate(
        page=page, per_page=20
    )
    return render_template('admin/assessments.html', assessments=page_data, level=level)


# ══════════════════════════════════════════════════════════════════
# 5.  CERTIFICATES
# ══════════════════════════════════════════════════════════════════
@admin_bp.route('/certificates')
@login_required
@admin_required
def certificates():
    """View and manage certificates."""
    db, _, _, _, Certificate, _ = _models()
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '').strip()
    query = Certificate.query
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'expired':
        query = query.filter(Certificate.expiry_date < datetime.utcnow())  # type: ignore[operator]
    elif status_filter == 'expiring':
        query = query.filter(
            Certificate.expiry_date <= datetime.utcnow() + timedelta(days=30),  # type: ignore[operator]
            Certificate.expiry_date >= datetime.utcnow(),  # type: ignore[operator]
            Certificate.is_active.is_(True),  # type: ignore[union-attr]
        )
    page_data = query.order_by(Certificate.created_at.desc()).paginate(
        page=page, per_page=20
    )
    return render_template('admin/certificates.html', certificates=page_data, status=status_filter)


@admin_bp.route('/certificates/<int:cert_id>/revoke', methods=['POST'])
@login_required
@admin_required
def certificate_revoke(cert_id):
    """Revoke a certificate, recording a reason."""
    db, _, _, _, Certificate, AuditLog = _models()
    cert = Certificate.query.get_or_404(cert_id)
    reason = (request.form.get('reason') or '').strip() or 'No reason provided'
    cert.is_active = False
    data = dict(cert.certificate_data or {})
    data['revocation'] = {
        'type': 'revoked',
        'reason': reason,
        'revoked_at': datetime.utcnow().date().isoformat(),
        'revoked_by': current_user.username,
    }
    cert.certificate_data = data
    log = AuditLog(
        user_id=current_user.id, action='admin_revoke_certificate',
        resource_type='certificate', resource_id=cert.id,
        details={'cert_number': cert.certificate_number,
                 'reason': reason, 'ip': request.remote_addr},
    )
    db.session.add(log)
    db.session.commit()
    flash(f'Certificate {cert.certificate_number} revoked.', 'success')
    return redirect(url_for('admin.certificates'))


# ══════════════════════════════════════════════════════════════════
# 6.  AUDIT LOGS (moved from main app – kept at old URL too)
# ══════════════════════════════════════════════════════════════════
@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """Browse audit trail."""
    db, User, _, _, _, AuditLog = _models()
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()
    user_filter = request.args.get('user_id', '', type=str).strip()

    query = AuditLog.query
    if action_filter:
        query = query.filter(AuditLog.action.ilike(f'%{action_filter}%'))  # type: ignore[attr-defined, arg-type]
    if user_filter:
        query = query.filter_by(user_id=int(user_filter))

    page_data = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=25
    )

    # For the filter dropdown
    distinct_actions = [r[0] for r in db.session.query(
        AuditLog.action  # type: ignore[arg-type]
    ).distinct().order_by(AuditLog.action).all()]

    all_users = User.query.order_by(User.username).all()

    return render_template(
        'admin/audit_logs.html',
        logs=page_data,
        action_filter=action_filter,
        user_filter=user_filter,
        distinct_actions=distinct_actions,
        all_users=all_users,
    )


# ══════════════════════════════════════════════════════════════════
# 7.  SYSTEM SETTINGS / HEALTH
# ══════════════════════════════════════════════════════════════════
@admin_bp.route('/system')
@login_required
@admin_required
def system():
    """System health and configuration summary."""
    import psutil

    db, User, Business, Assessment, Certificate, AuditLog = _models()

    # Counts
    counts = {
        'users': User.query.count(),
        'businesses': Business.query.count(),
        'assessments': Assessment.query.count(),
        'certificates': Certificate.query.count(),
        'audit_logs': AuditLog.query.count(),
    }

    # Hardware
    hw = {
        'os': f"{platform.system()} {platform.release()}",
        'python': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'cpu_percent': psutil.cpu_percent(interval=0.5),
        'memory': psutil.virtual_memory()._asdict(),
        'disk': (
            psutil.disk_usage('/')._asdict()
            if platform.system() != 'Windows'
            else psutil.disk_usage('C:\\')._asdict()
        ),
    }

    return render_template('admin/system.html', counts=counts, hw=hw)


# ══════════════════════════════════════════════════════════════════
# 8.  ADMIN DATA EXPORT
# ══════════════════════════════════════════════════════════════════
@admin_bp.route('/export/<string:resource>/<string:fmt>')
@login_required
@admin_required
def admin_export(resource, fmt):
    """Export platform data as CSV or JSON."""
    db, User, Business, Assessment, Certificate, AuditLog = _models()

    if resource == 'users':
        rows = [{'id': u.id, 'username': u.username, 'email': u.email,
                 'role': u.role, 'active': u.is_active,
                 'created': u.created_at.isoformat()} for u in User.query.all()]
    elif resource == 'assessments':
        rows = [{'id': a.id, 'business': a.business.name if a.business else '',
                 'score': a.total_score, 'level': a.certification_level,
                 'date': a.created_at.isoformat()} for a in Assessment.query.all()]
    elif resource == 'businesses':
        rows = [{'id': b.id, 'name': b.name, 'reg': b.registration_number,
                 'industry': b.industry,
                 'created': b.created_at.isoformat()} for b in Business.query.all()]
    else:
        abort(404)

    if fmt == 'json':
        return jsonify(rows)
    elif fmt == 'csv':
        if not rows:
            abort(404, description='No data to export.')
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        buf.seek(0)
        return send_file(
            io.BytesIO(buf.getvalue().encode()),
            as_attachment=True,
            download_name=f'{resource}_{datetime.utcnow():%Y%m%d}.csv',
            mimetype='text/csv',
        )
    abort(400)


# ══════════════════════════════════════════════════════════════════
# 9.  JSON API – chart data for the admin dashboard
# ══════════════════════════════════════════════════════════════════
@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """Return stats JSON for dashboard charts (AJAX)."""
    db, User, Business, Assessment, Certificate, AuditLog = _models()

    now = datetime.utcnow()

    # Cert-level distribution
    level_counts = dict(
        db.session.query(Assessment.certification_level, db.func.count(Assessment.id))  # type: ignore[call-overload]
        .group_by(Assessment.certification_level).all()
    )

    # Monthly assessment counts (last 12 months)
    monthly = []
    for i in range(11, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        if i > 0:
            month_end = (now.replace(day=1) - timedelta(days=30 * (i - 1))).replace(day=1)
        else:
            month_end = now
        cnt = Assessment.query.filter(
            Assessment.created_at >= month_start,
            Assessment.created_at < month_end,
        ).count()
        monthly.append({'label': month_start.strftime('%b %Y'), 'count': cnt})

    # Industry breakdown
    industry = dict(
        db.session.query(Business.industry, db.func.count(Business.id))  # type: ignore[call-overload]
        .group_by(Business.industry).all()
    )

    return jsonify({
        'cert_levels': level_counts,
        'monthly_assessments': monthly,
        'industry_breakdown': industry,
    })


# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------
def _mask_db_uri():
    """Return the DB URI with password masked."""
    from flask import current_app
    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    # Mask password in mysql://user:pass@host/db
    import re
    return re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', uri)
