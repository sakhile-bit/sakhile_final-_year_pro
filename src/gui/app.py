"""Main application window — manages screen transitions."""

import customtkinter as ctk

from src.gui.theme import APP_NAME, APP_VERSION, CLR_BG, WIN_H, WIN_W

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

        # Centre the window within the usable work area (excludes taskbar)
        self.update_idletasks()
        import sys
        if sys.platform == "win32":
            import ctypes, ctypes.wintypes
            wa = ctypes.wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(wa), 0)
            work_w = wa.right  - wa.left
            work_h = wa.bottom - wa.top
            x = wa.left + max(0, (work_w - WIN_W) // 2)
            y = wa.top  + max(0, (work_h - WIN_H) // 2)
        else:
            x = (self.winfo_screenwidth()  - WIN_W) // 2
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
        self._swap(WelcomeScreen(
            self,
            on_start=self._show_business_info,
            on_history=self._show_history,
            on_infra=self._show_infra_scanner,
            on_zambia_risk=self._show_zambia_risk,
            on_policies=self._show_policy_templates,
            on_network=self._show_network_scanner,
            on_deploy=self._show_deployment_checker,
            on_remediation=self._show_remediation_guidance,
            on_active_dir=self._show_active_directory,
            on_export=self._show_export_reports,
            on_audit=self._show_audit_logs,
            on_settings=self._show_settings,
            on_dashboard=self._show_assessment_dashboard,
        ))

    def _show_history(self):
        from src.gui.screens.history import HistoryScreen
        self._swap(HistoryScreen(self, on_back=self._show_welcome))

    def _show_infra_scanner(self):
        from src.gui.screens.infra_scanner import InfraScannerScreen
        self._swap(InfraScannerScreen(self, on_back=self._show_welcome))

    def _show_zambia_risk(self):
        from src.gui.screens.zambia_risk import ZambiaRiskScreen
        self._swap(ZambiaRiskScreen(self, on_back=self._show_welcome))

    def _show_policy_templates(self):
        from src.gui.screens.policy_templates import PolicyTemplatesScreen
        self._swap(PolicyTemplatesScreen(self, on_back=self._show_welcome))

    def _show_network_scanner(self):
        from src.gui.screens.network_scanner import NetworkScannerScreen
        self._swap(NetworkScannerScreen(self, on_back=self._show_welcome))

    def _show_deployment_checker(self):
        from src.gui.screens.deployment_screen import DeploymentCheckerScreen
        self._swap(DeploymentCheckerScreen(self, on_back=self._show_welcome))

    def _show_remediation_guidance(self):
        from src.gui.screens.remediation_guidance import RemediationGuidanceScreen
        self._swap(RemediationGuidanceScreen(self, on_back=self._show_welcome))

    def _show_active_directory(self):
        from src.gui.screens.active_directory import ActiveDirectoryScreen
        self._swap(ActiveDirectoryScreen(self, on_back=self._show_welcome))

    def _show_export_reports(self):
        from src.gui.screens.export_reports import ExportReportsScreen
        self._swap(ExportReportsScreen(self, on_back=self._show_welcome))

    def _show_audit_logs(self):
        from src.gui.screens.audit_log_viewer import AuditLogViewerScreen
        self._swap(AuditLogViewerScreen(self, on_back=self._show_welcome))

    def _show_settings(self):
        from src.gui.screens.settings import SettingsScreen
        self._swap(SettingsScreen(self, on_back=self._show_welcome))

    def _show_assessment_dashboard(self):
        from src.gui.screens.assessment_dashboard import AssessmentDashboardScreen
        self._swap(AssessmentDashboardScreen(self, on_back=self._show_welcome))

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
            on_skip=self._show_quick_results,
        ))

    def _show_manual(self, auto_results):
        self._auto_results = auto_results
        from src.gui.screens.manual_checks import ManualChecksScreen
        self._swap(ManualChecksScreen(
            self,
            on_next=self._show_results,
            on_back=lambda: self._show_scanning(self._business_info),  # type: ignore[arg-type]
        ))

    def _show_quick_results(self, auto_results):
        """Skip manual questions — score C06-C15 as NOT_ASSESSED."""
        self._auto_results = auto_results
        self._show_results({}, {})

    def _show_results(self, manual_scores, evidence=None):
        from src.security.assessment.assessor import (
            CONTROL_CATALOGUE,
            DigitalHygieneAssessor,
        )

        # Merge automated results + manual scores into a full assessment
        assert self._business_info is not None, "business_info must be set before showing results"
        assessor = DigitalHygieneAssessor(
            self._business_info,
            manual_answers=manual_scores,
            assessment_tier="full",
        )
        # Patch in the already-computed automated results
        results = assessor.run_assessment()
        for cid_key, ctrl_result in self._auto_results.items():
            _suffix: str = {
                "C01": "os_updates",
                "C02": "antivirus",
                "C03": "firewall",
                "C04": "password_policy",
                "C05": "backups",
            }.get(cid_key) or cid_key
            full_key = f"C0{cid_key[-1]}_" + _suffix
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
