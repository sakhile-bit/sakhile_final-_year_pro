# Installing from your terminal

The tool ships as a standard Python package (see `pyproject.toml`). Installing
it puts a global **`zamsec`** command (alias: `zambia-hygiene`) on your PATH,
usable from PowerShell, Command Prompt, or any Unix shell.

## The short way — pip / pipx

Works on every OS with Python 3.9+:

```bash
pip install "https://github.com/sakhile-bit/sakhile_final-_year_pro/archive/refs/heads/main.zip"
```

Or, for an isolated install that never conflicts with other Python packages
(recommended for end users):

```bash
pipx install "https://github.com/sakhile-bit/sakhile_final-_year_pro/archive/refs/heads/main.zip"
```

If you have git installed, `pip install git+https://github.com/sakhile-bit/sakhile_final-_year_pro.git`
works too.

## One-line installer scripts

These live in `devops/` and are fetched straight from GitHub. They check your
Python version, install with pipx or pip, and verify `zamsec` landed on PATH.

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/sakhile-bit/sakhile_final-_year_pro/main/devops/install.ps1 | iex
```

### Windows (Command Prompt)

```cmd
curl -fsSL -o install.bat https://raw.githubusercontent.com/sakhile-bit/sakhile_final-_year_pro/main/devops/install.bat && install.bat
```

### Linux/macOS

```bash
curl -fsSL https://raw.githubusercontent.com/sakhile-bit/sakhile_final-_year_pro/main/devops/install.sh | bash
```

## After installing

```bash
zamsec --version       # confirm the install
zamsec --help          # all commands
zamsec scan            # quick system security scan
zamsec assess          # full 15-control assessment
zamsec harden          # hardening audit (add --fix-all-safe as Administrator)
zamsec web             # web dashboard at http://127.0.0.1:5000
zamsec completion      # TAB-completion setup for bash/zsh/fish/PowerShell
zamsec upgrade         # self-update from GitHub
```

## Optional extras

The base install covers the CLI, scanning, hardening, fleet scanning and the
web dashboard (SQLite). Extras add optional integrations:

| Extra      | Adds                                        |
| ---------- | ------------------------------------------- |
| `pdf`      | PDF report generation (reportlab)           |
| `mysql`    | MySQL database support                      |
| `postgres` | PostgreSQL database support                 |
| `ad`       | Active Directory auditing (ldap3)           |
| `audit`    | Dependency vulnerability scanning           |
| `gui`      | Desktop GUI app (customtkinter)             |
| `server`   | Production WSGI server (gunicorn)           |
| `all`      | Everything above                            |

```bash
pip install "zambia-digital-hygiene[all] @ https://github.com/sakhile-bit/sakhile_final-_year_pro/archive/refs/heads/main.zip"
```

## `zamsec` not found after install?

pip prints a yellow warning when the scripts folder is not on PATH.

- **Windows:** add the folder printed by
  `python -c "import sysconfig; print(sysconfig.get_path('scripts'))"`
  to your PATH, then open a new terminal.
- **Linux/macOS:** add `export PATH="$HOME/.local/bin:$PATH"` to `~/.bashrc`.
- **pipx:** run `pipx ensurepath` once, then open a new terminal.

## Developer install (from a clone)

```bash
git clone https://github.com/sakhile-bit/sakhile_final-_year_pro.git
cd sakhile_final-_year_pro
python -m venv .venv && .venv\Scripts\activate   # or source .venv/bin/activate
pip install -e .[all]
zamsec status
```

`python cli.py …` still works from the project root exactly as before.

## Uninstall

```bash
pip uninstall zambia-digital-hygiene    # or: pipx uninstall zambia-digital-hygiene
```
