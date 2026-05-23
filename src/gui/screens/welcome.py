"""Welcome / home screen — two-column professional layout."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BRAND, CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_SURFACE_HVR,
    CLR_ACCENT, CLR_ACCENT_HOV, CLR_ACCENT_DIM,
    CLR_BLUE, CLR_BLUE_DIM, CLR_AMBER, CLR_AMBER_DIM,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED, CLR_BORDER, CLR_DIVIDER,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER,
    FONT_DISPLAY, FONT_SUBHEAD, FONT_SUBTITLE, FONT_SMALL, FONT_CAPTION,
    PAD_LG, BTN_H_LG, BTN_R, APP_NAME, APP_VERSION,
    TIER_COLOURS,
)


TIER_ICON = {"GOLD": "🥇", "SILVER": "🥈", "BRONZE": "🥉", "NOT CERTIFIED": "✕"}


class WelcomeScreen(ctk.CTkFrame):

    def __init__(self, master, on_start, on_history=None, on_infra=None,
                 on_zambia_risk=None, on_policies=None,
                 on_network=None, on_deploy=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_start = on_start
        self._on_history = on_history or (lambda: None)
        self._on_infra = on_infra or (lambda: None)
        self._on_zambia_risk = on_zambia_risk or (lambda: None)
        self._on_policies = on_policies or (lambda: None)
        self._on_network = on_network or (lambda: None)
        self._on_deploy = on_deploy or (lambda: None)
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=0)   # left brand panel — fixed
        self.grid_columnconfigure(1, weight=1)   # right action panel — grows
        self.grid_rowconfigure(0, weight=1)

        self._build_left()
        self._build_right()

    # ── Left brand panel ───────────────────────────────────────────────────
    def _build_left(self):
        left = ctk.CTkFrame(self, fg_color=CLR_BRAND, corner_radius=0,
                            width=290)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(8, weight=1)   # push bottom content down

        # Green top edge stripe
        ctk.CTkFrame(left, fg_color=CLR_ACCENT, height=3,
                     corner_radius=0).grid(row=0, column=0, sticky="ew")

        # Shield mark
        ctk.CTkLabel(left, text="🛡",
                     font=("Segoe UI Emoji", 48), text_color=CLR_ACCENT,
                     ).grid(row=1, column=0, pady=(36, 12))

        # Program name
        ctk.CTkLabel(left,
                     text="Zambia\nDigital Hygiene\nCertification",
                     font=("Segoe UI", 16, "bold"), text_color=CLR_TEXT,
                     justify="left",
                     ).grid(row=2, column=0, padx=28, sticky="w")

        ctk.CTkLabel(left, text="Program",
                     font=("Segoe UI", 13), text_color=CLR_ACCENT,
                     justify="left",
                     ).grid(row=3, column=0, padx=28, pady=(0, 16), sticky="w")

        # Divider
        ctk.CTkFrame(left, fg_color=CLR_BORDER, height=1,
                     corner_radius=0).grid(row=4, column=0,
                                           padx=28, sticky="ew")

        # Key stats
        stats_frame = ctk.CTkFrame(left, fg_color="transparent")
        stats_frame.grid(row=5, column=0, padx=28, pady=20, sticky="ew")
        stats_frame.grid_columnconfigure(0, weight=1)

        stats = [
            ("15", "Security Controls", CLR_ACCENT),
            ("3",  "Certification Tiers", CLR_AMBER),
            ("120", "Max Score Points", CLR_BLUE),
        ]
        for i, (num, label, clr) in enumerate(stats):
            cell = ctk.CTkFrame(stats_frame, fg_color=CLR_SURFACE,
                                corner_radius=10, border_width=1,
                                border_color=CLR_BORDER)
            cell.grid(row=i, column=0, pady=5, sticky="ew")
            cell.grid_columnconfigure(1, weight=1)

            ctk.CTkFrame(cell, fg_color=clr, width=4,
                         corner_radius=2).grid(row=0, column=0,
                                               sticky="ns", padx=(6, 0),
                                               pady=8)
            ctk.CTkLabel(cell, text=num,
                         font=("Segoe UI", 20, "bold"), text_color=clr,
                         width=44, anchor="e",
                         ).grid(row=0, column=1, padx=(10, 6), pady=10)
            ctk.CTkLabel(cell, text=label, font=FONT_CAPTION,
                         text_color=CLR_MUTED, anchor="w",
                         ).grid(row=0, column=2, padx=(0, 10), sticky="w")

        # Frameworks
        ctk.CTkFrame(left, fg_color=CLR_BORDER, height=1,
                     corner_radius=0).grid(row=6, column=0,
                                           padx=28, sticky="ew")

        ctk.CTkLabel(left,
                     text="NIST CSF  ·  CIS Controls v8\n"
                          "ISO 27001  ·  Zambia DPA 2021",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     justify="center",
                     ).grid(row=7, column=0, padx=28, pady=(14, 0))

        # Spacer + UNZA footer
        ctk.CTkLabel(left,
                     text=f"v{APP_VERSION}  ·  University of Zambia",
                     font=("Segoe UI", 9), text_color="#2A4060",
                     ).grid(row=9, column=0, padx=28, pady=(0, 18), sticky="s")

    # ── Right action panel ─────────────────────────────────────────────────
    def _build_right(self):
        right = ctk.CTkFrame(self, fg_color=CLR_BG, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=0)

        # Centre content vertically
        inner = ctk.CTkFrame(right, fg_color="transparent")
        inner.grid(row=0, column=0, padx=PAD_LG, pady=PAD_LG, sticky="nsew")
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_rowconfigure(0, weight=1)
        inner.grid_rowconfigure(99, weight=1)

        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew")
        content.grid_columnconfigure(0, weight=1)

        # Heading
        ctk.CTkLabel(content,
                     text="Your Digital Hygiene Dashboard",
                     font=FONT_DISPLAY, text_color=CLR_TEXT, anchor="w",
                     ).grid(row=0, column=0, pady=(0, 4), sticky="w")

        ctk.CTkLabel(content,
                     text="Assess, remediate and certify your business "
                          "cybersecurity posture",
                     font=FONT_SUBTITLE, text_color=CLR_MUTED, anchor="w",
                     ).grid(row=1, column=0, pady=(0, 20), sticky="w")

        # Last assessment card (if available)
        self._build_last_assessment(content, row=2)

        # Divider
        ctk.CTkFrame(content, fg_color=CLR_DIVIDER, height=1,
                     corner_radius=0).grid(row=3, column=0,
                                           pady=18, sticky="ew")

        # Primary CTA
        ctk.CTkButton(
            content,
            text="  ▶   Start New Assessment",
            font=("Segoe UI", 14, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#000000", command=self._on_start,
            height=BTN_H_LG, corner_radius=BTN_R,
        ).grid(row=4, column=0, pady=(0, 14), sticky="ew")

        # Reminder banner
        self._build_reminder(content, row=5)

        # Tool grid (2 × 2)
        self._build_tools(content, row=6)

        # Footer
        ctk.CTkLabel(right,
                     text=f"{APP_NAME}  ·  Dept. of Computing & Informatics, UNZA",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=1, column=0, pady=(0, 10))

    def _build_last_assessment(self, parent, row):
        from src.utils.local_db import list_assessments
        try:
            rows = list_assessments(limit=1)
        except Exception:
            rows = []

        if not rows:
            # Show feature pills instead
            feat = ctk.CTkFrame(parent, fg_color="transparent")
            feat.grid(row=row, column=0, sticky="ew")
            feat.grid_columnconfigure((0, 1), weight=1)
            items = [
                ("🔧", "One-click auto-remediation", CLR_ACCENT),
                ("🏅", "Gold / Silver / Bronze cert", CLR_AMBER),
                ("🔍", "Infrastructure web scanner", CLR_BLUE),
                ("📄", "Policy template library", "#CD8A3A"),
            ]
            for i, (icon, txt, clr) in enumerate(items):
                pill = ctk.CTkFrame(feat, fg_color=CLR_SURFACE,
                                    corner_radius=10, border_width=1,
                                    border_color=CLR_BORDER)
                pill.grid(row=i // 2, column=i % 2,
                          padx=4, pady=4, sticky="ew")
                pill.grid_columnconfigure(1, weight=1)
                ctk.CTkFrame(pill, fg_color=clr, width=3,
                             corner_radius=0).grid(row=0, column=0,
                                                   sticky="ns", pady=0)
                ctk.CTkLabel(pill, text=icon,
                             font=("Segoe UI Emoji", 14),
                             text_color=clr, width=30,
                             ).grid(row=0, column=1, padx=(8, 4), pady=10)
                ctk.CTkLabel(pill, text=txt, font=FONT_SMALL,
                             text_color=CLR_TEXT_SEC, anchor="w",
                             ).grid(row=0, column=2, padx=(0, 10), sticky="w")
            return

        r = rows[0]
        tier = r["tier"]
        tier_clr = TIER_COLOURS.get(tier, CLR_DANGER)

        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=14,
                            border_width=1, border_color=CLR_BORDER)
        card.grid(row=row, column=0, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # Left tier stripe
        ctk.CTkFrame(card, fg_color=tier_clr, width=5,
                     corner_radius=0).grid(row=0, column=0,
                                           rowspan=3, sticky="ns",
                                           padx=(0, 0), pady=0)

        ctk.CTkLabel(card,
                     text="Last Assessment",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=0, column=1, padx=14, pady=(12, 2), sticky="w")

        ctk.CTkLabel(card, text=r["biz_name"],
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).grid(row=1, column=1, padx=14, sticky="w")

        meta = f"{r.get('saved_at', '')[:10]}  ·  {r.get('industry', '')}"
        ctk.CTkLabel(card, text=meta, font=FONT_CAPTION,
                     text_color=CLR_MUTED,
                     ).grid(row=2, column=1, padx=14, pady=(0, 12), sticky="w")

        # Score pill
        ctk.CTkLabel(card,
                     text=f"{TIER_ICON.get(tier, '')}  {r['pct']}%  {tier}",
                     font=("Segoe UI", 11, "bold"), text_color=tier_clr,
                     fg_color=CLR_SURFACE_ALT, corner_radius=10,
                     width=130, height=28,
                     ).grid(row=0, column=2, rowspan=3, padx=(0, 14))

    def _build_reminder(self, parent, row):
        try:
            from src.utils.local_db import get_reassessment_date
            import datetime
            due = get_reassessment_date()
            if due:
                days = (due - datetime.date.today()).days
                if days <= 30:
                    clr = CLR_WARNING if days > 0 else CLR_DANGER
                    msg = (f"⏰  Reassessment due in {days} day(s) — "
                           f"{due.strftime('%d %b %Y')}"
                           if days > 0
                           else "🔴  Reassessment overdue — please re-assess now")
                    b = ctk.CTkFrame(parent, fg_color=CLR_SURFACE,
                                     corner_radius=10, border_width=1,
                                     border_color=clr)
                    b.grid(row=row, column=0, pady=(0, 10), sticky="ew")
                    ctk.CTkLabel(b, text=msg,
                                 font=("Segoe UI", 11, "bold"),
                                 text_color=clr,
                                 ).grid(padx=14, pady=8)
                    return
        except Exception:
            pass

    def _build_tools(self, parent, row):
        from src.utils.local_db import assessment_count
        try:
            count = assessment_count()
        except Exception:
            count = 0

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.grid(row=row, column=0, sticky="ew")
        grid.grid_columnconfigure((0, 1, 2), weight=1)

        tools = [
            (f"📋  History{' (' + str(count) + ')' if count else ''}",
             CLR_ACCENT,  CLR_ACCENT_DIM, self._on_history,      0, 0),
            ("🌐  Network Scan",
             "#00B0D0",   "#001A20",      self._on_network,       0, 1),
            ("🔍  Infra Scan",
             CLR_BLUE,    CLR_BLUE_DIM,   self._on_infra,         0, 2),
            ("🇿🇲  Zambia Risk",
             CLR_AMBER,   CLR_AMBER_DIM,  self._on_zambia_risk,   1, 0),
            ("📄  Policy Docs",
             "#CD8A3A",   "#1A0E00",      self._on_policies,      1, 1),
            ("🚀  Deploy Check",
             CLR_SUCCESS, "#1A1730",      self._on_deploy,        1, 2),
        ]
        for label, clr, hov, cmd, r, c in tools:
            btn = ctk.CTkFrame(grid, fg_color=CLR_SURFACE, corner_radius=12,
                               border_width=1, border_color=CLR_BORDER)
            btn.grid(row=r, column=c, padx=4, pady=4, sticky="ew")
            btn.grid_columnconfigure(0, weight=1)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(
                fg_color=CLR_SURFACE_HVR))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(
                fg_color=CLR_SURFACE))
            ctk.CTkButton(
                btn, text=label, font=FONT_SMALL,
                fg_color="transparent", hover_color=CLR_SURFACE_HVR,
                text_color=clr, height=36, corner_radius=10,
                anchor="w", command=cmd,
            ).grid(row=0, column=0, padx=6, pady=2, sticky="ew")
