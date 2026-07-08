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
    """Mutable state for one pass through the assessment wizard."""

    business_info: Optional[Any] = None
    selected_tools: Set[str] = field(default_factory=set)
    auto_results: Dict[str, Any] = field(default_factory=dict)
    manual_scores: Dict[str, int] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)

    def reset_assessment(self) -> None:
        """Clear all wizard data so the next assessment starts clean."""
        self.business_info = None
        self.selected_tools = set()
        self.auto_results = {}
        self.manual_scores = {}
        self.evidence = {}
        logger.debug("Assessment state reset")

    # ------------------------------------------------------------------
    def build_results(self):
        """Assemble a finished ``AssessmentResults`` from wizard inputs.

        Runs the assessor with the collected business info, selected tools
        and manual answers, then patches in the automated control results
        captured live on the scanning screen and recomputes the headline
        score / critical count / certification tier.

        This logic used to live inside the navigation controller; keeping
        it here means the controller only decides *where to go*, not *how
        an assessment is scored*.
        """
        from src.security.assessment.assessor import (
            CONTROL_CATALOGUE,
            DigitalHygieneAssessor,
            certification_for,
        )

        if self.business_info is None:
            raise ValueError("business_info must be set before building results")

        assessor = DigitalHygieneAssessor(
            self.business_info,
            manual_answers=self.manual_scores,
            assessment_tier="full",
            selected_tools=self.selected_tools,
        )
        results = assessor.run_assessment()

        # Patch in the automated results captured live on the scanning screen
        for cid_key, ctrl_result in self.auto_results.items():
            suffix = _AUTO_CONTROL_SUFFIX.get(cid_key)
            full_key = f"{cid_key}_{suffix}" if suffix else cid_key
            if full_key in results.controls:
                results.controls[full_key] = ctrl_result

        # Recompute headline figures from the merged control set
        results.score = sum(c.score for c in results.controls.values())
        pct = ((results.score / results.total_possible) * 100
               if results.total_possible else 0)
        results.critical_failures = sum(
            1 for k, v in results.controls.items()
            if CONTROL_CATALOGUE.get(k, {}).get("critical") and v.status == "FAIL"
        )
        results.certification_level = certification_for(
            pct, results.critical_failures)
        return results
