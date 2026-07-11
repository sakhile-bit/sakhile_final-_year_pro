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

# Each tool: (id, name, icon, control_id, colour, description, impact).
# Descriptions are written for a non-technical business owner — plain
# language first, with any technical term explained in everyday words.
TOOLS = [
    (
        "active_dir",
        "Staff Logins & Accounts",
        "🔐",
        "C16",
        CLR_ACCENT,
        "Choose this if your staff sign in to shared computers or systems with"
        " company usernames and passwords managed in one place (often called"
        " \"Active Directory\" or a Microsoft 365 / Azure work account).",
        "We'll check: strong password rules, that only the right people have"
        " admin access, and that accounts of staff who leave are closed promptly.",
    ),
    (
        "network_scan",
        "Your Office Network",
        "🌐",
        "C17",
        "#2485E8",
        "Choose this if you have an office network (Wi-Fi and cables connecting"
        " your computers, printers, and other devices) that you'd like checked"
        " for unknown or unsafe devices.",
        "We'll check: a list of every device on your network, that guest Wi-Fi"
        " is kept separate from business systems, and that nothing risky is"
        " left open to the internet.",
    ),
    (
        "infra_scan",
        "Your Website & Online Services",
        "🖥",
        "C18",
        "#5A7490",
        "Choose this if your business has a website, online store, or email"
        " system that customers or staff reach over the internet.",
        "We'll check: that your website's security padlock (the certificate) is"
        " valid, that basic web protections are switched on, and that no unsafe"
        " doors are left open for attackers.",
    ),
    (
        "zambia_risk",
        "Local Zambian Threats",
        "🇿🇲",
        "C19",
        "#F0A500",
        "Choose this to check how well protected you are against scams common in"
        " Zambia — SIM-swap fraud, mobile-money theft, and WhatsApp phishing —"
        " and against local data-protection law.",
        "We'll check: mobile-money account safeguards, staff awareness of local"
        " scams, and whether you meet the Zambia Data Protection Act.",
    ),
    (
        "remediation",
        "Fixing Security Problems",
        "🔧",
        "C20",
        CLR_SUCCESS,
        "Choose this if your business keeps track of security problems once they"
        " are found and makes sure someone is responsible for fixing them.",
        "We'll check: that problems are written down with an owner and a"
        " deadline, and that the serious ones actually get fixed on time.",
    ),
    (
        "fleet_scan",
        "Multiple Computers or Branches",
        "🖧",
        "C21",
        "#00BCD4",
        "Choose this if your business runs several computers or servers — for"
        " example across different branches — and you want them all checked"
        " together, not one at a time.",
        "We'll check: that every machine is accounted for, that they're all"
        " scanned regularly, and that the weakest machine is brought up to"
        " standard (a business is only as safe as its least-protected computer).",
    ),
    (
        "server_hardening",
        "Business Servers",
        "🛡",
        "C22",
        "#4CAF50",
        "Choose this if you run one or more servers — the always-on computers"
        " that store shared files, run your website, or hold company data.",
        "We'll check: that servers are set up securely rather than left on"
        " default settings, that old risky features are switched off, and that"
        " security updates are installed promptly.",
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

        # Left accent bar. Height is pinned to 1px so the stripe never
        # inflates the card (an empty CTkFrame otherwise requests its 200px
        # default height, which was pushing later cards off-screen); the
        # sticky="ns" span still stretches it to the card's real height.
        accent = ctk.CTkFrame(card, fg_color=colour, width=5, height=1,
                              corner_radius=0)
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
