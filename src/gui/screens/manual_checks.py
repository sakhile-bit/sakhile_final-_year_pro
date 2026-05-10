"""Manual assessment questionnaire screen — C06-C15."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_ACCENT, CLR_TEXT, CLR_MUTED,
    FONT_HEADING, FONT_BODY, FONT_SMALL, PAD,
)

# (control_key, id, name, question)
MANUAL_CONTROLS = [
    (
        "C06_security_training", "C06", "Security Awareness Training",
        "Do ALL staff receive at least annual cybersecurity awareness training "
        "(including phishing simulations)?",
    ),
    (
        "C07_access_control", "C07", "Access Control Policy",
        "Is there a documented least-privilege access control policy, "
        "reviewed at least annually?",
    ),
    (
        "C08_incident_response", "C08", "Incident Response Plan",
        "Do you have a documented incident response plan that has been tested "
        "in the past 12 months and includes ZICTA/CERT-ZM contacts?",
    ),
    (
        "C09_encryption", "C09", "Data Encryption",
        "Is all sensitive data encrypted at rest (e.g. BitLocker/VeraCrypt) "
        "and in transit (TLS/HTTPS) on all systems?",
    ),
    (
        "C10_mobile_security", "C10", "Mobile Device Security",
        "Are all business mobile devices protected with screen locks, "
        "encryption, and a mobile device management (MDM) policy?",
    ),
    (
        "C11_physical_security", "C11", "Physical Security",
        "Is the server/IT area access-controlled, with visitor logs "
        "and CCTV in place?",
    ),
    (
        "C12_network_security", "C12", "Network Security",
        "Does the business use WPA2/WPA3 Wi-Fi with a separate guest "
        "network and network segmentation?",
    ),
    (
        "C13_acceptable_use", "C13", "Acceptable Use Policy",
        "Is there a documented acceptable use policy (AUP) signed "
        "by all staff with regular awareness reminders?",
    ),
    (
        "C14_vendor_risk", "C14", "Vendor / Third-Party Risk",
        "Do all vendor contracts include security clauses with formal "
        "risk assessments and regular reviews?",
    ),
    (
        "C15_regulatory_compliance", "C15", "Regulatory Compliance",
        "Is the business fully compliant with Zambia's Data Protection Act "
        "and ZICTA cybersecurity regulations?",
    ),
]

# Answer → fraction of weight awarded
ANSWER_SCORE = {"Yes – Fully": 1.0, "Partially": 0.5, "No": 0.0}


class ManualChecksScreen(ctk.CTkFrame):
    """Shows C06-C15 as Yes/Partially/No radio-button questions."""

    def __init__(self, master, on_next, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_next = on_next
        self._on_back = on_back
        self._answers: dict[str, ctk.StringVar] = {}
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=64)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="Manual Assessment Questions",
            font=FONT_HEADING, text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=PAD, pady=16, sticky="w")
        ctk.CTkLabel(
            hdr, text="Step 3 of 4",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(row=0, column=1, padx=PAD, pady=16, sticky="e")

        # Scrollable question list
        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            scroll,
            text="Answer each question honestly based on your current security practices.",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(row=0, column=0, padx=PAD, pady=(PAD, 8), sticky="w")

        for q_idx, (ctrl_key, cid, cname, question) in enumerate(MANUAL_CONTROLS):
            var = ctk.StringVar(value="No")
            self._answers[ctrl_key] = var

            card = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=12)
            card.grid(row=q_idx + 1, column=0, padx=PAD, pady=6, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            # Badge + name
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.grid(row=0, column=0, padx=14, pady=(12, 4), sticky="ew")
            top.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                top, text=cid,
                font=("Segoe UI", 10, "bold"),
                text_color="#000000",
                fg_color=CLR_ACCENT,
                corner_radius=6, width=40, height=22,
            ).grid(row=0, column=0, padx=(0, 8))

            ctk.CTkLabel(
                top, text=cname,
                font=("Segoe UI", 12, "bold"), text_color=CLR_TEXT, anchor="w",
            ).grid(row=0, column=1, sticky="w")

            # Question text
            ctk.CTkLabel(
                card, text=question,
                font=FONT_SMALL, text_color=CLR_MUTED,
                wraplength=740, justify="left", anchor="w",
            ).grid(row=1, column=0, padx=14, pady=(0, 10), sticky="w")

            # Radio buttons
            radio_row = ctk.CTkFrame(card, fg_color="transparent")
            radio_row.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")
            for choice in ("Yes – Fully", "Partially", "No"):
                colour = {"Yes – Fully": "#00C896", "Partially": "#FFB800", "No": "#FF4C4C"}[choice]
                ctk.CTkRadioButton(
                    radio_row, text=choice, variable=var, value=choice,
                    font=FONT_BODY, text_color=CLR_TEXT,
                    fg_color=colour, hover_color=colour,
                    border_color=CLR_MUTED,
                ).pack(side="left", padx=(0, 20))

        # Nav
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=64)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            nav, text="← Back", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_MUTED, border_width=1,
            text_color=CLR_TEXT, hover_color="#243447", width=100, height=36,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

        ctk.CTkButton(
            nav, text="Calculate Results →",
            font=("Segoe UI", 13, "bold"),
            fg_color=CLR_ACCENT, hover_color="#00A87A",
            text_color="#000000", height=36, corner_radius=18,
            command=self._submit,
        ).grid(row=0, column=2, padx=PAD, pady=14)

    # ---------------------------------------------------------------- submit
    def _submit(self):
        from src.security.assessment.assessor import CONTROL_CATALOGUE

        manual_scores: dict[str, int] = {}
        for ctrl_key, var in self._answers.items():
            weight = CONTROL_CATALOGUE[ctrl_key]["weight"]
            fraction = ANSWER_SCORE[var.get()]
            manual_scores[ctrl_key] = round(weight * fraction)

        self._on_next(manual_scores)
