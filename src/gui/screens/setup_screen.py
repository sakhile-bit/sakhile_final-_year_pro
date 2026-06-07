"""First-run setup screen — creates the root account on first launch."""
from __future__ import annotations

import re
import customtkinter as ctk
from typing import Callable

from src.gui.theme import (
    APP_NAME, APP_VERSION,
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_BORDER,
    CLR_ACCENT, CLR_ACCENT_HOV, CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_DANGER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    BTN_R, PAD,
)
from src.utils.auth import save_credentials

_MIN_PW_LEN = 8


def _strength(pw: str) -> tuple[int, str]:
    """Return (score 0-4, label)."""
    score = 0
    if len(pw) >= _MIN_PW_LEN:
        score += 1
    if re.search(r'[A-Z]', pw):
        score += 1
    if re.search(r'[0-9]', pw):
        score += 1
    if re.search(r'[^A-Za-z0-9]', pw):
        score += 1
    label = ["Too short", "Weak", "Fair", "Good", "Strong"][score]
    return score, label


_STRENGTH_CLR = ["#E84040", "#E84040", "#E87000", "#F0A500", "#2BA22B"]


class SetupScreen(ctk.CTkFrame):
    """Shown on first launch — user creates their root account."""

    def __init__(self, master, on_done: Callable):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_done = on_done
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Centre card ───────────────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=16,
                            border_width=1, border_color=CLR_BORDER,
                            width=440)
        card.grid(row=0, column=0, padx=40, pady=40)
        card.grid_columnconfigure(0, weight=1)

        # Brand strip
        brand = ctk.CTkFrame(card, fg_color=CLR_ACCENT, corner_radius=0,
                             height=5)
        brand.grid(row=0, column=0, sticky="ew")

        # Icon + heading
        ctk.CTkLabel(card, text="🔐",
                     font=("Segoe UI Emoji", 42)
                     ).grid(row=1, column=0, pady=(28, 4))

        ctk.CTkLabel(card, text="Welcome to",
                     font=FONT_SMALL, text_color=CLR_MUTED
                     ).grid(row=2, column=0)

        ctk.CTkLabel(card, text=APP_NAME,
                     font=FONT_HEADING, text_color=CLR_TEXT
                     ).grid(row=3, column=0, padx=PAD)

        ctk.CTkLabel(card, text=f"v{APP_VERSION}  ·  First-time setup",
                     font=FONT_CAPTION, text_color=CLR_MUTED
                     ).grid(row=4, column=0, pady=(2, 18))

        # Divider
        ctk.CTkFrame(card, fg_color=CLR_BORDER, height=1
                     ).grid(row=5, column=0, sticky="ew", padx=PAD)

        ctk.CTkLabel(card,
                     text="Create your root account to get started.\n"
                          "You will need these credentials every time you open the app.",
                     font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     justify="center", wraplength=380
                     ).grid(row=6, column=0, padx=PAD, pady=(14, 18))

        # ── Form ─────────────────────────────────────────────────────
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.grid(row=7, column=0, padx=PAD, pady=(0, 8), sticky="ew")
        form.grid_columnconfigure(0, weight=1)

        # Username
        ctk.CTkLabel(form, text="Username", font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, anchor="w"
                     ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._username = ctk.CTkEntry(
            form, placeholder_text="e.g. admin",
            font=FONT_BODY, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT, height=38, corner_radius=8,
        )
        self._username.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        # Password
        ctk.CTkLabel(form, text="Password", font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, anchor="w"
                     ).grid(row=2, column=0, sticky="w", pady=(0, 4))
        self._password = ctk.CTkEntry(
            form, placeholder_text="Minimum 8 characters",
            show="•", font=FONT_BODY, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT, height=38, corner_radius=8,
        )
        self._password.grid(row=3, column=0, sticky="ew")
        self._password.bind("<KeyRelease>", self._on_pw_change)

        # Strength bar
        self._strength_bar = ctk.CTkProgressBar(
            form, height=4, corner_radius=2,
            fg_color=CLR_SURFACE_ALT, progress_color=CLR_MUTED,
        )
        self._strength_bar.set(0)
        self._strength_bar.grid(row=4, column=0, sticky="ew", pady=(6, 2))
        self._strength_lbl = ctk.CTkLabel(
            form, text="", font=FONT_CAPTION, text_color=CLR_MUTED, anchor="w"
        )
        self._strength_lbl.grid(row=5, column=0, sticky="w", pady=(0, 14))

        # Confirm password
        ctk.CTkLabel(form, text="Confirm Password", font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, anchor="w"
                     ).grid(row=6, column=0, sticky="w", pady=(0, 4))
        self._confirm = ctk.CTkEntry(
            form, placeholder_text="Re-enter password",
            show="•", font=FONT_BODY, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT, height=38, corner_radius=8,
        )
        self._confirm.grid(row=7, column=0, sticky="ew", pady=(0, 6))

        # Error label
        self._error_lbl = ctk.CTkLabel(
            form, text="", font=FONT_CAPTION,
            text_color=CLR_DANGER, anchor="w", wraplength=380,
        )
        self._error_lbl.grid(row=8, column=0, sticky="w", pady=(0, 10))

        # Submit button
        self._btn = ctk.CTkButton(
            form, text="Create Account & Continue →",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#000000", height=42, corner_radius=BTN_R,
            command=self._submit,
        )
        self._btn.grid(row=9, column=0, sticky="ew", pady=(0, 4))

        # Tip
        ctk.CTkLabel(card,
                     text="🔒  Your credentials are stored locally on this device only.",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=8, column=0, padx=PAD, pady=(4, 24))

        # Focus username on open
        self.after(100, self._username.focus)
        self._password.bind("<Return>", lambda e: self._confirm.focus())
        self._confirm.bind("<Return>", lambda e: self._submit())

    def _on_pw_change(self, _event=None):
        pw = self._password.get()
        score, label = _strength(pw)
        self._strength_bar.set(score / 4)
        self._strength_bar.configure(progress_color=_STRENGTH_CLR[score])
        self._strength_lbl.configure(text=label, text_color=_STRENGTH_CLR[score])

    def _submit(self):
        username = self._username.get().strip()
        password = self._password.get()
        confirm  = self._confirm.get()

        if not username:
            self._error("Username cannot be empty.")
            return
        if len(username) < 3:
            self._error("Username must be at least 3 characters.")
            return
        if len(password) < _MIN_PW_LEN:
            self._error(f"Password must be at least {_MIN_PW_LEN} characters.")
            return
        if password != confirm:
            self._error("Passwords do not match.")
            return

        save_credentials(username, password)
        self._on_done()

    def _error(self, msg: str):
        self._error_lbl.configure(text=f"! {msg}")
