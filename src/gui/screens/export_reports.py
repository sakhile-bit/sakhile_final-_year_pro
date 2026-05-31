"""Report Generation and Export screen — multiple output formats."""

import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.gui.screens.business_info import _header
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_BG,
    CLR_SURFACE,
    CLR_SURFACE_ALT,
    CLR_SURFACE_HVR,
    CLR_TEXT,
    CLR_TEXT_SEC,
    FONT_BODY,
    FONT_SMALL,
    FONT_SUBHEAD,
    NAV_H,
    PAD,
)


class ExportReportsScreen(ctk.CTkFrame):
    def __init__(self, master, on_back=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back or (lambda: None)
        self._export_format = tk.StringVar(value="pdf")
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        _header(self, "Report Generation & Export", "", 0.0)

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=CLR_BG)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=PAD)
        main_frame.grid_columnconfigure(0, weight=1)

        # Section 1: Export Format Selection
        format_section = self._build_format_section(main_frame, 0)
        format_section.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        # Section 2: Customization Options
        options_section = self._build_options_section(main_frame, 1)
        options_section.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        # Section 3: Recent Exports
        recent_section = self._build_recent_exports(main_frame, 2)
        recent_section.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        main_frame.grid_rowconfigure(2, weight=1)

        # Footer with action buttons
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=NAV_H)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)

        btn_export = ctk.CTkButton(
            footer,
            text="📊 Generate & Export",
            command=self._export_report,
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

    def _build_format_section(self, parent, row):
        """Build export format selection section."""
        section = ctk.CTkFrame(
            parent, fg_color=CLR_SURFACE, corner_radius=10,
            border_width=1, border_color="#2E2B3B"
        )
        section.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            section,
            text="📋 Select Export Format",
            font=FONT_SUBHEAD,
            text_color=CLR_TEXT,
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 16))

        # Format options with improved styling
        formats = [
            ("📄", "PDF Report", "pdf", "Professional PDF with charts and formatting"),
            ("📊", "Excel Spreadsheet", "xlsx", "Detailed data in Excel format"),
            ("🔗", "HTML Report", "html", "Interactive web-viewable report"),
            ("📝", "JSON Data", "json", "Raw data in JSON format"),
            ("📋", "CSV Data", "csv", "Comma-separated values for data analysis"),
        ]

        for idx, (icon, label, value, desc) in enumerate(formats):
            self._build_format_option(section, idx + 1, icon, label, value, desc)

        return section

    def _build_format_option(self, parent, row, icon, label, value, description):
        """Build a single format option with enhanced design."""
        option_frame = ctk.CTkFrame(
            parent, fg_color=CLR_SURFACE_ALT, corner_radius=8,
            border_width=1, border_color="#2E2B3B"
        )
        option_frame.grid(row=row, column=0, sticky="ew", padx=16, pady=6)
        option_frame.grid_columnconfigure(2, weight=1)

        # Icon
        icon_label = ctk.CTkLabel(
            option_frame,
            text=icon,
            font=("Segoe UI Emoji", 20),
        )
        icon_label.grid(row=0, column=0, padx=12, pady=8)

        # Radio button
        radio = ctk.CTkRadioButton(
            option_frame,
            text="",
            variable=self._export_format,
            value=value,
            fg_color=CLR_ACCENT,
        )
        radio.grid(row=0, column=1, padx=(0, 12), pady=8)

        # Label and description
        content = ctk.CTkFrame(option_frame, fg_color="transparent")
        content.grid(row=0, column=2, sticky="ew", padx=(0, 12), pady=8)
        content.grid_columnconfigure(0, weight=1)

        label_widget = ctk.CTkLabel(
            content,
            text=label,
            font=FONT_BODY,
            text_color=CLR_TEXT,
        )
        label_widget.pack(anchor="w")

        desc_widget = ctk.CTkLabel(
            content,
            text=description,
            font=FONT_SMALL,
            text_color=CLR_TEXT_SEC,
        )
        desc_widget.pack(anchor="w")

    def _build_options_section(self, parent, row):
        """Build customization options section."""
        section = ctk.CTkFrame(
            parent, fg_color=CLR_SURFACE, corner_radius=10,
            border_width=1, border_color="#2E2B3B"
        )
        section.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            section,
            text="⚙️ Customization Options",
            font=FONT_SUBHEAD,
            text_color=CLR_TEXT,
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 16))

        # Options grid with better spacing
        options = [
            ("Include executive summary", True),
            ("Include detailed control analysis", True),
            ("Include remediation roadmap", True),
            ("Include benchmarking data", False),
            ("Include audit trail", True),
        ]

        for idx, (option, default) in enumerate(options):
            opt_frame = ctk.CTkFrame(section, fg_color="transparent")
            opt_frame.grid(row=idx + 1, column=0, sticky="w", padx=16, pady=6)

            var = tk.BooleanVar(value=default)
            checkbox = ctk.CTkCheckBox(
                opt_frame,
                text=option,
                variable=var,
                font=FONT_BODY,
                text_color=CLR_TEXT,
                fg_color=CLR_ACCENT,
            )
            checkbox.pack(anchor="w")

        return section

    def _build_recent_exports(self, parent, row):
        """Build recent exports section."""
        section = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=8)
        section.grid_columnconfigure(0, weight=1)
        section.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(
            section,
            text="📁 Recent Exports",
            font=FONT_SUBHEAD,
            text_color=CLR_TEXT,
        )
        title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 16))

        # Scrollable list
        scroll_frame = ctk.CTkScrollableFrame(section, fg_color="transparent")
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        scroll_frame.grid_columnconfigure(0, weight=1)

        recent_exports = [
            ("Assessment_2026-05-20.pdf", "PDF", "2 days ago", "2.4 MB"),
            ("Assessment_2026-05-15.xlsx", "Excel", "1 week ago", "1.1 MB"),
            ("Assessment_2026-05-10.html", "HTML", "2 weeks ago", "3.2 MB"),
        ]

        if not recent_exports:
            no_data = ctk.CTkLabel(
                scroll_frame,
                text="No exports yet. Generate your first report above.",
                font=FONT_SMALL,
                text_color=CLR_TEXT_SEC,
            )
            no_data.pack()
        else:
            for idx, (filename, fmt, date, size) in enumerate(recent_exports):
                export_item = ctk.CTkFrame(scroll_frame, fg_color=CLR_SURFACE_ALT, corner_radius=6)
                export_item.grid(row=idx, column=0, sticky="ew", pady=6)
                export_item.grid_columnconfigure(1, weight=1)

                # File icon
                icon = ctk.CTkLabel(export_item, text="📄", font=("Segoe UI Emoji", 14))
                icon.grid(row=0, column=0, padx=10, pady=8)

                # File info
                info = ctk.CTkFrame(export_item, fg_color="transparent")
                info.grid(row=0, column=1, sticky="ew", padx=0, pady=8)
                info.grid_columnconfigure(0, weight=1)

                name_label = ctk.CTkLabel(info, text=filename, font=FONT_BODY, text_color=CLR_TEXT)
                name_label.pack(anchor="w")

                meta_label = ctk.CTkLabel(
                    info, text=f"{fmt} • {date} • {size}", font=FONT_SMALL, text_color=CLR_TEXT_SEC
                )
                meta_label.pack(anchor="w")

                # Download button
                dl_btn = ctk.CTkButton(
                    export_item,
                    text="↓",
                    width=32,
                    fg_color=CLR_SURFACE_ALT,
                    hover_color=CLR_SURFACE_HVR,
                    font=FONT_SUBHEAD,
                )
                dl_btn.grid(row=0, column=2, padx=10)

        return section

    def _export_report(self):
        """Export report in selected format."""
        fmt = self._export_format.get()
        folder = filedialog.askdirectory(title="Select export location")
        if folder:
            messagebox.showinfo("Export", f"Report exported as {fmt.upper()} to:\n{folder}")
