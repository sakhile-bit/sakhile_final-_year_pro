# Zambia Digital Hygiene Certification Program

[![CI/CD Pipeline](https://github.com/yourusername/zambia-digital-hygiene/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/yourusername/zambia-digital-hygiene/actions/workflows/ci-cd.yml)
[![Coverage](https://img.shields.io/badge/coverage-80%25-green)](https://yourusername.github.io/zambia-digital-hygiene/htmlcov/)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A comprehensive cybersecurity assessment tool for Small and Medium Enterprises (SMEs) in Zambia, designed to evaluate digital hygiene and provide certification.

## 🌟 Features

### Core Assessment

- **Automated Assessment**: 5 critical security controls evaluation
- **Manual Assessment**: Comprehensive checklist for non-automated scenarios
- **Certification Levels**: Gold, Silver, Bronze, and Not Certified
- **Detailed Reporting**: JSON, CSV, HTML, and PDF formats

### Enhanced Features (v2.0)

- **Web Dashboard**: Modern web interface for assessment management
- **Database Integration**: MySQL database for data persistence
- **Email Notifications**: Automated report delivery
- **Multi-format Reports**: Professional HTML and PDF reports
- **REST API**: Programmatic access to assessment data
- **User Management**: Role-based access control
- **Audit Logging**: Complete audit trail
- **Localization**: Support for multiple languages

### Security Controls Assessed

1. **Operating System Updates** (10 points)
2. **Antivirus Protection** (15 points)
3. **Firewall Configuration** (10 points)
4. **Password Policy** (10 points)
5. **Backup System** (5 points)

## 🚀 Quick Start

### Prerequisites

- Windows 7+ (for automated assessment)
- Python 3.8+
- MySQL 8.0+
- Administrator privileges (recommended)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/zambia-digital-hygiene.git
   cd zambia-digital-hygiene
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database**

   ```bash
   # Using Docker Compose (recommended)
   docker-compose up -d db

   # Or initialize manually
   python -m src.main init-db
   ```

4. **Run the application**

   ```bash
   # Web dashboard
   python -m src.main web

   # CLI assessment
   python -m src.main assess
   ```

## 📖 Usage

### Command Line Interface

```bash
# Run automated assessment
python -m src.main assess --business-name "My Business" --business-id "REG001"

# Generate manual assessment guide
python -m src.main manual

# Start web dashboard
python -m src.main web --host 0.0.0.0 --port 8000

# Initialize database
python -m src.main init-db
```

### Web Interface

1. Start the web server: `python -m src.main web`
2. Open http://localhost:5000 in your browser
3. Register/Login to access the dashboard
4. Create new assessments or view existing ones

### API Usage

```python
from src.main import create_app
from src.assessment.assessor import DigitalHygieneAssessor

# Create assessment programmatically
app = create_app()
with app.app_context():
    assessor = DigitalHygieneAssessor("Business Name", "REG001")
    results = assessor.run_assessment()
    print(f"Score: {results.score}/{results.total_possible}")
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

## 📄 License

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
