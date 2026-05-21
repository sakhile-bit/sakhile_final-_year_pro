"""Automated scanning screen — C01-C05 with live progress and one-click fixes."""

import threading
import subprocess
import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_ACCENT_HOV, CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER, CLR_DIVIDER,
    FONT_TITLE, FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, PAD_SM, HDR_H, NAV_H, BTN_H, BTN_R,
)
from src.gui.screens.business_info import _header, _nav  # shared helpers

CHECKS = [
    ("C01", "Operating System Updates",   "Verifies Windows Update is current"),
    ("C02", "Antivirus / Defender",        "Checks real-time protection status"),
    ("C03", "Firewall Configuration",      "Tests all firewall profiles"),
    ("C04", "Password Policy",             "Reads local password requirements"),
    ("C05", "Backup System",               "Looks for backup software & files"),
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
        "description": "Set Windows Update service to Automatic and start it.",
        "commands": [["powershell", "-NonInteractive", "-Command",
                      "Set-Service -Name wuauserv -StartupType Automatic; "
                      "Start-Service -Name wuauserv -ErrorAction SilentlyContinue"]],
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
        "commands": [["netsh", "advfirewall", "set", "allprofiles",
                      "state", "on"]],
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


class ScanningScreen(ctk.CTkFrame):

    def __init__(self, master, business_info, on_next, on_back, on_skip=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._biz = business_info
        self._on_next = on_next
        self._on_back = on_back
        self._on_skip = on_skip
        self._results: dict = {}
        self._row_frames: dict = {}
        self._fix_btns: dict = {}
        self._build()
        threading.Thread(target=self._run_scan, daemon=True).start()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        _header(self, "Automated Security Checks", "2 of 4", 0.50)

        body = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=PAD)
        body.grid_columnconfigure(0, weight=1)

        # Info banner
        info = ctk.CTkFrame(body, fg_color=CLR_SURFACE_ALT,
                            corner_radius=12, border_width=1,
                            border_color=CLR_BORDER)
        info.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        ctk.CTkLabel(
            info,
            text="Running 5 automated Windows checks.  "
                 "After scanning, use 🔧 Fix to automatically "
                 "remediate any issues found.",
            font=FONT_SMALL, text_color=CLR_MUTED,
            wraplength=800, justify="left",
        ).grid(padx=14, pady=10)

        # Overall progress bar
        self._progress = ctk.CTkProgressBar(
            body, fg_color=CLR_SURFACE, progress_color=CLR_ACCENT,
            height=6, corner_radius=3,
        )
        self._progress.set(0)
        self._progress.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        # Check rows
        self._check_rows = {}
        for i, (cid, cname, cdesc) in enumerate(CHECKS):
            row_f = ctk.CTkFrame(body, fg_color=CLR_SURFACE, corner_radius=12,
                                 border_width=1, border_color=CLR_BORDER)
            row_f.grid(row=i + 2, column=0, sticky="ew", pady=4)
            row_f.grid_columnconfigure(1, weight=1)
            self._row_frames[cid] = row_f

            # Status icon
            icon_lbl = ctk.CTkLabel(
                row_f, text="…", font=("Segoe UI Emoji", 20),
                text_color=CLR_MUTED, width=40,
            )
            icon_lbl.grid(row=0, column=0, padx=(14, 8), pady=16, sticky="n")

            # Name + description
            txt_f = ctk.CTkFrame(row_f, fg_color="transparent")
            txt_f.grid(row=0, column=1, sticky="w", pady=14)
            ctk.CTkLabel(txt_f, text=f"{cid}  {cname}",
                         font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
                         ).pack(anchor="w")
            ctk.CTkLabel(txt_f, text=cdesc, font=FONT_CAPTION,
                         text_color=CLR_MUTED, anchor="w",
                         ).pack(anchor="w")

            # Score + detail (right side)
            detail_lbl = ctk.CTkLabel(
                row_f, text="Pending", font=FONT_SMALL,
                text_color=CLR_MUTED, anchor="e", wraplength=260,
            )
            detail_lbl.grid(row=0, column=2, padx=(0, 14), pady=14, sticky="e")

            self._check_rows[cid] = (icon_lbl, detail_lbl)

        # Status text
        self._status_var = ctk.StringVar(value="Preparing checks…")
        ctk.CTkLabel(body, textvariable=self._status_var,
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=len(CHECKS) + 2, column=0,
                            pady=(10, 0), sticky="w")

        # Nav
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
            text_color=CLR_ACCENT, hover_color="#003D28",
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

    # ------------------------------------------------------------------ scan
    def _run_scan(self):
        from src.security.assessment.assessor import DigitalHygieneAssessor
        assessor = DigitalHygieneAssessor(self._biz, assessment_tier="automated")
        methods = [
            ("C01", assessor._check_os_updates),
            ("C02", assessor._check_antivirus_enhanced),
            ("C03", assessor._check_firewall_enhanced),
            ("C04", assessor._check_password_policy),
            ("C05", assessor._check_backup_system),
        ]
        for idx, (cid, method) in enumerate(methods):
            self.after(0, self._status_var.set, f"Scanning {cid}…")
            try:
                result = method()
            except Exception as exc:
                from src.security.assessment.assessor import (
                    ControlResult, CONTROL_CATALOGUE)
                cat_key = next(
                    k for k in CONTROL_CATALOGUE
                    if CONTROL_CATALOGUE[k]["id"] == cid)
                ctrl = CONTROL_CATALOGUE[cat_key]
                result = ControlResult(
                    control_id=cid, name=ctrl["name"],
                    score=0, weight=ctrl["weight"],
                    status="ERROR", details=str(exc),
                )
            self._results[cid] = result
            self.after(0, self._update_row, cid, result,
                       (idx + 1) / len(CHECKS))
        self.after(0, self._scan_complete)

    def _update_row(self, cid, result, progress):
        icon_lbl, detail_lbl = self._check_rows[cid]
        icon_txt, icon_clr = STATUS_STYLE.get(result.status, ("?", CLR_MUTED))
        icon_lbl.configure(text=icon_txt, text_color=icon_clr)
        short = (result.details[:72] + "…"
                 if len(result.details) > 72 else result.details)
        detail_lbl.configure(
            text=f"{result.score}/{result.weight} pts  ·  {short}",
            text_color=icon_clr,
        )
        self._progress.set(progress)

    def _scan_complete(self):
        self._status_var.set(
            "✔  Scan complete — fix any issues, then proceed.")
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
            row_f = self._row_frames[cid]
            fix = FIX_ACTIONS[cid]
            btn = ctk.CTkButton(
                row_f, text="🔧  Fix",
                font=FONT_CAPTION,
                fg_color=CLR_SURFACE_ALT,
                hover_color="#1E3A2F",
                border_color=CLR_ACCENT, border_width=1,
                text_color=CLR_ACCENT,
                width=78, height=30, corner_radius=8,
                command=lambda c=cid, f=fix: self._confirm_fix(c, f),
            )
            btn.grid(row=0, column=3, padx=(0, 14), pady=14)
            self._fix_btns[cid] = btn

    def _confirm_fix(self, cid, fix):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Apply Fix")
        dlg.geometry("440x190")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text=f"Apply Fix: {fix['label']}",
                     font=FONT_SUBHEAD, text_color=CLR_ACCENT,
                     ).pack(pady=(22, 6))
        ctk.CTkLabel(dlg, text=fix["description"], font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, wraplength=390,
                     justify="center").pack(pady=(0, 20))
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
            btn.configure(text="Applying…", state="disabled")

        def run():
            try:
                if fix.get("open_url"):
                    import os
                    os.startfile(fix["open_url"])  # type: ignore
                for cmd in fix.get("commands", []):
                    subprocess.run(cmd, capture_output=True,
                                   timeout=30, shell=False)
            except Exception:
                pass
            self.after(0, self._recheck, cid)

        threading.Thread(target=run, daemon=True).start()

    def _recheck(self, cid):
        from src.security.assessment.assessor import DigitalHygieneAssessor
        assessor = DigitalHygieneAssessor(self._biz, assessment_tier="automated")
        method_map = {
            "C01": assessor._check_os_updates,
            "C02": assessor._check_antivirus_enhanced,
            "C03": assessor._check_firewall_enhanced,
            "C04": assessor._check_password_policy,
            "C05": assessor._check_backup_system,
        }

        def run():
            try:
                result = method_map[cid]()
            except Exception as exc:
                from src.security.assessment.assessor import (
                    ControlResult, CONTROL_CATALOGUE)
                cat_key = next(
                    k for k in CONTROL_CATALOGUE
                    if CONTROL_CATALOGUE[k]["id"] == cid)
                ctrl = CONTROL_CATALOGUE[cat_key]
                result = ControlResult(
                    control_id=cid, name=ctrl["name"],
                    score=0, weight=ctrl["weight"],
                    status="ERROR", details=str(exc),
                )
            self._results[cid] = result
            self.after(0, self._post_recheck, cid, result)

        threading.Thread(target=run, daemon=True).start()

    def _post_recheck(self, cid, result):
        self._update_row(cid, result, self._progress.get())
        btn = self._fix_btns.get(cid)
        if btn:
            if result.status == "PASS":
                btn.configure(text="✔  Fixed", state="disabled",
                              fg_color="#0D2A1E", text_color=CLR_SUCCESS,
                              border_color=CLR_SUCCESS)
            else:
                btn.configure(text="🔧  Retry", state="normal")

    def _proceed(self):
        self._on_next(self._results)

    def _skip(self):
        if self._on_skip:
            self._on_skip(self._results)
