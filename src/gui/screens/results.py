"""Results screen — shows certification tier, score breakdown, and save report."""

import datetime
import json
import os
import customtkinter as ctk
from tkinter import filedialog

from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_ACCENT, CLR_TEXT, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER,
    CLR_GOLD, CLR_SILVER, CLR_BRONZE,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL, PAD,
    TIER_COLOURS,
)

TIER_ICON = {
    "GOLD":          "🥇",
    "SILVER":        "🥈",
    "BRONZE":        "🥉",
    "NOT CERTIFIED": "❌",
}


class ResultsScreen(ctk.CTkFrame):
    """Displays the final score, tier badge, control breakdown and report export."""

    def __init__(self, master, results, on_restart):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._results = results
        self._on_restart = on_restart
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        r = self._results
        tier = r.certification_level
        pct = round((r.score / r.total_possible) * 100) if r.total_possible else 0
        tier_colour = TIER_COLOURS.get(tier, CLR_DANGER)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=84)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        hdr.grid_columnconfigure(1, weight=0)
        ctk.CTkLabel(
            hdr, text="Assessment Results",
            font=FONT_HEADING, text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=PAD, pady=(16, 6), sticky="w")
        ctk.CTkLabel(
            hdr, text="Step 4 of 4",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(row=0, column=1, padx=PAD, pady=(16, 6), sticky="e")
        progress = ctk.CTkProgressBar(
            hdr, fg_color=CLR_BG, progress_color=CLR_ACCENT,
            corner_radius=6, height=10,
        )
        progress.set(1.0)
        progress.grid(row=1, column=0, columnspan=2, sticky="ew", padx=PAD, pady=(0, 16))

        # Scrollable body
        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # ── Certification badge ──────────────────────────────────────
        badge = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=18, border_width=1, border_color=CLR_BORDER)
        badge.grid(row=0, column=0, padx=PAD, pady=(PAD, 12), sticky="ew")
        badge.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            badge, text=TIER_ICON.get(tier, ""), font=("Segoe UI Emoji", 52),
        ).grid(row=0, column=0, pady=(22, 8))

        ctk.CTkLabel(
            badge, text=f"{tier} CERTIFICATION",
            font=("Segoe UI", 22, "bold"), text_color=tier_colour,
        ).grid(row=1, column=0)

        ctk.CTkLabel(
            badge,
            text=f"{r.business_info.name}  •  {r.business_info.id}",
            font=FONT_BODY, text_color=CLR_TEXT,
        ).grid(row=2, column=0, pady=(8, 0))

        ctk.CTkLabel(
            badge,
            text=f"Score: {r.score} / {r.total_possible}  ({pct}%)",
            font=("Segoe UI", 14, "bold"), text_color=tier_colour,
        ).grid(row=3, column=0, pady=(4, 10))

        # Score bar
        bar = ctk.CTkProgressBar(
            badge, fg_color=CLR_BG, progress_color=tier_colour,
            height=14, corner_radius=7,
        )
        bar.set(pct / 100)
        bar.grid(row=4, column=0, padx=PAD * 2, pady=(0, 22), sticky="ew")

        metrics = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=18, border_width=1, border_color=CLR_BORDER)
        metrics.grid(row=1, column=0, padx=PAD, pady=(0, 16), sticky="ew")
        metrics.grid_columnconfigure((0, 1, 2), weight=1)

        counts = {
            "PASS": sum(1 for ctrl in r.controls.values() if ctrl.status == "PASS"),
            "WARNING": sum(1 for ctrl in r.controls.values() if ctrl.status == "WARNING"),
            "FAIL": sum(1 for ctrl in r.controls.values() if ctrl.status == "FAIL"),
        }
        labels = [
            ("Passed", counts["PASS"], CLR_SUCCESS),
            ("Review", counts["WARNING"], CLR_WARNING),
            ("Failed", counts["FAIL"], CLR_DANGER),
        ]
        for idx, (label, value, colour) in enumerate(labels):
            cell = ctk.CTkFrame(metrics, fg_color="transparent")
            cell.grid(row=0, column=idx, padx=8, pady=18, sticky="ew")
            cell.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                cell, text=label, font=FONT_SMALL, text_color=CLR_MUTED,
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                cell, text=str(value), font=("Segoe UI", 24, "bold"), text_color=colour,
            ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        # ── Control breakdown ────────────────────────────────────────
        ctk.CTkLabel(
            scroll, text="Control Breakdown",
            font=FONT_HEADING, text_color=CLR_TEXT,
        ).grid(row=1, column=0, padx=PAD, pady=(12, 4), sticky="w")

        STATUS_CLR = {
            "PASS": CLR_SUCCESS, "WARNING": CLR_WARNING,
            "FAIL": CLR_DANGER, "ERROR": CLR_WARNING,
            "NOT_ASSESSED": CLR_MUTED,
        }
        STATUS_ICON = {
            "PASS": "✔", "WARNING": "⚠", "FAIL": "✖",
            "ERROR": "!", "NOT_ASSESSED": "–",
        }

        for i, (key, ctrl) in enumerate(r.controls.items()):
            row_f = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=14, border_width=1, border_color=CLR_BORDER)
            row_f.grid(row=i + 3, column=0, padx=PAD, pady=6, sticky="ew")
            row_f.grid_columnconfigure(1, weight=1)

            clr = STATUS_CLR.get(ctrl.status, CLR_MUTED)
            icon = STATUS_ICON.get(ctrl.status, "?")

            ctk.CTkLabel(
                row_f, text=icon, font=("Segoe UI", 14),
                text_color=clr, width=32,
            ).grid(row=0, column=0, padx=(14, 8), pady=18)

            ctk.CTkLabel(
                row_f, text=f"{ctrl.control_id}  {ctrl.name}",
                font=FONT_BODY, text_color=CLR_TEXT, anchor="w",
            ).grid(row=0, column=1, sticky="w")

            ctk.CTkLabel(
                row_f, text=f"{ctrl.score}/{ctrl.weight}",
                font=("Segoe UI", 11, "bold"), text_color=clr, anchor="e",
            ).grid(row=0, column=2, padx=14, sticky="e")

        base_row = len(r.controls) + 3

        # ── Recommendations ──────────────────────────────────────────
        if r.recommendations:
            ctk.CTkLabel(
                scroll, text="Recommendations",
                font=FONT_HEADING, text_color=CLR_TEXT,
            ).grid(row=base_row, column=0, padx=PAD, pady=(14, 4), sticky="w")

            for j, rec in enumerate(r.recommendations[:8]):
                rec_f = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=8)
                rec_f.grid(row=base_row + 1 + j, column=0, padx=PAD, pady=3, sticky="ew")
                rec_f.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(
                    rec_f, text="→", font=FONT_BODY, text_color=CLR_ACCENT, width=24,
                ).grid(row=0, column=0, padx=(10, 4), pady=8)
                ctk.CTkLabel(
                    rec_f, text=rec, font=FONT_SMALL, text_color=CLR_TEXT,
                    wraplength=740, justify="left", anchor="w",
                ).grid(row=0, column=1, padx=(0, 10), pady=8, sticky="w")

        # ── Nav ──────────────────────────────────────────────────────
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=64)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            nav, text="New Assessment",
            font=FONT_BODY,
            fg_color="transparent", border_color=CLR_MUTED, border_width=1,
            text_color=CLR_TEXT, hover_color="#243447", height=36, corner_radius=18,
            command=self._on_restart,
        ).grid(row=0, column=0, padx=PAD, pady=14)

        ctk.CTkButton(
            nav, text="💾  Save JSON Report",
            font=FONT_BODY,
            fg_color=CLR_ACCENT, hover_color="#00A87A",
            text_color="#000000", height=36, corner_radius=18,
            command=self._save_json,
        ).grid(row=0, column=2, padx=(0, 8), pady=14)

        ctk.CTkButton(
            nav, text="📄  Save HTML Report",
            font=FONT_BODY,
            fg_color=CLR_ACCENT, hover_color="#00A87A",
            text_color="#000000", height=36, corner_radius=18,
            command=self._save_html,
        ).grid(row=0, column=3, padx=(0, PAD), pady=14)

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
            "percentage": round((r.score / r.total_possible) * 100) if r.total_possible else 0,
            "certification_level": r.certification_level,
            "critical_failures": r.critical_failures,
            "controls": {
                k: {
                    "id": v.control_id,
                    "name": v.name,
                    "status": v.status,
                    "score": v.score,
                    "weight": v.weight,
                    "details": v.details,
                }
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
                json.dump(self._to_dict(), f, indent=2)
            self._show_saved(path)

    def _save_html(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=f"assessment_{self._results.business_info.id}.html",
        )
        if path:
            html = self._build_html()
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            self._show_saved(path)
            # Open in browser automatically
            import subprocess
            try:
                os.startfile(path)   # Windows
            except AttributeError:
                subprocess.Popen(["xdg-open", path])

    def _show_saved(self, path):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Saved")
        dlg.geometry("440x140")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        ctk.CTkLabel(
            dlg, text="✔  Report saved successfully!",
            font=FONT_HEADING, text_color=CLR_SUCCESS,
        ).pack(pady=(24, 4))
        ctk.CTkLabel(
            dlg, text=path, font=FONT_SMALL, text_color=CLR_MUTED,
            wraplength=400,
        ).pack(pady=(0, 16))
        ctk.CTkButton(
            dlg, text="OK", fg_color=CLR_ACCENT, text_color="#000000",
            command=dlg.destroy,
        ).pack()

    def _build_html(self):
        r = self._results
        d = self._to_dict()
        pct = d["percentage"]
        tier = d["certification_level"]
        tier_colour = {
            "GOLD": "#FFD700", "SILVER": "#C0C0C0",
            "BRONZE": "#CD7F32", "NOT CERTIFIED": "#FF4C4C",
        }.get(tier, "#FF4C4C")
        status_colours = {
            "PASS": "#00C896", "WARNING": "#FFB800",
            "FAIL": "#FF4C4C", "ERROR": "#FFB800", "NOT_ASSESSED": "#7A8FA6",
        }

        controls_html = ""
        for k, v in d["controls"].items():
            clr = status_colours.get(v["status"], "#7A8FA6")
            controls_html += f"""
            <tr>
                <td style="color:#7A8FA6;font-size:12px">{v['id']}</td>
                <td>{v['name']}</td>
                <td style="color:{clr};font-weight:bold">{v['status']}</td>
                <td style="color:{clr};font-weight:bold">{v['score']}/{v['weight']}</td>
                <td style="font-size:11px;color:#7A8FA6">{v['details'][:80]}</td>
            </tr>"""

        recs_html = "".join(
            f"<li>{rec}</li>" for rec in d.get("recommendations", [])
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Digital Hygiene Assessment — {d['business']['name']}</title>
<style>
  body{{font-family:'Segoe UI',sans-serif;background:#0D1B2A;color:#E6F1FF;margin:0;padding:32px}}
  h1{{color:{tier_colour};}} h2{{color:#00C896;border-bottom:1px solid #1B2A3B;padding-bottom:6px}}
  .badge{{background:#1B2A3B;border-radius:16px;padding:24px;text-align:center;margin-bottom:24px}}
  .score{{font-size:48px;font-weight:bold;color:{tier_colour}}}
  table{{width:100%;border-collapse:collapse;background:#1B2A3B;border-radius:10px;overflow:hidden}}
  th{{background:#243447;padding:10px 14px;text-align:left;font-size:12px;color:#7A8FA6;text-transform:uppercase}}
  td{{padding:10px 14px;border-bottom:1px solid #0D1B2A;font-size:13px}}
  .bar-outer{{background:#243447;border-radius:6px;height:10px;width:300px;display:inline-block}}
  .bar-inner{{background:{tier_colour};border-radius:6px;height:10px;width:{pct*3}px}}
  ul{{color:#E6F1FF;line-height:2}}
  footer{{margin-top:40px;color:#7A8FA6;font-size:11px;text-align:center}}
</style>
</head>
<body>
<div class="badge">
  <p style="color:#7A8FA6;margin:0">{d['business']['name']}  •  {d['business']['id']}</p>
  <h1>{tier} CERTIFICATION</h1>
  <div class="score">{pct}%</div>
  <p>{d['score']} / {d['total_possible']} points</p>
  <div class="bar-outer"><div class="bar-inner"></div></div>
  <p style="color:#7A8FA6;font-size:12px">Assessment date: {d['assessment_date'][:10]}</p>
</div>

<h2>Control Results</h2>
<table>
  <thead><tr><th>ID</th><th>Control</th><th>Status</th><th>Score</th><th>Details</th></tr></thead>
  <tbody>{controls_html}</tbody>
</table>

<h2 style="margin-top:28px">Recommendations</h2>
<ul>{recs_html}</ul>

<footer>
  Zambia Digital Hygiene Certification Program &nbsp;•&nbsp;
  University of Zambia, Dept. of Computing &amp; Informatics &nbsp;•&nbsp;
  Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
</footer>
</body>
</html>"""
