"""Manual assessment questionnaire screen — C06-C15."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_ACCENT, CLR_TEXT, CLR_MUTED,
    CLR_BORDER, CLR_SUCCESS, CLR_WARNING, CLR_DANGER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, PAD,
)

# (control_key, id, name, question, plain_hint)
# plain_hint is shown in simple, everyday language for non-technical users.
MANUAL_CONTROLS = [
    (
        "C06_security_training", "C06", "Security Awareness Training",
        "Do ALL staff receive at least annual cybersecurity awareness training "
        "(including phishing simulations)?",
        "💡 In plain terms: Have all your employees learned how to spot fake emails "
        "(phishing), create strong passwords, and handle customer data safely — "
        "at least once in the past 12 months?",
    ),
    (
        "C07_access_control", "C07", "Access Control Policy",
        "Is there a documented least-privilege access control policy, "
        "reviewed at least annually?",
        "💡 In plain terms: Do you control who can see and edit what on your computers? "
        "For example, does only your accountant access financial files, and do you "
        "remove access when staff leave?",
    ),
    (
        "C08_incident_response", "C08", "Incident Response Plan",
        "Do you have a documented incident response plan that has been tested "
        "in the past 12 months and includes ZICTA/CERT-ZM contacts?",
        "💡 In plain terms: If your business were hacked or data stolen today, "
        "do you have a written step-by-step plan of what to do and who to call? "
        "ZICTA is Zambia's communications regulator — you should have their contact.",
    ),
    (
        "C09_encryption", "C09", "Data Encryption",
        "Is all sensitive data encrypted at rest (e.g. BitLocker/VeraCrypt) "
        "and in transit (TLS/HTTPS) on all systems?",
        "💡 In plain terms: Is customer and business data scrambled/locked so only "
        "authorised people can read it? For example: does your website address start "
        "with https:// and are laptops password-protected if lost or stolen?",
    ),
    (
        "C10_mobile_security", "C10", "Mobile Device Security",
        "Are all business mobile devices protected with screen locks, "
        "encryption, and a mobile device management (MDM) policy?",
        "💡 In plain terms: Do all company phones and tablets have a PIN or "
        "fingerprint lock, auto-lock after a few minutes of inactivity, and rules "
        "about what staff can install on them?",
    ),
    (
        "C11_physical_security", "C11", "Physical Security",
        "Is the server/IT area access-controlled, with visitor logs "
        "and CCTV in place?",
        "💡 In plain terms: Is your router, server, or main computer kept in a "
        "locked room or cabinet? Can you tell who has been in that area, and is "
        "there a security camera covering it?",
    ),
    (
        "C12_network_security", "C12", "Network Security",
        "Does the business use WPA2/WPA3 Wi-Fi with a separate guest "
        "network and network segmentation?",
        "💡 In plain terms: Is your Wi-Fi password strong and changed regularly? "
        "Do visitors connect to a different Wi-Fi from your staff, so they cannot "
        "access your business files or printers?",
    ),
    (
        "C13_acceptable_use", "C13", "Acceptable Use Policy",
        "Is there a documented acceptable use policy (AUP) signed "
        "by all staff with regular awareness reminders?",
        "💡 In plain terms: Do your employees have written rules about how to use "
        "company computers, phones, and internet — and have they signed to confirm "
        "they understand? For example: no personal downloads on work devices.",
    ),
    (
        "C14_vendor_risk", "C14", "Vendor / Third-Party Risk",
        "Do all vendor contracts include security clauses with formal "
        "risk assessments and regular reviews?",
        "💡 In plain terms: Do the companies you hire (IT support, cloud storage, "
        "payment processors) have security obligations in their contracts? Do you "
        "check that they are keeping your data safe?",
    ),
    (
        "C15_regulatory_compliance", "C15", "Regulatory Compliance",
        "Is the business fully compliant with Zambia's Data Protection Act "
        "and ZICTA cybersecurity regulations?",
        "💡 In plain terms: Are you following Zambia's laws about protecting "
        "customer data (Data Protection Act 2021) and cybersecurity (Cyber Security "
        "and Cyber Crimes Act 2021)? If unsure, consider consulting a legal adviser.",
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
        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=84)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        hdr.grid_columnconfigure(1, weight=0)
        ctk.CTkLabel(
            hdr, text="Manual Assessment Questions",
            font=FONT_HEADING, text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=PAD, pady=(16, 6), sticky="w")
        ctk.CTkLabel(
            hdr, text="Step 3 of 4",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(row=0, column=1, padx=PAD, pady=(16, 6), sticky="e")
        progress = ctk.CTkProgressBar(
            hdr, fg_color=CLR_BG, progress_color=CLR_ACCENT,
            corner_radius=6, height=10,
        )
        progress.set(0.75)
        progress.grid(row=1, column=0, columnspan=2, sticky="ew", padx=PAD, pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        info_card = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=18, border_width=1, border_color=CLR_BORDER)
        info_card.grid(row=0, column=0, padx=PAD, pady=(PAD, 10), sticky="ew")
        ctk.CTkLabel(
            info_card,
            text="Answer each question as honestly as possible — choose the option that best describes your business right now.",
            font=FONT_BODY, text_color=CLR_MUTED, wraplength=760, justify="left",
        ).grid(row=0, column=0, padx=PAD, pady=PAD)

        for q_idx, (ctrl_key, cid, cname, question, hint) in enumerate(MANUAL_CONTROLS):
            var = ctk.StringVar(value="No")
            self._answers[ctrl_key] = var

            card = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=18, border_width=1, border_color=CLR_BORDER)
            card.grid(row=q_idx + 1, column=0, padx=PAD, pady=8, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            # Control ID badge + name
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.grid(row=0, column=0, padx=18, pady=(16, 4), sticky="ew")
            top.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                top, text=cid,
                font=("Segoe UI", 10, "bold"),
                text_color="#000000",
                fg_color=CLR_ACCENT,
                corner_radius=6, width=42, height=24,
            ).grid(row=0, column=0, padx=(0, 10))

            ctk.CTkLabel(
                top, text=cname,
                font=("Segoe UI", 13, "bold"), text_color=CLR_TEXT, anchor="w",
            ).grid(row=0, column=1, sticky="w")

            # Formal question text
            ctk.CTkLabel(
                card, text=question,
                font=FONT_BODY, text_color=CLR_TEXT,
                wraplength=760, justify="left", anchor="w",
            ).grid(row=1, column=0, padx=18, pady=(0, 6), sticky="w")

            # Plain-language hint (always visible)
            hint_frame = ctk.CTkFrame(card, fg_color=CLR_SURFACE_ALT, corner_radius=10, border_width=1, border_color=CLR_BORDER)
            hint_frame.grid(row=2, column=0, padx=18, pady=(0, 10), sticky="ew")
            hint_frame.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                hint_frame, text=hint,
                font=FONT_SMALL, text_color=CLR_MUTED,
                wraplength=740, justify="left", anchor="w",
            ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

            # Radio buttons
            radio_row = ctk.CTkFrame(card, fg_color="transparent")
            radio_row.grid(row=3, column=0, padx=18, pady=(0, 18), sticky="w")
            for choice in ("Yes – Fully", "Partially", "No"):
                colour = {"Yes – Fully": CLR_SUCCESS, "Partially": CLR_WARNING, "No": CLR_DANGER}[choice]
                ctk.CTkRadioButton(
                    radio_row, text=choice, variable=var, value=choice,
                    font=FONT_BODY, text_color=CLR_TEXT,
                    fg_color=colour, hover_color=colour,
                    border_color=CLR_BORDER, border_width=1,
                    width=170, height=32,
                ).pack(side="left", padx=(0, 14))

        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=64)
        nav.grid(row=2, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            nav, text="← Back", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_MUTED, border_width=1,
            text_color=CLR_TEXT, hover_color="#243447", width=110, height=38,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

        ctk.CTkButton(
            nav, text="Calculate Results →",
            font=("Segoe UI", 13, "bold"),
            fg_color=CLR_ACCENT, hover_color="#00A87A",
            text_color="#000000", height=38, corner_radius=18,
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
