"""Active Directory Hygiene screen — AD-specific security checks."""

import customtkinter as ctk

from src.gui.screens.business_info import _header
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_BG,
    CLR_DANGER,
    CLR_MUTED,
    CLR_SURFACE,
    CLR_SURFACE_ALT,
    CLR_SURFACE_HVR,
    CLR_TEXT,
    CLR_TEXT_SEC,
    CLR_WARNING,
    FONT_BODY,
    FONT_SMALL,
    FONT_SUBHEAD,
    NAV_H,
    PAD,
)

# AD security checks mapping
AD_CHECKS = [
    {
        "id": "AD01",
        "title": "Password Policy Configuration",
        "description": "Minimum length 12+ chars, complexity, lockout policy",
        "status": "PENDING",
        "severity": "HIGH",
    },
    {
        "id": "AD02",
        "title": "Privileged Account Management",
        "description": "Built-in admin accounts disabled, separate admin accounts",
        "status": "PENDING",
        "severity": "CRITICAL",
    },
    {
        "id": "AD03",
        "title": "Group Policy Objects (GPO) Security",
        "description": "Verify GPO permissions and access controls",
        "status": "PENDING",
        "severity": "HIGH",
    },
    {
        "id": "AD04",
        "title": "AD Domain Controller Security",
        "description": "DCs patched, hardened, monitored for unauthorized changes",
        "status": "PENDING",
        "severity": "CRITICAL",
    },
    {
        "id": "AD05",
        "title": "User Account Provisioning/Deprovisioning",
        "description": "Timely account removal, inactive account review",
        "status": "PENDING",
        "severity": "MEDIUM",
    },
    {
        "id": "AD06",
        "title": "Group Membership Review",
        "description": "Quarterly verification of group memberships",
        "status": "PENDING",
        "severity": "MEDIUM",
    },
    {
        "id": "AD07",
        "title": "Kerberos Authentication Configuration",
        "description": "Verify Kerberos settings and disable legacy protocols",
        "status": "PENDING",
        "severity": "HIGH",
    },
    {
        "id": "AD08",
        "title": "AD Audit Logging",
        "description": "Enable object access, directory service changes logging",
        "status": "PENDING",
        "severity": "MEDIUM",
    },
    {
        "id": "AD09",
        "title": "Service Accounts Security",
        "description": "Managed service accounts with strong password policies",
        "status": "PENDING",
        "severity": "HIGH",
    },
    {
        "id": "AD10",
        "title": "Domain Trust Verification",
        "description": "Review and validate domain trusts for security",
        "status": "PENDING",
        "severity": "MEDIUM",
    },
]


class ActiveDirectoryScreen(ctk.CTkFrame):
    def __init__(self, master, on_back=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back or (lambda: None)
        self._build()

    def _build(self):
        # Header
        _header(self, "Active Directory Hygiene", "", 0.0)

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=CLR_BG)
        main_frame.pack(fill="both", expand=True, padx=PAD, pady=PAD)
        main_frame.grid_columnconfigure(0, weight=1)

        # Info box
        info_frame = ctk.CTkFrame(main_frame, fg_color=CLR_SURFACE, corner_radius=8)
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        info_frame.grid_columnconfigure(0, weight=1)

        info_label = ctk.CTkLabel(
            info_frame,
            text="🔐 Active Directory Security Assessment\n\nVerify AD infrastructure meets security standards.",
            font=FONT_BODY,
            text_color=CLR_TEXT,
            wraplength=800,
            justify="left",
        )
        info_label.pack(padx=16, pady=12)

        # Scrollable checks list
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.grid(row=1, column=0, sticky="nsew", pady=20)
        scroll_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        for idx, check in enumerate(AD_CHECKS):
            self._build_check_card(scroll_frame, idx, check)

        # Footer with buttons
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=NAV_H)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        btn_run = ctk.CTkButton(
            footer,
            text="▶ Run AD Checks",
            command=self._run_checks,
            fg_color=CLR_ACCENT,
            hover_color=CLR_ACCENT,
            text_color="#ffffff",
            font=FONT_SUBHEAD,
            height=BTN_H,
            corner_radius=BTN_R,
            border_width=0,
        )
        btn_run.pack(side="left", padx=PAD, pady=PAD)

        btn_back = ctk.CTkButton(
            footer,
            text="← Back",
            command=self._on_back,
            fg_color=CLR_SURFACE_ALT,
            hover_color=CLR_SURFACE_HVR,
            text_color=CLR_TEXT,
            font=FONT_SUBHEAD,
            height=BTN_H,
            corner_radius=BTN_R,
            border_width=0,
        )
        btn_back.pack(side="right", padx=PAD, pady=PAD)

    def _build_check_card(self, parent, idx, check):
        """Build a single AD check card."""
        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=8)
        card.grid(row=idx, column=0, sticky="ew", pady=8)
        card.grid_columnconfigure(1, weight=1)

        # Severity icon
        severity_color = {
            "CRITICAL": CLR_DANGER,
            "HIGH": CLR_WARNING,
            "MEDIUM": CLR_ACCENT,
        }.get(check["severity"], CLR_MUTED)

        severity_icon = ctk.CTkLabel(
            card,
            text="⚠" if check["severity"] in ["CRITICAL", "HIGH"] else "ℹ",
            font=("Segoe UI Emoji", 16),
            text_color=severity_color,
        )
        severity_icon.grid(row=0, column=0, padx=12, pady=12, sticky="nw")

        # Content frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=0, column=1, sticky="ew", padx=0, pady=12)
        content.grid_columnconfigure(0, weight=1)

        # Title and ID
        title_frame = ctk.CTkFrame(content, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        title_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            title_frame,
            text=f"{check['id']}: {check['title']}",
            font=FONT_SUBHEAD,
            text_color=CLR_TEXT,
        )
        title_label.grid(row=0, column=0, sticky="w")

        status_label = ctk.CTkLabel(
            title_frame,
            text=check["status"],
            font=FONT_SMALL,
            text_color=CLR_TEXT_SEC,
        )
        status_label.grid(row=0, column=1, sticky="e", padx=12)

        # Description
        desc_label = ctk.CTkLabel(
            content,
            text=check["description"],
            font=FONT_SMALL,
            text_color=CLR_TEXT_SEC,
            wraplength=600,
            justify="left",
        )
        desc_label.grid(row=1, column=0, sticky="w")

        # Status indicator
        status_indicator = ctk.CTkFrame(card, fg_color="transparent", width=3)
        status_indicator.grid(row=0, column=2, sticky="ns", padx=(12, 0))

    def _run_checks(self):
        """Simulate running AD checks."""
        print("Running AD hygiene checks...")
        # This would call actual AD checking logic
