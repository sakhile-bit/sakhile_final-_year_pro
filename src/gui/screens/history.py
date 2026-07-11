"""Past assessments history screen."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_BLUE,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER,
    FONT_TITLE, FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, HDR_H, NAV_H, BTN_H, BTN_R,
    TIER_COLOURS,
)

TIER_ICON = {"GOLD": "🥇", "SILVER": "🥈",
             "BRONZE": "🥉", "NOT CERTIFIED": "✕"}
STATUS_CLR = {
    "PASS": CLR_SUCCESS, "WARNING": CLR_WARNING,
    "FAIL": CLR_DANGER,  "ERROR":   CLR_WARNING,
    "NOT_ASSESSED": CLR_MUTED,
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
        self.grid_rowconfigure(0, weight=0)   # header
        self.grid_rowconfigure(1, weight=1)   # scroll — expands
        self.grid_rowconfigure(2, weight=0)   # nav bar — pinned

        # Header
        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                           height=HDR_H)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        hdr.grid_propagate(False)

        ctk.CTkLabel(hdr, text="Past Assessments",
                     font=FONT_TITLE, text_color=CLR_TEXT,
                     ).grid(row=0, column=0, padx=PAD, pady=18, sticky="w")

        # Thin accent line at bottom of header
        ctk.CTkFrame(hdr, fg_color=CLR_ACCENT, height=2,
                     corner_radius=0).grid(row=1, column=0,
                                           columnspan=2, sticky="ew")

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG,
                                        corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        from src.utils.local_db import list_assessments, delete_assessment
        rows = list_assessments()

        if not rows:
            empty = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE,
                                 corner_radius=16, border_width=1,
                                 border_color=CLR_BORDER)
            empty.grid(row=0, column=0, padx=PAD, pady=PAD, sticky="ew")
            ctk.CTkLabel(
                empty,
                text="No assessments yet\n\n"
                     "Complete your first assessment and it will appear here.",
                font=FONT_BODY, text_color=CLR_MUTED, justify="center",
            ).pack(pady=48)
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
        pct = row["pct"]

        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE,
                            corner_radius=14, border_width=1,
                            border_color=CLR_BORDER)
        card.grid(row=idx, column=0, padx=PAD, pady=5, sticky="ew")
        card.grid_columnconfigure(2, weight=1)

        # Coloured left stripe
        ctk.CTkFrame(card, fg_color=tier_clr, width=5,
                     corner_radius=0).grid(row=0, column=0,
                                           rowspan=2, sticky="ns")

        # Tier icon
        ctk.CTkLabel(card,
                     text=TIER_ICON.get(tier, "✕"),
                     font=("Segoe UI Emoji", 26),
                     ).grid(row=0, column=1, rowspan=2,
                            padx=(12, 10), pady=16)

        # Business name
        ctk.CTkLabel(card, text=row["biz_name"],
                     font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
                     ).grid(row=0, column=2, sticky="w", pady=(14, 2))

        # Meta
        meta_parts = [p for p in [
            row.get("biz_id", ""), row.get("province", ""),
            row.get("industry", ""), row.get("saved_at", "")[:10],
        ] if p]
        ctk.CTkLabel(card, text="  ·  ".join(meta_parts),
                     font=FONT_CAPTION, text_color=CLR_MUTED, anchor="w",
                     ).grid(row=1, column=2, sticky="w", pady=(0, 14))

        # Score badge
        ctk.CTkLabel(
            card,
            text=f"{pct}%",
            font=("Segoe UI", 18, "bold"), text_color=tier_clr,
        ).grid(row=0, column=3, padx=(0, 4), pady=(14, 2))

        ctk.CTkLabel(
            card, text=tier,
            font=("Segoe UI", 10, "bold"), text_color=tier_clr,
            fg_color=CLR_SURFACE_ALT, corner_radius=6,
            width=90, height=18,
        ).grid(row=1, column=3, padx=(0, 8), pady=(0, 14))

        row_id = row["id"]

        # Action buttons
        btn_f = ctk.CTkFrame(card, fg_color="transparent")
        btn_f.grid(row=0, column=4, rowspan=2, padx=(0, 14), pady=14)

        ctk.CTkButton(
            btn_f, text="👁  View", font=FONT_CAPTION,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_ALT,
            border_color=CLR_ACCENT, border_width=1,
            text_color=CLR_ACCENT,
            width=72, height=30, corner_radius=8,
            command=lambda rid=row_id: self._show_details(rid),
        ).pack(pady=(0, 6))

        ctk.CTkButton(
            btn_f, text="Compare", font=FONT_CAPTION,
            fg_color="transparent", hover_color=CLR_SURFACE_ALT,
            border_color=CLR_BLUE, border_width=1,
            text_color=CLR_BLUE,
            width=72, height=30, corner_radius=8,
            command=lambda rid=row_id: self._show_compare(rid),
        ).pack(pady=(0, 6))

        ctk.CTkButton(
            btn_f, text="Delete", font=FONT_CAPTION,
            fg_color="transparent", hover_color=CLR_SURFACE_ALT,
            border_color=CLR_DANGER, border_width=1,
            text_color=CLR_DANGER,
            width=72, height=30, corner_radius=8,
            command=lambda rid=row_id, c=card: self._confirm_delete(
                rid, c, delete_fn),
        ).pack()

    # ----------------------------------------------------------------- details
    def _show_details(self, row_id):
        from src.utils.local_db import get_assessment
        data = get_assessment(row_id)
        if not data:
            return

        tier = data.get("certification_level", "—")
        tier_clr = TIER_COLOURS.get(tier, CLR_DANGER)
        pct = data.get("percentage", 0)
        biz = data.get("business", {})

        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Assessment — {biz.get('name', '')}")
        dlg.geometry("700x560")
        dlg.configure(fg_color=CLR_BG)
        dlg.grab_set()

        # Header
        hdr = ctk.CTkFrame(dlg, fg_color=CLR_SURFACE, corner_radius=0,
                           height=68)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkFrame(hdr, fg_color=tier_clr, width=5,
                     corner_radius=0).pack(side="left", fill="y")

        ctk.CTkLabel(
            hdr,
            text=f"{TIER_ICON.get(tier, '')}  "
                 f"{biz.get('name', '—')}  —  {tier}  ({pct}%)",
            font=FONT_SUBHEAD, text_color=tier_clr,
        ).pack(side="left", padx=16, pady=18)

        ctk.CTkLabel(
            hdr,
            text=f"{biz.get('id', '')}  ·  "
                 f"{data.get('assessment_date', '')[:10]}",
            font=FONT_CAPTION, text_color=CLR_MUTED,
        ).pack(side="right", padx=PAD)

        # Control breakdown
        scroll = ctk.CTkScrollableFrame(dlg, fg_color=CLR_BG,
                                        corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        for i, (_, ctrl) in enumerate(
                data.get("controls", {}).items()):
            status = ctrl.get("status", "—")
            clr = STATUS_CLR.get(status, CLR_MUTED)
            icon = STATUS_ICON.get(status, "?")

            rf = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE,
                              corner_radius=10, border_width=1,
                              border_color=CLR_BORDER)
            rf.grid(row=i, column=0, padx=12, pady=3, sticky="ew")
            rf.grid_columnconfigure(1, weight=1)

            # Status stripe
            ctk.CTkFrame(rf, fg_color=clr, width=4,
                         corner_radius=0).grid(row=0, column=0,
                                               sticky="ns")

            ctk.CTkLabel(rf, text=icon,
                         font=("Segoe UI", 12), text_color=clr,
                         width=24,
                         ).grid(row=0, column=1,
                                padx=(8, 4), pady=(10, 2), sticky="n")
            ctk.CTkLabel(rf,
                         text=f"{ctrl.get('id', '')}  {ctrl.get('name', '')}",
                         font=FONT_SUBHEAD, text_color=CLR_TEXT,
                         anchor="w",
                         ).grid(row=0, column=2,
                                sticky="w", pady=(10, 2))
            ctk.CTkLabel(rf,
                         text=f"{ctrl.get('score', 0)}"
                              f"/{ctrl.get('weight', 0)} pts",
                         font=("Segoe UI", 10, "bold"),
                         text_color=clr,
                         ).grid(row=0, column=3,
                                padx=12, pady=(10, 2), sticky="e")
            if ctrl.get("details"):
                ctk.CTkLabel(rf, text=ctrl["details"],
                             font=FONT_CAPTION, text_color=CLR_MUTED,
                             wraplength=550, justify="left",
                             anchor="w",
                             ).grid(row=1, column=1, columnspan=3,
                                    padx=(8, 12), pady=(0, 8),
                                    sticky="w")

        ctk.CTkButton(
            dlg, text="Close",
            height=BTN_H, corner_radius=BTN_R,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_BORDER,
            text_color=CLR_TEXT, font=FONT_BODY,
            command=dlg.destroy,
        ).pack(pady=10)

    # --------------------------------------------------------------- comparison
    def _show_compare(self, row_id: int):
        """Open a side-by-side comparison of this assessment vs the one before it."""
        from src.utils.local_db import list_assessments, get_assessment
        all_rows = list_assessments()
        ids = [r["id"] for r in all_rows]
        try:
            pos = ids.index(row_id)
        except ValueError:
            return
        if pos >= len(ids) - 1:
            # No older assessment to compare with
            dlg = ctk.CTkToplevel(self)
            dlg.title("Compare")
            dlg.geometry("360x120")
            dlg.configure(fg_color=CLR_SURFACE)
            dlg.grab_set()
            ctk.CTkLabel(dlg,
                         text="No previous assessment to compare with.\n"
                              "Complete at least two assessments first.",
                         font=FONT_SMALL, text_color=CLR_MUTED,
                         justify="center").pack(pady=(22, 14))
            ctk.CTkButton(dlg, text="OK", fg_color=CLR_ACCENT,
                          text_color="#FFFFFF", command=dlg.destroy).pack()
            return

        newer_id = row_id
        older_id = ids[pos + 1]
        newer = get_assessment(newer_id)
        older = get_assessment(older_id)
        if not newer or not older:
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("Assessment Comparison")
        dlg.geometry("820x600")
        dlg.configure(fg_color=CLR_BG)
        dlg.grab_set()

        # Header
        hdr = ctk.CTkFrame(dlg, fg_color=CLR_SURFACE, corner_radius=0,
                           height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr,
                     text="Side-by-side Assessment Comparison",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(side="left", padx=PAD, pady=16)
        ctk.CTkButton(hdr, text="Close", height=BTN_H, corner_radius=BTN_R,
                      fg_color=CLR_SURFACE_ALT, hover_color=CLR_BORDER,
                      text_color=CLR_TEXT, font=FONT_BODY,
                      command=dlg.destroy).pack(side="right", padx=PAD)

        scroll = ctk.CTkScrollableFrame(dlg, fg_color=CLR_BG)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure((0, 1), weight=1)

        def _col_header(parent, col, data):
            tier = data.get("certification_level", "—")
            pct = data.get("percentage", 0)
            biz = data.get("business", {}).get("name", "—")
            date = data.get("assessment_date", "")[:10]
            tier_clr = TIER_COLOURS.get(tier, CLR_DANGER)
            f = ctk.CTkFrame(parent, fg_color=CLR_SURFACE,
                             corner_radius=10, border_width=2,
                             border_color=tier_clr)
            f.grid(row=0, column=col, padx=8, pady=8, sticky="ew")
            ctk.CTkLabel(f, text=biz, font=FONT_SUBHEAD,
                         text_color=CLR_TEXT).pack(pady=(12, 2))
            ctk.CTkLabel(f,
                         text=f"{TIER_ICON.get(tier, '?')}  {tier}  ({pct}%)",
                         font=("Segoe UI", 14, "bold"),
                         text_color=tier_clr).pack()
            ctk.CTkLabel(f, text=date, font=FONT_CAPTION,
                         text_color=CLR_MUTED).pack(pady=(2, 12))

        _col_header(scroll, 0, newer)
        _col_header(scroll, 1, older)

        # Control-by-control comparison
        newer_ctrls = newer.get("controls", {})
        older_ctrls = older.get("controls", {})
        all_ctrl_ids = list(newer_ctrls.keys()) or list(older_ctrls.keys())

        for row_i, ctrl_key in enumerate(all_ctrl_ids):
            nc = newer_ctrls.get(ctrl_key, {})
            oc = older_ctrls.get(ctrl_key, {})
            for col, ctrl in [(0, nc), (1, oc)]:
                status = ctrl.get("status", "—")
                clr = STATUS_CLR.get(status, CLR_MUTED)
                icon = STATUS_ICON.get(status, "?")
                rf = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE,
                                  corner_radius=8, border_width=1,
                                  border_color=CLR_BORDER)
                rf.grid(row=row_i + 1, column=col,
                        padx=8, pady=3, sticky="ew")
                rf.grid_columnconfigure(1, weight=1)
                ctk.CTkFrame(rf, fg_color=clr, width=3,
                             corner_radius=0).grid(row=0, column=0,
                                                   sticky="ns")
                ctk.CTkLabel(rf, text=icon, font=("Segoe UI", 11),
                             text_color=clr, width=22,
                             ).grid(row=0, column=1,
                                    padx=(8, 4), pady=8, sticky="n")
                name = ctrl.get("name", ctrl_key)
                ctk.CTkLabel(rf,
                             text=f"{ctrl.get('id', '?')}  {name}",
                             font=FONT_SMALL, text_color=CLR_TEXT,
                             anchor="w",
                             ).grid(row=0, column=2, sticky="w", pady=8)
                ctk.CTkLabel(rf,
                             text=f"{ctrl.get('score', 0)}"
                                  f"/{ctrl.get('weight', 0)}",
                             font=("Segoe UI", 10, "bold"),
                             text_color=clr,
                             ).grid(row=0, column=3,
                                    padx=8, pady=8, sticky="e")

    # ----------------------------------------------------------------- delete
    def _confirm_delete(self, row_id, card, delete_fn):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Delete")
        dlg.geometry("340x150")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="Delete this assessment?",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(pady=(24, 4))
        ctk.CTkLabel(dlg, text="This cannot be undone.",
                     font=FONT_SMALL, text_color=CLR_MUTED,
                     ).pack(pady=(0, 16))

        r = ctk.CTkFrame(dlg, fg_color="transparent")
        r.pack()
        ctk.CTkButton(r, text="Cancel", width=100,
                      fg_color="transparent", border_color=CLR_BORDER,
                      border_width=1, text_color=CLR_TEXT_SEC,
                      hover_color=CLR_SURFACE_ALT,
                      command=dlg.destroy).pack(side="left", padx=8)
        ctk.CTkButton(r, text="Delete", width=100,
                      fg_color=CLR_DANGER, hover_color="#B02020",
                      text_color="#ffffff",
                      command=lambda: (delete_fn(row_id),
                                       dlg.destroy(),
                                       card.destroy()),
                      ).pack(side="left", padx=8)


class HistoryFilters(ctk.CTkFrame):
    """Filter widget for assessment history."""

    def __init__(self, parent, on_filter_change=None):
        super().__init__(parent, fg_color=CLR_SURFACE, corner_radius=8)
        self.on_filter_change = on_filter_change or (lambda: None)

        ctk.CTkLabel(self, text="🔍 Filter Assessments",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=12, pady=(12, 8))

        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda *args: self.on_filter_change())
        ctk.CTkEntry(self, placeholder_text="Search by organization name...",
                     textvariable=self.search_var, fg_color=CLR_SURFACE_ALT,
                     border_color=CLR_BORDER, text_color=CLR_TEXT,
                     font=FONT_BODY, height=32,
                     ).pack(fill="x", padx=12, pady=(0, 12))

        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkLabel(filter_frame, text="Level:", font=FONT_SMALL,
                     text_color=CLR_TEXT).pack(side="left", padx=(0, 8))
        for level in ["All", "Gold", "Silver", "Bronze", "Failed"]:
            ctk.CTkCheckBox(filter_frame, text=level, font=FONT_SMALL,
                            text_color=CLR_TEXT, fg_color=CLR_SUCCESS,
                            ).pack(side="left", padx=4)

        sort_frame = ctk.CTkFrame(self, fg_color="transparent")
        sort_frame.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkLabel(sort_frame, text="Sort by:", font=FONT_SMALL,
                     text_color=CLR_TEXT).pack(side="left", padx=(0, 8))
        self.sort_var = ctk.StringVar(value="recent")
        for sort_opt, sort_val in [("Recent", "recent"), ("Score", "score"), ("Name", "name")]:
            ctk.CTkRadioButton(sort_frame, text=sort_opt,
                               variable=self.sort_var, value=sort_val,
                               fg_color=CLR_SUCCESS, text_color=CLR_TEXT,
                               font=FONT_SMALL,
                               ).pack(side="left", padx=8)


class AssessmentDetailView(ctk.CTkToplevel):
    """Detailed view of a single assessment."""

    def __init__(self, parent, assessment_data):
        super().__init__(parent)
        biz_name = assessment_data.get("biz_name", "Unknown")
        self.title(f"Assessment Details — {biz_name}")
        self.geometry("800x600")
        self.configure(fg_color=CLR_BG)

        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"📋 {biz_name}",
                     font=("Segoe UI", 16, "bold"), text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=16, pady=(12, 4))
        meta = (f"Assessed: {assessment_data.get('saved_at', 'Unknown')} "
                f"• Score: {assessment_data.get('pct', 0)}%")
        ctk.CTkLabel(hdr, text=meta, font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC).pack(anchor="w", padx=16, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        summary_frame = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=8)
        summary_frame.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(summary_frame, text="Assessment Summary",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=12, pady=(12, 8))
        for label, value in [
            ("Certification Level", assessment_data.get("tier", "N/A")),
            ("Overall Score",       f"{assessment_data.get('pct', 0)}%"),
            ("Total Points",        f"{assessment_data.get('score', 0)} / 120"),
            ("Assessment Date",     assessment_data.get("saved_at", "N/A")),
            ("Assessor",            assessment_data.get("assessor", "System")),
        ]:
            row_f = ctk.CTkFrame(summary_frame, fg_color="transparent")
            row_f.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row_f, text=label,
                         font=FONT_BODY, text_color=CLR_TEXT_SEC).pack(side="left")
            ctk.CTkLabel(row_f, text=value,
                         font=FONT_BODY, text_color=CLR_TEXT).pack(side="right")

        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=50)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        ctk.CTkButton(footer, text="Close", command=self.destroy,
                      fg_color=CLR_SURFACE_ALT, text_color=CLR_TEXT,
                      font=FONT_BODY, height=BTN_H, corner_radius=BTN_R,
                      ).pack(side="right", padx=8, pady=12)


class BulkExportDialog(ctk.CTkToplevel):
    """Dialog for bulk exporting multiple assessments."""

    def __init__(self, parent, selected_count):
        super().__init__(parent)
        self.title(f"Bulk Export — {selected_count} Assessments")
        self.geometry("500x300")
        self.configure(fg_color=CLR_BG)

        ctk.CTkLabel(self, text=f"Export {selected_count} Assessments",
                     font=("Segoe UI", 14, "bold"), text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=16, pady=(16, 8))

        frame = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=8)
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(frame, text="Select Export Format",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=12, pady=(12, 8))

        self.format_var = ctk.StringVar(value="pdf")
        for fmt, label in [
            ("pdf",  "📄 PDF (One file per assessment)"),
            ("xlsx", "📊 Excel (All in one sheet)"),
            ("zip",  "📦 ZIP Archive (All formats)"),
        ]:
            ctk.CTkRadioButton(frame, text=label, variable=self.format_var,
                               value=fmt, fg_color=CLR_SUCCESS,
                               text_color=CLR_TEXT, font=FONT_BODY,
                               ).pack(anchor="w", padx=12, pady=6)

        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=50)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        ctk.CTkButton(footer, text="Cancel", command=self.destroy,
                      fg_color=CLR_SURFACE_ALT, text_color=CLR_TEXT,
                      font=FONT_BODY, height=BTN_H, corner_radius=BTN_R,
                      width=120).pack(side="left", padx=8, pady=12)
        ctk.CTkButton(footer, text="Export",
                      fg_color=CLR_SUCCESS, text_color="#ffffff",
                      font=FONT_BODY, height=BTN_H, corner_radius=BTN_R,
                      ).pack(side="right", padx=8, pady=12)
