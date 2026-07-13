"""Security Tools & Infrastructure — Step 2 of 5.

The business selects which advanced tools / infrastructure apply to them.
Each selection adds an optional scored control (C16-C20) to the assessment.
"""

import ipaddress
import re

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_DANGER, CLR_BORDER,
    FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD,
)
from src.gui.screens.business_info import _header, _nav

# The website/infrastructure tool needs a target to check — the business's
# public domain or IP. We collect it inline on that card so the scan (and the
# certificate/header/port checks) know what to look at.
INFRA_TOOL_ID = "infra_scan"

# RFC-1123 hostname with at least two labels (example.co.zm) — bare words
# like "mywebsite" can't be scanned, so they're rejected with guidance.
_HOST_RE = re.compile(
    r"^(?=.{1,253}$)"
    r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?"
    r"(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$")


def _normalise_target(raw: str) -> str:
    """Reduce whatever the owner pastes to a bare hostname or IP.

    Business owners paste full URLs ("https://example.co.zm/shop?x=1"),
    host:port pairs, or add stray spaces/trailing dots — accept all of it
    rather than bouncing them back with an error.
    """
    t = (raw or "").strip()
    if "://" in t:
        t = t.split("://", 1)[1]
    t = t.split("/", 1)[0].split("?", 1)[0]
    if "@" in t:                       # user:pass@host
        t = t.rsplit("@", 1)[1]
    host, sep, port = t.partition(":")
    if sep and port.isdigit():         # host:port (IPv6 has more colons)
        t = host
    return t.strip().strip(".").lower()


def _is_valid_target(target: str) -> bool:
    """True when the normalised target is an IP address or a dotted hostname."""
    try:
        ipaddress.ip_address(target)
        return True
    except ValueError:
        return bool(_HOST_RE.match(target))


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
        self._infra_target_row = None   # frame revealed when C18 is selected
        self._infra_error = None        # inline validation label
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

        def _refresh(c=card, v=var, col=colour, tid=tool_id):
            c.configure(border_color=col if v.get() else CLR_BORDER)
            if tid == INFRA_TOOL_ID:
                self._toggle_infra_target(v.get())

        # Left accent bar. Height is pinned to 1px so the stripe never
        # inflates the card (an empty CTkFrame otherwise requests its 200px
        # default height, which was pushing later cards off-screen); the
        # sticky="ns" span still stretches it to the card's real height.
        # The infra card has an extra row (the revealed domain/IP field), so
        # the stripe must span it too or it stops short when expanded.
        accent = ctk.CTkFrame(card, fg_color=colour, width=5, height=1,
                              corner_radius=0)
        accent_rows = 4 if tool_id == INFRA_TOOL_ID else 3
        accent.grid(row=0, column=0, rowspan=accent_rows, sticky="ns", pady=0)
        accent.grid_propagate(False)

        # Icon + name row
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=1, sticky="ew", padx=16, pady=(14, 4))
        top.grid_columnconfigure(1, weight=1)

        icon_lbl = ctk.CTkLabel(
            top, text=icon,
            font=("Segoe UI Emoji", 22), text_color=colour, width=34,
        )
        icon_lbl.grid(row=0, column=0, sticky="w")

        name_lbl = ctk.CTkLabel(
            top, text=name,
            font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
        )
        name_lbl.grid(row=0, column=1, padx=(8, 0), sticky="w")

        chip_lbl = ctk.CTkLabel(
            top, text=control_id,
            font=FONT_CAPTION, text_color=colour,
            fg_color=CLR_SURFACE_ALT, corner_radius=6,
            width=36, height=20,
        )
        chip_lbl.grid(row=0, column=2, padx=(0, 0))

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
        desc_lbl = ctk.CTkLabel(
            card, text=desc,
            font=FONT_BODY, text_color=CLR_TEXT_SEC,
            anchor="w", wraplength=780, justify="left",
        )
        desc_lbl.grid(row=1, column=1, sticky="w", padx=16, pady=(0, 4))

        # Impact note
        impact_lbl = ctk.CTkLabel(
            card, text=f"  {impact}",
            font=FONT_SMALL, text_color=CLR_MUTED,
            anchor="w", wraplength=780, justify="left",
        )
        impact_lbl.grid(row=2, column=1, sticky="w", padx=16, pady=(0, 14))

        # The website/infrastructure card carries a target input, hidden until
        # the tool is switched on. Built here so it lives inside the card.
        if tool_id == INFRA_TOOL_ID:
            self._build_infra_target(card)

        # Whole-card click toggles the switch. The labels must be bound too:
        # they cover almost all of the card's surface, so binding only the
        # frames left clicks on the visible text doing nothing.
        clickable = (card, top, icon_lbl, name_lbl, chip_lbl,
                     desc_lbl, impact_lbl)
        for widget in clickable:
            widget.bind("<Button-1>",
                        lambda e, v=var, r=_refresh: (v.set(not v.get()), r()))

    # ---------------------------------------------------------- infra target
    def _build_infra_target(self, card):
        """Domain / IP entry, revealed only when the website tool is on."""
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.grid_columnconfigure(0, weight=1)
        # Kept out of the grid until the toggle is turned on.
        self._infra_target_row = row

        ctk.CTkLabel(
            row, text="Website domain or IP address to check",
            font=FONT_SMALL, text_color=CLR_TEXT_SEC, anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        # No textvariable: CTkEntry suppresses its placeholder whenever a
        # textvariable is attached (the "e.g. …" hint never rendered), so the
        # value is read with entry.get() at submit time instead.
        entry = ctk.CTkEntry(
            row,
            placeholder_text="e.g. example.co.zm  or  41.72.10.5",
            height=34, border_color=CLR_BORDER,
        )
        entry.grid(row=1, column=0, sticky="ew")
        self._infra_entry = entry
        # Typing clears any prior validation error.
        entry.bind("<KeyRelease>", lambda e: self._clear_infra_error())

        self._infra_error = ctk.CTkLabel(
            row, text="", font=FONT_SMALL, text_color=CLR_DANGER, anchor="w",
        )
        self._infra_error.grid(row=2, column=0, sticky="w", pady=(4, 0))

    def _clear_infra_error(self):
        """Drop the validation message once the operator starts typing."""
        if self._infra_error is not None:
            self._infra_error.configure(text="")
        if getattr(self, "_infra_entry", None) is not None:
            self._infra_entry.configure(border_color=CLR_BORDER)

    def _toggle_infra_target(self, show: bool):
        """Show or hide the domain/IP entry as the C18 toggle flips."""
        if self._infra_target_row is None:
            return
        if show:
            self._infra_target_row.grid(row=3, column=1, sticky="ew",
                                        padx=16, pady=(0, 14))
            self._infra_entry.focus_set()
        else:
            self._infra_target_row.grid_remove()
            if self._infra_error is not None:
                self._infra_error.configure(text="")

    def _show_infra_error(self, message: str):
        if self._infra_error is not None:
            self._infra_error.configure(text=message)
        if getattr(self, "_infra_entry", None) is not None:
            self._infra_entry.configure(border_color=CLR_DANGER)
            self._infra_entry.focus_set()

    # ------------------------------------------------------------------ submit
    def _submit(self):
        selected = {tid for tid, v in self._vars.items() if v.get()}

        # If the website/infrastructure tool is on, a scannable domain or IP
        # is required — there's nothing to check without one.
        target = ""
        if INFRA_TOOL_ID in selected:
            target = _normalise_target(self._infra_entry.get())
            if not target:
                self._show_infra_error(
                    "Enter the domain or IP address you want checked.")
                return
            if not _is_valid_target(target):
                self._show_infra_error(
                    "That doesn't look like a domain or IP address — "
                    "try something like example.co.zm or 41.72.10.5.")
                return
            # Reflect the cleaned-up value (scheme/path stripped) so the
            # owner sees exactly what will be checked.
            if target != self._infra_entry.get():
                self._infra_entry.delete(0, "end")
                self._infra_entry.insert(0, target)

        self._on_next(selected, target)
