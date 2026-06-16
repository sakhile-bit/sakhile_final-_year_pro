"""Security Tools & Infrastructure — Step 2 of 5.

The business selects which advanced tools / infrastructure apply to them.
Each selection adds an optional scored control (C16-C20) to the assessment.
"""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_SURFACE_HVR,
    CLR_ACCENT, CLR_ACCENT_HOV,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_BORDER,
    FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, NAV_H, BTN_H, BTN_R,
)
from src.gui.screens.business_info import _header, _nav

TOOLS = [
    (
        "active_dir",
        "Active Directory",
        "🔐",
        "C16",
        CLR_ACCENT,
        "The business manages user accounts and access through Microsoft Active Directory"
        " (on-premises or Azure AD).",
        "Adds: AD password policies, privileged account management, and stale account review.",
    ),
    (
        "network_scan",
        "Network Architecture Scan",
        "🌐",
        "C17",
        "#2485E8",
        "The business has performed or requires a network scan to map devices,"
        " detect rogue systems, and review exposed ports.",
        "Adds: network device inventory, port exposure review, and segmentation assessment.",
    ),
    (
        "infra_scan",
        "Infrastructure Security Scan",
        "🖥",
        "C18",
        "#5A7490",
        "The business has public-facing services (website, email, APIs) that need"
        " SSL certificate, security-header, and port-exposure checks.",
        "Adds: SSL/TLS validity, HTTP security headers, and risky-port exposure.",
    ),
    (
        "zambia_risk",
        "Zambia Local Threat Assessment",
        "🇿🇲",
        "C19",
        "#F0A500",
        "The business wants to assess exposure to Zambia-specific threats such as SIM swap"
        " fraud, mobile money scams, WhatsApp phishing, and local regulatory compliance.",
        "Adds: mobile-money controls, local-threat training, and Data Protection Act compliance.",
    ),
    (
        "remediation",
        "Remediation Process",
        "🔧",
        "C20",
        CLR_SUCCESS,
        "The business actively tracks and remediates identified security findings with"
        " assigned owners and defined SLAs.",
        "Adds: finding-tracking, SLA adherence, and evidence of completed remediations.",
    ),
]


class ToolsProfileScreen(ctk.CTkFrame):

    def __init__(self, master, on_next, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_next = on_next
        self._on_back = on_back
        self._vars: dict[str, ctk.BooleanVar] = {}
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        _header(self, "Security Tools & Infrastructure", "2 of 5", 0.25)

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=(PAD, 0))
        scroll.grid_columnconfigure(0, weight=1)

        intro = ctk.CTkLabel(
            scroll,
            text=(
                "Select every tool or infrastructure that applies to your business.\n"
                "Each selection adds an additional scored control to your certification."
            ),
            font=FONT_BODY,
            text_color=CLR_TEXT_SEC,
            justify="left",
            wraplength=860,
            anchor="w",
        )
        intro.grid(row=0, column=0, sticky="w", pady=(0, PAD))

        for idx, (tool_id, name, icon, control_id, colour, desc, impact) in enumerate(TOOLS):
            var = ctk.BooleanVar(value=False)
            self._vars[tool_id] = var
            self._build_card(scroll, idx + 1, tool_id, name, icon,
                             control_id, colour, desc, impact, var)

        _nav(self, self._on_back, "Next: Automated Scan  →", self._submit)

    # ------------------------------------------------------------------ card
    def _build_card(self, parent, row, tool_id, name, icon,
                    control_id, colour, desc, impact, var):
        card = ctk.CTkFrame(
            parent, fg_color=CLR_SURFACE, corner_radius=12,
            border_width=2, border_color=CLR_BORDER,
        )
        card.grid(row=row, column=0, sticky="ew", pady=6)
        card.grid_columnconfigure(1, weight=1)

        def _refresh(c=card, v=var, col=colour):
            c.configure(border_color=col if v.get() else CLR_BORDER)

        # Left accent bar
        accent = ctk.CTkFrame(card, fg_color=colour, width=5, corner_radius=0)
        accent.grid(row=0, column=0, rowspan=3, sticky="ns", pady=0)
        accent.grid_propagate(False)

        # Icon + name row
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=1, sticky="ew", padx=16, pady=(14, 4))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top, text=icon,
            font=("Segoe UI Emoji", 22), text_color=colour, width=34,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            top, text=name,
            font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
        ).grid(row=0, column=1, padx=(8, 0), sticky="w")

        ctk.CTkLabel(
            top, text=control_id,
            font=FONT_CAPTION, text_color=colour,
            fg_color=CLR_SURFACE_ALT, corner_radius=6,
            width=36, height=20,
        ).grid(row=0, column=2, padx=(0, 0))

        # Toggle switch (right-aligned)
        switch = ctk.CTkSwitch(
            top, variable=var, text="",
            onvalue=True, offvalue=False,
            fg_color=CLR_BORDER, progress_color=colour,
            command=_refresh,
            width=44, height=22,
        )
        switch.grid(row=0, column=3, padx=(12, 0))

        # Description
        ctk.CTkLabel(
            card, text=desc,
            font=FONT_BODY, text_color=CLR_TEXT_SEC,
            anchor="w", wraplength=780, justify="left",
        ).grid(row=1, column=1, sticky="w", padx=16, pady=(0, 4))

        # Impact note
        ctk.CTkLabel(
            card, text=f"  {impact}",
            font=FONT_SMALL, text_color=CLR_MUTED,
            anchor="w", wraplength=780, justify="left",
        ).grid(row=2, column=1, sticky="w", padx=16, pady=(0, 14))

        # Whole-card click toggles the switch
        for widget in (card, top):
            widget.bind("<Button-1>", lambda e, v=var, r=_refresh: [v.set(not v.get()), r()])

    # ------------------------------------------------------------------ submit
    def _submit(self):
        selected = {tid for tid, v in self._vars.items() if v.get()}
        self._on_next(selected)
