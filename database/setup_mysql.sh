#!/bin/bash
# Quick MySQL setup script for Linux/macOS
# Run this to set up MySQL for production

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  MySQL Database Setup - Digital Hygiene Tool               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if MySQL is installed
if ! command -v mysql &> /dev/null; then
    echo "❌ MySQL is not installed."
    echo ""
    echo "Install with:"
    echo "  macOS:  brew install mysql"
    echo "  Ubuntu: sudo apt-get install mysql-server"
    exit 1
fi

echo "✓ MySQL found: $(mysql --version)"
echo ""

# Get credentials
read -p "MySQL host [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "MySQL port [3306]: " DB_PORT
DB_PORT=${DB_PORT:-3306}

read -p "MySQL root user [root]: " DB_ROOT_USER
DB_ROOT_USER=${DB_ROOT_USER:-root}

read -sp "MySQL root password: " DB_ROOT_PASSWORD
echo ""

read -p "Database name [digital_hygiene]: " DB_NAME
DB_NAME=${DB_NAME:-digital_hygiene}

read -p "App user [dhassess]: " DB_APP_USER
DB_APP_USER=${DB_APP_USER:-dhassess}

read -sp "App user password: " DB_APP_PASSWORD
echo ""

# Read SQL file
SQL_FILE="$(dirname "$0")/init.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ SQL file not found: $SQL_FILE"
    exit 1
fi

echo ""
echo "Running setup..."

# Create database and tables
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ROOT_USER" -p"$DB_ROOT_PASSWORD" < "$SQL_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Schema setup failed"
    exit 1
fi

echo "✓ Schema created"

# Create application user
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ROOT_USER" -p"$DB_ROOT_PASSWORD" <<EOF
CREATE USER IF NOT EXISTS '$DB_APP_USER'@'$DB_HOST' IDENTIFIED BY '$DB_APP_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_APP_USER'@'$DB_HOST';
FLUSH PRIVILEGES;
EOF

echo "✓ User created"

# Create .env file
ENV_FILE="$(dirname "$0")/../.env"
cat > "$ENV_FILE" << EOF
# MySQL Database Configuration
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_APP_USER
DB_PASSWORD=$DB_APP_PASSWORD

# Flask Configuration
DEBUG=false
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO
WEB_HOST=0.0.0.0
WEB_PORT=5000
EOF

echo "✓ Created $ENV_FILE"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Setup Complete! 🎉                                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Connection String:"
echo "mysql+mysqlconnector://$DB_APP_USER:$DB_APP_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "Next steps:"
echo "1. Load environment: source .env"
echo "2. Start app: python src/web/app.py"
echo "3. Open http://localhost:5000"
