"""Tests for the settings persistence layer and Settings screen."""

import pytest

from src.utils import local_db


class TestSettingsStore:
    def test_set_and_get(self):
        local_db.set_setting("org_name", "Acme Ltd")
        assert local_db.get_setting("org_name") == "Acme Ltd"

    def test_get_default_when_unset(self):
        assert local_db.get_setting("does_not_exist", "fallback") == "fallback"

    def test_bool_setting(self):
        local_db.set_setting("detailed_logging", "true")
        assert local_db.get_bool_setting("detailed_logging") is True
        local_db.set_setting("detailed_logging", "false")
        assert local_db.get_bool_setting("detailed_logging") is False
        assert local_db.get_bool_setting("missing", True) is True

    def test_int_setting(self):
        local_db.set_setting("reassess_interval_days", "90")
        assert local_db.get_int_setting("reassess_interval_days") == 90
        assert local_db.get_int_setting("missing", 182) == 182

    def test_int_setting_bad_value_falls_back(self):
        local_db.set_setting("reassess_interval_days", "not-a-number")
        assert local_db.get_int_setting("reassess_interval_days", 182) == 182

    def test_overwrite(self):
        local_db.set_setting("k", "one")
        local_db.set_setting("k", "two")
        assert local_db.get_setting("k") == "two"

    def test_get_all_settings(self):
        local_db.set_setting("a", "1")
        local_db.set_setting("b", "2")
        alls = local_db.get_all_settings()
        assert alls.get("a") == "1" and alls.get("b") == "2"

    def test_none_stored_as_empty(self):
        local_db.set_setting("empty", None)
        assert local_db.get_setting("empty") == ""


class TestClearHistory:
    def test_clear_history_removes_reports_keeps_settings(self):
        # Seed one of each record type
        local_db.save_fleet_report({
            "scanned_at": "t", "fleet_grade": "HARDENED",
            "summary": {"total_nodes": 1, "online": 1}})
        local_db.save_agent_report({"hostname": "h", "collected_at": "t"})
        local_db.set_setting("keep_me", "yes")

        assert local_db.fleet_report_count() >= 1
        assert local_db.agent_report_count() >= 1

        local_db.clear_history()

        assert local_db.fleet_report_count() == 0
        assert local_db.agent_report_count() == 0
        assert local_db.assessment_count() == 0
        # settings survive
        assert local_db.get_setting("keep_me") == "yes"

    def test_db_location_returns_path(self):
        assert local_db.db_location()


class TestSettingsScreen:
    def test_screen_loads_saved_values(self):
        ctk = pytest.importorskip("customtkinter")
        try:
            root = ctk.CTk()
        except Exception:  # pragma: no cover - headless
            pytest.skip("no display")
        root.withdraw()
        try:
            local_db.set_setting("org_name", "Prefilled Co")
            from src.gui.screens.settings import SettingsScreen
            screen = SettingsScreen(root, on_back=lambda: None)
            root.update_idletasks()
            # The general tab entry should have loaded the saved value
            assert screen._entries["org_name"].get() == "Prefilled Co"
            # Saving persists edited values
            screen._entries["org_name"].delete(0, "end")
            screen._entries["org_name"].insert(0, "Edited Co")
            screen._save_settings()
            assert local_db.get_setting("org_name") == "Edited Co"
            screen.destroy()
        finally:
            root.destroy()
