"""Settings screen — real, persisted application preferences.

Every field is loaded from and saved to the local SQLite settings store
(src/utils/local_db). The settings that have runtime effects are applied on
save (detailed logging) or read where they matter (reassessment interval by
the results screen, export folder by the export dialogs).
"""

import os
import tkinter as tk

import customtkinter as ctk

from src.gui.screens.business_info import _header
from src.gui.theme import (
    BTN_H,
    BTN_R,
    CLR_ACCENT,
    CLR_ACCENT_HOV,
    CLR_BG,
    CLR_BORDER,
    CLR_DANGER,
    CLR_MUTED,
    CLR_SUCCESS,
    CLR_SURFACE,
    CLR_SURFACE_ALT,
    CLR_SURFACE_HVR,
    CLR_TEXT,
    CLR_TEXT_SEC,
    CLR_WARNING,
    FONT_BODY,
    FONT_CAPTION,
    FONT_SMALL,
    FONT_SUBHEAD,
    NAV_H,
    PAD,
)
from src.utils import local_db

# Setting key → default value
DEFAULTS = {
    "org_name": "",
    "org_industry": "",
    "org_province": "",
    "reassess_interval_days": "182",
    "detailed_logging": "false",
    "export_path": "",
}


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, master, on_back=None):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back or (lambda: None)
        self._entries: dict = {}     # key -> CTkEntry
        self._toggles: dict = {}     # key -> tk.BooleanVar
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        _header(self, "Settings & Configuration", "", 0.0)

        main = ctk.CTkFrame(self, fg_color=CLR_BG)
        main.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=PAD)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        # Tab buttons
        tabs = ctk.CTkFrame(main, fg_color="transparent")
        tabs.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self._tab_var = tk.StringVar(value="general")
        self._tab_btns = {}
        for name, tid in [("General", "general"),
                          ("Storage", "storage"),
                          ("Export", "export")]:
            btn = ctk.CTkButton(
                tabs, text=name, width=110,
                command=lambda t=tid: self._switch_tab(t),
                fg_color=CLR_SURFACE, hover_color=CLR_SURFACE_HVR,
                text_color=CLR_TEXT, font=FONT_BODY, height=BTN_H,
                border_width=0, corner_radius=BTN_R)
            btn.pack(side="left", padx=4)
            self._tab_btns[tid] = btn

        self._content = ctk.CTkFrame(main, fg_color=CLR_BG)
        self._content.grid(row=1, column=0, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)

        # Footer
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0,
                              height=NAV_H)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)

        ctk.CTkButton(
            footer, text="← Back", command=self._on_back,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            text_color=CLR_TEXT, font=FONT_BODY, height=BTN_H,
            corner_radius=BTN_R, width=100,
        ).pack(side="left", padx=PAD, pady=PAD)

        self._status_lbl = ctk.CTkLabel(footer, text="", font=FONT_SMALL,
                                        text_color=CLR_SUCCESS)
        self._status_lbl.pack(side="left", padx=8)

        self._save_btn = ctk.CTkButton(
            footer, text="💾  Save Settings", command=self._save_settings,
            fg_color=CLR_SUCCESS, hover_color="#2E8B57", text_color="#ffffff",
            font=FONT_SUBHEAD, height=BTN_H, corner_radius=BTN_R,
        )
        self._save_btn.pack(side="right", padx=PAD, pady=PAD)

        self._switch_tab("general")

    # ------------------------------------------------------------- tab switch
    def _switch_tab(self, tab_id):
        # Persist the tab we're leaving so edits aren't lost on switch, then
        # drop the stale widget references (they're about to be destroyed).
        self._persist_current()
        self._entries = {}
        self._toggles = {}

        self._tab_var.set(tab_id)
        for tid, btn in self._tab_btns.items():
            btn.configure(fg_color=CLR_ACCENT if tid == tab_id else CLR_SURFACE,
                          text_color="#000000" if tid == tab_id else CLR_TEXT)
        for w in self._content.winfo_children():
            w.destroy()
        # Save button only applies to editable tabs
        self._save_btn.configure(
            state="normal" if tab_id != "storage" else "disabled")
        if tab_id == "general":
            self._build_general_tab()
        elif tab_id == "storage":
            self._build_storage_tab()
        elif tab_id == "export":
            self._build_export_tab()

    def _scroll(self):
        sf = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        sf.pack(fill="both", expand=True)
        sf.grid_columnconfigure(0, weight=1)
        return sf

    # ------------------------------------------------------- section helpers
    def _section(self, parent, row, title):
        sec = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=10,
                           border_width=1, border_color=CLR_BORDER)
        sec.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        sec.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(sec, text=title, font=FONT_SUBHEAD, text_color=CLR_TEXT,
                     ).grid(row=0, column=0, columnspan=2, padx=16,
                            pady=(12, 10), sticky="w")
        return sec

    def _field(self, section, row, label, key, hint=""):
        ctk.CTkLabel(section, text=label, font=FONT_BODY, text_color=CLR_TEXT,
                     ).grid(row=row, column=0, padx=16, pady=8, sticky="w")
        entry = ctk.CTkEntry(
            section, fg_color=CLR_SURFACE_ALT, border_color=CLR_BORDER,
            border_width=1, text_color=CLR_TEXT, font=FONT_BODY, height=32,
            placeholder_text=hint)
        cur = local_db.get_setting(key, DEFAULTS.get(key, ""))
        if cur:
            entry.insert(0, cur)
        entry.grid(row=row, column=1, padx=16, pady=8, sticky="ew")
        self._entries[key] = entry
        return entry

    def _toggle(self, section, row, label, key):
        var = tk.BooleanVar(value=local_db.get_bool_setting(
            key, DEFAULTS.get(key, "false") == "true"))
        ctk.CTkSwitch(section, text=label, variable=var,
                      progress_color=CLR_ACCENT, text_color=CLR_TEXT,
                      font=FONT_BODY,
                      ).grid(row=row, column=0, columnspan=2, padx=16,
                             pady=8, sticky="w")
        self._toggles[key] = var

    # ------------------------------------------------------------- General tab
    def _build_general_tab(self):
        sf = self._scroll()

        org = self._section(sf, 0, "🏢 Organization defaults")
        ctk.CTkLabel(org, text="Pre-fills the business details when you start "
                     "a new assessment.", font=FONT_CAPTION, text_color=CLR_MUTED,
                     ).grid(row=0, column=0, columnspan=2, padx=16,
                            pady=(30, 6), sticky="w")
        self._field(org, 1, "Organization name", "org_name",
                    "e.g. Acme Ltd")
        self._field(org, 2, "Industry", "org_industry", "e.g. Retail")
        self._field(org, 3, "Province", "org_province", "e.g. Lusaka")

        assess = self._section(sf, 1, "📋 Assessment")
        self._field(assess, 1, "Reassessment reminder (days)",
                    "reassess_interval_days", "182")
        self._toggle(assess, 2, "Enable detailed (debug) logging",
                     "detailed_logging")

    # ------------------------------------------------------------- Storage tab
    def _build_storage_tab(self):
        sf = self._scroll()

        sec = self._section(sf, 0, "🗄️ Local database (self-contained SQLite)")
        path = local_db.db_location()
        try:
            assessments = local_db.assessment_count()
            agents = local_db.agent_report_count()
            fleets = local_db.fleet_report_count()
        except Exception:
            assessments = agents = fleets = 0

        rows = [
            ("Location", path),
            ("Saved assessments", str(assessments)),
            ("Agent reports", str(agents)),
            ("Fleet reports", str(fleets)),
        ]
        for i, (label, value) in enumerate(rows, start=1):
            ctk.CTkLabel(sec, text=label, font=FONT_BODY, text_color=CLR_TEXT_SEC,
                         ).grid(row=i, column=0, padx=16, pady=6, sticky="w")
            ctk.CTkLabel(sec, text=value, font=FONT_SMALL, text_color=CLR_TEXT,
                         anchor="w", wraplength=520, justify="left",
                         ).grid(row=i, column=1, padx=16, pady=6, sticky="w")

        actions = ctk.CTkFrame(sec, fg_color="transparent")
        actions.grid(row=len(rows) + 1, column=0, columnspan=2, padx=16,
                     pady=(6, 14), sticky="w")
        ctk.CTkButton(
            actions, text="📂  Open data folder", command=self._open_folder,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            text_color=CLR_TEXT, border_color=CLR_BORDER, border_width=1,
            font=FONT_SMALL, height=32, corner_radius=BTN_R, width=170,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            actions, text="🗑  Clear history", command=self._confirm_clear,
            fg_color="transparent", hover_color=CLR_SURFACE_HVR,
            text_color=CLR_DANGER, border_color=CLR_DANGER, border_width=1,
            font=FONT_SMALL, height=32, corner_radius=BTN_R, width=150,
        ).pack(side="left")

        ctk.CTkLabel(
            sf, text="This is the self-contained store used by the desktop "
            "app — no server required. Credentials and settings are kept when "
            "you clear history.",
            font=FONT_CAPTION, text_color=CLR_MUTED, wraplength=640,
            justify="left", anchor="w",
        ).grid(row=1, column=0, padx=4, pady=(0, 8), sticky="w")

    # -------------------------------------------------------------- Export tab
    def _build_export_tab(self):
        sf = self._scroll()
        sec = self._section(sf, 0, "📁 Export")
        entry = self._field(sec, 1, "Default export folder", "export_path",
                            "Choose where reports are saved by default")
        ctk.CTkButton(
            sec, text="Browse…", command=lambda e=entry: self._browse_folder(e),
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
            text_color=CLR_TEXT, border_color=CLR_BORDER, border_width=1,
            font=FONT_SMALL, height=32, corner_radius=BTN_R, width=90,
        ).grid(row=2, column=1, padx=16, pady=(0, 12), sticky="w")
        ctk.CTkLabel(
            sf, text="When set, the Save dialogs for reports open at this "
            "folder by default.",
            font=FONT_CAPTION, text_color=CLR_MUTED, wraplength=640,
            justify="left", anchor="w",
        ).grid(row=1, column=0, padx=4, sticky="w")

    # ----------------------------------------------------------------- actions
    def _browse_folder(self, entry):
        from tkinter import filedialog
        d = filedialog.askdirectory(title="Default export folder")
        if d:
            entry.delete(0, "end")
            entry.insert(0, d)

    def _open_folder(self):
        folder = os.path.dirname(local_db.db_location())
        try:
            os.startfile(folder)  # type: ignore[attr-defined]
        except AttributeError:
            import subprocess
            subprocess.Popen(["xdg-open", folder])
        except Exception:
            import logging
            logging.getLogger(__name__).warning(
                "could not open database folder", exc_info=True)

    def _confirm_clear(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Clear history")
        dlg.geometry("420x180")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text="⚠  Clear all saved history?",
                     font=FONT_SUBHEAD, text_color=CLR_WARNING,
                     ).pack(pady=(22, 6))
        ctk.CTkLabel(
            dlg, text="This permanently deletes all saved assessments, agent "
            "reports and fleet reports. Your login and settings are kept.",
            font=FONT_SMALL, text_color=CLR_TEXT_SEC, wraplength=370,
            justify="center").pack(pady=(0, 14), padx=16)
        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack()
        ctk.CTkButton(btns, text="Cancel", command=dlg.destroy,
                      fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
                      text_color=CLR_TEXT, height=BTN_H, corner_radius=BTN_R,
                      width=120).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="Clear history",
                      command=lambda: self._do_clear(dlg),
                      fg_color=CLR_DANGER, hover_color="#B22222",
                      text_color="#ffffff", height=BTN_H, corner_radius=BTN_R,
                      width=140).pack(side="left", padx=6)

    def _do_clear(self, dlg):
        try:
            local_db.clear_history()
        except Exception:
            import logging
            logging.getLogger(__name__).warning(
                "could not clear assessment history", exc_info=True)
        dlg.destroy()
        self._switch_tab("storage")   # refresh counts
        self._flash("History cleared.")

    def _persist_current(self):
        """Write the currently-shown tab's fields to the settings store.

        Safe to call when a tab has no editable fields (no-op) or when its
        widgets have already been torn down (guarded).
        """
        for key, entry in list(self._entries.items()):
            try:
                value = entry.get().strip()
            except Exception:
                continue
            if key == "reassess_interval_days":
                try:
                    days = int(value) if value else int(DEFAULTS[key])
                    value = str(max(1, min(days, 3650)))
                except ValueError:
                    value = DEFAULTS[key]
            local_db.set_setting(key, value)

        for key, var in list(self._toggles.items()):
            try:
                local_db.set_setting(key, "true" if var.get() else "false")
            except Exception:
                continue

    def _save_settings(self):
        self._persist_current()
        # Apply effects that take hold immediately
        self._apply_logging()
        self._flash("Settings saved ✓")

    def _apply_logging(self):
        import logging
        detailed = local_db.get_bool_setting("detailed_logging", False)
        logging.getLogger("zambia_digital_hygiene").setLevel(
            logging.DEBUG if detailed else logging.INFO)

    def _flash(self, msg):
        self._status_lbl.configure(text=msg)
        self.after(2600, lambda: self._status_lbl.configure(text=""))
