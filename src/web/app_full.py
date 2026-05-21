"""
Phase 2 — Full Assessment Platform (Zambia Digital Hygiene Certification Program)

This module provides a backward-compatible alias for `src.web.app`.

The canonical application implementation now lives in `src.web.app`.
`app_full` remains so older imports continue to work without change.

Phase 2 features:
    - User authentication (login / register / MFA)
    - Role-based dashboard (admin / assessor / business_owner)
    - Online assessment submission and results
    - Certificate generation and public verification
    - Admin panel (users, businesses, assessments, certificates, audit logs)
    - Incident reporting and pre-deployment checks
"""

# Re-export the entire Phase 2 app surface from the canonical app module
from src.web.app import (  # noqa: F401
    app as app,
    db as db,
    create_app as create_app,
    login_manager as login_manager,
    csrf as csrf,
    # Models
    User as User,
    Business as Business,
    Assessment as Assessment,
    Certificate as Certificate,
    AuditLog as AuditLog,
    AssessmentRequest as AssessmentRequest,
    Remediation as Remediation,
    # Helpers / utilities
    login_attempts as login_attempts,
    load_user as load_user,
    check_password_strength as check_password_strength,
    admin_required as admin_required,
    rate_limit as rate_limit,
)

if __name__ == "__main__":
    import os
    application = create_app()
    application.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", port=5000)
