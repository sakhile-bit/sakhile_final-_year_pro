# Development Guide

This guide will help you set up your development environment and understand the development workflow for the Zambia Digital Hygiene Certification Program.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Development Workflow](#development-workflow)
4. [Common Tasks](#common-tasks)
5. [Testing](#testing)
6. [Building & Deployment](#building--deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** (preferably 3.11 or 3.12)
- **Git** (for version control)
- **pip** or **conda** (Python package manager)
- **Docker** and **Docker Compose** (for containerized development)
- **VS Code** (recommended editor)
- **make** (for running common commands on Linux/macOS, optional on Windows)

### Check Versions

```bash
python3 --version  # Should be 3.10 or higher
git --version
docker --version
docker-compose --version
```

---

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/sakhile-bit/sakhile_final-_year_pro.git
cd sakhile_final-_year_pro
```

### 2. Create Virtual Environment

```bash
# Using Python venv (recommended)
python3 -m venv .venv

# Activate on Linux/macOS
source .venv/bin/activate

# Activate on Windows
.venv\Scripts\activate

# Or use make
make venv
```

### 3. Install Dependencies

```bash
# Development setup (includes all tools)
make dev-install

# Or manual installation
pip install -r requirements.txt
pip install --upgrade black flake8 mypy pytest pytest-cov isort bandit
```

### 4. Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your settings
# For local development, defaults usually work fine
```

### 5. Setup Pre-commit Hooks (Recommended)

```bash
make pre-commit-install
# or
pre-commit install
```

### 6. Verify Installation

```bash
make health
# or
python3 cli.py --help
```

> **Tip:** installing the package in editable mode (`pip install -e .`) puts a
> global `zamsec` command on your PATH, so every `python3 cli.py …` example in
> this guide also works as `zamsec …` from any directory. Full command
> reference: [CLI.md](CLI.md).

---

## Development Workflow

### Branch Strategy

We follow a modified Git Flow:

```
main (production releases)
  ↓
develop (integration branch)
  ↓
feature/* (feature branches)
hotfix/* (urgent fixes)
```

### Creating a Feature Branch

```bash
# Update develop first
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Work on your feature...

# Commit with conventional commits
git add .
git commit -m "feat: add new assessment control"
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, etc.
- `ci`: CI/CD changes

**Examples:**

```bash
# Good feature commit
git commit -m "feat(assessment): add cloud security control (C16)

- Implements automated cloud service scanning
- Checks S3, Azure Storage, GCP bucket permissions
- Adds 10 points to total scoring

Closes #123"

# Good fix commit
git commit -m "fix(gui): prevent duplicate screen rendering

Fixes issue where manual checks screen appeared twice after
returning from scanning screen"

# Good docs commit
git commit -m "docs: update API endpoint documentation"
```

### Pull Request Workflow

1. **Push your branch**

   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request on GitHub**
   - Add descriptive title and description
   - Reference related issues with `Closes #123`
   - Ensure all CI checks pass

3. **Address Review Comments**

   ```bash
   # Make changes
   git add .
   git commit -m "fix review comments"
   git push origin feature/your-feature-name
   ```

4. **Merge to Develop**
   - Squash commits if desired
   - Delete branch after merge

---

## Common Tasks

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
make test-one
# Then enter: tests/test_assessor.py

# Run tests in watch mode
pytest-watch tests/

# Run with verbose output
pytest tests/ -vv

# Run specific test function
pytest tests/test_assessor.py::TestAssessmentTier -v
```

### Code Quality Checks

```bash
# Format code (auto-fix)
make format

# Check formatting without modifying
make format-check

# Run linting
make lint

# Run type checking
make type-check

# Security scan
make security

# All checks together
make quality
```

### Running the Application

```bash
# Desktop app
make run
# or
python3 windows_app.py

# CLI help
make cli
# or
python3 cli.py --help

# Web server (development)
make web
# or
FLASK_ENV=development python3 -m flask run

# Specific CLI command
python3 cli.py assess --help
python3 cli.py scan
```

### Working with Database (Phase 2)

```bash
# Initialize database
make db-init

# Reset database (destructive!)
make db-reset

# Start MySQL with Docker
docker-compose up db

# Access MySQL
mysql -u root -p -h localhost
```

---

## Testing

### Test Structure

```
tests/
├── test_assessor.py        ← Assessment engine tests
├── test_deployment.py      ← Deployment checker tests
└── test_web.py             ← Web application tests
```

### Writing Tests

```python
import pytest
from src.security.assessment.assessor import BusinessInfo, DigitalHygieneAssessor

def test_gold_tier_certification():
    """Test that high score achieves gold tier."""
    business = BusinessInfo(
        name="Test Org",
        id="TEST123",
        contact_person="John Doe",
        contact_email="john@test.com",
        contact_phone="+260..."
    )

    assessor = DigitalHygieneAssessor(business_info=business)
    results = assessor.run_assessment()

    assert results.certification_level in ["GOLD", "SILVER", "BRONZE"]
    assert results.score >= 0
    assert results.score <= 120
```

### Test Coverage

```bash
# Generate coverage report
make test

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Target minimum coverage
pytest --cov=src --cov-fail-under=80 tests/
```

### Testing Best Practices

1. **Use descriptive test names** - `test_gold_tier_with_zero_critical_failures`
2. **Follow AAA pattern** - Arrange, Act, Assert
3. **Test edge cases** - Empty input, null values, boundaries
4. **Mock external dependencies** - Don't hit real APIs in tests
5. **Keep tests isolated** - Each test should be independent

---

## Building & Deployment

### Building Windows Executable

```bash
# Build .exe
make build

# Or manually
python3 -m PyInstaller devops/build.spec

# Result: dist/ZambiaDigitalHygiene.exe
```

### Docker Deployment

```bash
# Build image
make docker-build

# Start services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down

# Access web app
# http://localhost:5000
```

### Manual Server Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

---

## IDE Setup

### VS Code Extensions (Recommended)

Install recommended extensions:

```bash
# VS Code will prompt you to install recommended extensions
# Or manually install:
# - ms-python.python
# - ms-python.vscode-pylance
# - eamodio.gitlens
# - charliermarsh.ruff
# - ms-python.black-formatter
```

### VS Code Workspace Settings

The workspace includes `.vscode/settings.json` with recommended settings:

- Python interpreter path
- Code formatting with Black
- Linting with flake8
- Type checking with Pylance
- Testing with pytest

These are automatically applied when you open the workspace.

---

## Troubleshooting

### Virtual Environment Issues

**Problem**: `Command 'python3' not found`

```bash
# Use python instead of python3
python -m venv .venv
python -m pip install -r requirements.txt
```

**Problem**: Pip modules not found when running

```bash
# Make sure venv is activated
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows
```

### Test Failures

**Problem**: `ModuleNotFoundError: No module named 'src'`

```bash
# Ensure you're running from project root
cd /path/to/sakhile_final-_year_pro
pytest tests/
```

**Problem**: Tests pass locally but fail on GitHub Actions

```bash
# Check Python version compatibility
python3 --version

# Run with specific Python version
python3.11 -m pytest tests/
```

### Build Issues

**Problem**: `PyInstaller: command not found`

```bash
# Install PyInstaller
pip install pyinstaller>=6.0.0

# Or use make
make install
```

**Problem**: Antivirus flags .exe as malicious

This is common with PyInstaller binaries. Options:

1. Sign the .exe with a code signing certificate
2. Submit to antivirus vendors for whitelisting
3. Use trusted distribution channels

### Docker Issues

**Problem**: `docker: command not found`

```bash
# Install Docker Desktop
# https://www.docker.com/products/docker-desktop
```

**Problem**: Port 5000 already in use

```bash
# Use different port
docker-compose -f docker-compose.yml up -p 8000:5000
```

---

## Performance Tips

### Development

- Use `make test-fast` for quick feedback
- Enable auto-formatting to save time
- Use pre-commit hooks to catch issues early

### Building

- Cache Docker layers by ordering Dockerfile commands
- Use `.dockerignore` to exclude unnecessary files
- Consider multi-stage builds for smaller images

### Code

- Profile slow code: `python3 -m cProfile -s cumulative cli.py`
- Use generators for large datasets
- Cache expensive computations

---

## Documentation

### Adding to Documentation

1. **Code Comments** - Use docstrings for all functions

   ```python
   def run_assessment(self) -> AssessmentResults:
       """Run complete 15-control security assessment.

       Returns:
           AssessmentResults with score, tier, and recommendations.

       Raises:
           ValueError: If business info is invalid.
       """
   ```

2. **README/Guides** - Update when adding features
3. **API Docs** - Maintain in comments
4. **CHANGELOG** - Document major changes

### Building Docs Locally

```bash
# Most docs are in Markdown
# View in VS Code or GitHub

# For API documentation
python3 -m pydoc -b src
```

---

## Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2)
- [Testing Best Practices](https://docs.pytest.org/en/latest/)
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](SECURITY.md) - Security best practices
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/sakhile-bit/sakhile_final-_year_pro/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sakhile-bit/sakhile_final-_year_pro/discussions)
- **Email**: development@digitalhygiene.gov.zm

---

**Last Updated**: May 10, 2026

Happy coding! 🚀
