from src.web.app import create_app, db, User

app = create_app()

with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if user:
        user.set_password('admin123')
        db.session.commit()
        print('Admin password reset to admin123')
    else:
        user = User(username='admin', email='admin@digitalhygiene.gov.zm')
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        print('Admin user created with password admin123')
