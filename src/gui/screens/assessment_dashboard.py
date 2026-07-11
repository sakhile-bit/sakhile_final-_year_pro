"""Assessment Dashboard screen — view and manage stored assessments.

Reads real assessments from the local database (``local_db``): the stat
tiles, the recent-assessment list, and every action (View / Export /
Delete / New) operate on actual saved data rather than placeholder samples.
"""

import json
from tkinter import filedialog

import customtkinter as ctk

from src.gui.gui import StatsCard
from src.gui.screens.business_info import _header
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_BG,
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
    FONT_CAPTION,
    FONT_SMALL,
    FONT_SUBHEAD,
    NAV_H,
    PAD,
    TIER_COLOURS,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

TIER_ICON = {"GOLD": "🥇", "SILVER": "🥈", "BRONZE": "🥉",
             "NOT CERTIFIED": "✕"}
STATUS_CLR = {"PASS": CLR_SUCCESS, "WARNING": CLR_WARNING,
              "FAIL": CLR_DANGER, "NOT_ASSESSED": CLR_MUTED,
              "ERROR": CLR_DANGER}
STATUS_ICON = {"PASS": "✓", "WARNING": "!", "FAIL": "✕",
               "NOT_ASSESSED": "–", "ERROR": "✕"}


class AssessmentDashboardScreen(ctk.CTkFrame):
    def __init__(self, master, on_back=None, on_new=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back or (lambda: None)
        self._on_new = on_new or (lambda: None)
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        _header(self, "Assessment Dashboard", "", 0.0)

        # Main container — rebuilt in place by _refresh()
        self._main = ctk.CTkFrame(self, fg_color=CLR_BG)
        self._main.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=PAD)
        self._main.grid_columnconfigure(0, weight=1)
        self._main.grid_rowconfigure(2, weight=1)
        self._populate()

        # Footer
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                              height=NAV_H)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)

        ctk.CTkButton(
            footer, text="➕  New Assessment", command=self._new_assessment,
            fg_color=CLR_SUCCESS, hover_color="#249A24", text_color="#ffffff",
            font=FONT_SUBHEAD, height=BTN_H, corner_radius=BTN_R,
        ).pack(side="left", padx=PAD, pady=PAD)

        ctk.CTkButton(
            footer, text="←  Back", command=self._on_back,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            text_color=CLR_TEXT, font=FONT_SUBHEAD, height=BTN_H,
            corner_radius=BTN_R,
        ).pack(side="right", padx=PAD, pady=PAD)

    # --------------------------------------------------------------- data load
    def _load_rows(self):
        try:
            from src.utils.local_db import list_assessments
            return list_assessments(limit=100)
        except Exception:
            logger.debug("could not load assessments", exc_info=True)
            return []

    def _populate(self):
        for w in self._main.winfo_children():
            w.destroy()

        rows = self._load_rows()
        self._build_stats(rows)

        ctk.CTkLabel(self._main, text="📋  Recent Assessments",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).grid(row=1, column=0, sticky="w", pady=(20, 12))

        scroll = ctk.CTkScrollableFrame(self._main, fg_color="transparent")
        scroll.grid(row=2, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        if not rows:
            self._build_empty_state(scroll)
            return
        for idx, row in enumerate(rows):
            self._build_card(scroll, idx, row)

    # ------------------------------------------------------------------ stats
    def _build_stats(self, rows):
        total = len(rows)
        gold = sum(1 for r in rows if r.get("tier") == "GOLD")
        certified = sum(1 for r in rows
                        if r.get("tier") in ("GOLD", "SILVER", "BRONZE"))
        avg = round(sum(r.get("pct", 0) for r in rows) / total) if total else 0
        not_cert = sum(1 for r in rows if r.get("tier") == "NOT CERTIFIED")

        stats = ctk.CTkFrame(self._main, fg_color="transparent")
        stats.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        stats.grid_columnconfigure((0, 1, 2, 3), weight=1)

        tiles = [
            ("📊", "Total Assessments", str(total), CLR_ACCENT),
            ("🥇", "Gold Certifications", str(gold), CLR_SUCCESS),
            ("📈", "Average Score", f"{avg}%", CLR_WARNING),
            ("⚠️", "Not Certified", str(not_cert), CLR_DANGER),
        ]
        for col, (icon, label, value, clr) in enumerate(tiles):
            StatsCard(stats, icon, label, value, clr).grid(
                row=0, column=col, sticky="ew", padx=4)

        # A one-line reading of the numbers so the tiles aren't just figures.
        summary = (f"{certified} of {total} certified"
                   if total else "No assessments saved yet")
        ctk.CTkLabel(self._main, text=summary, font=FONT_CAPTION,
                     text_color=CLR_MUTED, anchor="w",
                     ).grid(row=0, column=0, sticky="sw", pady=(0, 0))

    def _build_empty_state(self, parent):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=0, column=0, pady=60)
        ctk.CTkLabel(box, text="📭", font=("Segoe UI Emoji", 44),
                     text_color=CLR_MUTED).pack(pady=(0, 8))
        ctk.CTkLabel(box, text="No assessments yet",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT).pack()
        ctk.CTkLabel(
            box,
            text="Run your first assessment to see it here, with its\n"
                 "certification tier, score and full control breakdown.",
            font=FONT_SMALL, text_color=CLR_MUTED, justify="center",
        ).pack(pady=(4, 16))
        ctk.CTkButton(
            box, text="➕  Start First Assessment",
            command=self._new_assessment, fg_color=CLR_ACCENT,
            hover_color="#7D70D6", text_color="#FFFFFF",
            height=BTN_H, corner_radius=BTN_R,
        ).pack()

    # ------------------------------------------------------------------ cards
    def _build_card(self, parent, idx, row):
        tier = row.get("tier", "—")
        tier_clr = TIER_COLOURS.get(tier, CLR_MUTED)
        row_id = row.get("id")

        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=10,
                            border_width=1, border_color=CLR_BORDER,
                            height=76)
        card.grid(row=idx, column=0, sticky="ew", pady=5)
        card.grid_propagate(False)
        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(0, weight=1)

        # Tier badge
        badge = ctk.CTkFrame(card, fg_color=tier_clr, corner_radius=8,
                             width=52, height=52)
        badge.grid(row=0, column=0, padx=12, pady=12)
        badge.grid_propagate(False)
        ctk.CTkLabel(badge, text=TIER_ICON.get(tier, "?"),
                     font=("Segoe UI Emoji", 22)).place(relx=0.5, rely=0.5,
                                                        anchor="center")

        # Info
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w", padx=(0, 8))
        ctk.CTkLabel(info, text=row.get("biz_name", "—"), font=FONT_SUBHEAD,
                     text_color=CLR_TEXT, anchor="w").pack(anchor="w")
        meta = "  ·  ".join(p for p in (
            row.get("biz_id") or "",
            (row.get("saved_at") or "")[:10],
            row.get("industry") or "",
        ) if p)
        ctk.CTkLabel(info, text=meta, font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     anchor="w").pack(anchor="w")

        # Score + tier
        score = ctk.CTkFrame(card, fg_color="transparent")
        score.grid(row=0, column=2, padx=10)
        ctk.CTkLabel(score, text=f"{row.get('pct', 0)}%",
                     font=("Segoe UI", 16, "bold"), text_color=tier_clr,
                     ).pack()
        ctk.CTkLabel(score, text=tier, font=FONT_CAPTION,
                     text_color=CLR_TEXT_SEC).pack()

        # Actions
        ctk.CTkButton(
            card, text="👁  View", width=64, height=30, font=FONT_SMALL,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            text_color=CLR_TEXT, corner_radius=BTN_R,
            command=lambda rid=row_id: self._view(rid),
        ).grid(row=0, column=3, padx=4)
        ctk.CTkButton(
            card, text="📥", width=38, height=30, font=FONT_SMALL,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            text_color=CLR_TEXT, corner_radius=BTN_R,
            command=lambda rid=row_id, nm=row.get("biz_name", ""):
                self._export(rid, nm),
        ).grid(row=0, column=4, padx=4)
        ctk.CTkButton(
            card, text="🗑", width=38, height=30, font=FONT_SMALL,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_DANGER,
            text_color=CLR_TEXT, corner_radius=BTN_R,
            command=lambda rid=row_id, nm=row.get("biz_name", ""):
                self._confirm_delete(rid, nm),
        ).grid(row=0, column=5, padx=(4, 12))

    # ---------------------------------------------------------------- actions
    def _view(self, row_id):
        if row_id is None:
            return
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
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        hdr = ctk.CTkFrame(dlg, fg_color=CLR_SURFACE, corner_radius=0,
                           height=68)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkFrame(hdr, fg_color=tier_clr, width=5,
                     corner_radius=0).pack(side="left", fill="y")
        ctk.CTkLabel(
            hdr, text=f"{TIER_ICON.get(tier, '')}  {biz.get('name', '—')}  —  "
                      f"{tier}  ({pct}%)",
            font=FONT_SUBHEAD, text_color=tier_clr,
        ).pack(side="left", padx=16, pady=18)
        ctk.CTkLabel(
            hdr, text=f"{biz.get('id', '')}  ·  "
                      f"{data.get('assessment_date', '')[:10]}",
            font=FONT_CAPTION, text_color=CLR_MUTED,
        ).pack(side="right", padx=PAD)

        scroll = ctk.CTkScrollableFrame(dlg, fg_color=CLR_BG, corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)
        for i, (_, ctrl) in enumerate(data.get("controls", {}).items()):
            status = ctrl.get("status", "—")
            clr = STATUS_CLR.get(status, CLR_MUTED)
            rf = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=10,
                              border_width=1, border_color=CLR_BORDER,
                              height=52)
            rf.grid(row=i, column=0, padx=12, pady=3, sticky="ew")
            rf.grid_propagate(False)
            rf.grid_columnconfigure(1, weight=1)
            rf.grid_rowconfigure(0, weight=1)
            ctk.CTkFrame(rf, fg_color=clr, width=4, height=52,
                         corner_radius=0).grid(row=0, column=0, sticky="ns")
            ctk.CTkLabel(rf, text=f"{STATUS_ICON.get(status, '?')}  "
                                  f"{ctrl.get('name', '')}",
                         font=FONT_SMALL, text_color=CLR_TEXT, anchor="w",
                         ).grid(row=0, column=1, padx=10, sticky="w")
            ctk.CTkLabel(rf, text=f"{ctrl.get('score', 0)}/{ctrl.get('weight', 0)}",
                         font=FONT_CAPTION, text_color=clr,
                         ).grid(row=0, column=2, padx=12)

    def _export(self, row_id, name):
        if row_id is None:
            return
        from src.utils.local_db import get_assessment
        data = get_assessment(row_id)
        if not data:
            return
        safe = "".join(c for c in (name or "assessment")
                       if c.isalnum() or c in " -_").strip() or "assessment"
        path = filedialog.asksaveasfilename(
            title="Export assessment",
            defaultextension=".html",
            initialfile=f"{safe}.html",
            filetypes=[("HTML report", "*.html"), ("JSON data", "*.json")],
        )
        if not path:
            return
        try:
            if path.lower().endswith(".json"):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self._render_html(data))
            self._toast(f"Exported to {path}")
        except Exception as exc:
            logger.warning("export failed", exc_info=True)
            self._toast(f"Export failed: {exc}", ok=False)

    @staticmethod
    def _render_html(data: dict) -> str:
        biz = data.get("business", {})
        tier = data.get("certification_level", "—")
        rows = "".join(
            f"<tr><td>{c.get('id', '')}</td><td>{c.get('name', '')}</td>"
            f"<td>{c.get('status', '')}</td>"
            f"<td>{c.get('score', 0)}/{c.get('weight', 0)}</td></tr>"
            for c in data.get("controls", {}).values())
        return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Assessment — {biz.get('name', '')}</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:40px;color:#222}}
h1{{margin-bottom:0}}table{{border-collapse:collapse;width:100%;margin-top:20px}}
td,th{{border:1px solid #ccc;padding:8px;text-align:left;font-size:14px}}
th{{background:#f0f0f0}}</style></head><body>
<h1>{biz.get('name', '')}</h1>
<p>{biz.get('id', '')} · {data.get('assessment_date', '')[:10]}</p>
<h2>{tier} — {data.get('percentage', 0)}%
({data.get('score', 0)}/{data.get('total_possible', 0)} points)</h2>
<table><tr><th>ID</th><th>Control</th><th>Status</th><th>Score</th></tr>
{rows}</table></body></html>"""

    def _confirm_delete(self, row_id, name):
        if row_id is None:
            return
        dlg = ctk.CTkToplevel(self)
        dlg.title("Delete assessment")
        dlg.geometry("400x180")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        ctk.CTkLabel(dlg, text="🗑  Delete this assessment?",
                     font=FONT_SUBHEAD, text_color=CLR_WARNING,
                     ).pack(pady=(22, 6))
        ctk.CTkLabel(dlg, text=f"“{name}” will be permanently removed.\n"
                               "This cannot be undone.",
                     font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     justify="center").pack(pady=(0, 16), padx=16)
        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack()
        ctk.CTkButton(btns, text="Cancel", command=dlg.destroy,
                      fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
                      text_color=CLR_TEXT, height=BTN_H, corner_radius=BTN_R,
                      width=120).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Delete",
                      command=lambda: self._do_delete(row_id, dlg),
                      fg_color=CLR_DANGER, hover_color="#B22222",
                      text_color="#ffffff", height=BTN_H, corner_radius=BTN_R,
                      width=120).pack(side="left", padx=6)

    def _do_delete(self, row_id, dlg):
        try:
            from src.utils.local_db import delete_assessment
            delete_assessment(row_id)
        except Exception:
            logger.warning("delete failed", exc_info=True)
        dlg.destroy()
        self._populate()   # refresh stats + list

    def _new_assessment(self):
        self._on_new()

    # ------------------------------------------------------------------ toast
    def _toast(self, msg, ok=True):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Export")
        dlg.geometry("420x150")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        ctk.CTkLabel(dlg, text="✔  Done" if ok else "⚠  Problem",
                     font=FONT_SUBHEAD,
                     text_color=CLR_SUCCESS if ok else CLR_DANGER,
                     ).pack(pady=(22, 6))
        ctk.CTkLabel(dlg, text=msg, font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     wraplength=380, justify="center").pack(pady=(0, 14),
                                                            padx=16)
        ctk.CTkButton(dlg, text="OK", command=dlg.destroy, fg_color=CLR_ACCENT,
                      text_color="#FFFFFF", height=BTN_H, corner_radius=BTN_R,
                      ).pack()
