"""Audit Log Viewer screen — view system activity and changes."""

from datetime import datetime, timedelta

import customtkinter as ctk

from src.gui.screens.business_info import _header
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_BG,
    CLR_BORDER,
    CLR_DANGER,
    CLR_MUTED,
    CLR_SUCCESS,
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


class AuditLogViewerScreen(ctk.CTkFrame):
    def __init__(self, master, on_back=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back or (lambda: None)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        _header(self, "Audit Log Viewer", "", 0.0)

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=CLR_BG)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=PAD)
        main_frame.grid_columnconfigure(0, weight=1)

        # Filters section
        filters_frame = ctk.CTkFrame(main_frame, fg_color=CLR_SURFACE, corner_radius=8)
        filters_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        filters_frame.grid_columnconfigure(1, weight=1)

        filter_label = ctk.CTkLabel(
            filters_frame, text="🔍 Filter Logs", font=FONT_SUBHEAD, text_color=CLR_TEXT
        )
        filter_label.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        # Filter options
        search_entry = ctk.CTkEntry(
            filters_frame,
            placeholder_text="Search by user, action, or resource...",
            fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER,
            text_color=CLR_TEXT,
            font=FONT_BODY,
            height=32,
        )
        search_entry.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="ew")

        # Log entries
        logs_title = ctk.CTkLabel(
            main_frame, text="📋 Recent Activity", font=FONT_SUBHEAD, text_color=CLR_TEXT
        )
        logs_title.grid(row=1, column=0, sticky="w", pady=(20, 12))

        # Scrollable logs
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.grid(row=2, column=0, sticky="nsew", pady=20)
        scroll_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        # Generate sample audit logs
        logs = self._generate_sample_logs()
        for idx, log in enumerate(logs):
            self._build_log_entry(scroll_frame, idx, log)

        # Footer
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=NAV_H)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)

        btn_export = ctk.CTkButton(
            footer,
            text="📥 Export Logs",
            command=self._export_logs,
            fg_color=CLR_ACCENT,
            hover_color=CLR_ACCENT,
            text_color="#ffffff",
            font=FONT_SUBHEAD,
            height=BTN_H,
            corner_radius=BTN_R,
            border_width=0,
        )
        btn_export.pack(side="left", padx=PAD, pady=PAD)

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

    def _generate_sample_logs(self):
        """Generate sample audit logs."""
        now = datetime.now()
        logs = [
            {
                "timestamp": now,
                "user": "admin@org.com",
                "action": "Assessment Created",
                "resource": "Assessment #1024",
                "severity": "INFO",
                "details": "Digital Hygiene assessment started",
            },
            {
                "timestamp": now - timedelta(hours=2),
                "user": "john@org.com",
                "action": "Assessment Updated",
                "resource": "Assessment #1024",
                "severity": "INFO",
                "details": "Manual checks completed",
            },
            {
                "timestamp": now - timedelta(hours=5),
                "user": "admin@org.com",
                "action": "User Added",
                "resource": "User: sarah@org.com",
                "severity": "WARNING",
                "details": "New assessor user added",
            },
            {
                "timestamp": now - timedelta(hours=12),
                "user": "john@org.com",
                "action": "Report Exported",
                "resource": "Assessment #1020",
                "severity": "INFO",
                "details": "PDF report generated",
            },
            {
                "timestamp": now - timedelta(hours=24),
                "user": "admin@org.com",
                "action": "Settings Changed",
                "resource": "System Config",
                "severity": "WARNING",
                "details": "Database connection parameters updated",
            },
        ]
        return logs

    def _build_log_entry(self, parent, idx, log):
        """Build a single audit log entry."""
        entry_frame = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=8)
        entry_frame.grid(row=idx, column=0, sticky="ew", pady=8)
        entry_frame.grid_columnconfigure(1, weight=1)

        # Severity indicator
        severity_colors = {
            "INFO": CLR_SUCCESS,
            "WARNING": CLR_WARNING,
            "ERROR": CLR_DANGER,
        }
        severity_color = severity_colors.get(log["severity"], CLR_MUTED)

        severity_badge = ctk.CTkFrame(
            entry_frame, fg_color=severity_color, width=4, corner_radius=0
        )
        severity_badge.grid(row=0, column=0, sticky="ns", pady=12)

        # Log content
        content_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
        content_frame.grid(row=0, column=1, sticky="ew", padx=16, pady=12)
        content_frame.grid_columnconfigure(0, weight=1)

        # Header: action and timestamp
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        action_label = ctk.CTkLabel(
            header_frame,
            text=log["action"],
            font=FONT_SUBHEAD,
            text_color=CLR_TEXT,
        )
        action_label.grid(row=0, column=0, sticky="w")

        time_label = ctk.CTkLabel(
            header_frame,
            text=log["timestamp"].strftime("%H:%M:%S"),
            font=FONT_SMALL,
            text_color=CLR_TEXT_SEC,
        )
        time_label.grid(row=0, column=1, sticky="e", padx=12)

        # Details: user, resource, description
        details_text = f"User: {log['user']} • Resource: {log['resource']}"
        details_label = ctk.CTkLabel(
            content_frame,
            text=details_text,
            font=FONT_SMALL,
            text_color=CLR_TEXT_SEC,
            wraplength=600,
        )
        details_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        desc_label = ctk.CTkLabel(
            content_frame,
            text=log["details"],
            font=FONT_SMALL,
            text_color=CLR_MUTED,
            wraplength=600,
        )
        desc_label.grid(row=2, column=0, sticky="w", pady=(2, 0))

    def _export_logs(self):
        """Export audit logs."""
        print("Exporting audit logs...")
