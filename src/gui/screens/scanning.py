"""Scanning screen — automated C01-C05 checks with live status and one-click fixes."""

import threading
import subprocess
import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_ACCENT_HOV,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER,
    FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, NAV_H, BTN_H, BTN_R,
)
from src.gui.screens.business_info import _header
from src.gui.screens._cancellable import CancellableScreenMixin

CHECKS = [
    ("C01", "OS Updates",           "Windows Update service and last patch date"),
    ("C02", "Antivirus / Defender", "Real-time protection and definition age"),
    ("C03", "Firewall",             "Domain, Private and Public profile status"),
    ("C04", "Password Policy",      "Minimum length, expiry and lockout threshold"),
    ("C05", "Backup System",        "Backup software, VSS, cloud sync"),
]

# Extended checks — run in parallel with C01-C05, displayed separately
EXTENDED_CHECKS = [
    ("EX-01", "Ransomware Protection", "Controlled Folder Access status"),
    ("EX-02", "Local Account Audit",   "Guest disabled, built-in admin review"),
    ("EX-03", "AutoRun Policy",        "USB/CD AutoRun disabled"),
    ("EX-04", "Windows Hello / PIN",   "Modern phishing-resistant authentication"),
    ("EX-05", "Pending Updates",       "Count of outstanding Windows updates"),
]

STATUS_STYLE = {
    "PASS":         ("✔", CLR_SUCCESS),
    "WARNING":      ("⚠", CLR_WARNING),
    "FAIL":         ("✖", CLR_DANGER),
    "ERROR":        ("!", CLR_WARNING),
    "NOT_ASSESSED": ("–", CLR_MUTED),
    "pending":      ("…", CLR_MUTED),
}

FIX_ACTIONS = {
    "C01": {
        "label": "Enable Auto-Update",
        "description": "Set Windows Update to Automatic and start the service.",
        "commands": [["powershell", "-NonInteractive", "-Command",
                      "Set-Service wuauserv -StartupType Automatic; "
                      "Start-Service wuauserv -EA SilentlyContinue"]],
    },
    "C02": {
        "label": "Enable Defender",
        "description": "Turn on Windows Defender real-time protection.",
        "commands": [["powershell", "-NonInteractive", "-Command",
                      "Set-MpPreference -DisableRealtimeMonitoring $false "
                      "-DisableBehaviorMonitoring $false"]],
    },
    "C03": {
        "label": "Enable Firewall",
        "description": "Turn on Windows Firewall for all network profiles.",
        "commands": [["netsh", "advfirewall", "set", "allprofiles", "state", "on"]],
    },
    "C04": {
        "label": "Apply Password Policy",
        "description": "Set 8-char minimum, 90-day expiry, 5-attempt lockout.",
        "commands": [["net", "accounts",
                      "/minpwlen:8", "/maxpwage:90", "/lockoutthreshold:5"]],
    },
    "C05": {
        "label": "Open Backup Settings",
        "description": "Open Windows Backup settings to configure backups.",
        "commands": [], "open_url": "ms-settings:backup",
    },
}


class ScanningScreen(CancellableScreenMixin, ctk.CTkFrame):

    def __init__(self, master, business_info, on_next, on_back, on_skip=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._biz = business_info
        self._on_next = on_next
        self._on_back = on_back
        self._on_skip = on_skip
        self._results: dict = {}
        self._ext_results: dict = {}   # {eid: (status_str, detail_str)}
        self._ext_rows: dict = {}      # {eid: (stripe, icon, detail_lbl)}
        self._row_frames: dict = {}
        self._status_labels: dict = {}
        self._icon_labels: dict = {}
        self._fix_btns: dict = {}
        self._build()
        # Background scans use self._safe_after (from CancellableScreenMixin)
        # so navigating away mid-scan can't touch a destroyed widget.
        threading.Thread(target=self._run_scan, daemon=True).start()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        _header(self, "Automated Security Checks", "3 of 5", 0.60)

        body = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=PAD)
        body.grid_columnconfigure(0, weight=1)

        # Info banner
        banner = ctk.CTkFrame(body, fg_color=CLR_SURFACE_ALT,
                              corner_radius=10, border_width=1,
                              border_color=CLR_BORDER)
        banner.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        ctk.CTkLabel(
            banner,
            text="🔍  Running 5 automated Windows security checks. "
                 "Click  🔧 Fix  to auto-remediate any issues found.",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(padx=14, pady=10)

        # Overall progress bar
        self._progress = ctk.CTkProgressBar(
            body, fg_color=CLR_SURFACE, progress_color=CLR_ACCENT,
            height=5, corner_radius=2)
        self._progress.set(0)
        self._progress.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        # Core check rows (C01-C05)
        ctk.CTkLabel(body, text="CORE CONTROLS  (C01 – C05)",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=2, column=0, sticky="w", pady=(0, 6))
        for i, (cid, cname, cdesc) in enumerate(CHECKS):
            self._make_check_row(body, i + 3, cid, cname, cdesc)

        # Extended check rows (EX-01 – EX-05)
        base = len(CHECKS) + 4
        ctk.CTkLabel(body, text="EXTENDED SECURITY CHECKS",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=base, column=0, sticky="w",
                            pady=(14, 6))
        self._ext_rows: dict = {}
        for i, (eid, ename, edesc) in enumerate(EXTENDED_CHECKS):
            self._make_ext_row(body, base + 1 + i, eid, ename, edesc)

        self._status_var = ctk.StringVar(value="Initialising…")
        ctk.CTkLabel(body, textvariable=self._status_var,
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=base + len(EXTENDED_CHECKS) + 2,
                            column=0, pady=(8, 0), sticky="w")

        # Nav bar
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                           height=NAV_H)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)
        nav.grid_propagate(False)

        ctk.CTkButton(
            nav, text="← Back", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC, hover_color=CLR_SURFACE_ALT,
            width=100, height=BTN_H, corner_radius=BTN_R,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

        self._skip_btn = ctk.CTkButton(
            nav, text="Auto-Only Results  →", font=FONT_SMALL,
            fg_color="transparent", border_color=CLR_ACCENT, border_width=1,
            text_color=CLR_ACCENT, hover_color=CLR_SURFACE_ALT,
            height=BTN_H, corner_radius=BTN_R,
            state="disabled", command=self._skip,
        )
        self._skip_btn.grid(row=0, column=2, padx=(0, 8), pady=14)

        self._next_btn = ctk.CTkButton(
            nav, text="Manual Questions  →",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#000000", height=BTN_H, corner_radius=BTN_R,
            state="disabled", command=self._proceed,
        )
        self._next_btn.grid(row=0, column=3, padx=PAD, pady=14)

    def _make_check_row(self, parent, grid_row, cid, cname, cdesc):
        # Outer card
        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=12,
                            border_width=1, border_color=CLR_BORDER)
        card.grid(row=grid_row, column=0, sticky="ew", pady=4)
        card.grid_columnconfigure(1, weight=1)
        self._row_frames[cid] = card

        # Left status stripe (colour updates after scan)
        stripe = ctk.CTkFrame(card, fg_color=CLR_BORDER, width=5,
                              corner_radius=0)
        stripe.grid(row=0, column=0, sticky="ns", padx=(0, 0), pady=0)

        # Status icon
        icon = ctk.CTkLabel(card, text="…",
                            font=("Segoe UI Emoji", 22),
                            text_color=CLR_MUTED, width=44)
        icon.grid(row=0, column=1, padx=(12, 6), pady=16, sticky="n")
        self._icon_labels[cid] = (stripe, icon)

        # Name + description
        txt = ctk.CTkFrame(card, fg_color="transparent")
        txt.grid(row=0, column=2, sticky="w", pady=14)
        ctk.CTkLabel(txt, text=f"{cid}  {cname}",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
                     ).pack(anchor="w")
        ctk.CTkLabel(txt, text=cdesc, font=FONT_CAPTION,
                     text_color=CLR_MUTED, anchor="w",
                     ).pack(anchor="w")

        # Score + detail (right)
        detail = ctk.CTkLabel(card, text="Pending…",
                              font=FONT_SMALL, text_color=CLR_MUTED,
                              anchor="e", wraplength=220)
        detail.grid(row=0, column=3, padx=(0, 14), pady=14, sticky="e")
        self._status_labels[cid] = detail

    def _make_ext_row(self, parent, grid_row, eid, ename, edesc):
        """Lightweight row for extended (EX-*) checks — no fix button."""
        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=10,
                            border_width=1, border_color=CLR_BORDER)
        card.grid(row=grid_row, column=0, sticky="ew", pady=3)
        card.grid_columnconfigure(2, weight=1)

        stripe = ctk.CTkFrame(card, fg_color=CLR_BORDER, width=3,
                              corner_radius=0)
        stripe.grid(row=0, column=0, sticky="ns")

        icon_lbl = ctk.CTkLabel(card, text="…",
                                font=("Segoe UI Emoji", 16),
                                text_color=CLR_MUTED, width=36)
        icon_lbl.grid(row=0, column=1, padx=(10, 6), pady=12, sticky="n")

        txt = ctk.CTkFrame(card, fg_color="transparent")
        txt.grid(row=0, column=2, sticky="w", pady=12)
        ctk.CTkLabel(txt, text=f"{eid}  {ename}",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
                     ).pack(anchor="w")
        ctk.CTkLabel(txt, text=edesc, font=FONT_CAPTION,
                     text_color=CLR_MUTED, anchor="w",
                     ).pack(anchor="w")

        detail_lbl = ctk.CTkLabel(card, text="Pending",
                                  font=FONT_SMALL, text_color=CLR_MUTED,
                                  anchor="e", wraplength=240)
        detail_lbl.grid(row=0, column=3, padx=(0, 12), pady=12, sticky="e")

        self._ext_rows[eid] = (stripe, icon_lbl, detail_lbl)

    # ------------------------------------------------------------------ scan
    def _run_scan(self):
        from src.security.assessment.assessor import DigitalHygieneAssessor
        assessor = DigitalHygieneAssessor(self._biz, assessment_tier="automated")

        # Core C01-C05 methods
        core_methods = [
            ("C01", assessor._check_os_updates),
            ("C02", assessor._check_antivirus_enhanced),
            ("C03", assessor._check_firewall_enhanced),
            ("C04", assessor._check_password_policy),
            ("C05", assessor._check_backup_system),
        ]
        total = len(CHECKS) + len(EXTENDED_CHECKS)

        for idx, (cid, method) in enumerate(core_methods):
            if self._cancelled:
                return
            if not self._safe_after(0, self._status_var.set, f"Scanning {cid}…"):
                return
            try:
                result = method()
            except Exception as exc:
                from src.security.assessment.assessor import (
                    ControlResult, CONTROL_CATALOGUE)
                cat_key = next(k for k in CONTROL_CATALOGUE
                               if CONTROL_CATALOGUE[k]["id"] == cid)
                ctrl = CONTROL_CATALOGUE[cat_key]
                result = ControlResult(
                    control_id=cid, name=ctrl["name"],
                    score=0, weight=ctrl["weight"],
                    status="ERROR", details=str(exc),
                )
            self._results[cid] = result
            if not self._safe_after(0, self._update_row, cid, result,
                                    (idx + 1) / total):
                return

        # Extended EX-01…EX-05 checks (run after core, in background thread)
        ext_methods = [
            ("EX-01", assessor._check_ransomware_protection),
            ("EX-02", assessor._check_local_accounts),
            ("EX-03", assessor._check_autorun_policy),
            ("EX-04", assessor._check_windows_hello),
            ("EX-05", assessor._check_pending_security_updates),
        ]
        for idx, (eid, method) in enumerate(ext_methods):
            if self._cancelled:
                return
            if not self._safe_after(0, self._status_var.set,
                                    f"Extended check {eid}…"):
                return
            try:
                status_str, detail_str = method()
            except Exception as exc:
                status_str, detail_str = "ERROR", str(exc)
            self._ext_results[eid] = (status_str, detail_str)
            progress = (len(CHECKS) + idx + 1) / total
            if not self._safe_after(0, self._update_ext_row, eid,
                                    status_str, detail_str, progress):
                return

        self._safe_after(0, self._scan_complete)

    def _update_row(self, cid, result, progress):
        icon_txt, icon_clr = STATUS_STYLE.get(result.status, ("?", CLR_MUTED))
        stripe, icon = self._icon_labels[cid]
        stripe.configure(fg_color=icon_clr)
        icon.configure(text=icon_txt, text_color=icon_clr)
        short = (result.details[:65] + "…"
                 if len(result.details) > 65 else result.details)
        self._status_labels[cid].configure(
            text=f"{result.score}/{result.weight} pts\n{short}",
            text_color=icon_clr)
        self._progress.set(progress)

    def _update_ext_row(self, eid, status_str, detail_str, progress):
        icon_txt, icon_clr = STATUS_STYLE.get(status_str, ("?", CLR_MUTED))
        stripe, icon, detail_lbl = self._ext_rows[eid]
        stripe.configure(fg_color=icon_clr)
        icon.configure(text=icon_txt, text_color=icon_clr)
        short = detail_str[:65] + "…" if len(detail_str) > 65 else detail_str
        detail_lbl.configure(text=short, text_color=icon_clr)
        self._progress.set(progress)

    def _scan_complete(self):
        passed = sum(1 for r in self._results.values() if r.status == "PASS")
        ext_pass = sum(1 for s, _ in self._ext_results.values()
                       if s == "PASS")
        self._status_var.set(
            f"All checks done — {passed}/5 core passed, "
            f"{ext_pass}/5 extended passed.  Fix issues, then continue.")
        self._next_btn.configure(state="normal")
        self._skip_btn.configure(state="normal")
        self._add_fix_buttons()

    # ---------------------------------------------------------- fix buttons
    def _add_fix_buttons(self):
        for cid, result in self._results.items():
            if result.status not in ("FAIL", "WARNING", "ERROR"):
                continue
            if cid not in FIX_ACTIONS:
                continue
            btn = ctk.CTkButton(
                self._row_frames[cid], text="🔧  Fix",
                font=("Segoe UI", 10, "bold"),
                fg_color=CLR_SURFACE_ALT, hover_color="#1A3A2A",
                border_color=CLR_ACCENT, border_width=1,
                text_color=CLR_ACCENT, width=76, height=30, corner_radius=8,
                command=lambda c=cid, f=FIX_ACTIONS[cid]: self._confirm_fix(c, f),
            )
            btn.grid(row=0, column=4, padx=(0, 14), pady=14)
            self._fix_btns[cid] = btn

    def _confirm_fix(self, cid, fix):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Apply Fix")
        dlg.geometry("420x180")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text=f"Apply: {fix['label']}",
                     font=FONT_SUBHEAD, text_color=CLR_ACCENT,
                     ).pack(pady=(22, 6))
        ctk.CTkLabel(dlg, text=fix["description"], font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, wraplength=380,
                     justify="center").pack(pady=(0, 18))
        row = ctk.CTkFrame(dlg, fg_color="transparent")
        row.pack()
        ctk.CTkButton(row, text="Cancel", width=100,
                      fg_color="transparent", border_color=CLR_BORDER,
                      border_width=1, text_color=CLR_TEXT_SEC,
                      hover_color=CLR_SURFACE_ALT,
                      command=dlg.destroy).pack(side="left", padx=8)
        ctk.CTkButton(row, text="Apply Fix", width=120,
                      fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
                      text_color="#000000",
                      command=lambda: self._apply_fix(cid, fix, dlg),
                      ).pack(side="left", padx=8)

    def _apply_fix(self, cid, fix, dlg):
        dlg.destroy()
        btn = self._fix_btns.get(cid)
        if btn:
            btn.configure(text="Fixing…", state="disabled")

        def run():
            try:
                if fix.get("open_url"):
                    import os
                    os.startfile(fix["open_url"])  # type: ignore
                for cmd in fix.get("commands", []):
                    subprocess.run(cmd, capture_output=True,
                                   timeout=30, shell=False)
            except Exception:
                import logging
                logging.getLogger(__name__).warning(
                    "quick-fix command failed", exc_info=True)
            self._safe_after(0, self._recheck, cid)

        threading.Thread(target=run, daemon=True).start()

    def _recheck(self, cid):
        from src.security.assessment.assessor import DigitalHygieneAssessor
        a = DigitalHygieneAssessor(self._biz, assessment_tier="automated")
        methods = {
            "C01": a._check_os_updates,
            "C02": a._check_antivirus_enhanced,
            "C03": a._check_firewall_enhanced,
            "C04": a._check_password_policy,
            "C05": a._check_backup_system,
        }

        def run():
            try:
                result = methods[cid]()
            except Exception as exc:
                from src.security.assessment.assessor import (
                    ControlResult, CONTROL_CATALOGUE)
                cat_key = next(k for k in CONTROL_CATALOGUE
                               if CONTROL_CATALOGUE[k]["id"] == cid)
                ctrl = CONTROL_CATALOGUE[cat_key]
                result = ControlResult(
                    control_id=cid, name=ctrl["name"],
                    score=0, weight=ctrl["weight"],
                    status="ERROR", details=str(exc),
                )
            self._results[cid] = result
            self._safe_after(0, self._post_recheck, cid, result)

        threading.Thread(target=run, daemon=True).start()

    def _post_recheck(self, cid, result):
        self._update_row(cid, result, self._progress.get())
        btn = self._fix_btns.get(cid)
        if btn:
            if result.status == "PASS":
                btn.configure(text="✔  Fixed", state="disabled",
                              fg_color="#1A1730", text_color=CLR_SUCCESS,
                              border_color=CLR_SUCCESS)
            else:
                btn.configure(text="🔧  Retry", state="normal")

    def _proceed(self):
        self._on_next(self._results)

    def _skip(self):
        if self._on_skip:
            self._on_skip(self._results)


class ScanningLogsViewer(ctk.CTkToplevel):
    """Detailed logs viewer for scanning operations."""

    def __init__(self, parent, check_id, check_name, logs):
        super().__init__(parent)
        self.title(f"Detailed Logs — {check_id}: {check_name}")
        self.geometry("800x600")
        self.configure(fg_color=CLR_BG)

        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"📋 Scan Logs: {check_id} — {check_name}",
                     font=("Segoe UI", 14, "bold"), text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=16, pady=12)

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG)
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        if not logs:
            ctk.CTkLabel(scroll, text="No logs available.",
                         font=FONT_BODY, text_color=CLR_MUTED).pack(pady=48)
        else:
            for idx, log_entry in enumerate(logs):
                self._build_log_entry(scroll, idx, log_entry)

        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=50)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        ctk.CTkButton(footer, text="Close", command=self.destroy,
                      fg_color=CLR_SURFACE_ALT, text_color=CLR_TEXT,
                      font=FONT_BODY, height=BTN_H, corner_radius=BTN_R,
                      ).pack(side="left", padx=16, pady=12)

    def _build_log_entry(self, parent, idx, entry):
        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE_ALT, corner_radius=8)
        card.pack(fill="x", pady=6)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 4))
        timestamp = entry.get("timestamp", "N/A")
        level = entry.get("level", "INFO")
        level_color = {"INFO": CLR_SUCCESS, "WARNING": CLR_WARNING,
                       "ERROR": CLR_DANGER}.get(level, CLR_MUTED)
        ctk.CTkLabel(header, text=f"[{timestamp}]",
                     font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     ).pack(anchor="w", side="left")
        ctk.CTkLabel(header, text=level,
                     font=FONT_SMALL, text_color=level_color,
                     ).pack(anchor="e", side="right")
        ctk.CTkLabel(card, text=entry.get("message", ""),
                     font=FONT_SMALL, text_color=CLR_TEXT,
                     wraplength=700, justify="left",
                     ).pack(anchor="w", padx=12, pady=(0, 8))


class DetailedCheckInfo(ctk.CTkToplevel):
    """Detailed information about a specific security check."""

    def __init__(self, parent, check_id, check_name, description, remediation_steps):
        super().__init__(parent)
        self.title(f"Check Details — {check_id}")
        self.geometry("700x500")
        self.configure(fg_color=CLR_BG)

        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"🔍 {check_id}: {check_name}",
                     font=("Segoe UI", 14, "bold"), text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=16, pady=12)

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(scroll, text="Description",
                     font=("Segoe UI", 12, "bold"), text_color=CLR_TEXT,
                     ).pack(anchor="w")
        ctk.CTkLabel(scroll, text=description,
                     font=FONT_BODY, text_color=CLR_TEXT_SEC,
                     wraplength=600, justify="left",
                     ).pack(anchor="w", pady=(4, 16))

        ctk.CTkLabel(scroll, text="Remediation Steps",
                     font=("Segoe UI", 12, "bold"), text_color=CLR_TEXT,
                     ).pack(anchor="w")
        for idx, step in enumerate(remediation_steps, 1):
            step_frame = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE_ALT, corner_radius=6)
            step_frame.pack(fill="x", pady=4)
            ctk.CTkLabel(step_frame, text=f"Step {idx}: {step}",
                         font=FONT_SMALL, text_color=CLR_TEXT,
                         wraplength=600, justify="left",
                         ).pack(anchor="w", padx=12, pady=8)

        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=50)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        ctk.CTkButton(footer, text="Close", command=self.destroy,
                      fg_color=CLR_SURFACE_ALT, text_color=CLR_TEXT,
                      font=FONT_BODY, height=BTN_H, corner_radius=BTN_R,
                      ).pack(side="left", padx=16, pady=12)
