"""Test MySQL connection from Flask app"""
from src.web.app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Test connection
        result = db.session.execute(text('SELECT 1'))
        print("✓ Connected to MySQL successfully!")
        
        # Get table list
        result = db.session.execute(text('SHOW TABLES'))
        tables = result.fetchall()
        print(f"✓ Tables in database: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Query users table
        result = db.session.execute(text('SELECT COUNT(*) as count FROM users'))
        count = result.fetchone()[0]
        print(f"\n✓ Users in database: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
