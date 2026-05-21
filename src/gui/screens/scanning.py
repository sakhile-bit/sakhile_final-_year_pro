"""Automated scanning screen — runs C01-C05 in a background thread."""

import threading
import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_ACCENT, CLR_TEXT, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, PAD,
)

CHECKS = [
    ("C01", "Operating System Updates"),
    ("C02", "Antivirus Protection"),
    ("C03", "Firewall Configuration"),
    ("C04", "Password Policy"),
    ("C05", "Backup System"),
]

STATUS_ICON = {
    "PASS":         ("✔", CLR_SUCCESS),
    "WARNING":      ("⚠", CLR_WARNING),
    "FAIL":         ("✖", CLR_DANGER),
    "ERROR":        ("!", CLR_WARNING),
    "NOT_ASSESSED": ("–", CLR_MUTED),
    "pending":      ("…", CLR_MUTED),
}


class ScanningScreen(ctk.CTkFrame):
    """Runs automated checks C01-C05 with live progress display."""

    def __init__(self, master, business_info, on_next, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._biz = business_info
        self._on_next = on_next
        self._on_back = on_back
        self._results = {}
        self._done = False
        self._build()
        # Start scan automatically
        threading.Thread(target=self._run_scan, daemon=True).start()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=84)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        hdr.grid_columnconfigure(1, weight=0)
        ctk.CTkLabel(
            hdr, text="Automated Security Checks",
            font=FONT_HEADING, text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=PAD, pady=(16, 6), sticky="w")
        ctk.CTkLabel(
            hdr, text="Step 2 of 4",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(row=0, column=1, padx=PAD, pady=(16, 6), sticky="e")
        progress = ctk.CTkProgressBar(
            hdr, fg_color=CLR_BG, progress_color=CLR_ACCENT,
            corner_radius=6, height=10,
        )
        progress.set(0.5)
        progress.grid(row=1, column=0, columnspan=2, sticky="ew", padx=PAD, pady=(0, 16))

        body = ctk.CTkFrame(self, fg_color=CLR_BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew", padx=PAD*2, pady=PAD)
        body.grid_columnconfigure(0, weight=1)

        info_card = ctk.CTkFrame(body, fg_color=CLR_SURFACE, corner_radius=18, border_width=1, border_color=CLR_BORDER)
        info_card.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        info_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            info_card,
            text="The desktop assessment runs a small suite of Windows security checks and preserves your results locally.",
            font=FONT_BODY, text_color=CLR_MUTED, wraplength=760, justify="left",
        ).grid(row=0, column=0, padx=PAD, pady=PAD)

        self._progress = ctk.CTkProgressBar(
            body, fg_color=CLR_SURFACE, progress_color=CLR_ACCENT,
            height=14, corner_radius=7,
        )
        self._progress.set(0)
        self._progress.grid(row=1, column=0, sticky="ew", pady=(0, 22))

        self._check_rows = {}
        for i, (cid, cname) in enumerate(CHECKS):
            row_frame = ctk.CTkFrame(body, fg_color=CLR_SURFACE, corner_radius=14, border_width=1, border_color=CLR_BORDER, height=64)
            row_frame.grid(row=i + 2, column=0, sticky="ew", pady=6)
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_propagate(False)

            icon_lbl = ctk.CTkLabel(
                row_frame, text="…", font=("Segoe UI Emoji", 18),
                text_color=CLR_MUTED, width=36,
            )
            icon_lbl.grid(row=0, column=0, padx=(14, 8), pady=16)

            name_lbl = ctk.CTkLabel(
                row_frame,
                text=f"{cid}  {cname}",
                font=FONT_BODY, text_color=CLR_TEXT, anchor="w",
            )
            name_lbl.grid(row=0, column=1, sticky="w")

            detail_lbl = ctk.CTkLabel(
                row_frame, text="Pending…",
                font=FONT_SMALL, text_color=CLR_MUTED, anchor="e",
            )
            detail_lbl.grid(row=0, column=2, padx=14, sticky="e")

            self._check_rows[cid] = (icon_lbl, name_lbl, detail_lbl)

        self._status_var = ctk.StringVar(value="Preparing automated checks...")
        ctk.CTkLabel(
            body, textvariable=self._status_var,
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(row=len(CHECKS) + 2, column=0, pady=(12, 0), sticky="w")

        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=64)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)

        back_btn = ctk.CTkButton(
            nav, text="← Back", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_MUTED, border_width=1,
            text_color=CLR_TEXT, hover_color="#243447", width=110, height=38,
            command=self._on_back,
        )
        back_btn.grid(row=0, column=0, padx=PAD, pady=14)

        self._next_btn = ctk.CTkButton(
            nav, text="Next: Manual Questions →",
            font=("Segoe UI", 13, "bold"),
            fg_color=CLR_ACCENT, hover_color="#00A87A",
            text_color="#000000", height=38, corner_radius=18,
            state="disabled", command=self._proceed,
        )
        self._next_btn.grid(row=0, column=2, padx=PAD, pady=14)

    # ------------------------------------------------------------------ scan
    def _run_scan(self):
        from src.security.assessment.assessor import DigitalHygieneAssessor

        assessor = DigitalHygieneAssessor(self._biz, assessment_tier="automated")
        # Run each check individually for live feedback
        check_methods = [
            ("C01", assessor._check_os_updates),
            ("C02", assessor._check_antivirus),
            ("C03", assessor._check_firewall),
            ("C04", assessor._check_password_policy),
            ("C05", assessor._check_backup_system),
        ]

        for idx, (cid, method) in enumerate(check_methods):
            self.after(0, self._status_var.set, f"Checking {cid}…")
            try:
                result = method()
            except Exception as exc:
                from src.security.assessment.assessor import ControlResult, CONTROL_CATALOGUE
                cat_key = next(k for k in CONTROL_CATALOGUE if CONTROL_CATALOGUE[k]["id"] == cid)
                ctrl = CONTROL_CATALOGUE[cat_key]
                result = ControlResult(
                    control_id=cid, name=ctrl["name"],
                    score=0, weight=ctrl["weight"],
                    status="ERROR", details=str(exc),
                )

            self._results[cid] = result
            progress = (idx + 1) / len(CHECKS)
            self.after(0, self._update_row, cid, result, progress)

        self.after(0, self._scan_complete)

    def _update_row(self, cid, result, progress):
        icon_lbl, name_lbl, detail_lbl = self._check_rows[cid]
        icon_txt, icon_clr = STATUS_ICON.get(result.status, ("?", CLR_MUTED))
        icon_lbl.configure(text=icon_txt, text_color=icon_clr)
        short = result.details[:60] + "…" if len(result.details) > 60 else result.details
        detail_lbl.configure(
            text=f"{result.score}/{result.weight}  {short}",
            text_color=icon_clr,
        )
        self._progress.set(progress)

    def _scan_complete(self):
        self._done = True
        self._status_var.set("✔  Automated checks complete.")
        self._next_btn.configure(state="normal")

    def _proceed(self):
        self._on_next(self._results)
