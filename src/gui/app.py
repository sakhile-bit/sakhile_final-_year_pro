"""Main application window — manages screen transitions."""

import customtkinter as ctk
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_ACCENT, CLR_TEXT,
    WIN_W, WIN_H, APP_NAME, APP_VERSION,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class DigitalHygieneApp(ctk.CTk):
    """Root window that hosts all screens."""

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  v{APP_VERSION}")
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.minsize(800, 560)
        self.configure(fg_color=CLR_BG)

        # Centre the window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - WIN_W) // 2
        y = (self.winfo_screenheight() - WIN_H) // 2
        self.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")

        self._business_info = None
        self._auto_results = {}

        self._current_screen = None
        self._show_welcome()

    # ─────────────────────────────────────── screen management
    def _swap(self, screen):
        if self._current_screen is not None:
            self._current_screen.destroy()
        self._current_screen = screen
        screen.pack(fill="both", expand=True)

    # ─────────────────────────────────────── screens
    def _show_welcome(self):
        from src.gui.screens.welcome import WelcomeScreen
        self._swap(WelcomeScreen(self, on_start=self._show_business_info))

    def _show_business_info(self):
        from src.gui.screens.business_info import BusinessInfoScreen
        self._swap(BusinessInfoScreen(
            self,
            on_next=self._show_scanning,
            on_back=self._show_welcome,
        ))

    def _show_scanning(self, business_info):
        self._business_info = business_info
        from src.gui.screens.scanning import ScanningScreen
        self._swap(ScanningScreen(
            self,
            business_info=business_info,
            on_next=self._show_manual,
            on_back=self._show_business_info,
        ))

    def _show_manual(self, auto_results):
        self._auto_results = auto_results
        from src.gui.screens.manual_checks import ManualChecksScreen
        self._swap(ManualChecksScreen(
            self,
            on_next=self._show_results,
            on_back=lambda: self._show_scanning(self._business_info),
        ))

    def _show_results(self, manual_scores):
        from src.security.assessment.assessor import (
            DigitalHygieneAssessor, ControlResult, CONTROL_CATALOGUE,
        )

        # Merge automated results + manual scores into a full assessment
        assessor = DigitalHygieneAssessor(
            self._business_info,
            manual_answers=manual_scores,
            assessment_tier="full",
        )
        # Patch in the already-computed automated results
        results = assessor.run_assessment()
        for cid_key, ctrl_result in self._auto_results.items():
            full_key = f"C0{cid_key[-1]}_" + {
                "C01": "os_updates",
                "C02": "antivirus",
                "C03": "firewall",
                "C04": "password_policy",
                "C05": "backups",
            }.get(cid_key, cid_key)
            if full_key in results.controls:
                results.controls[full_key] = ctrl_result

        # Re-calculate totals
        results.score = sum(c.score for c in results.controls.values())
        pct = (results.score / results.total_possible) * 100 if results.total_possible else 0
        critical_failures = sum(
            1 for k, v in results.controls.items()
            if CONTROL_CATALOGUE.get(k, {}).get("critical") and v.status == "FAIL"
        )
        results.critical_failures = critical_failures
        if pct >= 80 and critical_failures == 0:
            results.certification_level = "GOLD"
        elif pct >= 60 and critical_failures <= 1:
            results.certification_level = "SILVER"
        elif pct >= 40 and critical_failures <= 2:
            results.certification_level = "BRONZE"
        else:
            results.certification_level = "NOT CERTIFIED"

        from src.gui.screens.results import ResultsScreen
        self._swap(ResultsScreen(
            self,
            results=results,
            on_restart=self._show_welcome,
        ))
