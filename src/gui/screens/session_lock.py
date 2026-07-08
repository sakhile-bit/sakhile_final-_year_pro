"""
Session Lock screen.

Shown when no session is active — on launch (before the first sign-in) and
after the user terminates their session. It presents a clear **Start Session**
button that authenticates the user, so the app is never sitting on a blank
window behind a popup.
"""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from src.gui.theme import (
    APP_NAME,
    APP_VERSION,
    BTN_H_LG,
    BTN_R,
    CLR_ACCENT,
    CLR_ACCENT_HOV,
    CLR_BG,
    CLR_BORDER,
    CLR_MUTED,
    CLR_SURFACE,
    CLR_SURFACE_ALT,
    CLR_TEXT,
    CLR_TEXT_SEC,
    FONT_CAPTION,
    FONT_SMALL,
)
from src.utils.auth import get_username


class SessionLockScreen(ctk.CTkFrame):
    """Full-window locked state with Start Session / Exit."""

    def __init__(self, master, on_start_session: Callable,
                 on_exit: Callable, ended: bool = False):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_start_session = on_start_session
        self._on_exit = on_exit
        self._ended = ended
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        card = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=18,
                            border_width=1, border_color=CLR_BORDER)
        card.grid(row=1, column=0)
        card.grid_columnconfigure(0, weight=1)

        # Accent top stripe
        ctk.CTkFrame(card, fg_color=CLR_ACCENT, height=4,
                     corner_radius=0).grid(row=0, column=0, sticky="ew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=1, column=0, padx=54, pady=40)
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(inner, text="🔒", font=("Segoe UI Emoji", 46),
                     ).grid(row=0, column=0, pady=(0, 6))

        ctk.CTkLabel(
            inner,
            text="Session Ended" if self._ended else APP_NAME,
            font=("Segoe UI", 20, "bold"), text_color=CLR_TEXT,
        ).grid(row=1, column=0)

        username = get_username()
        subtitle = (
            f"You signed out{(' of ' + username) if username else ''}. "
            "Start a session to continue."
            if self._ended else
            f"v{APP_VERSION}  ·  Start a session to continue"
        )
        ctk.CTkLabel(inner, text=subtitle, font=FONT_SMALL,
                     text_color=CLR_MUTED, wraplength=340, justify="center",
                     ).grid(row=2, column=0, pady=(4, 22))

        # Start Session — authenticates the user
        ctk.CTkButton(
            inner, text="🔓  Start Session",
            font=("Segoe UI", 13, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#000000", height=BTN_H_LG, corner_radius=BTN_R,
            width=300, command=self._on_start_session,
        ).grid(row=3, column=0, pady=(0, 10), sticky="ew")

        # Exit the app
        ctk.CTkButton(
            inner, text="Exit", font=FONT_SMALL,
            fg_color="transparent", border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC, hover_color=CLR_SURFACE_ALT,
            height=BTN_H_LG, corner_radius=BTN_R, width=300,
            command=self._on_exit,
        ).grid(row=4, column=0, sticky="ew")

        ctk.CTkLabel(self,
                     text="🔒  Local credentials only — nothing leaves this machine.",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=3, column=0, pady=(0, 16))
