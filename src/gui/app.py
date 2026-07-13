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

        # Fit and centre the window within the usable work area (excludes the
        # taskbar). On small screens or high-DPI scaling (125%/150% laptops)
        # a fixed 1060x700 window overflows the screen and hides the bottom
        # navigation bar, so clamp the size to what actually fits.
        self.update_idletasks()
        import sys
        if sys.platform == "win32":
            import ctypes
            import ctypes.wintypes
            wa = ctypes.wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(wa), 0)
            work_x, work_y = wa.left, wa.top
            work_w = wa.right  - wa.left
            work_h = wa.bottom - wa.top
        else:
            work_x = work_y = 0
            work_w = self.winfo_screenwidth()
            work_h = self.winfo_screenheight()

        # customtkinter multiplies geometry sizes by the DPI scaling factor,
        # so convert the physical work area into logical units before
        # clamping (leave room for the OS title bar).
        try:
            scale = float(self._get_window_scaling())
        except Exception:
            scale = 1.0
        titlebar = int(36 * scale)
        win_w = min(WIN_W, int(work_w / scale))
        win_h = min(WIN_H, int((work_h - titlebar) / scale))
        x = work_x + max(0, (work_w - int(win_w * scale)) // 2)
        y = work_y + max(0, (work_h - titlebar - int(win_h * scale)) // 2)
        self.minsize(min(800, win_w), min(560, win_h))
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")

        # Soft fade-in instead of popping onto the screen
        from src.gui import motion
        motion.enable_global_smooth_scroll()
        motion.fade_in_window(self, duration_ms=260)

        # Single source of truth for wizard data + the navigation stack
        self.app_state = AppState()
        self.router = Router(self)

        # Apply the saved logging-verbosity preference
        try:
            import logging
            from src.utils.local_db import get_bool_setting
            logging.getLogger("zambia_digital_hygiene").setLevel(
                logging.DEBUG if get_bool_setting("detailed_logging", False)
                else logging.INFO)
        except Exception:
            import logging
            logging.getLogger(__name__).debug(
                "could not apply detailed-logging setting", exc_info=True)

        # Register any certificates left provisional while offline, now that
        # the app is up and the portal may be reachable again. Background +
        # best-effort: it only touches the local DB, never the UI, and stays
        # silent if still offline.
        self._sync_provisional_certificates_bg()

        # Route through auth before showing the app
        from src.utils.auth import is_setup
        if is_setup():
            # Show the lock screen, then bring up the sign-in dialog over it.
            self._show_lock(ended=False)
            self._start_session()
        else:
            self._show_setup()

    def _sync_provisional_certificates_bg(self):
        """Best-effort background registration of offline-provisional certs."""
        def _run():
            try:
                from src.utils.cert_client import sync_provisional_certificates
                sync_provisional_certificates()
            except Exception:
                import logging
                logging.getLogger(__name__).debug(
                    "provisional certificate sync failed", exc_info=True)
        import threading
        threading.Thread(target=_run, daemon=True).start()

    # ─────────────────────────────────────── auth / session screens
    def _show_setup(self):
        from src.gui.screens.setup_screen import SetupScreen
        # First run: creating credentials also authenticates the operator.
        self.router.reset_to(
            "setup",
            lambda: SetupScreen(self, on_done=self._on_authenticated))

    def _show_lock(self, ended: bool = False):
        """Show the locked state (no active session)."""
        from src.gui.screens.session_lock import SessionLockScreen
        self.router.reset_to(
            "session_lock",
            lambda: SessionLockScreen(
                self,
                on_start_session=self._start_session,
                on_exit=self.destroy,
                ended=ended,
            ))

    def _start_session(self):
        """Authenticate the user via the sign-in dialog."""
        from src.gui.screens.login_screen import LoginScreen
        # Modal popup over the lock screen. Cancelling returns to the lock
        # screen (already shown) rather than exiting the app.
        LoginScreen(self, on_success=self._on_authenticated,
                    on_cancel=lambda: None)

    def _on_authenticated(self):
        """Called once the operator has signed in — open a clean session."""
        from src.utils.auth import get_username
        self.app_state.start_session(get_username())
        self._show_welcome()
        # Offer to relaunch elevated if we're not admin (once per process).
        self.after(600, self._maybe_show_admin_banner)

    def _maybe_show_admin_banner(self):
        """Show the elevation banner when running unelevated on Windows."""
        if getattr(self, "_admin_banner_shown", False):
            return
        from src.gui.screens.admin_banner import (
            AdminBanner, should_offer_elevation, relaunch_as_admin)
        if not should_offer_elevation():
            return
        self._admin_banner_shown = True

        def _do_relaunch():
            if relaunch_as_admin():
                self.after(150, self.destroy)  # hand off to elevated instance
                return True
            return False

        banner = AdminBanner(self, on_relaunch=_do_relaunch)
        banner.reveal(before=self.router._current_widget)

    def _terminate_session(self):
        """Ask to confirm, then end the session and lock the app."""
        self._confirm_terminate()

    def _do_terminate(self):
        """Tear down the session: wipe all state and return to the lock."""
        self.app_state.end_session()
        self._show_lock(ended=True)

    def _confirm_terminate(self):
        """Confirmation dialog for signing out."""
        from src.gui.theme import (
            CLR_SURFACE, CLR_SURFACE_ALT, CLR_SURFACE_HVR, CLR_WARNING,
            CLR_TEXT, CLR_TEXT_SEC, CLR_DANGER, BTN_H, BTN_R,
            FONT_SUBHEAD, FONT_SMALL,
        )
        in_progress = self.app_state.has_active_assessment()
        dlg = ctk.CTkToplevel(self)
        dlg.title("End session")
        dlg.geometry("420x190")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        dlg.transient(self)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text="⏻  End your session?",
                     font=FONT_SUBHEAD, text_color=CLR_WARNING,
                     ).pack(pady=(22, 6))
        msg = ("You'll need to sign in again to continue. All in-memory data "
               "is cleared when you sign out.")
        if in_progress:
            msg = ("You have an assessment in progress that will be discarded. "
                   + msg)
        ctk.CTkLabel(dlg, text=msg, font=FONT_SMALL, text_color=CLR_TEXT_SEC,
                     wraplength=370, justify="center",
                     ).pack(pady=(0, 16), padx=16)
        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack()
        ctk.CTkButton(btns, text="Cancel", command=dlg.destroy,
                      fg_color=CLR_SURFACE_ALT, hover_color=CLR_SURFACE_HVR,
                      text_color=CLR_TEXT, height=BTN_H, corner_radius=BTN_R,
                      width=130).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="⏻  End session",
                      command=lambda: (dlg.destroy(), self._do_terminate()),
                      fg_color=CLR_DANGER, hover_color="#B22222",
                      text_color="#ffffff", height=BTN_H, corner_radius=BTN_R,
                      width=150).pack(side="left", padx=6)

    # ─────────────────────────────────────── home
    def _show_welcome(self):
        """Return to the home screen — clears the nav stack and wizard state."""
        self.app_state.reset_assessment()
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
            on_logout=self._terminate_session,
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
            lambda: AssessmentDashboardScreen(self, on_back=self.router.back,
                                              on_new=self._start_assessment))

    # ─────────────────────────────────────── assessment wizard
    # business_info → tools → scanning → manual → results
    # Each step stores its output in ``self.app_state`` and pushes the next
    # step; "back" pops through the stack automatically.

    def _start_assessment(self):
        """Begin a fresh assessment from the home screen."""
        self.app_state.reset_assessment()
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
        self.app_state.business_info = business_info
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
        self.app_state.selected_tools = selected_tools or set()
        self._show_scanning()

    def _show_scanning(self):
        from src.gui.screens.scanning import ScanningScreen
        self.router.push(
            "scanning",
            lambda: ScanningScreen(
                self,
                business_info=self.app_state.business_info,
                on_next=self._on_scanning_done,
                on_back=self.router.back,
                on_skip=self._on_scanning_skip,
            ))

    def _on_scanning_done(self, auto_results):
        self.app_state.auto_results = auto_results or {}
        self._show_manual()

    def _on_scanning_skip(self, auto_results):
        """Skip the manual questions — C06-C15 stay NOT_ASSESSED."""
        self.app_state.auto_results = auto_results or {}
        self.app_state.manual_scores = {}
        self.app_state.evidence = {}
        self._show_results()

    def _show_manual(self):
        from src.gui.screens.manual_checks import ManualChecksScreen
        self.router.push(
            "manual_checks",
            lambda: ManualChecksScreen(
                self,
                selected_tools=self.app_state.selected_tools,
                on_next=self._on_manual_done,
                on_back=self.router.back,
            ))

    def _on_manual_done(self, manual_scores, evidence=None):
        self.app_state.manual_scores = manual_scores or {}
        self.app_state.evidence = evidence or {}
        self._show_results()

    def _show_results(self):
        # Certification must never crash the app. If assembling the results
        # fails, tell the user plainly and keep them on the wizard so their
        # answers aren't lost, rather than leaving a blank window.
        try:
            results = self.app_state.build_results()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).exception("Failed to build results")
            self._show_certify_error(exc)
            return
        from src.gui.screens.results import ResultsScreen
        self.router.push(
            "results",
            lambda: ResultsScreen(
                self,
                results=results,
                on_restart=self._show_welcome,
            ))

    def _show_certify_error(self, exc):
        """Show a recoverable dialog when results can't be assembled."""
        import customtkinter as ctk
        from src.gui.theme import (
            CLR_SURFACE, CLR_WARNING, CLR_TEXT_SEC, CLR_ACCENT, BTN_H, BTN_R,
            FONT_SUBHEAD, FONT_SMALL,
        )
        try:
            dlg = ctk.CTkToplevel(self)
            dlg.title("Could not complete assessment")
            dlg.geometry("460x190")
            dlg.resizable(False, False)
            dlg.configure(fg_color=CLR_SURFACE)
            dlg.grab_set()
            ctk.CTkLabel(dlg, text="⚠  Could not complete the assessment",
                         font=FONT_SUBHEAD, text_color=CLR_WARNING,
                         ).pack(pady=(22, 6))
            ctk.CTkLabel(
                dlg,
                text="Something went wrong while scoring your answers. "
                     "Your inputs are still here — you can go back and try "
                     "again.\n\n" + str(exc)[:200],
                font=FONT_SMALL, text_color=CLR_TEXT_SEC, wraplength=410,
                justify="left").pack(pady=(0, 14), padx=16)
            ctk.CTkButton(dlg, text="OK", fg_color=CLR_ACCENT,
                          text_color="#FFFFFF", height=BTN_H,
                          corner_radius=BTN_R, command=dlg.destroy).pack()
        except Exception:
            # Even the dialog failed — fall back to going home.
            self._show_welcome()
