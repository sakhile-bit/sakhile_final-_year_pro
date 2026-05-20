"""Welcome / splash screen."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_ACCENT, CLR_TEXT, CLR_MUTED,
    CLR_BORDER,
    FONT_TITLE, FONT_SUBTITLE, FONT_BODY, PAD, APP_NAME, APP_VERSION,
)


class WelcomeScreen(ctk.CTkFrame):
    """First screen shown when the app launches."""

    def __init__(self, master, on_start):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_start = on_start
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # ── Centre card ────────────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=20, border_width=1, border_color=CLR_BORDER)
        card.grid(row=0, column=0, padx=100, pady=50, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        accent_bar = ctk.CTkFrame(card, fg_color=CLR_ACCENT, height=6, corner_radius=4)
        accent_bar.grid(row=0, column=0, sticky="ew", pady=(0, 22), padx=24)

        icon = ctk.CTkLabel(
            card, text="🛡", font=("Segoe UI Emoji", 72),
            text_color=CLR_ACCENT,
        )
        icon.grid(row=1, column=0, pady=(0, 8))

        title = ctk.CTkLabel(
            card, text="Zambia Digital Hygiene\nCertification Program",
            font=FONT_TITLE, text_color=CLR_TEXT, justify="center",
        )
        title.grid(row=2, column=0, padx=PAD, pady=(0, 8))

        subtitle = ctk.CTkLabel(
            card,
            text="Assess your business against 15 essential cybersecurity controls\n"
                 "aligned to NIST CSF, CIS Controls v8, ISO 27001 & Cyber Essentials.",
            font=FONT_SUBTITLE, text_color=CLR_MUTED, justify="center",
        )
        subtitle.grid(row=3, column=0, padx=PAD, pady=(0, 26))

        features_frame = ctk.CTkFrame(card, fg_color="transparent")
        features_frame.grid(row=4, column=0, padx=40, pady=(0, 28), sticky="ew")
        features_frame.grid_columnconfigure((0, 1), weight=1)

        features = [
            ("✅", "5 automated Windows security checks"),
            ("📋", "10 guided manual assessment questions"),
            ("🏅", "Bronze / Silver / Gold certification"),
            ("📄", "Downloadable assessment report"),
        ]
        for r, (icon_txt, label_txt) in enumerate(features):
            row = r // 2
            col = r % 2
            item = ctk.CTkFrame(features_frame, fg_color=CLR_SURFACE_ALT, corner_radius=12, border_width=1, border_color=CLR_BORDER)
            item.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
            item.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                item, text=icon_txt,
                font=("Segoe UI Emoji", 18), text_color=CLR_ACCENT,
            ).grid(row=0, column=0, padx=14, pady=14)
            ctk.CTkLabel(
                item, text=label_txt,
                font=FONT_BODY, text_color=CLR_TEXT, anchor="w",
            ).grid(row=0, column=1, sticky="w", pady=14)

        start_btn = ctk.CTkButton(
            card, text="Start Desktop Assessment",
            font=("Segoe UI", 16, "bold"),
            fg_color=CLR_ACCENT, hover_color="#00A87A",
            text_color="#000000", height=50, corner_radius=24,
            command=self._on_start,
        )
        start_btn.grid(row=5, column=0, pady=(0, 36), ipadx=10)

        footer = ctk.CTkLabel(
            self,
            text=f"{APP_NAME}  v{APP_VERSION}  •  University of Zambia  •  Dept. of Computing & Informatics",
            font=("Segoe UI", 9), text_color=CLR_MUTED,
        )
        footer.grid(row=1, column=0, pady=(0, 12))
