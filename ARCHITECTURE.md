# Project Architecture

## System Overview

The Zambia Digital Hygiene Certification Program is a comprehensive cybersecurity assessment tool with two primary components:

1. **Windows Desktop Application** (Phase 1 - Current)
2. **Web Portal** (Phase 1 - Landing Page; Phase 2 - Full Dashboard)

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Zambia Digital Hygiene Program                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────┐           ┌──────────────────────┐        │
│  │  Windows Desktop App │           │    Web Portal        │        │
│  │  (Standalone .exe)   │           │  (Flask Landing Page)│        │
│  │                      │           │                      │        │
│  │  • GUI Wizard        │           │  • Marketing Page    │        │
│  │  • 5 Assessment      │           │  • About Page        │        │
│  │    Screens           │           │  • Verify Cert       │        │
│  │  • 15-Control        │           │  • Download Link     │        │
│  │    Assessment        │           │                      │        │
│  │  • Real-time Progress│           │  Phase 2:            │        │
│  │  • JSON/HTML Reports │           │  • Dashboard         │        │
│  │  • Local Storage     │           │  • User Auth         │        │
│  │                      │           │  • Assessment Mgmt   │        │
│  └──────────────────────┘           │  • Analytics         │        │
│           ↓                          └──────────────────────┘        │
│           └─────────────────────────────┬────────────────────────┘ │
│                                         ↓                          │
│                        ┌────────────────────────────┐              │
│                        │  Assessment Engine (Core)  │              │
│                        │                            │              │
│                        │  • 15 Security Controls    │              │
│                        │  • Scoring Algorithm       │              │
│                        │  • Tier Assignment         │              │
│                        │  • Recommendations         │              │
│                        └────────────────────────────┘              │
│                                         ↓                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Reports    │  │   Database   │  │  Pre-Deploy  │             │
│  │  (JSON/CSV/  │  │   Layer      │  │   Checker    │             │
│  │  HTML/PDF)   │  │              │  │              │             │
│  │              │  │  • MySQL     │  │  • 13 Checks │             │
│  │ Local Files  │  │  • SQLAlchemy│  │  • Readiness │             │
│  │              │  │  • Models    │  │    Report    │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              CLI Interface (automation)                       │  │
│  │  • assess • scan • manual • predeploy • web • init-db • etc. │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
sakhile_final-_year_pro/
│
├── windows_app.py              ← Entry point for desktop app
├── cli.py                      ← Entry point for CLI
├── requirements.txt            ← Python dependencies
├── pytest.ini                  ← Test configuration
│
├── src/                        ← Main source code
│   ├── __init__.py
│   │
│   ├── gui/                    ← Desktop GUI (Phase 1)
│   │   ├── __init__.py
│   │   ├── theme.py            ← Design constants (#0D1B2A, #00C896)
│   │   ├── app.py              ← Main CTk window manager
│   │   └── screens/            ← 5 Assessment screens
│   │       ├── welcome.py       ← Splash screen
│   │       ├── business_info.py ← Form screen
│   │       ├── scanning.py      ← Live progress screen
│   │       ├── manual_checks.py ← Questionnaire screen
│   │       └── results.py       ← Certification + export
│   │
│   ├── security/               ← Security assessment logic
│   │   ├── __init__.py
│   │   ├── assessment/         ← 15-control assessment
│   │   │   ├── __init__.py
│   │   │   └── assessor.py     ← DigitalHygieneAssessor class
│   │   │       ├── ControlResult (data class)
│   │   │       ├── BusinessInfo (data class)
│   │   │       ├── AssessmentResults (data class)
│   │   │       ├── run_assessment() → AssessmentResults
│   │   │       └── CONTROL_CATALOGUE (15 controls)
│   │   │
│   │   └── deployment/         ← Pre-deployment checks
│   │       ├── __init__.py
│   │       └── checker.py      ← PreDeploymentChecker class
│   │           ├── CheckResult (data class)
│   │           ├── DeploymentReadiness (report)
│   │           └── run_all() → 13 deployment checks
│   │
│   ├── reporting/              ← Report generation
│   │   ├── __init__.py
│   │   ├── generator.py        ← ReportGenerator class
│   │   │   ├── generate_html_report() → file path
│   │   │   ├── generate_json_report() → dict
│   │   │   ├── generate_csv_report() → list of rows
│   │   │   └── generate_pdf_report() → file path (framework)
│   │   │
│   │   └── templates/
│   │       └── report.html     ← HTML template
│   │
│   ├── web/                    ← Flask web application
│   │   ├── __init__.py
│   │   ├── app.py              ← Flask app factory
│   │   │   ├── create_app() → Flask app
│   │   │   ├── GET /           → Landing page
│   │   │   ├── GET /download   → Redirect to .exe
│   │   │   ├── GET /about      → About page
│   │   │   ├── GET /verify/<id>→ Verify cert (Phase 2)
│   │   │   └── Error handlers (404, 500)
│   │   │
│   │   ├── app_full.py         ← Backup of Phase 1 full app
│   │   │
│   │   └── templates/          ← Jinja2 HTML templates
│   │       ├── base.html       ← Base layout
│   │       ├── index.html      ← Landing page
│   │       ├── about.html      ← About page
│   │       ├── verify.html     ← Cert verification
│   │       ├── 404.html        ← Error page
│   │       └── 500.html        ← Error page
│   │
│   ├── database/               ← Database layer (Phase 2 foundation)
│   │   ├── __init__.py
│   │   ├── connection.py       ← DB connection & models
│   │   └── init.sql            ← Schema definition
│   │
│   └── utils/                  ← Utility modules
│       ├── __init__.py
│       ├── cli.py              ← CLI commands (click-based)
│       │   ├── @click.command() decorators
│       │   ├── assess_command()
│       │   ├── scan_command()
│       │   ├── manual_command()
│       │   ├── predeploy_command()
│       │   ├── web_command()
│       │   ├── init_db_command()
│       │   └── users_command()
│       ├── config.py           ← Configuration loading
│       ├── logging_config.py   ← Logging setup
│       └── exceptions.py       ← Custom exceptions (Phase 2)
│
├── tests/                      ← Test suite (42 tests, 100% passing)
│   ├── __init__.py
│   ├── test_assessor.py        ← Assessment engine tests
│   ├── test_deployment.py      ← Deployment checker tests
│   └── test_web.py             ← Flask app tests
│
├── devops/                     ← Deployment configuration
│   ├── build.spec             ← PyInstaller spec
│   └── build.bat              ← Windows build script
│
├── database/                   ← Database setup scripts
│   ├── init.sql               ← MySQL schema
│   ├── setup_mysql.py         ← MySQL setup utility
│   └── setup_mysql.sh         ← MySQL setup shell script
│
├── logs/                       ← Application logs (created at runtime)
├── reports/                    ← Assessment reports (created at runtime)
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml          ← GitHub Actions CI/CD
│
├── Dockerfile                  ← Container image
├── docker-compose.yml          ← Multi-container orchestration
│
├── .env.example               ← Environment variables template
├── .pre-commit-config.yaml    ← Pre-commit hooks
├── .gitignore                 ← Git ignore rules
│
├── README.md                  ← Main documentation
├── BUILD.md                   ← Build instructions
├── DEPLOYMENT.md              ← Deployment guide
├── ENVIRONMENT_SETUP.md       ← Dev environment guide
├── ARCHITECTURE.md            ← This file
├── CONTRIBUTING.md            ← Contribution guidelines
├── SECURITY.md                ← Security best practices
├── CODE_OF_CONDUCT.md         ← Community guidelines
├── CHANGELOG.md               ← Version history
├── PROJECT_PROPOSAL.md        ← Technical proposal
├── COMPLETION_SUMMARY.md      ← Phase 1 summary
├── TESTING_CHECKLIST.md       ← QA verification
├── TODO.md                    ← Development roadmap
│
└── LICENSE                    ← MIT License
```

---

## Data Flow Diagram

### Assessment Flow (Desktop App)

```
User runs ZambiaDigitalHygiene.exe
    ↓
Welcome Screen
    ↓
Business Info Form
    ↓ (create BusinessInfo object)
    ↓
Automated Scanning (C01-C05)
    ├─ _check_os_updates()
    ├─ _check_antivirus()
    ├─ _check_firewall()
    ├─ _check_password_policy()
    └─ _check_backup_system()
    ↓ (create ControlResult objects)
    ↓
Manual Questions (C06-C15)
    ├─ Security Awareness Training
    ├─ Access Control Policy
    ├─ Incident Response
    ├─ Data Encryption
    ├─ Mobile Device Security
    ├─ Physical Security
    ├─ Network Security
    ├─ Acceptable Use Policy
    ├─ Vendor Risk Management
    └─ Regulatory Compliance
    ↓ (create manual_answers dict)
    ↓
Assessment Calculation
    ├─ Calculate score (0-120)
    ├─ Determine certification level
    ├─ Identify critical failures
    └─ Generate recommendations
    ↓ (create AssessmentResults object)
    ↓
Results Display
    ├─ Certification badge (Gold/Silver/Bronze)
    ├─ Score breakdown
    └─ Recommendations
    ↓
Report Export
    ├─ Save JSON
    └─ Save HTML
    ↓
Exit or New Assessment
```

### Assessment Engine Core

```
DigitalHygieneAssessor(business_info, manual_answers)
    ↓
run_assessment() → AssessmentResults
    │
    ├─ 5 Automated Checks (C01-C05) → 50 points max
    │   ├─ OS Updates: 10 points
    │   ├─ Antivirus: 15 points
    │   ├─ Firewall: 10 points
    │   ├─ Password Policy: 10 points
    │   └─ Backups: 5 points
    │
    ├─ 10 Manual Checks (C06-C15) → 70 points max
    │   ├─ Training: 8 points
    │   ├─ Access Control: 7 points
    │   ├─ Incident Response: 7 points
    │   ├─ Encryption: 7 points
    │   ├─ Mobile Security: 5 points
    │   ├─ Physical Security: 5 points
    │   ├─ Network Security: 5 points
    │   ├─ Acceptable Use: 5 points
    │   ├─ Vendor Risk: 8 points
    │   └─ Compliance: 8 points
    │
    └─ Total: 120 points
        ├─ GOLD: ≥80% + 0 critical failures
        ├─ SILVER: ≥60% + ≤1 critical failure
        ├─ BRONZE: ≥40% + ≤2 critical failures
        └─ NOT CERTIFIED: <40% or >2 critical failures
```

---

## Technology Stack

### Desktop Application
- **Framework**: customtkinter (5.2.0+)
- **Build**: PyInstaller (6.0.0+)
- **System Utils**: psutil (5.9.0+)
- **UI Theme**: Custom dark theme (#0D1B2A / #00C896)

### Web Application
- **Framework**: Flask (2.3.0+)
- **Frontend**: Bootstrap 5.3.0+, JavaScript
- **Icons**: Font Awesome 6.5.0+

### Core Libraries
- **CLI**: click (8.1.0+)
- **Configuration**: PyYAML (6.0+)
- **Logging**: Python standard logging
- **Output Formatting**: rich (13.0.0+)

### Database (Phase 2)
- **ORM**: SQLAlchemy (2.0.0+)
- **Database**: MySQL 8.0+
- **Connector**: mysql-connector-python (8.0.0+)

### Testing
- **Framework**: pytest (7.4.0+)
- **Coverage**: pytest-cov (4.1.0+)
- **Mocking**: unittest.mock

### Deployment
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Server**: Gunicorn (production)
- **Reverse Proxy**: Nginx (production)

### Development Tools
- **Code Formatting**: black (24.1.0+)
- **Linting**: flake8 (7.0.0+)
- **Type Checking**: mypy (1.8.0+)
- **Import Sorting**: isort (5.13.0+)
- **Security**: bandit (1.7.5+)
- **Pre-commit**: pre-commit (2.15.0+)
- **CI/CD**: GitHub Actions

---

## Module Dependencies

### Assessment Module Dependencies
```
assessor.py
    ├─ requires: BusinessInfo (data class)
    ├─ requires: ControlResult (data class)
    ├─ requires: AssessmentResults (data class)
    ├─ uses: logging
    ├─ uses: psutil (for system checks)
    └─ optional: Phase 2 database models
```

### GUI Module Dependencies
```
app.py
    ├─ requires: screens (all 5 screens)
    ├─ uses: theme (design constants)
    ├─ requires: DigitalHygieneAssessor
    ├─ requires: ReportGenerator
    └─ uses: customtkinter
```

### Web Module Dependencies
```
app.py
    ├─ requires: Flask
    ├─ uses: templates (Jinja2)
    ├─ optional: DigitalHygieneAssessor (Phase 2)
    └─ optional: database models (Phase 2)
```

### CLI Module Dependencies
```
cli.py
    ├─ requires: click (CLI framework)
    ├─ uses: DigitalHygieneAssessor
    ├─ uses: ReportGenerator
    ├─ uses: PreDeploymentChecker
    ├─ uses: config (configuration)
    ├─ uses: logging_config
    └─ optional: database (Phase 2)
```

---

## Key Design Patterns

### 1. Data Classes
Used for immutable data structures:
```python
@dataclass
class BusinessInfo:
    name: str
    id: str
    # ... other fields

@dataclass
class ControlResult:
    control_id: str
    passed: bool
    points: int
    # ...

@dataclass
class AssessmentResults:
    score: int
    total_possible: int
    certification_level: str
    # ...
```

### 2. Factory Pattern
Flask app factory for flexible configuration:
```python
def create_app():
    app = Flask(__name__)
    # ... configuration
    return app
```

### 3. Strategy Pattern
Different assessment tiers (Tier 1, 2, 3):
```python
assessor = DigitalHygieneAssessor(
    business_info=business,
    assessment_tier="automated"  # or "manual_verification"
)
```

### 4. Command Pattern
CLI commands as separate functions:
```python
@cli.command()
def assess():
    """Run full assessment."""
    pass
```

### 5. Report Generator (Template Method)
```python
class ReportGenerator:
    def generate_html_report(self, results, business):
        # Template method - override _build_html() in subclasses
        html = self._build_html(results, business)
        return self._save_file(html, ".html")
```

---

## Security Architecture

### Input Validation
- All user inputs validated before processing
- File paths checked for directory traversal
- Business IDs validated for format

### Logging Security
- No sensitive data in logs
- Structured logging for audit trails
- Log rotation and management

### Database Security (Phase 2)
- SQL injection prevention via SQLAlchemy ORM
- Connection pooling and SSL
- Least privilege database user

### API Security (Phase 2)
- JWT token authentication
- Rate limiting
- CORS configuration

---

## Scalability Considerations

### Current (Phase 1)
- Single-machine desktop application
- No concurrent usage constraints
- Local file-based reports

### Phase 2 (Database + Web)
- Multi-user web dashboard
- Database connection pooling
- Async task processing (Celery ready)
- Horizontal scaling via containers

### Phase 3+ (Enterprise)
- Microservices architecture
- Message queues (RabbitMQ/Kafka)
- CDN for static assets
- Multi-region deployment

---

## Performance Optimization

### Current Optimizations
- Assessment completes <30 seconds
- Report generation <5 seconds
- Efficient system scanning (psutil)
- Lazy loading of GUI components

### Future Optimizations
- Database query optimization (indexes)
- Caching (Redis)
- API response pagination
- Report streaming

---

## Testing Architecture

### Unit Tests
- Assessment engine logic
- Report generation
- Utility functions
- CLI commands

### Integration Tests
- Assessment → Reporting pipeline
- CLI → Assessment workflow
- Web routes

### End-to-End Tests
- Full assessment workflow (desktop)
- Web portal navigation

---

## Deployment Architecture

### Development
```
Local Machine
    ├─ Python venv
    ├─ SQLite database (optional)
    └─ Flask dev server
```

### Staging
```
Docker Container
    ├─ Flask app
    ├─ MySQL database (linked)
    └─ Exposed on localhost:5000
```

### Production
```
Linux Server / Cloud
    ├─ Docker Container (web app)
    ├─ MySQL Database Container
    ├─ Nginx Reverse Proxy
    ├─ SSL/TLS (Let's Encrypt)
    └─ Monitoring & Logging
```

---

## References

- [Project Proposal](PROJECT_PROPOSAL.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [README](README.md)

---

**Last Updated**: May 10, 2026
