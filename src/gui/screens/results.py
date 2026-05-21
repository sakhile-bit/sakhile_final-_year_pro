"""Results screen — certification badge, score breakdown, export, certificate."""

import datetime
import json
import os
import customtkinter as ctk
from tkinter import filedialog

from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_ACCENT_HOV,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER, CLR_DIVIDER,
    FONT_TITLE, FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, PAD_SM, HDR_H, NAV_H, BTN_H, BTN_R,
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
    "C01_os_updates":           ("⚡ Quick Fix",  "#00C896"),
    "C02_antivirus":            ("⚡ Quick Fix",  "#00C896"),
    "C03_firewall":             ("⚡ Quick Fix",  "#00C896"),
    "C04_password_policy":      ("📅 This Week",  "#2485E8"),
    "C05_backups":              ("📅 This Week",  "#2485E8"),
    "C06_security_training":    ("📆 This Month", "#F0A500"),
    "C07_access_control":       ("📆 This Month", "#F0A500"),
    "C08_incident_response":    ("📆 This Month", "#F0A500"),
    "C09_encryption":           ("📅 This Week",  "#2485E8"),
    "C10_mobile_security":      ("📅 This Week",  "#2485E8"),
    "C11_physical_security":    ("📆 This Month", "#F0A500"),
    "C12_network_security":     ("📅 This Week",  "#2485E8"),
    "C13_acceptable_use":       ("📆 This Month", "#F0A500"),
    "C14_vendor_risk":          ("🔁 Ongoing",    "#6A8099"),
    "C15_regulatory_compliance":("🔁 Ongoing",    "#6A8099"),
}


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

        _header(self, "Assessment Results", "4 of 4", 1.0)

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # ── Certification badge ────────────────────────────────────
        badge = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=18,
                             border_width=2, border_color=tier_clr)
        badge.grid(row=0, column=0, padx=PAD, pady=(PAD, 10), sticky="ew")
        badge.grid_columnconfigure(0, weight=1)

        # Top accent stripe in tier colour
        ctk.CTkFrame(badge, fg_color=tier_clr, height=4,
                     corner_radius=0).grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(badge, text=TIER_ICON.get(tier, ""),
                     font=("Segoe UI Emoji", 48),
                     ).grid(row=1, column=0, pady=(20, 6))

        ctk.CTkLabel(badge, text=f"{tier} CERTIFICATION",
                     font=("Segoe UI", 20, "bold"), text_color=tier_clr,
                     ).grid(row=2, column=0)

        TIER_MSG = {
            "GOLD":          "Excellent — your business meets a high standard of cybersecurity.",
            "SILVER":        "Good foundations — fix the highlighted issues to reach Gold.",
            "BRONZE":        "A start has been made — address the urgent items below.",
            "NOT CERTIFIED": "Significant gaps found — please work through the action plan below.",
        }
        ctk.CTkLabel(badge, text=TIER_MSG.get(tier, ""),
                     font=FONT_SMALL, text_color=CLR_MUTED,
                     wraplength=560, justify="center",
                     ).grid(row=3, column=0, padx=PAD, pady=(4, 0))

        ctk.CTkLabel(badge,
                     text=f"{r.business_info.name}  ·  {r.business_info.id}",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).grid(row=4, column=0, pady=(10, 0))

        ctk.CTkLabel(badge,
                     text=f"Score: {r.score} / {r.total_possible} pts  ({pct}%)",
                     font=("Segoe UI", 15, "bold"), text_color=tier_clr,
                     ).grid(row=5, column=0, pady=(4, 8))

        score_bar = ctk.CTkProgressBar(badge, fg_color=CLR_SURFACE_ALT,
                                       progress_color=tier_clr,
                                       height=10, corner_radius=5)
        score_bar.set(pct / 100)
        score_bar.grid(row=6, column=0, padx=PAD * 3, pady=(0, 20), sticky="ew")

        # ── Summary metrics ────────────────────────────────────────
        met = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=14,
                           border_width=1, border_color=CLR_BORDER)
        met.grid(row=1, column=0, padx=PAD, pady=(0, 14), sticky="ew")
        met.grid_columnconfigure((0, 1, 2), weight=1)

        counts = {
            "PASS":    sum(1 for c in r.controls.values() if c.status == "PASS"),
            "WARNING": sum(1 for c in r.controls.values() if c.status == "WARNING"),
            "FAIL":    sum(1 for c in r.controls.values() if c.status == "FAIL"),
        }
        for col, (label, val, clr) in enumerate([
            ("Passed", counts["PASS"], CLR_SUCCESS),
            ("Review", counts["WARNING"], CLR_WARNING),
            ("Failed", counts["FAIL"], CLR_DANGER),
        ]):
            cell = ctk.CTkFrame(met, fg_color="transparent")
            cell.grid(row=0, column=col, padx=PAD, pady=16, sticky="nsew")
            ctk.CTkLabel(cell, text=str(val),
                         font=("Segoe UI", 28, "bold"), text_color=clr,
                         ).pack()
            ctk.CTkLabel(cell, text=label,
                         font=FONT_CAPTION, text_color=CLR_MUTED,
                         ).pack()

        # ── Category breakdown ─────────────────────────────────────
        ctk.CTkLabel(scroll, text="Score by Category",
                     font=FONT_TITLE, text_color=CLR_TEXT,
                     ).grid(row=2, column=0, padx=PAD, pady=(6, 4), sticky="w")

        cat_data = {
            "Technical":      {"t": 0, "m": 0},
            "Administrative": {"t": 0, "m": 0},
            "Physical":       {"t": 0, "m": 0},
        }
        cat_map = {
            "technical": "Technical",
            "administrative": "Administrative",
            "physical": "Physical",
        }
        for ctrl in r.controls.values():
            k = cat_map.get(ctrl.category, "Technical")
            cat_data[k]["t"] += ctrl.score
            cat_data[k]["m"] += ctrl.weight

        cat_clrs = {
            "Technical": CLR_ACCENT,
            "Administrative": "#2485E8",
            "Physical": "#F0A500",
        }
        cat_f = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=14,
                             border_width=1, border_color=CLR_BORDER)
        cat_f.grid(row=3, column=0, padx=PAD, pady=(0, 14), sticky="ew")
        cat_f.grid_columnconfigure((0, 1, 2), weight=1)

        for col, (cat, d) in enumerate(cat_data.items()):
            p = round((d["t"] / d["m"]) * 100) if d["m"] else 0
            clr = cat_clrs[cat]
            cell = ctk.CTkFrame(cat_f, fg_color="transparent")
            cell.grid(row=0, column=col, padx=PAD, pady=16, sticky="ew")
            cell.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(cell, text=cat, font=FONT_CAPTION,
                         text_color=CLR_MUTED).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(cell,
                         text=f"{d['t']} / {d['m']}  ({p}%)",
                         font=("Segoe UI", 15, "bold"), text_color=clr,
                         ).grid(row=1, column=0, sticky="w", pady=(3, 6))
            b = ctk.CTkProgressBar(cell, fg_color=CLR_SURFACE_ALT,
                                   progress_color=clr, height=6,
                                   corner_radius=3)
            b.set(p / 100)
            b.grid(row=2, column=0, sticky="ew")

        # ── Control breakdown ──────────────────────────────────────
        ctk.CTkLabel(scroll, text="Control Breakdown",
                     font=FONT_TITLE, text_color=CLR_TEXT,
                     ).grid(row=4, column=0, padx=PAD, pady=(6, 4), sticky="w")

        for i, (_, ctrl) in enumerate(r.controls.items()):
            clr = STATUS_CLR.get(ctrl.status, CLR_MUTED)
            icon = STATUS_ICON.get(ctrl.status, "?")
            row_f = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE,
                                 corner_radius=12, border_width=1,
                                 border_color=CLR_BORDER)
            row_f.grid(row=5 + i, column=0, padx=PAD, pady=3, sticky="ew")
            row_f.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row_f, text=icon, font=("Segoe UI", 13),
                         text_color=clr, width=30,
                         ).grid(row=0, column=0, padx=(14, 6),
                                pady=(12, 2), sticky="n")
            ctk.CTkLabel(row_f,
                         text=f"{ctrl.control_id}  {ctrl.name}",
                         font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
                         ).grid(row=0, column=1, sticky="w", pady=(12, 2))
            ctk.CTkLabel(row_f, text=f"{ctrl.score}/{ctrl.weight}",
                         font=("Segoe UI", 11, "bold"), text_color=clr,
                         ).grid(row=0, column=2, padx=14, pady=(12, 2),
                                sticky="ne")
            if ctrl.status in ("FAIL", "WARNING", "ERROR") and ctrl.details:
                det = (ctrl.details[:100] + "…"
                       if len(ctrl.details) > 100 else ctrl.details)
                ctk.CTkLabel(row_f, text=det, font=FONT_CAPTION,
                             text_color=CLR_MUTED, wraplength=700,
                             justify="left", anchor="w",
                             ).grid(row=1, column=0, columnspan=3,
                                    padx=(50, 14), pady=(0, 10), sticky="w")

        base = len(r.controls) + 5

        # ── Action plan ────────────────────────────────────────────
        if r.recommendations:
            ctk.CTkLabel(scroll, text="Action Plan",
                         font=FONT_TITLE, text_color=CLR_TEXT,
                         ).grid(row=base, column=0, padx=PAD,
                                pady=(14, 4), sticky="w")
            ctrl_keys = list(r.controls.keys())
            for j, rec in enumerate(r.recommendations):
                eff_label, eff_clr = "📋 Note", CLR_MUTED
                for k in ctrl_keys:
                    if k.split("_")[0] in rec:
                        eff_label, eff_clr = EFFORT.get(k, ("📋 Note", CLR_MUTED))
                        break
                rec_f = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE,
                                     corner_radius=10)
                rec_f.grid(row=base + 1 + j, column=0, padx=PAD,
                           pady=2, sticky="ew")
                rec_f.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(rec_f, text=eff_label,
                             font=("Segoe UI", 9, "bold"),
                             text_color=eff_clr,
                             fg_color=CLR_SURFACE_ALT, corner_radius=6,
                             width=86, height=20,
                             ).grid(row=0, column=0, padx=(10, 8), pady=8)
                ctk.CTkLabel(rec_f, text=rec, font=FONT_SMALL,
                             text_color=CLR_TEXT_SEC, wraplength=720,
                             justify="left", anchor="w",
                             ).grid(row=0, column=1, padx=(0, 10),
                                    pady=8, sticky="w")

        # ── Nav ───────────────────────────────────────────────────
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                           height=NAV_H)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)
        nav.grid_propagate(False)

        ctk.CTkButton(
            nav, text="New Assessment", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC, hover_color=CLR_SURFACE_ALT,
            height=BTN_H, corner_radius=BTN_R, command=self._on_restart,
        ).grid(row=0, column=0, padx=PAD, pady=14)

        export_btns = [
            ("💾  JSON",        CLR_ACCENT, CLR_ACCENT_HOV, "#000000",
             "normal", self._save_json),
            ("📄  HTML Report", CLR_ACCENT, CLR_ACCENT_HOV, "#000000",
             "normal", self._save_html),
            ("📑  PDF Report",  "#2485E8",  "#1A6ABF",      "#ffffff",
             "normal", self._save_pdf),
            ("🏆  Certificate", tier_clr,   "#7A6010",      "#000000",
             "normal" if certified else "disabled",
             self._generate_certificate if certified else (lambda: None)),
        ]
        for col, (label, clr, hov, txt_clr, state, cmd) in enumerate(
                export_btns):
            ctk.CTkButton(
                nav, text=label, font=FONT_SMALL,
                fg_color=clr, hover_color=hov, text_color=txt_clr,
                height=BTN_H, corner_radius=BTN_R,
                state=state, command=cmd,
            ).grid(row=0, column=2 + col, padx=(0, 6), pady=14)

    # ----------------------------------------------------------------- export
    def _to_dict(self):
        r = self._results
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
            "percentage": (round((r.score / r.total_possible) * 100)
                          if r.total_possible else 0),
            "certification_level": r.certification_level,
            "critical_failures": r.critical_failures,
            "controls": {
                k: {"id": v.control_id, "name": v.name, "status": v.status,
                    "score": v.score, "weight": v.weight, "details": v.details}
                for k, v in r.results.controls.items()
            } if hasattr(r, "results") else {
                k: {"id": v.control_id, "name": v.name, "status": v.status,
                    "score": v.score, "weight": v.weight, "details": v.details}
                for k, v in r.controls.items()
            },
            "recommendations": r.recommendations,
        }

    def _save_json(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"assessment_{self._results.business_info.id}.json",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._get_dict(), f, indent=2)
            self._toast("Saved", path)

    def _get_dict(self):
        r = self._results
        pct = round((r.score / r.total_possible) * 100) if r.total_possible else 0
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
                k: {"id": v.control_id, "name": v.name, "status": v.status,
                    "score": v.score, "weight": v.weight, "details": v.details}
                for k, v in r.controls.items()
            },
            "recommendations": r.recommendations,
        }

    def _save_html(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=f"assessment_{self._results.business_info.id}.html",
        )
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
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"assessment_{self._results.business_info.id}.pdf",
        )
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
        pct = round((r.score / r.total_possible) * 100) if r.total_possible else 0
        tier_clr = {"GOLD": "#F5C518", "SILVER": "#C8D0D8",
                    "BRONZE": "#CD8A3A"}.get(tier, "#00C896")
        tier_icon = {"GOLD": "🥇", "SILVER": "🥈", "BRONZE": "🥉"}.get(tier, "✔")
        valid_until = (r.assessment_date.replace(year=r.assessment_date.year + 1)
                       .strftime("%d %B %Y"))
        passed = [c for c in r.controls.values() if c.status == "PASS"]
        passed_html = "".join(
            f"<li>{c.control_id}: {c.name}</li>" for c in passed)

        html = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8">
<title>Certificate — {r.business_info.name}</title>
<style>
  @media print {{body{{margin:0}}}}
  body{{font-family:'Segoe UI',Georgia,sans-serif;background:#f4f2ee;
    display:flex;justify-content:center;align-items:center;
    min-height:100vh;margin:0;padding:20px;box-sizing:border-box}}
  .cert{{background:#fff;border:6px solid {tier_clr};border-radius:20px;
    padding:48px 60px;max-width:760px;width:100%;
    box-shadow:0 8px 40px rgba(0,0,0,.12);text-align:center}}
  .prog{{font-size:12px;color:#888;letter-spacing:3px;text-transform:uppercase;
    margin-bottom:4px}}
  .name{{font-size:22px;font-weight:700;color:#1a2840;margin-bottom:24px}}
  hr{{border:none;border-top:2px solid {tier_clr};margin:20px 0}}
  .award{{font-size:12px;color:#aaa;letter-spacing:3px;
    text-transform:uppercase;margin-bottom:8px}}
  .tier{{font-size:40px;font-weight:900;color:{tier_clr};margin:0}}
  .icon{{font-size:52px;margin:8px 0}}
  .biz{{font-size:26px;font-weight:700;color:#1a2840;margin:16px 0 4px}}
  .meta{{font-size:13px;color:#888;margin-bottom:18px}}
  .score-box{{display:inline-block;border:2px solid {tier_clr};
    border-radius:10px;padding:10px 28px;margin:8px 0 18px;
    background:{tier_clr}18}}
  .score{{font-size:32px;font-weight:700;color:{tier_clr}}}
  .slabel{{font-size:12px;color:#888}}
  .passed-hd{{font-size:11px;text-transform:uppercase;letter-spacing:2px;
    color:#888;margin:20px 0 6px}}
  ul{{text-align:left;display:inline-block;color:#444;
    font-size:12px;line-height:2;margin:0;padding-left:20px}}
  .validity{{margin-top:24px;font-size:11px;color:#aaa}}
  .foot{{margin-top:26px;font-size:10px;color:#ccc}}
</style></head><body>
<div class="cert">
  <div class="prog">University of Zambia · Dept. of Computing & Informatics</div>
  <div class="name">Zambia Digital Hygiene Certification Program</div>
  <hr>
  <div class="award">This certifies that</div>
  <div class="biz">{r.business_info.name}</div>
  <div class="meta">{r.business_info.id}
    {(" · " + r.business_info.province) if r.business_info.province else ""}
    {(" · " + r.business_info.industry) if r.business_info.industry else ""}
  </div>
  <div class="award">has achieved</div>
  <div class="icon">{tier_icon}</div>
  <div class="tier">{tier} CERTIFICATION</div>
  <div class="score-box">
    <div class="score">{pct}%</div>
    <div class="slabel">{r.score} / {r.total_possible} points</div>
  </div>
  <div class="passed-hd">Controls Passed ({len(passed)} of 15)</div>
  <ul>{passed_html}</ul>
  <div class="validity">
    Assessed: {r.assessment_date.strftime('%d %B %Y')} &nbsp;·&nbsp;
    Valid until: {valid_until}
  </div>
  <hr>
  <div class="foot">NIST CSF v1.1 · CIS Controls v8 · ISO 27001:2022 ·
    Zambia Data Protection Act 2021<br>
    Self-assessment certificate issued under the ZDCHP framework.</div>
</div></body></html>"""

        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Certificate", "*.html"), ("All files", "*.*")],
            initialfile=(f"certificate_{r.business_info.id}"
                         f"_{tier.replace(' ', '_')}.html"),
        )
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
        tc = {"GOLD": "#F5C518", "SILVER": "#C8D0D8", "BRONZE": "#CD8A3A",
              "NOT CERTIFIED": "#E84040"}.get(tier, "#E84040")
        sc = {"PASS": "#00C896", "WARNING": "#F0A500", "FAIL": "#E84040",
              "ERROR": "#F0A500", "NOT_ASSESSED": "#6A8099"}
        rows = "".join(
            f"<tr><td style='color:#6A8099;font-size:11px'>{v['id']}</td>"
            f"<td>{v['name']}</td>"
            f"<td style='color:{sc.get(v['status'], '#ccc')};font-weight:bold'>"
            f"{v['status']}</td>"
            f"<td style='color:{sc.get(v['status'], '#ccc')};font-weight:bold'>"
            f"{v['score']}/{v['weight']}</td>"
            f"<td style='font-size:11px;color:#6A8099'>{v['details'][:60]}</td></tr>"
            for v in d["controls"].values()
        )
        recs = "".join(f"<li>{r}</li>"
                      for r in d.get("recommendations", []))
        return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8">
<title>Assessment Report — {d['business']['name']}</title>
<style>
  body{{font-family:'Segoe UI',sans-serif;background:#0B1622;
    color:#E8F1FF;margin:0;padding:32px}}
  h1{{color:{tc}}} h2{{color:#00C896;border-bottom:1px solid #1E2E42;
    padding-bottom:6px}}
  .badge{{background:#152030;border-radius:16px;padding:24px;
    text-align:center;margin-bottom:24px}}
  .score{{font-size:44px;font-weight:bold;color:{tc}}}
  table{{width:100%;border-collapse:collapse;background:#152030;
    border-radius:10px;overflow:hidden}}
  th{{background:#1E2E42;padding:10px 14px;text-align:left;
    font-size:11px;color:#6A8099;text-transform:uppercase}}
  td{{padding:10px 14px;border-bottom:1px solid #0B1622;font-size:12px}}
  ul{{color:#E8F1FF;line-height:2}}
  footer{{margin-top:40px;color:#6A8099;font-size:10px;text-align:center}}
</style></head><body>
<div class="badge">
  <p style="color:#6A8099;margin:0">{d['business']['name']} ·
    {d['business']['id']}</p>
  <h1>{tier} CERTIFICATION</h1>
  <div class="score">{pct}%</div>
  <p>{d['score']} / {d['total_possible']} points ·
    {d['assessment_date'][:10]}</p>
</div>
<h2>Control Results</h2>
<table><thead><tr>
  <th>ID</th><th>Control</th><th>Status</th>
  <th>Score</th><th>Details</th>
</tr></thead><tbody>{rows}</tbody></table>
<h2 style="margin-top:28px">Recommendations</h2>
<ul>{recs}</ul>
<footer>Zambia Digital Hygiene Certification Programme &nbsp;·&nbsp;
  University of Zambia &nbsp;·&nbsp;
  Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
</body></html>"""

    # ----------------------------------------------------------------- dialogs
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
