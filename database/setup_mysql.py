"""
MySQL Database Setup and Initialization Script
Zambia Digital Hygiene Assessment Tool

This script:
1. Creates the database and user
2. Sets up tables and indexes
3. Inserts sample data (optional)
4. Verifies the setup
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and report results."""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"{'='*60}")
    print(f"$ {cmd}")
    print()
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ Failed: {description}")
        return False
    print(f"\n✓ Completed: {description}")
    return True


def main():
    """Main setup function."""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  MySQL Database Setup for Digital Hygiene Assessment Tool  ║
    ║  Production Configuration                                  ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Check if MySQL is installed
    print("\n1️⃣  Checking MySQL installation...")
    result = subprocess.run("mysql --version", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("""
        ❌ MySQL is not installed or not in PATH.
        
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
    
    print(f"✓ MySQL found: {result.stdout.strip()}")
    
    # Get database credentials
    print("\n2️⃣  Configuring database credentials...")
    
    db_host = input("Enter MySQL host [localhost]: ").strip() or "localhost"
    db_port = input("Enter MySQL port [3306]: ").strip() or "3306"
    db_user = input("Enter MySQL root user [root]: ").strip() or "root"
    db_password = input("Enter MySQL root password [admin123]: ").strip() or "admin123"
    db_name = input("Enter new database name [digital_hygiene]: ").strip() or "digital_hygiene"
    app_user = input("Enter app database user [dhassess]: ").strip() or "dhassess"
    app_password = input("Enter app database password [SecurePass123!]: ").strip() or "SecurePass123!"
    
    print(f"""
    Configuration:
    - Host: {db_host}
    - Port: {db_port}
    - Root User: {db_user}
    - Database: {db_name}
    - App User: {app_user}
    """)
    
    # Check MySQL connection
    print("\n3️⃣  Testing MySQL connection...")
    test_cmd = f'mysql -h {db_host} -P {db_port} -u {db_user} -p{db_password} -e "SELECT 1;"'
    result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"""
        ❌ Cannot connect to MySQL.
        Error: {result.stderr}
        
        Troubleshooting:
        1. Verify MySQL is running: mysql.server start (macOS) or net start MySQL80 (Windows)
        2. Check credentials: {db_user} / {db_password}
        3. Verify host/port: {db_host}:{db_port}
        """)
        return False
    
    print("✓ MySQL connection successful")
    
    # Create database and user
    print("\n4️⃣  Creating database and user...")
    
    # Read SQL schema
    sql_file = Path(__file__).parent / "init.sql"
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return False
    
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    # Execute schema
    sql_cmd = f'mysql -h {db_host} -P {db_port} -u {db_user} -p{db_password} < "{sql_file}"'
    print(f"Executing: {sql_file}")
    result = subprocess.run(sql_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Schema creation failed: {result.stderr}")
        return False
    
    print(f"✓ Database schema created: {db_name}")
    
    # Create application user
    print("\n5️⃣  Creating application user...")
    create_user_sql = f"""
    CREATE USER IF NOT EXISTS '{app_user}'@'{db_host}' IDENTIFIED BY '{app_password}';
    GRANT ALL PRIVILEGES ON {db_name}.* TO '{app_user}'@'{db_host}';
    FLUSH PRIVILEGES;
    """
    
    cmd = f'mysql -h {db_host} -P {db_port} -u {db_user} -p{db_password} -e "{create_user_sql}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"⚠️  User creation issue (may already exist): {result.stderr}")
    else:
        print(f"✓ Application user created: {app_user}")
    
    # Verify setup
    print("\n6️⃣  Verifying database setup...")
    verify_sql = """
    SELECT 
        TABLE_NAME 
    FROM 
        INFORMATION_SCHEMA.TABLES 
    WHERE 
        TABLE_SCHEMA = '{db_name}';
    """.format(db_name=db_name)
    
    cmd = f'mysql -h {db_host} -P {db_port} -u {app_user} -p{app_password} -e "{verify_sql}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        tables = result.stdout.strip().split('\n')[1:]  # Skip header
        print(f"✓ Created {len(tables)} tables:")
        for table in tables:
            if table.strip():
                print(f"  - {table}")
    else:
        print(f"❌ Verification failed: {result.stderr}")
        return False
    
    # Generate connection string
    print("\n7️⃣  Database Setup Complete! 🎉")
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║  MySQL Connection Details                                  ║
    ╠════════════════════════════════════════════════════════════╣
    ║  Host:     {db_host:<50}║
    ║  Port:     {db_port:<50}║
    ║  Database: {db_name:<50}║
    ║  User:     {app_user:<50}║
    ╚════════════════════════════════════════════════════════════╝
    
    🔗 Connection String:
    mysql+mysqlconnector://{app_user}:{app_password}@{db_host}:{db_port}/{db_name}
    
    ⚙️  Set these environment variables:
    
    Windows (CMD):
        set DB_HOST={db_host}
        set DB_PORT={db_port}
        set DB_NAME={db_name}
        set DB_USER={app_user}
        set DB_PASSWORD={app_password}
    
    Windows (PowerShell):
        $env:DB_HOST = "{db_host}"
        $env:DB_PORT = "{db_port}"
        $env:DB_NAME = "{db_name}"
        $env:DB_USER = "{app_user}"
        $env:DB_PASSWORD = "{app_password}"
    
    Linux/Mac (.bash_profile):
        export DB_HOST={db_host}
        export DB_PORT={db_port}
        export DB_NAME={db_name}
        export DB_USER={app_user}
        export DB_PASSWORD={app_password}
    
    ✅ Next steps:
    1. Set the environment variables above
    2. Start the Flask app: python src/web/app.py
    3. Open http://localhost:5000 in your browser
    4. Login with: admin / admin123 (default credentials)
    """)
    
    # Create .env file option
    create_env = input("\n📝 Create .env file with these settings? [y/N]: ").strip().lower()
    if create_env == 'y':
        env_content = f"""# MySQL Database Configuration
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={app_user}
DB_PASSWORD={app_password}

# Flask Configuration
DEBUG=false
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO
WEB_HOST=0.0.0.0
WEB_PORT=5000
"""
        env_file = Path(__file__).parent.parent / ".env"
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✓ Created .env file: {env_file}")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
