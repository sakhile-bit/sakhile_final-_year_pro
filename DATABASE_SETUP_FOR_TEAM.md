# MySQL Database Setup Guide for Team

This guide walks your team through setting up the MySQL database for the Zambia Digital Hygiene Assessment Tool on Ubuntu.

## Prerequisites

Before starting, ensure you have:

1. **MySQL Server installed and running**
   ```bash
   sudo systemctl status mysql
   ```
   
   If not installed, run:
   ```bash
   sudo apt-get update
   sudo apt-get install -y mysql-server mysql-client
   sudo systemctl start mysql
   ```

2. **Python project cloned**
   ```bash
   cd ~/Desktop
   git clone https://github.com/sakhile-bit/sakhile_final-_year_pro.git
   cd sakhile_final-_year_pro
   ```

3. **Python dependencies installed**
   ```bash
   python3 -m pip install --break-system-packages -r requirements.txt
   ```

## Step 1: Create the Project Database

Connect to MySQL as root and create the database and application user:

```bash
sudo mysql -u root << 'EOF'
CREATE DATABASE digital_hygiene CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL ON digital_hygiene.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
EOF
```

**What this does:**
- `CREATE DATABASE digital_hygiene` – Creates the database with UTF-8 support
- `CREATE USER 'app_user'@'localhost'` – Creates an unprivileged application user
- `GRANT ALL ON digital_hygiene.*` – Gives the user full access to only this database
- `FLUSH PRIVILEGES` – Reloads MySQL privilege tables

### Verify User Creation

```bash
sudo mysql -u root << 'EOF'
SELECT user, host FROM mysql.user WHERE user='app_user';
EOF
```

**Expected output:**
```
user    host
app_user        localhost
```

## Step 2: Test Database Connection

Verify the `app_user` can connect to the database:

```bash
mysql -u app_user -p'secure_password' -h localhost digital_hygiene -e "SELECT DATABASE();"
```

**Expected output:**
```
+-----------------+
| DATABASE()      |
+-----------------+
| digital_hygiene |
+-----------------+
```

If you see this, the connection is working! ✅

### Troubleshooting Connection Issues

| Error | Solution |
|-------|----------|
| `ERROR 2003: Can't connect to MySQL server` | MySQL not running: `sudo systemctl start mysql` |
| `ERROR 1045: Access denied` | Wrong password—double-check `'secure_password'` |
| `ERROR 1049: Unknown database` | Database not created—re-run Step 1 |

## Step 3: Configure Environment Variables

Create or update the `.env` file in your project root with the database credentials:

```bash
cat > /path/to/sakhile_final-_year_pro/.env << 'EOF'
# Database Configuration (MySQL)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=digital_hygiene
DB_USER=app_user
DB_PASSWORD=secure_password

# Flask & Security
DEBUG=false
SECRET_KEY=dev-secret-key-change-in-production

# Web Server
WEB_HOST=127.0.0.1
WEB_PORT=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Admin defaults (change on first deployment!)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@digitalhygiene.gov.zm
ADMIN_DEFAULT_PASSWORD=admin123
EOF
```

**Verify the file was created:**
```bash
cat /path/to/sakhile_final-_year_pro/.env
```

### Important Security Notes

⚠️ **Never commit `.env` to version control** – it contains database passwords!

Add to `.gitignore`:
```bash
echo ".env" >> /path/to/sakhile_final-_year_pro/.gitignore
```

## Step 4: Initialize Application Database

Now initialize the project's database schema and seed the default admin user:

```bash
cd /path/to/sakhile_final-_year_pro
python3 cli.py init-db
```

**Expected output:**
```
✅ Database initialized successfully
👤 Admin account already exists
```

**What this does:**
- Creates all required tables (users, businesses, assessments, certificates, etc.)
- Creates a default admin user (username: `admin`, password: `admin123`)
- Sets up database indexes and foreign keys

### If You Get an Error

**Error: "Can't connect to MySQL server on 'localhost:3306'"**

- Ensure MySQL is running: `sudo systemctl start mysql`
- Verify credentials in `.env` file match Step 1
- Check MySQL is listening: `sudo systemctl status mysql`

**Error: "Database 'digital_hygiene' doesn't exist"**

- Re-run Step 1 to create the database

**Error: "Access denied for user 'app_user'@'localhost'"**

- Verify the password in `.env` matches `'secure_password'` from Step 1
- Run Step 2 to test connection

## Step 5: Verify Database Setup

Check that all tables were created:

```bash
mysql -u app_user -p'secure_password' -h localhost digital_hygiene -e "SHOW TABLES;"
```

**Expected output (should show ~7 tables):**
```
+---------------------------+
| Tables_in_digital_hygiene |
+---------------------------+
| assessments               |
| assessment_requests       |
| audit_logs                |
| businesses                |
| certificates              |
| users                     |
| (other tables)            |
+---------------------------+
```

Verify the default admin user exists:

```bash
mysql -u app_user -p'secure_password' -h localhost digital_hygiene -e "SELECT id, username, role, is_active FROM users;"
```

**Expected output:**
```
+----+----------+-------+-----------+
| id | username | role  | is_active |
+----+----------+-------+-----------+
|  1 | admin    | admin |         1 |
+----+----------+-------+-----------+
```

## Step 6: Start the Application

Now that the database is ready, start the web server:

```bash
cd /path/to/sakhile_final-_year_pro
python3 cli.py web --debug
```

**Expected output:**
```
Web dashboard starting…
http://127.0.0.1:5000
 * Running on http://127.0.0.1:5000
```

Open **http://127.0.0.1:5000** in your browser and login:
- **Username**: `admin`
- **Password**: `admin123`

## Optional: MySQL Workbench GUI

For a graphical database management tool, install MySQL Workbench:

```bash
sudo snap install mysql-workbench-community
```

Launch it:
```bash
snap run mysql-workbench-community &
```

**To connect in Workbench:**
- Hostname: `localhost`
- Port: `3306`
- Username: `app_user`
- Password: `secure_password`

## Database Backups

### Backup the Database

```bash
mysqldump -u app_user -p'secure_password' digital_hygiene > digital_hygiene_backup.sql
```

### Restore from Backup

```bash
mysql -u app_user -p'secure_password' digital_hygiene < digital_hygiene_backup.sql
```

## Reset Database (Development Only)

**WARNING: This deletes all data!**

```bash
sudo mysql -u root << 'EOF'
DROP DATABASE digital_hygiene;
CREATE DATABASE digital_hygiene CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF
```

Then re-run Step 4 to reinitialize.

## Common Database Tasks

### View All Users and Their Permissions

```bash
sudo mysql -u root << 'EOF'
SELECT user, host, Select_priv, Insert_priv, Update_priv, Delete_priv FROM mysql.user WHERE user='app_user';
EOF
```

### Change Application User Password

```bash
sudo mysql -u root << 'EOF'
ALTER USER 'app_user'@'localhost' IDENTIFIED BY 'new_secure_password';
FLUSH PRIVILEGES;
EOF
```

Then update `.env` with the new password.

### View Database Size

```bash
mysql -u app_user -p'secure_password' -h localhost -e "SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb FROM information_schema.TABLES WHERE table_schema = 'digital_hygiene';"
```

### Reset Admin Password (via Application)

If you forget the admin password, reset it using the CLI:

```bash
python3 cli.py users reset-password --username admin
```

You'll be prompted for a new password.

## Production Deployment

For production, use these additional security measures:

### 1. Use Strong Passwords

```bash
# Generate a strong password
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update the user password:
```bash
sudo mysql -u root << 'EOF'
ALTER USER 'app_user'@'localhost' IDENTIFIED BY 'YOUR_STRONG_PASSWORD_HERE';
FLUSH PRIVILEGES;
EOF
```

### 2. Restrict User Host Access

Instead of `'app_user'@'localhost'`, if your app runs on a different server:

```bash
sudo mysql -u root << 'EOF'
GRANT ALL ON digital_hygiene.* TO 'app_user'@'192.168.1.100' IDENTIFIED BY 'secure_password';
FLUSH PRIVILEGES;
EOF
```

### 3. Disable Root Remote Access

```bash
sudo mysql -u root << 'EOF'
DELETE FROM mysql.user WHERE user='root' AND host != 'localhost';
FLUSH PRIVILEGES;
EOF
```

### 4. Enable SSL/TLS Connections

See MySQL documentation for SSL setup: https://dev.mysql.com/doc/

## Troubleshooting

### MySQL Service Won't Start

```bash
# Check status
sudo systemctl status mysql

# View logs
sudo journalctl -u mysql -n 50

# Try restarting
sudo systemctl restart mysql
```

### High Memory Usage

MySQL's default configuration uses ~400MB+. To reduce memory on development machines:

Edit `/etc/mysql/mysql.conf.d/mysqld.cnf` and add:

```ini
[mysqld]
innodb_buffer_pool_size = 256M
max_connections = 50
```

Restart:
```bash
sudo systemctl restart mysql
```

### Port Already in Use

If port 3306 is in use by another process:

```bash
# Find what's using port 3306
sudo lsof -i :3306

# Kill the process (if needed)
sudo kill -9 <PID>

# Start MySQL
sudo systemctl start mysql
```

## Getting Help

1. **Check MySQL logs**:
   ```bash
   sudo tail -50 /var/log/mysql/error.log
   ```

2. **Run project status check**:
   ```bash
   python3 cli.py status
   ```

3. **Test database connection**:
   ```bash
   mysql -u app_user -p'secure_password' -h localhost digital_hygiene -e "SELECT NOW();"
   ```

4. **Check application logs**:
   ```bash
   tail -50 logs/app.log
   ```

## Related Documentation

- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) – Full environment setup guide
- [README.md](README.md) – Project overview and quick start
- [SETUP.md](SETUP.md) – Additional manual setup instructions

---

**Last Updated**: March 6, 2026  
**MySQL Version Tested**: 8.4.8  
**OS Tested**: Ubuntu 22.04 LTS, Ubuntu 24.04 LTS
