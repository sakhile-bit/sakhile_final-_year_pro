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
    app,
    db,
    create_app,
    login_manager,
    csrf,
    # Models
    User,
    Business,
    Assessment,
    Certificate,
    AuditLog,
    AssessmentRequest,
    Remediation,
    # Helpers / utilities
    login_attempts,
    load_user,
    check_password_strength,
    admin_required,
    rate_limit,
)

if __name__ == "__main__":
    import os
    application = create_app()
    application.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", port=5000)
