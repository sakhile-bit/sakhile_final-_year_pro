"""Past assessments history screen."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_ACCENT, CLR_TEXT, CLR_MUTED,
    CLR_BORDER, CLR_SUCCESS, CLR_WARNING, CLR_DANGER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, PAD,
    TIER_COLOURS,
)

TIER_ICON = {"GOLD": "🥇", "SILVER": "🥈", "BRONZE": "🥉", "NOT CERTIFIED": "❌"}


class HistoryScreen(ctk.CTkFrame):
    """Shows a list of past assessments saved to local storage."""

    def __init__(self, master, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back
        self._rows: list[dict] = []
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=72)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="Past Assessments",
            font=FONT_HEADING, text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=PAD, pady=(16, 16), sticky="w")

        # Scrollable list
        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)

        from src.utils.local_db import list_assessments, delete_assessment
        self._rows = list_assessments()

        if not self._rows:
            ctk.CTkLabel(
                scroll,
                text="No assessments saved yet.\nComplete an assessment and it will appear here.",
                font=FONT_BODY, text_color=CLR_MUTED, justify="center",
            ).grid(row=0, column=0, pady=80)
        else:
            for i, row in enumerate(self._rows):
                self._add_row(scroll, i, row, delete_assessment)

        # Nav bar
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=64)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_columnconfigure(0, weight=0)
        ctk.CTkButton(
            nav, text="← Back to Home",
            font=FONT_BODY,
            fg_color="transparent", border_color=CLR_MUTED, border_width=1,
            text_color=CLR_TEXT, hover_color="#243447", width=150, height=38,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

    def _add_row(self, parent, idx, row, delete_fn):
        tier = row["tier"]
        tier_clr = TIER_COLOURS.get(tier, CLR_DANGER)
        icon = TIER_ICON.get(tier, "❌")

        card = ctk.CTkFrame(
            parent, fg_color=CLR_SURFACE,
            corner_radius=14, border_width=1, border_color=CLR_BORDER,
        )
        card.grid(row=idx, column=0, padx=PAD, pady=6, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # Tier icon
        ctk.CTkLabel(
            card, text=icon, font=("Segoe UI Emoji", 26),
        ).grid(row=0, column=0, rowspan=2, padx=(16, 10), pady=16)

        # Business name + date
        ctk.CTkLabel(
            card, text=row["biz_name"],
            font=("Segoe UI", 13, "bold"), text_color=CLR_TEXT, anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=(14, 0))

        meta = f"{row['biz_id']}  •  {row['province']}  •  {row['industry']}  •  {row['saved_at'][:10]}"
        ctk.CTkLabel(
            card, text=meta,
            font=FONT_SMALL, text_color=CLR_MUTED, anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(0, 14))

        # Score pill
        ctk.CTkLabel(
            card, text=f"{row['pct']}%  {tier}",
            font=("Segoe UI", 11, "bold"), text_color=tier_clr,
            fg_color=CLR_SURFACE_ALT, corner_radius=8,
            width=110, height=28,
        ).grid(row=0, column=2, rowspan=2, padx=(0, 8))

        # Delete button
        row_id = row["id"]
        ctk.CTkButton(
            card, text="🗑", width=36, height=36,
            fg_color="transparent", hover_color="#3a1a1a",
            text_color=CLR_DANGER, font=("Segoe UI Emoji", 14),
            corner_radius=8,
            command=lambda rid=row_id, c=card: self._confirm_delete(rid, c, delete_fn),
        ).grid(row=0, column=3, rowspan=2, padx=(0, 12))

    def _confirm_delete(self, row_id: int, card: ctk.CTkFrame, delete_fn):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Delete Assessment")
        dlg.geometry("380x160")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()
        ctk.CTkLabel(
            dlg, text="Delete this assessment record?",
            font=FONT_BODY, text_color=CLR_TEXT,
        ).pack(pady=(28, 6))
        ctk.CTkLabel(
            dlg, text="This cannot be undone.",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).pack(pady=(0, 18))
        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack()
        ctk.CTkButton(
            btn_row, text="Cancel", width=100,
            fg_color="transparent", border_color=CLR_MUTED, border_width=1,
            text_color=CLR_TEXT, hover_color="#243447",
            command=dlg.destroy,
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_row, text="Delete", width=100,
            fg_color=CLR_DANGER, hover_color="#c0392b",
            text_color="#ffffff",
            command=lambda: self._do_delete(row_id, card, dlg, delete_fn),
        ).pack(side="left", padx=8)

    def _do_delete(self, row_id: int, card: ctk.CTkFrame, dlg, delete_fn):
        delete_fn(row_id)
        dlg.destroy()
        card.destroy()
