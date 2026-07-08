# Deployment Guide

This guide covers deploying the Zambia Digital Hygiene Certification Program in production environments.

## Architecture Overview

The project consists of two main components:

1. **Windows Desktop App** (`ZambiaDigitalHygiene.exe`)
   - Standalone executable for SMEs
   - No internet required for core functionality
   - Reports saved locally or exported

2. **Web Portal** (Flask app)
   - Landing page / marketing site
   - Certificate verification lookup
   - Phase 2: Full dashboard and database

## Option 1: Docker Deployment (Recommended)

### Prerequisites

- Docker and Docker Compose installed
- Port 5000 available (or configure a reverse proxy)

### Setup

1. **Clone the repository:**

```bash
git clone https://github.com/sakhile-bit/sakhile_final-_year_pro.git
cd sakhile_final-_year_pro
```

2. **Create `.env` file:**

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
DEBUG=false
SECRET_KEY=<generate-with: python -c "import secrets; print(secrets.token_urlsafe(64))">
DB_HOST=db
DB_USER=root
DB_PASSWORD=<strong-password>
DB_NAME=digital_hygiene
DOWNLOAD_URL=https://your-domain.com/downloads/ZambiaDigitalHygiene.exe
```

3. **Build and run Docker containers:**

```bash
docker-compose up --build
```

4. **Verify deployment:**

```bash
curl http://localhost:5000/
```

### Production Docker Commands

```bash
# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

## Option 2: Manual Server Deployment (Linux/Ubuntu)

### Prerequisites

- Ubuntu 20.04 LTS or later
- Python 3.10+
- MySQL 8.0+
- Nginx (optional, for reverse proxy)

### Step 1: System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.10 python3.10-venv python3-pip \
    mysql-server mysql-client default-libmysqlclient-dev \
    nginx supervisor

# Create application user
sudo useradd --home-dir /var/www/digital-hygiene --shell /bin/bash app
sudo mkdir -p /var/www/digital-hygiene
```

### Step 2: Clone Repository

```bash
cd /var/www/digital-hygiene
sudo git clone https://github.com/sakhile-bit/sakhile_final-_year_pro.git .
sudo chown -R app:app /var/www/digital-hygiene
```

### Step 3: Setup Python Environment

```bash
sudo -u app python3.10 -m venv venv
sudo -u app venv/bin/pip install -r requirements.txt
```

### Step 4: Configure MySQL

```bash
sudo mysql -u root -p << EOF
CREATE DATABASE digital_hygiene;
CREATE USER 'hygiene_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON digital_hygiene.* TO 'hygiene_user'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### Step 5: Create `.env` Configuration

```bash
sudo nano /var/www/digital-hygiene/.env
```

Add:

```env
DEBUG=false
FLASK_ENV=production
SECRET_KEY=<generate-strong-key>
DB_HOST=localhost
DB_USER=hygiene_user
DB_PASSWORD=secure_password
DB_NAME=digital_hygiene
WEB_PORT=5000
```

### Step 6: Setup Gunicorn with Supervisor

Create `/etc/supervisor/conf.d/digital-hygiene.conf`:

```ini
[program:digital-hygiene]
directory=/var/www/digital-hygiene
command=/var/www/digital-hygiene/venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile /var/log/digital-hygiene/access.log \
    --error-logfile /var/log/digital-hygiene/error.log \
    src.web.app:create_app()
user=app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/digital-hygiene/app.log
```

Then:

```bash
sudo mkdir -p /var/log/digital-hygiene
sudo chown app:app /var/log/digital-hygiene
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start digital-hygiene
```

### Step 7: Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/digital-hygiene`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/digital-hygiene/src/web/static/;
        expires 1y;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/digital-hygiene /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 8: Setup SSL with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Environment Variables

Key configuration variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable Flask debug mode (never in production!) |
| `SECRET_KEY` | N/A | Flask session secret (generate with `secrets.token_urlsafe(64)`) |
| `DB_HOST` | `localhost` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_NAME` | `digital_hygiene` | Database name |
| `DB_USER` | `root` | MySQL user |
| `DB_PASSWORD` | N/A | MySQL password |
| `DOWNLOAD_URL` | N/A | URL to download Windows exe |
| `FLASK_ENV` | `production` | Flask environment |
| `WEB_PORT` | `5000` | Web server port |

## Monitoring & Maintenance

### Health Checks

```bash
# Check app status
curl http://your-domain.com/

# Check logs
docker-compose logs -f  # Docker
sudo tail -f /var/log/digital-hygiene/app.log  # Manual
```

### Backup Strategy

```bash
# Backup database
mysqldump -u hygiene_user -p digital_hygiene > backup_$(date +%Y%m%d).sql

# Restore from backup
mysql -u hygiene_user -p digital_hygiene < backup_20260510.sql
```

### Auto-Updates

For automatic security updates on Ubuntu:

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Security Best Practices

1. **Use HTTPS**: Configure SSL/TLS certificates
2. **Strong Passwords**: Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
3. **Firewall**: Only expose necessary ports (80, 443)
4. **Database**: Don't expose MySQL to the internet
5. **Environment Secrets**: Keep `.env` out of version control
6. **Updates**: Keep OS and dependencies updated
7. **Logging**: Monitor access and error logs

## Troubleshooting

### App won't start

```bash
# Check logs
docker-compose logs
# or
journalctl -u supervisor

# Check if port is in use
netstat -tupln | grep 5000
```

### Database connection error

```bash
# Test MySQL connection
mysql -h db -u hygiene_user -p

# Check MySQL is running
docker-compose ps
```

### File permissions issues

```bash
# Fix file ownership
sudo chown -R app:app /var/www/digital-hygiene
```

## Support

- [GitHub Issues](https://github.com/sakhile-bit/sakhile_final-_year_pro/issues)
- [Project Documentation](README.md)

