"""Infrastructure Scanner screen — exposes InfrastructureAssessor in the GUI."""

import threading
import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_ACCENT, CLR_TEXT, CLR_MUTED,
    CLR_BORDER, CLR_SUCCESS, CLR_WARNING, CLR_DANGER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, PAD,
)


class InfraScannerScreen(ctk.CTkFrame):
    """Scan a domain or IP for web-facing security issues."""

    def __init__(self, master, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back
        self._scanning = False
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=84)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="Infrastructure Scanner",
            font=FONT_HEADING, text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=PAD, pady=(16, 4), sticky="w")
        ctk.CTkLabel(
            hdr,
            text="Scan a domain or IP for SSL, open ports, security headers and DNS records",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(row=1, column=0, padx=PAD, pady=(0, 14), sticky="w")

        # Scrollable body
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        # Input card
        input_card = ctk.CTkFrame(self._scroll, fg_color=CLR_SURFACE,
                                  corner_radius=18, border_width=1, border_color=CLR_BORDER)
        input_card.grid(row=0, column=0, padx=PAD, pady=(PAD, 12), sticky="ew")
        input_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            input_card, text="Enter target domain or IP address:",
            font=FONT_BODY, text_color=CLR_TEXT, anchor="w",
        ).grid(row=0, column=0, padx=18, pady=(16, 6), sticky="w")

        row_in = ctk.CTkFrame(input_card, fg_color="transparent")
        row_in.grid(row=1, column=0, padx=18, pady=(0, 16), sticky="ew")
        row_in.grid_columnconfigure(0, weight=1)

        self._target_entry = ctk.CTkEntry(
            row_in,
            placeholder_text="e.g. example.com  or  192.168.1.1",
            font=FONT_BODY, text_color=CLR_TEXT,
            fg_color=CLR_SURFACE_ALT, border_color=CLR_BORDER, border_width=1,
            height=40, corner_radius=10,
        )
        self._target_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._target_entry.bind("<Return>", lambda _e: self._start_scan())

        self._scan_btn = ctk.CTkButton(
            row_in, text="🔍  Scan", width=110, height=40,
            font=("Segoe UI", 13, "bold"),
            fg_color=CLR_ACCENT, hover_color="#00A87A",
            text_color="#000000", corner_radius=10,
            command=self._start_scan,
        )
        self._scan_btn.grid(row=0, column=1)

        # Status / spinner label
        self._status_var = ctk.StringVar(value="")
        self._status_lbl = ctk.CTkLabel(
            self._scroll, textvariable=self._status_var,
            font=FONT_SMALL, text_color=CLR_MUTED,
        )
        self._status_lbl.grid(row=1, column=0, padx=PAD, pady=(0, 6), sticky="w")

        # Results container (rebuilt each scan)
        self._results_frame = ctk.CTkFrame(self._scroll, fg_color="transparent", corner_radius=0)
        self._results_frame.grid(row=2, column=0, sticky="ew")
        self._results_frame.grid_columnconfigure(0, weight=1)

    # --------------------------------------------------------------- scanning
    def _start_scan(self):
        if self._scanning:
            return
        target = self._target_entry.get().strip()
        if not target:
            self._status_var.set("⚠  Please enter a domain or IP address.")
            return

        # Clear previous results
        for w in self._results_frame.winfo_children():
            w.destroy()

        self._scanning = True
        self._scan_btn.configure(state="disabled", text="Scanning…")
        self._status_var.set(f"Scanning {target} — this may take up to 30 seconds…")
        threading.Thread(target=self._run_scan, args=(target,), daemon=True).start()

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
        self._scan_btn.configure(state="normal", text="🔍  Scan")
        self._status_var.set(f"❌  Scan failed: {msg}")

    def _show_results(self, target: str, data: dict):
        self._scanning = False
        self._scan_btn.configure(state="normal", text="🔍  Scan Again")
        self._status_var.set(f"✔  Scan complete for: {target}")

        f = self._results_frame

        # ── DNS ──────────────────────────────────────────────────────
        self._section(f, 0, "🌐  DNS Resolution & Security")
        dns_items = [
            ("Resolution", data.get("dns_resolution", "—"), None),
        ]
        dns_sec = data.get("dns_security", {})
        spf = dns_sec.get("spf", "—")
        dmarc = dns_sec.get("dmarc", "—")
        dns_items += [
            ("SPF Record",   spf,   CLR_SUCCESS if "found" in spf.lower() else CLR_WARNING),
            ("DMARC Record", dmarc, CLR_SUCCESS if "found" in dmarc.lower() else CLR_WARNING),
        ]
        if dns_sec.get("notes"):
            dns_items.append(("Notes", dns_sec["notes"], CLR_MUTED))
        self._kv_card(f, 1, dns_items)

        # ── SSL / TLS ────────────────────────────────────────────────
        self._section(f, 2, "🔒  SSL / TLS")
        ssl_val = data.get("ssl_certificate", "—")
        tls_val = data.get("tls_version", "—")
        redir_val = data.get("https_redirect", "—")
        ssl_clr = (CLR_SUCCESS if "enabled" in ssl_val.lower() and "SOON" not in ssl_val
                   else CLR_WARNING if "SOON" in ssl_val else CLR_DANGER)
        tls_clr = CLR_SUCCESS if "Good" in tls_val else CLR_WARNING
        redir_clr = CLR_SUCCESS if "redirects to HTTPS" in redir_val else CLR_WARNING
        self._kv_card(f, 3, [
            ("Certificate",     ssl_val,  ssl_clr),
            ("TLS Version",     tls_val,  tls_clr),
            ("HTTPS Redirect",  redir_val, redir_clr),
        ])

        # ── Security Headers ─────────────────────────────────────────
        self._section(f, 4, "🛡  HTTP Security Headers")
        headers = data.get("security_headers", {})
        header_items = []
        for hname, hval in headers.items():
            clr = CLR_SUCCESS if hval.startswith("PRESENT") else CLR_DANGER
            header_items.append((hname, hval, clr))
        self._kv_card(f, 5, header_items)

        # ── Port Exposure ────────────────────────────────────────────
        self._section(f, 6, "🔌  Port Exposure")
        open_ports = data.get("open_ports", [])
        risky = data.get("risky_ports", [])
        ext_ip = data.get("external_ip", "—")
        port_items = [
            ("External IP", ext_ip, CLR_MUTED),
            ("Open Ports",
             ", ".join(str(p) for p in open_ports) if open_ports else "None detected",
             CLR_MUTED),
        ]
        for rp in risky:
            port_items.append(("⚠ Risky Port", rp, CLR_DANGER))
        if not risky:
            port_items.append(("Risky Ports", "None detected — good", CLR_SUCCESS))
        self._kv_card(f, 7, port_items)

        # ── Remediation tips for issues found ────────────────────────
        tips = []
        if "MISSING" in str(headers.get("Strict-Transport-Security", "")):
            tips.append("Add HSTS header: Strict-Transport-Security: max-age=31536000; includeSubDomains")
        if "MISSING" in str(headers.get("X-Frame-Options", "")):
            tips.append("Add X-Frame-Options: DENY  (prevents clickjacking attacks)")
        if "MISSING" in str(headers.get("Content-Security-Policy", "")):
            tips.append("Define a Content-Security-Policy header to block XSS injection")
        if "No SPF" in spf:
            tips.append("Add an SPF TXT record to your DNS to prevent email spoofing")
        if "No DMARC" in dmarc:
            tips.append("Add a _dmarc TXT record to reduce phishing risk from your domain")
        if risky:
            tips.append("Close or firewall risky ports — especially RDP (3389) and FTP (21)")
        if "EXPIRED" in ssl_val:
            tips.append("Renew your SSL certificate immediately — it has expired")

        if tips:
            self._section(f, 8, "💡  Remediation Tips")
            tip_card = ctk.CTkFrame(f, fg_color=CLR_SURFACE, corner_radius=14,
                                    border_width=1, border_color=CLR_BORDER)
            tip_card.grid(row=9, column=0, padx=PAD, pady=(0, 12), sticky="ew")
            tip_card.grid_columnconfigure(0, weight=1)
            for i, tip in enumerate(tips):
                row_f = ctk.CTkFrame(tip_card, fg_color="transparent")
                row_f.grid(row=i, column=0, padx=14, pady=(8 if i == 0 else 2, 0), sticky="ew")
                row_f.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(row_f, text="→", font=FONT_BODY,
                             text_color=CLR_ACCENT, width=20).grid(row=0, column=0, padx=(0, 8))
                ctk.CTkLabel(row_f, text=tip, font=FONT_SMALL, text_color=CLR_TEXT,
                             wraplength=760, justify="left", anchor="w",
                             ).grid(row=0, column=1, sticky="w",
                                    pady=(0, 8 if i == len(tips) - 1 else 0))

    # ------------------------------------------------------------ helpers
    def _section(self, parent, row: int, title: str):
        ctk.CTkLabel(
            parent, text=title, font=FONT_HEADING, text_color=CLR_TEXT,
        ).grid(row=row, column=0, padx=PAD, pady=(16, 4), sticky="w")

    def _kv_card(self, parent, row: int, items: list):
        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=14,
                            border_width=1, border_color=CLR_BORDER)
        card.grid(row=row, column=0, padx=PAD, pady=(0, 4), sticky="ew")
        card.grid_columnconfigure(1, weight=1)
        for i, (key, val, clr) in enumerate(items):
            pad_top = 14 if i == 0 else 4
            pad_bot = 14 if i == len(items) - 1 else 4
            ctk.CTkLabel(
                card, text=key + ":", font=("Segoe UI", 11, "bold"),
                text_color=CLR_MUTED, width=160, anchor="w",
            ).grid(row=i, column=0, padx=(16, 8), pady=(pad_top, pad_bot), sticky="w")
            ctk.CTkLabel(
                card, text=str(val), font=FONT_SMALL,
                text_color=clr or CLR_TEXT, anchor="w",
                wraplength=620, justify="left",
            ).grid(row=i, column=1, padx=(0, 16), pady=(pad_top, pad_bot), sticky="w")

    # ------------------------------------------------------------------ nav
    def _back(self):
        self._on_back()
