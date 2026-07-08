"""Main application window.

The window is a thin navigation controller: it owns a :class:`Router`
(the navigation stack) and an :class:`AppState` (the wizard's data), and
each ``_show_*`` method just registers a screen factory with the router.
Screens are unaware of the router — they still receive plain ``on_next`` /
``on_back`` callbacks, so no screen needed to change.
"""

import customtkinter as ctk

from src.gui.router import Router
from src.gui.state import AppState
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
            import ctypes
            import ctypes.wintypes
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

        # Single source of truth for wizard data + the navigation stack
        self.state = AppState()
        self.router = Router(self)

        # Route through auth before showing the app
        from src.utils.auth import is_setup
        if is_setup():
            self._show_login()
        else:
            self._show_setup()

    # ─────────────────────────────────────── auth screens
    def _show_setup(self):
        from src.gui.screens.setup_screen import SetupScreen
        self.router.reset_to(
            "setup",
            lambda: SetupScreen(self, on_done=self._show_welcome))

    def _show_login(self):
        from src.gui.screens.login_screen import LoginScreen
        # Popup dialog — sits on top of the empty main window, not routed
        LoginScreen(self, on_success=self._show_welcome)

    # ─────────────────────────────────────── home
    def _show_welcome(self):
        """Return to the home screen — clears the nav stack and wizard state."""
        self.state.reset_assessment()
        self.router.reset_to("welcome", self._make_welcome)

    def _make_welcome(self):
        from src.gui.screens.welcome import WelcomeScreen
        return WelcomeScreen(
            self,
            on_start=self._start_assessment,
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
            on_hardening=self._show_server_hardening,
            on_fleet=self._show_fleet_scan,
        )

    # ─────────────────────────────────────── standalone tools
    # Each tool is pushed onto the stack; "back" pops it via the router,
    # so the screens no longer need to know they came from welcome.
    def _push_tool(self, name, factory):
        self.router.push(name, factory)

    def _show_history(self):
        from src.gui.screens.history import HistoryScreen
        self._push_tool(
            "history",
            lambda: HistoryScreen(self, on_back=self.router.back))

    def _show_infra_scanner(self):
        from src.gui.screens.infra_scanner import InfraScannerScreen
        self._push_tool(
            "infra_scanner",
            lambda: InfraScannerScreen(self, on_back=self.router.back))

    def _show_zambia_risk(self):
        from src.gui.screens.zambia_risk import ZambiaRiskScreen
        self._push_tool(
            "zambia_risk",
            lambda: ZambiaRiskScreen(self, on_back=self.router.back))

    def _show_policy_templates(self):
        from src.gui.screens.policy_templates import PolicyTemplatesScreen
        self._push_tool(
            "policy_templates",
            lambda: PolicyTemplatesScreen(self, on_back=self.router.back))

    def _show_network_scanner(self):
        from src.gui.screens.network_scanner import NetworkScannerScreen
        self._push_tool(
            "network_scanner",
            lambda: NetworkScannerScreen(self, on_back=self.router.back))

    def _show_deployment_checker(self):
        from src.gui.screens.deployment_screen import DeploymentCheckerScreen
        self._push_tool(
            "deployment_checker",
            lambda: DeploymentCheckerScreen(self, on_back=self.router.back))

    def _show_remediation_guidance(self):
        from src.gui.screens.remediation_guidance import RemediationGuidanceScreen
        self._push_tool(
            "remediation_guidance",
            lambda: RemediationGuidanceScreen(self, on_back=self.router.back))

    def _show_active_directory(self):
        from src.gui.screens.active_directory import ActiveDirectoryScreen
        self._push_tool(
            "active_directory",
            lambda: ActiveDirectoryScreen(self, on_back=self.router.back))

    def _show_export_reports(self):
        from src.gui.screens.export_reports import ExportReportsScreen
        self._push_tool(
            "export_reports",
            lambda: ExportReportsScreen(self, on_back=self.router.back))

    def _show_audit_logs(self):
        from src.gui.screens.audit_log_viewer import AuditLogViewerScreen
        self._push_tool(
            "audit_logs",
            lambda: AuditLogViewerScreen(self, on_back=self.router.back))

    def _show_settings(self):
        from src.gui.screens.settings import SettingsScreen
        self._push_tool(
            "settings",
            lambda: SettingsScreen(self, on_back=self.router.back))

    def _show_server_hardening(self):
        from src.gui.screens.server_hardening import ServerHardeningScreen
        self._push_tool(
            "server_hardening",
            lambda: ServerHardeningScreen(self, on_back=self.router.back))

    def _show_fleet_scan(self):
        from src.gui.screens.fleet_scan import FleetScanScreen
        self._push_tool(
            "fleet_scan",
            lambda: FleetScanScreen(self, on_back=self.router.back))

    def _show_assessment_dashboard(self):
        from src.gui.screens.assessment_dashboard import AssessmentDashboardScreen
        self._push_tool(
            "assessment_dashboard",
            lambda: AssessmentDashboardScreen(self, on_back=self.router.back))

    # ─────────────────────────────────────── assessment wizard
    # business_info → tools → scanning → manual → results
    # Each step stores its output in ``self.state`` and pushes the next
    # step; "back" pops through the stack automatically.

    def _start_assessment(self):
        """Begin a fresh assessment from the home screen."""
        self.state.reset_assessment()
        self._show_business_info()

    def _show_business_info(self):
        from src.gui.screens.business_info import BusinessInfoScreen
        self.router.push(
            "business_info",
            lambda: BusinessInfoScreen(
                self,
                on_next=self._on_business_info_done,
                on_back=self.router.back,
            ))

    def _on_business_info_done(self, business_info):
        self.state.business_info = business_info
        self._show_tools_profile()

    def _show_tools_profile(self):
        from src.gui.screens.tools_profile import ToolsProfileScreen
        self.router.push(
            "tools_profile",
            lambda: ToolsProfileScreen(
                self,
                on_next=self._on_tools_done,
                on_back=self.router.back,
            ))

    def _on_tools_done(self, selected_tools=None):
        self.state.selected_tools = selected_tools or set()
        self._show_scanning()

    def _show_scanning(self):
        from src.gui.screens.scanning import ScanningScreen
        self.router.push(
            "scanning",
            lambda: ScanningScreen(
                self,
                business_info=self.state.business_info,
                on_next=self._on_scanning_done,
                on_back=self.router.back,
                on_skip=self._on_scanning_skip,
            ))

    def _on_scanning_done(self, auto_results):
        self.state.auto_results = auto_results or {}
        self._show_manual()

    def _on_scanning_skip(self, auto_results):
        """Skip the manual questions — C06-C15 stay NOT_ASSESSED."""
        self.state.auto_results = auto_results or {}
        self.state.manual_scores = {}
        self.state.evidence = {}
        self._show_results()

    def _show_manual(self):
        from src.gui.screens.manual_checks import ManualChecksScreen
        self.router.push(
            "manual_checks",
            lambda: ManualChecksScreen(
                self,
                selected_tools=self.state.selected_tools,
                on_next=self._on_manual_done,
                on_back=self.router.back,
            ))

    def _on_manual_done(self, manual_scores, evidence=None):
        self.state.manual_scores = manual_scores or {}
        self.state.evidence = evidence or {}
        self._show_results()

    def _show_results(self):
        results = self.state.build_results()
        from src.gui.screens.results import ResultsScreen
        self.router.push(
            "results",
            lambda: ResultsScreen(
                self,
                results=results,
                on_restart=self._show_welcome,
            ))
