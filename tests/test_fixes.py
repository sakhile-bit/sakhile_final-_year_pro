"""Tests for the Windows hardening auto-fix engine.

These run on any OS: the low-level registry/service primitives are
monkeypatched with in-memory fakes, so no real Windows state is touched.
"""

import pytest

import src.security.hardening.fixes as fx


# ---------------------------------------------------------------------------
# In-memory fakes for the registry + service backends
# ---------------------------------------------------------------------------


class FakeRegistry:
    def __init__(self, initial=None):
        # keyed by (path, name) -> value
        self.store = dict(initial or {})
        self.subkeys = {}  # path -> [names]

    def read(self, path, name):
        return self.store.get((path, name))

    def write(self, path, name, value):
        self.store[(path, name)] = int(value)

    def delete(self, path, name):
        self.store.pop((path, name), None)

    def list_subkeys(self, path):
        return list(self.subkeys.get(path, []))


class FakeServices:
    def __init__(self, states=None):
        # name -> {"startup": str, "running": bool}
        self.svc = dict(states or {})

    def startup(self, name):
        return self.svc.get(name, {}).get("startup", "unknown")

    def running(self, name):
        return self.svc.get(name, {}).get("running", False)

    def set_startup(self, name, startup):
        self.svc.setdefault(name, {})["startup"] = startup
        return True

    def stop(self, name):
        self.svc.setdefault(name, {})["running"] = False
        return True

    def start(self, name):
        self.svc.setdefault(name, {})["running"] = True
        return True


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Wire the fix engine to in-memory backends + a temp journal."""
    reg = FakeRegistry()
    svc = FakeServices()

    monkeypatch.setattr(fx, "IS_WINDOWS", True)
    monkeypatch.setattr(fx, "is_admin", lambda: True)
    monkeypatch.setattr(fx, "_reg_read", reg.read)
    monkeypatch.setattr(fx, "_reg_write", reg.write)
    monkeypatch.setattr(fx, "_reg_delete", reg.delete)
    monkeypatch.setattr(fx, "_reg_subkeys", reg.list_subkeys)
    monkeypatch.setattr(fx, "_svc_startup_type", svc.startup)
    monkeypatch.setattr(fx, "_svc_running", svc.running)
    monkeypatch.setattr(fx, "_svc_set_startup", svc.set_startup)
    monkeypatch.setattr(fx, "_svc_stop", svc.stop)
    monkeypatch.setattr(fx, "_svc_start", svc.start)
    monkeypatch.setattr(fx, "_journal_path",
                        lambda: tmp_path / "fix_journal.json")

    return {"reg": reg, "svc": svc, "tmp": tmp_path}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestFixRegistry:
    def test_available_fixes_cover_expected_checks(self):
        ids = set(fx.available_fixes())
        # The judgement-required checks must NOT have auto-fixes
        assert "HRD-08" not in ids
        assert "HRD-12" not in ids
        # Core protocol/credential fixes must exist
        for cid in ("HRD-01", "HRD-05", "HRD-13", "HRD-14"):
            assert cid in ids

    def test_smb1_and_others_are_safe(self):
        f01 = fx.fix_for("HRD-01")
        f05 = fx.fix_for("HRD-05")
        assert f01 is not None and f01.safe
        assert f05 is not None and f05.safe

    def test_spooler_and_tls_are_caution(self):
        f09 = fx.fix_for("HRD-09")
        f07 = fx.fix_for("HRD-07")
        assert f09 is not None and not f09.safe
        assert f07 is not None and not f07.safe
        assert f09.caution


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


class TestApplyFixes:
    def test_apply_smb1_writes_registry(self, env):
        env["reg"].store[(fx._LANMAN_SRV, "SMB1")] = 1  # currently enabled
        results = fx.apply_fixes(["HRD-01"])
        assert results[0].success
        assert results[0].message == "Fixed"
        assert env["reg"].read(fx._LANMAN_SRV, "SMB1") == 0

    def test_apply_records_journal(self, env):
        env["reg"].store[(fx._LANMAN_SRV, "SMB1")] = 1
        fx.apply_fixes(["HRD-01"])
        entry = fx.last_journal_entry()
        assert entry is not None
        assert entry["check_ids"] == ["HRD-01"]
        assert not entry["reverted"]

    def test_already_compliant_makes_no_journal_entry(self, env):
        env["reg"].store[(fx._LANMAN_SRV, "SMB1")] = 0  # already disabled
        results = fx.apply_fixes(["HRD-01"])
        assert results[0].success
        assert results[0].message == "Already compliant"
        assert fx.last_journal_entry() is None

    def test_llmnr_fix_covers_all_adapters(self, env):
        reg = env["reg"]
        reg.subkeys[fx._NETBT_IF] = ["{AAA}", "{BBB}"]
        reg.store[(f"{fx._NETBT_IF}\\{{AAA}}", "NetbiosOptions")] = 0
        reg.store[(f"{fx._NETBT_IF}\\{{BBB}}", "NetbiosOptions")] = 0
        fx.apply_fixes(["HRD-05"])
        assert reg.read(fx._DNSCLIENT, "EnableMulticast") == 0
        assert reg.read(f"{fx._NETBT_IF}\\{{AAA}}", "NetbiosOptions") == 2
        assert reg.read(f"{fx._NETBT_IF}\\{{BBB}}", "NetbiosOptions") == 2

    def test_unknown_check_returns_failure(self, env):
        results = fx.apply_fixes(["HRD-99"])
        assert not results[0].success
        assert "No automatic fix" in results[0].message

    def test_non_admin_refuses(self, env, monkeypatch):
        monkeypatch.setattr(fx, "is_admin", lambda: False)
        results = fx.apply_fixes(["HRD-01"])
        assert not results[0].success
        assert "Administrator" in results[0].message

    def test_non_windows_refuses(self, env, monkeypatch):
        monkeypatch.setattr(fx, "IS_WINDOWS", False)
        results = fx.apply_fixes(["HRD-01"])
        assert not results[0].success


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


class TestServiceFixes:
    def test_disable_spooler(self, env):
        env["svc"].svc["Spooler"] = {"startup": "auto", "running": True}
        results = fx.apply_fixes(["HRD-09"])
        assert results[0].success
        assert env["svc"].startup("Spooler") == "disabled"
        assert not env["svc"].running("Spooler")

    def test_spooler_already_disabled_noop(self, env):
        env["svc"].svc["Spooler"] = {"startup": "disabled", "running": False}
        results = fx.apply_fixes(["HRD-09"])
        assert results[0].message == "Already compliant"


# ---------------------------------------------------------------------------
# Revert
# ---------------------------------------------------------------------------


class TestRevert:
    def test_revert_restores_previous_value(self, env):
        env["reg"].store[(fx._LANMAN_SRV, "SMB1")] = 1
        fx.apply_fixes(["HRD-01"])
        assert env["reg"].read(fx._LANMAN_SRV, "SMB1") == 0
        ok, _msg, _details = fx.revert_last()
        assert ok
        assert env["reg"].read(fx._LANMAN_SRV, "SMB1") == 1

    def test_revert_deletes_value_that_was_absent(self, env):
        # NoLMHash absent before; HRD-13 sets it to 1
        fx.apply_fixes(["HRD-13"])
        assert env["reg"].read(fx._LSA, "RunAsPPL") == 1
        fx.revert_last()
        # value that did not exist before must be removed again
        assert env["reg"].read(fx._LSA, "RunAsPPL") is None

    def test_revert_restores_service_state(self, env):
        env["svc"].svc["RemoteRegistry"] = {"startup": "demand",
                                            "running": True}
        fx.apply_fixes(["HRD-10"])
        assert env["svc"].startup("RemoteRegistry") == "disabled"
        fx.revert_last()
        assert env["svc"].startup("RemoteRegistry") == "demand"
        assert env["svc"].running("RemoteRegistry")

    def test_nothing_to_undo(self, env):
        ok, msg, _ = fx.revert_last()
        assert not ok
        assert "Nothing to undo" in msg

    def test_revert_is_one_shot(self, env):
        env["reg"].store[(fx._LANMAN_SRV, "SMB1")] = 1
        fx.apply_fixes(["HRD-01"])
        assert fx.revert_last()[0]
        # second undo has nothing left
        ok, msg, _ = fx.revert_last()
        assert not ok
