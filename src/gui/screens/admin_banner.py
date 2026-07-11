"""
Elevation banner
================
A slim, dismissible strip shown at the top of the app when it is running
*without* administrator rights on Windows. Several features — the Server
Hardening one-click fixes in particular — need elevation, so this offers a
one-tap "Relaunch as administrator" (Windows UAC) instead of leaving the
user to guess why the Fix buttons are greyed out.

Non-Windows, or when already elevated, ``should_offer_elevation()`` returns
False and nothing is shown.
"""

from __future__ import annotations

import platform
import subprocess
import sys

import customtkinter as ctk

from src.gui import motion
from src.gui.theme import (
    BTN_R,
    CLR_AMBER,
    CLR_AMBER_DIM,
    CLR_BORDER,
    CLR_TEXT,
    CLR_TEXT_SEC,
    FONT_SMALL,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def is_admin() -> bool:
    """True when this process already has administrator rights (Windows)."""
    if platform.system() != "Windows":
        return False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def should_offer_elevation() -> bool:
    """Only offer to elevate on Windows when not already elevated."""
    return platform.system() == "Windows" and not is_admin()


def relaunch_as_admin() -> bool:
    """Relaunch this app elevated via the UAC prompt.

    Returns True when a new elevated instance was started (the caller should
    then close the current one); False when the user declined UAC or the
    relaunch could not be started, so the app keeps running unelevated.
    """
    if platform.system() != "Windows":
        return False
    try:
        import ctypes
        if getattr(sys, "frozen", False):
            exe = sys.executable                    # the packaged .exe
            params = subprocess.list2cmdline(sys.argv[1:])
        else:
            exe = sys.executable                    # python.exe
            params = subprocess.list2cmdline(sys.argv)
        # ShellExecuteW returns a value > 32 on success.
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe, params, None, 1)
        if int(rc) > 32:
            return True
        logger.info("Elevation declined or failed (ShellExecute rc=%s)", rc)
        return False
    except Exception:
        logger.warning("Relaunch as admin failed", exc_info=True)
        return False


class AdminBanner(ctk.CTkFrame):
    """Thin amber strip offering to relaunch elevated. Dismissible."""

    def __init__(self, master, on_relaunch, on_dismiss=None):
        super().__init__(master, fg_color=CLR_AMBER_DIM, corner_radius=0,
                         height=40, border_width=0)
        self._on_relaunch = on_relaunch
        self._on_dismiss = on_dismiss
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)

        # A subtle amber underline so it reads as a distinct band.
        ctk.CTkFrame(self, fg_color=CLR_AMBER, height=2, corner_radius=0,
                     ).grid(row=1, column=0, columnspan=4, sticky="ew")

        ctk.CTkLabel(self, text="🛡️", font=("Segoe UI Emoji", 14),
                     ).grid(row=0, column=0, padx=(14, 8), pady=8)
        ctk.CTkLabel(
            self,
            text="Running without administrator rights — one-click fixes and "
                 "some hardening actions are disabled.",
            font=FONT_SMALL, text_color=CLR_TEXT_SEC, anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=8)

        self._relaunch_btn = ctk.CTkButton(
            self, text="Relaunch as administrator",
            font=("Segoe UI", 11, "bold"),
            fg_color=CLR_AMBER, hover_color="#C79020", text_color="#1A1500",
            height=26, corner_radius=BTN_R, command=self._relaunch,
        )
        self._relaunch_btn.grid(row=0, column=2, padx=(8, 6), pady=7)

        ctk.CTkButton(
            self, text="✕", width=28, height=26,
            font=("Segoe UI", 12, "bold"),
            fg_color="transparent", hover_color=CLR_BORDER,
            text_color=CLR_TEXT, corner_radius=BTN_R, command=self._dismiss,
        ).grid(row=0, column=3, padx=(0, 10), pady=7)

    def _relaunch(self):
        self._relaunch_btn.configure(state="disabled", text="Requesting…")
        if self._on_relaunch():
            return  # app is closing to hand off to the elevated instance
        # UAC declined — re-enable so they can try again.
        self._relaunch_btn.configure(
            state="normal", text="Relaunch as administrator")

    def _dismiss(self):
        try:
            self.pack_forget()
            self.destroy()
        except Exception:
            pass
        if self._on_dismiss is not None:
            self._on_dismiss()

    def reveal(self, before=None):
        """Pack above the current screen and slide down into view.

        ``before`` is the currently-shown screen widget, so the banner is
        inserted *above* it in pack order rather than squeezed below an
        expand-filled screen.
        """
        try:
            if before is not None and before.winfo_exists():
                self.pack(side="top", fill="x", before=before)
            else:
                self.pack(side="top", fill="x")
            self.lift()
        except Exception:
            self.pack(side="top", fill="x")
        motion.slide_down_reveal(self)
