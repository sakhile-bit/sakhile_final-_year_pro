"""
MySQL Database Setup and Initialization Script
Zambia Digital Hygiene Assessment Tool

This script:
1. Creates the database and user
2. Sets up tables and indexes
3. Inserts sample data (optional)
4. Verifies the setup
"""

import sys
import subprocess
from pathlib import Path


def _mysql_args(db_host: str, db_port: str, db_user: str, db_password: str) -> list:
    """Return the base mysql argument list (no shell, no interpolation)."""
    return ['mysql', f'-h{db_host}', f'-P{db_port}', f'-u{db_user}', f'-p{db_password}']


def main():
    """Main setup function."""
    print("""
    â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    â•‘  MySQL Database Setup for Digital Hygiene Assessment Tool  â•‘
    â•‘  Production Configuration                                  â•‘
    â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    """)

    # Check if MySQL is installed
    print("\n1ï¸âƒ£  Checking MySQL installation...")
    result = subprocess.run(['mysql', '--version'], capture_output=True, text=True)
    if result.returncode != 0:
        print("""
        âŒ MySQL is not installed or not in PATH.

        Installation options:

        A. Windows (Chocolatey):
           choco install mysql -y

        B. Windows (Direct):
           Download from https://dev.mysql.com/downloads/mysql/

        C. Windows (Docker - Recommended):
           docker run -d \\
             --name mysql \\
             -p 3306:3306 \\
             -e MYSQL_ROOT_PASSWORD=admin123 \\
             mysql:8.0.35

        Then re-run this script.
        """)
        return False

    print(f"âœ“ MySQL found: {result.stdout.strip()}")

    # Get database credentials
    print("\n2ï¸âƒ£  Configuring database credentials...")

    db_host = input("Enter MySQL host [localhost]: ").strip() or "localhost"
    db_port = input("Enter MySQL port [3306]: ").strip() or "3306"
    db_user = input("Enter MySQL root user [root]: ").strip() or "root"
    import getpass
    db_password = getpass.getpass("Enter MySQL root password: ") or "admin123"
    db_name = input("Enter new database name [digital_hygiene]: ").strip() or "digital_hygiene"
    app_user = input("Enter app database user [dhassess]: ").strip() or "dhassess"
    app_password = getpass.getpass("Enter app database password: ") or "SecurePass123!"

    print(f"""
    Configuration:
    - Host: {db_host}
    - Port: {db_port}
    - Root User: {db_user}
    - Database: {db_name}
    - App User: {app_user}
    """)

    # Check MySQL connection
    print("\n3ï¸âƒ£  Testing MySQL connection...")
    base_args = _mysql_args(db_host, db_port, db_user, db_password)
    result = subprocess.run(
        base_args + ['-e', 'SELECT 1;'],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        print(f"""
        âŒ Cannot connect to MySQL.
        Error: {result.stderr}

        Troubleshooting:
        1. Verify MySQL is running: net start MySQL80 (Windows)
        2. Check credentials and host/port.
        """)
        return False

    print("âœ“ MySQL connection successful")

    # Create database and user
    print("\n4ï¸âƒ£  Creating database and user...")

    # Read SQL schema
    sql_file = Path(__file__).parent / "init.sql"
    if not sql_file.exists():
        print(f"âŒ SQL file not found: {sql_file}")
        return False

    # Execute schema â€” pass file content via stdin (no shell interpolation)
    print(f"Executing: {sql_file}")
    with open(sql_file, 'rb') as fh:
        result = subprocess.run(
            base_args,
            stdin=fh,
            capture_output=True, text=True,
        )

    if result.returncode != 0:
        print(f"âŒ Schema creation failed: {result.stderr}")
        return False

    print(f"âœ“ Database schema created: {db_name}")

    # Create application user â€” use parameterised argument list, not shell
    print("\n5ï¸âƒ£  Creating application user...")
    create_user_sql = (
        f"CREATE USER IF NOT EXISTS '{app_user}'@'{db_host}' IDENTIFIED BY '{app_password}';"
        f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{app_user}'@'{db_host}';"
        "FLUSH PRIVILEGES;"
    )
    result = subprocess.run(
        base_args + ['-e', create_user_sql],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        print(f"âš ï¸  User creation issue (may already exist): {result.stderr}")
    else:
        print(f"âœ“ Application user created: {app_user}")

    # Verify setup
    print("\n6ï¸âƒ£  Verifying database setup...")
    verify_sql = (
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
        f"WHERE TABLE_SCHEMA = '{db_name}';"
    )
    app_base = _mysql_args(db_host, db_port, app_user, app_password)
    result = subprocess.run(
        app_base + ['-e', verify_sql],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        tables = result.stdout.strip().split('\n')[1:]  # Skip header
        print(f"âœ“ Created {len(tables)} tables:")
        for table in tables:
            if table.strip():
                print(f"  - {table}")
    else:
        print(f"âŒ Verification failed: {result.stderr}")
        return False

    # Generate connection string
    print("\n7ï¸âƒ£  Database Setup Complete! ðŸŽ‰")
    print(f"""
    â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    â•‘  MySQL Connection Details                                  â•‘
    â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
    â•‘  Host:     {db_host:<50}â•‘
    â•‘  Port:     {db_port:<50}â•‘
    â•‘  Database: {db_name:<50}â•‘
    â•‘  User:     {app_user:<50}â•‘
    â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    âš™ï¸  Set these environment variables:

    Windows (PowerShell):
        $env:DB_HOST = "{db_host}"
        $env:DB_PORT = "{db_port}"
        $env:DB_NAME = "{db_name}"
        $env:DB_USER = "{app_user}"
        $env:DB_PASSWORD = "<your-app-password>"

    âœ… Next steps:
    1. Set the environment variables above (do not hardcode passwords)
    2. Start the Flask app: python src/web/app.py
    3. Open http://localhost:5000 in your browser
    4. Login with admin and the password set in ADMIN_DEFAULT_PASSWORD env var
    """)

    # Create .env file option
    create_env = input("\nðŸ“ Create .env file with these settings? [y/N]: ").strip().lower()
    if create_env == 'y':
        env_content = f"""# MySQL Database Configuration
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={app_user}
# Set DB_PASSWORD via a secrets manager or CI secret â€” do not commit this file
DB_PASSWORD=

# Flask Configuration
DEBUG=false
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY=
LOG_LEVEL=INFO
WEB_HOST=0.0.0.0
WEB_PORT=5000
"""
        env_file = Path(__file__).parent.parent / ".env"
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"âœ“ Created .env file: {env_file}")
        print("âš ï¸  Fill in DB_PASSWORD and SECRET_KEY â€” never commit real credentials to git.")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nâŒ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nâŒ Error: {e}")
        sys.exit(1)
