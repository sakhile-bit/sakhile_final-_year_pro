# Database Setup

> **The app is self-contained on SQLite by default — no database server is required.**
> MySQL is only needed for a shared, multi-user production deployment.
>
> **SQLite (default, self-contained):**
> - Desktop app: stores everything in `%APPDATA%\ZambiaDigitalHygiene\history.db`,
>   created automatically at runtime (reference schema:
>   [`database/schema_sqlite_local.sql`](database/schema_sqlite_local.sql)).
> - Web portal: falls back to `instance/digital_hygiene.db`. Create it with
>   `python cli.py init-db` (or `python database/setup_sqlite.py`); reference schema:
>   [`database/schema_sqlite.sql`](database/schema_sqlite.sql).
>
> The MySQL instructions below are **optional** — use them only for a
> server-backed multi-user deployment.

---

# MySQL Production Database Setup (optional)

This guide covers setting up MySQL for the Digital Hygiene Assessment Tool in production.

## Prerequisites

- MySQL 8.0+ (or MariaDB 10.5+)
- Administrator access to MySQL
- Python 3.8+ with the app installed

## Quick Setup (3 Methods)

### Method 1: Python Setup Script (Recommended)

Works on Windows, macOS, and Linux.

```bash
# Windows (CMD)
cd c:\Users\sakil\Desktop\sakhile_final-_year_pro
python database\setup_mysql.py

# macOS/Linux
cd ~/sakhile_final-_year_pro
python database/setup_mysql.py
```

This script will:

- Check MySQL installation
- Create the database
- Create tables and indexes
- Create app user with proper permissions
- Generate connection string
- Optionally create `.env` file

### Method 2: Manual Setup (MySQL CLI)

```bash
# 1. Connect to MySQL as root
mysql -u root -p

# 2. Create database
CREATE DATABASE digital_hygiene CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 3. Create app user
CREATE USER 'dhassess'@'localhost' IDENTIFIED BY 'SecurePassword123!';
GRANT ALL PRIVILEGES ON digital_hygiene.* TO 'dhassess'@'localhost';
FLUSH PRIVILEGES;

# 4. Exit MySQL
exit

# 5. Run schema setup
mysql -u dhassess -p digital_hygiene < database/init.sql
```

### Method 3: Docker (Quickest)

```bash
# 1. Run MySQL container
docker run -d \
  --name mysql-dhassess \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=admin123 \
  -e MYSQL_DATABASE=digital_hygiene \
  mysql:8.0.35

# 2. Wait for startup (5-10 seconds)
sleep 10

# 3. Run schema initialization
mysql -h 127.0.0.1 -u root -padmin123 digital_hygiene < database/init.sql

# 4. Create app user
mysql -h 127.0.0.1 -u root -padmin123 -e \
  "CREATE USER 'dhassess'@'%' IDENTIFIED BY 'SecurePass123!'; \
   GRANT ALL PRIVILEGES ON digital_hygiene.* TO 'dhassess'@'%'; \
   FLUSH PRIVILEGES;"
```

## Configuration

### Environment Variables

Set these variables before starting the app:

**Windows (CMD)**

```cmd
set DB_HOST=localhost
set DB_PORT=3306
set DB_NAME=digital_hygiene
set DB_USER=dhassess
set DB_PASSWORD=SecurePass123!
set DEBUG=false
set SECRET_KEY=your-random-secret-key
```

**Windows (PowerShell)**

```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_NAME = "digital_hygiene"
$env:DB_USER = "dhassess"
$env:DB_PASSWORD = "SecurePass123!"
$env:DEBUG = "false"
$env:SECRET_KEY = "your-random-secret-key"
```

**Linux/macOS**

```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=digital_hygiene
export DB_USER=dhassess
export DB_PASSWORD=SecurePass123!
export DEBUG=false
export SECRET_KEY=your-random-secret-key
```

### .env File (Alternative)

Create `.env` file in project root:

```ini
# MySQL Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=digital_hygiene
DB_USER=dhassess
DB_PASSWORD=SecurePass123!

# Flask
DEBUG=false
SECRET_KEY=your-random-secret-key-min-32-chars
LOG_LEVEL=INFO
WEB_HOST=0.0.0.0
WEB_PORT=5000
```

## Database Schema

The schema includes:

### Tables

| Table          | Purpose                        |
| -------------- | ------------------------------ |
| `users`        | User authentication and roles  |
| `businesses`   | Organization data              |
| `assessments`  | Assessment records and results |
| `certificates` | Certification data             |
| `audit_logs`   | Activity tracking              |

### Default Data

- **Admin User**: `admin` / `admin123` (⚠️ Change in production!)
- **Sample Businesses**: 3 test organizations
- **Sample Assessments**: 3 test assessments

## Verification

### Test Connection

```bash
# Test with app user
mysql -h localhost -u dhassess -p -D digital_hygiene -e "SHOW TABLES;"

# Should output:
# Tables_in_digital_hygiene
# assessments
# audit_logs
# businesses
# certificates
# users
```

### Test From Python

```python
from src.utils.config import config
from src.web.app import create_app

app = create_app()
with app.app_context():
    # This will use MySQL if configured
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Check connection
    from src.web.app import db
    db.create_all()  # Create any missing tables
    print("✓ Connection successful")
```

## Starting the App

```bash
# 1. Activate virtual environment
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux

# 2. Start Flask app
python src/web/app.py

# 3. Open http://localhost:5000
# Login: admin / admin123
```

## Production Checklist

- [ ] MySQL 8.0+ installed and running
- [ ] Database `digital_hygiene` created
- [ ] App user `dhassess` created with privileges
- [ ] All environment variables set (DB_HOST, DB_USER, DB_PASSWORD, SECRET_KEY)
- [ ] DEBUG=false in production
- [ ] SECRET_KEY is strong (>32 characters)
- [ ] Database backups configured
- [ ] Connection tested with Python script
- [ ] Admin password changed from default
- [ ] Firewall allows MySQL port (3306) if remote
- [ ] SSL certificates configured for HTTPS

## Security Notes

### Change Default Credentials

```sql
-- Change admin password
UPDATE users SET password_hash='<new_hash>' WHERE username='admin';

-- Or use Flask shell
python -c "
from src.web.app import db, User
user = User.query.filter_by(username='admin').first()
user.set_password('NewPassword123!')
db.session.commit()
print('Password updated')
"
```

### MySQL User Security

```sql
-- Restrict app user to localhost only (recommended)
CREATE USER 'dhassess'@'localhost' IDENTIFIED BY 'StrongPassword123!';

-- Or allow from specific host
CREATE USER 'dhassess'@'192.168.1.100' IDENTIFIED BY 'StrongPassword123!';

-- Revoke dangerous privileges
REVOKE SUPER, GRANT OPTION ON *.* FROM 'dhassess'@'localhost';
```

### Backup Strategy

```bash
# Daily backup
mysqldump -u dhassess -p digital_hygiene > backup_$(date +%Y%m%d).sql

# Weekly full backup with compression
mysqldump -u dhassess -p --all-databases | gzip > backup_$(date +%Y%W).sql.gz

# Restore from backup
mysql -u dhassess -p digital_hygiene < backup_20260118.sql
```

## Troubleshooting

### Connection Refused

```
Error: Can't connect to MySQL server on 'localhost'
```

**Solutions:**

1. Verify MySQL is running: `mysql -u root -p` should work
2. Check port: Default is 3306
3. Verify credentials: DB_USER and DB_PASSWORD
4. Check firewall: Allow port 3306 if remote

### Access Denied

```
Error: Access denied for user 'dhassess'@'localhost'
```

**Solutions:**

1. Verify password: `mysql -u dhassess -p` with correct password
2. Check permissions: `SHOW GRANTS FOR 'dhassess'@'localhost';`
3. Grant privileges: `GRANT ALL PRIVILEGES ON digital_hygiene.* TO 'dhassess'@'localhost';`

### Database Not Found

```
Error: Unknown database 'digital_hygiene'
```

**Solutions:**

1. Create database: `CREATE DATABASE digital_hygiene;`
2. Run schema: `mysql -u root -p digital_hygiene < database/init.sql`
3. Verify: `SHOW DATABASES;` should list it

### Slow Queries

```sql
-- Check table sizes
SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.TABLES
WHERE table_schema = 'digital_hygiene'
ORDER BY size_mb DESC;

-- Rebuild indexes
OPTIMIZE TABLE assessments;
ANALYZE TABLE assessments;
```

## Remote MySQL (Advanced)

To connect from a different server:

```sql
-- Allow remote connection
CREATE USER 'dhassess'@'192.168.1.%' IDENTIFIED BY 'StrongPassword123!';
GRANT ALL PRIVILEGES ON digital_hygiene.* TO 'dhassess'@'192.168.1.%';

-- Edit my.cnf to bind to 0.0.0.0 (not localhost only)
[mysqld]
bind-address = 0.0.0.0
port = 3306
```

Connection string:

```
mysql+mysqlconnector://dhassess:StrongPassword123!@192.168.1.100:3306/digital_hygiene
```

## Support

For issues:

1. Check MySQL logs: `tail -f /var/log/mysql/error.log`
2. Verify table creation: `SHOW CREATE TABLE users\G`
3. Check data: `SELECT COUNT(*) FROM assessments;`
4. Run tests: `pytest -v` (will use SQLite by default)
