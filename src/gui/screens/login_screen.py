"""Login screen — shown on every launch after first-time setup."""
from __future__ import annotations

import customtkinter as ctk

from src.gui.theme import (
    APP_NAME, APP_VERSION,
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_BORDER,
    CLR_ACCENT, CLR_ACCENT_HOV, CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_DANGER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    BTN_H, BTN_R, PAD,
)
from src.utils.auth import get_username, verify

_MAX_ATTEMPTS = 5


class LoginScreen(ctk.CTkFrame):
    """Password gate — user must authenticate before accessing the app."""

    def __init__(self, master, on_success: callable):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_success = on_success
        self._attempts = 0
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Centre card ───────────────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=16,
                            border_width=1, border_color=CLR_BORDER,
                            width=420)
        card.grid(row=0, column=0, padx=40, pady=40)
        card.grid_columnconfigure(0, weight=1)

        # Brand strip
        ctk.CTkFrame(card, fg_color=CLR_ACCENT, corner_radius=0,
                     height=5).grid(row=0, column=0, sticky="ew")

        # Icon + heading
        ctk.CTkLabel(card, text="🔐",
                     font=("Segoe UI Emoji", 42)
                     ).grid(row=1, column=0, pady=(28, 4))

        ctk.CTkLabel(card, text=APP_NAME,
                     font=FONT_HEADING, text_color=CLR_TEXT
                     ).grid(row=2, column=0, padx=PAD)

        ctk.CTkLabel(card, text=f"v{APP_VERSION}",
                     font=FONT_CAPTION, text_color=CLR_MUTED
                     ).grid(row=3, column=0, pady=(2, 18))

        # Divider
        ctk.CTkFrame(card, fg_color=CLR_BORDER, height=1
                     ).grid(row=4, column=0, sticky="ew", padx=PAD)

        # ── Form ─────────────────────────────────────────────────────
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.grid(row=5, column=0, padx=PAD, pady=20, sticky="ew")
        form.grid_columnconfigure(0, weight=1)

        # Username (pre-filled, read-only display)
        stored_user = get_username()
        ctk.CTkLabel(form, text="Username", font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, anchor="w"
                     ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        ctk.CTkEntry(
            form, font=FONT_BODY, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_MUTED, height=38, corner_radius=8,
            state="disabled",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 14))
        # Insert stored username into the disabled field
        _u = form.winfo_children()[-1]
        _u.configure(state="normal")
        _u.insert(0, stored_user)
        _u.configure(state="disabled")

        # Password
        ctk.CTkLabel(form, text="Password", font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, anchor="w"
                     ).grid(row=2, column=0, sticky="w", pady=(0, 4))
        self._password = ctk.CTkEntry(
            form, placeholder_text="Enter your password",
            show="•", font=FONT_BODY, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT, height=38, corner_radius=8,
        )
        self._password.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        self._password.bind("<Return>", lambda e: self._submit())

        # Error label
        self._error_lbl = ctk.CTkLabel(
            form, text="", font=FONT_CAPTION,
            text_color=CLR_DANGER, anchor="w", wraplength=360,
        )
        self._error_lbl.grid(row=4, column=0, sticky="w", pady=(0, 10))

        # Login button
        self._btn = ctk.CTkButton(
            form, text="Sign In →",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#000000", height=42, corner_radius=BTN_R,
            command=self._submit,
        )
        self._btn.grid(row=5, column=0, sticky="ew")

        # Footer note
        ctk.CTkLabel(card,
                     text="🔒  Secured with local credential storage.",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=6, column=0, padx=PAD, pady=(4, 24))

        # Auto-focus password field
        self.after(100, self._password.focus)

    def _error(self, msg: str):
        self._error_lbl.configure(text=f"⚠  {msg}")

    def _submit(self):
        if self._attempts >= _MAX_ATTEMPTS:
            return

        username = get_username()
        password = self._password.get()

        if verify(username, password):
            self._on_success()
        else:
            self._attempts += 1
            remaining = _MAX_ATTEMPTS - self._attempts
            if remaining > 0:
                self._error(f"Incorrect password. {remaining} attempt(s) remaining.")
            else:
                self._error("Too many failed attempts. Closing app.")
                self._btn.configure(state="disabled")
                self.after(2000, self.winfo_toplevel().destroy)
            self._password.delete(0, "end")
