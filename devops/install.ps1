# Zambia Digital Hygiene Assessment Tool - PowerShell Quick Install
# Usage: irm https://your-domain.com/install.ps1 | iex

param(
    [switch]$NoWeb,
    [switch]$NoDB,
    [string]$Branch = "main"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Zambia Digital Hygiene Assessment Tool" -ForegroundColor Cyan
Write-Host "PowerShell Quick Install & Run Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check Python installation
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create temp directory
$tempDir = Join-Path $env:TEMP "digital_hygiene_install"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null
Set-Location $tempDir

# Download the repository
Write-Host "Downloading repository..." -ForegroundColor Yellow
try {
    $zipUrl = "https://github.com/yourusername/digital-hygiene-tool/archive/$Branch.zip"
    $zipPath = Join-Path $tempDir "repo.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing

    # Extract ZIP
    Expand-Archive -Path $zipPath -DestinationPath $tempDir
    $extractedDir = Get-ChildItem -Directory | Select-Object -First 1
    Set-Location $extractedDir.FullName

    Write-Host "✓ Repository downloaded and extracted" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to download repository: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
try {
    & python -m pip install --upgrade pip
    & pip install -r requirements.txt
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Setup database (unless skipped)
if (-not $NoDB) {
    Write-Host "Setting up database..." -ForegroundColor Yellow
    try {
        & python database/setup_mysql.py
        Write-Host "✓ Database setup completed" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Database setup failed or was cancelled" -ForegroundColor Yellow
        Write-Host "You can run it manually later: python database/setup_mysql.py" -ForegroundColor Yellow
    }
}

# Run the tool
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

if (-not $NoWeb) {
    Write-Host "`nStarting web interface..." -ForegroundColor Yellow
    Write-Host "Visit: http://localhost:5000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow

    try {
        & python src/web/app.py
    } catch {
        Write-Host "❌ Failed to start web interface" -ForegroundColor Red
        Write-Host "You can start it manually: python src/web/app.py" -ForegroundColor Yellow
    }
} else {
    Write-Host "`nTo start the web interface manually:" -ForegroundColor Cyan
    Write-Host "  python src/web/app.py" -ForegroundColor White
}

Write-Host "`nTo use the CLI:" -ForegroundColor Cyan
Write-Host "  python src/utils/cli.py --help" -ForegroundColor White

Write-Host "`nInstallation directory: $((Get-Location).Path)" -ForegroundColor Gray