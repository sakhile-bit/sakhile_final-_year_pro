# Changelog

All notable changes to the Zambia Digital Hygiene Certification Program will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — Certificate Signing & Verification (anti-forgery)
- **Ed25519-signed certificates** — every certificate is signed over its material
  facts; altering any field invalidates the signature (tamper detection).
- **Central registry + issuance API** — passing assessments are registered and
  signed server-side; the desktop app registers via `POST /api/certificates/issue`
  (the signing key never ships in the `.exe`), staying *provisional* when offline.
- **Online verification** — hardened `/verify/<number>` and `/api/verify/<number>`
  with VALID / EXPIRED / REVOKED / SUPERSEDED / INVALID / NOT FOUND status,
  48-bit unguessable numbers, per-IP rate limiting, and audit logging.
- **QR codes & printable certificate** — `/certificate/<number>` plus QR + signed
  block embedded in desktop PDF/HTML reports.
- **Offline verifier** — self-contained `/verify-offline` page verifies a
  certificate's signed block client-side against the published public key, no
  connectivity required (browser JS cross-validated against the Python signer).
- **Key rotation** — `key_id`-tagged signatures, retired keys retained for
  verification (`ZDH_PUBLIC_KEYS`), `/verify/pubkey` publishes all keys, plus a
  `scripts/rotate_signing_key.py` helper.
- **Revocation reasons & re-issue supersede** — admin revocation records a reason;
  re-assessment marks the prior certificate SUPERSEDED. Reasons surfaced on all
  verification surfaces.
- Docs: [`docs/features/22-certificate-verification.md`](docs/features/22-certificate-verification.md).

### Security
- **Issuance auth fails closed** — the certificate issuance API no longer falls
  back to the source-published dev key in production; if `ZDH_ISSUE_API_KEY` is
  unset (and not in debug/test), issuance is refused rather than left open.
- **Rate-limit spoofing fixed** — `X-Forwarded-For` is trusted only when
  `TRUST_PROXY=1`; otherwise the socket peer is used, so the header can't be
  rotated to bypass the per-IP enumeration cap.
- **Rate-limiter memory bounded** — stale per-IP buckets are pruned (cap 20k),
  preventing unbounded growth under a spoofed-IP flood.

### Planned for Phase 2
- Web dashboard with user authentication
- Assessment history and management
- Certificate database and verification system
- Email notifications
- Scheduled assessments
- Multi-language support (Bemba, Nyanja)
- Advanced analytics and reporting
- API documentation with Swagger/OpenAPI
- Mobile app (iOS/Android)

---

## [1.0.0] - 2026-05-10

### Added - Phase 1 Release

#### Desktop Application
- Windows GUI wizard with customtkinter framework
- 5-screen assessment flow (Welcome → Business Info → Scanning → Manual Questions → Results)
- Real-time progress tracking for automated checks
- JSON and HTML report export
- Professional dark-themed UI (#0D1B2A / #00C896 color scheme)

#### Assessment Engine
- 15-control cybersecurity framework (5 automated + 10 manual)
- Automated checks for:
  - C01: Operating System Updates
  - C02: Antivirus Protection
  - C03: Firewall Configuration
  - C04: Password Policy
  - C05: Backup Systems
- Manual assessment for administrative controls (C06-C15)
- 120-point scoring system
- Three certification tiers:
  - Gold (≥80% score, 0 critical failures)
  - Silver (≥60% score, ≤1 critical failure)
  - Bronze (≥40% score, ≤2 critical failures)
- Framework alignment:
  - NIST Cybersecurity Framework v1.1
  - CIS Critical Security Controls v8 (IG1)
  - ISO/IEC 27001:2022 Annex A
  - UK Cyber Essentials

#### Reporting System
- Multi-format reports (JSON, CSV, HTML)
- PDF generation framework (ready for implementation)
- Executive summaries with certification levels
- Control-by-control breakdowns
- Framework references and compliance guidance
- Actionable recommendations

#### Command-Line Interface
- `assess` - Run full 15-control assessment
- `scan` - Quick system scan
- `manual` - Generate printable assessment guide
- `predeploy` - Pre-deployment readiness checks
- `zambia` - Zambia-specific risk assessment
- `web` - Start Flask development server
- `users` - User management commands
- `init-db` - Database schema initialization
- `status` - System status report

#### Web Landing Page
- Marketing homepage with feature showcase
- "How it works" walkthrough
- 15 controls breakdown
- Certification tiers explanation
- Download button for Windows .exe
- About page with program details
- Certificate verification endpoint (Phase 2 ready)

#### Deployment Infrastructure
- Docker containerization
- Docker Compose with web app + MySQL services
- Production-ready Dockerfile
- MySQL 8.0 database schema
- Gunicorn WSGI server configuration
- Nginx reverse proxy documentation
- Let's Encrypt SSL setup guide
- Health checks and monitoring setup

#### Testing Suite
- 42 comprehensive tests (100% passing)
- Unit tests for assessment engine
- Deployment readiness tests (13 checks)
- Web application tests
- CLI interface tests
- Code coverage reporting

#### Build & Distribution
- PyInstaller specification for Windows .exe
- Single-file executable with all dependencies bundled
- Windows build script (`build.bat`)
- GitHub Actions CI/CD pipeline (added in improvements)
- GitHub Releases integration

#### Documentation
- [README.md](README.md) - Complete project overview
- [BUILD.md](BUILD.md) - Windows exe building instructions
- [DEPLOYMENT.md](DEPLOYMENT.md) - Docker and production setup
- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) - Ubuntu/Linux development
- [PROJECT_PROPOSAL.md](PROJECT_PROPOSAL.md) - Technical specifications
- [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) - QA verification template
- [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md) - Phase 1 achievements
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributor guidelines (added in improvements)
- [SECURITY.md](SECURITY.md) - Security best practices (added in improvements)

#### Configuration
- `.env.example` - Complete environment variables template
- `docker-compose.yml` - Multi-container orchestration
- `pytest.ini` - Test runner configuration
- `Dockerfile` - Container image definition
- `devops/build.spec` - PyInstaller configuration
- `devops/build.bat` - Windows build script

### Architecture
- Modular codebase with clear separation of concerns
- `src/gui/` - Desktop GUI with 5 screens
- `src/security/assessment/` - Core assessment engine
- `src/security/deployment/` - Deployment readiness checks
- `src/reporting/` - Multi-format report generation
- `src/web/` - Flask landing page
- `src/utils/` - CLI, config, logging utilities
- `tests/` - Comprehensive test suite

### Technical Stack
- **Desktop**: customtkinter 5.2.0+, PyInstaller 6.0.0+
- **Web**: Flask 2.3.0+, Bootstrap 5.3.0+
- **Database**: MySQL 8.0+ (with SQLite dev fallback)
- **Testing**: pytest 7.4.0+, pytest-cov
- **System**: psutil 5.9.0+, click 8.1.0+, PyYAML 6.0+
- **Core**: Python 3.10+

### Bug Fixes
- None (initial release)

### Security
- Input validation on all user inputs
- Secure password handling framework (Phase 2 ready)
- Pre-deployment security checks
- Logging best practices (no sensitive data)

### Performance
- Assessment completes in <30 seconds (target met)
- Report generation <5 seconds
- Memory-efficient system scanning
- Database connection pooling ready

---

## Release Notes

### v1.0.0 Highlights

✨ **Production-Ready Phase 1**

The Zambia Digital Hygiene Certification Program Phase 1 is complete with:
- Fully functional Windows desktop application
- 15-control cybersecurity assessment framework
- Professional GUI with wizard-based flow
- Multi-format reporting system
- Comprehensive CLI for automation
- Production-ready Docker deployment
- Complete test suite (42 tests)
- Professional documentation

**Installation & Usage:**
1. Download `ZambiaDigitalHygiene.exe` from releases
2. Double-click to run (no installation needed)
3. Complete the assessment wizard
4. Export certification reports in JSON or HTML

**For Developers:**
- Full source code on GitHub
- Contributing guidelines in [CONTRIBUTING.md](CONTRIBUTING.md)
- Security best practices in [SECURITY.md](SECURITY.md)
- Architecture documentation in [README.md](README.md)

**Next Steps (Phase 2):**
- Web dashboard with full CRUD operations
- User authentication and authorization
- Certificate management system
- Advanced analytics
- Multi-language support

---

## Version History

### Upcoming
- v1.1.0 - Enhancement release with quality improvements
- v2.0.0 - Phase 2: Full web dashboard

### Current
- v1.0.0 - Phase 1 release (2026-05-10)

---

## Migration Guide

### From Pre-Release to v1.0.0

If you were using pre-release versions:

1. **Backup Assessment Results**
   ```bash
   # Export all reports
   copy reports\*.* backup_reports\
   ```

2. **Update Installation**
   - Download new `ZambiaDigitalHygiene.exe`
   - Old version can be uninstalled (just delete .exe)

3. **Database Changes**
   - SQLite dev database incompatible; recreate for Phase 2
   - Run: `python cli.py init-db` if using web

4. **Configuration**
   - Check `.env` file for any removed variables
   - Use `.env.example` as reference

---

## Known Issues

### v1.0.0

- **Windows 7 Compatibility**: Automated firewall check may fail on Windows 7 (no impact on final score for unsupported OS)
- **Antivirus Detection**: Some AV vendors may not be detected (assessment continues with partial score)
- **High DPI Displays**: GUI scaling may need adjustment on 4K displays (workaround in advanced settings)

### Workarounds

```python
# For high DPI displays, set environment variable before running:
set QT_QPA_PLATFORM_PLUGIN_PATH=
# Then run the application
```

---

## Support

- **Bug Reports**: [GitHub Issues](https://github.com/sakhile-bit/sakhile_final-_year_pro/issues)
- **Security**: See [SECURITY.md](SECURITY.md)
- **Questions**: [GitHub Discussions](https://github.com/sakhile-bit/sakhile_final-_year_pro/discussions)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Code style and standards
- Testing requirements
- Commit message format
- Pull request process

---

## License

All changes are released under the [MIT License](LICENSE).

---

## Acknowledgments

- **NIST Cybersecurity Framework**
- **CIS Critical Security Controls**
- **ISO/IEC 27001:2022**
- **UK Cyber Essentials Scheme**
- **Open Source Community**

---

**Last Updated**: 2026-05-10
**Maintainer**: University of Zambia, Dept. of Computing & Informatics

[Unreleased]: https://github.com/sakhile-bit/sakhile_final-_year_pro/compare/v1.0.0...main
[1.0.0]: https://github.com/sakhile-bit/sakhile_final-_year_pro/releases/tag/v1.0.0
