"""Manual assessment — C06-C15 questions with numbered cards and live scoring."""

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

_ANS_STYLE = {
    "Yes – Fully": (CLR_SUCCESS, "#1A1730"),
    "Partially":   (CLR_WARNING, "#1A1400"),
    "No":          (CLR_DANGER,  "#2A0A0A"),
}


class ManualChecksScreen(ctk.CTkFrame):

    def __init__(self, master, on_next, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_next = on_next
        self._on_back = on_back
        self._answers: dict[str, ctk.StringVar] = {}
        self._notes: dict[str, ctk.CTkTextbox] = {}
        self._score_var = ctk.StringVar(value="0 / 65 pts  (0%)")
        self._done_var = ctk.StringVar(value="0 of 10 answered")
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        _header(self, "Manual Assessment Questions", "3 of 4", 0.75)

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
            text_color="#000000", height=BTN_H, corner_radius=BTN_R,
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
                     font=("Segoe UI", 9, "bold"), text_color=CLR_MUTED,
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
            total += round(_WEIGHTS.get(k, 0) * ANSWER_SCORE.get(choice, 0.0))
            if choice in ("Yes – Fully", "Partially"):
                answered += 1
        pct = round(total / _MAX * 100) if _MAX else 0
        self._score_var.set(f"{total} / {_MAX} pts  ({pct}%)")
        self._done_var.set(f"{answered} of 10 answered")

    # ---------------------------------------------------------------- submit
    def _submit(self):
        from src.security.assessment.assessor import CONTROL_CATALOGUE
        manual_scores: dict[str, int] = {}
        for ctrl_key, var in self._answers.items():
            weight = CONTROL_CATALOGUE[ctrl_key]["weight"]
            manual_scores[ctrl_key] = round(
                weight * ANSWER_SCORE[var.get()])
        evidence: dict[str, str] = {}
        for ctrl_key, tb in self._notes.items():
            txt = tb.get("1.0", "end").strip()
            if txt:
                evidence[ctrl_key] = txt
        self._on_next(manual_scores, evidence)
