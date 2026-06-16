# Building ZambiaDigitalHygiene.exe

This guide explains how to build the Windows executable for the Zambia Digital Hygiene Certification Program.

## Prerequisites

- **Windows 10 or Windows 11**
- **Python 3.10 or 3.11** (available on PATH)
- **Git** (for cloning the repository)

## Quick Build (Windows)

### Step 1: Clone the Repository

```bash
git clone https://github.com/sakhile-bit/sakhile_final-_year_pro.git
cd sakhile_final-_year_pro
```

### Step 2: Run the Build Script

From the project root in **PowerShell** or **Command Prompt**:

```powershell
# PowerShell
.\devops\build.bat
```

or

```cmd
# Command Prompt
devops\build.bat
```

This script will:
- ✓ Check Python 3.10+ installation
- ✓ Create a virtual environment (if needed)
- ✓ Install dependencies from `requirements.txt`
- ✓ Install PyInstaller
- ✓ Clean previous builds
- ✓ Run PyInstaller with `devops/build.spec`
- ✓ Output `dist/ZambiaDigitalHygiene.exe`

### Step 3: Find Your Executable

After a successful build, your executable will be at:

```
dist/ZambiaDigitalHygiene.exe
```

## Manual Build Process

If you prefer to build manually or the script doesn't work:

### 1. Setup Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller>=6.0.0
```

### 2. Run PyInstaller

```bash
pyinstaller devops/build.spec
```

### 3. Verify Build

```bash
# Check if exe exists
dir dist\
```

The exe should be in `dist/ZambiaDigitalHygiene.exe`

## Build Configuration

The PyInstaller specification is in `devops/build.spec`:

- **Single-file executable**: All dependencies bundled into one `.exe`
- **No console window**: The app is a pure GUI (tkinter-based)
- **Optimizations**: UPX compression enabled, unused modules excluded
- **Icon**: Windows shield icon embedded
- **Hidden imports**: GUI and security modules explicitly included

## Troubleshooting

### Issue: "Python command not found"

**Solution**: Ensure Python 3.10+ is installed and on your PATH.

```bash
python --version
```

Should show Python 3.10 or later.

### Issue: "PyInstaller module not found"

**Solution**: Install PyInstaller:

```bash
pip install pyinstaller>=6.0.0
```

### Issue: Build takes too long

**Normal behavior**. The first build can take 2-5 minutes depending on your system. Subsequent builds are faster.

### Issue: Antivirus warns about the exe

**Expected**. New executables sometimes trigger antivirus warnings. You can:
- Submit the exe to your antivirus vendor
- Add an exception in your antivirus settings
- Sign the exe with a code-signing certificate (for production releases)

### Issue: "dist" directory already exists

**Solution**: The build script cleans it automatically. If you want to manually clean:

```bash
rmdir /s /q dist build
```

## Distribution

### GitHub Releases

1. Create a new release on GitHub
2. Tag it (e.g., `v1.0.0`)
3. Upload `dist/ZambiaDigitalHygiene.exe`
4. Set download URL: `https://github.com/sakhile-bit/sakhile_final-_year_pro/releases/download/v1.0.0/ZambiaDigitalHygiene.exe`

### Update .env for Downloads

Set the DOWNLOAD_URL environment variable:

```bash
export DOWNLOAD_URL="https://github.com/sakhile-bit/sakhile_final-_year_pro/releases/download/v1.0.0/ZambiaDigitalHygiene.exe"
```

The Flask web app will redirect `/download` to this URL.

## Code Signing (Optional)

For production releases, you can sign the exe:

```bash
# Using Signtool (Windows SDK)
signtool sign /f cert.pfx /p password /t http://timestamp.comodoca.com/authenticode dist\ZambiaDigitalHygiene.exe
```

## Development Builds

During development, you can run the app directly without building an exe:

```bash
python windows_app.py
```

This is faster for testing and debugging.

---

## Support

For issues with the build process, check:
- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [Project Issues](https://github.com/sakhile-bit/sakhile_final-_year_pro/issues)

