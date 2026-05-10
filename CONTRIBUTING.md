# Contributing to Zambia Digital Hygiene Certification Program

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a Code of Conduct. All contributors are expected to be respectful and professional.

---

## Getting Started

### Prerequisites

- Python 3.10 or later
- Git
- Basic understanding of the project structure (see [README.md](README.md))

### Setup Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/sakhile-bit/sakhile_final-_year_pro.git
   cd sakhile_final-_year_pro
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

4. **Install development tools**
   ```bash
   pip install flake8 black mypy pytest-cov
   ```

5. **Run tests to verify setup**
   ```bash
   pytest tests/ -v
   ```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b bugfix/issue-number-description
```

Use descriptive branch names:
- `feature/add-certificate-generation`
- `bugfix/fix-firewall-detection`
- `docs/update-api-documentation`

### 2. Make Your Changes

Follow these guidelines:

#### Code Style
- Use **PEP 8** formatting
- Max line length: 120 characters
- Use type hints for all functions
- Write docstrings for all classes and functions

```python
def calculate_score(controls: Dict[str, ControlResult]) -> int:
    """
    Calculate total assessment score from control results.
    
    Args:
        controls: Dictionary mapping control IDs to ControlResult objects
        
    Returns:
        Total score as integer
        
    Raises:
        ValueError: If controls dictionary is empty
    """
    if not controls:
        raise ValueError("Controls dictionary cannot be empty")
    return sum(c.points for c in controls.values())
```

#### Formatting
- Use `black` for automatic formatting:
  ```bash
  black src tests
  ```
- Use `flake8` for linting:
  ```bash
  flake8 src tests
  ```
- Use `mypy` for type checking:
  ```bash
  mypy src
  ```

### 3. Write Tests

All new features must include tests:

```python
import pytest
from src.security.assessment.assessor import DigitalHygieneAssessor, BusinessInfo

def test_new_control_calculation():
    """Test that new control is calculated correctly."""
    business = BusinessInfo(name="Test", id="TEST-001")
    assessor = DigitalHygieneAssessor(business_info=business)
    results = assessor.run_assessment()
    
    assert results.score >= 0
    assert results.total_possible == 120
```

Run tests before committing:
```bash
pytest tests/ -v --cov=src
```

### 4. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git commit -m "feat: add multi-language support for assessment report

- Add i18n framework using gettext
- Support English, Bemba, and Nyanja
- Update report generation to use locale

Fixes #42"
```

**Commit message format:**
```
<type>: <short description>

<detailed description>

Fixes #<issue_number>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, missing semicolons, etc.)
- `refactor:` - Code refactoring without feature change
- `perf:` - Performance improvements
- `test:` - Test additions or updates
- `chore:` - Build, dependencies, tooling

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title
- Description of changes
- Link to related issues
- Screenshots if applicable

---

## Areas for Contribution

### High-Priority

- [ ] Phase 2 Database Implementation
  - User authentication system
  - Assessment storage and retrieval
  - Certificate generation and verification

- [ ] Advanced Features
  - Email notifications
  - Scheduled assessments
  - Multi-language support

- [ ] Testing
  - Performance tests
  - Security tests
  - Integration tests

### Medium-Priority

- [ ] Documentation
  - API documentation
  - Architecture diagrams
  - Video tutorials

- [ ] UI/UX Improvements
  - Accessibility enhancements
  - Mobile responsiveness
  - Dark/light mode toggle

- [ ] DevOps
  - Kubernetes deployment
  - Monitoring setup
  - Auto-scaling

---

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_assessor.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_assessor.py::TestDigitalHygieneAssessor::test_assessment -v
```

### Test Organization

```python
# tests/test_my_feature.py

import pytest
from unittest.mock import patch, MagicMock

class TestMyFeature:
    """Tests for my new feature."""
    
    @pytest.fixture
    def setup(self):
        """Setup test data."""
        # Setup code here
        yield  # Tests run here
        # Teardown code here
    
    def test_happy_path(self, setup):
        """Test successful scenario."""
        assert True
    
    def test_error_handling(self, setup):
        """Test error scenario."""
        with pytest.raises(ValueError):
            # Code that should raise ValueError
            pass
```

---

## Documentation Standards

### Docstrings

Use Google-style docstrings:

```python
def assess_system(business_info: BusinessInfo, verbose: bool = False) -> AssessmentResults:
    """
    Run comprehensive cybersecurity assessment on system.
    
    Performs automated checks for all 15 security controls and generates
    certification level (Gold/Silver/Bronze) based on score.
    
    Args:
        business_info: Business information for the assessment
        verbose: Whether to print detailed progress (default: False)
        
    Returns:
        AssessmentResults object containing score, level, and recommendations
        
    Raises:
        PermissionError: If admin privileges required for checks are missing
        TimeoutError: If assessment takes longer than 5 minutes
        
    Example:
        >>> business = BusinessInfo(name="Acme Inc", id="AM-001")
        >>> results = assess_system(business, verbose=True)
        >>> print(f"Certification: {results.certification_level}")
    """
```

### Comments

- Write comments for complex logic
- Avoid obvious comments
- Keep comments up-to-date with code changes

```python
# Calculate weighted score considering critical failures
# Each critical failure reduces score by 20 points
score = total_points - (critical_failures * 20)
```

---

## Security Guidelines

### Security Considerations

1. **Input Validation**
   - Validate all user inputs
   - Sanitize file paths
   - Validate business registration IDs

2. **Logging**
   - Don't log sensitive information (passwords, tokens)
   - Use appropriate log levels

3. **Dependencies**
   - Keep dependencies updated
   - Review security advisories

```python
# Good: Validate input
def create_business(name: str, reg_id: str) -> BusinessInfo:
    if not name or len(name) > 255:
        raise ValueError("Business name invalid")
    if not reg_id or not reg_id.isalnum():
        raise ValueError("Registration ID must be alphanumeric")
    return BusinessInfo(name=name, id=reg_id)

# Bad: No validation
def create_business(name, reg_id):
    return BusinessInfo(name=name, id=reg_id)
```

---

## Performance Considerations

### Optimization Tips

1. **Database Queries** (Phase 2)
   - Use indexes for frequently queried fields
   - Batch operations when possible
   - Avoid N+1 queries

2. **Assessment Speed**
   - Target < 30 seconds for full assessment
   - Cache system information
   - Run checks in parallel when safe

3. **Memory Usage**
   - Stream large files instead of loading into memory
   - Clean up large objects after use

---

## Troubleshooting Development Issues

### Common Issues

**Issue: Tests failing locally but passing on CI**
- Ensure you're using the same Python version
- Clear pytest cache: `pytest --cache-clear`
- Check for environment-specific issues

**Issue: Import errors**
- Verify virtual environment is activated
- Reinstall package: `pip install -e .`
- Check PYTHONPATH

**Issue: Module not found**
- Add project root to PYTHONPATH
- Use relative imports correctly

---

## Release Process

### Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** (v1.0.0): Breaking changes
- **MINOR** (v1.1.0): New features (backward compatible)
- **PATCH** (v1.0.1): Bug fixes (backward compatible)

### Creating a Release

1. Update version in relevant files
2. Update [CHANGELOG.md](CHANGELOG.md)
3. Create a git tag: `git tag -a v1.2.0 -m "Release version 1.2.0"`
4. Push tag: `git push origin v1.2.0`
5. GitHub Actions will automatically build and release

---

## Getting Help

- **Questions**: Create a GitHub Discussion
- **Bugs**: Create an Issue with reproduction steps
- **Security**: See [SECURITY.md](SECURITY.md)
- **General**: Check [README.md](README.md) and documentation

---

## Code Review Process

1. **Automated Checks**: CI/CD pipeline must pass
2. **Code Review**: At least one maintainer review
3. **Testing**: Coverage must not decrease
4. **Documentation**: Update relevant docs

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Zambia Digital Hygiene Certification Program! 🎉
