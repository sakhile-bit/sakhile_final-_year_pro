@echo off
REM Zambia Digital Hygiene Assessment Tool (zamsec) - CMD installer
REM Usage (Command Prompt):
REM   curl -fsSL -o install.bat https://raw.githubusercontent.com/sakhile-bit/sakhile_final-_year_pro/main/devops/install.bat && install.bat
REM
REM Installs the "zamsec" command globally via pip.

setlocal
set "ARCHIVE=https://github.com/sakhile-bit/sakhile_final-_year_pro/archive/refs/heads/main.zip"

echo ==============================================
echo  Zambia Digital Hygiene Assessment Tool
echo  zamsec - terminal installer
echo ==============================================

REM --- 1. Check Python -------------------------------------------------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Install Python 3.9+ from https://python.org and tick "Add to PATH".
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version') do echo Python found: %%v
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"
if %errorlevel% neq 0 (
    echo ERROR: Python 3.9+ is required.
    pause
    exit /b 1
)

REM --- 2. Install ------------------------------------------------------
echo Installing zamsec with pip...
python -m pip install --upgrade "%ARCHIVE%"
if %errorlevel% neq 0 (
    echo Retrying with --user, no admin rights needed...
    python -m pip install --user --upgrade "%ARCHIVE%"
)
if %errorlevel% neq 0 (
    echo ERROR: installation failed - see pip output above.
    pause
    exit /b 1
)

REM --- 3. Verify -------------------------------------------------------
echo.
echo ==============================================
where zamsec >nul 2>&1
if %errorlevel% equ 0 (
    echo Installed successfully!
    zamsec --version
) else (
    echo Installed, but 'zamsec' is not on your PATH yet.
    echo Add your Python Scripts folder to PATH, then open a new terminal:
    python -c "import sysconfig; print('  ' + sysconfig.get_path('scripts'))"
)
echo ==============================================
echo.
echo Get started:
echo   zamsec --help        all commands
echo   zamsec scan          quick system security scan
echo   zamsec assess        full 15-control assessment
echo   zamsec harden        infrastructure hardening audit
echo   zamsec web           web dashboard (http://127.0.0.1:5000)
echo   zamsec completion    enable TAB completion
echo   zamsec upgrade       update to the latest version
pause
