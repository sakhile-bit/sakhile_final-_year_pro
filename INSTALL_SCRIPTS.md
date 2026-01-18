# Quick Install Scripts

These scripts allow you to install and run the Zambia Digital Hygiene Assessment Tool with a single command, similar to `irm https://get.activated.win | iex`.

## Windows (PowerShell)

```powershell
irm https://your-domain.com/install.ps1 | iex
```

Or using curl:

```cmd
curl -s https://your-domain.com/install.ps1 | powershell -Command -
```

## Windows (Command Prompt)

```cmd
curl -s https://your-domain.com/install.bat | cmd
```

## Linux/macOS

```bash
curl -s https://your-domain.com/install.sh | bash
```

## What the scripts do:

1. **Check Python installation** - Ensures Python 3.8+ is available
2. **Download the tool** - Clones or downloads the repository
3. **Install dependencies** - Runs `pip install -r requirements.txt`
4. **Setup database** - Runs the MySQL setup script
5. **Start the tool** - Launches the web interface on http://localhost:5000

## Options

### PowerShell Script Options:

- `-NoWeb`: Skip starting the web interface
- `-NoDB`: Skip database setup
- `-Branch "branch-name"`: Specify git branch to download

Example:

```powershell
irm https://your-domain.com/install.ps1 | iex -NoDB
```

## Hosting the Scripts

To make this work like the example, you need to:

1. Host these scripts on a web server
2. Update the repository URLs in the scripts
3. Make sure the scripts are accessible via HTTPS

## Manual Installation

If the quick install doesn't work, you can still install manually:

```bash
git clone https://github.com/yourusername/digital-hygiene-tool.git
cd digital-hygiene-tool
pip install -r requirements.txt
python database/setup_mysql.py
python src/web/app.py
```
