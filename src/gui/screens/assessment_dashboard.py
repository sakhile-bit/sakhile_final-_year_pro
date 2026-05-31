"""Assessment Dashboard screen — view and manage stored assessments."""

from datetime import datetime, timedelta

import customtkinter as ctk

from src.gui.gui import StatsCard
from src.gui.screens.business_info import _header
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_BG,
    CLR_DANGER,
    CLR_MUTED,
    CLR_SUCCESS,
    CLR_SURFACE,
    CLR_SURFACE_ALT,
    CLR_SURFACE_HVR,
    CLR_TEXT,
    CLR_TEXT_SEC,
    CLR_WARNING,
    FONT_SMALL,
    FONT_SUBHEAD,
    NAV_H,
    PAD,
    TIER_COLOURS,
)


class AssessmentDashboardScreen(ctk.CTkFrame):
    def __init__(self, master, on_back=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back or (lambda: None)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        _header(self, "Assessment Dashboard", "", 0.0)

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=CLR_BG)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=PAD)
        main_frame.grid_columnconfigure(0, weight=1)

        # Statistics overview
        stats_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        stats_frame.grid_rowconfigure(0, minsize=120)

        StatsCard(stats_frame, "📊", "Total Assessments", "12", CLR_ACCENT).grid(
            row=0, column=0, sticky="ew", padx=4
        )
        StatsCard(stats_frame, "🥇", "Gold Certifications", "4", CLR_SUCCESS).grid(
            row=0, column=1, sticky="ew", padx=4
        )
        StatsCard(stats_frame, "⏳", "Pending Reviews", "3", CLR_WARNING).grid(
            row=0, column=2, sticky="ew", padx=4
        )
        StatsCard(stats_frame, "⚠️", "Failed Controls", "8", CLR_DANGER).grid(
            row=0, column=3, sticky="ew", padx=4
        )

        # Assessments list
        title = ctk.CTkLabel(
            main_frame, text="📋 Recent Assessments", font=FONT_SUBHEAD, text_color=CLR_TEXT
        )
        title.grid(row=1, column=0, sticky="w", pady=(20, 12))

        # Scrollable list
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.grid(row=2, column=0, sticky="nsew", pady=20)
        scroll_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        assessments = self._get_assessments()
        for idx, assessment in enumerate(assessments):
            self._build_assessment_card(scroll_frame, idx, assessment)

        # Footer
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=NAV_H)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)

        btn_new = ctk.CTkButton(
            footer,
            text="➕ New Assessment",
            command=self._new_assessment,
            fg_color=CLR_SUCCESS,
            hover_color=CLR_SUCCESS,
            text_color="#ffffff",
            font=FONT_SUBHEAD,
            height=BTN_H,
            corner_radius=BTN_R,
            border_width=0,
        )
        btn_new.pack(side="left", padx=PAD, pady=PAD)

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

    def _get_assessments(self):
        """Get list of assessments from database."""
        return [
            {
                "id": "ASSESS-1024",
                "organization": "Tech Company Ltd",
                "date": datetime.now(),
                "score": 85,
                "level": "GOLD",
                "status": "Completed",
            },
            {
                "id": "ASSESS-1023",
                "organization": "Finance Corp",
                "date": datetime.now() - timedelta(days=5),
                "score": 72,
                "level": "SILVER",
                "status": "Completed",
            },
            {
                "id": "ASSESS-1022",
                "organization": "Healthcare Inc",
                "date": datetime.now() - timedelta(days=10),
                "score": 45,
                "level": "BRONZE",
                "status": "Completed",
            },
            {
                "id": "ASSESS-1021",
                "organization": "Education Plus",
                "date": datetime.now() - timedelta(days=15),
                "score": 90,
                "level": "GOLD",
                "status": "Completed",
            },
        ]

    def _build_assessment_card(self, parent, idx, assessment):
        """Build a single assessment card."""
        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=8)
        card.grid(row=idx, column=0, sticky="ew", pady=8)
        card.grid_columnconfigure(1, weight=1)

        # Certification badge
        tier_color = TIER_COLOURS.get(assessment["level"], CLR_MUTED)
        badge = ctk.CTkFrame(card, fg_color=tier_color, corner_radius=6, width=60, height=60)
        badge.grid(row=0, column=0, padx=12, pady=12, sticky="nw")
        badge.grid_propagate(False)

        tier_icon = {"GOLD": "🥇", "SILVER": "🥈", "BRONZE": "🥉"}.get(assessment["level"], "?")
        tier_label = ctk.CTkLabel(badge, text=tier_icon, font=("Segoe UI Emoji", 24))
        tier_label.pack(expand=True)

        # Assessment info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=0, pady=12)
        info_frame.grid_columnconfigure(0, weight=1)

        org_label = ctk.CTkLabel(
            info_frame,
            text=assessment["organization"],
            font=FONT_SUBHEAD,
            text_color=CLR_TEXT,
        )
        org_label.pack(anchor="w")

        meta = f"{assessment['id']} • {assessment['date'].strftime('%Y-%m-%d')} • {assessment['status']}"
        meta_label = ctk.CTkLabel(info_frame, text=meta, font=FONT_SMALL, text_color=CLR_TEXT_SEC)
        meta_label.pack(anchor="w")

        # Score ring
        score_frame = ctk.CTkFrame(card, fg_color="transparent")
        score_frame.grid(row=0, column=2, padx=12, pady=12)

        score_label = ctk.CTkLabel(
            score_frame,
            text=f"{assessment['score']}%",
            font=("Segoe UI", 16, "bold"),
            text_color=tier_color,
        )
        score_label.pack()

        level_label = ctk.CTkLabel(score_frame, text=assessment["level"], font=FONT_SMALL, text_color=CLR_TEXT_SEC)
        level_label.pack()

        # Actions
        view_btn = ctk.CTkButton(
            card,
            text="👁️ View",
            width=60,
            fg_color=CLR_SURFACE_ALT,
            hover_color=CLR_SURFACE_HVR,
            font=FONT_SMALL,
            command=lambda: self._view_assessment(assessment),
        )
        view_btn.grid(row=0, column=3, padx=4)

        export_btn = ctk.CTkButton(
            card,
            text="📥",
            width=40,
            fg_color=CLR_SURFACE_ALT,
            hover_color=CLR_SURFACE_HVR,
            font=FONT_SMALL,
        )
        export_btn.grid(row=0, column=4, padx=4)

        delete_btn = ctk.CTkButton(
            card,
            text="🗑️",
            width=40,
            fg_color=CLR_SURFACE_ALT,
            hover_color=CLR_DANGER,
            font=FONT_SMALL,
        )
        delete_btn.grid(row=0, column=5, padx=(4, 12))

    def _view_assessment(self, assessment):
        """View assessment details."""
        print(f"Viewing {assessment['id']}")

    def _new_assessment(self):
        """Create new assessment."""
        print("Starting new assessment...")
