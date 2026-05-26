# Project Features Documentation

This document summarizes the implemented features in the `sakhile_final-_year_pro` project, what each feature does, and the current working scope.

## 1. Desktop Application

### `windows_app.py` and `src/gui/`

- Provides a Windows GUI for the digital hygiene assessment.
- Uses `customtkinter` UI screens to guide users through the workflow.
- Included screens:
  - `welcome.py`: startup splash and introduction.
  - `business_info.py`: capture business details for assessment reports.
  - `scanning.py`: live progress display for automated checks.
  - `manual_checks.py`: manual questionnaire / assessment inputs.
  - `results.py`: display certification results and export options.
- Status: **Implemented and working** for core desktop assessment flow.

## 2. CLI Interface

### `cli.py`

- Entry point for command-line actions.
- Supports running the web app, assessment automation, or deployment checks.
- Status: **Available**, with existing CLI scaffolding in place.

## 3. Security Assessment Engine

### `src/security/assessment/assessor.py`

- Implements the main digital hygiene assessment logic.
- Defines the assessment controls, scoring model, and assessment result objects.
- Produces structured assessment results for reporting and GUI display.
- Status: **Implemented and available**.

### `src/security/assessment/remote_collector.py`

- Provides a data ingestion helper for remote agent reports.
- Can load and summarize agent JSON results.
- Status: **Implemented as a helper module**.

## 4. Pre-Deployment Digital Hygiene Checker

### `src/security/deployment/checker.py`

- Runs a battery of host readiness checks before deployment.
- Checks included:
  - `PDC-01` OS Updates
  - `PDC-02` Firewall status
  - `PDC-03` Antivirus / Defender detection
  - `PDC-04` Disk encryption (BitLocker/LUKS)
  - `PDC-14` Software inventory summary
  - `PDC-15` Monitoring and log hygiene
  - `PDC-05` Risky open ports
  - `PDC-06` DNS resolution
  - `PDC-07` TLS/OpenSSL availability
  - `PDC-08` Python version
  - `PDC-09` Dependency vulnerability scan via `pip audit`
  - `PDC-10` Debug mode environment variable audit
  - `PDC-11` `.env` file exposure check
  - `PDC-12` Hard-coded secret detection in Python source
  - `PDC-13` Sensitive tracked git files detection
- Produces a `DeploymentReadiness` report with verdict, totals, and check details.
- Status: **Implemented and validated** via unit tests.

## 5. Monitoring & SIEM Integration

### `src/security/monitoring/checks.py`

- Performs host logging and monitoring hygiene inspection.
- On Windows, checks Windows Event Log availability and searches for log-forwarding agents.
- On Unix, checks for journal/syslog and local logging functionality.
- Status: **Implemented and integrated** into deployment readiness.

### `src/security/siem/forwarder.py`

- Contains a webhook forwarder for SIEM event delivery.
- Builds an aggregated event payload from the deployment report.
- Status: **Implemented as a forwarding helper**.

## 6. Remediation Guidance

### `src/security/remediation/guidance.py`

- Contains remediation guidance mapping for common checks.
- Provides actionable advice and PowerShell/snippet remediation text.
- Status: **Implemented as reference guidance**.

## 7. Reporting

### `src/reporting/generator.py`

- Handles generation of assessment reports.
- Supports multiple output formats, including HTML and JSON.
- Uses `src/reporting/templates/report.html` for HTML formatting.
- Status: **Implemented and available**.

## 8. Flask Web Portal

### `src/web/app.py`

- Implements a minimal Flask web portal.
- Includes landing page, about page, and verification page.
- Web templates available under `src/web/templates/`.
- Status: **Implemented in landing page form**; full dashboard features are scaffolded.

## 9. Database Integration

### `src/database/connection.py`

- Contains database connection logic and persistence scaffolding.
- Supports MySQL and SQLite integration for assessment storage.
- Status: **Implemented as a backend foundation**, used by web and data workflows.

## 10. Active Directory & AD Hygiene

### `src/security/active_directory/checks.py`

- Contains AD hygiene check scaffolding for future Active Directory security validations.
- Status: **Present as a dedicated module**; ready for expanded AD checks.

## 11. Test Coverage

### `tests/test_deployment.py`

- Covers `PreDeploymentChecker`, `CheckResult`, and `DeploymentReadiness` behavior.
- Includes unit tests for monitoring hygiene, environment checks, and debug-mode detection.
- Status: **Implemented and passing**.

## 12. Project Documentation & Setup

### Existing documentation files

- `README.md`: project overview, setup, and usage guidance.
- `ARCHITECTURE.md`: system architecture and component diagrams.
- `DEPLOYMENT.md`: deployment and maintenance notes.
- `ENVIRONMENT_SETUP.md`: environment setup instructions.
- `INSTALL_SCRIPTS.md`: install script details.
- `BUILD.md`: build instructions.

## Feature Status Summary

- Desktop GUI assessment flow: **Working**
- Pre-deployment readiness checks: **Working**
- Monitoring/logging hygiene checks: **Working**
- SIEM webhook forwarder: **Implemented**
- Reporting engine: **Available**
- Web portal landing pages: **Available**
- Database scaffolding: **Available**
- Active Directory hygiene module: **Scaffolded**
- Remediation guidance: **Available**
- CLI entry point: **Available**
- Unit tests for deployment checker: **Working**

---

## Notes

This document reflects the current repository implementation and working scope as present in the codebase.
For additional feature details, consult the individual source files under `src/` and the existing project markdown documentation.
