"""Manual assessment — C06-C15 questionnaire with live scoring."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_ACCENT_HOV, CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_SUCCESS, CLR_WARNING, CLR_DANGER, CLR_BORDER,
    FONT_TITLE, FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, PAD_SM, HDR_H, NAV_H, BTN_H, BTN_R,
)
from src.gui.screens.business_info import _header

MANUAL_CONTROLS = [
    ("C06_security_training", "C06", "Security Awareness Training",
     "Do ALL staff receive at least annual cybersecurity awareness training "
     "and phishing simulations?",
     "💡 Have your employees been trained to spot fake emails (phishing), "
     "use strong passwords, and handle customer data safely in the past 12 months?"),
    ("C07_access_control", "C07", "Access Control Policy",
     "Is there a documented least-privilege access control policy, "
     "reviewed at least annually?",
     "💡 Do you control who can see and edit what on your computers? "
     "Do you remove access immediately when staff leave?"),
    ("C08_incident_response", "C08", "Incident Response Plan",
     "Do you have a tested incident response plan that includes ZICTA/CERT-ZM contacts?",
     "💡 If hacked today, do you have a written plan of what to do and who to call? "
     "ZICTA: +260 211 369 000 | cert@zicta.zm"),
    ("C09_encryption", "C09", "Data Encryption",
     "Is sensitive data encrypted at rest (BitLocker) and in transit (HTTPS) on all systems?",
     "💡 Does your website start with https:// and are laptops protected if lost or stolen?"),
    ("C10_mobile_security", "C10", "Mobile Device Security",
     "Are all business mobile devices protected with screen locks, encryption and MDM policy?",
     "💡 Do all company phones lock automatically and only allow apps from official stores?"),
    ("C11_physical_security", "C11", "Physical Security",
     "Is the server/IT area access-controlled with visitor logs and CCTV?",
     "💡 Is your router or server in a locked room? Can you tell who has been in that area?"),
    ("C12_network_security", "C12", "Network Security",
     "Does the business use WPA2/WPA3 Wi-Fi with a separate guest network?",
     "💡 Is your Wi-Fi password strong? Do visitors use a different Wi-Fi from your staff?"),
    ("C13_acceptable_use", "C13", "Acceptable Use Policy",
     "Is there a documented acceptable use policy signed by all staff?",
     "💡 Do employees have written rules about company computers and internet use?"),
    ("C14_vendor_risk", "C14", "Vendor / Third-Party Risk",
     "Do vendor contracts include security clauses with formal risk assessments?",
     "💡 Do your IT suppliers and cloud providers have security obligations in their contracts?"),
    ("C15_regulatory_compliance", "C15", "Regulatory Compliance",
     "Is the business compliant with Zambia's Data Protection Act and ZICTA regulations?",
     "💡 Are you following the Data Protection Act 2021 and Cyber Security Act 2021?"),
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

# Answer button colours
_ANS_COLOURS = {
    "Yes – Fully": CLR_SUCCESS,
    "Partially":   CLR_WARNING,
    "No":          CLR_DANGER,
}


class ManualChecksScreen(ctk.CTkFrame):

    def __init__(self, master, on_next, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_next = on_next
        self._on_back = on_back
        self._answers: dict[str, ctk.StringVar] = {}
        self._notes: dict[str, ctk.CTkTextbox] = {}
        self._score_var = ctk.StringVar(value="0 / 65 pts  (0%)")
        self._answered_var = ctk.StringVar(value="0 of 10 answered")
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        _header(self, "Manual Assessment Questions", "3 of 4", 0.75)

        # Live score strip (below header, above scroll)
        score_bar = ctk.CTkFrame(self, fg_color=CLR_SURFACE,
                                 corner_radius=0, height=40)
        score_bar.grid(row=1, column=0, sticky="ew")
        score_bar.grid_columnconfigure(1, weight=1)
        score_bar.grid_propagate(False)

        ctk.CTkLabel(score_bar, text="Live Score:",
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=0, column=0, padx=(PAD, 6), pady=10)
        ctk.CTkLabel(score_bar, textvariable=self._score_var,
                     font=("Segoe UI", 11, "bold"), text_color=CLR_ACCENT,
                     ).grid(row=0, column=1, sticky="w", pady=10)
        ctk.CTkLabel(score_bar, textvariable=self._answered_var,
                     font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=0, column=2, padx=(0, PAD), pady=10)

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=2, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # Re-weight grid rows
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)

        # Intro
        intro = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE_ALT,
                             corner_radius=12, border_width=1,
                             border_color=CLR_BORDER)
        intro.grid(row=0, column=0, padx=PAD, pady=(PAD, 10), sticky="ew")
        ctk.CTkLabel(
            intro,
            text="Answer each question honestly — choose what best describes "
                 "your business today. Add notes or evidence to support your answer.",
            font=FONT_SMALL, text_color=CLR_MUTED, wraplength=800,
        ).grid(padx=14, pady=10)

        for q_idx, (ctrl_key, cid, cname, question, hint) in enumerate(
                MANUAL_CONTROLS):
            var = ctk.StringVar(value="No")
            self._answers[ctrl_key] = var
            var.trace_add("write", lambda *_: self._update_score())

            card = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE,
                                corner_radius=14, border_width=1,
                                border_color=CLR_BORDER)
            card.grid(row=q_idx + 1, column=0, padx=PAD, pady=6, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            # Header row: ID badge + control name
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.grid(row=0, column=0, padx=14, pady=(14, 6), sticky="ew")
            top.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                top, text=cid,
                font=("Segoe UI", 9, "bold"), text_color="#000000",
                fg_color=CLR_ACCENT, corner_radius=6,
                width=38, height=22,
            ).grid(row=0, column=0, padx=(0, 10))
            ctk.CTkLabel(
                top, text=cname,
                font=FONT_SUBHEAD, text_color=CLR_TEXT, anchor="w",
            ).grid(row=0, column=1, sticky="w")

            # Question
            ctk.CTkLabel(
                card, text=question, font=FONT_BODY, text_color=CLR_TEXT_SEC,
                wraplength=800, justify="left", anchor="w",
            ).grid(row=1, column=0, padx=14, pady=(0, 6), sticky="w")

            # Hint box
            hint_f = ctk.CTkFrame(card, fg_color=CLR_SURFACE_ALT,
                                  corner_radius=8, border_width=1,
                                  border_color=CLR_BORDER)
            hint_f.grid(row=2, column=0, padx=14, pady=(0, 10), sticky="ew")
            hint_f.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                hint_f, text=hint, font=FONT_CAPTION, text_color=CLR_MUTED,
                wraplength=800, justify="left", anchor="w",
            ).grid(row=0, column=0, padx=12, pady=8, sticky="w")

            # Radio buttons
            radio_row = ctk.CTkFrame(card, fg_color="transparent")
            radio_row.grid(row=3, column=0, padx=14, pady=(0, 8), sticky="w")
            for choice in ("Yes – Fully", "Partially", "No"):
                ctk.CTkRadioButton(
                    radio_row, text=choice, variable=var, value=choice,
                    font=FONT_BODY, text_color=CLR_TEXT,
                    fg_color=_ANS_COLOURS[choice],
                    hover_color=_ANS_COLOURS[choice],
                    border_color=CLR_BORDER,
                    width=160, height=30,
                ).pack(side="left", padx=(0, 12))

            # Evidence notes
            ctk.CTkLabel(card, text="Evidence / Notes (optional):",
                         font=FONT_CAPTION, text_color=CLR_MUTED, anchor="w",
                         ).grid(row=4, column=0, padx=14, pady=(0, 4), sticky="w")
            tb = ctk.CTkTextbox(
                card, height=48,
                fg_color=CLR_SURFACE_ALT, border_color=CLR_BORDER,
                border_width=1, text_color=CLR_TEXT, font=FONT_CAPTION,
                corner_radius=8,
            )
            tb.grid(row=5, column=0, padx=14, pady=(0, 14), sticky="ew")
            self._notes[ctrl_key] = tb

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

        ctk.CTkButton(
            nav, text="Calculate Results  →",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
            text_color="#000000", height=BTN_H, corner_radius=BTN_R,
            command=self._submit,
        ).grid(row=0, column=2, padx=PAD, pady=14)

    def _update_score(self):
        total = 0
        answered = 0
        for k, var in self._answers.items():
            choice = var.get()
            fraction = ANSWER_SCORE.get(choice, 0.0)
            total += round(_WEIGHTS.get(k, 0) * fraction)
            if choice in ("Yes – Fully", "Partially"):
                answered += 1
        pct = round(total / _MAX * 100) if _MAX else 0
        self._score_var.set(f"{total} / {_MAX} pts  ({pct}%)")
        self._answered_var.set(f"{answered} of 10 answered")

    def _submit(self):
        from src.security.assessment.assessor import CONTROL_CATALOGUE
        manual_scores: dict[str, int] = {}
        for ctrl_key, var in self._answers.items():
            weight = CONTROL_CATALOGUE[ctrl_key]["weight"]
            manual_scores[ctrl_key] = round(weight * ANSWER_SCORE[var.get()])
        evidence: dict[str, str] = {}
        for ctrl_key, tb in self._notes.items():
            txt = tb.get("1.0", "end").strip()
            if txt:
                evidence[ctrl_key] = txt
        self._on_next(manual_scores, evidence)
