"""Quick login test using Flask test client."""

from src.web.app import create_app, db, User

app = create_app()

with app.app_context():
    # Ensure admin user exists
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", email="admin@digitalhygiene.gov.zm")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

    client = app.test_client()
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True,
    )

    path = response.request.path if response.request else ""
    body = response.get_data(as_text=True)
    if response.status_code == 200 and "dashboard" in path:
        print("✓ Login succeeded, landed on dashboard")
    else:
        print("❌ Login failed")
        print(f"Status: {response.status_code}, Path: {path}")
        if "Invalid username or password" in body:
            print("Server reported invalid credentials")
        else:
            print(body[:500])
