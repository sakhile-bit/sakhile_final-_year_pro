"""Tests for the desktop app's navigation stack and wizard state."""

import types

import pytest

from src.gui.state import AppState
from src.security.assessment import assessor as assessor_mod


# ---------------------------------------------------------------------------
# AppState — wizard data lifecycle
# ---------------------------------------------------------------------------


class TestAppState:
    def test_defaults_are_empty(self):
        s = AppState()
        assert s.business_info is None
        assert s.selected_tools == set()
        assert s.auto_results == {}
        assert s.manual_scores == {}
        assert s.evidence == {}

    def test_reset_clears_everything(self):
        s = AppState()
        s.business_info = object()
        s.selected_tools = {"infra_scan"}
        s.auto_results = {"C01": object()}
        s.manual_scores = {"C06_security_training": 8}
        s.evidence = {"C06_security_training": "note"}
        s.reset_assessment()
        assert s.business_info is None
        assert s.selected_tools == set()
        assert s.auto_results == {}
        assert s.manual_scores == {}
        assert s.evidence == {}

    def test_build_results_requires_business_info(self):
        with pytest.raises(ValueError):
            AppState().build_results()

    def test_build_results_merges_auto_and_scores(self, monkeypatch):
        # Fake control objects with the attributes build_results touches
        def ctrl(score, status):
            return types.SimpleNamespace(score=score, status=status)

        base_controls = {
            "C01_os_updates": ctrl(0, "FAIL"),
            "C02_antivirus": ctrl(5, "WARNING"),
        }
        fake_results = types.SimpleNamespace(
            controls=base_controls,
            total_possible=100,
            score=0,
            critical_failures=0,
            certification_level="",
        )

        class FakeAssessor:
            def __init__(self, *a, **k):
                pass

            def run_assessment(self):
                return fake_results

        monkeypatch.setattr(assessor_mod, "DigitalHygieneAssessor", FakeAssessor)
        monkeypatch.setattr(assessor_mod, "CONTROL_CATALOGUE",
                            {"C01_os_updates": {"critical": True}})

        s = AppState()
        s.business_info = object()
        # An automated result captured on the scanning screen overrides C01
        s.auto_results = {"C01": ctrl(10, "PASS")}
        out = s.build_results()

        # C01 was patched to the passing automated result
        assert out.controls["C01_os_updates"].status == "PASS"
        # Score recomputed from the merged controls (10 + 5)
        assert out.score == 15
        # C01 no longer failing → no critical failures
        assert out.critical_failures == 0
        assert out.certification_level == "NOT CERTIFIED"  # 15% < 40%


# ---------------------------------------------------------------------------
# certification_for — single source of truth for the tier rule
# ---------------------------------------------------------------------------


class TestCertificationFor:
    def test_gold_needs_no_critical_failures(self):
        assert assessor_mod.certification_for(85, 0) == "GOLD"
        assert assessor_mod.certification_for(85, 1) == "SILVER"

    def test_tiers(self):
        assert assessor_mod.certification_for(60, 1) == "SILVER"
        assert assessor_mod.certification_for(40, 2) == "BRONZE"
        assert assessor_mod.certification_for(39, 0) == "NOT CERTIFIED"
        assert assessor_mod.certification_for(90, 3) == "NOT CERTIFIED"


# ---------------------------------------------------------------------------
# Router — navigation stack (requires a Tk display)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def root():
    # A single Tk root is shared across the module: creating and destroying
    # multiple CTk() roots in one process is unreliable.
    ctk = pytest.importorskip("customtkinter")
    try:
        r = ctk.CTk()
    except Exception:  # pragma: no cover - headless CI without a display
        pytest.skip("no display available")
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


@pytest.fixture
def frame_factory(root):
    import customtkinter as ctk
    return lambda: ctk.CTkFrame(root)


class TestRouter:
    def test_reset_to_sets_root(self, root, frame_factory):
        from src.gui.router import Router
        r = Router(root)
        r.reset_to("welcome", frame_factory)
        assert r.stack_names() == ["welcome"]
        assert not r.can_go_back
        assert r.current_name == "welcome"

    def test_push_grows_stack(self, root, frame_factory):
        from src.gui.router import Router
        r = Router(root)
        r.reset_to("welcome", frame_factory)
        r.push("a", frame_factory)
        r.push("b", frame_factory)
        assert r.stack_names() == ["welcome", "a", "b"]
        assert r.can_go_back
        assert r.depth == 3

    def test_back_pops(self, root, frame_factory):
        from src.gui.router import Router
        r = Router(root)
        r.reset_to("welcome", frame_factory)
        r.push("a", frame_factory)
        r.push("b", frame_factory)
        assert r.back() is True
        assert r.current_name == "a"
        assert r.back() is True
        assert r.current_name == "welcome"
        # at root — no further back
        assert r.back() is False
        assert r.stack_names() == ["welcome"]

    def test_replace_keeps_depth(self, root, frame_factory):
        from src.gui.router import Router
        r = Router(root)
        r.reset_to("welcome", frame_factory)
        r.push("a", frame_factory)
        r.replace("a2", frame_factory)
        assert r.stack_names() == ["welcome", "a2"]

    def test_reset_to_collapses_stack(self, root, frame_factory):
        from src.gui.router import Router
        r = Router(root)
        r.reset_to("welcome", frame_factory)
        r.push("a", frame_factory)
        r.push("b", frame_factory)
        r.reset_to("welcome", frame_factory)
        assert r.stack_names() == ["welcome"]

    def test_error_screen_on_factory_failure(self, root, frame_factory):
        from src.gui.router import Router
        r = Router(root)
        r.reset_to("welcome", frame_factory)

        def boom():
            raise RuntimeError("screen exploded")

        # Must not raise — falls back to an error screen
        r.push("broken", boom)
        assert r.current_name == "broken"
        assert r._current_widget is not None
