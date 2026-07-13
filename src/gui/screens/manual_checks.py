"""Manual assessment — C06-C15 questions with numbered cards and live scoring."""

from tkinter import filedialog
import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_ACCENT_HOV,
    CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER,
    FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, NAV_H, BTN_H, BTN_R,
)
from src.gui.screens.business_info import _header

MANUAL_CONTROLS = [
    ("C06_security_training", "C06", "Security Awareness Training",
     "Do ALL staff receive at least annual cybersecurity awareness training "
     "and phishing simulations?",
     "Have your employees been trained to spot fake emails, create strong passwords "
     "and handle customer data safely in the past 12 months?"),

    ("C07_access_control", "C07", "Access Control Policy",
     "Is there a documented least-privilege access control policy, "
     "reviewed at least annually?",
     "Do you control who can see and edit what on your computers, and remove "
     "access the same day a staff member leaves?"),

    ("C08_incident_response", "C08", "Incident Response Plan",
     "Do you have a tested incident response plan that includes ZICTA/CERT-ZM contacts?",
     "If hacked today, do you have a written step-by-step plan? "
     "ZICTA: +260 211 369 000 | cert@zicta.zm"),

    ("C09_encryption", "C09", "Data Encryption",
     "Is sensitive data encrypted at rest (BitLocker) and in transit (HTTPS)?",
     "Does your website start with https:// and are laptops "
     "protected if lost or stolen?"),

    ("C10_mobile_security", "C10", "Mobile Device Security",
     "Are all business mobile devices protected with screen locks, "
     "encryption and MDM policy?",
     "Do all company phones auto-lock and only allow "
     "apps from official app stores?"),

    ("C11_physical_security", "C11", "Physical Security",
     "Is the server/IT area access-controlled with visitor logs and CCTV?",
     "Is your router or server in a locked room? "
     "Can you tell who has been in that area?"),

    ("C12_network_security", "C12", "Network Security",
     "Does the business use WPA2/WPA3 Wi-Fi with a separate guest network?",
     "Is your Wi-Fi password strong? Do visitors connect to a "
     "different Wi-Fi from your staff?"),

    ("C13_acceptable_use", "C13", "Acceptable Use Policy",
     "Is there a documented acceptable use policy signed by all staff?",
     "Do employees have written rules about company computers and internet "
     "use, and have they signed to confirm?"),

    ("C14_vendor_risk", "C14", "Vendor / Third-Party Risk",
     "Do vendor contracts include security clauses with formal risk assessments?",
     "Do your IT suppliers and cloud providers have security "
     "obligations written into their contracts?"),

    ("C15_regulatory_compliance", "C15", "Regulatory Compliance",
     "Is the business compliant with Zambia's Data Protection Act "
     "and ZICTA regulations?",
     "Are you following the Data Protection Act 2021 and "
     "Cyber Security and Cyber Crimes Act 2021?"),
]

ANSWER_SCORE = {"Yes – Fully": 1.0, "Partially": 0.5, "No": 0.0}
_WEIGHTS = {
    "C06_security_training": 8, "C07_access_control": 7,
    "C08_incident_response": 7, "C09_encryption": 7,
    "C10_mobile_security": 5, "C11_physical_security": 5,
    "C12_network_security": 5, "C13_acceptable_use": 5,
    "C14_vendor_risk": 8, "C15_regulatory_compliance": 8,
}
_MAX = sum(_WEIGHTS.values())

# ── Tool-specific questions (shown only when the business selects the tool) ──
TOOL_QUESTIONS: dict[str, list[tuple]] = {
    "active_dir": [
        ("C16_active_directory", "C16", "Active Directory Security",
         "Are AD password policies enforced? "
         "(min 12 chars, complexity, 90-day expiry, lockout after 5 failures)",
         "Check via Group Policy > Computer Config > Windows Settings > "
         "Security Settings > Account Policies."),
        ("C16_active_directory_b", "C16b", "AD Privileged Account Review",
         "Are privileged accounts (Domain Admins, Enterprise Admins) "
         "actively monitored and reviewed at least quarterly?",
         "Use the AD 'Protected Users' group and enable audit logging. "
         "Run 'Get-ADGroupMember -Identity \"Domain Admins\"' to list members."),
        ("C16_active_directory_c", "C16c", "AD Stale Account Management",
         "Are stale or inactive AD accounts disabled and removed "
         "within 30 days of a staff member's departure?",
         "Run: Get-ADUser -Filter {Enabled -eq $True} | "
         "Where LastLogonDate -lt (Get-Date).AddDays(-90)"),
    ],
    "network_scan": [
        ("C17_network_scan", "C17", "Network Device Inventory",
         "Has a network scan been performed in the last 6 months "
         "to detect all connected devices and identify unauthorised systems?",
         "Use the built-in Network Scanner, Nmap, or a managed security service. "
         "Document all approved devices."),
        ("C17_network_scan_b", "C17b", "Network Segmentation",
         "Are network segments properly separated? "
         "(e.g. DMZ for public servers, internal LAN, isolated guest Wi-Fi)",
         "Use VLANs or separate physical networks. Guests and IoT devices "
         "must not reach internal business systems."),
        ("C17_network_scan_c", "C17c", "Port & Service Exposure",
         "Are only the ports and services required for business operations "
         "exposed on the network edge — all others blocked?",
         "Review firewall rules quarterly. Risky open ports: 23 (Telnet), "
         "21 (FTP), 3389 (RDP), 3306 (MySQL)."),
    ],
    "infra_scan": [
        ("C18_infra_scan", "C18", "SSL/TLS Certificate Validity",
         "Does your public domain have a valid, non-expired SSL/TLS certificate "
         "with at least 30 days remaining before expiry?",
         "Check at ssllabs.com/ssltest/ or use the built-in Infra Scanner. "
         "Certificates must use TLS 1.2+ (no TLS 1.0/1.1)."),
        ("C18_infra_scan_b", "C18b", "HTTP Security Headers",
         "Are HTTP security headers configured on your web presence? "
         "(HSTS, X-Frame-Options, CSP, X-Content-Type-Options, Referrer-Policy)",
         "Check at securityheaders.com. Missing headers leave your site "
         "vulnerable to XSS, clickjacking, and content injection."),
        ("C18_infra_scan_c", "C18c", "Risky Port Closure",
         "Have risky or unused ports been closed on all public-facing "
         "infrastructure? (Telnet/23, FTP/21, RDP/3389, MySQL/3306)",
         "Only ports 80 (HTTP → redirect) and 443 (HTTPS) should be "
         "publicly accessible for typical web services."),
    ],
    "zambia_risk": [
        ("C19_zambia_risk", "C19", "Zambia Threat Awareness Training",
         "Are staff trained on Zambia-specific threats? "
         "(SIM swap fraud, mobile money scams, WhatsApp phishing, local social engineering)",
         "Arrange sessions via ZICTA (zicta.zm) or CERT-ZM. "
         "Include mobile money awareness and SIM PIN activation."),
        ("C19_zambia_risk_b", "C19b", "Zambia Regulatory Compliance",
         "Is the business compliant with the Data Protection Act 2021 "
         "and the Cyber Security & Cyber Crimes Act 2021?",
         "Register data processing activities with the Data Protection Commission (DPC). "
         "Contact ZICTA for cybersecurity obligations guidance."),
        ("C19_zambia_risk_c", "C19c", "Mobile Money Account Controls",
         "Are mobile money account controls in place? "
         "(daily transaction limits, SIM PIN enabled, no shared account PINs)",
         "Set limits on Airtel Money, MTN MoMo, Zamtel Kwacha accounts. "
         "Enable SIM PIN via *100# menus or by visiting your network provider."),
    ],
    "remediation": [
        ("C20_remediation", "C20", "Findings Tracking Register",
         "Are identified security findings tracked in a register with "
         "assigned owners and target remediation dates?",
         "Use a spreadsheet, Jira, or Trello. Each finding needs: "
         "description, severity, owner, due date, and status."),
        ("C20_remediation_b", "C20b", "Remediation SLA Adherence",
         "Are critical security issues remediated within defined SLAs? "
         "(e.g. Critical: 48 h, High: 1 week, Medium: 1 month)",
         "Review your remediation register monthly. "
         "Escalate overdue critical items to senior management immediately."),
    ],
    "fleet_scan": [
        ("C21_fleet_scan", "C21", "Fleet Asset Inventory",
         "Are all machines and servers in the business enrolled in the "
         "fleet scan so every node is inventoried and reachable?",
         "Run the Fleet Scan tool with an inventory (or auto-discovery). "
         "Every production machine should appear as a reachable node."),
        ("C21_fleet_scan_b", "C21b", "Fleet-Wide Scan Cadence",
         "Is the whole fleet scanned on a regular schedule "
         "(at least monthly), not just individual machines ad-hoc?",
         "Schedule fleet scans monthly. Consistent cadence catches drift "
         "on machines that would otherwise be forgotten."),
        ("C21_fleet_scan_c", "C21c", "Weakest-Node Remediation",
         "Is the fleet's weakest-node grade acted on — the lowest-scoring "
         "machine brought up to standard rather than ignored?",
         "The fleet is only as strong as its weakest node. Prioritise the "
         "lowest-graded machine after each fleet scan."),
    ],
    "server_hardening": [
        ("C22_server_hardening", "C22", "Secure Configuration Baseline",
         "Do servers follow a documented secure-configuration baseline "
         "(CIS Benchmark or equivalent) rather than default settings?",
         "Apply a CIS Benchmark for the OS. Run the Server Hardening tool "
         "to score the current baseline and close the gaps."),
        ("C22_server_hardening_b", "C22b", "Legacy Service Disablement",
         "Are unnecessary and legacy services disabled on servers? "
         "(SMBv1, Telnet, unused roles/features, default sample apps)",
         "Disable SMBv1 and Telnet. Remove unused roles/features. "
         "Every enabled service is attack surface."),
        ("C22_server_hardening_c", "C22c", "Server Patch Currency",
         "Are servers kept patch-current with security updates applied "
         "within a defined window (e.g. critical patches within 14 days)?",
         "Enable automatic security updates or a managed patch process. "
         "Track outstanding patches per server."),
    ],
}

# Weights for tool sub-questions (map to parent control weight proportionally)
_TOOL_Q_WEIGHTS: dict[str, int] = {
    "C16_active_directory": 3, "C16_active_directory_b": 3, "C16_active_directory_c": 2,
    "C17_network_scan": 3, "C17_network_scan_b": 2, "C17_network_scan_c": 2,
    "C18_infra_scan": 3, "C18_infra_scan_b": 2, "C18_infra_scan_c": 2,
    "C19_zambia_risk": 3, "C19_zambia_risk_b": 3, "C19_zambia_risk_c": 2,
    "C20_remediation": 3, "C20_remediation_b": 3,
    "C21_fleet_scan": 3, "C21_fleet_scan_b": 2, "C21_fleet_scan_c": 2,
    "C22_server_hardening": 3, "C22_server_hardening_b": 3, "C22_server_hardening_c": 2,
}

# Parent control key for each sub-question
_TOOL_Q_PARENT: dict[str, str] = {
    "C16_active_directory": "C16_active_directory",
    "C16_active_directory_b": "C16_active_directory",
    "C16_active_directory_c": "C16_active_directory",
    "C17_network_scan": "C17_network_scan",
    "C17_network_scan_b": "C17_network_scan",
    "C17_network_scan_c": "C17_network_scan",
    "C18_infra_scan": "C18_infra_scan",
    "C18_infra_scan_b": "C18_infra_scan",
    "C18_infra_scan_c": "C18_infra_scan",
    "C19_zambia_risk": "C19_zambia_risk",
    "C19_zambia_risk_b": "C19_zambia_risk",
    "C19_zambia_risk_c": "C19_zambia_risk",
    "C20_remediation": "C20_remediation",
    "C20_remediation_b": "C20_remediation",
    "C21_fleet_scan": "C21_fleet_scan",
    "C21_fleet_scan_b": "C21_fleet_scan",
    "C21_fleet_scan_c": "C21_fleet_scan",
    "C22_server_hardening": "C22_server_hardening",
    "C22_server_hardening_b": "C22_server_hardening",
    "C22_server_hardening_c": "C22_server_hardening",
}

_ANS_STYLE = {
    "Yes – Fully": (CLR_SUCCESS, "#1A1730"),
    "Partially":   (CLR_WARNING, "#1A1400"),
    "No":          (CLR_DANGER,  "#2A0A0A"),
}


class ManualChecksScreen(ctk.CTkFrame):

    def __init__(self, master, on_next, on_back, selected_tools=None,
                 infra_target=""):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_next = on_next
        self._on_back = on_back
        self._selected_tools: set = selected_tools or set()
        self._infra_target: str = (infra_target or "").strip()
        self._answers: dict[str, ctk.StringVar] = {}
        self._notes: dict[str, ctk.CTkTextbox] = {}
        # Compute max points / question count AFTER methods are accessible
        self._max_pts = _MAX + self._tool_max()
        self._total_qs = 10 + self._tool_q_count()
        self._score_var = ctk.StringVar(
            value=f"0 / {self._max_pts} pts  (0%)")
        self._done_var = ctk.StringVar(
            value=f"0 of {self._total_qs} answered")
        self._build()

    def _tool_max(self) -> int:
        total = 0
        for tid in self._selected_tools:
            for qkey, _, _, _, _ in TOOL_QUESTIONS.get(tid, []):
                total += _TOOL_Q_WEIGHTS.get(qkey, 0)
        return total

    def _tool_q_count(self) -> int:
        return sum(
            len(TOOL_QUESTIONS.get(tid, []))
            for tid in self._selected_tools
        )

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        _header(self, "Manual Assessment Questions", "4 of 5", 0.80)

        # ── Live score strip ──────────────────────────────────────
        score_bar = ctk.CTkFrame(self, fg_color=CLR_SURFACE,
                                 corner_radius=0, height=44)
        score_bar.grid(row=1, column=0, sticky="ew")
        score_bar.grid_columnconfigure(1, weight=1)
        score_bar.grid_propagate(False)

        ctk.CTkLabel(score_bar, text="Live Score",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=0, column=0, padx=(PAD, 6), pady=12)

        score_f = ctk.CTkFrame(score_bar, fg_color=CLR_SURFACE_ALT,
                               corner_radius=8)
        score_f.grid(row=0, column=1, pady=10, sticky="w")
        ctk.CTkLabel(score_f, textvariable=self._score_var,
                     font=("Segoe UI", 11, "bold"), text_color=CLR_ACCENT,
                     ).grid(row=0, column=0, padx=10, pady=6)

        ctk.CTkLabel(score_bar, textvariable=self._done_var,
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=0, column=2, padx=(12, PAD), pady=12)

        # ── Scrollable questions ──────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG,
                                        corner_radius=0)
        scroll.grid(row=2, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # Intro card
        intro = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE_ALT,
                             corner_radius=10, border_width=1,
                             border_color=CLR_BORDER)
        intro.grid(row=0, column=0, padx=PAD, pady=(PAD, 10), sticky="ew")
        ctk.CTkLabel(
            intro,
            text="ℹ  Answer honestly — choose what best describes your business "
                 "today. Add notes or evidence to support each answer.",
            font=FONT_SMALL, text_color=CLR_MUTED, wraplength=820,
        ).grid(padx=14, pady=10)

        for idx, (ctrl_key, cid, cname, question, hint) in enumerate(
                MANUAL_CONTROLS):
            var = ctk.StringVar(value="No")
            self._answers[ctrl_key] = var
            var.trace_add("write", lambda *_: self._update_score())
            self._make_question(scroll, idx + 1, ctrl_key,
                                cid, cname, question, hint, var)

        # ── Tool-specific sections ────────────────────────────────
        TOOL_LABELS = {
            "active_dir":   ("🔐", "Staff Logins & Accounts",     "#6C5FC7"),
            "network_scan": ("🌐", "Your Office Network",         "#2485E8"),
            "infra_scan":   ("🖥",  "Your Website & Online Services", "#5A7490"),
            "zambia_risk":  ("🇿🇲", "Local Zambian Threats",       "#F0A500"),
            "remediation":  ("🔧", "Fixing Security Problems",    "#27AE60"),
            "fleet_scan":   ("🖧", "Multiple Computers or Branches", "#00BCD4"),
            "server_hardening": ("🛡", "Business Servers",        "#4CAF50"),
        }
        q_offset = len(MANUAL_CONTROLS) + 1
        for tid in ("active_dir", "network_scan", "infra_scan",
                    "zambia_risk", "remediation", "fleet_scan",
                    "server_hardening"):
            if tid not in self._selected_tools:
                continue
            icon, label, colour = TOOL_LABELS[tid]
            # Section divider
            sec = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE,
                               corner_radius=10, border_width=1,
                               border_color=colour)
            sec.grid(row=q_offset, column=0, sticky="ew",
                     padx=PAD, pady=(PAD, 4))
            sec.grid_columnconfigure(1, weight=1)
            q_offset += 1
            ctk.CTkFrame(sec, fg_color=colour, width=5,
                         corner_radius=0).grid(row=0, column=0,
                                               sticky="ns", pady=0)
            sec.grid_propagate(False)
            sec.configure(height=44)
            header = f"{icon}  {label} — Additional Controls"
            if tid == "infra_scan" and self._infra_target:
                header += f"    (checking: {self._infra_target})"
            ctk.CTkLabel(sec, text=header,
                         font=("Segoe UI", 12, "bold"),
                         text_color=colour).grid(
                row=0, column=1, padx=14, pady=12, sticky="w")

            for ctrl_key, cid, cname, question, hint in TOOL_QUESTIONS[tid]:
                var = ctk.StringVar(value="No")
                self._answers[ctrl_key] = var
                var.trace_add("write", lambda *_: self._update_score())
                self._make_question(scroll, q_offset, ctrl_key,
                                    cid, cname, question, hint, var)
                q_offset += 1

        # ── Nav ───────────────────────────────────────────────────
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

        ctk.CTkButton(
            nav, text="Calculate Results  →",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#FFFFFF", height=BTN_H, corner_radius=BTN_R,
            command=self._submit,
        ).grid(row=0, column=2, padx=PAD, pady=14)

    def _make_question(self, parent, num, ctrl_key, cid, cname,
                       question, hint, var):
        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE,
                            corner_radius=14, border_width=1,
                            border_color=CLR_BORDER)
        card.grid(row=num, column=0, padx=PAD, pady=6, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        # ── Header: number badge + CID chip + name ────────────────
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, padx=14, pady=(14, 8), sticky="ew")
        top.grid_columnconfigure(2, weight=1)

        # Question number badge
        ctk.CTkLabel(top,
                     text=f"{num:02d}",
                     font=("Segoe UI", 11, "bold"), text_color=CLR_BG,
                     fg_color=CLR_ACCENT, corner_radius=8,
                     width=32, height=32,
                     ).grid(row=0, column=0, padx=(0, 8))

        # Control ID chip
        ctk.CTkLabel(top,
                     text=cid,
                     font=("Segoe UI", 10, "bold"), text_color=CLR_MUTED,
                     fg_color=CLR_SURFACE_ALT, corner_radius=6,
                     width=36, height=20,
                     ).grid(row=0, column=1, padx=(0, 10))

        # Control name
        ctk.CTkLabel(top, text=cname,
                     font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
                     ).grid(row=0, column=2, sticky="w")

        # Left accent stripe
        ctk.CTkFrame(card, fg_color=CLR_ACCENT, width=3,
                     corner_radius=0).grid(row=0, column=0,
                                           rowspan=6, sticky="nws",
                                           padx=(0, 0))

        # ── Question text ─────────────────────────────────────────
        ctk.CTkLabel(card, text=question,
                     font=FONT_BODY, text_color=CLR_TEXT_SEC,
                     wraplength=820, justify="left", anchor="w",
                     ).grid(row=1, column=0, padx=(20, 14),
                            pady=(0, 6), sticky="w")

        # ── Hint ─────────────────────────────────────────────────
        hint_f = ctk.CTkFrame(card, fg_color=CLR_SURFACE_ALT,
                              corner_radius=8, border_width=1,
                              border_color=CLR_BORDER)
        hint_f.grid(row=2, column=0, padx=(20, 14),
                    pady=(0, 10), sticky="ew")
        ctk.CTkLabel(hint_f,
                     text=f"💡  {hint}",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     wraplength=800, justify="left", anchor="w",
                     ).grid(padx=12, pady=8, sticky="w")

        # ── Radio buttons ─────────────────────────────────────────
        radio_row = ctk.CTkFrame(card, fg_color="transparent")
        radio_row.grid(row=3, column=0, padx=(20, 14),
                       pady=(0, 10), sticky="w")

        for choice in ("Yes – Fully", "Partially", "No"):
            clr, _ = _ANS_STYLE[choice]
            ctk.CTkRadioButton(
                radio_row, text=choice, variable=var, value=choice,
                font=FONT_BODY, text_color=CLR_TEXT,
                fg_color=clr, hover_color=clr,
                border_color=CLR_BORDER, width=150, height=30,
            ).pack(side="left", padx=(0, 16))

        # ── Evidence notes ────────────────────────────────────────
        ctk.CTkLabel(card, text="Evidence / Notes (optional):",
                     font=FONT_CAPTION, text_color=CLR_MUTED, anchor="w",
                     ).grid(row=4, column=0, padx=(20, 14),
                            pady=(0, 4), sticky="w")
        tb = ctk.CTkTextbox(
            card, height=44,
            fg_color=CLR_SURFACE_ALT, border_color=CLR_BORDER,
            border_width=1, text_color=CLR_TEXT, font=FONT_CAPTION,
            corner_radius=8)
        tb.grid(row=5, column=0, padx=(20, 14), pady=(0, 14), sticky="ew")
        self._notes[ctrl_key] = tb

    # ---------------------------------------------------------- live score
    def _update_score(self):
        total = 0
        answered = 0
        for k, var in self._answers.items():
            choice = var.get()
            w = _WEIGHTS.get(k) or _TOOL_Q_WEIGHTS.get(k, 0)
            total += round(w * ANSWER_SCORE.get(choice, 0.0))
            if choice in ("Yes – Fully", "Partially"):
                answered += 1
        pct = round(total / self._max_pts * 100) if self._max_pts else 0
        self._score_var.set(f"{total} / {self._max_pts} pts  ({pct}%)")
        self._done_var.set(f"{answered} of {self._total_qs} answered")

    # ---------------------------------------------------------------- submit
    def _submit(self):
        from src.security.assessment.assessor import CONTROL_CATALOGUE, TOOL_CONTROLS
        manual_scores: dict[str, int] = {}

        # Aggregate core C06-C15 directly
        for ctrl_key, var in self._answers.items():
            if ctrl_key in CONTROL_CATALOGUE:
                w = CONTROL_CATALOGUE[ctrl_key]["weight"]
                manual_scores[ctrl_key] = round(w * ANSWER_SCORE[var.get()])

        # Aggregate tool sub-questions → their parent C16-C20 control
        parent_scores: dict[str, list[int]] = {}
        parent_maxes:  dict[str, int]       = {}
        for ctrl_key, var in self._answers.items():
            if ctrl_key not in CONTROL_CATALOGUE and ctrl_key in _TOOL_Q_PARENT:
                parent = _TOOL_Q_PARENT[ctrl_key]
                pts = round(_TOOL_Q_WEIGHTS.get(ctrl_key, 0)
                            * ANSWER_SCORE[var.get()])
                parent_scores.setdefault(parent, []).append(pts)
                parent_maxes[parent] = parent_maxes.get(parent, 0) + \
                    _TOOL_Q_WEIGHTS.get(ctrl_key, 0)

        for parent, scores in parent_scores.items():
            if parent in TOOL_CONTROLS:
                ctrl_weight = TOOL_CONTROLS[parent]["weight"]
                sub_total   = sum(scores)
                sub_max     = parent_maxes.get(parent, 1)
                manual_scores[parent] = round(
                    ctrl_weight * sub_total / sub_max) if sub_max else 0

        evidence: dict[str, str] = {}
        for ctrl_key, tb in self._notes.items():
            txt = tb.get("1.0", "end").strip()
            if txt:
                evidence[ctrl_key] = txt
        self._on_next(manual_scores, evidence)


class EvidenceCapture(ctk.CTkToplevel):
    """Modal for capturing evidence for a manual check."""

    def __init__(self, parent, control_id, control_name):
        super().__init__(parent)
        self.title(f"Evidence Capture — {control_id}")
        self.geometry("600x400")
        self.configure(fg_color=CLR_BG)
        self.evidence_data = None

        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"📸 Evidence: {control_id} — {control_name}",
                     font=("Segoe UI", 13, "bold"), text_color=CLR_TEXT,
                     ).pack(anchor="w", padx=16, pady=12)

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(scroll, text="Notes",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT).pack(anchor="w")
        self.notes_text = ctk.CTkTextbox(scroll, fg_color=CLR_SURFACE_ALT,
                                         border_color=CLR_BORDER,
                                         text_color=CLR_TEXT,
                                         font=("Segoe UI", 11), height=150)
        self.notes_text.pack(fill="x", pady=(4, 16))

        ctk.CTkLabel(scroll, text="Attachments (screenshots, docs)",
                     font=FONT_SUBHEAD, text_color=CLR_TEXT).pack(anchor="w")
        ctk.CTkButton(scroll, text="+ Add File", command=self._add_file,
                      fg_color=CLR_SURFACE_ALT, hover_color=CLR_SUCCESS,
                      text_color=CLR_TEXT, font=FONT_BODY,
                      height=BTN_H, corner_radius=BTN_R,
                      ).pack(fill="x", pady=(4, 12))
        self.files_list = ctk.CTkTextbox(scroll, fg_color=CLR_SURFACE_ALT,
                                         border_color=CLR_BORDER,
                                         text_color=CLR_MUTED,
                                         font=("Segoe UI", 10),
                                         height=80, state="disabled")
        self.files_list.pack(fill="x", pady=(0, 16))
        self.attached_files = []

        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=50)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        ctk.CTkButton(footer, text="Cancel", command=self.destroy,
                      fg_color=CLR_SURFACE_ALT, text_color=CLR_TEXT,
                      font=FONT_BODY, height=BTN_H, corner_radius=BTN_R,
                      width=120).pack(side="left", padx=8, pady=12)
        ctk.CTkButton(footer, text="Save Evidence",
                      command=self._save_evidence,
                      fg_color=CLR_SUCCESS, text_color="#ffffff",
                      font=FONT_BODY, height=BTN_H, corner_radius=BTN_R,
                      ).pack(side="right", padx=8, pady=12)

    def _add_file(self):
        file_path = filedialog.askopenfilename(
            title="Select evidence file",
            filetypes=[("All Files", "*.*"), ("Images", "*.jpg *.png"),
                       ("Documents", "*.pdf")])
        if file_path:
            self.attached_files.append(file_path)
            self.files_list.configure(state="normal")
            self.files_list.delete("1.0", "end")
            for f in self.attached_files:
                self.files_list.insert("end", f"• {f}\n")
            self.files_list.configure(state="disabled")

    def _save_evidence(self):
        self.evidence_data = {"notes": self.notes_text.get("1.0", "end"),
                               "files": self.attached_files}
        self.destroy()


class ControlSearchFilter(ctk.CTkFrame):
    """Search and filter widget for manual controls."""

    def __init__(self, parent, on_search=None):
        super().__init__(parent, fg_color=CLR_SURFACE, corner_radius=8)
        self.on_search = on_search or (lambda x: None)
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda *args: self.on_search(self.search_var.get()))
        ctk.CTkEntry(self, placeholder_text="Search controls by name or ID...",
                     textvariable=self.search_var, fg_color=CLR_SURFACE_ALT,
                     border_color=CLR_BORDER, text_color=CLR_TEXT,
                     font=FONT_BODY, height=36,
                     ).pack(fill="x", padx=12, pady=(12, 8))

        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=12, pady=(0, 12))
        self.filter_var = ctk.StringVar(value="all")
        for text, value in [("All", "all"), ("Answered", "answered"), ("Pending", "pending")]:
            ctk.CTkRadioButton(filter_frame, text=text,
                               variable=self.filter_var, value=value,
                               fg_color=CLR_SUCCESS, text_color=CLR_TEXT,
                               font=FONT_SMALL,
                               ).pack(side="left", padx=8)


class ManualProgressIndicator(ctk.CTkFrame):
    """Live progress indicator for manual checks."""

    def __init__(self, parent, total_controls):
        super().__init__(parent, fg_color=CLR_SURFACE, corner_radius=8)
        self.total = total_controls
        self.progress_bar = ctk.CTkProgressBar(self, fg_color=CLR_SURFACE_ALT,
                                               progress_color=CLR_SUCCESS,
                                               height=6, corner_radius=2)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=12, pady=(12, 8))
        self.status_label = ctk.CTkLabel(
            self,
            text=f"Progress: 0 of {total_controls} completed",
            font=FONT_SMALL, text_color=CLR_TEXT_SEC)
        self.status_label.pack(anchor="w", padx=12, pady=(0, 12))

    def update_progress(self, answered):
        progress = answered / self.total if self.total > 0 else 0
        self.progress_bar.set(progress)
        self.status_label.configure(
            text=f"Progress: {answered} of {self.total} completed "
                 f"({int(progress * 100)}%)")
