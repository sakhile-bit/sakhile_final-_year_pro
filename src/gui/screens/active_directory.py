"""Active Directory Hygiene screen — runs real AD security checks over LDAP."""

import threading

import customtkinter as ctk

from src.gui import motion
from src.gui.screens.business_info import _header
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_ACCENT_HOV,
    CLR_BG,
    CLR_BLUE,
    CLR_BORDER,
    CLR_DANGER,
    CLR_DIVIDER,
    CLR_MUTED,
    CLR_SUCCESS,
    CLR_SURFACE,
    CLR_SURFACE_ALT,
    CLR_SURFACE_HVR,
    CLR_TEXT,
    CLR_TEXT_SEC,
    CLR_WARNING,
    FONT_BODY,
    FONT_CAPTION,
    FONT_HEADING,
    FONT_SMALL,
    FONT_SUBHEAD,
    NAV_H,
    PAD,
)

GRADE_STYLE = {
    "HEALTHY": ("🛡️", CLR_SUCCESS, "DIRECTORY HEALTHY",
                "Your Active Directory meets good hygiene standards. Keep "
                "privileged groups small and accounts current."),
    "NEEDS ATTENTION": ("⚠️", CLR_WARNING, "NEEDS ATTENTION",
                        "The essentials are in place but attackers could still "
                        "exploit the gaps below. Fix them worst-first."),
    "AT RISK": ("🚨", CLR_DANGER, "DIRECTORY AT RISK",
                "Serious AD weaknesses were found — these enable lateral "
                "movement and privilege escalation. Remediate them first."),
    "NOT APPLICABLE": ("ℹ️", CLR_MUTED, "NOT ASSESSED",
                       "No live checks ran. Enter the domain and credentials, "
                       "then run the audit on a machine that can reach a "
                       "domain controller."),
}

SEV_CLR = {"CRITICAL": CLR_DANGER, "HIGH": "#E87000",
           "MEDIUM": CLR_WARNING, "LOW": CLR_MUTED}
STATUS_STYLE = {
    "PASS": ("✔", CLR_SUCCESS), "WARN": ("⚠", CLR_WARNING),
    "FAIL": ("✖", CLR_DANGER), "ERROR": ("!", CLR_MUTED),
    "SKIP": ("–", CLR_MUTED),
}
STATUS_ORDER = {"FAIL": 0, "ERROR": 1, "WARN": 2, "PASS": 3, "SKIP": 4}
SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


class ActiveDirectoryScreen(ctk.CTkFrame):
    def __init__(self, master, on_back=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back or (lambda: None)
        self._scanning = False
        self._report = None
        self._build()

    # ------------------------------------------------------------- build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        _header(self, "Active Directory Hygiene", "Tools", 0.0)

        # ── Connection bar ────────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0)
        bar.grid(row=1, column=0, sticky="ew")
        for c in (1, 3):
            bar.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(bar, text="Domain", font=FONT_CAPTION,
                     text_color=CLR_MUTED).grid(row=0, column=0, padx=(PAD, 6),
                                                pady=(12, 0), sticky="w")
        self._domain = ctk.CTkEntry(
            bar, placeholder_text="corp.example.com", font=FONT_SMALL,
            fg_color=CLR_SURFACE_ALT, border_color=CLR_BORDER, border_width=1,
            height=32)
        self._domain.grid(row=1, column=0, columnspan=2, padx=(PAD, 6),
                          pady=(2, 12), sticky="ew")

        ctk.CTkLabel(bar, text="Username (DOMAIN\\user)", font=FONT_CAPTION,
                     text_color=CLR_MUTED).grid(row=0, column=2, padx=6,
                                                pady=(12, 0), sticky="w")
        self._user = ctk.CTkEntry(
            bar, placeholder_text="optional — blank tries current session",
            font=FONT_SMALL, fg_color=CLR_SURFACE_ALT, border_color=CLR_BORDER,
            border_width=1, height=32)
        self._user.grid(row=1, column=2, padx=6, pady=(2, 12), sticky="ew")

        ctk.CTkLabel(bar, text="Password", font=FONT_CAPTION,
                     text_color=CLR_MUTED).grid(row=0, column=3, padx=6,
                                                pady=(12, 0), sticky="w")
        self._pw = ctk.CTkEntry(
            bar, show="•", font=FONT_SMALL, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1, height=32)
        self._pw.grid(row=1, column=3, padx=6, pady=(2, 12), sticky="ew")

        self._run_btn = ctk.CTkButton(
            bar, text="▶  Run Audit", font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#FFFFFF", height=32, width=120, corner_radius=BTN_R,
            command=self._start)
        self._run_btn.grid(row=1, column=4, padx=(6, PAD), pady=(2, 12))

        # Prefill the detected domain in the background (subprocess is slow).
        threading.Thread(target=self._prefill_domain, daemon=True).start()

        # ── Body ──────────────────────────────────────────────────────
        body = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        self._body = body

        self._placeholder = ctk.CTkLabel(
            body,
            text="Enter your domain and (optionally) admin credentials, then "
                 "click  ▶ Run Audit.\n\nChecks: directory connectivity · stale "
                 "accounts · Domain Admins size · machine-account quota · krbtgt "
                 "age · risky account flags · anonymous LDAP bind.",
            font=FONT_BODY, text_color=CLR_MUTED, justify="center")
        self._placeholder.grid(row=0, column=0, pady=60, padx=PAD)

        self._progress = ctk.CTkProgressBar(
            self, fg_color=CLR_DIVIDER, progress_color=CLR_ACCENT, height=3,
            corner_radius=0)
        self._progress.set(0)
        self._progress.grid(row=2, column=0, sticky="new")
        self._progress.grid_remove()

        # ── Nav ───────────────────────────────────────────────────────
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                           height=NAV_H)
        nav.grid(row=3, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)
        nav.grid_propagate(False)
        ctk.CTkButton(
            nav, text="← Back", font=FONT_BODY, fg_color="transparent",
            border_color=CLR_BORDER, border_width=1, text_color=CLR_TEXT_SEC,
            hover_color=CLR_SURFACE_ALT, width=100, height=BTN_H,
            corner_radius=BTN_R, command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

    def _prefill_domain(self):
        try:
            from src.security.active_directory.checks import get_domain_name
            d = get_domain_name()
        except Exception:
            d = None
        if d and self._domain.winfo_exists() and not self._domain.get().strip():
            self.after(0, lambda: self._domain.insert(0, d))

    # ------------------------------------------------------------- run
    def _start(self):
        if self._scanning:
            return
        self._scanning = True
        self._report = None
        self._run_btn.configure(state="disabled", text="Auditing…")
        for w in self._body.winfo_children():
            w.destroy()
        self._progress.grid()
        self._progress.set(0)
        motion.smooth_progress(self._progress, 0.4)
        self._status = ctk.CTkLabel(self._body, text="Contacting directory…",
                                    font=FONT_SMALL, text_color=CLR_MUTED)
        self._status.grid(row=0, column=0, pady=(16, 4))

        domain = self._domain.get().strip()
        user = self._user.get().strip()
        pw = self._pw.get()
        threading.Thread(target=self._run, args=(domain, user, pw),
                         daemon=True).start()

    def _run(self, domain, user, pw):
        try:
            from src.security.active_directory.checks import ADAuditor
            report = ADAuditor(domain=domain or None, user=user,
                               password=pw).run()
        except Exception as exc:
            self.after(0, self._show_error, str(exc))
            return
        self.after(0, self._show_results, report)

    def _show_error(self, msg):
        self._scanning = False
        self._run_btn.configure(state="normal", text="▶  Run Audit")
        self._progress.grid_remove()
        for w in self._body.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._body, text=f"Audit failed:\n{msg}", font=FONT_BODY,
                     text_color=CLR_DANGER, justify="center", wraplength=600,
                     ).grid(row=0, column=0, pady=40, padx=PAD)

    # ------------------------------------------------------------- results
    def _show_results(self, report):
        self._scanning = False
        self._report = report
        self._run_btn.configure(state="normal", text="▶  Re-run Audit")
        motion.smooth_progress(self._progress, 1.0)
        self.after(180, self._progress.grid_remove)

        for w in self._body.winfo_children():
            w.destroy()
        row = [0]

        def nrow():
            r = row[0]
            row[0] += 1
            return r

        icon, clr, title, msg = GRADE_STYLE.get(
            report.grade, GRADE_STYLE["NOT APPLICABLE"])
        hero = ctk.CTkFrame(self._body, fg_color=CLR_SURFACE, corner_radius=16,
                            border_width=2, border_color=clr)
        hero.grid(row=nrow(), column=0, padx=PAD, pady=(PAD, 10), sticky="ew")
        hero.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hero, text=icon, font=("Segoe UI Emoji", 38),
                     ).grid(row=0, column=0, rowspan=2, padx=(18, 14), pady=14)
        ctk.CTkLabel(hero, text=title, font=("Segoe UI", 17, "bold"),
                     text_color=clr, anchor="w",
                     ).grid(row=0, column=1, sticky="w", pady=(14, 0))
        ctk.CTkLabel(hero, text=msg, font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     wraplength=560, justify="left", anchor="w",
                     ).grid(row=1, column=1, sticky="w", pady=(0, 14))
        if report.applicable:
            ctk.CTkLabel(hero, text=f"{report.score_percent}%\nhealthy",
                         font=("Segoe UI", 14, "bold"), text_color=clr,
                         justify="center",
                         ).grid(row=0, column=2, rowspan=2, padx=(10, 18))

        if report.domain:
            ctk.CTkLabel(self._body,
                         text=f"Domain: {report.domain}   ·   "
                              f"{report.passed} passed · {report.warnings} "
                              f"warnings · {report.failed} failed",
                         font=FONT_CAPTION, text_color=CLR_MUTED, anchor="w",
                         ).grid(row=nrow(), column=0, padx=PAD, pady=(0, 8),
                                sticky="w")

        ctk.CTkLabel(self._body, text="Check Details", font=FONT_HEADING,
                     text_color=CLR_TEXT).grid(row=nrow(), column=0, padx=PAD,
                                               pady=(4, 6), sticky="w")

        findings = sorted(
            report.findings,
            key=lambda f: (STATUS_ORDER.get(f.status, 5),
                           SEV_ORDER.get(f.severity, 4)))
        for f in findings:
            self._finding_card(nrow(), f)

        self.after(20, lambda: motion.stagger_grid(
            list(self._body.winfo_children()), interval_ms=16))

    def _finding_card(self, row, f):
        icon, sclr = STATUS_STYLE.get(f.status, ("?", CLR_MUTED))
        card = ctk.CTkFrame(self._body, fg_color=CLR_SURFACE, corner_radius=12,
                            border_width=1, border_color=CLR_BORDER)
        card.grid(row=row, column=0, padx=PAD, pady=3, sticky="ew")
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkFrame(card, fg_color=sclr, width=4, corner_radius=0,
                     ).grid(row=0, column=0, rowspan=3, sticky="ns")
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=1, sticky="ew", padx=(10, 12), pady=(10, 2))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text=f"{icon}  {f.check_id}  {f.name}",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(top, text=f.severity, font=("Segoe UI", 10, "bold"),
                     text_color=SEV_CLR.get(f.severity, CLR_MUTED),
                     fg_color=CLR_SURFACE_ALT, corner_radius=6, width=70,
                     height=20).grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(card, text=f.details, font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, anchor="w", wraplength=680,
                     justify="left").grid(row=1, column=1, sticky="w",
                                          padx=(10, 12), pady=(0, 4))
        if f.status in ("FAIL", "WARN", "ERROR", "SKIP") and f.remediation:
            rem = ctk.CTkFrame(card, fg_color=CLR_SURFACE_ALT, corner_radius=8)
            rem.grid(row=2, column=1, sticky="ew", padx=(10, 12), pady=(0, 10))
            rem.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(rem, text="Fix:", font=("Segoe UI", 10, "bold"),
                         text_color=CLR_ACCENT, width=28,
                         ).grid(row=0, column=0, padx=(10, 4), pady=6)
            ctk.CTkLabel(rem, text=f.remediation, font=FONT_CAPTION,
                         text_color=CLR_TEXT_SEC, anchor="w", wraplength=620,
                         justify="left").grid(row=0, column=1, padx=(0, 10),
                                              pady=6, sticky="w")
