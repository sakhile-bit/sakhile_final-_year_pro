"""Infrastructure Scanner — scan any domain or IP for web-facing security."""

import datetime
import threading
from tkinter import filedialog

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_BORDER, CLR_SUCCESS, CLR_WARNING, CLR_DANGER,
    FONT_BODY, FONT_SMALL, FONT_SUBHEAD, FONT_CAPTION,
    PAD, NAV_H, BTN_H, BTN_R,
)
from src.gui.screens.business_info import _header
from src.gui import motion

# Verdict styling — mirrors the Server Hardening screen's grade hero.
GRADE_STYLE = {
    "SECURE": ("🛡️", CLR_SUCCESS, "INFRASTRUCTURE SECURE",
               "This host's public-facing surface meets good hygiene "
               "standards. Keep certificates and headers current."),
    "NEEDS ATTENTION": ("⚠️", CLR_WARNING, "NEEDS ATTENTION",
                        "The basics are mostly in place, but attackers can "
                        "still exploit the gaps below. Fix them worst-first."),
    "AT RISK": ("🚨", CLR_DANGER, "INFRASTRUCTURE AT RISK",
                "Serious exposure was found. Remediate the failures below "
                "before anything else — they put your users at risk."),
}

SEV_CLR = {
    "CRITICAL": CLR_DANGER, "HIGH": "#E87000",
    "MEDIUM": CLR_WARNING, "LOW": CLR_MUTED, "INFO": CLR_MUTED,
}
SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


class InfraScannerScreen(ctk.CTkFrame):
    """Scan a domain or IP for SSL, open ports, security headers and DNS."""

    def __init__(self, master, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back
        self._scanning = False
        self._last_result: dict | None = None
        self._last_target: str = ""
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        _header(self, "Infrastructure Scanner", "Infra Scan", 0.0)

        # Scrollable body
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=CLR_BG, corner_radius=0)
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)
        motion.smooth_scroll(self._scroll)

        # Info banner
        info = ctk.CTkFrame(
            self._scroll, fg_color=CLR_SURFACE_ALT,
            corner_radius=10, border_width=1, border_color=CLR_BORDER)
        info.grid(row=0, column=0, padx=PAD, pady=(PAD, 10), sticky="ew")
        ctk.CTkLabel(
            info,
            text="Enter a domain name or IP address to check its SSL "
                 "certificate, open ports, HTTP security headers and DNS "
                 "configuration.",
            font=FONT_SMALL, text_color=CLR_MUTED,
            wraplength=800, justify="left",
        ).grid(padx=14, pady=10)

        # Input row
        input_row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        input_row.grid(row=1, column=0, padx=PAD, pady=(0, 14), sticky="ew")
        input_row.grid_columnconfigure(0, weight=1)

        self._target_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="e.g.  example.com   or   192.168.1.1",
            font=FONT_BODY, text_color=CLR_TEXT,
            fg_color=CLR_SURFACE, border_color=CLR_BORDER, border_width=1,
            height=42, corner_radius=10,
        )
        self._target_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._target_entry.bind("<Return>", lambda _e: self._start_scan())

        self._scan_btn = ctk.CTkButton(
            input_row, text="Scan",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color="#7D70D6",
            text_color="#FFFFFF",
            width=100, height=42, corner_radius=10,
            command=self._start_scan,
        )
        self._scan_btn.grid(row=0, column=1)

        # Status label
        self._status_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            self._scroll, textvariable=self._status_var,
            font=FONT_CAPTION, text_color=CLR_MUTED,
        ).grid(row=2, column=0, padx=PAD, pady=(0, 4), sticky="w")

        # Results container — rebuilt on each scan
        self._results_frame = ctk.CTkFrame(
            self._scroll, fg_color="transparent", corner_radius=0)
        self._results_frame.grid(row=3, column=0, sticky="ew")
        self._results_frame.grid_columnconfigure(0, weight=1)

        # Nav bar
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                           height=NAV_H)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)
        nav.grid_propagate(False)
        ctk.CTkButton(
            nav, text="<- Back to Home",
            font=FONT_BODY,
            fg_color="transparent", border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC, hover_color=CLR_SURFACE_ALT,
            width=150, height=BTN_H, corner_radius=BTN_R,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

        self._export_btn = ctk.CTkButton(
            nav, text="📄  Export Report",
            font=FONT_SMALL,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE,
            border_color=CLR_BORDER, border_width=1, text_color=CLR_TEXT_SEC,
            height=BTN_H, corner_radius=BTN_R,
            state="disabled", command=self._export_html,
        )
        self._export_btn.grid(row=0, column=2, padx=(0, PAD), pady=14)

    # ----------------------------------------------------------------- scan
    def _start_scan(self):
        if self._scanning:
            return
        target = self._target_entry.get().strip()
        if not target:
            self._status_var.set("Please enter a domain or IP address.")
            return

        for w in self._results_frame.winfo_children():
            w.destroy()

        self._scanning = True
        self._scan_btn.configure(state="disabled", text="Scanning…")
        self._status_var.set(
            f"Scanning {target} — may take up to 30 seconds…")
        threading.Thread(
            target=self._run_scan, args=(target,), daemon=True).start()

    def _run_scan(self, target: str):
        from src.security.assessment.assessor import InfrastructureAssessor
        assessor = InfrastructureAssessor(target)
        try:
            data = assessor.run_checks()
        except Exception as exc:
            self.after(0, self._show_error, str(exc))
            return
        self.after(0, self._show_results, target, data)

    # --------------------------------------------------------------- display
    def _show_error(self, msg: str):
        self._scanning = False
        self._scan_btn.configure(state="normal", text="Scan")
        self._status_var.set(f"Scan failed: {msg}")

    def _show_results(self, target: str, data: dict):
        self._scanning = False
        self._scan_btn.configure(state="normal", text="Scan Again")
        self._status_var.set(f"Scan complete: {target}")
        self._last_result = data
        self._last_target = target
        self._export_btn.configure(state="normal")

        f = self._results_frame
        row = [0]

        def nrow():
            r = row[0]
            row[0] += 1
            return r

        # ── Grade verdict hero ────────────────────────────────────────
        grade = data.get("grade", "NEEDS ATTENTION")
        score = data.get("score", 0)
        icon, clr, title, msg = GRADE_STYLE.get(
            grade, GRADE_STYLE["NEEDS ATTENTION"])
        hero = ctk.CTkFrame(f, fg_color=CLR_SURFACE, corner_radius=16,
                            border_width=2, border_color=clr)
        hero.grid(row=nrow(), column=0, padx=PAD, pady=(PAD, 10), sticky="ew")
        hero.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hero, text=icon, font=("Segoe UI Emoji", 38),
                     ).grid(row=0, column=0, rowspan=2, padx=(18, 14),
                            pady=14)
        ctk.CTkLabel(hero, text=title, font=("Segoe UI", 17, "bold"),
                     text_color=clr, anchor="w",
                     ).grid(row=0, column=1, sticky="w", pady=(14, 0))
        ctk.CTkLabel(hero, text=msg, font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     wraplength=560, justify="left", anchor="w",
                     ).grid(row=1, column=1, sticky="w", pady=(0, 14))
        ctk.CTkLabel(hero, text=f"{score}%\nsecure",
                     font=("Segoe UI", 14, "bold"), text_color=clr,
                     justify="center",
                     ).grid(row=0, column=2, rowspan=2, padx=(10, 18))

        # ── Prioritised findings ──────────────────────────────────────
        findings = sorted(
            data.get("findings", []),
            key=lambda x: SEV_ORDER.get(x.get("severity", "LOW"), 5))
        if findings:
            self._section(f, nrow(), f"Findings ({len(findings)})")
            for fd in findings:
                self._finding_card(f, nrow(), fd)
        else:
            self._section(f, nrow(), "Findings")
            self._kv_card(f, nrow(),
                          [("Result", "No issues found — well configured",
                            CLR_SUCCESS)])

        # ── DNS ───────────────────────────────────────────────────────
        self._section(f, nrow(), "DNS Resolution & Security")
        dns_sec = data.get("dns_security", {})
        spf = dns_sec.get("spf", "—")
        dmarc = dns_sec.get("dmarc", "—")
        caa = dns_sec.get("caa", "—")
        dns_items = [
            ("Resolution",   data.get("dns_resolution", "—"), None),
            ("Target IP",    data.get("target_ip", "—"), CLR_MUTED),
            ("Reverse DNS",  data.get("reverse_dns", "—"), CLR_MUTED),
            ("SPF Record",   spf,
             CLR_SUCCESS if "found" in spf.lower() else CLR_WARNING),
            ("DMARC Record", dmarc,
             CLR_SUCCESS if "found" in dmarc.lower() else CLR_WARNING),
            ("CAA Record",   caa,
             CLR_SUCCESS if "found" in caa.lower() else CLR_WARNING),
        ]
        if dns_sec.get("notes"):
            dns_items.append(("Notes", dns_sec["notes"], CLR_MUTED))
        self._kv_card(f, nrow(), dns_items)

        # ── SSL / TLS ─────────────────────────────────────────────────
        self._section(f, nrow(), "SSL / TLS")
        ssl_val  = data.get("ssl_certificate", "—")
        tls_val  = data.get("tls_version", "—")
        redir    = data.get("https_redirect", "—")
        cert     = data.get("certificate", {}) or {}
        ssl_clr  = (CLR_SUCCESS
                    if "enabled" in ssl_val.lower() and "SOON" not in ssl_val
                    else CLR_WARNING if "SOON" in ssl_val
                    else CLR_DANGER)
        tls_clr  = CLR_SUCCESS if "Good" in tls_val else CLR_WARNING
        redir_clr = (CLR_SUCCESS if "redirects to HTTPS" in redir
                     else CLR_WARNING)
        tls_items = [
            ("Certificate",    ssl_val,  ssl_clr),
            ("TLS Version",    tls_val,  tls_clr),
            ("HTTPS Redirect", redir,    redir_clr),
        ]
        if cert.get("issuer"):
            tls_items.insert(1, ("Issued By", cert["issuer"], CLR_MUTED))
        self._kv_card(f, nrow(), tls_items)

        # ── Security Headers ──────────────────────────────────────────
        self._section(f, nrow(), "HTTP Security Headers")
        headers = data.get("security_headers", {})
        self._kv_card(f, nrow(), [
            (hname, hval,
             CLR_SUCCESS if str(hval).startswith("PRESENT") else CLR_DANGER)
            for hname, hval in headers.items()
        ])

        # ── Port Exposure ─────────────────────────────────────────────
        self._section(f, nrow(), "Port Exposure")
        open_ports = data.get("open_ports", [])
        services   = data.get("services", {})
        risky      = data.get("risky_ports", [])
        port_labels = ", ".join(
            f"{p} ({services.get(p, services.get(str(p), '?'))})"
            for p in open_ports) if open_ports else "None detected"
        port_items = [
            ("Open Ports", port_labels, CLR_MUTED),
        ]
        for rp in risky:
            # strip the "[SEVERITY]" tag for display
            port_items.append(("Risky Port", rp.rsplit(" [", 1)[0], CLR_DANGER))
        if not risky:
            port_items.append(
                ("Risky Ports", "None detected — good", CLR_SUCCESS))
        self._kv_card(f, nrow(), port_items)

        # Reveal the assembled report as a gentle top-down cascade.
        self.after(20, lambda: motion.stagger_grid(
            list(f.winfo_children()), interval_ms=18))

    def _finding_card(self, parent, row: int, fd: dict):
        sev = fd.get("severity", "LOW")
        clr = SEV_CLR.get(sev, CLR_MUTED)
        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=12,
                            border_width=1, border_color=CLR_BORDER)
        card.grid(row=row, column=0, padx=PAD, pady=3, sticky="ew")
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkFrame(card, fg_color=clr, width=4, corner_radius=0,
                     ).grid(row=0, column=0, rowspan=3, sticky="ns")
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=1, sticky="ew", padx=(10, 12), pady=(10, 2))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text=fd.get("title", ""), font=FONT_SUBHEAD,
                     text_color=CLR_TEXT, anchor="w",
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(top, text=sev, font=("Segoe UI", 10, "bold"),
                     text_color=clr, fg_color=CLR_SURFACE_ALT,
                     corner_radius=6, width=70, height=20,
                     ).grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(card, text=fd.get("detail", ""), font=FONT_SMALL,
                     text_color=CLR_TEXT_SEC, anchor="w", wraplength=680,
                     justify="left",
                     ).grid(row=1, column=1, sticky="w", padx=(10, 12),
                            pady=(0, 4))
        if fd.get("remediation"):
            rem = ctk.CTkFrame(card, fg_color=CLR_SURFACE_ALT, corner_radius=8)
            rem.grid(row=2, column=1, sticky="ew", padx=(10, 12), pady=(0, 10))
            rem.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(rem, text="Fix:", font=("Segoe UI", 10, "bold"),
                         text_color=CLR_ACCENT, width=28,
                         ).grid(row=0, column=0, padx=(10, 4), pady=6)
            ctk.CTkLabel(rem, text=fd["remediation"], font=FONT_CAPTION,
                         text_color=CLR_TEXT_SEC, anchor="w", wraplength=620,
                         justify="left",
                         ).grid(row=0, column=1, padx=(0, 10), pady=6,
                                sticky="w")

    # ------------------------------------------------------------ helpers
    def _section(self, parent, row: int, title: str):
        ctk.CTkLabel(
            parent, text=title,
            font=FONT_SUBHEAD, text_color=CLR_TEXT,
        ).grid(row=row, column=0, padx=PAD, pady=(14, 4), sticky="w")

    def _kv_card(self, parent, row: int, items: list):
        if not items:
            return
        card = ctk.CTkFrame(
            parent, fg_color=CLR_SURFACE, corner_radius=12,
            border_width=1, border_color=CLR_BORDER)
        card.grid(row=row, column=0, padx=PAD, pady=(0, 4), sticky="ew")
        card.grid_columnconfigure(1, weight=1)
        n = len(items)
        for i, (key, val, clr) in enumerate(items):
            pt = 12 if i == 0 else 4
            pb = 12 if i == n - 1 else 4
            ctk.CTkLabel(
                card, text=f"{key}:",
                font=("Segoe UI", 11, "bold"),
                text_color=CLR_MUTED, width=170, anchor="w",
            ).grid(row=i, column=0,
                   padx=(14, 8), pady=(pt, pb), sticky="w")
            ctk.CTkLabel(
                card, text=str(val),
                font=FONT_SMALL, text_color=clr or CLR_TEXT,
                anchor="w", wraplength=620, justify="left",
            ).grid(row=i, column=1,
                   padx=(0, 14), pady=(pt, pb), sticky="w")

    # ------------------------------------------------------------- export
    def _export_html(self):
        data = self._last_result
        if not data:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Report", "*.html"), ("All files", "*.*")],
            initialfile=(f"infra_scan_{self._last_target}_"
                         f"{datetime.date.today().isoformat()}.html"),
        )
        if not path:
            return

        grade = data.get("grade", "NEEDS ATTENTION")
        score = data.get("score", 0)
        icon, clr, title, msg = GRADE_STYLE.get(
            grade, GRADE_STYLE["NEEDS ATTENTION"])
        clr_hex = {CLR_SUCCESS: "#4CAF50", CLR_WARNING: "#F0A500",
                   CLR_DANGER: "#E84040"}.get(clr, "#6C5FC7")

        findings = sorted(
            data.get("findings", []),
            key=lambda x: SEV_ORDER.get(x.get("severity", "LOW"), 5))
        sev_hex = {"CRITICAL": "#E84040", "HIGH": "#E87000",
                   "MEDIUM": "#F0A500", "LOW": "#A0B4C8", "INFO": "#A0B4C8"}
        find_rows = "".join(
            f"<tr><td style='color:{sev_hex.get(fd['severity'], '#A0B4C8')};"
            f"font-weight:bold'>{fd['severity']}</td>"
            f"<td>{fd['title']}</td><td style='font-size:11px'>{fd['detail']}</td>"
            f"<td style='font-size:11px;color:#F0A500'>"
            f"{fd.get('remediation', '') or '—'}</td></tr>"
            for fd in findings) or (
            "<tr><td colspan='4' style='color:#4CAF50'>"
            "No issues found — well configured.</td></tr>")

        def esc(v):
            return str(v).replace("<", "&lt;").replace(">", "&gt;")

        raw_rows = ""
        for label, key in [
            ("DNS Resolution", "dns_resolution"), ("Target IP", "target_ip"),
            ("Reverse DNS", "reverse_dns"), ("SSL Certificate", "ssl_certificate"),
            ("TLS Version", "tls_version"), ("HTTPS Redirect", "https_redirect"),
        ]:
            raw_rows += (f"<tr><td>{label}</td><td>"
                         f"{esc(data.get(key, '—'))}</td></tr>")
        open_ports = data.get("open_ports", [])
        services = data.get("services", {})
        raw_rows += ("<tr><td>Open Ports</td><td>" + (", ".join(
            f"{p} ({services.get(p, services.get(str(p), '?'))})"
            for p in open_ports) or "None") + "</td></tr>")

        html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>Infrastructure Scan — {esc(self._last_target)}</title><style>
 body{{font-family:'Segoe UI',sans-serif;background:#0B1622;color:#ECF4FF;
  margin:0;padding:32px}}
 h1{{color:{clr_hex}}} h2{{color:#2485E8;border-bottom:1px solid #1A2D42;
  padding-bottom:6px;margin-top:28px}}
 .badge{{background:#132236;border-radius:16px;padding:24px;
  border:2px solid {clr_hex};display:flex;align-items:center;gap:20px}}
 .big{{font-size:42px}} .verdict{{font-size:22px;font-weight:bold;color:{clr_hex}}}
 .msg{{font-size:12px;color:#A0B4C8;margin-top:6px;max-width:600px}}
 .score{{font-size:32px;font-weight:bold;color:{clr_hex};margin-left:auto}}
 table{{width:100%;border-collapse:collapse;background:#132236;
  border-radius:10px;overflow:hidden;margin-top:8px}}
 th{{background:#1A2D42;padding:10px 14px;text-align:left;font-size:11px;
  color:#5A7490;text-transform:uppercase}}
 td{{padding:8px 14px;border-bottom:1px solid #0B1622;font-size:12px}}
 footer{{margin-top:40px;color:#5A7490;font-size:10px;text-align:center}}
</style></head><body>
<h1>🌐 Infrastructure Scan Report</h1>
<div class="badge"><div class="big">{icon}</div><div>
 <div class="verdict">{title}</div><div class="msg">{msg}</div>
 <div style="margin-top:8px;font-size:11px;color:#5A7490">
  Target: {esc(self._last_target)} &nbsp;·&nbsp;
  Scanned: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</div><div class="score">{score}%</div></div>
<h2>Findings</h2>
<table><thead><tr><th>Severity</th><th>Issue</th><th>Detail</th>
 <th>Remediation</th></tr></thead><tbody>{find_rows}</tbody></table>
<h2>Scan Details</h2>
<table><tbody>{raw_rows}</tbody></table>
<footer>Zambia Digital Hygiene Certification Programme · Infrastructure Scanner
 · University of Zambia</footer></body></html>"""

        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        try:
            import os
            os.startfile(path)  # type: ignore
        except AttributeError:
            import subprocess as sp
            sp.Popen(["xdg-open", path])
        self._status_var.set(f"Report saved: {path}")


class ScanProgressTracker(ctk.CTkFrame):
    """Real-time scan progress tracker with detailed metrics."""

    def __init__(self, parent, total_targets):
        super().__init__(parent, fg_color=CLR_SURFACE, corner_radius=8)
        self.total = total_targets
        self.vulnerabilities = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        ctk.CTkLabel(self, text="Scan Progress",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=12, pady=(12, 4))
        self.progress_bar = ctk.CTkProgressBar(self, fg_color=CLR_SURFACE_ALT,
                                               progress_color=CLR_SUCCESS,
                                               height=8, corner_radius=2)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=12, pady=(0, 4))
        self.status_label = ctk.CTkLabel(
            self, text=f"0 of {total_targets} scanned",
            font=FONT_SMALL, text_color=CLR_TEXT_SEC)
        self.status_label.pack(anchor="w", padx=12, pady=(0, 12))

        vuln_frame = ctk.CTkFrame(self, fg_color="transparent")
        vuln_frame.pack(fill="x", padx=12, pady=(0, 12))
        for level, color in [("critical", CLR_DANGER), ("high", CLR_WARNING),
                             ("medium", "#FF9800"), ("low", "#2196F3")]:
            badge = ctk.CTkFrame(vuln_frame, fg_color=color,
                                 corner_radius=4, width=50, height=28)
            badge.pack(side="left", padx=4)
            badge.pack_propagate(False)
            label = ctk.CTkLabel(badge, text=f"{level.capitalize()}: 0",
                                 font=FONT_SMALL, text_color="#ffffff")
            label.pack(expand=True)
            setattr(self, f"badge_{level}", label)

    def update_progress(self, scanned):
        progress = scanned / self.total if self.total > 0 else 0
        self.progress_bar.set(progress)
        self.status_label.configure(
            text=f"{scanned} of {self.total} targets scanned ({int(progress * 100)}%)")

    def update_vulnerabilities(self, level, count):
        self.vulnerabilities[level] = count
        if hasattr(self, f"badge_{level}"):
            getattr(self, f"badge_{level}").configure(
                text=f"{level.capitalize()}: {count}")


class VulnerabilityDetailDialog(ctk.CTkToplevel):
    """Detailed view of a specific vulnerability."""

    def __init__(self, parent, vuln_data):
        super().__init__(parent)
        self.title(f"Vulnerability: {vuln_data.get('name', 'Unknown')}")
        self.geometry("700x600")
        self.configure(fg_color=CLR_BG)

        severity = vuln_data.get("severity", "UNKNOWN").upper()
        severity_color = {"CRITICAL": CLR_DANGER, "HIGH": CLR_WARNING,
                          "MEDIUM": "#FF9800", "LOW": "#2196F3"}.get(severity, CLR_MUTED)

        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        title_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        title_frame.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(title_frame, text=vuln_data.get("name", "Unknown"),
                     font=("Segoe UI", 14, "bold"), text_color=CLR_TEXT,
                     ).pack(anchor="w", side="left")
        ctk.CTkLabel(title_frame, text=severity,
                     font=FONT_SMALL, text_color=severity_color,
                     ).pack(anchor="e", side="right")

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)
        for section_title, content in [
            ("Description",   vuln_data.get("description", "")),
            ("Affected Target", vuln_data.get("target", "")),
            ("CVSS Score",    vuln_data.get("cvss_score", "N/A")),
            ("Remediation",   vuln_data.get("remediation", "")),
        ]:
            frame = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE_ALT, corner_radius=8)
            frame.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(frame, text=section_title,
                         font=FONT_SUBHEAD, text_color=CLR_TEXT,
                         ).pack(anchor="w", padx=12, pady=(12, 4))
            ctk.CTkLabel(frame, text=content, font=FONT_BODY,
                         text_color=CLR_TEXT_SEC, wraplength=600, justify="left",
                         ).pack(anchor="w", padx=12, pady=(0, 12))

        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=50)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        ctk.CTkButton(footer, text="Close", command=self.destroy,
                      fg_color=CLR_SURFACE_ALT, text_color=CLR_TEXT,
                      font=FONT_BODY, height=BTN_H, corner_radius=BTN_R,
                      ).pack(side="left", padx=16, pady=12)


class PortFilterPanel(ctk.CTkFrame):
    """Filter ports and services in network scan."""

    def __init__(self, parent, on_filter_change=None):
        super().__init__(parent, fg_color=CLR_SURFACE, corner_radius=8)
        self.on_filter_change = on_filter_change or (lambda: None)

        ctk.CTkLabel(self, text="🔌 Filter Ports & Services",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=12, pady=(12, 8))

        port_frame = ctk.CTkFrame(self, fg_color="transparent")
        port_frame.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkLabel(port_frame, text="Port Range:",
                     font=FONT_BODY, text_color=CLR_TEXT).pack(side="left")
        self.port_start = ctk.CTkEntry(port_frame, placeholder_text="Start",
                                       fg_color=CLR_SURFACE_ALT, text_color=CLR_TEXT,
                                       font=FONT_SMALL, width=60, height=28)
        self.port_start.pack(side="left", padx=4)
        ctk.CTkLabel(port_frame, text="to",
                     font=FONT_BODY, text_color=CLR_TEXT).pack(side="left")
        self.port_end = ctk.CTkEntry(port_frame, placeholder_text="End",
                                     fg_color=CLR_SURFACE_ALT, text_color=CLR_TEXT,
                                     font=FONT_SMALL, width=60, height=28)
        self.port_end.pack(side="left", padx=4)

        svc_frame = ctk.CTkFrame(self, fg_color="transparent")
        svc_frame.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkLabel(svc_frame, text="Services:",
                     font=FONT_BODY, text_color=CLR_TEXT,
                     ).pack(side="left", padx=(0, 8))
        for service in ["HTTP", "HTTPS", "SSH", "Database", "Other"]:
            ctk.CTkCheckBox(svc_frame, text=service,
                            text_color=CLR_TEXT, fg_color=CLR_SUCCESS,
                            font=FONT_SMALL).pack(side="left", padx=4)
