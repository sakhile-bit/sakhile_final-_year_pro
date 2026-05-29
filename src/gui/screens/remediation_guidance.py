"""Remediation Guidance screen — step-by-step fixes for failed controls."""

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

# Remediation steps mapping
REMEDIATION_STEPS = {
    "C01_os_updates": {
        "title": "Operating System Updates",
        "status": "FAIL",
        "steps": [
            "1. Open Settings > Update & Security",
            "2. Click 'Check for updates'",
            "3. Install all available updates",
            "4. Restart your computer",
            "5. Verify updates in Settings > System > About",
        ],
        "effort": "⚡ Quick Fix (15 minutes)",
        "priority": "CRITICAL",
    },
    "C02_antivirus": {
        "title": "Antivirus Protection",
        "status": "FAIL",
        "steps": [
            "1. Open Windows Security",
            "2. Check Virus & threat protection status",
            "3. If Windows Defender is off, enable it",
            "4. Run a quick scan to verify",
            "5. Schedule daily scans",
        ],
        "effort": "⚡ Quick Fix (10 minutes)",
        "priority": "CRITICAL",
    },
    "C03_firewall": {
        "title": "Firewall Configuration",
        "status": "FAIL",
        "steps": [
            "1. Open Windows Defender Firewall",
            "2. Verify Firewall is ON for all networks",
            "3. Review firewall rules for open ports",
            "4. Allow only necessary applications",
            "5. Test with netstat -an command",
        ],
        "effort": "📅 This Week (30 minutes)",
        "priority": "CRITICAL",
    },
    "C04_password_policy": {
        "title": "Password Policy",
        "status": "FAIL",
        "steps": [
            "1. Open Local Group Policy Editor (gpedit.msc)",
            "2. Navigate to Computer Configuration > Policies > Windows Settings > Account Policies",
            "3. Set minimum password length to 12 characters",
            "4. Enable password complexity requirements",
            "5. Apply and restart",
        ],
        "effort": "📅 This Week (20 minutes)",
        "priority": "HIGH",
    },
    "C05_backups": {
        "title": "Backup Systems",
        "status": "FAIL",
        "steps": [
            "1. Open Settings > System > Storage > Backup options",
            "2. Configure File History backups",
            "3. Set up external drive or cloud backup",
            "4. Schedule daily backups",
            "5. Test restore from backup",
        ],
        "effort": "📅 This Week (45 minutes)",
        "priority": "HIGH",
    },
    "C06_security_training": {
        "title": "Security Awareness Training",
        "status": "NOT_ASSESSED",
        "steps": [
            "1. Enroll employees in security awareness training",
            "2. Cover topics: phishing, password security, data protection",
            "3. Conduct monthly security briefings",
            "4. Track training completion",
            "5. Document training records",
        ],
        "effort": "📆 This Month",
        "priority": "MEDIUM",
    },
    "C07_access_control": {
        "title": "Access Control Policy",
        "status": "NOT_ASSESSED",
        "steps": [
            "1. Create role-based access control (RBAC) policy",
            "2. Define user roles and permissions",
            "3. Implement least privilege principle",
            "4. Conduct quarterly access reviews",
            "5. Document and communicate policy",
        ],
        "effort": "📆 This Month",
        "priority": "MEDIUM",
    },
    "C08_incident_response": {
        "title": "Incident Response Plan",
        "status": "NOT_ASSESSED",
        "steps": [
            "1. Develop incident response plan document",
            "2. Define incident types and severity levels",
            "3. Establish incident response team",
            "4. Create escalation procedures",
            "5. Conduct quarterly incident response drills",
        ],
        "effort": "📆 This Month",
        "priority": "MEDIUM",
    },
}


class RemediationGuidanceScreen(ctk.CTkFrame):
    def __init__(self, master, on_back=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back or (lambda: None)
        self._build()

    def _build(self):
        # Header
        _header(self, "Remediation Guidance", "", 0.0)

        # Main container with scrollable frame
        main_frame = ctk.CTkFrame(self, fg_color=CLR_BG)
        main_frame.pack(fill="both", expand=True, padx=PAD, pady=PAD)
        main_frame.grid_columnconfigure(0, weight=1)

        # Intro text
        intro = ctk.CTkLabel(
            main_frame,
            text="Step-by-step guidance to remediate failed security controls",
            font=FONT_BODY,
            text_color=CLR_TEXT_SEC,
            wraplength=800,
        )
        intro.grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Scrollable container
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.grid(row=1, column=0, sticky="nsew", pady=20)
        scroll_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        row = 0
        for control_id, guidance in REMEDIATION_STEPS.items():
            self._build_remediation_card(scroll_frame, row, control_id, guidance)
            row += 1

        # Footer with back button
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=NAV_H)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        btn_back = ctk.CTkButton(
            footer,
            text="← Back to Home",
            command=self._on_back,
            fg_color=CLR_SURFACE_ALT,
            hover_color=CLR_SURFACE_HVR,
            text_color=CLR_TEXT,
            font=FONT_SUBHEAD,
            height=BTN_H,
            corner_radius=BTN_R,
            border_width=0,
        )
        btn_back.pack(side="left", padx=PAD, pady=PAD)

    def _build_remediation_card(self, parent, row, control_id, guidance):
        """Build a single remediation card with enhanced styling."""
        # Determine color based on priority
        priority_color = {
            "CRITICAL": CLR_DANGER,
            "HIGH": CLR_WARNING,
            "MEDIUM": CLR_ACCENT,
        }.get(guidance.get("priority", "MEDIUM"), CLR_MUTED)

        # Main card with left border accent
        card = ctk.CTkFrame(
            parent, fg_color=CLR_SURFACE, corner_radius=10,
            border_width=2, border_color=priority_color
        )
        card.grid(row=row, column=0, sticky="ew", pady=12)
        card.grid_columnconfigure(1, weight=1)

        # Left accent bar
        accent_bar = ctk.CTkFrame(card, fg_color=priority_color, width=4, corner_radius=0)
        accent_bar.grid(row=0, column=0, sticky="ns", padx=0, pady=0)
        accent_bar.pack_propagate(False)

        # Main content container
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=0, column=1, sticky="ew", padx=16, pady=16)
        content.grid_columnconfigure(0, weight=1)

        # Top section: Title and priority badge
        top_frame = ctk.CTkFrame(content, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            top_frame,
            text=f"{control_id}: {guidance['title']}",
            font=FONT_SUBHEAD,
            text_color=CLR_TEXT,
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Priority badge
        priority_badge = ctk.CTkFrame(
            top_frame, fg_color=priority_color,
            corner_radius=4
        )
        priority_badge.grid(row=0, column=1, sticky="e", padx=(12, 0))

        ctk.CTkLabel(
            priority_badge,
            text=guidance.get("priority", ""),
            font=FONT_SMALL,
            text_color="#ffffff",
        ).pack(padx=8, pady=4)

        # Effort indicator
        effort_label = ctk.CTkLabel(
            content,
            text=guidance.get("effort", ""),
            font=FONT_SMALL,
            text_color=CLR_TEXT_SEC,
        )
        effort_label.grid(row=1, column=0, sticky="w", pady=(0, 12))

        # Steps section with enhanced styling
        steps_title = ctk.CTkLabel(
            content,
            text="Steps to Remediate:",
            font=("Segoe UI", 10, "bold"),
            text_color=CLR_TEXT,
        )
        steps_title.grid(row=2, column=0, sticky="w", pady=(4, 8))

        steps_frame = ctk.CTkFrame(content, fg_color=CLR_SURFACE_ALT, corner_radius=6)
        steps_frame.grid(row=3, column=0, sticky="ew")
        steps_frame.grid_columnconfigure(0, weight=1)

        for idx, step in enumerate(guidance.get("steps", [])):
            step_label = ctk.CTkLabel(
                steps_frame,
                text=step,
                font=FONT_SMALL,
                text_color=CLR_TEXT_SEC,
                wraplength=650,
                justify="left",
            )
            step_label.grid(row=idx, column=0, sticky="w", padx=12, pady=6)
