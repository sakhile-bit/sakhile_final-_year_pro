"""
Application state — single source of truth for the assessment wizard.

Previously the wizard's data (business info, selected tools, automated
results, manual answers) lived as loose attributes on the main window and
was never reset between runs, so a second assessment could inherit stale
data from the first. ``AppState`` centralises that data, gives it a clear
reset point, and owns the logic that assembles a finished assessment from
the collected wizard inputs.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Automated control id (as produced by the scanning screen) → catalogue suffix
_AUTO_CONTROL_SUFFIX = {
    "C01": "os_updates",
    "C02": "antivirus",
    "C03": "firewall",
    "C04": "password_policy",
    "C05": "backups",
}


@dataclass
class AppState:
    """The app's in-memory state: the current session + the wizard's data.

    A single instance lives for the whole run. Because it is reused across
    sign-ins, ``end_session`` wipes *everything* so one operator's data can
    never bleed into the next session on the same machine.
    """

    # ── Session ───────────────────────────────────────────────────────
    authenticated: bool = False
    username: str = ""
    session_started: Optional[datetime.datetime] = None

    # ── Assessment wizard ─────────────────────────────────────────────
    business_info: Optional[Any] = None
    selected_tools: Set[str] = field(default_factory=set)
    auto_results: Dict[str, Any] = field(default_factory=dict)
    manual_scores: Dict[str, int] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)

    # ── Session lifecycle ─────────────────────────────────────────────
    def start_session(self, username: str) -> None:
        """Begin an authenticated session with a clean slate."""
        self.reset_assessment()
        self.authenticated = True
        self.username = username or ""
        self.session_started = datetime.datetime.now()
        logger.info("Session started (%s)", self.username or "user")

    def end_session(self) -> None:
        """Tear the session down and wipe ALL in-memory state.

        After this the app holds nothing about the previous operator or their
        assessment — the next person must sign in and starts fresh.
        """
        who = self.username or "user"
        self.reset_assessment()
        self.authenticated = False
        self.username = ""
        self.session_started = None
        logger.info("Session ended (%s)", who)

    def has_active_assessment(self) -> bool:
        """True once the operator has started entering an assessment."""
        return self.business_info is not None

    def session_duration(self) -> Optional[datetime.timedelta]:
        if self.session_started is None:
            return None
        return datetime.datetime.now() - self.session_started

    # ── Assessment wizard ─────────────────────────────────────────────
    def reset_assessment(self) -> None:
        """Clear all wizard data so the next assessment starts clean."""
        self.business_info = None
        self.selected_tools = set()
        self.auto_results = {}
        self.manual_scores = {}
        self.evidence = {}
        logger.debug("Assessment state reset")

    # ------------------------------------------------------------------
    def _clean_manual_scores(self) -> Dict[str, int]:
        """Coerce manual answers to safe ints so scoring can't crash.

        UI widgets can hand back strings or ``None``; a stray value would
        otherwise blow up deep inside the assessor while certifying.
        """
        clean: Dict[str, int] = {}
        for key, raw in (self.manual_scores or {}).items():
            try:
                clean[key] = int(raw)
            except (TypeError, ValueError):
                logger.warning("Dropping non-numeric manual score for %s: %r",
                               key, raw)
        return clean

    @staticmethod
    def _looks_like_control(obj) -> bool:
        return all(hasattr(obj, attr) for attr in ("score", "status", "weight"))

    def build_results(self):
        """Assemble a finished ``AssessmentResults`` from wizard inputs.

        Runs the assessor with the collected business info, selected tools
        and manual answers, patches in the automated control results
        captured live on the scanning screen, then recomputes the headline
        score / critical count / certification tier.

        The method is defensive on every input the UI feeds it — bad manual
        scores, malformed automated results, controls missing a score — so
        the certification step can never crash the app, and it records the
        integrity of the underlying data so an unverifiable result is
        surfaced as *provisional* rather than silently certified.

        Keeping this here means the navigation controller only decides
        *where to go*, not *how an assessment is scored*.
        """
        from src.security.assessment.assessor import (
            CONTROL_CATALOGUE,
            DigitalHygieneAssessor,
            assessment_integrity,
            certification_for,
        )

        if self.business_info is None:
            raise ValueError("business_info must be set before building results")

        assessor = DigitalHygieneAssessor(
            self.business_info,
            manual_answers=self._clean_manual_scores(),
            assessment_tier="full",
            selected_tools=self.selected_tools,
        )
        results = assessor.run_assessment()

        # Patch in the automated results captured live on the scanning screen,
        # ignoring anything that doesn't look like a real ControlResult.
        for cid_key, ctrl_result in (self.auto_results or {}).items():
            suffix = _AUTO_CONTROL_SUFFIX.get(cid_key)
            full_key = f"{cid_key}_{suffix}" if suffix else cid_key
            if full_key not in results.controls:
                continue
            if not self._looks_like_control(ctrl_result):
                logger.warning("Ignoring malformed automated result for %s",
                               full_key)
                continue
            results.controls[full_key] = ctrl_result

        # Recompute headline figures from the merged control set. Use getattr
        # defaults so a single odd control can't abort certification.
        results.score = sum(int(getattr(c, "score", 0) or 0)
                            for c in results.controls.values())
        pct = ((results.score / results.total_possible) * 100
               if results.total_possible else 0)

        # A critical control that FAILED or could not be VERIFIED both block
        # the top tiers — you cannot certify what you could not confirm.
        integrity = assessment_integrity(results.controls, CONTROL_CATALOGUE)
        critical_fail = sum(
            1 for k, v in results.controls.items()
            if CONTROL_CATALOGUE.get(k, {}).get("critical")
            and getattr(v, "status", None) == "FAIL"
        )
        critical_gaps = critical_fail + len(integrity["unverified_critical"])

        results.critical_failures = critical_fail
        results.integrity = integrity
        results.provisional = integrity["provisional"]
        results.certification_level = certification_for(pct, critical_gaps)

        if results.provisional:
            logger.warning(
                "Assessment for %s is provisional — unverified critical "
                "controls: %s",
                getattr(self.business_info, "name", "?"),
                ", ".join(integrity["unverified_critical"]))
        return results
