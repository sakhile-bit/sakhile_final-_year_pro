"""Zambia Local Threat Assessment — evaluates Zambia-specific digital risks."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_ACCENT, CLR_TEXT, CLR_MUTED,
    CLR_BORDER, CLR_SUCCESS, CLR_WARNING, CLR_DANGER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, PAD,
)

# ─── Assessment questions grouped by category ────────────────────────────────
CATEGORIES = [
    {
        "title": "📱 Mobile Money & SIM Security",
        "colour": "#1E90FF",
        "items": [
            ("sim_swap_protection",
             "Has your business set a SIM PIN on all company SIMs and registered for SIM swap alerts with your network provider?",
             "SIM swap fraud is a leading cybercrime in Zambia — attackers transfer your number to steal mobile money OTPs."),
            ("mobile_money_limits",
             "Have you set daily transaction limits on all mobile money accounts (Airtel Money, MTN MoMo, Zamtel Kwacha)?",
             "Transaction limits reduce losses if an account is compromised."),
            ("mobile_money_2fa",
             "Are all mobile money and mobile banking accounts protected with a PIN/password that is NOT shared with anyone?",
             "A unique PIN for each service prevents one compromise from affecting all accounts."),
            ("mobile_money_policy",
             "Do you have a written policy for mobile money transactions (approvals, limits, who can authorise payments)?",
             "Uncontrolled mobile payments are a common source of fraud in Zambian SMBs."),
        ],
    },
    {
        "title": "📧 Email & Phishing Protection",
        "colour": "#FFB800",
        "items": [
            ("phishing_training",
             "Have all staff been trained in the last 12 months to recognise phishing emails, fake links, and social engineering?",
             "Most successful cyberattacks in Zambia start with a deceptive email or WhatsApp message."),
            ("email_mfa",
             "Is multi-factor authentication (MFA) enabled on all business email accounts (Gmail, Outlook, etc.)?",
             "MFA blocks over 99% of automated account takeover attacks."),
            ("spf_dmarc",
             "Has your IT provider configured SPF and DMARC DNS records to prevent email spoofing of your domain?",
             "Without SPF/DMARC, attackers can send emails that appear to come from your business."),
            ("whatsapp_fraud_awareness",
             "Have staff been warned about WhatsApp impersonation scams (e.g. a 'manager' requesting urgent payments)?",
             "WhatsApp fraud impersonating executives is extremely common in Zambia."),
        ],
    },
    {
        "title": "⚖️ Zambia Legal Compliance",
        "colour": "#6C5FC7",
        "items": [
            ("dpa_registered",
             "Is your business registered with the Data Protection Commission (DPC) under the Zambia Data Protection Act No. 3 of 2021?",
             "Registration is required for businesses that process personal data of Zambian residents."),
            ("dpa_policy",
             "Do you have a written Data Protection Policy that explains how you collect, use, and protect customer data?",
             "The DPA 2021 requires organisations to be transparent about data processing."),
            ("cyber_crimes_act",
             "Are staff aware of the Cyber Security and Cyber Crimes Act 2021 and the penalties for misusing company systems?",
             "Employees who misuse systems can face criminal prosecution — awareness is a legal defence."),
            ("zicta_alerts",
             "Is your business subscribed to ZICTA security alerts and CERT-ZM notifications?",
             "ZICTA/CERT-ZM provide free early warnings about threats targeting Zambian organisations."),
        ],
    },
    {
        "title": "💼 Business Continuity",
        "colour": "#CD7F32",
        "items": [
            ("backup_offsite",
             "Are business backups stored off-site or in the cloud (not only on the same premises as the original data)?",
             "A fire, flood, or theft will destroy local-only backups. Cloud backup is essential."),
            ("disaster_recovery",
             "Do you have a written plan for how the business would operate if all computers were destroyed or stolen?",
             "Without a plan, most small businesses cannot recover from a serious incident."),
            ("supplier_security",
             "Have you checked that your key technology suppliers (internet, cloud, payment processor) have their own security controls in place?",
             "Supply chain attacks are rising — your suppliers are part of your security posture."),
            ("cyber_insurance",
             "Does your business have cyber insurance or has management assessed whether it is appropriate for your risk level?",
             "Cyber insurance can cover losses from ransomware, fraud, and data breaches."),
        ],
    },
]

RISK_COLOURS = {
    "LOW RISK":    ("#6C5FC7", "Your business has good protection against local threats. "
                   "Maintain these controls and review annually."),
    "MEDIUM RISK": ("#FFB800", "Your business has some gaps in local threat protection. "
                   "Address the unchecked items as a priority."),
    "HIGH RISK":   ("#FF4C4C", "Your business is significantly exposed to local digital threats. "
                   "Take immediate action on the items below."),
}


class ZambiaRiskScreen(ctk.CTkFrame):
    """Zambia-specific local threat and compliance assessment."""

    def __init__(self, master, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back
        self._checks: dict[str, ctk.BooleanVar] = {}
        self._result_frame: ctk.CTkFrame | None = None
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
            hdr, text="Zambia Local Threat Assessment",
            font=FONT_HEADING, text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=PAD, pady=(16, 4), sticky="w")
        ctk.CTkLabel(
            hdr,
            text="Assess your exposure to threats specific to Zambia — "
                 "mobile money fraud, WhatsApp scams, and regulatory compliance.",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(row=1, column=0, padx=PAD, pady=(0, 14), sticky="w")

        self._scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        intro = ctk.CTkFrame(self._scroll, fg_color=CLR_SURFACE_ALT, corner_radius=12,
                             border_width=1, border_color=CLR_BORDER)
        intro.grid(row=0, column=0, padx=PAD, pady=(PAD, 12), sticky="ew")
        ctk.CTkLabel(
            intro,
            text="✅  Tick each control that your business currently has in place. "
                 "Be honest — this assessment is for your benefit. "
                 "Click 'Calculate Risk' when done.",
            font=FONT_SMALL, text_color=CLR_MUTED, wraplength=820, justify="left",
        ).grid(row=0, column=0, padx=14, pady=10, sticky="w")

        current_row = 1
        for cat in CATEGORIES:
            # Category header
            cat_hdr = ctk.CTkFrame(self._scroll, fg_color=CLR_SURFACE, corner_radius=12,
                                   border_width=1, border_color=CLR_BORDER)
            cat_hdr.grid(row=current_row, column=0, padx=PAD, pady=(10, 4), sticky="ew")
            cat_hdr.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                cat_hdr, text=cat["title"],
                font=("Segoe UI", 13, "bold"), text_color=cat["colour"],
            ).grid(row=0, column=0, padx=16, pady=10, sticky="w")
            current_row += 1

            for key, question, hint in cat["items"]:
                var = ctk.BooleanVar(value=False)
                self._checks[key] = var

                card = ctk.CTkFrame(self._scroll, fg_color=CLR_SURFACE, corner_radius=12,
                                    border_width=1, border_color=CLR_BORDER)
                card.grid(row=current_row, column=0, padx=PAD, pady=4, sticky="ew")
                card.grid_columnconfigure(1, weight=1)

                cb = ctk.CTkCheckBox(
                    card, text="", variable=var,
                    fg_color=CLR_ACCENT, hover_color="#7D70D6",
                    border_color=CLR_BORDER, width=24, height=24,
                )
                cb.grid(row=0, column=0, padx=(16, 10), pady=14, sticky="n")

                text_frame = ctk.CTkFrame(card, fg_color="transparent")
                text_frame.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=10)
                text_frame.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(
                    text_frame, text=question,
                    font=FONT_BODY, text_color=CLR_TEXT,
                    wraplength=740, justify="left", anchor="w",
                ).grid(row=0, column=0, sticky="w")

                hint_f = ctk.CTkFrame(text_frame, fg_color=CLR_SURFACE_ALT,
                                      corner_radius=8, border_width=1, border_color=CLR_BORDER)
                hint_f.grid(row=1, column=0, sticky="ew", pady=(6, 0))
                ctk.CTkLabel(
                    hint_f, text=f"💡 {hint}",
                    font=FONT_SMALL, text_color=CLR_MUTED,
                    wraplength=720, justify="left", anchor="w",
                ).grid(row=0, column=0, padx=10, pady=6, sticky="w")

                current_row += 1

        # Placeholder for results (inserted dynamically)
        self._result_row = current_row

        # Nav
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=64)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            nav, text="← Back to Home", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_MUTED, border_width=1,
            text_color=CLR_TEXT, hover_color="#243447", width=150, height=38,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

        ctk.CTkButton(
            nav, text="Calculate Risk →",
            font=("Segoe UI", 13, "bold"),
            fg_color=CLR_ACCENT, hover_color="#7D70D6",
            text_color="#000000", height=38, corner_radius=18,
            command=self._calculate,
        ).grid(row=0, column=2, padx=PAD, pady=14)

    # ---------------------------------------------------------------- calculate
    def _calculate(self):
        total = len(self._checks)
        mitigated = sum(1 for v in self._checks.values() if v.get())
        score = round((mitigated / total) * 100) if total else 0

        if score >= 75:
            level = "LOW RISK"
        elif score >= 45:
            level = "MEDIUM RISK"
        else:
            level = "HIGH RISK"

        clr, msg = RISK_COLOURS[level]

        # Destroy old result if re-calculating
        if self._result_frame:
            self._result_frame.destroy()

        rf = ctk.CTkFrame(self._scroll, fg_color=CLR_SURFACE, corner_radius=16,
                          border_width=2, border_color=clr)
        rf.grid(row=self._result_row, column=0, padx=PAD, pady=(14, PAD), sticky="ew")
        rf.grid_columnconfigure(0, weight=1)
        self._result_frame = rf

        ctk.CTkLabel(
            rf, text=level,
            font=("Segoe UI", 26, "bold"), text_color=clr,
        ).grid(row=0, column=0, pady=(20, 4))

        ctk.CTkLabel(
            rf, text=f"{mitigated} of {total} controls in place  ({score}%)",
            font=("Segoe UI", 14, "bold"), text_color=CLR_TEXT,
        ).grid(row=1, column=0, pady=(0, 8))

        bar = ctk.CTkProgressBar(rf, fg_color=CLR_SURFACE_ALT, progress_color=clr,
                                 height=12, corner_radius=6)
        bar.set(score / 100)
        bar.grid(row=2, column=0, padx=40, pady=(0, 12), sticky="ew")

        ctk.CTkLabel(
            rf, text=msg,
            font=FONT_SMALL, text_color=CLR_MUTED,
            wraplength=700, justify="center",
        ).grid(row=3, column=0, padx=PAD, pady=(0, 12))

        # List gaps
        gaps = [key for key, var in self._checks.items() if not var.get()]
        if gaps:
            ctk.CTkLabel(
                rf, text="Gaps to address:",
                font=("Segoe UI", 11, "bold"), text_color=CLR_TEXT,
            ).grid(row=4, column=0, padx=PAD, pady=(4, 0), sticky="w")

            for i, key in enumerate(gaps):
                # Find the question text for this key
                label = key.replace("_", " ").title()
                for cat in CATEGORIES:
                    for item_key, question, _ in cat["items"]:
                        if item_key == key:
                            label = question[:80] + "…" if len(question) > 80 else question
                            break
                gap_f = ctk.CTkFrame(rf, fg_color=CLR_SURFACE_ALT, corner_radius=8)
                gap_f.grid(row=5 + i, column=0, padx=PAD, pady=2, sticky="ew")
                gap_f.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(gap_f, text="✖", font=FONT_BODY,
                             text_color=CLR_DANGER, width=20,
                             ).grid(row=0, column=0, padx=(10, 6), pady=6)
                ctk.CTkLabel(gap_f, text=label, font=FONT_SMALL,
                             text_color=CLR_TEXT, anchor="w",
                             wraplength=720, justify="left",
                             ).grid(row=0, column=1, sticky="w", padx=(0, 10), pady=6)

        ctk.CTkLabel(
            rf, text="",
            height=10,
        ).grid(row=5 + len(gaps), column=0)

        # Scroll to results
        self._scroll._parent_canvas.after(
            100, lambda: self._scroll._parent_canvas.yview_moveto(1.0)
        )
