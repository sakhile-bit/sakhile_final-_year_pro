from src.web.app import create_app, db, User

app = create_app()

with app.app_context():
    user: User | None = User.query.filter_by(username='admin').first()
    if user is not None:
        user.set_password('admin123')
        db.session.commit()
        print('Admin password reset to admin123')
    else:
        new_user = User(username='admin', email='admin@digitalhygiene.gov.zm')  # type: ignore[call-arg]
        new_user.set_password('admin123')
        db.session.add(new_user)
        db.session.commit()
        print('Admin user created with password admin123')
