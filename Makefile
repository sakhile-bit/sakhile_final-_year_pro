.PHONY: help install dev-install test lint format type-check security clean build run docker-up docker-down pre-commit-install pre-commit-run

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
FLAKE8 := $(PYTHON) -m flake8
MYPY := $(PYTHON) -m mypy
BANDIT := $(PYTHON) -m bandit
VENV := .venv

# Default target
help:
	@echo "Zambia Digital Hygiene Certification Program - Development Commands"
	@echo ""
	@echo "Installation & Setup:"
	@echo "  make install              Install production dependencies"
	@echo "  make dev-install          Install development dependencies"
	@echo "  make venv                 Create virtual environment"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test                 Run all tests with coverage"
	@echo "  make test-fast            Run tests without coverage"
	@echo "  make lint                 Run all linting checks (flake8)"
	@echo "  make format               Format code with black"
	@echo "  make format-check         Check code formatting"
	@echo "  make type-check           Run type checking (mypy)"
	@echo "  make security             Run security scan (bandit)"
	@echo "  make quality              Run all quality checks (lint, format, type, security)"
	@echo ""
	@echo "Pre-commit Hooks:"
	@echo "  make pre-commit-install   Setup pre-commit hooks"
	@echo "  make pre-commit-run       Run pre-commit on all files"
	@echo ""
	@echo "Building & Running:"
	@echo "  make build                Build Windows .exe (PyInstaller)"
	@echo "  make run                  Run desktop app from source"
	@echo "  make cli                  Run CLI help"
	@echo "  make web                  Run web server (Flask)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build         Build Docker image"
	@echo "  make docker-up            Start containers (docker-compose)"
	@echo "  make docker-down          Stop containers"
	@echo "  make docker-logs          View container logs"
	@echo ""
	@echo "Database:"
	@echo "  make db-init              Initialize database schema"
	@echo "  make db-reset             Reset database (destructive)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                Remove build artifacts and cache"
	@echo "  make clean-all            Remove all generated files including venv"
	@echo ""

# Virtual Environment
venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	@echo "✓ Virtual environment created. Activate with: source $(VENV)/bin/activate"

# Installation
install: venv
	$(PIP) install -r requirements.txt
	@echo "✓ Production dependencies installed"

dev-install: install
	$(PIP) install --upgrade pytest pytest-cov black flake8 mypy isort bandit detect-secrets pre-commit
	@echo "✓ Development dependencies installed"

# Testing
test:
	$(PYTEST) tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "✓ Tests passed! Coverage report generated in htmlcov/index.html"

test-fast:
	$(PYTEST) tests/ -v
	@echo "✓ All tests passed!"

test-one:
	@read -p "Enter test file (e.g., tests/test_assessor.py): " test_file; \
	$(PYTEST) $$test_file -v

# Code Quality
lint:
	$(FLAKE8) src/ tests/ --max-line-length=120 --extend-ignore=E203,W503
	@echo "✓ Linting passed (flake8)"

format:
	$(BLACK) src/ tests/ --line-length=120
	$(PYTHON) -m isort src/ tests/ --profile black
	@echo "✓ Code formatted with black and isort"

format-check:
	$(BLACK) src/ tests/ --line-length=120 --check
	$(PYTHON) -m isort src/ tests/ --profile black --check-only
	@echo "✓ Code format is correct"

type-check:
	$(MYPY) src/ --ignore-missing-imports --no-strict-optional
	@echo "✓ Type checking passed (mypy)"

security:
	$(BANDIT) -r src/ --skip B101
	@echo "✓ Security scan passed (bandit)"

quality: lint format-check type-check security
	@echo ""
	@echo "✓ All quality checks passed!"

# Pre-commit Hooks
pre-commit-install:
	$(PIP) install pre-commit
	pre-commit install
	@echo "✓ Pre-commit hooks installed"

pre-commit-run:
	pre-commit run --all-files
	@echo "✓ Pre-commit checks completed"

# Building
build:
	@echo "Building Windows executable..."
	$(PYTHON) -m PyInstaller --onefile devops/build.spec
	@echo "✓ Build complete! Executable: dist/ZambiaDigitalHygiene.exe"

# Running
run:
	$(PYTHON) windows_app.py

cli:
	$(PYTHON) cli.py --help

web:
	FLASK_APP=src/web/app.py FLASK_ENV=development $(PYTHON) -m flask run --reload

# Docker
docker-build:
	docker build -t zambia-digital-hygiene:latest .
	@echo "✓ Docker image built"

docker-up:
	docker-compose up -d
	@echo "✓ Containers started. Access at http://localhost:5000"
	@echo "  Database: mysql://localhost:3306"

docker-down:
	docker-compose down
	@echo "✓ Containers stopped"

docker-logs:
	docker-compose logs -f

docker-ps:
	docker-compose ps

# Database
db-init:
	$(PYTHON) database/setup_mysql.py
	@echo "✓ Database initialized"

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (y/n): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		$(PYTHON) database/setup_mysql.py --reset; \
		echo "✓ Database reset"; \
	else \
		echo "Cancelled"; \
	fi

# Documentation
docs-serve:
	@echo "Documentation files:"
	@echo "  - README.md - Main project documentation"
	@echo "  - CONTRIBUTING.md - Contribution guidelines"
	@echo "  - SECURITY.md - Security best practices"
	@echo "  - ARCHITECTURE.md - System architecture"
	@echo "  - BUILD.md - Build instructions"
	@echo "  - DEPLOYMENT.md - Deployment guide"
	@echo "  - CHANGELOG.md - Version history"

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	@echo "✓ Cleanup complete"

clean-all: clean
	rm -rf $(VENV)
	rm -rf .venv
	@echo "✓ All files cleaned including venv"

# Development Workflow
workflow: dev-install pre-commit-install
	@echo ""
	@echo "✓ Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Activate venv: source $(VENV)/bin/activate"
	@echo "  2. Start coding!"
	@echo "  3. Run: make quality   (before committing)"
	@echo "  4. Run: make test      (before pushing)"
	@echo ""

# Quick commands
q: quality
t: test
f: format
l: lint

# Print version
version:
	@$(PYTHON) --version
	@$(BLACK) --version
	@$(FLAKE8) --version
	@$(MYPY) --version

# Health check
health: type-check lint security
	@echo ""
	@echo "✓ Project health is good!"
