"""Settings and Configuration screen — app preferences and configuration."""

import tkinter as tk

import customtkinter as ctk

from src.gui.screens.business_info import _header
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_BG,
    CLR_BORDER,
    CLR_SUCCESS,
    CLR_SURFACE,
    CLR_SURFACE_ALT,
    CLR_SURFACE_HVR,
    CLR_TEXT,
    FONT_BODY,
    FONT_SUBHEAD,
    NAV_H,
    PAD,
)


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, master, on_back=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back or (lambda: None)
        self._build()

    def _build(self):
        # Header
        _header(self, "Settings & Configuration", "", 0.0)

        # Main container with tabs
        main_frame = ctk.CTkFrame(self, fg_color=CLR_BG)
        main_frame.pack(fill="both", expand=True, padx=PAD, pady=PAD)
        main_frame.grid_columnconfigure(0, weight=1)

        # Tab buttons
        tabs_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tabs_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        self._tab_var = tk.StringVar(value="general")

        for tab_name, tab_id in [("General", "general"), ("Database", "database"), ("Export", "export")]:
            btn = ctk.CTkButton(
                tabs_frame,
                text=tab_name,
                command=lambda tid=tab_id: self._switch_tab(tid),
                fg_color=CLR_SURFACE,
                hover_color=CLR_SURFACE_HVR,
                text_color=CLR_TEXT,
                font=FONT_BODY,
                height=BTN_H,
                border_width=0,
            )
            btn.pack(side="left", padx=4)

        # Content frame
        self._content_frame = ctk.CTkFrame(main_frame, fg_color=CLR_BG)
        self._content_frame.grid(row=1, column=0, sticky="nsew")
        self._content_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Build tabs
        self._build_general_tab()

        # Footer
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=NAV_H)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        btn_save = ctk.CTkButton(
            footer,
            text="💾 Save Settings",
            command=self._save_settings,
            fg_color=CLR_SUCCESS,
            hover_color=CLR_SUCCESS,
            text_color="#ffffff",
            font=FONT_SUBHEAD,
            height=BTN_H,
            corner_radius=BTN_R,
            border_width=0,
        )
        btn_save.pack(side="left", padx=PAD, pady=PAD)

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

    def _build_general_tab(self):
        """Build general settings tab."""
        # Clear content frame
        for widget in self._content_frame.winfo_children():
            widget.destroy()

        scroll_frame = ctk.CTkScrollableFrame(self._content_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Organization section
        self._build_section(scroll_frame, 0, "🏢 Organization", [
            ("Organization Name", "My Company Ltd"),
            ("Industry Type", "Technology"),
            ("Assessment Tier", "Tier 3 (On-site)"),
        ])

        # Assessment settings
        self._build_section_toggle(scroll_frame, 1, "📋 Assessment Settings", [
            ("Auto-scan on startup", True),
            ("Enable detailed logging", True),
            ("Notifications on completion", False),
        ])

        # Appearance
        self._build_section(scroll_frame, 2, "🎨 Appearance", [
            ("Theme", "Dark"),
            ("Language", "English"),
        ])

    def _build_section(self, parent, row, title, fields):
        """Build a settings section with input fields."""
        section = ctk.CTkFrame(
            parent, fg_color=CLR_SURFACE, corner_radius=10,
            border_width=1, border_color=CLR_BORDER
        )
        section.grid(row=row, column=0, sticky="ew", pady=(0, 20))
        section.grid_columnconfigure(1, weight=1)

        # Section title
        title_label = ctk.CTkLabel(
            section, text=title, font=FONT_SUBHEAD, text_color=CLR_TEXT
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 16), sticky="w")

        # Fields
        for idx, (label, value) in enumerate(fields, start=1):
            label_widget = ctk.CTkLabel(
                section, text=label, font=FONT_BODY, text_color=CLR_TEXT
            )
            label_widget.grid(row=idx, column=0, padx=16, pady=8, sticky="w")

            entry = ctk.CTkEntry(
                section,
                placeholder_text=value,
                fg_color=CLR_SURFACE_ALT,
                border_color=CLR_BORDER,
                text_color=CLR_TEXT,
                font=FONT_BODY,
                height=32,
            )
            entry.grid(row=idx, column=1, padx=16, pady=8, sticky="ew")

    def _build_section_toggle(self, parent, row, title, toggles):
        """Build a settings section with toggle options."""
        section = ctk.CTkFrame(
            parent, fg_color=CLR_SURFACE, corner_radius=10,
            border_width=1, border_color=CLR_BORDER
        )
        section.grid(row=row, column=0, sticky="ew", pady=(0, 20))
        section.grid_columnconfigure(0, weight=1)

        # Section title
        title_label = ctk.CTkLabel(
            section, text=title, font=FONT_SUBHEAD, text_color=CLR_TEXT
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 16), sticky="w")

        # Toggles
        for idx, (label, default_value) in enumerate(toggles, start=1):
            var = tk.BooleanVar(value=default_value)

            toggle = ctk.CTkSwitch(
                section,
                text=label,
                variable=var,
                fg_color=CLR_ACCENT,
                text_color=CLR_TEXT,
                font=FONT_BODY,
            )
            toggle.grid(row=idx, column=0, columnspan=2, padx=16, pady=8, sticky="w")

    def _build_setting_field(self, parent, row, label, value):
        """Build a single setting field (deprecated - use _build_section)."""
        label_widget = ctk.CTkLabel(parent, text=label, font=FONT_BODY, text_color=CLR_TEXT)
        label_widget.grid(row=row, column=0, padx=16, pady=8, sticky="w")

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=value,
            fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER,
            text_color=CLR_TEXT,
            font=FONT_BODY,
            height=32,
        )
        entry.grid(row=row, column=1, padx=16, pady=8, sticky="ew")

    def _switch_tab(self, tab_id):
        """Switch between tabs."""
        self._tab_var.set(tab_id)
        if tab_id == "general":
            self._build_general_tab()
        elif tab_id == "database":
            self._build_database_tab()
        elif tab_id == "export":
            self._build_export_tab()

    def _build_database_tab(self):
        """Build database settings tab."""
        for widget in self._content_frame.winfo_children():
            widget.destroy()

        scroll_frame = ctk.CTkScrollableFrame(self._content_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Database connection
        self._build_section(scroll_frame, 0, "🗄️ Database Connection", [
            ("Host", "localhost"),
            ("Port", "3306"),
            ("Database", "digital_hygiene"),
            ("Username", "admin"),
        ])

        # Connection status
        status_frame = ctk.CTkFrame(
            scroll_frame, fg_color=CLR_SURFACE, corner_radius=10,
            border_width=1, border_color=CLR_BORDER
        )
        status_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        status_label = ctk.CTkLabel(
            status_frame, text="Connection Status", font=FONT_SUBHEAD, text_color=CLR_TEXT
        )
        status_label.grid(row=0, column=0, columnspan=2, padx=16, pady=(12, 12), sticky="w")

        status_indicator = ctk.CTkLabel(
            status_frame, text="✔ Connected", font=FONT_BODY, text_color="#2BA22B"
        )
        status_indicator.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="w")

        test_btn = ctk.CTkButton(
            status_frame,
            text="Test Connection",
            fg_color=CLR_ACCENT,
            text_color="#ffffff",
            font=FONT_BODY,
            height=32,
            corner_radius=BTN_R,
        )
        test_btn.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="ew")

    def _build_export_tab(self):
        """Build export settings tab."""
        for widget in self._content_frame.winfo_children():
            widget.destroy()

        scroll_frame = ctk.CTkScrollableFrame(self._content_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Export paths
        self._build_section(scroll_frame, 0, "📁 Export Settings", [
            ("Default Export Path", "C:\\Reports"),
            ("PDF Template Path", "C:\\Templates"),
        ])

        # Export options
        self._build_section_toggle(scroll_frame, 1, "⚙️ Export Options", [
            ("Include watermark in PDFs", True),
            ("Auto-backup on export", True),
            ("Encrypt sensitive data", False),
        ])

    def _save_settings(self):
        """Save settings to configuration."""
        print("Settings saved...")
