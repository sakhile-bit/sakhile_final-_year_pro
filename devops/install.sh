#!/bin/bash
# Zambia Digital Hygiene Assessment Tool - Quick Install & Run
# Usage: curl -s https://your-domain.com/install.sh | bash

set -e

echo "========================================"
echo "Zambia Digital Hygiene Assessment Tool"
echo "Quick Install & Run Script"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ ERROR: Python is not installed"
    echo "Please install Python 3.8+ first"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "✓ Python found: $($PYTHON_CMD --version)"

# Create temp directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Try to clone repository first, fallback to download ZIP
echo "Downloading repository..."
if command -v git &> /dev/null; then
    git clone https://github.com/yourusername/digital-hygiene-tool.git .
else
    echo "Git not found, downloading ZIP..."
    curl -L -o repo.zip https://github.com/yourusername/digital-hygiene-tool/archive/main.zip
    unzip repo.zip
    cd digital-hygiene-tool-main
fi

# Install dependencies
echo "Installing dependencies..."
$PYTHON_CMD -m pip install --user --upgrade pip
$PYTHON_CMD -m pip install --user -r requirements.txt

# Setup database
echo "Setting up database..."
if $PYTHON_CMD database/setup_mysql.py; then
    echo "✓ Database setup completed"
else
    echo "⚠️  Database setup failed or was cancelled"
    echo "You can run it manually later: $PYTHON_CMD database/setup_mysql.py"
fi

# Run the tool
echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
echo ""
echo "To run the web interface:"
echo "  $PYTHON_CMD src/web/app.py"
echo ""
echo "To use the CLI:"
echo "  $PYTHON_CMD src/utils/cli.py --help"
echo ""
echo "Visit: http://localhost:5000"
echo ""

# Ask if user wants to start the web interface
read -p "Start web interface now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting web interface..."
    echo "Press Ctrl+C to stop"
    $PYTHON_CMD src/web/app.py
fi

echo ""
echo "Installation directory: $(pwd)"
echo "You can safely delete this directory after copying the files elsewhere."