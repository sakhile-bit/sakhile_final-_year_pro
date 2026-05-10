"""Welcome / splash screen."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_ACCENT, CLR_TEXT, CLR_MUTED,
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
        card = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=16)
        card.grid(row=0, column=0, padx=120, pady=60, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        # Shield icon (text-based)
        icon = ctk.CTkLabel(
            card, text="🛡", font=("Segoe UI Emoji", 72),
            text_color=CLR_ACCENT,
        )
        icon.grid(row=0, column=0, pady=(40, 8))

        title = ctk.CTkLabel(
            card, text="Zambia Digital Hygiene\nCertification Program",
            font=FONT_TITLE, text_color=CLR_TEXT, justify="center",
        )
        title.grid(row=1, column=0, padx=PAD, pady=(0, 6))

        subtitle = ctk.CTkLabel(
            card,
            text="Assess your business against 15 essential cybersecurity controls\n"
                 "aligned to NIST CSF, CIS Controls v8, ISO 27001 & Cyber Essentials.",
            font=FONT_SUBTITLE, text_color=CLR_MUTED, justify="center",
        )
        subtitle.grid(row=2, column=0, padx=PAD, pady=(0, 24))

        # Feature bullets
        features_frame = ctk.CTkFrame(card, fg_color="transparent")
        features_frame.grid(row=3, column=0, padx=60, pady=(0, 28))
        features = [
            ("✅", "5 automated Windows security checks"),
            ("📋", "10 guided manual assessment questions"),
            ("🏅", "Bronze / Silver / Gold certification"),
            ("📄", "Downloadable assessment report"),
        ]
        for r, (icon_txt, label_txt) in enumerate(features):
            ctk.CTkLabel(
                features_frame, text=icon_txt,
                font=("Segoe UI Emoji", 14), text_color=CLR_ACCENT,
            ).grid(row=r, column=0, sticky="w", padx=(0, 8), pady=3)
            ctk.CTkLabel(
                features_frame, text=label_txt,
                font=FONT_BODY, text_color=CLR_TEXT, anchor="w",
            ).grid(row=r, column=1, sticky="w", pady=3)

        start_btn = ctk.CTkButton(
            card, text="  Start Assessment  →",
            font=("Segoe UI", 15, "bold"),
            fg_color=CLR_ACCENT, hover_color="#00A87A",
            text_color="#000000", height=48, corner_radius=24,
            command=self._on_start,
        )
        start_btn.grid(row=4, column=0, pady=(0, 40))

        # ── Footer ──────────────────────────────────────────────────
        footer = ctk.CTkLabel(
            self,
            text=f"{APP_NAME}  v{APP_VERSION}  •  University of Zambia  •  Dept. of Computing & Informatics",
            font=("Segoe UI", 9), text_color=CLR_MUTED,
        )
        footer.grid(row=1, column=0, pady=(0, 10))
