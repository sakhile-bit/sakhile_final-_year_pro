#!/bin/bash
# Zambia Digital Hygiene Assessment Tool (zamsec) - Linux/macOS installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/sakhile-bit/sakhile_final-_year_pro/main/devops/install.sh | bash
#
# Installs the "zamsec" command globally via pipx (preferred) or pip.

set -e

REPO="https://github.com/sakhile-bit/sakhile_final-_year_pro"
ARCHIVE="$REPO/archive/refs/heads/main.zip"

echo "=============================================="
echo " Zambia Digital Hygiene Assessment Tool"
echo " zamsec - terminal installer"
echo "=============================================="

# --- 1. Check Python --------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "ERROR: Python is not installed."
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL:   sudo yum install python3 python3-pip"
    echo "  macOS:         brew install python3"
    exit 1
fi
echo "Python found: $($PY --version)"
if ! $PY -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo "ERROR: Python 3.9+ is required."
    exit 1
fi

# --- 2. Install --------------------------------------------------------------
if command -v pipx >/dev/null 2>&1; then
    echo "Installing with pipx (isolated environment)..."
    pipx install --force "$ARCHIVE"
else
    echo "Installing with pip..."
    # --user keeps it out of system site-packages; --break-system-packages
    # handles PEP 668 distros (Ubuntu 23.04+, Debian 12+) where user
    # installs are refused without it.
    $PY -m pip install --user --upgrade "$ARCHIVE" ||
        $PY -m pip install --user --break-system-packages --upgrade "$ARCHIVE"
fi

# --- 3. Verify ----------------------------------------------------------------
echo ""
echo "=============================================="
if command -v zamsec >/dev/null 2>&1; then
    echo "Installed successfully!"
    zamsec --version
else
    echo "Installed, but 'zamsec' is not on your PATH yet."
    echo "Add your user scripts directory to PATH, e.g. append to ~/.bashrc:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
    echo "then open a new terminal."
fi
echo "=============================================="
echo ""
echo "Get started:"
echo "  zamsec --help        all commands"
echo "  zamsec scan          quick system security scan"
echo "  zamsec assess        full 15-control assessment"
echo "  zamsec web           web dashboard (http://127.0.0.1:5000)"
echo "  zamsec completion    enable TAB completion"
echo "  zamsec upgrade       update to the latest version"
