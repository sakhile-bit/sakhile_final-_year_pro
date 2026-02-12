"""
Command-line interface for the assessment tool
"""

import click
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from assessment.assessor import DigitalHygieneAssessor, BusinessInfo
from reporting.generator import ReportGenerator
from database.connection import DatabaseManager
from utils.logging_config import get_logger
from utils.config import config

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version="2.0.0")
@click.option('--config', 'config_file', type=click.Path(exists=True),
              help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def cli(config_file: Optional[str], verbose: bool):
    """Zambia Digital Hygiene Assessment Tool

    A comprehensive cybersecurity assessment tool for SMEs in Zambia.
    """
    if config_file:
        # Load custom config
        pass

    if verbose:
        logger.setLevel("DEBUG")


@cli.command()
@click.option('--business-name', prompt='Business name', help='Name of the business')
@click.option('--business-id', prompt='Business ID', help='Business registration ID')
@click.option('--output-dir', '-o', default='reports',
              help='Output directory for reports')
@click.option('--format', '-f', multiple=True,
              type=click.Choice(['json', 'csv', 'html', 'pdf']),
              default=['json'], help='Report formats to generate')
@click.option('--save-db', is_flag=True, help='Save assessment to database')
def assess(business_name: str, business_id: str, output_dir: str,
           format: tuple, save_db: bool):
    """Run automated cybersecurity assessment"""

    console.print(Panel.fit(
        "[bold blue]Zambia Digital Hygiene Assessment Tool[/bold blue]\n"
        "[dim]Automated cybersecurity assessment for SMEs[/dim]",
        title="🚀 Starting Assessment"
    ))

    try:
        # Create business info
        business_info = BusinessInfo(
            name=business_name,
            id=business_id
        )

        # Initialize assessor
        assessor = DigitalHygieneAssessor(business_info)

        # Run assessment with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running assessment...", total=5)

            results = assessor.run_assessment()

            for i in range(5):
                progress.update(task, advance=1)

        # Display results
        _display_results(results)

        # Generate reports
        if format:
            generator = ReportGenerator(results, business_info)
            Path(output_dir).mkdir(exist_ok=True)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Generating reports...", total=len(format))

                for fmt in format:
                    if fmt == 'json':
                        generator.generate_json(output_dir)
                    elif fmt == 'csv':
                        generator.generate_csv(output_dir)
                    elif fmt == 'html':
                        generator.generate_html(output_dir)
                    elif fmt == 'pdf':
                        generator.generate_pdf(output_dir)

                    progress.update(task, advance=1)

        # Save to database if requested
        if save_db:
            db = DatabaseManager()
            db.save_assessment(results, business_info)
            console.print("✅ Assessment saved to database")

        console.print("\n[green]✓ Assessment completed successfully![/green]")

    except Exception as e:
        logger.error(f"Assessment failed: {e}")
        console.print(f"[red]✗ Assessment failed: {e}[/red]")
        sys.exit(1)


@cli.command()
def manual():
    """Generate manual assessment guide"""
    from manual_assessment_guide import generate_manual_checklist

    try:
        filename = generate_manual_checklist()
        console.print(f"✅ Manual assessment guide generated: {filename}")
    except Exception as e:
        console.print(f"[red]✗ Failed to generate manual guide: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--host', default='localhost', help='Server host')
@click.option('--port', default=5000, type=int, help='Server port')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def web(host: str, port: int, debug: bool):
    """Start web dashboard"""
    from ..web.app import create_app

    try:
        app = create_app()
        console.print(f"🚀 Starting web dashboard on http://{host}:{port}")
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        console.print(f"[red]✗ Failed to start web server: {e}[/red]")
        sys.exit(1)


@cli.command()
def init_db():
    """Initialize database schema"""
    try:
        db = DatabaseManager()
        db.init_database()
        console.print("✅ Database initialized successfully")
    except Exception as e:
        console.print(f"[red]✗ Database initialization failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--project-root', '-p', default='.', help='Project root directory to scan')
@click.option('--json-out', '-j', is_flag=True, help='Output raw JSON instead of formatted table')
def predeploy(project_root: str, json_out: bool):
    """Run pre-deployment digital hygiene checks.

    Scans the current system for security issues before deployment:
    OS patches, firewall, antivirus, open ports, dependency
    vulnerabilities, debug flags, and credential hygiene.

    Exit code 0 = READY, exit code 1 = NOT READY (use in CI/CD).
    """
    from deployment.checker import PreDeploymentChecker
    import json as _json

    console.print(Panel.fit(
        "[bold blue]Pre-Deployment Digital Hygiene Check[/bold blue]\n"
        "[dim]Verifying system is safe to deploy from[/dim]",
        title="🚀 Pre-Deploy Gate"
    ))

    checker = PreDeploymentChecker(project_root=project_root)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running 13 hygiene checks...", total=None)
        report = checker.run_all()
        progress.update(task, completed=True)

    if json_out:
        console.print_json(_json.dumps(report.to_dict(), indent=2))
    else:
        # Build a results table
        table = Table(title="Pre-Deployment Checks")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Check", style="white")
        table.add_column("Severity", style="magenta")
        table.add_column("Result", min_width=8)
        table.add_column("Details", style="dim")

        for c in report.checks:
            result_style = "green" if c.passed else "red"
            result_text = "✅ PASS" if c.passed else "❌ FAIL"
            sev_style = {"CRITICAL": "bold red", "HIGH": "yellow", "MEDIUM": "cyan", "LOW": "dim"}.get(c.severity, "")
            table.add_row(
                c.check_id,
                c.name,
                Text(c.severity, style=sev_style),
                Text(result_text, style=result_style),
                c.details,
            )

        console.print(table)

        # Remediation list for failures
        failures = [c for c in report.checks if not c.passed and c.remediation]
        if failures:
            rem_lines = "\n".join(f"• [bold]{c.check_id}[/bold]: {c.remediation}" for c in failures)
            console.print(Panel.fit(rem_lines, title="🔧 Remediation Steps"))

        # Verdict
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
                f"({report.critical_failures} critical). Fix issues above before deploying.",
                title="🚫 Deploy Gate"
            ))
            sys.exit(1)


def _display_results(results):
    """Display assessment results in a nice table"""
    table = Table(title="Assessment Results")
    table.add_column("Control", style="cyan", no_wrap=True)
    table.add_column("Score", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    for control_id, control_data in results.controls.items():
        status_emoji = {
            "PASS": "✅",
            "WARNING": "⚠️",
            "FAIL": "❌",
            "ERROR": "🔥"
        }.get(control_data.status, "❓")

        table.add_row(
            control_data.name,
            f"{control_data.score}/{control_data.weight}",
            f"{status_emoji} {control_data.status}",
            control_data.details
        )

    console.print(table)

    # Overall score
    percentage = (results.score / results.total_possible) * 100
    score_text = Text(f"Overall Score: {results.score}/{results.total_possible} ({percentage:.1f}%)", style="bold blue")
    level_text = Text(f"Certification Level: {results.certification_level}", style="bold green")

    console.print(Panel.fit(f"{score_text}\n{level_text}", title="📊 Summary"))

    # Recommendations
    if results.recommendations:
        rec_text = "\n".join(f"• {rec}" for rec in results.recommendations)
        console.print(Panel.fit(rec_text, title="💡 Recommendations"))


if __name__ == '__main__':
    cli()
