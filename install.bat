@echo off
REM Zambia Digital Hygiene Assessment Tool - Quick Install & Run
REM Usage: curl -s https://your-domain.com/install.bat | cmd

echo ========================================
echo Zambia Digital Hygiene Assessment Tool
echo Quick Install & Run Script
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Git not found. Will try to download as ZIP...
    goto :download_zip
)

REM Clone the repository
echo Cloning repository...
git clone https://github.com/yourusername/digital-hygiene-tool.git temp_digital_hygiene
cd temp_digital_hygiene
goto :setup

:download_zip
echo Downloading as ZIP...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/yourusername/digital-hygiene-tool/archive/main.zip' -OutFile 'temp_digital_hygiene.zip'"
powershell -Command "Expand-Archive -Path 'temp_digital_hygiene.zip' -DestinationPath '.'"
cd digital-hygiene-tool-main

:setup
REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Setup database
echo Setting up database...
python database/setup_mysql.py

REM Run the tool
echo Starting the tool...
python src/utils/cli.py --help

echo.
echo ========================================
echo Installation complete!
echo.
echo To run the web interface:
echo   python src/web/app.py
echo.
echo To use the CLI:
echo   python src/utils/cli.py [command]
echo.
echo Visit: http://localhost:5000
echo ========================================

pause