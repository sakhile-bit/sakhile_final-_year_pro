"""Infrastructure Scanner — scan any domain or IP for web-facing security."""

import threading
import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_BORDER, CLR_SUCCESS, CLR_WARNING, CLR_DANGER,
    FONT_BODY, FONT_SMALL, FONT_SUBHEAD, FONT_CAPTION,
    PAD, NAV_H, BTN_H, BTN_R,
)
from src.gui.screens.business_info import _header


class InfraScannerScreen(ctk.CTkFrame):
    """Scan a domain or IP for SSL, open ports, security headers and DNS."""

    def __init__(self, master, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back
        self._scanning = False
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
            text_color="#000000",
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
        nav.grid_propagate(False)
        ctk.CTkButton(
            nav, text="<- Back to Home",
            font=FONT_BODY,
            fg_color="transparent", border_color=CLR_BORDER, border_width=1,
            text_color=CLR_TEXT_SEC, hover_color=CLR_SURFACE_ALT,
            width=150, height=BTN_H, corner_radius=BTN_R,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

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

        f = self._results_frame

        # DNS
        self._section(f, 0, "DNS Resolution & Security")
        dns_sec = data.get("dns_security", {})
        spf = dns_sec.get("spf", "—")
        dmarc = dns_sec.get("dmarc", "—")
        dns_items = [
            ("Resolution",   data.get("dns_resolution", "—"), None),
            ("SPF Record",   spf,
             CLR_SUCCESS if "found" in spf.lower() else CLR_WARNING),
            ("DMARC Record", dmarc,
             CLR_SUCCESS if "found" in dmarc.lower() else CLR_WARNING),
        ]
        if dns_sec.get("notes"):
            dns_items.append(("Notes", dns_sec["notes"], CLR_MUTED))
        self._kv_card(f, 1, dns_items)

        # SSL / TLS
        self._section(f, 2, "SSL / TLS")
        ssl_val  = data.get("ssl_certificate", "—")
        tls_val  = data.get("tls_version", "—")
        redir    = data.get("https_redirect", "—")
        ssl_clr  = (CLR_SUCCESS
                    if "enabled" in ssl_val.lower() and "SOON" not in ssl_val
                    else CLR_WARNING if "SOON" in ssl_val
                    else CLR_DANGER)
        tls_clr  = CLR_SUCCESS if "Good" in tls_val else CLR_WARNING
        redir_clr = (CLR_SUCCESS if "redirects to HTTPS" in redir
                     else CLR_WARNING)
        self._kv_card(f, 3, [
            ("Certificate",    ssl_val,  ssl_clr),
            ("TLS Version",    tls_val,  tls_clr),
            ("HTTPS Redirect", redir,    redir_clr),
        ])

        # Security Headers
        self._section(f, 4, "HTTP Security Headers")
        headers = data.get("security_headers", {})
        self._kv_card(f, 5, [
            (hname, hval,
             CLR_SUCCESS if hval.startswith("PRESENT") else CLR_DANGER)
            for hname, hval in headers.items()
        ])

        # Port Exposure
        self._section(f, 6, "Port Exposure")
        open_ports = data.get("open_ports", [])
        risky      = data.get("risky_ports", [])
        ext_ip     = data.get("external_ip", "—")
        port_items = [
            ("External IP", ext_ip, CLR_MUTED),
            ("Open Ports",
             ", ".join(str(p) for p in open_ports) if open_ports
             else "None detected",
             CLR_MUTED),
        ]
        for rp in risky:
            port_items.append(("Risky Port", rp, CLR_DANGER))
        if not risky:
            port_items.append(
                ("Risky Ports", "None detected — good", CLR_SUCCESS))
        self._kv_card(f, 7, port_items)

        # Remediation tips
        tips = []
        hsts = str(headers.get("Strict-Transport-Security", ""))
        xfo  = str(headers.get("X-Frame-Options", ""))
        csp  = str(headers.get("Content-Security-Policy", ""))
        if "MISSING" in hsts:
            tips.append(
                "Add HSTS header: Strict-Transport-Security: "
                "max-age=31536000; includeSubDomains")
        if "MISSING" in xfo:
            tips.append(
                "Add X-Frame-Options: DENY (prevents clickjacking)")
        if "MISSING" in csp:
            tips.append(
                "Define a Content-Security-Policy to block XSS injection")
        if "No SPF" in spf:
            tips.append(
                "Add an SPF TXT record to prevent email spoofing")
        if "No DMARC" in dmarc:
            tips.append(
                "Add a _dmarc TXT record to reduce phishing risk")
        if risky:
            tips.append(
                "Firewall risky ports — especially RDP (3389) and FTP (21)")
        if "EXPIRED" in ssl_val:
            tips.append("Renew your SSL certificate — it has expired")

        if tips:
            self._section(f, 8, "Remediation Tips")
            tip_card = ctk.CTkFrame(
                f, fg_color=CLR_SURFACE, corner_radius=12,
                border_width=1, border_color=CLR_BORDER)
            tip_card.grid(row=9, column=0, padx=PAD,
                          pady=(0, 12), sticky="ew")
            tip_card.grid_columnconfigure(1, weight=1)
            for i, tip in enumerate(tips):
                ctk.CTkLabel(
                    tip_card, text="→", font=FONT_BODY,
                    text_color=CLR_ACCENT, width=20,
                ).grid(row=i, column=0,
                       padx=(14, 6), pady=(10 if i == 0 else 2, 0))
                ctk.CTkLabel(
                    tip_card, text=tip,
                    font=FONT_SMALL, text_color=CLR_TEXT,
                    wraplength=760, justify="left", anchor="w",
                ).grid(row=i, column=1, sticky="w",
                       padx=(0, 14),
                       pady=(10 if i == 0 else 2,
                             10 if i == len(tips) - 1 else 0))

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
