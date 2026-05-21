"""
Pre-Deployment Security Gate
Tech-stack agnostic security checks for any project before shipping to users.
Covers system hygiene, network exposure, secrets, code quality and
cross-stack application health (Node, Python, PHP, Java, Go, Ruby, .NET, etc.)
"""

import os
import re
import shutil
import subprocess
import sys
import threading
import datetime
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from typing import List

from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_SURFACE_HVR,
    CLR_ACCENT, CLR_ACCENT_HOV, CLR_BLUE,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER, CLR_DIVIDER,
    FONT_TITLE, FONT_HEADING, FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, PAD_SM, NAV_H, BTN_H, BTN_R,
)
from src.gui.screens.business_info import _header
from src.security.deployment.checker import (
    PreDeploymentChecker, CheckResult, DeploymentReadiness,
)

# ── Verdict definitions ───────────────────────────────────────────────────────
VERDICT_STYLE = {
    "CLEARED": {
        "icon": "🚀",
        "colour": CLR_SUCCESS,
        "title": "CLEARED FOR DEPLOYMENT",
        "msg": "All critical checks passed. Your environment meets baseline "
               "digital hygiene standards for shipping to end users.",
    },
    "CAUTION": {
        "icon": "⚠️",
        "colour": CLR_WARNING,
        "title": "DEPLOY WITH CAUTION",
        "msg": "No critical failures, but some warnings require attention before "
               "shipping to production users. Review and resolve highlighted items.",
    },
    "BLOCKED": {
        "icon": "🚫",
        "colour": CLR_DANGER,
        "title": "DEPLOYMENT BLOCKED",
        "msg": "Critical security issues were found. Resolve all CRITICAL failures "
               "before deploying to production end users.",
    },
}

SEV_CLR = {
    "CRITICAL": CLR_DANGER,
    "HIGH":     "#E87000",
    "MEDIUM":   CLR_WARNING,
    "LOW":      CLR_MUTED,
    "INFO":     CLR_BLUE,
}

CAT_ICON = {
    "system":      "💻",
    "network":     "🌐",
    "application": "⚙️",
    "secrets":     "🔑",
    "code":        "📝",
}


# ── Extra code-scanning checks ────────────────────────────────────────────────
class CodeSecurityChecker:
    """Scans source files for common security anti-patterns."""

    SKIP_DIRS = {".git", "__pycache__", "node_modules", "venv", ".venv",
                 "dist", "build", ".tox", "htmlcov"}
    CODE_EXT  = {".py", ".js", ".ts", ".jsx", ".tsx", ".php", ".rb",
                 ".go", ".java", ".cs"}
    CONFIG_EXT = {".env", ".json", ".yaml", ".yml", ".ini", ".conf",
                  ".config", ".toml"}

    def __init__(self, project_root: str):
        self.root = Path(project_root)

    def run_all(self) -> List[CheckResult]:
        return [
            self._check_hardcoded_http_urls(),
            self._check_sql_injection_patterns(),
            self._check_command_injection(),
            self._check_backup_temp_files(),
            self._check_requirements_pinned(),
            self._check_broad_exception_handlers(),
        ]

    def _code_files(self):
        for dirpath, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for fname in files:
                if Path(fname).suffix in self.CODE_EXT:
                    yield Path(dirpath) / fname

    def _read(self, path: Path) -> list:
        try:
            return path.read_text(encoding="utf-8", errors="ignore"
                                  ).splitlines()
        except Exception:
            return []

    def _check_hardcoded_http_urls(self) -> CheckResult:
        """CCS-01  Non-HTTPS URLs hardcoded in source files."""
        # http:// that is NOT localhost / 127.x and NOT a comment
        pattern = re.compile(r'(?<![#/])http://(?!localhost|127\.0\.0\.1)', re.I)
        hits = []
        for fpath in self._code_files():
            lines = self._read(fpath)
            for i, line in enumerate(lines, 1):
                stripped = line.lstrip()
                if stripped.startswith(("#", "//")):
                    continue
                if pattern.search(line):
                    rel = fpath.relative_to(self.root)
                    hits.append(f"{rel}:{i}")
                    if len(hits) >= 5:
                        break
            if len(hits) >= 5:
                break

        if not hits:
            return CheckResult(
                "CCS-01", "Non-HTTPS URLs", True, "MEDIUM",
                "No hardcoded http:// URLs found in source code",
                category="code")
        return CheckResult(
            "CCS-01", "Non-HTTPS URLs", False, "MEDIUM",
            f"Hardcoded http:// found in: {', '.join(hits)}",
            "Replace http:// with https:// or move URLs to config/env vars",
            "code")

    def _check_sql_injection_patterns(self) -> CheckResult:
        """CCS-02  String-formatted SQL queries (injection risk)."""
        patterns = [
            re.compile(r'f["\'].*SELECT.*\{', re.I),
            re.compile(r'["\'].*SELECT.*["\'].*%.*["\']', re.I),
            re.compile(r'execute\s*\(\s*["\'].*\+', re.I),
            re.compile(r'\.format\(.*\).*WHERE', re.I),
        ]
        hits = []
        for fpath in self._code_files():
            lines = self._read(fpath)
            for i, line in enumerate(lines, 1):
                for pat in patterns:
                    if pat.search(line):
                        rel = fpath.relative_to(self.root)
                        hits.append(f"{rel}:{i}")
                        break
                if len(hits) >= 5:
                    break
            if len(hits) >= 5:
                break

        if not hits:
            return CheckResult(
                "CCS-02", "SQL Injection Patterns", True, "CRITICAL",
                "No string-formatted SQL queries detected",
                category="code")
        return CheckResult(
            "CCS-02", "SQL Injection Patterns", False, "CRITICAL",
            f"Potential SQL injection in: {', '.join(hits)}",
            "Use parameterised queries (cursor.execute(sql, params)) — never "
            "format user input directly into SQL strings",
            "code")

    def _check_command_injection(self) -> CheckResult:
        """CCS-03  Dynamic shell/OS command execution patterns."""
        patterns = [
            re.compile(r'os\.system\s*\(.*[+%{]', re.I),
            re.compile(r'subprocess\.(call|run|Popen)\s*\(.*shell\s*=\s*True', re.I),
            re.compile(r'eval\s*\(', re.I),
            re.compile(r'exec\s*\(', re.I),
        ]
        hits = []
        for fpath in self._code_files():
            lines = self._read(fpath)
            for i, line in enumerate(lines, 1):
                stripped = line.lstrip()
                if stripped.startswith(("#", "//")):
                    continue
                for pat in patterns:
                    if pat.search(line):
                        rel = fpath.relative_to(self.root)
                        hits.append(f"{rel}:{i}")
                        break
                if len(hits) >= 5:
                    break
            if len(hits) >= 5:
                break

        if not hits:
            return CheckResult(
                "CCS-03", "Command Injection Risk", True, "CRITICAL",
                "No unsafe dynamic shell execution detected",
                category="code")
        return CheckResult(
            "CCS-03", "Command Injection Risk", False, "CRITICAL",
            f"Unsafe exec patterns in: {', '.join(hits)}",
            "Avoid shell=True with user input. Use a list of arguments and "
            "validate/whitelist all inputs before passing to subprocess",
            "code")

    def _check_backup_temp_files(self) -> CheckResult:
        """CCS-04  Backup / temp / test-data files left in the project."""
        BAD_EXT = {".bak", ".orig", ".tmp", ".swp", ".old", ".save"}
        BAD_NAMES = {"test_data.sql", "dump.sql", "backup.sql",
                     "test.db", "dev.db", "secrets.txt"}
        hits = []
        for dirpath, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for fname in files:
                lower = fname.lower()
                fpath = Path(dirpath) / fname
                if (Path(fname).suffix in BAD_EXT
                        or lower in BAD_NAMES):
                    try:
                        rel = fpath.relative_to(self.root)
                        hits.append(str(rel))
                    except ValueError:
                        hits.append(fname)
                if len(hits) >= 5:
                    break
            if len(hits) >= 5:
                break

        if not hits:
            return CheckResult(
                "CCS-04", "Backup / Temp Files", True, "LOW",
                "No backup or temporary files found in project tree",
                category="code")
        return CheckResult(
            "CCS-04", "Backup / Temp Files", False, "LOW",
            f"Stale files found: {', '.join(hits)}",
            "Delete backup/temp files before deploying. Add *.bak, *.tmp "
            "to .gitignore to prevent future commits",
            "code")

    def _check_requirements_pinned(self) -> CheckResult:
        """CCS-05  requirements.txt exists and uses pinned versions (==)."""
        req = self.root / "requirements.txt"
        if not req.exists():
            return CheckResult(
                "CCS-05", "Pinned Dependencies", False, "HIGH",
                "requirements.txt not found",
                "Create requirements.txt with `pip freeze > requirements.txt` "
                "to pin all dependency versions for reproducible deploys",
                "code")
        lines = [l.strip() for l in req.read_text(errors="ignore").splitlines()
                 if l.strip() and not l.startswith("#")]
        unpinned = [l for l in lines if l and "==" not in l
                    and not l.startswith("-")]
        if not unpinned:
            return CheckResult(
                "CCS-05", "Pinned Dependencies", True, "HIGH",
                f"All {len(lines)} dependencies are version-pinned",
                category="code")
        return CheckResult(
            "CCS-05", "Pinned Dependencies", False, "HIGH",
            f"{len(unpinned)} unpinned: {', '.join(unpinned[:4])}{'…' if len(unpinned) > 4 else ''}",
            "Pin all versions with == (e.g. flask==3.0.2) to prevent "
            "unexpected upgrades breaking production",
            "code")

    def _check_broad_exception_handlers(self) -> CheckResult:
        """CCS-06  Bare except / except Exception that swallow errors silently."""
        pattern_bare  = re.compile(r'^\s*except\s*:', re.M)
        pattern_broad = re.compile(r'^\s*except\s+(Exception|BaseException)\s*:', re.M)
        hits = []
        for fpath in self._code_files():
            if fpath.suffix != ".py":
                continue
            text = "\n".join(self._read(fpath))
            lines = text.splitlines()
            matches = list(pattern_bare.finditer(text)) + \
                      list(pattern_broad.finditer(text))
            for m in matches[:2]:
                line_no = text[:m.start()].count("\n") + 1
                # Only flag if the except block contains 'pass' or no re-raise
                ctx = "\n".join(lines[line_no - 1: line_no + 3])
                if "pass" in ctx or "log" not in ctx.lower():
                    rel = fpath.relative_to(self.root)
                    hits.append(f"{rel}:{line_no}")
            if len(hits) >= 5:
                break

        if not hits:
            return CheckResult(
                "CCS-06", "Exception Handling", True, "MEDIUM",
                "No silent broad exception handlers detected",
                category="code")
        return CheckResult(
            "CCS-06", "Exception Handling", False, "MEDIUM",
            f"Silent exception handlers in: {', '.join(hits)}",
            "Replace bare except/pass with specific exceptions and proper "
            "logging so errors are not silently swallowed in production",
            "code")


# ── Tech-stack agnostic application checks ───────────────────────────────────
class ApplicationHygieneChecker:
    """
    Replaces the Python-only PDC-08/09/10 checks with ones that work for
    any tech stack: Node.js, Python, PHP, Java, Go, Ruby, .NET, Rust, etc.
    """

    # Environment variables that signal debug / development mode per stack
    DEBUG_VARS = {
        "DEBUG":                   ("Generic",       {"1", "true", "yes"}),
        "FLASK_DEBUG":             ("Flask/Python",  {"1", "true"}),
        "DJANGO_DEBUG":            ("Django/Python", {"1", "true"}),
        "NODE_ENV":                ("Node.js",       {"development", "dev", "local", "test"}),
        "RAILS_ENV":               ("Rails/Ruby",    {"development", "dev", "test"}),
        "APP_ENV":                 ("Generic",       {"development", "dev", "local", "debug"}),
        "APP_DEBUG":               ("Laravel/PHP",   {"1", "true"}),
        "LARAVEL_DEBUG":           ("Laravel/PHP",   {"1", "true"}),
        "SPRING_PROFILES_ACTIVE":  ("Spring/Java",   {"dev", "development", "local", "test"}),
        "ASPNETCORE_ENVIRONMENT":  ("ASP.NET Core",  {"development", "dev"}),
        "RACK_ENV":                ("Rack/Ruby",     {"development", "dev"}),
        "GO_ENV":                  ("Go",            {"development", "dev", "local"}),
        "SYMFONY_ENV":             ("Symfony/PHP",   {"dev", "test"}),
        "ENVIRONMENT":             ("Generic",       {"development", "dev", "staging", "local"}),
    }

    # Package manifest → (display name, audit command)
    MANIFESTS = {
        "package.json":    ("Node.js",       ["npm", "audit", "--json"]),
        "requirements.txt":("Python (pip)",  [sys.executable, "-m", "pip", "audit"]),
        "Pipfile":         ("Python (pipenv)",["pipenv", "check"]),
        "Gemfile":         ("Ruby",          ["bundle", "audit"]),
        "composer.json":   ("PHP (Composer)",["composer", "audit"]),
        "go.mod":          ("Go",            ["govulncheck", "./..."]),
        "pom.xml":         ("Java (Maven)",  None),   # No simple CLI audit
        "build.gradle":    ("Java (Gradle)", None),
        "Cargo.toml":      ("Rust",          ["cargo", "audit"]),
        "Package.swift":   ("Swift",         None),
        "*.csproj":        (".NET",          ["dotnet", "list", "package", "--vulnerable"]),
    }

    # Known runtime executables
    RUNTIMES = [
        ("node",    "Node.js"),
        ("python3", "Python"),
        ("python",  "Python"),
        ("ruby",    "Ruby"),
        ("php",     "PHP"),
        ("java",    "Java"),
        ("go",      "Go"),
        ("dotnet",  ".NET"),
        ("rustc",   "Rust"),
        ("dart",    "Dart / Flutter"),
    ]

    def __init__(self, project_root: str):
        self.root = Path(project_root)

    def run_all(self) -> List[CheckResult]:
        return [
            self._check_detected_runtimes(),
            self._check_dependency_manifests(),
            self._check_debug_mode(),
            self._check_dev_config_files(),
            self._check_production_config(),
        ]

    def _check_detected_runtimes(self) -> CheckResult:
        """APP-01  Detect all runtimes present and verify they are supported."""
        found = []
        unsupported = []

        for exe, name in self.RUNTIMES:
            path = shutil.which(exe)
            if not path:
                continue
            try:
                out = subprocess.run(
                    [exe, "--version"] if exe not in ("java",) else [exe, "-version"],
                    capture_output=True, text=True, timeout=5
                )
                ver_line = (out.stdout or out.stderr).strip().splitlines()[0]
            except Exception:
                ver_line = "version unknown"
            found.append(f"{name}: {ver_line[:40]}")

        # Check for end-of-life runtimes (simple heuristics)
        eol_patterns = [
            (re.compile(r"v(8|10|12)\.", re.I), "Node.js v8/10/12 are End-of-Life"),
            (re.compile(r"python 2\.", re.I),   "Python 2 is End-of-Life"),
            (re.compile(r"php/?(5\.|7\.0|7\.1)", re.I), "PHP 5/7.0/7.1 are End-of-Life"),
        ]
        for text in found:
            for pat, msg in eol_patterns:
                if pat.search(text):
                    unsupported.append(msg)

        if not found:
            return CheckResult(
                "APP-01", "Runtime Environment", True, "LOW",
                "No runtimes detected in PATH — manual verification recommended",
                category="application")

        if unsupported:
            return CheckResult(
                "APP-01", "Runtime Environment", False, "HIGH",
                f"EOL runtime(s) detected: {'; '.join(unsupported)}",
                "Upgrade to a supported LTS version before deploying to production",
                "application")

        return CheckResult(
            "APP-01", "Runtime Environment", True, "HIGH",
            f"{len(found)} runtime(s) detected: {' | '.join(found)}",
            category="application")

    def _check_dependency_manifests(self) -> CheckResult:
        """APP-02  Find package manifests and attempt a vulnerability audit."""
        found_manifests = []
        audit_results = []
        vulnerable = []

        for pattern, (stack, audit_cmd) in self.MANIFESTS.items():
            # Glob for manifests (support wildcard like *.csproj)
            if "*" in pattern:
                matches = list(self.root.glob(pattern))[:1]
            else:
                matches = [self.root / pattern] if (self.root / pattern).exists() else []

            for manifest in matches:
                found_manifests.append(f"{stack} ({manifest.name})")
                if audit_cmd is None:
                    continue
                # Check if audit tool is available
                if not shutil.which(audit_cmd[0]):
                    continue
                try:
                    r = subprocess.run(
                        audit_cmd, capture_output=True, text=True,
                        timeout=45, cwd=str(self.root))
                    if r.returncode != 0:
                        vulnerable.append(
                            f"{stack}: vulnerabilities found (run "
                            f"{' '.join(audit_cmd)} for details)")
                    else:
                        audit_results.append(f"{stack}: no known vulnerabilities")
                except Exception:
                    pass  # Tool not usable, skip

        if not found_manifests:
            return CheckResult(
                "APP-02", "Dependency Manifests", True, "MEDIUM",
                "No package manifests found (or project uses a non-standard layout)",
                "Ensure a manifest file (package.json, requirements.txt, pom.xml, "
                "Gemfile, etc.) is present so dependencies can be audited",
                "application")

        if vulnerable:
            return CheckResult(
                "APP-02", "Dependency Vulnerabilities", False, "CRITICAL",
                f"Vulnerable packages detected — {'; '.join(vulnerable)}",
                "Update vulnerable dependencies before deploying. "
                "Run the audit tool for your stack to see full details.",
                "application")

        detail = (f"Manifests: {', '.join(found_manifests)}"
                  + (f" | Audited: {', '.join(audit_results)}"
                     if audit_results else " | Audit tools not found — install them"))
        return CheckResult(
            "APP-02", "Dependency Manifests", True, "CRITICAL",
            detail, category="application")

    def _check_debug_mode(self) -> CheckResult:
        """APP-03  Check debug/dev-mode env vars for ALL tech stacks."""
        active = []
        for var, (stack, bad_vals) in self.DEBUG_VARS.items():
            val = os.environ.get(var, "").lower().strip()
            if val and val in bad_vals:
                active.append(f"{var}={os.environ[var]} ({stack})")

        if not active:
            return CheckResult(
                "APP-03", "Debug / Dev Mode", True, "HIGH",
                "No debug or development-mode environment variables detected",
                category="application")

        return CheckResult(
            "APP-03", "Debug / Dev Mode", False, "HIGH",
            f"Development mode active: {' | '.join(active)}",
            "Set all debug flags to production values before deploying: "
            "e.g. NODE_ENV=production, DEBUG=false, APP_ENV=production",
            "application")

    def _check_dev_config_files(self) -> CheckResult:
        """APP-04  Development-only config files that should not reach production."""
        BAD_FILES = [
            ".env.development", ".env.dev", ".env.local", ".env.test",
            ".env.staging",
            "config/development.json", "config/development.yml",
            "config/dev.json", "appsettings.Development.json",
            "application-dev.yml", "application-dev.properties",
            "database.yml.example", "secrets.yml",
        ]
        found = []
        for fname in BAD_FILES:
            candidate = self.root / fname
            if candidate.exists():
                found.append(fname)

        if not found:
            return CheckResult(
                "APP-04", "Dev Config Files", True, "MEDIUM",
                "No development-only configuration files found in project root",
                category="application")

        return CheckResult(
            "APP-04", "Dev Config Files", False, "MEDIUM",
            f"Dev-only configs present: {', '.join(found)}",
            "Remove or exclude development config files from production builds. "
            "Add them to .gitignore and .dockerignore",
            "application")

    def _check_production_config(self) -> CheckResult:
        """APP-05  Verify production-mode indicators exist."""
        signals = []
        missing = []

        # Check key env vars that should be set for production
        if os.environ.get("NODE_ENV", "").lower() == "production":
            signals.append("NODE_ENV=production")
        if os.environ.get("APP_ENV", "").lower() == "production":
            signals.append("APP_ENV=production")
        if os.environ.get("RAILS_ENV", "").lower() == "production":
            signals.append("RAILS_ENV=production")
        if os.environ.get("ASPNETCORE_ENVIRONMENT", "").lower() == "production":
            signals.append("ASPNETCORE_ENVIRONMENT=Production")
        if os.environ.get("DJANGO_SETTINGS_MODULE", ""):
            signals.append(f"DJANGO_SETTINGS_MODULE="
                           f"{os.environ['DJANGO_SETTINGS_MODULE']}")

        # Check for .env.production
        if (self.root / ".env.production").exists():
            signals.append(".env.production present")

        # Check if DATABASE_URL points to localhost (dev indicator)
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url and ("localhost" in db_url or "127.0.0.1" in db_url):
            missing.append("DATABASE_URL points to localhost — use a "
                           "production database URL")

        if missing:
            return CheckResult(
                "APP-05", "Production Configuration", False, "HIGH",
                f"Production config issue: {' | '.join(missing)}",
                "Update DATABASE_URL and other connection strings to point to "
                "production services before deploying",
                "application")

        if signals:
            return CheckResult(
                "APP-05", "Production Configuration", True, "HIGH",
                f"Production indicators found: {' | '.join(signals)}",
                category="application")

        return CheckResult(
            "APP-05", "Production Configuration", True, "MEDIUM",
            "No production env vars detected — ensure your deployment pipeline "
            "sets NODE_ENV=production (or equivalent) at runtime",
            category="application")


# ── Aggregate verdict helper ──────────────────────────────────────────────────
def _compute_extended_verdict(report: DeploymentReadiness,
                              code_checks: List[CheckResult]) -> str:
    all_checks = report.checks + code_checks
    critical_fail = any(not c.passed and c.severity == "CRITICAL"
                        for c in all_checks)
    total_fail = sum(1 for c in all_checks if not c.passed)
    if critical_fail:
        return "BLOCKED"
    if total_fail > 2:
        return "CAUTION"
    return "CLEARED"


# ── Screen ────────────────────────────────────────────────────────────────────
class DeploymentCheckerScreen(ctk.CTkFrame):

    def __init__(self, master, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back
        self._scanning = False
        self._report: DeploymentReadiness | None = None
        self._code_checks: List[CheckResult] = []
        self._project_path = ctk.StringVar(value=str(Path.cwd()))
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        _header(self, "Pre-Deployment Security Gate", "Tools", 0.0)

        # ── Controls bar ──────────────────────────────────────────────
        ctrl = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                            height=58)
        ctrl.grid(row=1, column=0, sticky="ew")
        ctrl.grid_columnconfigure(1, weight=1)
        ctrl.grid_propagate(False)

        ctk.CTkLabel(ctrl, text="Project:",
                     font=FONT_SMALL, text_color=CLR_MUTED,
                     ).grid(row=0, column=0, padx=(PAD, 6), pady=14)

        ctk.CTkEntry(
            ctrl, textvariable=self._project_path,
            font=FONT_SMALL, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT, height=32, corner_radius=8,
        ).grid(row=0, column=1, padx=(0, 8), pady=14, sticky="ew")

        ctk.CTkButton(
            ctrl, text="Browse…", font=FONT_SMALL,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC, height=32, corner_radius=8, width=80,
            command=self._browse,
        ).grid(row=0, column=2, padx=(0, 8), pady=14)

        self._scan_btn = ctk.CTkButton(
            ctrl, text="▶  Run Security Check",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#000000", height=34, corner_radius=BTN_R,
            command=self._start_scan,
        )
        self._scan_btn.grid(row=0, column=3, padx=(0, PAD), pady=14)

        # ── Body: verdict + scrollable results ───────────────────────
        body = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        self._body = body

        # Placeholder
        self._placeholder = ctk.CTkLabel(
            body,
            text="Select your project folder and click  ▶ Run Security Check\n\n"
                 "21 checks across 5 categories — works with any tech stack:\n"
                 "Node.js  ·  Python  ·  PHP  ·  Java  ·  Go  ·  Ruby  ·  .NET  ·  Rust  ·  and more",
            font=FONT_BODY, text_color=CLR_MUTED, justify="center",
        )
        self._placeholder.grid(row=0, column=0, pady=60)

        # Progress bar (shown during scan)
        self._progress = ctk.CTkProgressBar(
            self, fg_color=CLR_DIVIDER, progress_color=CLR_ACCENT,
            height=3, corner_radius=0)
        self._progress.set(0)
        self._progress.grid(row=2, column=0, sticky="new")
        self._progress.grid_remove()

        # Nav
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                           height=NAV_H)
        nav.grid(row=3, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)
        nav.grid_propagate(False)

        ctk.CTkButton(
            nav, text="← Back", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC, hover_color=CLR_SURFACE_ALT,
            width=100, height=BTN_H, corner_radius=BTN_R,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

        self._export_btn = ctk.CTkButton(
            nav, text="📄  Export Report",
            font=FONT_SMALL,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC,
            height=BTN_H, corner_radius=BTN_R,
            state="disabled", command=self._export_html,
        )
        self._export_btn.grid(row=0, column=2, padx=(0, PAD), pady=14)

    # ------------------------------------------------------------------- scan
    def _browse(self):
        path = filedialog.askdirectory(
            title="Select Project Root Folder",
            initialdir=self._project_path.get(),
        )
        if path:
            self._project_path.set(path)

    def _start_scan(self):
        if self._scanning:
            return
        self._scanning = True
        self._report = None
        self._code_checks = []
        self._scan_btn.configure(state="disabled", text="Scanning…")
        self._export_btn.configure(state="disabled")

        # Clear body
        for w in self._body.winfo_children():
            w.destroy()

        self._progress.grid()
        self._progress.set(0)
        self._status_lbl = ctk.CTkLabel(
            self._body, text="Running system checks…",
            font=FONT_SMALL, text_color=CLR_MUTED)
        self._status_lbl.grid(row=0, column=0, pady=(16, 4))

        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        root = self._project_path.get()

        # System + Network + Secrets checks from existing checker
        # (PDC-08/09/10 — Python-specific — are intentionally SKIPPED here
        #  and replaced by the tech-agnostic ApplicationHygieneChecker below)
        sys_checker  = PreDeploymentChecker(project_root=root)
        app_checker  = ApplicationHygieneChecker(project_root=root)
        code_checker = CodeSecurityChecker(project_root=root)

        # Total: 7 system/network + 3 secrets + 5 app + 6 code = 21
        total_checks = 21
        done = [0]

        def run_and_track(method, label):
            self.after(0, self._status_lbl.configure, {"text": label})
            result = method()
            done[0] += 1
            self.after(0, self._progress.set, done[0] / total_checks)
            return result

        # System (4) + Network (3) + Secrets (3) — skip PDC-08/09/10
        system_network_secrets = [
            (sys_checker._check_os_updates,        "System: OS patch status…"),
            (sys_checker._check_firewall,           "System: Firewall…"),
            (sys_checker._check_antivirus,          "System: Antivirus…"),
            (sys_checker._check_disk_encryption,    "System: Disk encryption…"),
            (sys_checker._check_open_ports,         "Network: Risky open ports…"),
            (sys_checker._check_dns_resolution,     "Network: DNS resolution…"),
            (sys_checker._check_ssl_tools,          "Network: TLS / OpenSSL…"),
            (sys_checker._check_env_file_exposure,  "Secrets: .env file exposure…"),
            (sys_checker._check_hardcoded_secrets,  "Secrets: Hardcoded credentials…"),
            (sys_checker._check_git_secrets,        "Secrets: Git-tracked secrets…"),
        ]

        # Tech-agnostic application checks (5)
        app_checks_labeled = [
            (app_checker._check_detected_runtimes,   "Application: Runtime detection…"),
            (app_checker._check_dependency_manifests,"Application: Dependency audit…"),
            (app_checker._check_debug_mode,          "Application: Debug/dev mode…"),
            (app_checker._check_dev_config_files,    "Application: Dev config files…"),
            (app_checker._check_production_config,   "Application: Production config…"),
        ]

        # Code scanning checks (6)
        code_checks_labeled = [
            (code_checker._check_hardcoded_http_urls,       "Code: Non-HTTPS URLs…"),
            (code_checker._check_sql_injection_patterns,    "Code: SQL injection patterns…"),
            (code_checker._check_command_injection,         "Code: Command injection…"),
            (code_checker._check_backup_temp_files,         "Code: Backup/temp files…"),
            (code_checker._check_requirements_pinned,       "Code: Dependency manifests…"),
            (code_checker._check_broad_exception_handlers,  "Code: Exception handling…"),
        ]

        report = DeploymentReadiness()
        for method, label in system_network_secrets:
            try:
                report.checks.append(run_and_track(method, label))
            except Exception as exc:
                report.checks.append(CheckResult(
                    "ERR", label.split(":")[1].strip(), False, "HIGH",
                    str(exc), category="system"))

        app_results = []
        for method, label in app_checks_labeled:
            try:
                app_results.append(run_and_track(method, label))
            except Exception as exc:
                app_results.append(CheckResult(
                    "ERR", label.split(":")[1].strip(), False, "MEDIUM",
                    str(exc), category="application"))

        code_results = []
        for method, label in code_checks_labeled:
            try:
                code_results.append(run_and_track(method, label))
            except Exception as exc:
                code_results.append(CheckResult(
                    "ERR", label.split(":")[1].strip(), False, "LOW",
                    str(exc), category="code"))

        self._report = report
        self._code_checks = app_results + code_results
        self.after(0, self._show_results)

    def _show_results(self):
        self._scanning = False
        self._scan_btn.configure(state="normal", text="▶  Re-run Check")
        self._export_btn.configure(state="normal")
        self._progress.grid_remove()

        report = self._report
        code_checks = self._code_checks
        all_checks = (report.checks if report else []) + code_checks
        verdict = _compute_extended_verdict(
            report or DeploymentReadiness(), code_checks)
        vs = VERDICT_STYLE[verdict]

        # Clear body
        for w in self._body.winfo_children():
            w.destroy()

        row = [0]

        def next_row():
            r = row[0]
            row[0] += 1
            return r

        # ── Verdict hero ──────────────────────────────────────────────
        hero = ctk.CTkFrame(self._body, fg_color=CLR_SURFACE,
                            corner_radius=16, border_width=2,
                            border_color=vs["colour"])
        hero.grid(row=next_row(), column=0, padx=PAD,
                  pady=(PAD, 10), sticky="ew")
        hero.grid_columnconfigure(0, weight=1)

        ctk.CTkFrame(hero, fg_color=vs["colour"], height=4,
                     corner_radius=0).grid(row=0, column=0, sticky="ew")

        inner = ctk.CTkFrame(hero, fg_color="transparent")
        inner.grid(row=1, column=0, padx=PAD, pady=14, sticky="ew")
        inner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(inner, text=vs["icon"],
                     font=("Segoe UI Emoji", 40),
                     ).grid(row=0, column=0, rowspan=2, padx=(0, 18),
                            pady=4)
        ctk.CTkLabel(inner, text=vs["title"],
                     font=("Segoe UI", 18, "bold"),
                     text_color=vs["colour"],
                     ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(inner, text=vs["msg"],
                     font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     wraplength=600, justify="left",
                     ).grid(row=1, column=1, sticky="w")

        # Score
        passed = sum(1 for c in all_checks if c.passed)
        total  = len(all_checks)
        ctk.CTkLabel(inner,
                     text=f"{passed}/{total}\npassed",
                     font=("Segoe UI", 14, "bold"),
                     text_color=vs["colour"], justify="center",
                     ).grid(row=0, column=2, rowspan=2, padx=(PAD, 0))

        # ── Category summary ──────────────────────────────────────────
        cats: dict = {}
        for c in all_checks:
            cat = c.category or "other"
            cats.setdefault(cat, {"pass": 0, "fail": 0})
            if c.passed:
                cats[cat]["pass"] += 1
            else:
                cats[cat]["fail"] += 1

        cat_f = ctk.CTkFrame(self._body, fg_color=CLR_SURFACE,
                             corner_radius=14, border_width=1,
                             border_color=CLR_BORDER)
        cat_f.grid(row=next_row(), column=0, padx=PAD,
                   pady=(0, 12), sticky="ew")
        cat_f.grid_columnconfigure(tuple(range(len(cats))), weight=1)

        for col_i, (cat, cnts) in enumerate(cats.items()):
            cat_total = cnts["pass"] + cnts["fail"]
            all_ok = cnts["fail"] == 0
            clr = CLR_SUCCESS if all_ok else CLR_DANGER
            cell = ctk.CTkFrame(cat_f, fg_color="transparent")
            cell.grid(row=0, column=col_i, padx=12, pady=14)
            ctk.CTkLabel(cell,
                         text=f"{CAT_ICON.get(cat, '📋')} {cat.title()}",
                         font=FONT_CAPTION, text_color=CLR_MUTED,
                         ).pack()
            ctk.CTkLabel(cell,
                         text=f"{cnts['pass']}/{cat_total}",
                         font=("Segoe UI", 15, "bold"), text_color=clr,
                         ).pack()

        # ── Individual check results ──────────────────────────────────
        ctk.CTkLabel(self._body, text="Check Details",
                     font=FONT_HEADING, text_color=CLR_TEXT,
                     ).grid(row=next_row(), column=0, padx=PAD,
                            pady=(4, 6), sticky="w")

        # Failures first, then passes
        sorted_checks = sorted(
            all_checks,
            key=lambda c: (c.passed, {"CRITICAL": 0, "HIGH": 1,
                                      "MEDIUM": 2, "LOW": 3}.get(c.severity, 4)),
        )

        for check in sorted_checks:
            self._make_check_card(self._body, next_row(), check)

    def _make_check_card(self, parent, row_idx: int, check: CheckResult):
        status_clr = CLR_SUCCESS if check.passed else SEV_CLR.get(
            check.severity, CLR_MUTED)
        icon = "✔" if check.passed else "✖"

        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE,
                            corner_radius=12, border_width=1,
                            border_color=CLR_BORDER)
        card.grid(row=row_idx, column=0, padx=PAD, pady=3, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # Left status stripe
        ctk.CTkFrame(card, fg_color=status_clr, width=4,
                     corner_radius=0).grid(row=0, column=0,
                                           rowspan=2, sticky="ns")

        # Icon
        ctk.CTkLabel(card, text=icon,
                     font=("Segoe UI", 13), text_color=status_clr,
                     width=26,
                     ).grid(row=0, column=1, padx=(10, 4),
                            pady=(10, 2), sticky="n")

        # Check name + category
        name_f = ctk.CTkFrame(card, fg_color="transparent")
        name_f.grid(row=0, column=2, sticky="w", pady=(10, 2))
        ctk.CTkLabel(name_f,
                     text=f"{check.check_id}  {check.name}",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(side="left")
        ctk.CTkLabel(name_f,
                     text=f"  [{CAT_ICON.get(check.category, '')} "
                          f"{check.category.title()}]",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).pack(side="left")

        # Severity badge
        ctk.CTkLabel(card,
                     text=check.severity,
                     font=("Segoe UI", 9, "bold"),
                     text_color=SEV_CLR.get(check.severity, CLR_MUTED),
                     fg_color=CLR_SURFACE_ALT, corner_radius=6,
                     width=68, height=20,
                     ).grid(row=0, column=3, padx=(0, 12),
                            pady=(10, 2), sticky="ne")

        # Details
        ctk.CTkLabel(card, text=check.details,
                     font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     anchor="w", wraplength=700,
                     ).grid(row=1, column=1, columnspan=3,
                            padx=(10, 12), pady=(0, 4), sticky="w")

        # Remediation (for failed checks only)
        if not check.passed and check.remediation:
            rem_f = ctk.CTkFrame(card, fg_color=CLR_SURFACE_ALT,
                                 corner_radius=8, border_width=1,
                                 border_color=CLR_BORDER)
            rem_f.grid(row=2, column=1, columnspan=3,
                       padx=(10, 12), pady=(0, 10), sticky="ew")
            rem_f.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(rem_f, text="Fix:",
                         font=("Segoe UI", 9, "bold"),
                         text_color=CLR_ACCENT, width=28,
                         ).grid(row=0, column=0, padx=(10, 4), pady=6)
            ctk.CTkLabel(rem_f, text=check.remediation,
                         font=FONT_CAPTION, text_color=CLR_TEXT_SEC,
                         anchor="w", wraplength=660, justify="left",
                         ).grid(row=0, column=1, padx=(0, 10),
                                pady=6, sticky="w")

    # ---------------------------------------------------------------- export
    def _export_html(self):
        if not self._report:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Report", "*.html"), ("All files", "*.*")],
            initialfile=(f"deployment_check_"
                         f"{datetime.date.today().isoformat()}.html"),
        )
        if not path:
            return

        all_checks = self._report.checks + self._code_checks
        verdict = _compute_extended_verdict(self._report, self._code_checks)
        vs = VERDICT_STYLE[verdict]
        passed = sum(1 for c in all_checks if c.passed)
        total  = len(all_checks)

        rows_html = ""
        for c in sorted(all_checks,
                        key=lambda x: (x.passed,
                                       {"CRITICAL": 0, "HIGH": 1,
                                        "MEDIUM": 2, "LOW": 3
                                        }.get(x.severity, 4))):
            status_clr = "#00C896" if c.passed else {
                "CRITICAL": "#E84040", "HIGH": "#E87000",
                "MEDIUM": "#F0A500", "LOW": "#A0B4C8",
            }.get(c.severity, "#A0B4C8")
            icon = "✔" if c.passed else "✖"
            rows_html += (
                f"<tr>"
                f"<td style='color:{status_clr};font-weight:bold'>{icon}</td>"
                f"<td style='font-size:11px;color:#5A7490'>{c.check_id}</td>"
                f"<td>{c.name}</td>"
                f"<td style='color:{status_clr};font-weight:bold'>"
                f"{c.severity}</td>"
                f"<td>{c.category.title()}</td>"
                f"<td style='font-size:11px'>{c.details}</td>"
                f"<td style='font-size:11px;color:#F0A500'>"
                f"{c.remediation or '—'}</td>"
                f"</tr>"
            )

        html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<title>Deployment Security Check — {datetime.date.today()}</title>
<style>
 body{{font-family:'Segoe UI',sans-serif;background:#0B1622;
  color:#ECF4FF;margin:0;padding:32px}}
 h1{{color:{vs['colour']}}}
 .badge{{background:#132236;border-radius:16px;padding:24px;
  margin-bottom:28px;border:2px solid {vs['colour']};
  display:flex;align-items:center;gap:20px}}
 .big{{font-size:42px}}
 .verdict{{font-size:22px;font-weight:bold;color:{vs['colour']}}}
 .msg{{font-size:12px;color:#A0B4C8;margin-top:6px;max-width:600px}}
 .score{{font-size:32px;font-weight:bold;color:{vs['colour']};
  margin-left:auto}}
 table{{width:100%;border-collapse:collapse;background:#132236;
  border-radius:10px;overflow:hidden}}
 th{{background:#1A2D42;padding:10px 14px;text-align:left;
  font-size:11px;color:#5A7490;text-transform:uppercase}}
 td{{padding:8px 14px;border-bottom:1px solid #0B1622;font-size:12px}}
 h2{{color:#2485E8;border-bottom:1px solid #1A2D42;padding-bottom:6px}}
 footer{{margin-top:40px;color:#5A7490;font-size:10px;text-align:center}}
</style></head><body>
<h1>🔒 Pre-Deployment Security Gate</h1>
<div class="badge">
 <div class="big">{vs['icon']}</div>
 <div>
  <div class="verdict">{vs['title']}</div>
  <div class="msg">{vs['msg']}</div>
  <div style="margin-top:8px;font-size:11px;color:#5A7490">
   Project: {self._project_path.get()} &nbsp;·&nbsp;
   Scanned: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
  </div>
 </div>
 <div class="score">{passed}/{total}</div>
</div>
<h2>Check Results</h2>
<table><thead><tr>
 <th></th><th>ID</th><th>Check</th>
 <th>Severity</th><th>Category</th>
 <th>Details</th><th>Remediation</th>
</tr></thead><tbody>{rows_html}</tbody></table>
<footer>Zambia Digital Hygiene Certification Programme
  · Pre-Deployment Security Gate
  · University of Zambia
</footer>
</body></html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        try:
            import os
            os.startfile(path)  # type: ignore
        except AttributeError:
            import subprocess as sp
            sp.Popen(["xdg-open", path])

        dlg = ctk.CTkToplevel(self)
        dlg.title("Saved")
        dlg.geometry("420x120")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text="✔  Report saved!",
                     font=FONT_SUBHEAD, text_color=CLR_SUCCESS,
                     ).pack(pady=(20, 4))
        ctk.CTkLabel(dlg, text=path, font=FONT_CAPTION,
                     text_color=CLR_MUTED, wraplength=380,
                     ).pack(pady=(0, 12))
        ctk.CTkButton(dlg, text="OK",
                      fg_color=CLR_ACCENT, text_color="#000000",
                      height=BTN_H, corner_radius=BTN_R,
                      command=dlg.destroy).pack()
