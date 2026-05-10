"""
Phase 2 — Full Assessment Platform (Zambia Digital Hygiene Certification Program)

This module activates the complete web platform by re-exporting everything
from app_full.  All callers that do `from src.web.app import ...` will
transparently receive the Phase 2 objects.

Phase 2 features:
    - User authentication (login / register / MFA)
    - Role-based dashboard (admin / assessor / business_owner)
    - Online assessment submission and results
    - Certificate generation and public verification
    - Admin panel (users, businesses, assessments, certificates, audit logs)
    - Incident reporting and pre-deployment checks
"""

# Re-export the entire Phase 2 app surface
from src.web.app_full import (  # noqa: F401
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
