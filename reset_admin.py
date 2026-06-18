"""Utility: reset the admin account password.

Set ADMIN_DEFAULT_PASSWORD in the environment before running, or enter it
interactively when prompted.  Never hardcode a password in this file.
"""
import os
import getpass
from src.web.app import create_app, db, User

new_password = os.environ.get('ADMIN_DEFAULT_PASSWORD', '').strip()
if not new_password:
    new_password = getpass.getpass('New admin password: ')
if not new_password:
    raise SystemExit('No password provided — aborting.')

app = create_app()

with app.app_context():
    user: User | None = User.query.filter_by(username='admin').first()
    if user is not None:
        user.set_password(new_password)
        db.session.commit()
        print('Admin password updated.')
    else:
        new_user = User(username='admin', email='admin@digitalhygiene.gov.zm')  # type: ignore[call-arg]
        new_user.set_password(new_password)
        db.session.add(new_user)
        db.session.commit()
        print('Admin user created.')
