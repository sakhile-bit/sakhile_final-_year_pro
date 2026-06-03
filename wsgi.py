"""WSGI entry point for gunicorn / uWSGI production deployment.

Usage:
    gunicorn wsgi:application --bind 0.0.0.0:5000 --workers 4

Environment variables required in production:
    SECRET_KEY      — long random string (generate: python -c "import secrets; print(secrets.token_urlsafe(64))")
    DB_HOST         — MySQL host
    DB_NAME         — database name
    DB_USER         — database user
    DB_PASSWORD     — database password
"""
from src.web.app import create_app

application = create_app()
