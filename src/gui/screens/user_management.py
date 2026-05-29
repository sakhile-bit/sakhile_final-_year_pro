"""User Profile & Preferences screen — for desktop app local user settings."""

from tkinter import messagebox

import customtkinter as ctk

from src.gui.screens.business_info import _header
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_BG,
    CLR_DANGER,
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


class UserManagementScreen(ctk.CTkFrame):
    """Desktop app user profile and preferences."""

    def __init__(self, master, on_back=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back or (lambda: None)
        self._build()

    def _build(self):
        # Header
        _header(self, "User Profile", "", 0.0)

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=CLR_BG)
        main_frame.pack(fill="both", expand=True, padx=PAD, pady=PAD)
        main_frame.grid_columnconfigure(0, weight=1)

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        # Section: Current User Profile
        profile_section = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=8)
        profile_section.pack(fill="x", pady=(0, 16))
        profile_section.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            profile_section,
            text="👤",
            font=("Segoe UI Emoji", 32),
        ).grid(row=0, column=0, padx=16, pady=(12, 0), sticky="n")

        info_frame = ctk.CTkFrame(profile_section, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=12)
        info_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info_frame,
            text="Assessor User",
            font=FONT_SUBHEAD,
            text_color=CLR_TEXT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_frame,
            text="assessor@organization.local",
            font=FONT_BODY,
            text_color=CLR_TEXT_SEC,
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_frame,
            text="Last login: Today at 10:30 AM",
            font=FONT_SMALL,
            text_color=CLR_TEXT_SEC,
        ).pack(anchor="w")

        # Section: App Preferences
        prefs_section = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=8)
        prefs_section.pack(fill="x", pady=(0, 16))
        prefs_section.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            prefs_section,
            text="⚙️ App Preferences",
            font=FONT_SUBHEAD,
            text_color=CLR_TEXT,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 12))

        # Preference items
        prefs = [
            ("Auto-save assessments", True),
            ("Notify on task completion", True),
            ("Enable offline mode", True),
            ("Auto-sync with server", False),
        ]

        for idx, (label, enabled) in enumerate(prefs, start=1):
            ctk.CTkLabel(
                prefs_section,
                text=label,
                font=FONT_BODY,
                text_color=CLR_TEXT,
            ).grid(row=idx, column=0, sticky="w", padx=16, pady=8)

            toggle = ctk.CTkSwitch(
                prefs_section,
                text="",
                onvalue=True,
                offvalue=False,
            )
            toggle.set(enabled)
            toggle.grid(row=idx, column=1, sticky="e", padx=16, pady=8)

        # Section: Security
        security_section = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=8)
        security_section.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            security_section,
            text="🔒 Security",
            font=FONT_SUBHEAD,
            text_color=CLR_TEXT,
        ).pack(anchor="w", padx=16, pady=(12, 12))

        btn_pwd = ctk.CTkButton(
            security_section,
            text="🔑 Change Password",
            command=self._change_password,
            fg_color=CLR_SURFACE_ALT,
            hover_color=CLR_SURFACE_HVR,
            text_color=CLR_TEXT,
            font=FONT_BODY,
            height=BTN_H,
            corner_radius=BTN_R,
        )
        btn_pwd.pack(fill="x", padx=16, pady=(0, 8))

        btn_session = ctk.CTkButton(
            security_section,
            text="📊 View Active Sessions",
            command=self._view_sessions,
            fg_color=CLR_SURFACE_ALT,
            hover_color=CLR_SURFACE_HVR,
            text_color=CLR_TEXT,
            font=FONT_BODY,
            height=BTN_H,
            corner_radius=BTN_R,
        )
        btn_session.pack(fill="x", padx=16, pady=(0, 12))

        # Footer with buttons
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=NAV_H)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        btn_logout = ctk.CTkButton(
            footer,
            text="🚪 Logout",
            command=self._logout,
            fg_color=CLR_DANGER,
            hover_color=CLR_DANGER,
            text_color="#ffffff",
            font=FONT_SUBHEAD,
            height=BTN_H,
            corner_radius=BTN_R,
            border_width=0,
        )
        btn_logout.pack(side="left", padx=PAD, pady=PAD)

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

    def _change_password(self):
        """Show password change dialog."""
        messagebox.showinfo("Change Password", "Password change dialog would open here")

    def _view_sessions(self):
        """View active sessions."""
        messagebox.showinfo("Active Sessions", "Current session: This computer\nNo other active sessions")

    def _logout(self):
        """Logout user."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            messagebox.showinfo("Logout", "You have been logged out")
