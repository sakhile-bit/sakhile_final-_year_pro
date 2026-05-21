"""Past assessments history screen."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_ACCENT_HOV,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER,
    FONT_TITLE, FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, HDR_H, NAV_H, BTN_H, BTN_R,
    TIER_COLOURS,
)

TIER_ICON = {
    "GOLD": "🥇", "SILVER": "🥈",
    "BRONZE": "🥉", "NOT CERTIFIED": "✕",
}
STATUS_CLR = {
    "PASS": CLR_SUCCESS, "WARNING": CLR_WARNING,
    "FAIL": CLR_DANGER, "ERROR": CLR_WARNING, "NOT_ASSESSED": CLR_MUTED,
}
STATUS_ICON = {
    "PASS": "✔", "WARNING": "⚠", "FAIL": "✖",
    "ERROR": "!", "NOT_ASSESSED": "–",
}


class HistoryScreen(ctk.CTkFrame):

    def __init__(self, master, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                           height=HDR_H)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        hdr.grid_propagate(False)
        ctk.CTkLabel(hdr, text="Past Assessments",
                     font=FONT_TITLE, text_color=CLR_TEXT,
                     ).grid(row=0, column=0, padx=PAD, pady=18, sticky="w")

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        from src.utils.local_db import list_assessments, delete_assessment
        rows = list_assessments()

        if not rows:
            ctk.CTkLabel(
                scroll,
                text="No assessments saved yet.\n"
                     "Complete an assessment and it will appear here.",
                font=FONT_BODY, text_color=CLR_MUTED, justify="center",
            ).grid(row=0, column=0, pady=80)
        else:
            for i, row in enumerate(rows):
                self._add_row(scroll, i, row, delete_assessment)

        # Nav
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                           height=NAV_H)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_propagate(False)
        ctk.CTkButton(
            nav, text="← Back to Home", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC, hover_color=CLR_SURFACE_ALT,
            width=150, height=BTN_H, corner_radius=BTN_R,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

    def _add_row(self, parent, idx, row, delete_fn):
        tier = row["tier"]
        tier_clr = TIER_COLOURS.get(tier, CLR_DANGER)
        icon = TIER_ICON.get(tier, "✕")
        pct = row["pct"]

        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=14,
                            border_width=1, border_color=CLR_BORDER)
        card.grid(row=idx, column=0, padx=PAD, pady=5, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # Tier badge (coloured left stripe)
        badge = ctk.CTkFrame(card, fg_color=tier_clr, width=6,
                             corner_radius=0)
        badge.grid(row=0, column=0, rowspan=2, sticky="ns",
                   padx=(0, 0), pady=0)

        # Tier icon
        ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 24),
                     ).grid(row=0, column=1, rowspan=2,
                            padx=(14, 10), pady=14)

        # Business name
        ctk.CTkLabel(card, text=row["biz_name"],
                     font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
                     ).grid(row=0, column=2, sticky="w", pady=(14, 1))

        # Meta line
        parts = [p for p in [row.get("biz_id"), row.get("province"),
                              row.get("industry"),
                              row.get("saved_at", "")[:10]] if p]
        ctk.CTkLabel(card, text="  ·  ".join(parts),
                     font=FONT_CAPTION, text_color=CLR_MUTED, anchor="w",
                     ).grid(row=1, column=2, sticky="w", pady=(0, 14))

        # Score pill
        ctk.CTkLabel(
            card, text=f"{pct}%  {tier}",
            font=("Segoe UI", 10, "bold"), text_color=tier_clr,
            fg_color=CLR_SURFACE_ALT, corner_radius=8,
            width=100, height=26,
        ).grid(row=0, column=3, rowspan=2, padx=(0, 8))

        row_id = row["id"]

        # View button
        ctk.CTkButton(
            card, text="👁", width=34, height=34,
            fg_color="transparent", hover_color="#1B3A5C",
            text_color=CLR_ACCENT, font=("Segoe UI Emoji", 13),
            corner_radius=8,
            command=lambda rid=row_id: self._show_details(rid),
        ).grid(row=0, column=4, rowspan=2, padx=(0, 4))

        # Delete button
        ctk.CTkButton(
            card, text="🗑", width=34, height=34,
            fg_color="transparent", hover_color="#3A1A1A",
            text_color=CLR_DANGER, font=("Segoe UI Emoji", 13),
            corner_radius=8,
            command=lambda rid=row_id, c=card: self._confirm_delete(
                rid, c, delete_fn),
        ).grid(row=0, column=5, rowspan=2, padx=(0, 12))

    # ----------------------------------------------------------------- details
    def _show_details(self, row_id: int):
        from src.utils.local_db import get_assessment
        data = get_assessment(row_id)
        if not data:
            return

        tier = data.get("certification_level", "—")
        tier_clr = TIER_COLOURS.get(tier, CLR_DANGER)
        pct = data.get("percentage", 0)
        biz = data.get("business", {})

        dlg = ctk.CTkToplevel(self)
        dlg.title("Assessment Details")
        dlg.geometry("680x540")
        dlg.configure(fg_color=CLR_BG)
        dlg.grab_set()

        # Header
        hdr = ctk.CTkFrame(dlg, fg_color=CLR_SURFACE, corner_radius=0,
                           height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr,
            text=f"{TIER_ICON.get(tier, '')}  "
                 f"{biz.get('name', '—')}  —  {tier}  ({pct}%)",
            font=FONT_SUBHEAD, text_color=tier_clr,
        ).pack(side="left", padx=PAD, pady=18)
        ctk.CTkLabel(
            hdr,
            text=f"{biz.get('id', '')}  ·  "
                 f"{data.get('assessment_date', '')[:10]}",
            font=FONT_CAPTION, text_color=CLR_MUTED,
        ).pack(side="right", padx=PAD)

        # Scrollable breakdown
        scroll = ctk.CTkScrollableFrame(dlg, fg_color=CLR_BG, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)

        for i, (_, ctrl) in enumerate(data.get("controls", {}).items()):
            status = ctrl.get("status", "—")
            clr = STATUS_CLR.get(status, CLR_MUTED)
            icon = STATUS_ICON.get(status, "?")

            rf = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=10,
                              border_width=1, border_color=CLR_BORDER)
            rf.grid(row=i, column=0, padx=12, pady=3, sticky="ew")
            rf.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(rf, text=icon, font=("Segoe UI", 12),
                         text_color=clr, width=26,
                         ).grid(row=0, column=0, padx=(12, 6),
                                pady=(10, 2), sticky="n")
            ctk.CTkLabel(rf,
                         text=f"{ctrl.get('id', '')}  {ctrl.get('name', '')}",
                         font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
                         ).grid(row=0, column=1, sticky="w", pady=(10, 2))
            ctk.CTkLabel(rf,
                         text=f"{ctrl.get('score', 0)}/{ctrl.get('weight', 0)} pts",
                         font=("Segoe UI", 10, "bold"), text_color=clr,
                         ).grid(row=0, column=2, padx=12, pady=(10, 2), sticky="e")
            if ctrl.get("details"):
                ctk.CTkLabel(rf, text=ctrl["details"], font=FONT_CAPTION,
                             text_color=CLR_MUTED, wraplength=560,
                             justify="left", anchor="w",
                             ).grid(row=1, column=0, columnspan=3,
                                    padx=(44, 12), pady=(0, 8), sticky="w")

        ctk.CTkButton(
            dlg, text="Close", height=BTN_H, corner_radius=BTN_R,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_BORDER,
            text_color=CLR_TEXT, font=FONT_BODY, command=dlg.destroy,
        ).pack(pady=10)

    # ----------------------------------------------------------------- delete
    def _confirm_delete(self, row_id, card, delete_fn):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Delete Assessment")
        dlg.geometry("360x150")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="Delete this assessment record?",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(pady=(24, 4))
        ctk.CTkLabel(dlg, text="This cannot be undone.",
                     font=FONT_SMALL, text_color=CLR_MUTED,
                     ).pack(pady=(0, 16))

        row = ctk.CTkFrame(dlg, fg_color="transparent")
        row.pack()
        ctk.CTkButton(row, text="Cancel", width=100,
                      fg_color="transparent", border_color=CLR_BORDER,
                      border_width=1, text_color=CLR_TEXT_SEC,
                      hover_color=CLR_SURFACE_ALT,
                      command=dlg.destroy).pack(side="left", padx=8)
        ctk.CTkButton(row, text="Delete", width=100,
                      fg_color=CLR_DANGER, hover_color="#B02020",
                      text_color="#ffffff",
                      command=lambda: self._do_delete(
                          row_id, card, dlg, delete_fn),
                      ).pack(side="left", padx=8)

    def _do_delete(self, row_id, card, dlg, delete_fn):
        delete_fn(row_id)
        dlg.destroy()
        card.destroy()
