@echo off
REM ────────────────────────────────────────────────────────────
REM  Build ZambiaDigitalHygiene.exe
REM  Run from the project root:  devops\build.bat
REM ────────────────────────────────────────────────────────────

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  Zambia Digital Hygiene — Windows Build Script   ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM ── 1. Check Python ─────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ and re-run.
    pause & exit /b 1
)

REM ── 2. Install/upgrade dependencies ─────────────────────────
echo [1/3] Installing dependencies...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet pyinstaller
echo        Done.
echo.

REM ── 3. Clean previous build ──────────────────────────────────
echo [2/3] Cleaning previous build...
if exist dist\ZambiaDigitalHygiene.exe del /f /q dist\ZambiaDigitalHygiene.exe
if exist build rmdir /s /q build
echo        Done.
echo.

REM ── 4. Run PyInstaller ───────────────────────────────────────
echo [3/3] Building executable...
pyinstaller devops\build.spec --distpath dist --workpath build --noconfirm
if %errorlevel% neq 0 (
    echo [ERROR] Build failed. Check output above.
    pause & exit /b 1
)

echo.
echo  ✔  Build complete!
echo     Executable: dist\ZambiaDigitalHygiene.exe
echo.
pause
