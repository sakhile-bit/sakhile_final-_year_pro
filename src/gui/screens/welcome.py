"""Welcome / home screen."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_ACCENT_HOV, CLR_BLUE, CLR_AMBER,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED, CLR_BORDER, CLR_DIVIDER, CLR_WARNING,
    FONT_DISPLAY, FONT_SUBTITLE, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, PAD_LG, BTN_H_LG, BTN_R, APP_NAME, APP_VERSION,
)


def _rule(parent, row):
    ctk.CTkFrame(parent, fg_color=CLR_DIVIDER, height=1,
                 corner_radius=0).grid(row=row, column=0, sticky="ew",
                                       padx=PAD_LG)


class WelcomeScreen(ctk.CTkFrame):
    """Home screen — entry point to all app features."""

    def __init__(self, master, on_start, on_history=None, on_infra=None,
                 on_zambia_risk=None, on_policies=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_start = on_start
        self._on_history = on_history or (lambda: None)
        self._on_infra = on_infra or (lambda: None)
        self._on_zambia_risk = on_zambia_risk or (lambda: None)
        self._on_policies = on_policies or (lambda: None)
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # ── main card ─────────────────────────────────────────────
        card = ctk.CTkFrame(
            self, fg_color=CLR_SURFACE,
            corner_radius=20, border_width=1, border_color=CLR_BORDER,
        )
        card.grid(row=0, column=0, padx=110, pady=32, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        # Green top stripe
        ctk.CTkFrame(card, fg_color=CLR_ACCENT, height=4,
                     corner_radius=0).grid(row=0, column=0, sticky="ew")

        # Shield + branding
        ctk.CTkLabel(
            card, text="🛡",
            font=("Segoe UI Emoji", 52), text_color=CLR_ACCENT,
        ).grid(row=1, column=0, pady=(26, 6))

        ctk.CTkLabel(
            card,
            text="Zambia Digital Hygiene\nCertification Program",
            font=FONT_DISPLAY, text_color=CLR_TEXT, justify="center",
        ).grid(row=2, column=0, padx=PAD)

        ctk.CTkLabel(
            card,
            text="Assess your business against 15 cybersecurity controls  ·  "
                 "Fix issues automatically  ·  Earn your certification",
            font=FONT_SUBTITLE, text_color=CLR_MUTED, justify="center",
        ).grid(row=3, column=0, padx=PAD_LG, pady=(6, 18))

        _rule(card, 4)

        # ── Feature highlights ────────────────────────────────────
        feat = ctk.CTkFrame(card, fg_color="transparent")
        feat.grid(row=5, column=0, padx=PAD_LG, pady=14, sticky="ew")
        feat.grid_columnconfigure((0, 1), weight=1)

        rows = [
            ("✅", "5 Automated Windows Checks",  "🔧", "One-Click Auto-Remediation"),
            ("📋", "10 Guided Manual Questions",  "🏅", "Gold / Silver / Bronze Certificate"),
        ]
        for r, (i1, t1, i2, t2) in enumerate(rows):
            for col, (icon, txt) in enumerate([(i1, t1), (i2, t2)]):
                f = ctk.CTkFrame(feat, fg_color="transparent")
                f.grid(row=r, column=col, padx=8, pady=4, sticky="w")
                ctk.CTkLabel(f, text=icon, font=("Segoe UI Emoji", 15),
                             text_color=CLR_ACCENT, width=26).pack(side="left")
                ctk.CTkLabel(f, text=txt, font=FONT_BODY,
                             text_color=CLR_TEXT_SEC).pack(side="left", padx=(6, 0))

        _rule(card, 6)

        # ── Reassessment banner (shown when due within 30 days) ───
        self._show_reminder(card, row=7)

        # ── Primary CTA ───────────────────────────────────────────
        ctk.CTkButton(
            card, text="▶   Start New Assessment",
            font=("Segoe UI", 14, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#000000", command=self._on_start,
            height=BTN_H_LG, corner_radius=BTN_R,
        ).grid(row=8, column=0, padx=PAD_LG, pady=(18, 10), sticky="ew")

        # ── Secondary tools row ───────────────────────────────────
        tools = ctk.CTkFrame(card, fg_color="transparent")
        tools.grid(row=9, column=0, padx=PAD_LG, pady=(0, 24))

        from src.utils.local_db import assessment_count
        try:
            count = assessment_count()
        except Exception:
            count = 0

        sec_btns = [
            (f"📋  History{' (' + str(count) + ')' if count else ''}",
             CLR_ACCENT, "#003D28", self._on_history),
            ("🔍  Infra Scan",   CLR_BLUE,    "#0A1520", self._on_infra),
            ("🇿🇲  Zambia Risk",  CLR_AMBER,   "#1A1200", self._on_zambia_risk),
            ("📄  Policy Docs",  "#CD8A3A",   "#1A0E00", self._on_policies),
        ]
        for col, (label, clr, hov, cmd) in enumerate(sec_btns):
            ctk.CTkButton(
                tools, text=label, font=FONT_SMALL,
                fg_color="transparent", border_color=clr, border_width=1,
                text_color=clr, hover_color=hov,
                height=34, corner_radius=17, command=cmd,
            ).grid(row=0, column=col, padx=4)

        # ── Footer ────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text=f"{APP_NAME}  ·  v{APP_VERSION}  ·  "
                 "University of Zambia, Dept. of Computing & Informatics",
            font=FONT_CAPTION, text_color=CLR_MUTED,
        ).grid(row=1, column=0, pady=(0, 10))

    def _show_reminder(self, parent, row: int):
        try:
            from src.utils.local_db import get_reassessment_date
            import datetime
            due = get_reassessment_date()
            if due:
                days_left = (due - datetime.date.today()).days
                if days_left <= 30:
                    clr = CLR_WARNING if days_left > 0 else "#E84040"
                    msg = (f"⏰  Next reassessment due in {days_left} day(s) — "
                           f"{due.strftime('%d %b %Y')}"
                           if days_left > 0
                           else f"🔴  Reassessment overdue since "
                                f"{due.strftime('%d %b %Y')} — please re-assess now")
                    b = ctk.CTkFrame(parent, fg_color=CLR_SURFACE_ALT,
                                     corner_radius=10, border_width=1,
                                     border_color=clr)
                    b.grid(row=row, column=0, padx=PAD_LG,
                           pady=(14, 0), sticky="ew")
                    ctk.CTkLabel(b, text=msg,
                                 font=("Segoe UI", 11, "bold"),
                                 text_color=clr).grid(padx=14, pady=8)
                    return
        except Exception:
            pass
        ctk.CTkFrame(parent, fg_color="transparent",
                     height=2).grid(row=row, column=0)
