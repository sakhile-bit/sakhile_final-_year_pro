"""GUI Enhancement Utilities — advanced styling components and layouts."""

import customtkinter as ctk

from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_ACCENT_DIM,
    CLR_ACCENT_HOV,
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
)


class StatsCard(ctk.CTkFrame):
    """Enhanced statistics card with icon, value, and label."""

    def __init__(self, parent, icon: str, label: str, value: str, color: str, **kwargs):
        super().__init__(
            parent,
            fg_color=CLR_SURFACE,
            corner_radius=10,
            border_width=1,
            border_color=CLR_BORDER,
            **kwargs
        )

        self.grid_columnconfigure(0, weight=1)

        # Icon
        ctk.CTkLabel(
            self, text=icon, font=("Segoe UI Emoji", 28), text_color=color
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        # Label
        ctk.CTkLabel(
            self, text=label, font=FONT_SMALL, text_color=CLR_TEXT_SEC
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        # Value
        ctk.CTkLabel(
            self, text=value, font=("Segoe UI", 24, "bold"), text_color=color
        ).grid(row=2, column=0, padx=16, pady=(0, 12), sticky="w")


class GradientCard(ctk.CTkFrame):
    """Card with colored left border accent."""

    def __init__(self, parent, accent_color: str, **kwargs):
        super().__init__(
            parent,
            fg_color=CLR_SURFACE,
            corner_radius=10,
            border_width=2,
            border_color=accent_color,
            **kwargs
        )

        # Visual accent line on the left
        accent_frame = ctk.CTkFrame(
            self, fg_color=accent_color, width=4, corner_radius=0
        )
        accent_frame.pack(side="left", fill="y", padx=(0, 12))
        accent_frame.pack_propagate(False)


class EnhancedButton(ctk.CTkButton):
    """Enhanced button with better styling and feedback."""

    def __init__(
        self,
        parent,
        text: str,
        command=None,
        primary: bool = True,
        icon: str = "",
        **kwargs
    ):
        fg_color = CLR_ACCENT if primary else CLR_SURFACE_ALT
        hover_color = CLR_ACCENT_HOV if primary else CLR_SURFACE_HVR
        text_color = "#ffffff" if primary else CLR_TEXT

        button_text = f"{icon} {text}" if icon else text

        super().__init__(
            parent,
            text=button_text,
            command=command,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            font=FONT_BODY,
            height=BTN_H,
            corner_radius=BTN_R,
            border_width=0,
            **kwargs
        )


class SectionHeader(ctk.CTkFrame):
    """Section header with icon, title, and optional action button."""

    def __init__(self, parent, icon: str, title: str, action_text: str = "", on_action=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        # Left side: icon and title
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(left, text=icon, font=("Segoe UI Emoji", 18)).pack(
            side="left", padx=(0, 8)
        )

        ctk.CTkLabel(
            left, text=title, font=FONT_SUBHEAD, text_color=CLR_TEXT
        ).pack(side="left")

        # Right side: action button
        if action_text and on_action:
            btn = ctk.CTkButton(
                self,
                text=action_text,
                command=on_action,
                fg_color=CLR_ACCENT_DIM,
                hover_color=CLR_ACCENT,
                text_color=CLR_ACCENT,
                font=FONT_SMALL,
                height=28,
                corner_radius=4,
                border_width=0,
            )
            btn.grid(row=0, column=1, sticky="e", padx=(12, 0))


class DataItem(ctk.CTkFrame):
    """Data display item with label and value."""

    def __init__(self, parent, label: str, value: str, value_color: str = CLR_TEXT, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(1, weight=1)

        # Label (left)
        ctk.CTkLabel(
            self, text=label, font=FONT_BODY, text_color=CLR_TEXT_SEC
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        # Value (right)
        ctk.CTkLabel(
            self, text=value, font=FONT_BODY, text_color=value_color
        ).grid(row=0, column=1, sticky="e")


class StatusBadge(ctk.CTkFrame):
    """Status badge with color coding."""

    def __init__(self, parent, status: str, **kwargs):
        status_color_map = {
            "PASS": CLR_SUCCESS,
            "FAIL": CLR_DANGER,
            "WARNING": CLR_WARNING,
            "PENDING": CLR_MUTED,
            "ACTIVE": CLR_SUCCESS,
            "INACTIVE": CLR_MUTED,
        }

        color = status_color_map.get(status.upper(), CLR_MUTED)

        super().__init__(
            parent,
            fg_color=CLR_SURFACE_ALT,
            corner_radius=4,
            border_width=1,
            border_color=color,
            **kwargs
        )

        ctk.CTkLabel(
            self, text=status, font=FONT_CAPTION, text_color=color
        ).pack(padx=6, pady=3)


class ProgressIndicator(ctk.CTkFrame):
    """Circular or linear progress indicator."""

    def __init__(self, parent, value: float, max_value: float = 100.0, mode: str = "linear", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        percentage = (value / max_value) * 100 if max_value > 0 else 0

        if mode == "linear":
            # Linear progress bar with percentage label
            self.grid_columnconfigure(0, weight=1)

            # Progress bar
            progress = ctk.CTkProgressBar(
                self,
                value=percentage / 100,
                fg_color=CLR_SURFACE_ALT,
                progress_color=CLR_ACCENT,
                height=6,
                corner_radius=3,
            )
            progress.grid(row=0, column=0, sticky="ew")

            # Percentage label
            label = ctk.CTkLabel(
                self,
                text=f"{int(percentage)}%",
                font=FONT_SMALL,
                text_color=CLR_ACCENT,
            )
            label.grid(row=0, column=1, padx=(8, 0))


class ControlCard(ctk.CTkFrame):
    """Enhanced control assessment card."""

    def __init__(
        self,
        parent,
        control_id: str,
        name: str,
        status: str,
        details: str = "",
        on_select=None,
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=CLR_SURFACE,
            corner_radius=8,
            border_width=1,
            border_color=CLR_BORDER,
            **kwargs
        )

        self.grid_columnconfigure(1, weight=1)

        # Status indicator color
        status_colors = {
            "PASS": CLR_SUCCESS,
            "FAIL": CLR_DANGER,
            "WARNING": CLR_WARNING,
            "PENDING": CLR_MUTED,
        }
        status_color = status_colors.get(status, CLR_MUTED)

        # Status badge
        status_icon = {
            "PASS": "✔",
            "FAIL": "✖",
            "WARNING": "⚠",
            "PENDING": "○",
        }.get(status, "?")

        badge = ctk.CTkLabel(
            self,
            text=status_icon,
            font=("Segoe UI Emoji", 18),
            text_color=status_color,
        )
        badge.grid(row=0, column=0, padx=12, pady=12, sticky="n")

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=12)
        content.grid_columnconfigure(0, weight=1)

        # Control ID and name
        ctk.CTkLabel(
            content,
            text=f"{control_id}: {name}",
            font=FONT_BODY,
            text_color=CLR_TEXT,
        ).pack(anchor="w")

        # Details
        if details:
            ctk.CTkLabel(
                content,
                text=details,
                font=FONT_SMALL,
                text_color=CLR_TEXT_SEC,
                wraplength=400,
            ).pack(anchor="w", pady=(2, 0))

        # Action button
        if on_select:
            btn = ctk.CTkButton(
                self,
                text="→",
                command=on_select,
                fg_color=CLR_ACCENT_DIM,
                hover_color=CLR_ACCENT,
                text_color=CLR_ACCENT,
                font=("Segoe UI", 12, "bold"),
                width=32,
                height=32,
                corner_radius=4,
                border_width=0,
            )
            btn.grid(row=0, column=2, padx=12, pady=12)
