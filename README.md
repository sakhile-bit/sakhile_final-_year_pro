ī# Zambia Digital Hygiene Certification Program

[![CI/CD Pipeline](https://github.com/yourusername/zambia-digital-hygiene/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/yourusername/zambia-digital-hygiene/actions/workflows/ci-cd.yml)
[![Coverage](https://img.shields.io/badge/coverage-80%25-green)](https://yourusername.github.io/zambia-digital-hygiene/htmlcov/)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A comprehensive cybersecurity assessment tool for Small and Medium Enterprises (SMEs) in Zambia, designed to evaluate digital hygiene and provide certification. Aligned with NIST CSF, CIS Controls v8, ISO 27001:2022, and UK Cyber Essentials.

## 🌟 Features

### Core Assessment (v2.0 – 15-Control Framework)

- **15 Security Controls**: 5 automated + 10 manual, covering technical, administrative, and physical domains
- **Three Assessment Tiers**: Tier 1 (self-assessment), Tier 2 (automated script), Tier 3 (manual on-site)
- **120-Point Scoring**: Weighted across all 15 controls
- **Certification Levels**: Gold (≥80%), Silver (≥60%), Bronze (≥40%), with critical-failure gates
- **Detailed Reporting**: JSON, CSV, HTML, and PDF formats with framework references

### Enhanced Features

- **Web Dashboard**: Modern web interface for assessment management
- **Database Integration**: MySQL database for data persistence (SQLite fallback for dev)
- **Multi-format Reports**: Professional HTML and PDF reports with NIST/CIS/ISO references
- **REST API**: Programmatic access to assessment data
- **User Management**: Role-based access control (admin, assessor, viewer)
- **Audit Logging**: Complete audit trail
- **Manual Assessment Guide**: Printable 15-control on-site checklist
- **Zambia Context**: Includes ZICTA/CERT reporting, Data Protection Act compliance checks

### Security Controls Assessed

| ID  | Control                     | Points  | Type           | Verification |
| --- | --------------------------- | ------- | -------------- | ------------ |
| C01 | Operating System Updates    | 10      | Technical      | Automated    |
| C02 | Antivirus Protection        | 15      | Technical      | Automated    |
| C03 | Firewall Configuration      | 10      | Technical      | Automated    |
| C04 | Password Policy             | 10      | Technical      | Automated    |
| C05 | Backup Systems              | 10      | Technical      | Automated    |
| C06 | Security Awareness Training | 8       | Administrative | Manual       |
| C07 | Access Control Policy       | 7       | Administrative | Manual       |
| C08 | Incident Response Plan      | 7       | Administrative | Manual       |
| C09 | Data Encryption             | 7       | Technical      | Manual       |
| C10 | Mobile Device Security      | 5       | Technical      | Manual       |
| C11 | Physical Security           | 5       | Physical       | Manual       |
| C12 | Network Security            | 5       | Technical      | Manual       |
| C13 | Acceptable Use Policy       | 5       | Administrative | Manual       |
| C14 | Vendor / Third-Party Risk   | 8       | Administrative | Manual       |
| C15 | Regulatory Compliance       | 8       | Administrative | Manual       |
|     | **Total**                   | **120** |                |              |

## 🚀 Quick Start

### Install from your terminal (PowerShell, CMD, or bash)

The tool installs as a normal Python package and puts a global **`zamsec`**
command on your PATH — no cloning or virtualenv juggling required.

**Any OS — with pip (Python 3.9+):**

```bash
pip install "https://github.com/sakhile-bit/sakhile_final-_year_pro/archive/refs/heads/main.zip"
```

**Recommended — with [pipx](https://pipx.pypa.io) (isolated, always-on-PATH):**

```bash
pipx install "https://github.com/sakhile-bit/sakhile_final-_year_pro/archive/refs/heads/main.zip"
```

**Or use the one-line installers** (they check Python, install, and verify PATH):

_Windows PowerShell:_

```powershell
irm https://raw.githubusercontent.com/sakhile-bit/sakhile_final-_year_pro/main/devops/install.ps1 | iex
```

_Windows Command Prompt:_

```cmd
curl -fsSL -o install.bat https://raw.githubusercontent.com/sakhile-bit/sakhile_final-_year_pro/main/devops/install.bat && install.bat
```

_Linux/macOS:_

```bash
curl -fsSL https://raw.githubusercontent.com/sakhile-bit/sakhile_final-_year_pro/main/devops/install.sh | bash
```

Then, from **any** terminal:

```bash
zamsec --help          # all commands
zamsec scan            # quick system security scan
zamsec assess          # full 15-control assessment
zamsec harden          # infrastructure hardening audit (+ --fix-all-safe)
zamsec web             # web dashboard at http://127.0.0.1:5000
zamsec completion      # enable TAB completion for your shell
zamsec upgrade         # self-update to the latest version
```

**Optional extras** (PDF reports, MySQL, Active Directory auditing, …):

```bash
pip install "zambia-digital-hygiene[all] @ https://github.com/sakhile-bit/sakhile_final-_year_pro/archive/refs/heads/main.zip"
```

Available extras: `pdf`, `mysql`, `postgres`, `ad`, `audit`, `gui`, `server`, `all`.

See [INSTALL_SCRIPTS.md](docs/INSTALL_SCRIPTS.md) for installation details and
[CLI.md](docs/CLI.md) for the complete command reference.

### Prerequisites

- Python 3.9+
- Windows 10/11 for the automated host assessment & hardening checks
  (the CLI itself runs anywhere)
- MySQL 8.0+ only for production web deployments (SQLite works out of the box)

## 🔧 Environment Setup

### For Ubuntu/Linux Users (Recommended)

If you're using **Ubuntu 20.04+**, follow the comprehensive [ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) guide, which covers:

- System prerequisites and package installation
- Handling PEP 668 "externally-managed-environment" errors
- Virtual environment setup (venv)
- Database configuration (SQLite for dev, MySQL for production)
- Running the application, tests, and CLI commands
- Troubleshooting common issues

**Quick Start for Ubuntu:**

```bash
# Clone and navigate
cd ~/Desktop
git clone https://github.com/sakhile-bit/sakhile_final-_year_pro.git
cd sakhile_final-_year_pro

# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-dev git build-essential

# Install Python dependencies
python3 -m pip install --break-system-packages -r requirements.txt

# Start the web server
python3 cli.py web --debug
```

Then open **http://127.0.0.1:5000** in your browser.

👉 **For detailed troubleshooting and full setup instructions, see [ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md)**

### Manual Installation (Windows/Other)

1. **Clone and enter directory**

   ```bash
   cd c:\Users\sakil\Desktop\sakhile_final-_year_pro
   ```

2. **Create virtual environment** (if needed)

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database** (optional - uses SQLite by default)

   For MySQL setup:

   ```bash
   python database/setup_mysql.py
   ```

   This will:
   - Install MySQL if needed
   - Create the database and user
   - Set up tables and sample data
   - Generate a `.env` file with connection details

   Alternatively, set environment variables manually:

   ```bash
   set DB_HOST=localhost
   set DB_PORT=3306
   set DB_NAME=digital_hygiene
   set DB_USER=user
   set DB_PASSWORD=password
   ```

5. **Run tests** (verify setup)

   ```bash
   python -m pytest -q
   ```

6. **Start the web app**
   ```bash
   python cli.py web --debug
   ```
   Then open http://localhost:5000 in your browser.
   - **Default login**: `admin` / `admin123` (change on first login)

### Environment Variables (Production)

```
DEBUG=false                    # Disable debug mode
SECRET_KEY=<random-key>        # Flask secret (generated if not set)
DB_HOST=localhost              # MySQL host
DB_PORT=3306  (also default)                 # MySQL port
DB_NAME=digital_hygiene        # Database name
DB_USER=                 # Database user
DB_PASSWORD=<password>         # Database password
LOG_LEVEL=              # Logging level
WEB_HOST=            # Web server host
WEB_PORT=                # Web server port
```

## 📖 Usage

### Windows Desktop App (Phase 1 – Current)

**Download and Run:**

1. **Download** `ZambiaDigitalHygiene.exe` from the [latest release](https://github.com/sakhile-bit/sakhile_final-_year_pro/releases)
2. **Double-click** the .exe – no installation needed
3. **Follow the wizard:**
   - Enter business information
   - Run automated checks
   - Answer 10 manual questions
   - Get your certification (Bronze/Silver/Gold)
4. **Export reports** in JSON or HTML format

**For developers – build the .exe:**

See [BUILD.md](docs/BUILD.md) for full instructions. Quick version:

```bash
# On Windows:
.\devops\build.bat
# Output: dist\ZambiaDigitalHygiene.exe
```

### Web Portal (Landing Page + Deployment)

The web app serves as a **marketing landing page** and **Phase 2 foundation**. 

**Local Development:**

```bash
python -m flask run
# or
python src/web/app.py
```

Then open **http://localhost:5000**

**Docker Deployment (Recommended for production):**

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete guide. Quick start:

```bash
cp .env.example .env
# Edit .env with your settings
docker-compose up --build
```

The app will be at **http://localhost:5000**

### Web Interface (Recommended)

1. **Start the app**
   ```bash
   python src/web/app.py
   ```
2. **Open http://localhost:5000**
   - View marketing landing page
   - Click "Download" to get the Windows exe
   - View "About" page for program details
   - Verify certificates (Phase 2)

### Command-Line Interface (CLI)

For batch processing and automation:

```bash
# Run full assessment
python cli.py assess --business-name "Acme Ltd" --business-id REG-001 -f html -f json

# Quick system scan
python cli.py scan

# Generate manual assessment guide
python cli.py manual

# Check deployment readiness
python cli.py predeploy

# Start web server
python cli.py web

# Initialize database
python cli.py init-db

# Manage users
python cli.py users list
python cli.py users create

# Show status
python cli.py status

# Get help
python cli.py --help
python cli.py assess --help
```

### Programmatic API

```python
from src.security.assessment.assessor import DigitalHygieneAssessor, BusinessInfo

# Create a business profile
business = BusinessInfo(
    name="Tech Company Ltd",
    id="TC001",
    industry="Technology",
    contact_person="Jammy Phiri",
    contact_email="jammyphiri@gmail.com",
    province="Lusaka"
)

# Run full assessment (with manual answers)
assessor = DigitalHygieneAssessor(
    business_info=business,
    manual_answers={
        "C06_security_training": 1,      # Fully implemented
        "C07_access_control": 0.5,       # Partially implemented
        "C08_incident_response": 0,      # Not implemented
        # ... etc for all 10 manual controls
    }
)
results = assessor.run_assessment()

print(f"Score: {results.score}/{results.total_possible}")
print(f"Level: {results.certification_level}")
for rec in results.recommendations:
    print(f"  - {rec}")

# Generate reports
from src.reporting.generator import ReportGenerator

gen = ReportGenerator(output_dir="reports")
html_file = gen.generate_html_report(results, business, "assessment_report")
json_data = gen.generate_json_report(results, business)
csv_rows = gen.generate_csv_report(results, business)
```

### Testing

Run the test suite to verify everything works:

```bash
python -m pytest -q              # Quick run
python -m pytest -v              # Verbose
python -m pytest --cov=src       # With coverage
```

## 🏗️ Architecture

```
src/
├── assessment/          # Core assessment logic
│   ├── assessor.py     # Main assessment class
│   └── __init__.py
├── database/           # Database models and connections
│   ├── models.py       # SQLAlchemy models
│   ├── connection.py   # Database connection management
│   └── __init__.py
├── reporting/          # Report generation
│   ├── generator.py    # Multi-format report generator
│   └── __init__.py
├── web/               # Web dashboard
│   ├── app.py         # Flask application
│   ├── routes.py      # Web routes
│   └── templates/     # Jinja2 templates
├── utils/             # Utilities
│   ├── cli.py         # Command-line interface
│   ├── config.py      # Configuration management
│   ├── logging_config.py # Logging setup
│   └── exceptions.py  # Custom exceptions
└── tests/             # Test suite
    ├── test_assessor.py
    └── __init__.py
```

## 🗄️ Database Schema

The application uses MySQL with the following main tables:

- `users` - User accounts and authentication
- `businesses` - Business information
- `assessments` - Assessment results and metadata
- `certificates` - Issued certificates
- `audit_logs` - Audit trail

## 🔧 Configuration

Create a `config.yaml` file for custom configuration:

```yaml
app:
  log_level: INFO
  log_file: logs/app.log

database:
  host: localhost
  port: 3306
  name: digital_hygiene
  user: your_user
  password: your_password

email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  username: your_email@gmail.com
  password: your_app_password

reports:
  output_dir: reports
  formats: [json, html, pdf]
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest src/tests/test_assessor.py

# Run Windows-specific tests only
pytest -m windows
```

## 📦 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t zambia-digital-hygiene .
docker run -p 5000:5000 zambia-digital-hygiene
```

### Standalone Executable

```bash
# Create executable (Windows)
pyinstaller --onefile --name zambia-digital-hygiene src/main.py

# Run the executable
./dist/zambia-digital-hygiene.exe assess
```

## 🌐 API Documentation

### REST API Endpoints

- `GET /api/assessments` - List assessments
- `POST /api/assessments` - Create assessment
- `GET /api/assessments/{id}` - Get assessment details
- `GET /api/certificates` - List certificates
- `POST /api/certificates` - Issue certificate

### Authentication

Use JWT tokens for API authentication:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/assessments
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run linting and formatting
black src/
isort src/
flake8 src/
mypy src/
```

## 📊 Certification Levels

| Level             | Score Range | Requirements                                   |
| ----------------- | ----------- | ---------------------------------------------- |
| **Gold**          | 40-50       | All controls implemented, no critical failures |
| **Silver**        | 30-39       | 4+ controls implemented, ≤1 critical failure   |
| **Bronze**        | 20-29       | 3+ controls implemented, ≤2 critical failures  |
| **Not Certified** | <20         | Significant security gaps                      |

## � Documentation

Key documentation files for your project:

| Document | Purpose |
|----------|---------|
| [CLI.md](docs/CLI.md) | **👉 Full `zamsec` CLI reference** – every command, option, exit code, and env var |
| [INSTALL_SCRIPTS.md](docs/INSTALL_SCRIPTS.md) | Installing from your terminal (pip/pipx + one-line scripts) |
| [USER_GUIDE.md](docs/USER_GUIDE.md) | End-user guide for the desktop app, web portal, and CLI |
| [ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) | **👉 Start here for Ubuntu/Linux setup** – Comprehensive guide with troubleshooting |
| [DATABASE_SETUP_FOR_TEAM.md](docs/DATABASE_SETUP_FOR_TEAM.md) | **👉 Team database setup** – Step-by-step MySQL database creation, credentials, and initialization |
| [DATABASE_SETUP.md](docs/DATABASE_SETUP.md) | Database configuration for MySQL and SQLite |
| [SETUP.md](docs/SETUP.md) | Manual setup instructions for other platforms |
| [TESTING_CHECKLIST.md](docs/TESTING_CHECKLIST.md) | Test procedures and acceptance criteria |
| [PROJECT_PROPOSAL.md](docs/PROJECT_PROPOSAL.md) | Project overview and requirements |

## �📞 Support

- **Documentation**: [Read the Docs](https://zambia-digital-hygiene.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/zambia-digital-hygiene/issues)
- **Email**: Stanford.sakhile@cs.unza.zm/misheck.trinity.chama@cs.unza.zm
- **Phone**: +260 969274765

## � Production Deployment

### Security Hardening

- **HTTPS Only**: Set `SESSION_COOKIE_SECURE=True` and use SSL certificates
- **Strong Passwords**: Enforced 12+ characters with uppercase, lowercase, digits, and special characters
- **Rate Limiting**: 5 login attempts per 5 minutes per IP
- **Session Security**: HTTPOnly, SameSite cookies with 30-minute lifetime
- **Admin Password Reset**: Required on first login

### Admin Reset Instructions

If you need to reset the admin password:

1. Connect to MySQL database
2. Run: `UPDATE users SET password_hash = '' WHERE username = 'admin';`
3. Restart the app - admin will be prompted to change password on login

### Environment Validation

The app validates required environment variables on startup:

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `SECRET_KEY` (generate a strong random key)
- `DEBUG=false` for production

## �📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Zambia Ministry of Technology and Science
- Local cybersecurity community
- Open source contributors
- university of zambia

## Changelog

### Version 2.0.0 (Current)

- Complete architecture refactor
- Web dashboard implementation
- MySQL database integration
- Multi-format reporting
- REST API
- Comprehensive test suite
- Docker containerization
- CI/CD pipeline

### Version 1.0.0

- Basic automated assessment
- Manual assessment guide
- Simple reporting
- Certificate generation

---

**Built with ❤️ for Zambia's digital future**
