"""Login popup — small modal dialog shown on every launch after first setup."""
from __future__ import annotations

import customtkinter as ctk
from typing import Callable

from src.gui.theme import (
    APP_NAME, APP_VERSION,
    CLR_SURFACE, CLR_SURFACE_ALT, CLR_BORDER,
    CLR_ACCENT, CLR_ACCENT_HOV, CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_DANGER,
    FONT_BODY, FONT_SMALL, FONT_CAPTION,
    BTN_R,
)
from src.utils.auth import get_username, verify

_MAX_ATTEMPTS = 5
_W, _H = 380, 310


class LoginScreen(ctk.CTkToplevel):
    """Small modal login popup — blocks the main window until authenticated."""

    def __init__(self, master, on_success: Callable):
        super().__init__(master)
        self._on_success = on_success
        self._attempts = 0

        # ── Window setup ─────────────────────────────────────────────
        self.title(f"{APP_NAME}  v{APP_VERSION}")
        self.geometry(f"{_W}x{_H}")
        self.resizable(False, False)
        self.configure(fg_color=CLR_SURFACE)

        # Closing the dialog exits the whole app
        self.protocol("WM_DELETE_WINDOW", master.destroy)

        # Centre on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{_W}x{_H}+{(sw - _W) // 2}+{(sh - _H) // 2}")

        self._build()

        # Force to front AFTER building — CTkToplevel on Windows needs this
        self.after(50, self._force_focus)

    def _build(self):
        # ── Accent bar at top ─────────────────────────────────────────
        ctk.CTkFrame(self, fg_color=CLR_ACCENT, height=4,
                     corner_radius=0).pack(fill="x")

        # ── Icon + app name ───────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(pady=(18, 4))

        ctk.CTkLabel(top, text="🔐",
                     font=("Segoe UI Emoji", 30)
                     ).pack(side="left", padx=(0, 10))

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left")
        ctk.CTkLabel(info, text=APP_NAME,
                     font=("Segoe UI", 13, "bold"),
                     text_color=CLR_TEXT, anchor="w"
                     ).pack(anchor="w")
        ctk.CTkLabel(info, text=f"v{APP_VERSION}  ·  Enter your password to continue",
                     font=FONT_CAPTION, text_color=CLR_MUTED, anchor="w"
                     ).pack(anchor="w")

        # Divider
        ctk.CTkFrame(self, fg_color=CLR_BORDER, height=1
                     ).pack(fill="x", padx=20, pady=(10, 0))

        # ── Form ──────────────────────────────────────────────────────
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=16)

        # Username — read-only, pre-filled
        ctk.CTkLabel(form, text="Username", font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, anchor="w"
                     ).pack(anchor="w", pady=(0, 3))

        user_entry = ctk.CTkEntry(
            form, font=FONT_BODY, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_MUTED, height=36, corner_radius=7,
            state="normal",
        )
        user_entry.insert(0, get_username())
        user_entry.configure(state="disabled")
        user_entry.pack(fill="x", pady=(0, 12))

        # Password
        ctk.CTkLabel(form, text="Password", font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, anchor="w"
                     ).pack(anchor="w", pady=(0, 3))

        self._password = ctk.CTkEntry(
            form, placeholder_text="Enter password",
            show="•", font=FONT_BODY, fg_color=CLR_SURFACE_ALT,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT, height=36, corner_radius=7,
        )
        self._password.pack(fill="x")
        self._password.bind("<Return>", lambda e: self._submit())

        # Error label
        self._error_lbl = ctk.CTkLabel(
            form, text="", font=FONT_CAPTION,
            text_color=CLR_DANGER, anchor="w", wraplength=320,
        )
        self._error_lbl.pack(anchor="w", pady=(5, 0))

        # ── Sign In button ────────────────────────────────────────────
        self._btn = ctk.CTkButton(
            self, text="Sign In  →",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#000000", height=40, corner_radius=BTN_R,
            command=self._submit,
        )
        self._btn.pack(fill="x", padx=24, pady=(4, 14))

        # Footer
        ctk.CTkLabel(self,
                     text="🔒  Local credentials only — not sent anywhere.",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).pack(pady=(0, 10))

        # Focus is handled by _force_focus() called after event loop starts

    def _force_focus(self):
        """Bring dialog to front and grab input — must run after event loop starts."""
        try:
            self.lift()
            self.attributes("-topmost", True)

            def _release_topmost():
                try:
                    self.attributes("-topmost", False)
                except Exception:
                    pass

            self.after(10, _release_topmost)

            try:
                self.grab_set()
            except Exception:
                # grab_set can fail if another window holds the grab;
                # the dialog still works — focus just isn't forced
                pass

            self.focus_force()
            self._password.focus()
        except Exception:
            pass

    def _error(self, msg: str):
        self._error_lbl.configure(text=f"! {msg}")

    def _submit(self):
        if self._attempts >= _MAX_ATTEMPTS:
            return

        username = get_username()
        password = self._password.get()

        if verify(username, password):
            self.grab_release()
            self.destroy()
            self._on_success()
        else:
            self._attempts += 1
            remaining = _MAX_ATTEMPTS - self._attempts
            if remaining > 0:
                self._error(f"Incorrect password. {remaining} attempt(s) remaining.")
            else:
                self._error("Too many failed attempts. Closing app.")
                self._btn.configure(state="disabled")
                self.after(2000, self.master.destroy)
            self._password.delete(0, "end")
