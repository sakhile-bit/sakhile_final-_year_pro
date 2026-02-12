# Zambia Digital Hygiene Certification Program

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

### One-Command Installation

Install and run the tool with a single command:

**Windows (PowerShell):**

```powershell
irm https://your-domain.com/install.ps1 | iex
```

**Windows (Command Prompt):**

```cmd
curl -s https://your-domain.com/install.bat | cmd
```

**Linux/macOS:**

```bash
curl -s https://your-domain.com/install.sh | bash
```

These scripts will automatically:

- Check Python installation
- Download the tool
- Install dependencies
- Setup the database
- Start the web interface

See [INSTALL_SCRIPTS.md](INSTALL_SCRIPTS.md) for details.

### Prerequisites

- Windows 7+ (for automated assessment)
- Python 3.8+
- MySQL 8.0+ (required for production)

### Manual Installation & Setup

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

4. **Configure database** (required - MySQL only)

   Run the MySQL setup script:

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
   set DB_PORT=3306(default)
   set DB_NAME=db_name here
   set DB_USER=user
   set DB_PASSWORD=db_password
   ```

5. **Run tests** (verify setup)

   ```bash
   python -m pytest -q
   ```

6. **Start the web app**
   ```bash
   python src/web/app.py
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

### Web Interface (Recommended)

1. **Start the app**
   ```bash
   python src/web/app.py
   ```
2. **Open http://localhost:5000**
   - Login with default credentials (admin / admin123)
   - Navigate to "Assessment" to run a new assessment
   - View results and download reports (HTML, PDF, JSON, CSV)

### Programmatic API

```python
from src.assessment.assessor import DigitalHygieneAssessor, BusinessInfo

# Create a business profile
business = BusinessInfo(
    name="Tech Company Ltd",
    id="TC001",
    industry="Technology",
    contact_person="Jammy phiri",
    contact_email="jammyphiri@gmail.com"
)

# Run assessment
assessor = DigitalHygieneAssessor(business)
results = assessor.run_assessment()

print(f"Score: {results.score}/{results.total_possible}")
print(f"Level: {results.certification_level}")
for rec in results.recommendations:
    print(f"  - {rec}")
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

## 📞 Support

- **Documentation**: [Read the Docs](https://zambia-digital-hygiene.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/zambia-digital-hygiene/issues)
- **Email**: digitalhygiene@zambia.gov.zm
- **Phone**: +260 211 123456

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

## 🙏 Acknowledgments

- Zambia Ministry of Technology and Science
- Local cybersecurity community
- Open source contributors

## 🔄 Changelog

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
