"""
Command-line interface for the Zambia Digital Hygiene Assessment Tool.

Provides developer-friendly terminal commands for running assessments,
system scans, pre-deployment checks, the web server, and user management
— all without needing the web UI.

Usage (from project root):
    python cli.py --help
    python cli.py assess --business-name "Acme" --business-id REG-001
    python cli.py scan
    python cli.py zambia
    python cli.py predeploy
    python cli.py web --debug
    python cli.py users list
    python cli.py users create --username dev1 --password secret
    python cli.py init-db
    python cli.py manual
    python cli.py status
"""

import click
import json as _json
import os
import platform
import socket
import ssl
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so ``src.*`` imports work regardless
# of how this module is invoked.
# ---------------------------------------------------------------------------
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.security.assessment.assessor import DigitalHygieneAssessor, BusinessInfo, ZambiaRiskAssessor  # noqa: E402
from src.reporting.generator import ReportGenerator  # noqa: E402
from src.utils.logging_config import get_logger  # noqa: E402
from src.utils.config import config  # noqa: E402

console = Console()
logger = get_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Root CLI group
# ──────────────────────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0")
@click.option('--config', 'config_file', type=click.Path(exists=True),
              help='Path to YAML configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose / DEBUG output')
def cli(config_file: Optional[str], verbose: bool):
    """Zambia Digital Hygiene Assessment Tool  –  Developer CLI

    A comprehensive cybersecurity assessment toolkit for SMEs in Zambia.
    Run any command with --help for details.
    """
    if config_file:
        config.load_from_file(config_file)

    if verbose:
        import logging
        logging.getLogger("zambia_digital_hygiene").setLevel(logging.DEBUG)


# ──────────────────────────────────────────────────────────────────────────────
# assess – full 15-control digital-hygiene assessment
# ──────────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option('--business-name', prompt='Business name', help='Name of the business')
@click.option('--business-id', prompt='Business ID', help='Business registration ID')
@click.option('--output-dir', '-o', default='reports',
              help='Output directory for reports')
@click.option('--format', '-f', 'formats', multiple=True,
              type=click.Choice(['json', 'csv', 'html', 'pdf']),
              default=['json'], help='Report formats to generate (repeatable)')
@click.option('--save-db', is_flag=True, help='Save assessment to database')
def assess(business_name: str, business_id: str, output_dir: str,
           formats: tuple, save_db: bool):
    """Run the full automated cybersecurity assessment (15 controls)."""

    console.print(Panel.fit(
        "[bold blue]Zambia Digital Hygiene Assessment Tool[/bold blue]\n"
        "[dim]Automated cybersecurity assessment for SMEs[/dim]",
        title="🚀 Starting Assessment"
    ))

    try:
        business_info = BusinessInfo(name=business_name, id=business_id)
        assessor = DigitalHygieneAssessor(business_info)

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running assessment…", total=None)
            results = assessor.run_assessment()
            progress.update(task, completed=True)

        _display_results(results)

        # Generate reports
        if formats:
            generator = ReportGenerator(output_dir)

            with Progress(
                SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Generating reports…", total=len(formats))
                report_name = f"assessment_{business_id}"

                for fmt in formats:
                    if fmt == 'json':
                        data = generator.generate_json_report(results, business_info)
                        json_path = Path(output_dir) / f"{report_name}.json"
                        json_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(json_path, 'w') as jf:
                            _json.dump(data, jf, indent=2)
                        console.print(f"  📄 JSON report: {json_path}")
                    elif fmt == 'csv':
                        rows = generator.generate_csv_report(results, business_info)
                        csv_path = Path(output_dir) / f"{report_name}.csv"
                        csv_path.parent.mkdir(parents=True, exist_ok=True)
                        import csv as _csv
                        with open(csv_path, 'w', newline='') as cf:
                            _csv.writer(cf).writerows(rows)
                        console.print(f"  📄 CSV report: {csv_path}")
                    elif fmt == 'html':
                        path = generator.generate_html_report(results, business_info, report_name)
                        console.print(f"  📄 HTML report: {path}")
                    elif fmt == 'pdf':
                        path = generator.generate_pdf_report(results, business_info, report_name)
                        console.print(f"  📄 PDF report: {path}")

                    progress.update(task, advance=1)

        # Save to database
        if save_db:
            from src.web.app import create_app, db as flask_db, Business, Assessment
            flask_app = create_app()
            with flask_app.app_context():
                business = Business.query.filter_by(registration_number=business_info.id).first()
                if not business:
                    business = Business(
                        name=business_info.name,
                        registration_number=business_info.id,
                        contact_person=business_info.contact_person,
                        contact_email=business_info.contact_email,
                        contact_phone=business_info.contact_phone,
                        industry=business_info.industry,
                        address=business_info.address,
                    )
                    flask_db.session.add(business)
                    flask_db.session.flush()
                controls_data = {
                    cid: {"name": c.name, "score": c.score, "weight": c.weight,
                          "status": c.status, "details": c.details}
                    for cid, c in results.controls.items()
                }
                record = Assessment(
                    business_id=business.id,
                    assessment_date=results.assessment_date,
                    controls_results=controls_data,
                    total_score=results.score,
                    certification_level=results.certification_level,
                    recommendations=results.recommendations,
                    status='completed',
                )
                flask_db.session.add(record)
                flask_db.session.commit()
            console.print("✅ Assessment saved to database")

        console.print("\n[green]✓ Assessment completed successfully![/green]")

    except Exception as e:
        logger.error(f"Assessment failed: {e}")
        console.print(f"[red]✗ Assessment failed: {e}[/red]")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# scan – quick system security scan (mirrors the /system-scan web route)
# ──────────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option('--domain', '-d', default='localhost',
              help='Domain for SSL/TLS check')
@click.option('--backup-path', '-b', default='/backups',
              help='Path to check for backup files')
@click.option('--json-out', '-j', is_flag=True,
              help='Output raw JSON instead of formatted table')
def scan(domain: str, backup_path: str, json_out: bool):
    """Run a quick system security scan.

    Checks OS info, open ports, firewall, antivirus, disk encryption,
    outdated packages, suspicious processes, SSL/TLS, patches, and more.
    """

    console.print(Panel.fit(
        "[bold blue]System Security Scan[/bold blue]\n"
        "[dim]Checking local system hygiene…[/dim]",
        title="🔍 System Scan"
    ))

    results = {}
    recommendations = []

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running system checks…", total=12)

        # 1 – OS information
        results['os'] = f"{platform.system()} {platform.release()}"
        results['hostname'] = socket.gethostname()
        progress.update(task, advance=1)

        # 2 – Open ports
        common_ports = [22, 80, 443, 3306, 5432, 8080, 8443]
        open_ports = []
        for port in common_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    if s.connect_ex(('127.0.0.1', port)) == 0:
                        open_ports.append(port)
            except Exception:
                pass
        results['open_ports'] = open_ports
        progress.update(task, advance=1)

        # 3 – Firewall
        results['firewall'] = _check_firewall()
        progress.update(task, advance=1)

        # 4 – Antivirus
        results['antivirus'] = _check_antivirus()
        progress.update(task, advance=1)

        # 5 – Disk encryption
        results['disk_encryption'] = _check_disk_encryption()
        progress.update(task, advance=1)

        # 6 – Outdated packages
        results['outdated_packages'] = _check_outdated_packages()
        progress.update(task, advance=1)

        # 7 – Suspicious processes
        results['suspicious_processes'] = _check_suspicious_processes()
        progress.update(task, advance=1)

        # 8 – SSL / TLS
        results['ssl_tls'] = _check_ssl_tls(domain)
        progress.update(task, advance=1)

        # 9 – Backup status
        results['backup'] = _check_backup_status(backup_path)
        progress.update(task, advance=1)

        # 10 – Patch status
        results['patch_status'] = _check_patch_status()
        progress.update(task, advance=1)

        # 11 – External IP
        results['external_ip'] = _get_external_ip()
        progress.update(task, advance=1)

        # 12 – Admin accounts (skipped in CLI-only mode)
        results['admin_accounts'] = 'N/A (run from web for DB query)'
        progress.update(task, advance=1)

    # Build recommendations
    if open_ports:
        recommendations.append(f"Open ports detected: {open_ports}. Restrict unused ports.")
    else:
        recommendations.append("No common open ports detected. Good!")
    if 'not' in results.get('firewall', '').lower() or 'unknown' in results.get('firewall', '').lower():
        recommendations.append("Enable and configure your firewall.")
    if 'not' in results.get('antivirus', '').lower() or 'error' in results.get('antivirus', '').lower():
        recommendations.append("Ensure real-time antivirus is active.")
    if 'not' in results.get('disk_encryption', '').lower():
        recommendations.append("Enable full-disk encryption (BitLocker / LUKS).")
    if results.get('outdated_packages'):
        recommendations.append("Update outdated Python packages.")
    if results.get('suspicious_processes'):
        recommendations.append("Investigate flagged suspicious processes.")
    recommendations.append("Ensure your OS and all software are up to date.")

    results['recommendations'] = recommendations

    if json_out:
        console.print_json(_json.dumps(results, indent=2, default=str))
    else:
        _display_scan_table(results, recommendations)

    console.print("\n[green]✓ System scan completed![/green]")


# ──────────────────────────────────────────────────────────────────────────────
# zambia – Zambia-specific risk assessment (interactive)
# ──────────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option('--json-out', '-j', is_flag=True,
              help='Output raw JSON instead of formatted table')
def zambia(json_out: bool):
    """Run the Zambia-specific digital hygiene risk assessment.

    Interactively asks about local threats (SIM swap fraud, mobile money,
    WhatsApp fraud, etc.) and compliance with Zambian cyber laws.
    """
    console.print(Panel.fit(
        "[bold blue]Zambia Risk Assessment[/bold blue]\n"
        "[dim]Local threat vectors & compliance checks[/dim]",
        title="🇿🇲 Zambia Assessment"
    ))

    assessor = ZambiaRiskAssessor()
    answers = {}

    console.print("\n[bold]Answer each question with [green]y[/green] (yes) or [red]n[/red] (no).[/bold]\n")

    # Ask about each local threat mitigation
    console.print("[bold cyan]── Local Threat Mitigations ──[/bold cyan]")
    for threat in assessor.LOCAL_THREATS:
        key = threat.replace(' ', '_').lower()
        response = click.confirm(f"  Is mitigation in place for: {threat}?", default=False)
        answers[key] = response

    # Ask about compliance with laws
    console.print("\n[bold cyan]── Regulatory Compliance ──[/bold cyan]")
    for law in assessor.COMPLIANCE_LAWS:
        key = law.replace(' ', '_').replace(',', '').lower()
        response = click.confirm(f"  Compliant with: {law}?", default=False)
        answers[key] = response

    # Run assessment
    result = assessor.assess(answers)

    if json_out:
        console.print_json(_json.dumps(result, indent=2, default=str))
    else:
        _display_zambia_results(result)


# ──────────────────────────────────────────────────────────────────────────────
# predeploy – pre-deployment hygiene gate
# ──────────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option('--project-root', '-p', default='.', help='Project root directory to scan')
@click.option('--json-out', '-j', is_flag=True, help='Output raw JSON instead of formatted table')
def predeploy(project_root: str, json_out: bool):
    """Run pre-deployment digital hygiene checks.

    Scans the system for security issues before deployment: OS patches,
    firewall, antivirus, open ports, dependency vulnerabilities, debug
    flags, and credential hygiene.

    Exit code 0 = READY · exit code 1 = NOT READY (use in CI/CD).
    """
    from src.security.deployment.checker import PreDeploymentChecker

    console.print(Panel.fit(
        "[bold blue]Pre-Deployment Digital Hygiene Check[/bold blue]\n"
        "[dim]Verifying system is safe to deploy from[/dim]",
        title="🚀 Pre-Deploy Gate"
    ))

    checker = PreDeploymentChecker(project_root=project_root)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running hygiene checks…", total=None)
        report = checker.run_all()
        progress.update(task, completed=True)

    if json_out:
        console.print_json(_json.dumps(report.to_dict(), indent=2))
    else:
        table = Table(title="Pre-Deployment Checks")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Check", style="white")
        table.add_column("Severity", style="magenta")
        table.add_column("Result", min_width=8)
        table.add_column("Details", style="dim")

        for c in report.checks:
            result_style = "green" if c.passed else "red"
            result_text = "✅ PASS" if c.passed else "❌ FAIL"
            sev_style = {"CRITICAL": "bold red", "HIGH": "yellow",
                         "MEDIUM": "cyan", "LOW": "dim"}.get(c.severity, "")
            table.add_row(
                c.check_id, c.name,
                Text(c.severity, style=sev_style),
                Text(result_text, style=result_style),
                c.details,
            )

        console.print(table)

        failures = [c for c in report.checks if not c.passed and c.remediation]
        if failures:
            rem_lines = "\n".join(f"• [bold]{c.check_id}[/bold]: {c.remediation}" for c in failures)
            console.print(Panel.fit(rem_lines, title="🔧 Remediation Steps"))

        if report.verdict == 'READY':
            console.print(Panel.fit(
                f"[bold green]VERDICT: READY[/bold green]\n"
                f"Passed {report.passed}/{report.total} checks – safe to deploy.",
                title="✅ Deploy Gate"
            ))
        else:
            console.print(Panel.fit(
                f"[bold red]VERDICT: NOT READY[/bold red]\n"
                f"Failed {report.failed}/{report.total} checks "
                f"({report.critical_failures} critical). Fix issues above.",
                title="🚫 Deploy Gate"
            ))
            sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# web – start the Flask web dashboard
# ──────────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option('--host', default='127.0.0.1', help='Server host')
@click.option('--port', default=5000, type=int, help='Server port')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def web(host: str, port: int, debug: bool):
    """Start the web dashboard (Flask dev server)."""
    from src.web.app import create_app

    try:
        app = create_app()
        console.print(Panel.fit(
            f"[bold green]Web dashboard starting…[/bold green]\n"
            f"[dim]http://{host}:{port}[/dim]",
            title="🌐 Web Server"
        ))
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        console.print(f"[red]✗ Failed to start web server: {e}[/red]")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# init-db – create / migrate the database schema
# ──────────────────────────────────────────────────────────────────────────────

@cli.command('init-db')
def init_db():
    """Initialize the database (create tables, default admin user)."""
    from src.web.app import create_app

    try:
        app = create_app()
        with app.app_context():
            from src.web.app import db, User as WebUser
            db.create_all()
            # Create default admin if none exists
            admin = WebUser.query.filter_by(role='admin').first()
            if not admin:
                admin = WebUser(username='admin', email='admin@zambia-hygiene.local', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                console.print("  👤 Default admin created (admin / admin123)")
            else:
                console.print("  👤 Admin account already exists")
        console.print("[green]✅ Database initialized successfully[/green]")
    except Exception as e:
        console.print(f"[red]✗ Database initialization failed: {e}[/red]")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# users – developer user management
# ──────────────────────────────────────────────────────────────────────────────

@cli.group()
def users():
    """Manage application users (list, create, reset password)."""
    pass


@users.command('list')
def users_list():
    """List all users in the database."""
    from src.web.app import create_app, User as WebUser

    app = create_app()
    with app.app_context():
        all_users = WebUser.query.order_by(WebUser.id).all()
        if not all_users:
            console.print("[yellow]No users found. Run 'init-db' first.[/yellow]")
            return

        table = Table(title="Application Users")
        table.add_column("ID", style="cyan")
        table.add_column("Username", style="white")
        table.add_column("Email", style="dim")
        table.add_column("Role", style="magenta")
        table.add_column("Active", style="green")
        table.add_column("MFA", style="yellow")
        table.add_column("Created", style="dim")

        for u in all_users:
            mfa = "✅" if getattr(u, 'mfa_enabled', False) else "—"
            active = "✅" if u.is_active else "❌"
            created = u.created_at.strftime('%Y-%m-%d %H:%M') if u.created_at else '—'
            table.add_row(
                str(u.id), u.username, u.email or '—',
                u.role, active, mfa, created
            )

        console.print(table)


@users.command('create')
@click.option('--username', prompt='Username', help='Username')
@click.option('--email', prompt='Email', help='Email address')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True,
              help='Password')
@click.option('--role', type=click.Choice(['admin', 'assessor', 'business_owner']),
              default='assessor', help='User role')
def users_create(username: str, email: str, password: str, role: str):
    """Create a new user account."""
    from src.web.app import create_app, db, User as WebUser

    app = create_app()
    with app.app_context():
        if WebUser.query.filter_by(username=username).first():
            console.print(f"[red]✗ Username '{username}' already exists[/red]")
            sys.exit(1)
        if WebUser.query.filter_by(email=email).first():
            console.print(f"[red]✗ Email '{email}' already in use[/red]")
            sys.exit(1)

        user = WebUser(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        console.print(f"[green]✅ User '{username}' created (role={role})[/green]")


@users.command('reset-password')
@click.option('--username', prompt='Username', help='Username to reset')
@click.option('--password', prompt='New password', hide_input=True,
              confirmation_prompt=True, help='New password')
def users_reset_password(username: str, password: str):
    """Reset a user's password."""
    from src.web.app import create_app, db, User as WebUser

    app = create_app()
    with app.app_context():
        user = WebUser.query.filter_by(username=username).first()
        if not user:
            console.print(f"[red]✗ User '{username}' not found[/red]")
            sys.exit(1)

        user.set_password(password)
        db.session.commit()
        console.print(f"[green]✅ Password reset for '{username}'[/green]")


# ──────────────────────────────────────────────────────────────────────────────
# manual – generate the on-site assessment guide
# ──────────────────────────────────────────────────────────────────────────────

@cli.command()
def manual():
    """Generate the manual (on-site) assessment guide."""
    try:
        # The file lives at the project root
        guide_path = Path(_project_root) / 'manual_assessment_guide.py'
        if not guide_path.exists():
            console.print("[red]✗ manual_assessment_guide.py not found in project root[/red]")
            sys.exit(1)

        # Import dynamically from the project root
        import importlib.util
        spec = importlib.util.spec_from_file_location("manual_assessment_guide", str(guide_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load spec for {guide_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]

        filename = mod.generate_manual_checklist()
        console.print(f"[green]✅ Manual assessment guide generated: {filename}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to generate manual guide: {e}[/red]")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# status – quick project / environment status summary
# ──────────────────────────────────────────────────────────────────────────────

@cli.command()
def status():
    """Show project and environment status summary."""
    console.print(Panel.fit(
        "[bold blue]Project Status[/bold blue]",
        title="📋 Status"
    ))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="cyan bold")
    table.add_column("Value", style="white")

    table.add_row("Python", f"{platform.python_version()} ({sys.executable})")
    table.add_row("OS", f"{platform.system()} {platform.release()}")
    table.add_row("Project Root", _project_root)
    table.add_row("Working Dir", os.getcwd())

    # Check database
    db_path = Path(_project_root) / 'instance' / 'digital_hygiene.db'
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        table.add_row("Database", f"SQLite ({size_mb:.2f} MB)")
    else:
        table.add_row("Database", "[yellow]Not initialized (run init-db)[/yellow]")

    # Check key dependencies
    deps = ['flask', 'click', 'rich', 'flask_sqlalchemy', 'flask_login', 'flask_wtf']
    missing = []
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)

    if missing:
        table.add_row("Dependencies", f"[red]Missing: {', '.join(missing)}[/red]")
    else:
        table.add_row("Dependencies", "[green]All core packages installed[/green]")

    # Check .env file
    env_path = Path(_project_root) / '.env'
    table.add_row(".env File", "Found" if env_path.exists() else "[yellow]Not found[/yellow]")

    console.print(table)

    # Show available commands
    console.print("\n[bold cyan]Available Commands:[/bold cyan]")
    cmds = [
        ("assess",    "Run full 15-control assessment"),
        ("scan",      "Quick system security scan"),
        ("zambia",    "Zambia-specific risk assessment"),
        ("predeploy", "Pre-deployment hygiene gate"),
        ("web",       "Start web dashboard"),
        ("init-db",   "Initialize database"),
        ("users",     "Manage users (list, create, reset-password)"),
        ("manual",    "Generate on-site assessment guide"),
        ("status",    "This status summary"),
    ]
    for name, desc in cmds:
        console.print(f"  [green]{name:12s}[/green] {desc}")


# ──────────────────────────────────────────────────────────────────────────────
# Helper: system scan checks (self-contained, no Flask dependency)
# ──────────────────────────────────────────────────────────────────────────────

def _check_firewall() -> str:
    try:
        if platform.system() == 'Windows':
            r = subprocess.run(
                'netsh advfirewall show allprofiles state',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0 and 'ON' in r.stdout.upper():
                return 'Enabled'
            return 'Disabled / Unknown'
        elif platform.system() == 'Linux':
            r = subprocess.run('ufw status', shell=True, capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and 'active' in r.stdout.lower():
                return 'UFW active'
            return 'UFW inactive / not installed'
        return 'Check manually for your OS'
    except Exception as e:
        return f'Check error: {e}'


def _check_antivirus() -> str:
    try:
        if platform.system() == 'Windows':
            r = subprocess.run(
                'powershell -Command "Get-MpComputerStatus | Select-Object -ExpandProperty AntivirusEnabled"',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0 and 'True' in r.stdout:
                return 'Windows Defender enabled'
            return 'Antivirus may not be active'
        elif platform.system() == 'Linux':
            for av in ['clamav', 'clamd']:
                r = subprocess.run(['which', av], capture_output=True, text=True)
                if r.returncode == 0:
                    return f'{av} detected'
            return 'No known antivirus detected'
        return 'Check manually for your OS'
    except Exception as e:
        return f'Check error: {e}'


def _check_disk_encryption() -> str:
    try:
        if platform.system() == 'Windows':
            r = subprocess.run('manage-bde -status C:', shell=True,
                               capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and 'Fully Encrypted' in r.stdout:
                return 'BitLocker enabled on C:'
            elif r.returncode == 0:
                return 'BitLocker not fully enabled'
            return 'Unable to determine BitLocker status'
        elif platform.system() == 'Linux':
            r = subprocess.run('lsblk -o NAME,TYPE,MOUNTPOINT', shell=True,
                               capture_output=True, text=True)
            if 'crypt' in r.stdout:
                return 'LUKS encryption detected'
            return 'No disk encryption detected'
        return 'Check manually for your OS'
    except Exception as e:
        return f'Check error: {e}'


def _check_outdated_packages() -> list:
    try:
        pip_cmd = 'pip' if platform.system() == 'Windows' else 'pip3'
        r = subprocess.run(
            [pip_cmd, 'list', '--outdated', '--format=json'],
            capture_output=True, text=True, timeout=30,
            shell=(platform.system() == 'Windows')
        )
        if r.returncode == 0 and r.stdout.strip():
            packages = _json.loads(r.stdout)
            return [f"{p['name']} ({p['version']} → {p['latest_version']})" for p in packages[:10]]
        return []
    except Exception:
        return ['Unable to check — pip not available']


def _check_suspicious_processes() -> list:
    try:
        import psutil
        known_suspicious = ['cryptominer', 'xmrig', 'coinhive', 'keylogger', 'trojan']
        suspicious = []
        for proc in psutil.process_iter(['name']):
            name = (proc.info['name'] or '').lower()
            for s in known_suspicious:
                if s in name:
                    suspicious.append(proc.info['name'])
        return suspicious
    except ImportError:
        return ['psutil not installed — cannot scan processes']
    except Exception:
        return []


def _check_ssl_tls(domain: str = 'localhost') -> str:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=2) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                expiry = cert['notAfter'] if cert else 'unknown'
                return f"SSL/TLS valid, expires: {expiry}"
    except Exception as e:
        return f"SSL/TLS not detected: {e}"


def _check_backup_status(path: str = '/backups') -> str:
    try:
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            if files:
                latest = max(os.path.getmtime(os.path.join(path, f)) for f in files)
                last_backup = datetime.fromtimestamp(latest)
                return f"Last backup: {last_backup.strftime('%Y-%m-%d %H:%M:%S')}"
            return "No backup files found"
        return "Backup folder not found"
    except Exception as e:
        return f"Backup check error: {e}"


def _check_patch_status() -> str:
    try:
        if platform.system() == 'Windows':
            r = subprocess.run('wmic qfe get HotFixID,InstalledOn',
                               shell=True, capture_output=True, text=True, timeout=15)
            if r.returncode == 0:
                lines = [ln.strip() for ln in r.stdout.strip().split('\n') if ln.strip()]
                return f"{len(lines) - 1} patches installed" if len(lines) > 1 else "Patch data unavailable"
            return "Patch status unavailable"
        else:
            r = subprocess.run('apt list --upgradable 2>/dev/null',
                               shell=True, capture_output=True, text=True, timeout=15)
            upgradable = [ln for ln in r.stdout.split('\n') if 'upgradable' in ln]
            return f"{len(upgradable)} packages upgradable" if upgradable else "All packages up to date"
    except Exception as e:
        return f"Patch check error: {e}"


def _get_external_ip() -> str:
    try:
        import requests as _requests
        r = _requests.get('https://api.ipify.org?format=json', timeout=3)
        return r.json().get('ip', 'Unknown')
    except ImportError:
        return 'requests library not installed'
    except Exception as e:
        return f"IP check error: {e}"


# ──────────────────────────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────────────────────────

def _display_results(results):
    """Display 15-control assessment results in a rich table."""
    table = Table(title="Assessment Results — 15 Controls")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Control", style="white")
    table.add_column("Score", style="magenta")
    table.add_column("Status", min_width=8)
    table.add_column("Details", style="dim")

    for control_id, control_data in results.controls.items():
        status_emoji = {
            "PASS": "✅", "WARNING": "⚠️ ", "FAIL": "❌",
            "ERROR": "🔥", "NOT_ASSESSED": "—"
        }.get(control_data.status, "❓")

        status_style = {
            "PASS": "green", "WARNING": "yellow", "FAIL": "red",
            "ERROR": "bold red"
        }.get(control_data.status, "dim")

        table.add_row(
            getattr(control_data, 'control_id', control_id),
            control_data.name,
            f"{control_data.score}/{control_data.weight}",
            Text(f"{status_emoji} {control_data.status}", style=status_style),
            control_data.details,
        )

    console.print(table)

    # Summary panel
    percentage = (results.score / results.total_possible) * 100 if results.total_possible else 0
    cert_style = {"GOLD": "bold yellow", "SILVER": "white", "BRONZE": "dark_orange",
                  "NOT_CERTIFIED": "red"}.get(results.certification_level, "dim")

    summary = (
        f"[bold blue]Overall Score:[/bold blue] {results.score}/{results.total_possible} ({percentage:.1f}%)\n"
        f"[bold]Certification Level:[/bold] [{cert_style}]{results.certification_level}[/{cert_style}]"
    )
    if hasattr(results, 'critical_failures') and results.critical_failures:
        summary += f"\n[red]Critical Failures: {results.critical_failures}[/red]"

    console.print(Panel.fit(summary, title="📊 Summary"))

    # Recommendations
    if results.recommendations:
        rec_text = "\n".join(f"• {rec}" for rec in results.recommendations)
        console.print(Panel.fit(rec_text, title="💡 Recommendations"))


def _display_scan_table(results: dict, recommendations: list):
    """Display system scan results in a rich table."""
    table = Table(title="System Scan Results")
    table.add_column("Check", style="cyan", no_wrap=True)
    table.add_column("Result", style="white")

    for key, value in results.items():
        if key == 'recommendations':
            continue
        display_key = key.replace('_', ' ').title()
        if isinstance(value, list):
            value_str = ', '.join(str(v) for v in value) if value else 'None'
        else:
            value_str = str(value)

        # Colour hints
        if any(bad in value_str.lower() for bad in ['not', 'error', 'disabled', 'unknown', 'unable']):
            style = "red"
        elif any(good in value_str.lower() for good in ['enabled', 'active', 'detected', 'good', 'none']):
            style = "green"
        else:
            style = "white"

        table.add_row(display_key, Text(value_str, style=style))

    console.print(table)

    if recommendations:
        rec_text = "\n".join(f"• {r}" for r in recommendations)
        console.print(Panel.fit(rec_text, title="💡 Recommendations"))


def _display_zambia_results(result: dict):
    """Display Zambia risk assessment results."""
    score = result['score']
    risk = result['risk_level']

    risk_style = {"LOW RISK": "green", "MEDIUM RISK": "yellow", "HIGH RISK": "bold red"}.get(risk, "dim")

    console.print(Panel.fit(
        f"[bold blue]Score:[/bold blue] {score}/100\n"
        f"[bold]Risk Level:[/bold] [{risk_style}]{risk}[/{risk_style}]\n"
        f"[dim]Mitigated: {result['mitigated']}/{result['total_checks']} checks[/dim]",
        title="📊 Zambia Assessment Summary"
    ))

    if result['findings']:
        findings_text = "\n".join(f"• {f}" for f in result['findings'])
        console.print(Panel.fit(findings_text, title="⚠️  Findings"))
    else:
        console.print("[green]✅ No findings — all mitigations in place![/green]")


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    cli()
