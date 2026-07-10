"""
Server Hardening Audit Screen
Audits the Windows host that *provides* services to end users — the
infrastructure side of digital hygiene. Fourteen server-grade checks
covering legacy protocols, remote access, credential protections,
risky services and security logging.
"""

import datetime
import threading
from tkinter import filedialog

import customtkinter as ctk

from src.gui.screens.business_info import _header
from src.gui.screens._cancellable import CancellableScreenMixin
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_ACCENT_HOV,
    CLR_BG,
    CLR_BLUE,
    CLR_BORDER,
    CLR_DANGER,
    CLR_DIVIDER,
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
    FONT_HEADING,
    FONT_SMALL,
    FONT_SUBHEAD,
    NAV_H,
    PAD,
)
from src.security.hardening.checks import (
    HardeningCheckResult,
    HardeningReport,
    WindowsHardeningAuditor,
)

GRADE_STYLE = {
    "HARDENED": {
        "icon": "🛡️",
        "colour": CLR_SUCCESS,
        "title": "INFRASTRUCTURE HARDENED",
        "msg": "This host meets server-grade digital hygiene standards. "
               "The services it provides to end users rest on a hardened base.",
    },
    "NEEDS ATTENTION": {
        "icon": "⚠️",
        "colour": CLR_WARNING,
        "title": "NEEDS ATTENTION",
        "msg": "The basics are in place, but gaps remain that attackers on the "
               "network can exploit. Apply the fixes below, most severe first.",
    },
    "AT RISK": {
        "icon": "🚨",
        "colour": CLR_DANGER,
        "title": "INFRASTRUCTURE AT RISK",
        "msg": "This host has serious hardening gaps. End users of the services "
               "it provides are exposed no matter how careful they are — "
               "remediate the failures below before anything else.",
    },
    "NOT APPLICABLE": {
        "icon": "ℹ️",
        "colour": CLR_MUTED,
        "title": "NOT APPLICABLE",
        "msg": "These checks target Windows hosts. Run the audit on the "
               "Windows machine that provides your services.",
    },
}

SEV_CLR = {
    "CRITICAL": CLR_DANGER,
    "HIGH":     "#E87000",
    "MEDIUM":   CLR_WARNING,
    "LOW":      CLR_MUTED,
}

STATUS_STYLE = {
    "PASS":           ("✔", CLR_SUCCESS),
    "WARNING":        ("⚠", CLR_WARNING),
    "FAIL":           ("✖", CLR_DANGER),
    "ERROR":          ("!", CLR_MUTED),
    "NOT_APPLICABLE": ("–", CLR_MUTED),
}

CAT_ICON = {
    "protocol":      "📡",
    "remote-access": "🖥️",
    "credentials":   "🔑",
    "services":      "⚙️",
    "logging":       "📝",
}


class ServerHardeningScreen(CancellableScreenMixin, ctk.CTkFrame):
    """Runs the Windows infrastructure hardening audit and shows results."""

    # (label, method-name) pairs — run in order for progress feedback
    CHECK_SEQUENCE = [
        ("Protocols: SMBv1…",                "check_smb1"),
        ("Protocols: SMB signing…",          "check_smb_signing"),
        ("Remote access: RDP hardening…",    "check_rdp_hardening"),
        ("Credentials: UAC…",                "check_uac"),
        ("Protocols: LLMNR / NetBIOS…",      "check_llmnr_netbios"),
        ("Logging: PowerShell logging…",     "check_powershell_logging"),
        ("Protocols: Legacy TLS…",           "check_legacy_tls"),
        ("Services: Unquoted paths…",        "check_unquoted_service_paths"),
        ("Services: Print Spooler…",         "check_print_spooler"),
        ("Services: Remote Registry…",       "check_remote_registry"),
        ("Logging: Audit policy…",           "check_audit_policy"),
        ("Credentials: Local accounts…",     "check_local_accounts"),
        ("Credentials: LSA protections…",    "check_lsa_protections"),
        ("Credentials: Anonymous access…",   "check_anonymous_enumeration"),
    ]

    def __init__(self, master, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back
        self._scanning = False
        self._report: HardeningReport | None = None
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        _header(self, "Server Hardening Audit", "Tools", 0.0)

        # ── Controls bar ──────────────────────────────────────────────
        ctrl = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                            height=58)
        ctrl.grid(row=1, column=0, sticky="ew")
        ctrl.grid_columnconfigure(0, weight=1)
        ctrl.grid_propagate(False)

        ctk.CTkLabel(
            ctrl,
            text="Audits THIS machine — run it on the server that provides "
                 "services to your users.",
            font=FONT_SMALL, text_color=CLR_MUTED, anchor="w",
        ).grid(row=0, column=0, padx=PAD, pady=14, sticky="w")

        self._scan_btn = ctk.CTkButton(
            ctrl, text="▶  Run Hardening Audit",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#FFFFFF", height=34, corner_radius=BTN_R,
            command=self._start_scan,
        )
        self._scan_btn.grid(row=0, column=1, padx=(0, PAD), pady=14)

        # ── Body: grade + scrollable results ──────────────────────────
        body = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        self._body = body

        self._placeholder = ctk.CTkLabel(
            body,
            text="Click  ▶ Run Hardening Audit  to assess this host\n\n"
                 "14 server-grade checks:  SMBv1 · SMB signing · RDP/NLA · UAC\n"
                 "LLMNR/NetBIOS · PowerShell logging · legacy TLS · service paths\n"
                 "Print Spooler · Remote Registry · audit policy · local accounts\n"
                 "LSA protections · anonymous enumeration",
            font=FONT_BODY, text_color=CLR_MUTED, justify="center",
        )
        self._placeholder.grid(row=0, column=0, pady=60)

        # Progress bar (shown during scan)
        self._progress = ctk.CTkProgressBar(
            self, fg_color=CLR_DIVIDER, progress_color=CLR_ACCENT,
            height=3, corner_radius=0)
        self._progress.set(0)
        self._progress.grid(row=2, column=0, sticky="new")
        self._progress.grid_remove()

        # Nav
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                           height=NAV_H)
        nav.grid(row=3, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)
        nav.grid_propagate(False)

        ctk.CTkButton(
            nav, text="← Back", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC, hover_color=CLR_SURFACE_ALT,
            width=100, height=BTN_H, corner_radius=BTN_R,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

        self._export_btn = ctk.CTkButton(
            nav, text="📄  Export Report",
            font=FONT_SMALL,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC,
            height=BTN_H, corner_radius=BTN_R,
            state="disabled", command=self._export_html,
        )
        self._export_btn.grid(row=0, column=2, padx=(0, PAD), pady=14)

    # ------------------------------------------------------------------- scan
    def _start_scan(self):
        if self._scanning:
            return
        self._scanning = True
        self._report = None
        self._scan_btn.configure(state="disabled", text="Auditing…")
        self._export_btn.configure(state="disabled")

        for w in self._body.winfo_children():
            w.destroy()

        self._progress.grid()
        self._progress.set(0)
        self._status_lbl = ctk.CTkLabel(
            self._body, text="Starting hardening audit…",
            font=FONT_SMALL, text_color=CLR_MUTED)
        self._status_lbl.grid(row=0, column=0, pady=(16, 4))

        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        auditor = WindowsHardeningAuditor()
        checks = []
        total = len(self.CHECK_SEQUENCE)
        for i, (label, method_name) in enumerate(self.CHECK_SEQUENCE, 1):
            if not self._safe_after(
                    0, lambda lbl=label: self._status_lbl.configure(text=lbl)):
                return
            try:
                checks.append(getattr(auditor, method_name)())
            except Exception as exc:
                checks.append(HardeningCheckResult(
                    check_id="ERR", name=label.rstrip("…"),
                    status="ERROR", severity="MEDIUM",
                    details=str(exc)))
            if not self._safe_after(0, self._progress.set, i / total):
                return

        self._report = HardeningReport(checks=checks)
        self._safe_after(0, self._show_results)

    # ---------------------------------------------------------------- results
    def _show_results(self):
        self._scanning = False
        self._scan_btn.configure(state="normal", text="▶  Re-run Audit")
        self._export_btn.configure(state="normal")
        self._progress.grid_remove()

        report = self._report
        if report is None:
            return
        gs = GRADE_STYLE.get(report.grade, GRADE_STYLE["NOT APPLICABLE"])

        for w in self._body.winfo_children():
            w.destroy()

        row = [0]

        def next_row():
            r = row[0]
            row[0] += 1
            return r

        # ── Grade hero ────────────────────────────────────────────────
        hero = ctk.CTkFrame(self._body, fg_color=CLR_SURFACE,
                            corner_radius=16, border_width=2,
                            border_color=gs["colour"])
        hero.grid(row=next_row(), column=0, padx=PAD,
                  pady=(PAD, 10), sticky="ew")
        hero.grid_columnconfigure(0, weight=1)

        ctk.CTkFrame(hero, fg_color=gs["colour"], height=4,
                     corner_radius=0).grid(row=0, column=0, sticky="ew")

        inner = ctk.CTkFrame(hero, fg_color="transparent")
        inner.grid(row=1, column=0, padx=PAD, pady=14, sticky="ew")
        inner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(inner, text=gs["icon"],
                     font=("Segoe UI Emoji", 40),
                     ).grid(row=0, column=0, rowspan=2, padx=(0, 18), pady=4)
        ctk.CTkLabel(inner, text=gs["title"],
                     font=("Segoe UI", 18, "bold"),
                     text_color=gs["colour"],
                     ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(inner, text=gs["msg"],
                     font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     wraplength=600, justify="left",
                     ).grid(row=1, column=1, sticky="w")

        ctk.CTkLabel(inner,
                     text=f"{report.score_percent}%\nhardened",
                     font=("Segoe UI", 14, "bold"),
                     text_color=gs["colour"], justify="center",
                     ).grid(row=0, column=2, rowspan=2, padx=(PAD, 0))

        # ── Summary strip ─────────────────────────────────────────────
        strip = ctk.CTkFrame(self._body, fg_color=CLR_SURFACE,
                             corner_radius=14, border_width=1,
                             border_color=CLR_BORDER)
        strip.grid(row=next_row(), column=0, padx=PAD,
                   pady=(0, 12), sticky="ew")
        cells = [
            ("Passed",   report.passed,            CLR_SUCCESS),
            ("Warnings", report.warnings,          CLR_WARNING),
            ("Failed",   report.failed,            CLR_DANGER),
            ("Critical", report.critical_failures, CLR_DANGER),
            ("Host",     report.hostname,          CLR_BLUE),
        ]
        strip.grid_columnconfigure(tuple(range(len(cells))), weight=1)
        for col_i, (label, value, clr) in enumerate(cells):
            cell = ctk.CTkFrame(strip, fg_color="transparent")
            cell.grid(row=0, column=col_i, padx=12, pady=14)
            ctk.CTkLabel(cell, text=label,
                         font=FONT_CAPTION, text_color=CLR_MUTED).pack()
            ctk.CTkLabel(cell, text=str(value),
                         font=("Segoe UI", 15, "bold"),
                         text_color=clr).pack()

        # ── Individual check results ──────────────────────────────────
        ctk.CTkLabel(self._body, text="Check Details",
                     font=FONT_HEADING, text_color=CLR_TEXT,
                     ).grid(row=next_row(), column=0, padx=PAD,
                            pady=(4, 6), sticky="w")

        status_order = {"FAIL": 0, "ERROR": 1, "WARNING": 2,
                        "PASS": 3, "NOT_APPLICABLE": 4}
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_checks = sorted(
            report.checks,
            key=lambda c: (status_order.get(c.status, 5),
                           sev_order.get(c.severity, 4)),
        )
        for check in sorted_checks:
            self._make_check_card(self._body, next_row(), check)

    def _make_check_card(self, parent, row_idx: int,
                         check: HardeningCheckResult):
        icon, status_clr = STATUS_STYLE.get(check.status, ("?", CLR_MUTED))

        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE,
                            corner_radius=12, border_width=1,
                            border_color=CLR_BORDER)
        card.grid(row=row_idx, column=0, padx=PAD, pady=3, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # Left status stripe
        ctk.CTkFrame(card, fg_color=status_clr, width=4,
                     corner_radius=0).grid(row=0, column=0,
                                           rowspan=3, sticky="ns")

        # Icon
        ctk.CTkLabel(card, text=icon,
                     font=("Segoe UI", 13), text_color=status_clr,
                     width=26,
                     ).grid(row=0, column=1, padx=(10, 4),
                            pady=(10, 2), sticky="n")

        # Check name + category
        name_f = ctk.CTkFrame(card, fg_color="transparent")
        name_f.grid(row=0, column=2, sticky="w", pady=(10, 2))
        ctk.CTkLabel(name_f,
                     text=f"{check.check_id}  {check.name}",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(side="left")
        if check.category:
            ctk.CTkLabel(name_f,
                         text=f"  [{CAT_ICON.get(check.category, '📋')} "
                              f"{check.category.replace('-', ' ').title()}]",
                         font=FONT_CAPTION, text_color=CLR_MUTED,
                         ).pack(side="left")

        # Severity badge
        ctk.CTkLabel(card,
                     text=check.severity,
                     font=("Segoe UI", 9, "bold"),
                     text_color=SEV_CLR.get(check.severity, CLR_MUTED),
                     fg_color=CLR_SURFACE_ALT, corner_radius=6,
                     width=68, height=20,
                     ).grid(row=0, column=3, padx=(0, 12),
                            pady=(10, 2), sticky="ne")

        # Details
        ctk.CTkLabel(card, text=check.details,
                     font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     anchor="w", wraplength=700, justify="left",
                     ).grid(row=1, column=1, columnspan=3,
                            padx=(10, 12), pady=(0, 4), sticky="w")

        # Remediation for anything that isn't a clean pass
        if check.status in ("FAIL", "WARNING", "ERROR") and check.remediation:
            rem_f = ctk.CTkFrame(card, fg_color=CLR_SURFACE_ALT,
                                 corner_radius=8, border_width=1,
                                 border_color=CLR_BORDER)
            rem_f.grid(row=2, column=1, columnspan=3,
                       padx=(10, 12), pady=(0, 10), sticky="ew")
            rem_f.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(rem_f, text="Fix:",
                         font=("Segoe UI", 9, "bold"),
                         text_color=CLR_ACCENT, width=28,
                         ).grid(row=0, column=0, padx=(10, 4), pady=6)
            ctk.CTkLabel(rem_f, text=check.remediation,
                         font=FONT_CAPTION, text_color=CLR_TEXT_SEC,
                         anchor="w", wraplength=660, justify="left",
                         ).grid(row=0, column=1, padx=(0, 10),
                                pady=6, sticky="w")

    # ---------------------------------------------------------------- export
    def _export_html(self):
        report = self._report
        if report is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Report", "*.html"), ("All files", "*.*")],
            initialfile=(f"hardening_audit_"
                         f"{datetime.date.today().isoformat()}.html"),
        )
        if not path:
            return

        gs = GRADE_STYLE.get(report.grade, GRADE_STYLE["NOT APPLICABLE"])
        status_order = {"FAIL": 0, "ERROR": 1, "WARNING": 2,
                        "PASS": 3, "NOT_APPLICABLE": 4}
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

        rows_html = ""
        for c in sorted(report.checks,
                        key=lambda x: (status_order.get(x.status, 5),
                                       sev_order.get(x.severity, 4))):
            clr = {
                "PASS": "#6C5FC7", "WARNING": "#F0A500",
                "FAIL": "#E84040", "ERROR": "#A0B4C8",
                "NOT_APPLICABLE": "#A0B4C8",
            }.get(c.status, "#A0B4C8")
            icon = {"PASS": "✔", "WARNING": "⚠", "FAIL": "✖"}.get(c.status, "–")
            rows_html += (
                f"<tr>"
                f"<td style='color:{clr};font-weight:bold'>{icon}</td>"
                f"<td style='font-size:11px;color:#5A7490'>{c.check_id}</td>"
                f"<td>{c.name}</td>"
                f"<td style='color:{clr};font-weight:bold'>{c.status}</td>"
                f"<td>{c.severity}</td>"
                f"<td style='font-size:11px'>{c.details}</td>"
                f"<td style='font-size:11px;color:#F0A500'>"
                f"{c.remediation or '—'}</td>"
                f"</tr>"
            )

        html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<title>Server Hardening Audit — {report.hostname}</title>
<style>
 body{{font-family:'Segoe UI',sans-serif;background:#0B1622;
  color:#ECF4FF;margin:0;padding:32px}}
 h1{{color:{gs['colour']}}}
 .badge{{background:#132236;border-radius:16px;padding:24px;
  margin-bottom:28px;border:2px solid {gs['colour']};
  display:flex;align-items:center;gap:20px}}
 .big{{font-size:42px}}
 .verdict{{font-size:22px;font-weight:bold;color:{gs['colour']}}}
 .msg{{font-size:12px;color:#A0B4C8;margin-top:6px;max-width:600px}}
 .score{{font-size:32px;font-weight:bold;color:{gs['colour']};
  margin-left:auto}}
 table{{width:100%;border-collapse:collapse;background:#132236;
  border-radius:10px;overflow:hidden}}
 th{{background:#1A2D42;padding:10px 14px;text-align:left;
  font-size:11px;color:#5A7490;text-transform:uppercase}}
 td{{padding:8px 14px;border-bottom:1px solid #0B1622;font-size:12px}}
 h2{{color:#2485E8;border-bottom:1px solid #1A2D42;padding-bottom:6px}}
 footer{{margin-top:40px;color:#5A7490;font-size:10px;text-align:center}}
</style></head><body>
<h1>🛡️ Server Hardening Audit</h1>
<div class="badge">
 <div class="big">{gs['icon']}</div>
 <div>
  <div class="verdict">{gs['title']}</div>
  <div class="msg">{gs['msg']}</div>
  <div style="margin-top:8px;font-size:11px;color:#5A7490">
   Host: {report.hostname} &nbsp;·&nbsp; OS: {report.os_info} &nbsp;·&nbsp;
   Audited: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
  </div>
 </div>
 <div class="score">{report.score_percent}%</div>
</div>
<h2>Check Results</h2>
<table><thead><tr>
 <th></th><th>ID</th><th>Check</th><th>Status</th>
 <th>Severity</th><th>Details</th><th>Remediation</th>
</tr></thead><tbody>{rows_html}</tbody></table>
<footer>Zambia Digital Hygiene Certification Programme
  · Server Hardening Audit
  · University of Zambia
</footer>
</body></html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        try:
            import os
            os.startfile(path)  # type: ignore
        except AttributeError:
            import subprocess as sp
            sp.Popen(["xdg-open", path])

        dlg = ctk.CTkToplevel(self)
        dlg.title("Saved")
        dlg.geometry("420x120")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text="✔  Report saved!",
                     font=FONT_SUBHEAD, text_color=CLR_SUCCESS,
                     ).pack(pady=(20, 4))
        ctk.CTkLabel(dlg, text=path, font=FONT_CAPTION,
                     text_color=CLR_MUTED, wraplength=380,
                     ).pack(pady=(0, 12))
        ctk.CTkButton(dlg, text="OK",
                      fg_color=CLR_ACCENT, text_color="#FFFFFF",
                      height=BTN_H, corner_radius=BTN_R,
                      command=dlg.destroy).pack()
