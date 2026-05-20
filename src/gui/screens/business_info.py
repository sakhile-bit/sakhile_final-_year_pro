"""Business information form screen."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_ACCENT, CLR_TEXT, CLR_MUTED,
    CLR_DANGER, CLR_BORDER,
    FONT_HEADING, FONT_BODY, FONT_SMALL, PAD,
)

PROVINCES = [
    "Lusaka", "Copperbelt", "Central", "Eastern",
    "Luapula", "Muchinga", "Northern", "North-Western",
    "Southern", "Western",
]

INDUSTRIES = [
    "Retail / Trade", "Finance & Banking", "Healthcare",
    "Education", "ICT / Technology", "Hospitality & Tourism",
    "Agriculture", "Construction", "Transport & Logistics", "Other",
]


class BusinessInfoScreen(ctk.CTkFrame):
    """Collects business details before the assessment starts."""

    def __init__(self, master, on_next, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_next = on_next
        self._on_back = on_back
        self._error_var = ctk.StringVar()
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
            hdr, text="Business & Contact Details",
            font=FONT_HEADING, text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=PAD, pady=(16, 6), sticky="w")
        ctk.CTkLabel(
            hdr, text="Step 1 of 4",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(row=0, column=1, padx=PAD, pady=(16, 6), sticky="e")
        progress = ctk.CTkProgressBar(
            hdr, fg_color=CLR_BG, progress_color=CLR_ACCENT,
            corner_radius=6, height=10,
        )
        progress.set(0.25)
        progress.grid(row=1, column=0, columnspan=2, sticky="ew", padx=PAD, pady=(0, 16))

        # Scrollable form body
        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)

        form_card = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=20, border_width=1, border_color=CLR_BORDER)
        form_card.grid(row=0, column=0, padx=PAD, pady=(PAD, 0), sticky="ew")
        form_card.grid_columnconfigure((0, 1), weight=1)

        fields = [
            ("Business Name *",        "name",           "e.g. Lusaka Tech Solutions",   0, 0, 2),
            ("Business Registration ID *", "reg_id",     "e.g. REG-2024-001",            1, 0, 1),
            ("Province *",             "province",       None,                           1, 1, 1),
            ("Industry *",             "industry",       None,                           2, 0, 1),
            ("Number of Employees",    "num_employees",  "e.g. 15",                      2, 1, 1),
            ("Contact Person",         "contact_person", "Full name",                    3, 0, 1),
            ("Contact Email",          "contact_email",  "name@business.zm",             3, 1, 1),
            ("Contact Phone",          "contact_phone",  "+260 97X XXX XXX",             4, 0, 1),
            ("Years in Operation",     "years",          "e.g. 3",                       4, 1, 1),
        ]

        self._vars: dict = {}
        for label_txt, key, placeholder, row, col, span in fields:
            frame = ctk.CTkFrame(form_card, fg_color=CLR_SURFACE_ALT, corner_radius=14, border_width=1, border_color=CLR_BORDER)
            frame.grid(
                row=row, column=col, columnspan=span,
                padx=(PAD//2, PAD//2), pady=(PAD//2, PAD//2), sticky="ew",
            )
            frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                frame, text=label_txt,
                font=FONT_SMALL, text_color=CLR_MUTED, anchor="w",
            ).grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")

            if key == "province":
                var = ctk.StringVar(value=PROVINCES[0])
                widget = ctk.CTkOptionMenu(
                    frame, values=PROVINCES, variable=var,
                    fg_color=CLR_SURFACE, button_color=CLR_ACCENT,
                    button_hover_color="#00A87A", font=FONT_BODY,
                    text_color=CLR_TEXT, dropdown_fg_color=CLR_SURFACE_ALT,
                )
                widget.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")
            elif key == "industry":
                var = ctk.StringVar(value=INDUSTRIES[0])
                widget = ctk.CTkOptionMenu(
                    frame, values=INDUSTRIES, variable=var,
                    fg_color=CLR_SURFACE, button_color=CLR_ACCENT,
                    button_hover_color="#00A87A", font=FONT_BODY,
                    text_color=CLR_TEXT, dropdown_fg_color=CLR_SURFACE_ALT,
                )
                widget.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")
            else:
                var = ctk.StringVar()
                entry = ctk.CTkEntry(
                    frame, textvariable=var,
                    placeholder_text=placeholder or "",
                    font=FONT_BODY, fg_color=CLR_BG,
                    border_color=CLR_BORDER, border_width=1,
                    text_color=CLR_TEXT, height=42,
                )
                entry.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")

            self._vars[key] = var

        ctk.CTkLabel(
            scroll, textvariable=self._error_var,
            font=FONT_SMALL, text_color=CLR_DANGER,
        ).grid(row=1, column=0, padx=PAD, pady=(10, 0), sticky="w")

        # ── Bottom nav ──────────────────────────────────────────────
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
            nav, text="Next: Run Automated Checks →",
            font=("Segoe UI", 13, "bold"),
            fg_color=CLR_ACCENT, hover_color="#00A87A",
            text_color="#000000", height=38, corner_radius=18,
            command=self._submit,
        ).grid(row=0, column=2, padx=PAD, pady=14)

    # ---------------------------------------------------------------- submit
    def _submit(self):
        name = self._vars["name"].get().strip()
        reg_id = self._vars["reg_id"].get().strip()
        if not name:
            self._error_var.set("Business Name is required.")
            return
        if not reg_id:
            self._error_var.set("Business Registration ID is required.")
            return
        self._error_var.set("")

        from src.security.assessment.assessor import BusinessInfo
        info = BusinessInfo(
            name=name,
            id=reg_id,
            province=self._vars["province"].get(),
            industry=self._vars["industry"].get(),
            contact_person=self._vars["contact_person"].get().strip() or None,
            contact_email=self._vars["contact_email"].get().strip() or None,
            contact_phone=self._vars["contact_phone"].get().strip() or None,
            num_employees=int(self._vars["num_employees"].get()) if self._vars["num_employees"].get().strip().isdigit() else None,
            years_in_operation=int(self._vars["years"].get()) if self._vars["years"].get().strip().isdigit() else None,
        )
        self._on_next(info)
