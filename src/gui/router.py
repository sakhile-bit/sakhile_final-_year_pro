"""
Screen router — navigation stack for the desktop app.

The main window used to hardcode every transition (``on_back`` was almost
always "go to welcome") and swapped screens by destroying the current one
*before* building the next, so a constructor error left a blank window.

``Router`` replaces that with a proper navigation stack:

- screens are pushed and popped, so **back** is generic — a screen no
  longer needs to know who opened it;
- the new screen is built *before* the old one is destroyed, and any
  failure is caught and shown as a recoverable error screen instead of a
  blank window;
- ``reset_to`` collapses the stack for "home" destinations.

Each stack entry stores a *factory* (a zero-argument callable returning a
fresh screen) rather than a live widget, so going back rebuilds the screen
against the current :class:`~src.gui.state.AppState`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

import customtkinter as ctk

from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_BG,
    CLR_DANGER,
    CLR_MUTED,
    CLR_TEXT,
    FONT_BODY,
    FONT_HEADING,
    FONT_SMALL,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# A factory builds and returns a fresh screen widget parented to the app.
ScreenFactory = Callable[[], ctk.CTkFrame]


@dataclass
class NavEntry:
    name: str
    factory: ScreenFactory


class Router:
    """Owns the on-screen widget and the navigation history stack."""

    def __init__(self, container: ctk.CTk):
        self._container = container
        self._stack: List[NavEntry] = []
        self._current_widget: ctk.CTkFrame | None = None

    # ── introspection ────────────────────────────────────────────────
    @property
    def can_go_back(self) -> bool:
        return len(self._stack) > 1

    @property
    def current_name(self) -> str:
        return self._stack[-1].name if self._stack else ""

    @property
    def depth(self) -> int:
        return len(self._stack)

    def stack_names(self) -> List[str]:
        return [e.name for e in self._stack]

    # ── navigation ───────────────────────────────────────────────────
    def reset_to(self, name: str, factory: ScreenFactory) -> None:
        """Clear the whole stack and show ``name`` as the new root."""
        logger.debug("Router.reset_to(%s)", name)
        self._stack = [NavEntry(name, factory)]
        self._render(factory, direction=1)

    def push(self, name: str, factory: ScreenFactory) -> None:
        """Navigate deeper, remembering the current screen for back()."""
        logger.debug("Router.push(%s) depth=%d", name, len(self._stack) + 1)
        self._stack.append(NavEntry(name, factory))
        self._render(factory, direction=1)

    def replace(self, name: str, factory: ScreenFactory) -> None:
        """Swap the current screen without changing stack depth."""
        logger.debug("Router.replace(%s)", name)
        if self._stack:
            self._stack[-1] = NavEntry(name, factory)
        else:
            self._stack.append(NavEntry(name, factory))
        self._render(factory, direction=0)

    def back(self) -> bool:
        """Pop the current screen and rebuild the previous one.

        Returns False (and does nothing) when already at the root.
        """
        if not self.can_go_back:
            logger.debug("Router.back() ignored — at root")
            return False
        self._stack.pop()
        entry = self._stack[-1]
        logger.debug("Router.back() → %s", entry.name)
        self._render(entry.factory, direction=-1)
        return True

    # ── rendering ────────────────────────────────────────────────────
    def _render(self, factory: ScreenFactory, direction: int = 0) -> None:
        """Build the new screen, then retire the old one with an instant swap.

        Screen swaps are instant on purpose. Tk has no compositor, so
        sliding a full, widget-heavy screen (e.g. the two-panel welcome)
        repaints the whole tree every frame and visibly janks — worse when
        it overlaps the destination screen's own entrance animation. The
        new screen is packed *before* the old one is destroyed so a build
        failure can't strand the window blank and there's no blank flash.
        Individual screens still animate their own lightweight entrances
        (window fade-in, hover states, staggered cards).

        ``direction`` is accepted for call-site compatibility but no longer
        drives an animation.
        """
        try:
            new_widget = factory()
        except Exception:
            logger.exception("Failed to build screen '%s'", self.current_name)
            new_widget = self._build_error_screen()

        old_widget = self._current_widget
        self._current_widget = new_widget
        new_widget.pack(fill="both", expand=True)
        if old_widget is not None:
            try:
                old_widget.destroy()
            except Exception:  # pragma: no cover - defensive teardown
                logger.exception("Failed to destroy previous screen")

    def _build_error_screen(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self._container, fg_color=CLR_BG, corner_radius=0)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.grid(row=0, column=0)
        ctk.CTkLabel(inner, text="⚠", font=("Segoe UI Emoji", 48),
                     text_color=CLR_DANGER).pack(pady=(0, 8))
        ctk.CTkLabel(inner, text="This screen could not be opened",
                     font=FONT_HEADING, text_color=CLR_TEXT).pack()
        ctk.CTkLabel(
            inner,
            text="An unexpected error occurred. Your data is safe — "
                 "return home and try again.",
            font=FONT_SMALL, text_color=CLR_MUTED, wraplength=420,
            justify="center").pack(pady=(4, 16))
        ctk.CTkButton(
            inner, text="⌂  Back to Home", font=FONT_BODY,
            fg_color=CLR_ACCENT, text_color="#FFFFFF",
            height=BTN_H, corner_radius=BTN_R,
            command=self._go_home).pack()
        return frame

    def _go_home(self) -> None:
        # Collapse to the root entry (welcome) if we have one.
        if self._stack:
            root = self._stack[0]
            self._stack = [root]
            self._render(root.factory)
