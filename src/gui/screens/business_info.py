"""Business information form screen."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT,
    CLR_ACCENT, CLR_ACCENT_HOV, CLR_TEXT, CLR_TEXT_SEC, CLR_MUTED,
    CLR_DANGER, CLR_BORDER, CLR_DIVIDER,
    FONT_TITLE, FONT_SUBHEAD, FONT_BODY, FONT_SMALL, FONT_CAPTION,
    PAD, PAD_SM, HDR_H, NAV_H, BTN_H, BTN_R,
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


def _header(parent, title, step, progress_val):
    """Standardised screen header with step indicator and progress bar."""
    hdr = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=0,
                       height=HDR_H)
    hdr.grid(row=0, column=0, sticky="ew")
    hdr.grid_columnconfigure(0, weight=1)
    hdr.grid_propagate(False)

    ctk.CTkLabel(hdr, text=title, font=FONT_TITLE,
                 text_color=CLR_TEXT, anchor="w",
                 ).grid(row=0, column=0, padx=PAD, pady=(16, 0), sticky="w")

    # Step indicator dots
    dots = "  ".join("●" if i < int(step[0]) else "○" for i in range(4))
    ctk.CTkLabel(hdr, text=f"Step {step}   {dots}",
                 font=FONT_CAPTION, text_color=CLR_MUTED,
                 ).grid(row=0, column=1, padx=PAD, pady=(16, 0), sticky="e")

    # Thin accent progress bar
    bar = ctk.CTkProgressBar(hdr, fg_color=CLR_DIVIDER,
                             progress_color=CLR_ACCENT,
                             corner_radius=0, height=3)
    bar.set(progress_val)
    bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
    return hdr


def _nav(parent, back_cmd, fwd_text, fwd_cmd, row=2):
    """Standardised bottom navigation bar."""
    nav = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=0,
                       height=NAV_H)
    nav.grid(row=row, column=0, sticky="ew")
    nav.grid_columnconfigure(1, weight=1)
    nav.grid_propagate(False)

    ctk.CTkButton(
        nav, text="← Back", font=FONT_BODY,
        fg_color="transparent", border_color=CLR_BORDER, border_width=1,
        text_color=CLR_TEXT_SEC, hover_color=CLR_SURFACE_ALT,
        width=100, height=BTN_H, corner_radius=BTN_R,
        command=back_cmd,
    ).grid(row=0, column=0, padx=PAD, pady=14)

    ctk.CTkButton(
        nav, text=fwd_text,
        font=("Segoe UI", 12, "bold"),
        fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HOV,
        text_color="#000000", height=BTN_H, corner_radius=BTN_R,
        command=fwd_cmd,
    ).grid(row=0, column=2, padx=PAD, pady=14)
    return nav


class BusinessInfoScreen(ctk.CTkFrame):

    def __init__(self, master, on_next, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_next = on_next
        self._on_back = on_back
        self._error_var = ctk.StringVar()
        self._vars: dict = {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        _header(self, "Business & Contact Details", "1 of 4", 0.25)

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # Info note
        note = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE_ALT,
                            corner_radius=12, border_width=1,
                            border_color=CLR_BORDER)
        note.grid(row=0, column=0, padx=PAD, pady=(PAD, 14), sticky="ew")
        ctk.CTkLabel(
            note,
            text="Fields marked * are required.  "
                 "This information is stored only on your device.",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(padx=14, pady=10)

        # Form card
        form = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE, corner_radius=16,
                            border_width=1, border_color=CLR_BORDER)
        form.grid(row=1, column=0, padx=PAD, pady=(0, 4), sticky="ew")
        form.grid_columnconfigure((0, 1), weight=1)

        fields = [
            ("Business Name *",         "name",           "e.g. Lusaka Tech Solutions",
             0, 0, 2),
            ("Business Registration ID *", "reg_id",      "e.g. REG-2024-001",
             1, 0, 1),
            ("Province *",              "province",        None,
             1, 1, 1),
            ("Industry *",              "industry",        None,
             2, 0, 1),
            ("Number of Employees",     "num_employees",   "e.g. 15",
             2, 1, 1),
            ("Contact Person",          "contact_person",  "Full name",
             3, 0, 1),
            ("Contact Email",           "contact_email",   "name@business.zm",
             3, 1, 1),
            ("Contact Phone",           "contact_phone",   "+260 97X XXX XXX",
             4, 0, 1),
            ("Years in Operation",      "years",           "e.g. 3",
             4, 1, 1),
        ]

        for label_txt, key, placeholder, row, col, span in fields:
            cell = ctk.CTkFrame(form, fg_color=CLR_SURFACE_ALT,
                                corner_radius=10, border_width=1,
                                border_color=CLR_BORDER)
            cell.grid(row=row, column=col, columnspan=span,
                      padx=PAD_SM, pady=PAD_SM, sticky="ew")
            cell.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(cell, text=label_txt, font=FONT_CAPTION,
                         text_color=CLR_MUTED, anchor="w",
                         ).grid(row=0, column=0, padx=14, pady=(10, 3), sticky="w")

            if key == "province":
                var = ctk.StringVar(value=PROVINCES[0])
                ctk.CTkOptionMenu(
                    cell, values=PROVINCES, variable=var,
                    fg_color=CLR_SURFACE, button_color=CLR_ACCENT,
                    button_hover_color=CLR_ACCENT_HOV,
                    font=FONT_BODY, text_color=CLR_TEXT,
                    dropdown_fg_color=CLR_SURFACE_ALT,
                    height=38, corner_radius=8,
                ).grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")
            elif key == "industry":
                var = ctk.StringVar(value=INDUSTRIES[0])
                ctk.CTkOptionMenu(
                    cell, values=INDUSTRIES, variable=var,
                    fg_color=CLR_SURFACE, button_color=CLR_ACCENT,
                    button_hover_color=CLR_ACCENT_HOV,
                    font=FONT_BODY, text_color=CLR_TEXT,
                    dropdown_fg_color=CLR_SURFACE_ALT,
                    height=38, corner_radius=8,
                ).grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")
            else:
                var = ctk.StringVar()
                ctk.CTkEntry(
                    cell, textvariable=var,
                    placeholder_text=placeholder or "",
                    font=FONT_BODY, fg_color=CLR_SURFACE,
                    border_color=CLR_BORDER, border_width=1,
                    text_color=CLR_TEXT, height=38, corner_radius=8,
                ).grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")

            self._vars[key] = var

        ctk.CTkLabel(scroll, textvariable=self._error_var,
                     font=FONT_SMALL, text_color=CLR_DANGER,
                     ).grid(row=2, column=0, padx=PAD, pady=(8, 0), sticky="w")

        _nav(self, self._on_back, "Run Security Checks  →", self._submit)

    def _submit(self):
        name = self._vars["name"].get().strip()
        reg_id = self._vars["reg_id"].get().strip()
        if not name:
            self._error_var.set("⚠  Business Name is required.")
            return
        if not reg_id:
            self._error_var.set("⚠  Business Registration ID is required.")
            return
        self._error_var.set("")
        from src.security.assessment.assessor import BusinessInfo
        self._on_next(BusinessInfo(
            name=name, id=reg_id,
            province=self._vars["province"].get(),
            industry=self._vars["industry"].get(),
            contact_person=self._vars["contact_person"].get().strip() or None,
            contact_email=self._vars["contact_email"].get().strip() or None,
            contact_phone=self._vars["contact_phone"].get().strip() or None,
            num_employees=(int(self._vars["num_employees"].get())
                          if self._vars["num_employees"].get().strip().isdigit()
                          else None),
            years_in_operation=(int(self._vars["years"].get())
                               if self._vars["years"].get().strip().isdigit()
                               else None),
        ))
