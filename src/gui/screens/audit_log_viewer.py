"""Audit Log Viewer screen — view system activity and changes."""

import csv
from datetime import datetime, timedelta

import customtkinter as ctk

from src.gui.screens.business_info import _header
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_ACCENT_HOV,
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
    FONT_CAPTION,
    FONT_SMALL,
    FONT_SUBHEAD,
    NAV_H,
    PAD,
)

# Severity → (accent colour, pill background, short label)
_SEVERITY = {
    "INFO": (CLR_SUCCESS, "#15301B", "INFO"),
    "WARNING": (CLR_WARNING, "#2C2200", "WARN"),
    "ERROR": (CLR_DANGER, "#2A0C0C", "ERROR"),
}


def _relative_time(ts: datetime) -> str:
    """Human-friendly relative timestamp, e.g. '2h ago'."""
    delta = datetime.now() - ts
    secs = int(delta.total_seconds())
    if secs < 60:
        return "just now"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"


class AuditLogViewerScreen(ctk.CTkFrame):
    def __init__(self, master, on_back=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back or (lambda: None)
        self._logs = self._generate_sample_logs()
        self._query = ""
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        _header(self, "Audit Log Viewer", "", 0.0)

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=CLR_BG)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=(PAD, 0))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # ── Filter / search bar ─────────────────────────────────────────────
        filters_frame = ctk.CTkFrame(main_frame, fg_color=CLR_SURFACE, corner_radius=8)
        filters_frame.grid(row=0, column=0, sticky="ew")
        filters_frame.grid_columnconfigure(0, weight=1)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        search_entry = ctk.CTkEntry(
            filters_frame,
            textvariable=self._search_var,
            placeholder_text="🔍  Search by user, action, resource or detail…",
            fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER,
            text_color=CLR_TEXT,
            font=FONT_BODY,
            height=38,
        )
        search_entry.grid(row=0, column=0, padx=12, pady=12, sticky="ew")

        self._count_label = ctk.CTkLabel(
            filters_frame, text="", font=FONT_CAPTION, text_color=CLR_MUTED
        )
        self._count_label.grid(row=0, column=1, padx=(0, 16), sticky="e")

        # ── Scrollable log list ─────────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self._scroll.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        self._scroll.grid_columnconfigure(0, weight=1)

        self._render_logs()

        # ── Footer ──────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=NAV_H)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)

        btn_export = ctk.CTkButton(
            footer,
            text="📥  Export Logs",
            command=self._export_logs,
            fg_color=CLR_ACCENT,
            hover_color=CLR_ACCENT_HOV,
            text_color="#ffffff",
            font=FONT_SUBHEAD,
            height=BTN_H,
            corner_radius=BTN_R,
            border_width=0,
        )
        btn_export.pack(side="left", padx=PAD, pady=PAD)

        self._status_label = ctk.CTkLabel(
            footer, text="", font=FONT_CAPTION, text_color=CLR_MUTED
        )
        self._status_label.pack(side="left", pady=PAD)

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

    # ── Data ────────────────────────────────────────────────────────────────
    def _generate_sample_logs(self):
        """Generate sample audit logs (newest first)."""
        now = datetime.now()
        return [
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
            {
                "timestamp": now - timedelta(days=2),
                "user": "system",
                "action": "Login Failed",
                "resource": "User: guest@org.com",
                "severity": "ERROR",
                "details": "3 failed login attempts — account temporarily locked",
            },
        ]

    def _filtered_logs(self):
        q = self._query.strip().lower()
        if not q:
            return self._logs
        return [
            log
            for log in self._logs
            if q in log["action"].lower()
            or q in log["user"].lower()
            or q in log["resource"].lower()
            or q in log["details"].lower()
            or q in log["severity"].lower()
        ]

    # ── Rendering ───────────────────────────────────────────────────────────
    def _on_search(self, *_):
        self._query = self._search_var.get()
        self._render_logs()

    def _render_logs(self):
        for child in self._scroll.winfo_children():
            child.destroy()

        logs = self._filtered_logs()
        total = len(self._logs)
        shown = len(logs)
        self._count_label.configure(
            text=f"{shown} of {total} events" if self._query else f"{total} events"
        )

        if not logs:
            empty = ctk.CTkLabel(
                self._scroll,
                text="No matching activity.\nTry a different search term.",
                font=FONT_BODY,
                text_color=CLR_MUTED,
                justify="center",
            )
            empty.grid(row=0, column=0, pady=60)
            return

        for idx, log in enumerate(logs):
            self._build_log_entry(self._scroll, idx, log)

    def _build_log_entry(self, parent, idx, log):
        """Build a single compact audit log entry."""
        accent, pill_bg, short = _SEVERITY.get(
            log["severity"], (CLR_MUTED, CLR_SURFACE_ALT, log["severity"])
        )

        entry = ctk.CTkFrame(
            parent, fg_color=CLR_SURFACE, corner_radius=8,
            border_width=1, border_color=CLR_BORDER,
        )
        entry.grid(row=idx, column=0, sticky="ew", pady=(0, 8))
        entry.grid_columnconfigure(1, weight=1)

        # Left severity accent bar
        bar = ctk.CTkFrame(entry, fg_color=accent, width=3, corner_radius=0)
        bar.grid(row=0, column=0, sticky="ns", padx=(0, 0), pady=1)

        content = ctk.CTkFrame(entry, fg_color="transparent")
        content.grid(row=0, column=1, sticky="ew", padx=14, pady=10)
        content.grid_columnconfigure(1, weight=1)

        # Severity pill
        pill = ctk.CTkLabel(
            content, text=f" {short} ", font=FONT_CAPTION, text_color=accent,
            fg_color=pill_bg, corner_radius=4,
        )
        pill.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Action
        ctk.CTkLabel(
            content, text=log["action"], font=FONT_SUBHEAD, text_color=CLR_TEXT,
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        # Timestamp (relative + exact tooltip-ish caption)
        ctk.CTkLabel(
            content,
            text=f"{_relative_time(log['timestamp'])}  ·  {log['timestamp'].strftime('%b %d, %H:%M')}",
            font=FONT_CAPTION, text_color=CLR_TEXT_SEC, anchor="e",
        ).grid(row=0, column=2, sticky="e", padx=(10, 0))

        # Meta line: user • resource
        ctk.CTkLabel(
            content,
            text=f"{log['user']}   •   {log['resource']}",
            font=FONT_SMALL, text_color=CLR_TEXT_SEC, anchor="w", justify="left",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # Detail line
        ctk.CTkLabel(
            content, text=log["details"], font=FONT_SMALL, text_color=CLR_MUTED,
            anchor="w", justify="left", wraplength=760,
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(2, 0))

    # ── Export ──────────────────────────────────────────────────────────────
    def _export_logs(self):
        """Export the currently visible logs to a CSV file."""
        from tkinter import filedialog

        logs = self._filtered_logs()
        if not logs:
            self._status_label.configure(text="Nothing to export.")
            return

        default_name = f"audit_logs_{datetime.now():%Y%m%d_%H%M%S}.csv"
        path = filedialog.asksaveasfilename(
            title="Export Audit Logs",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(
                    ["Timestamp", "Severity", "User", "Action", "Resource", "Details"]
                )
                for log in logs:
                    writer.writerow([
                        log["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                        log["severity"],
                        log["user"],
                        log["action"],
                        log["resource"],
                        log["details"],
                    ])
            self._status_label.configure(text=f"Exported {len(logs)} events ✓")
        except OSError as exc:
            self._status_label.configure(text=f"Export failed: {exc}")
