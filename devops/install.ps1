# Zambia Digital Hygiene Assessment Tool (zamsec) - PowerShell installer
# Usage:
#   irm https://raw.githubusercontent.com/sakhile-bit/sakhile_final-_year_pro/main/devops/install.ps1 | iex
#
# Installs the "zamsec" command globally via pip (or pipx when available).

$ErrorActionPreference = "Stop"
$Repo = "https://github.com/sakhile-bit/sakhile_final-_year_pro"
$Archive = "$Repo/archive/refs/heads/main.zip"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " Zambia Digital Hygiene Assessment Tool" -ForegroundColor Cyan
Write-Host " zamsec - terminal installer" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# --- 1. Check Python -------------------------------------------------------
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Install Python 3.9+ from https://python.org (tick 'Add to PATH')." -ForegroundColor Yellow
    exit 1
}
$pyVersion = & python -c "import sys; print('%d.%d' % sys.version_info[:2])"
Write-Host "Python found: $pyVersion" -ForegroundColor Green
$verOk = & python -c "import sys; print(1 if sys.version_info >= (3, 9) else 0)"
if ($verOk -ne "1") {
    Write-Host "ERROR: Python 3.9+ is required (found $pyVersion)." -ForegroundColor Red
    exit 1
}

# --- 2. Install ------------------------------------------------------------
$pipx = Get-Command pipx -ErrorAction SilentlyContinue
if ($pipx) {
    Write-Host "Installing with pipx (isolated environment)..." -ForegroundColor Yellow
    & pipx install --force $Archive
} else {
    Write-Host "Installing with pip..." -ForegroundColor Yellow
    & python -m pip install --upgrade $Archive
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Retrying with --user (no admin rights needed)..." -ForegroundColor Yellow
        & python -m pip install --user --upgrade $Archive
    }
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: installation failed - see pip output above." -ForegroundColor Red
    exit 1
}

# --- 3. Verify -------------------------------------------------------------
$zamsec = Get-Command zamsec -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
if ($zamsec) {
    Write-Host "Installed successfully!" -ForegroundColor Green
    & zamsec --version
} else {
    $scriptsDir = & python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
    $userScripts = & python -m site --user-site 2>$null
    Write-Host "Installed, but 'zamsec' is not on your PATH yet." -ForegroundColor Yellow
    Write-Host "Add this folder to PATH, then open a new terminal:" -ForegroundColor Yellow
    Write-Host "  $scriptsDir" -ForegroundColor White
    if ($userScripts) {
        Write-Host "(or the user Scripts folder next to: $userScripts)" -ForegroundColor Gray
    }
}
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Get started:" -ForegroundColor Cyan
Write-Host "  zamsec --help        all commands"
Write-Host "  zamsec scan          quick system security scan"
Write-Host "  zamsec assess        full 15-control assessment"
Write-Host "  zamsec harden        infrastructure hardening audit"
Write-Host "  zamsec web           web dashboard (http://127.0.0.1:5000)"
Write-Host "  zamsec completion    enable TAB completion"
Write-Host "  zamsec upgrade       update to the latest version"
