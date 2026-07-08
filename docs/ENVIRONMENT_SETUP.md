# Environment Setup Guide

## Overview

This document provides step-by-step instructions for setting up the Zambia Digital Hygiene Assessment Tool development environment on Ubuntu Linux systems.

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04 LTS or later
- **Python**: 3.10 or higher (tested with Python 3.13)
- **RAM**: 2GB minimum (4GB+ recommended)
- **Disk Space**: 500MB free space

### Required System Packages

Before installing Python dependencies, ensure your system has the necessary packages:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-dev python3.13-venv git build-essential
```

**Note on PEP 668**: Ubuntu 23.10+ enforces PEP 668, which prevents direct pip installations to the system Python. You have two options:
1. **Use `--break-system-packages`** (recommended for development): Install to system Python with a development flag
2. **Create a virtual environment** (recommended for production): Use venv to isolate dependencies

## Installation Steps

### Step 1: Clone the Repository

```bash
cd ~/Desktop
git clone https://github.com/sakhile-bit/sakhile_final-_year_pro.git
cd sakhile_final-_year_pro
```

### Step 2: Install Python Dependencies

#### Option A: Development Setup (Recommended for Ubuntu 23.10+)

If you encounter the "externally-managed-environment" error, use this approach:

```bash
cd /path/to/sakhile_final-_year_pro
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install --break-system-packages -r requirements.txt
```

The `--break-system-packages` flag is safe for development environments and allows you to skip virtual environment setup.

#### Option B: Virtual Environment Setup (Alternative)

If your system has `python3.13-venv` available:

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt
```

**Note**: If you get an error "The virtual environment was not created successfully because ensurepip is not available", install the venv package:

```bash
sudo apt-get install -y python3.13-venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 3: Environment Configuration (Optional)

Create a `.env` file in the project root for custom configuration:

```bash
cp .env.example .env
```

**Key environment variables** (edit `.env` as needed):

```env
# Application
DEBUG=false
LOG_LEVEL=INFO

# Database (defaults to SQLite for local dev)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=digital_hygiene
DB_USER=root
DB_PASSWORD=

# Web Server
WEB_HOST=127.0.0.1
WEB_PORT=5000
SECRET_KEY=your-secret-key-here
```

**For SQLite (default in dev)**: No database credentials needed—the app creates `instance/digital_hygiene.db` automatically.

**For MySQL**: Configure the above credentials and ensure MySQL is running.

### Step 4: Verify Installation

Check that all dependencies are installed:

```bash
python3 -c "import flask; import click; import rich; print('✅ All dependencies loaded successfully')"
```

## Running the Application

### Start the Web Server

```bash
cd /path/to/sakhile_final-_year_pro
python3 cli.py web --debug
```

The dashboard will be available at: **http://127.0.0.1:5000**

**Default Admin Credentials**:
- Username: `admin`
- Password: `admin123`

### Initialize the Database (Optional)

To manually create the database schema and seed default admin:

```bash
python3 cli.py init-db
```

This is normally done automatically when the web server starts.

### Run CLI Commands

The tool provides several CLI commands:

```bash
# Run full 15-control assessment
python3 cli.py assess --business-name "Acme Ltd" --business-id REG-001

# Quick system security scan
python3 cli.py scan

# Zambia-specific risk assessment
python3 cli.py zambia

# Pre-deployment hygiene check
python3 cli.py predeploy

# User management
python3 cli.py users list
python3 cli.py users create

# View project status
python3 cli.py status

# See all commands
python3 cli.py --help
```

## Running Tests

### Execute All Tests

```bash
python3 -m pytest tests/ -v
```

### Run Tests with Coverage

```bash
python3 -m pytest tests/ --cov=src --cov-report=html
```

### Run Specific Test File

```bash
python3 -m pytest src/tests/test_assessor.py -v
```

### Run Smoke Tests

```bash
python3 smoke_test.py
```

## Troubleshooting

### Issue: "externally-managed-environment" Error

**Solution**: Use `--break-system-packages` flag or create a virtual environment (see Step 2 above).

### Issue: MySQL Connection Refused

**Solution**: The app auto-detects MySQL availability and falls back to SQLite. No action needed—it will use `instance/digital_hygiene.db` instead.

### Issue: "ModuleNotFoundError" for Project Modules

**Cause**: Working directory is not the project root.

**Solution**:
```bash
cd /path/to/sakhile_final-_year_pro  # Must run from project root
python3 cli.py web --debug
```

### Issue: Port 5000 Already in Use

**Solution**: Run on a different port:
```bash
python3 cli.py web --debug --port 5001
```

### Issue: Dependencies Not Found After Installation

**Solution**: Ensure pip packages are correctly installed:
```bash
python3 -m pip list | grep -E "Flask|SQLAlchemy|Click"
```

If missing, reinstall:
```bash
python3 -m pip install --break-system-packages -r requirements.txt --force-reinstall
```

## Database Setup

### SQLite (Default for Development)

- **Location**: `instance/digital_hygiene.db`
- **Auto-created**: Yes, on first web server start
- **No setup needed**: Database initializes automatically

### MySQL (Optional for Production)

1. Install and start MySQL:
   ```bash
   sudo apt-get install -y mysql-server
   sudo service mysql start
   ```

2. Create database:
   ```bash
   mysql -u root -p << EOF
   CREATE DATABASE digital_hygiene CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'secure_password';
   GRANT ALL ON digital_hygiene.* TO 'app_user'@'localhost';
   FLUSH PRIVILEGES;
   EOF
   ```

3. Update `.env`:
   ```env
   DB_HOST=localhost
   DB_USER=app_user
   DB_PASSWORD=secure_password
   DB_NAME=digital_hygiene
   ```

4. Initialize:
   ```bash
   python3 cli.py init-db
   ```

## Deployment Considerations

### Security Best Practices

- **Never commit `.env` file** to version control
- **Change default admin password** immediately: `python3 cli.py users reset-password`
- **Use HTTPS in production**: Set `SESSION_COOKIE_SECURE=true` in config
- **Enable MFA** for admin accounts via web dashboard

### Production Deployment

For production deployment, use Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "src.web.app:create_app()"
```

Or with systemd service (see deployment documentation).

## Additional Resources

- [README.md](README.md) – Project overview and quick start
- [DATABASE_SETUP.md](DATABASE_SETUP.md) – Detailed database configuration
- [SETUP.md](SETUP.md) – Manual setup instructions
- [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) – Testing procedures

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review the application logs: `cd logs && tail -f app.log`
3. Run `python3 cli.py status` to check environment health
4. Check [GitHub Issues](https://github.com/sakhile-bit/sakhile_final-_year_pro/issues) for similar problems

---

**Last Updated**: March 6, 2026  
**Python Version Tested**: 3.13.7  
**OS Tested**: Ubuntu 22.04 LTS, Ubuntu 24.04 LTS
