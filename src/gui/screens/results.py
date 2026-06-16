"""Results screen — ring chart, certification badge, breakdown, exports."""

import datetime
import json
import os
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog

from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_ACCENT_HOV,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER,
    FONT_HEADING, FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, NAV_H, BTN_H, BTN_R,
    TIER_COLOURS,
)
from src.gui.screens.business_info import _header

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
EFFORT = {
    "C01_os_updates":            ("⚡ Quick Fix",  "#6C5FC7"),
    "C02_antivirus":             ("⚡ Quick Fix",  "#6C5FC7"),
    "C03_firewall":              ("⚡ Quick Fix",  "#6C5FC7"),
    "C04_password_policy":       ("📅 This Week",  "#2485E8"),
    "C05_backups":               ("📅 This Week",  "#2485E8"),
    "C06_security_training":     ("📆 This Month", "#F0A500"),
    "C07_access_control":        ("📆 This Month", "#F0A500"),
    "C08_incident_response":     ("📆 This Month", "#F0A500"),
    "C09_encryption":            ("📅 This Week",  "#2485E8"),
    "C10_mobile_security":       ("📅 This Week",  "#2485E8"),
    "C11_physical_security":     ("📆 This Month", "#F0A500"),
    "C12_network_security":      ("📅 This Week",  "#2485E8"),
    "C13_acceptable_use":        ("📆 This Month", "#F0A500"),
    "C14_vendor_risk":           ("🔁 Ongoing",    "#5A7490"),
    "C15_regulatory_compliance": ("🔁 Ongoing",    "#5A7490"),
    # Tool controls C16-C20
    "C16_active_directory":      ("📅 This Week",  "#6C5FC7"),
    "C17_network_scan":          ("📆 This Month", "#2485E8"),
    "C18_infra_scan":            ("📆 This Month", "#5A7490"),
    "C19_zambia_risk":           ("📆 This Month", "#F0A500"),
    "C20_remediation":           ("🔁 Ongoing",    "#27AE60"),
}

TOOL_CONTROL_KEYS = {
    "C16_active_directory", "C17_network_scan",
    "C18_infra_scan", "C19_zambia_risk", "C20_remediation",
}


# ── Ring chart widget ─────────────────────────────────────────────────────────

class _RingChart(tk.Canvas):
    """Canvas-drawn circular progress ring."""

    def __init__(self, parent, pct: int, colour: str,
                 size: int = 140, bg: str = CLR_SURFACE, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=bg, highlightthickness=0, **kw)
        cx = cy = size // 2
        r = size // 2 - 16
        w = 14

        # Background ring
        self.create_arc(cx - r, cy - r, cx + r, cy + r,
                        start=0, extent=359.9,
                        style="arc", outline=CLR_SURFACE_ALT, width=w)

        # Progress arc (clockwise from top)
        if pct > 0:
            self.create_arc(cx - r, cy - r, cx + r, cy + r,
                            start=90, extent=-(min(pct, 100) / 100 * 359.9),
                            style="arc", outline=colour, width=w)

        # Centre text
        self.create_text(cx, cy - 9, text=f"{pct}%",
                         font=("Segoe UI", 19, "bold"), fill=colour)
        self.create_text(cx, cy + 13, text="Score",
                         font=("Segoe UI", 9), fill=CLR_MUTED)


# ── Screen ────────────────────────────────────────────────────────────────────

class ResultsScreen(ctk.CTkFrame):

    def __init__(self, master, results, on_restart):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._results = results
        self._on_restart = on_restart
        self._auto_save()
        self._build()

    def _auto_save(self):
        try:
            from src.utils.local_db import save_assessment, set_reassessment_date
            save_assessment(self._results)
            due = (datetime.date.today() +
                   datetime.timedelta(days=182)).isoformat()
            set_reassessment_date(due)
        except Exception:
            pass

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        r = self._results
        tier = r.certification_level
        pct = round((r.score / r.total_possible) * 100) if r.total_possible else 0
        tier_clr = TIER_COLOURS.get(tier, CLR_DANGER)
        certified = tier != "NOT CERTIFIED"

        _header(self, "Assessment Results", "5 of 5", 1.0)

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # ── Hero badge card ────────────────────────────────────────
        hero = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=16,
                            border_width=1, border_color=tier_clr)
        hero.grid(row=0, column=0, padx=PAD, pady=(PAD, 10), sticky="ew")
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=0)

        # Tier colour top stripe
        ctk.CTkFrame(hero, fg_color=tier_clr, height=4,
                     corner_radius=0).grid(row=0, column=0,
                                           columnspan=2, sticky="ew")

        # Left: tier name + business + message
        left = ctk.CTkFrame(hero, fg_color="transparent")
        left.grid(row=1, column=0, padx=PAD, pady=(16, 16), sticky="w")

        ctk.CTkLabel(left,
                     text=f"{TIER_ICON.get(tier, '')}  {tier} CERTIFICATION",
                     font=("Segoe UI", 20, "bold"), text_color=tier_clr,
                     ).pack(anchor="w")

        TIER_MSG = {
            "GOLD":
                "Excellent — your business meets a high standard of cybersecurity.",
            "SILVER":
                "Good foundations — address the highlighted issues to reach Gold.",
            "BRONZE":
                "A start has been made — work through the action plan below.",
            "NOT CERTIFIED":
                "Significant gaps found — please act on the recommendations below.",
        }
        ctk.CTkLabel(left, text=TIER_MSG.get(tier, ""),
                     font=FONT_SMALL, text_color=CLR_MUTED,
                     wraplength=500, justify="left",
                     ).pack(anchor="w", pady=(4, 10))

        ctk.CTkLabel(left,
                     text=f"{r.business_info.name}  ·  {r.business_info.id}",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(anchor="w")

        ctk.CTkLabel(left,
                     text=f"{r.score} / {r.total_possible} points  "
                          f"·  Assessed {r.assessment_date.strftime('%d %b %Y')}",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).pack(anchor="w", pady=(2, 0))

        # Right: ring chart
        ring_frame = ctk.CTkFrame(hero, fg_color=CLR_SURFACE_ALT,
                                  corner_radius=12)
        ring_frame.grid(row=1, column=1, padx=(0, PAD), pady=PAD)

        _RingChart(ring_frame, pct, tier_clr, size=140,
                   bg=CLR_SURFACE_ALT).pack(padx=14, pady=14)

        # ── Summary metrics ────────────────────────────────────────
        met = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=14,
                           border_width=1, border_color=CLR_BORDER)
        met.grid(row=1, column=0, padx=PAD, pady=(0, 12), sticky="ew")
        met.grid_columnconfigure((0, 1, 2), weight=1)

        counts = {
            "PASS":    sum(1 for c in r.controls.values() if c.status == "PASS"),
            "WARNING": sum(1 for c in r.controls.values() if c.status == "WARNING"),
            "FAIL":    sum(1 for c in r.controls.values() if c.status == "FAIL"),
        }
        for col, (label, val, clr) in enumerate([
            ("Controls Passed", counts["PASS"],    CLR_SUCCESS),
            ("Need Review",     counts["WARNING"],  CLR_WARNING),
            ("Failed",          counts["FAIL"],     CLR_DANGER),
        ]):
            cell = ctk.CTkFrame(met, fg_color="transparent")
            cell.grid(row=0, column=col, padx=PAD, pady=16)
            ctk.CTkLabel(cell, text=str(val),
                         font=("Segoe UI", 32, "bold"), text_color=clr,
                         ).pack()
            ctk.CTkLabel(cell, text=label,
                         font=FONT_CAPTION, text_color=CLR_MUTED,
                         ).pack()
            if col < 2:
                ctk.CTkFrame(met, fg_color=CLR_BORDER,
                             width=1, corner_radius=0,
                             ).grid(row=0, column=col,
                                    sticky="nse", pady=12, padx=0)

        # ── Category breakdown ─────────────────────────────────────
        ctk.CTkLabel(scroll, text="Score by Category",
                     font=FONT_HEADING, text_color=CLR_TEXT,
                     ).grid(row=2, column=0, padx=PAD,
                            pady=(6, 4), sticky="w")

        cat_d = {"Technical": [0, 0], "Administrative": [0, 0],
                 "Physical": [0, 0]}
        cat_map = {"technical": "Technical", "administrative": "Administrative",
                   "physical": "Physical"}
        for ctrl in r.controls.values():
            k = cat_map.get(ctrl.category, "Technical")
            cat_d[k][0] += ctrl.score
            cat_d[k][1] += ctrl.weight

        cat_clrs = {"Technical": CLR_ACCENT, "Administrative": "#2485E8",
                    "Physical": "#F0A500"}
        cat_f = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=14,
                             border_width=1, border_color=CLR_BORDER)
        cat_f.grid(row=3, column=0, padx=PAD, pady=(0, 12), sticky="ew")
        cat_f.grid_columnconfigure((0, 1, 2), weight=1)

        for col, (cat, (sc, mx)) in enumerate(cat_d.items()):
            p = round(sc / mx * 100) if mx else 0
            clr = cat_clrs[cat]
            cell = ctk.CTkFrame(cat_f, fg_color="transparent")
            cell.grid(row=0, column=col, padx=PAD, pady=16, sticky="ew")
            cell.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(cell, text=cat, font=FONT_CAPTION,
                         text_color=CLR_MUTED).grid(row=0, sticky="w")
            ctk.CTkLabel(cell,
                         text=f"{sc} / {mx}  ({p}%)",
                         font=("Segoe UI", 15, "bold"), text_color=clr,
                         ).grid(row=1, sticky="w", pady=(3, 6))
            b = ctk.CTkProgressBar(cell, fg_color=CLR_SURFACE_ALT,
                                   progress_color=clr, height=6,
                                   corner_radius=3)
            b.set(p / 100)
            b.grid(row=2, sticky="ew")

        # ── Control breakdown ──────────────────────────────────────
        core_items = [(k, v) for k, v in r.controls.items()
                      if k not in TOOL_CONTROL_KEYS]
        tool_items = [(k, v) for k, v in r.controls.items()
                      if k in TOOL_CONTROL_KEYS]

        def _render_ctrl_row(parent, grid_row, ctrl):
            clr  = STATUS_CLR.get(ctrl.status, CLR_MUTED)
            icon = STATUS_ICON.get(ctrl.status, "?")
            row_f = ctk.CTkFrame(parent, fg_color=CLR_SURFACE,
                                 corner_radius=12, border_width=1,
                                 border_color=CLR_BORDER)
            row_f.grid(row=grid_row, column=0, padx=PAD, pady=3, sticky="ew")
            row_f.grid_columnconfigure(2, weight=1)
            ctk.CTkFrame(row_f, fg_color=clr, width=4,
                         corner_radius=0).grid(row=0, column=0,
                                               sticky="ns", pady=0)
            ctk.CTkLabel(row_f, text=icon,
                         font=("Segoe UI", 13), text_color=clr, width=28,
                         ).grid(row=0, column=1, padx=(10, 4),
                                pady=(11, 2), sticky="n")
            ctk.CTkLabel(row_f,
                         text=f"{ctrl.control_id}  {ctrl.name}",
                         font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
                         ).grid(row=0, column=2, sticky="w", pady=(11, 2))
            ctk.CTkLabel(row_f,
                         text=f"{ctrl.score}/{ctrl.weight} pts",
                         font=("Segoe UI", 10, "bold"), text_color=clr,
                         ).grid(row=0, column=3, padx=14,
                                pady=(11, 2), sticky="ne")
            if ctrl.status in ("FAIL", "WARNING", "ERROR") and ctrl.details:
                det = (ctrl.details[:100] + "…"
                       if len(ctrl.details) > 100 else ctrl.details)
                ctk.CTkLabel(row_f, text=det, font=FONT_CAPTION,
                             text_color=CLR_MUTED, wraplength=680,
                             justify="left", anchor="w",
                             ).grid(row=1, column=1, columnspan=3,
                                    padx=(10, 14), pady=(0, 10), sticky="w")

        # Core controls header
        ctk.CTkLabel(scroll, text="Core Controls  (C01–C15)",
                     font=FONT_HEADING, text_color=CLR_TEXT,
                     ).grid(row=4, column=0, padx=PAD,
                            pady=(6, 4), sticky="w")
        for i, (_, ctrl) in enumerate(core_items):
            _render_ctrl_row(scroll, 5 + i, ctrl)

        grid_row = 5 + len(core_items)

        # Tool controls section (only when tools were selected)
        if tool_items:
            ctk.CTkLabel(scroll,
                         text="Advanced Tool Assessments  (C16–C20)",
                         font=FONT_HEADING, text_color=CLR_TEXT,
                         ).grid(row=grid_row, column=0, padx=PAD,
                                pady=(PAD, 4), sticky="w")
            grid_row += 1
            for _, ctrl in tool_items:
                _render_ctrl_row(scroll, grid_row, ctrl)
                grid_row += 1

        base = grid_row

        # ── Action plan ────────────────────────────────────────────
        if r.recommendations:
            ctk.CTkLabel(scroll, text="Action Plan",
                         font=FONT_HEADING, text_color=CLR_TEXT,
                         ).grid(row=base, column=0, padx=PAD,
                                pady=(12, 4), sticky="w")
            ctrl_keys = list(r.controls.keys())
            for j, rec in enumerate(r.recommendations):
                eff_label, eff_clr = "📋 Note", CLR_MUTED
                for k in ctrl_keys:
                    if k.split("_")[0] in rec:
                        eff_label, eff_clr = EFFORT.get(
                            k, ("📋 Note", CLR_MUTED))
                        break
                rec_f = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE,
                                     corner_radius=10)
                rec_f.grid(row=base + 1 + j, column=0,
                           padx=PAD, pady=2, sticky="ew")
                rec_f.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(rec_f, text=eff_label,
                             font=("Segoe UI", 9, "bold"),
                             text_color=eff_clr,
                             fg_color=CLR_SURFACE_ALT, corner_radius=6,
                             width=88, height=20,
                             ).grid(row=0, column=0, padx=(10, 8), pady=8)
                ctk.CTkLabel(rec_f, text=rec, font=FONT_SMALL,
                             text_color=CLR_TEXT_SEC, wraplength=720,
                             justify="left", anchor="w",
                             ).grid(row=0, column=1,
                                    padx=(0, 10), pady=8, sticky="w")

        # ── Nav ───────────────────────────────────────────────────
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                           height=NAV_H)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)
        nav.grid_propagate(False)

        # Home / New Assessment button
        left_btns = ctk.CTkFrame(nav, fg_color="transparent")
        left_btns.grid(row=0, column=0, padx=PAD, pady=14)

        ctk.CTkButton(
            left_btns, text="<- Home", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC, hover_color=CLR_SURFACE_ALT,
            height=BTN_H, corner_radius=BTN_R,
            command=self._on_restart,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            left_btns, text="+ New Assessment", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_ACCENT, border_width=1,
            text_color=CLR_ACCENT, hover_color=CLR_SURFACE_ALT,
            height=BTN_H, corner_radius=BTN_R,
            command=self._on_restart,
        ).pack(side="left")

        export_btns = [
            ("💾  JSON",         CLR_ACCENT, CLR_ACCENT_HOV, "#000000",
             "normal", self._save_json),
            ("📄  HTML Report",  CLR_ACCENT, CLR_ACCENT_HOV, "#000000",
             "normal", self._save_html),
            ("📑  PDF Report",   "#2485E8",  "#1A6ABF",      "#ffffff",
             "normal", self._save_pdf),
            ("🏆  Certificate",  tier_clr,   "#7A6010",      "#000000",
             "normal" if certified else "disabled",
             self._generate_certificate if certified else (lambda: None)),
        ]
        for col, (label, clr, hov, tc, state, cmd) in enumerate(export_btns):
            ctk.CTkButton(
                nav, text=label, font=FONT_SMALL,
                fg_color=clr, hover_color=hov, text_color=tc,
                height=BTN_H, corner_radius=BTN_R,
                state=state, command=cmd,
            ).grid(row=0, column=2 + col, padx=(0, 6), pady=14)

    # ----------------------------------------------------------------- helpers
    def _get_dict(self):
        r = self._results
        pct = round(r.score / r.total_possible * 100) if r.total_possible else 0
        return {
            "business": {
                "name": r.business_info.name,
                "id": r.business_info.id,
                "province": r.business_info.province,
                "industry": r.business_info.industry,
                "contact_person": r.business_info.contact_person,
            },
            "assessment_date": r.assessment_date.isoformat(),
            "score": r.score,
            "total_possible": r.total_possible,
            "percentage": pct,
            "certification_level": r.certification_level,
            "critical_failures": r.critical_failures,
            "controls": {
                k: {"id": v.control_id, "name": v.name,
                    "status": v.status, "score": v.score,
                    "weight": v.weight, "details": v.details}
                for k, v in r.controls.items()
            },
            "recommendations": r.recommendations,
        }

    def _save_json(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
            initialfile=f"assessment_{self._results.business_info.id}.json")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._get_dict(), f, indent=2)
            self._toast("Saved", path)

    def _save_html(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("All", "*.*")],
            initialfile=f"assessment_{self._results.business_info.id}.html")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._build_html())
        self._toast("Saved", path)
        try:
            os.startfile(path)  # type: ignore
        except AttributeError:
            import subprocess
            subprocess.Popen(["xdg-open", path])

    def _save_pdf(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf"), ("All", "*.*")],
            initialfile=f"assessment_{self._results.business_info.id}.pdf")
        if not path:
            return
        try:
            from src.reporting.generator import ReportGenerator
            import shutil
            gen = ReportGenerator(output_dir=str(os.path.dirname(path)))
            name = os.path.splitext(os.path.basename(path))[0]
            out = gen.generate_pdf_report(
                self._results, self._results.business_info, name)
            if out != path:
                shutil.move(out, path)
            self._toast("Saved", path)
        except Exception as exc:
            self._alert("PDF Error", str(exc))

    def _generate_certificate(self):
        r = self._results
        tier = r.certification_level
        pct = round(r.score / r.total_possible * 100) if r.total_possible else 0
        tc = {"GOLD": "#F5C518", "SILVER": "#C0CDD8",
              "BRONZE": "#D4873A"}.get(tier, "#6C5FC7")
        ti = {"GOLD": "🥇", "SILVER": "🥈", "BRONZE": "🥉"}.get(tier, "✔")
        valid = (r.assessment_date.replace(year=r.assessment_date.year + 1)
                 .strftime("%d %B %Y"))
        passed = [c for c in r.controls.values() if c.status == "PASS"]
        p_html = "".join(
            f"<li>{c.control_id}: {c.name}</li>" for c in passed)

        html = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><title>Certificate — {r.business_info.name}</title>
<style>
 @media print{{body{{margin:0}}}}
 body{{font-family:'Segoe UI',Georgia,sans-serif;background:#f0ede8;
  display:flex;justify-content:center;align-items:center;
  min-height:100vh;margin:0;padding:20px;box-sizing:border-box}}
 .cert{{background:#fff;border:6px solid {tc};border-radius:20px;
  padding:48px 60px;max-width:760px;width:100%;
  box-shadow:0 10px 50px rgba(0,0,0,.12);text-align:center}}
 .prog{{font-size:11px;color:#aaa;letter-spacing:3px;text-transform:uppercase}}
 .title{{font-size:20px;font-weight:700;color:#1a2840;margin:6px 0 20px}}
 hr{{border:none;border-top:2px solid {tc};margin:18px 0}}
 .award{{font-size:11px;color:#aaa;letter-spacing:3px;text-transform:uppercase}}
 .tier{{font-size:38px;font-weight:900;color:{tc}}}
 .icon{{font-size:50px;margin:8px 0}}
 .biz{{font-size:24px;font-weight:700;color:#1a2840;margin:14px 0 4px}}
 .meta{{font-size:12px;color:#888;margin-bottom:16px}}
 .box{{display:inline-block;border:2px solid {tc};border-radius:10px;
  padding:10px 28px;margin:8px 0 16px;background:{tc}18}}
 .score{{font-size:30px;font-weight:700;color:{tc}}}
 .sl{{font-size:11px;color:#888}}
 .ph{{font-size:11px;text-transform:uppercase;letter-spacing:2px;
  color:#888;margin:18px 0 6px}}
 ul{{text-align:left;display:inline-block;color:#444;
  font-size:12px;line-height:2;padding-left:20px;margin:0}}
 .val{{margin-top:22px;font-size:11px;color:#aaa}}
 .foot{{margin-top:24px;font-size:10px;color:#ccc}}
</style></head><body><div class="cert">
 <div class="prog">University of Zambia · Dept. of Computing & Informatics</div>
 <div class="title">Zambia Digital Hygiene Certification Programme</div>
 <hr>
 <div class="award">This certifies that</div>
 <div class="biz">{r.business_info.name}</div>
 <div class="meta">{r.business_info.id}
  {(' · ' + r.business_info.province) if r.business_info.province else ''}
  {(' · ' + r.business_info.industry) if r.business_info.industry else ''}
 </div>
 <div class="award">has achieved</div>
 <div class="icon">{ti}</div>
 <div class="tier">{tier} CERTIFICATION</div>
 <div class="box"><div class="score">{pct}%</div>
  <div class="sl">{r.score} / {r.total_possible} points</div></div>
 <div class="ph">Controls Passed ({len(passed)} of 15)</div>
 <ul>{p_html}</ul>
 <div class="val">Assessed: {r.assessment_date.strftime('%d %B %Y')} &nbsp;·&nbsp;
  Valid until: {valid}</div>
 <hr>
 <div class="foot">NIST CSF v1.1 · CIS Controls v8 · ISO 27001:2022 ·
  Zambia Data Protection Act 2021<br>
  Self-assessment certificate — Zambia Digital Hygiene Certification Programme
 </div>
</div></body></html>"""

        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Certificate", "*.html"), ("All", "*.*")],
            initialfile=(f"certificate_{r.business_info.id}"
                         f"_{tier.replace(' ', '_')}.html"))
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._toast("Certificate Saved", path)
        try:
            os.startfile(path)  # type: ignore
        except AttributeError:
            import subprocess
            subprocess.Popen(["xdg-open", path])

    def _build_html(self):
        d = self._get_dict()
        pct = d["percentage"]
        tier = d["certification_level"]
        tc = {"GOLD": "#F5C518", "SILVER": "#C0CDD8", "BRONZE": "#D4873A",
              "NOT CERTIFIED": "#E84040"}.get(tier, "#E84040")
        sc_clr = {"PASS": "#6C5FC7", "WARNING": "#F0A500", "FAIL": "#E84040",
                  "ERROR": "#F0A500", "NOT_ASSESSED": "#5A7490"}
        rows = "".join(
            "<tr>"
            f"<td style='color:#5A7490;font-size:11px'>{v['id']}</td>"
            f"<td>{v['name']}</td>"
            "<td style='color:" + sc_clr.get(v['status'], '#ccc')
            + ";font-weight:bold'>" + v['status'] + "</td>"
            "<td style='color:" + sc_clr.get(v['status'], '#ccc')
            + ";font-weight:bold'>"
            + str(v['score']) + "/" + str(v['weight']) + "</td>"
            f"<td style='font-size:11px;color:#5A7490'>{v['details'][:60]}</td>"
            "</tr>"
            for v in d["controls"].values()
        )
        recs = "".join(f"<li>{r}</li>" for r in d.get("recommendations", []))
        return (
            f'<!DOCTYPE html><html lang="en"><head>'
            f'<meta charset="UTF-8">'
            f'<title>Report — {d["business"]["name"]}</title>'
            f'<style>'
            f'body{{font-family:"Segoe UI",sans-serif;background:#0B1622;'
            f'color:#ECF4FF;margin:0;padding:32px}}'
            f'h2{{color:#00C896;border-bottom:1px solid #1A2D42;padding-bottom:6px}}'
            f'.badge{{background:#132236;border-radius:16px;padding:24px;'
            f'text-align:center;margin-bottom:24px;border:1px solid {tc}}}'
            f'.score{{font-size:42px;font-weight:bold;color:{tc}}}'
            f'table{{width:100%;border-collapse:collapse;background:#132236;'
            f'border-radius:10px;overflow:hidden}}'
            f'th{{background:#1A2D42;padding:10px 14px;text-align:left;'
            f'font-size:11px;color:#5A7490;text-transform:uppercase}}'
            f'td{{padding:10px 14px;border-bottom:1px solid #0B1622;font-size:12px}}'
            f'ul{{color:#ECF4FF;line-height:2}}'
            f'footer{{margin-top:40px;color:#5A7490;font-size:10px;text-align:center}}'
            f'</style></head><body>'
            f'<div class="badge">'
            f'<p style="color:#5A7490;margin:0">{d["business"]["name"]} · {d["business"]["id"]}</p>'
            f'<h1 style="color:{tc}">{tier}</h1>'
            f'<div class="score">{pct}%</div>'
            f'<p>{d["score"]} / {d["total_possible"]} pts · {d["assessment_date"][:10]}</p>'
            f'</div>'
            f'<h2>Control Results</h2>'
            f'<table><thead><tr><th>ID</th><th>Control</th><th>Status</th>'
            f'<th>Score</th><th>Details</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>'
            f'<h2 style="margin-top:28px">Recommendations</h2>'
            f'<ul>{recs}</ul>'
            f'<footer>Zambia Digital Hygiene Certification Programme · University of Zambia · '
            f'Generated {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}'
            f'</footer></body></html>'
        )

    def _toast(self, title, path):
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.geometry("440x130")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text=f"✔  {title} successfully!",
                     font=FONT_SUBHEAD, text_color=CLR_SUCCESS,
                     ).pack(pady=(22, 4))
        ctk.CTkLabel(dlg, text=path, font=FONT_CAPTION,
                     text_color=CLR_MUTED, wraplength=400,
                     ).pack(pady=(0, 14))
        ctk.CTkButton(dlg, text="OK",
                      fg_color=CLR_ACCENT, text_color="#000000",
                      height=BTN_H, corner_radius=BTN_R,
                      command=dlg.destroy).pack()

    def _alert(self, title, msg):
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.geometry("440x160")
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text=f"⚠  {title}",
                     font=FONT_SUBHEAD, text_color=CLR_WARNING,
                     ).pack(pady=(22, 6))
        ctk.CTkLabel(dlg, text=msg, font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, wraplength=400,
                     ).pack(pady=(0, 14))
        ctk.CTkButton(dlg, text="OK", fg_color=CLR_ACCENT,
                      text_color="#000000", command=dlg.destroy).pack()


class RecommendationsPanel(ctk.CTkFrame):
    """Recommendations panel showing suggested actions for improvement."""

    _EFFORT_MAP = {
        "C01": "⚡ Quick Fix", "C02": "⚡ Quick Fix", "C03": "⚡ Quick Fix",
        "C04": "📅 This Week", "C05": "📅 This Week",
        "C06": "📆 This Month", "C07": "📆 This Month", "C08": "📆 This Month",
        "C09": "📅 This Week", "C10": "📅 This Week",
        "C11": "📆 This Month", "C12": "📅 This Week",
        "C13": "📆 This Month", "C14": "🔁 Ongoing", "C15": "🔁 Ongoing",
    }

    def __init__(self, parent, results):
        super().__init__(parent, fg_color=CLR_SURFACE, corner_radius=12)
        self._build_recommendations(results)

    def _get_effort(self, control_id):
        return self._EFFORT_MAP.get(control_id[:3], "📆 This Month")

    def _build_recommendations(self, results):
        ctk.CTkLabel(self, text="💡 Recommended Actions",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=16, pady=(12, 8))

        recommendations = []
        for control_id, control_result in results.get("controls", {}).items():
            status = control_result.get("status", "NOT_ASSESSED")
            if status in ["FAIL", "WARNING"]:
                effort = self._get_effort(control_id)
                recommendations.append(
                    (control_id, control_result.get("name", control_id), status, effort)
                )

        if not recommendations:
            ctk.CTkLabel(self, text="✓ All controls are passing. Great work!",
                         font=FONT_BODY, text_color=CLR_SUCCESS,
                         ).pack(padx=16, pady=12)
            return

        for idx, (cid, name, status, effort) in enumerate(recommendations):
            item = ctk.CTkFrame(self, fg_color=CLR_SURFACE_ALT, corner_radius=8)
            item.pack(fill="x", padx=16, pady=4)
            priority_color = CLR_DANGER if status == "FAIL" else CLR_WARNING
            ctk.CTkFrame(item, fg_color=priority_color, width=3,
                         corner_radius=0).grid(row=0, column=0, sticky="ns", pady=0)
            content = ctk.CTkFrame(item, fg_color="transparent")
            content.grid(row=0, column=1, sticky="ew", padx=12, pady=8)
            ctk.CTkLabel(content, text=f"{cid}: {name}",
                         font=FONT_BODY, text_color=CLR_TEXT).pack(anchor="w")
            ctk.CTkLabel(content, text=f"{status} • {effort}",
                         font=FONT_SMALL, text_color=CLR_TEXT_SEC).pack(anchor="w")


class BenchmarkComparison(ctk.CTkToplevel):
    """Compare current assessment with previous assessments and industry benchmarks."""

    def __init__(self, parent, current_results):
        super().__init__(parent)
        self.title("Assessment Benchmarking")
        self.geometry("700x500")
        self.configure(fg_color=CLR_BG)

        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="📊 Benchmarking & Comparison",
                     font=("Segoe UI", 14, "bold"), text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=16, pady=12)

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        current_score = current_results.get("score", 0)
        total_possible = current_results.get("total_possible", 120)
        pct = (current_score / total_possible * 100) if total_possible > 0 else 0

        current_frame = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=8)
        current_frame.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(current_frame, text="Your Current Score",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(current_frame,
                     text=f"{current_score} / {total_possible} ({pct:.0f}%)",
                     font=("Segoe UI", 24, "bold"), text_color=CLR_SUCCESS,
                     ).pack(anchor="w", padx=16, pady=(0, 12))

        ctk.CTkLabel(scroll, text="Benchmarks",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(anchor="w", pady=(0, 8))

        benchmarks = [
            ("Your Industry Average", 65), ("Zambian SME Average", 58),
            ("Your Region Average", 62),   ("Top 25% Performance", 85),
        ]
        for label, score in benchmarks:
            bench_frame = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE_ALT, corner_radius=6)
            bench_frame.pack(fill="x", pady=4)
            bench_frame.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(bench_frame, text=label,
                         font=FONT_BODY, text_color=CLR_TEXT,
                         ).grid(row=0, column=0, padx=12, pady=8, sticky="w")
            bar = ctk.CTkProgressBar(bench_frame, fg_color=CLR_SURFACE,
                                     progress_color=CLR_WARNING, height=4)
            bar.set(score / 100)
            bar.grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 8), sticky="ew")
            ctk.CTkLabel(bench_frame, text=str(score),
                         font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                         ).grid(row=0, column=1, padx=12, sticky="e")

        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=50)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        ctk.CTkButton(footer, text="Close", command=self.destroy,
                      fg_color=CLR_SURFACE_ALT, text_color=CLR_TEXT,
                      font=FONT_BODY, height=BTN_H, corner_radius=BTN_R,
                      ).pack(side="left", padx=16, pady=12)
