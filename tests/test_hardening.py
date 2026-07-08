"""Tests for the Windows infrastructure hardening auditor."""

import pytest

import src.security.hardening.checks as hc
from src.security.hardening.checks import (
    HardeningCheckResult,
    HardeningReport,
    WindowsHardeningAuditor,
)
from src.security.remediation.guidance import get_remediation


def _result(check_id="HRD-00", status="PASS", severity="MEDIUM"):
    return HardeningCheckResult(
        check_id=check_id, name="Test", status=status,
        severity=severity, details="details")


# ---------------------------------------------------------------------------
# Aggregate report
# ---------------------------------------------------------------------------


class TestHardeningReport:
    def test_all_pass_is_hardened(self):
        report = HardeningReport(checks=[_result() for _ in range(10)])
        assert report.score_percent == 100
        assert report.grade == "HARDENED"
        assert report.failed == 0

    def test_critical_failure_blocks_hardened_grade(self):
        checks = [_result() for _ in range(9)]
        checks.append(_result(status="FAIL", severity="CRITICAL"))
        report = HardeningReport(checks=checks)
        assert report.critical_failures == 1
        assert report.grade != "HARDENED"

    def test_warnings_count_half(self):
        checks = [_result(status="WARNING") for _ in range(4)]
        report = HardeningReport(checks=checks)
        assert report.score_percent == 50

    def test_mostly_failing_is_at_risk(self):
        checks = [_result(status="FAIL", severity="HIGH") for _ in range(8)]
        checks.append(_result())
        report = HardeningReport(checks=checks)
        assert report.grade == "AT RISK"

    def test_not_applicable_excluded(self):
        checks = [_result(), _result(status="NOT_APPLICABLE")]
        report = HardeningReport(checks=checks)
        assert report.total == 1
        assert report.score_percent == 100

    def test_empty_report(self):
        report = HardeningReport(checks=[])
        assert report.score_percent == 0
        assert report.grade == "NOT APPLICABLE"

    def test_to_dict_shape(self):
        report = HardeningReport(checks=[_result()])
        d = report.to_dict()
        assert d["grade"] == "HARDENED"
        assert d["summary"]["total"] == 1
        assert d["checks"][0]["check_id"] == "HRD-00"
        assert d["checks"][0]["passed"] is True
        assert d["hostname"]
        assert d["timestamp"]


# ---------------------------------------------------------------------------
# Individual checks (registry/service access mocked for determinism)
# ---------------------------------------------------------------------------


@pytest.fixture
def auditor():
    return WindowsHardeningAuditor()


@pytest.fixture
def on_windows(monkeypatch):
    monkeypatch.setattr(hc, "IS_WINDOWS", True)


def _patch_registry(monkeypatch, values):
    """Patch _reg_value to return values[(path, name)] (None when absent)."""
    monkeypatch.setattr(
        hc, "_reg_value",
        lambda path, name, hive=None: values.get((path, name)))


class TestSmb1Check:
    LANMAN = r"SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"

    def test_disabled_passes(self, auditor, on_windows, monkeypatch):
        _patch_registry(monkeypatch, {(self.LANMAN, "SMB1"): 0})
        result = auditor.check_smb1()
        assert result.status == "PASS"

    def test_enabled_fails_critical(self, auditor, on_windows, monkeypatch):
        _patch_registry(monkeypatch, {(self.LANMAN, "SMB1"): 1})
        result = auditor.check_smb1()
        assert result.status == "FAIL"
        assert result.severity == "CRITICAL"

    def test_absent_falls_back_to_powershell(self, auditor, on_windows,
                                              monkeypatch):
        _patch_registry(monkeypatch, {})
        monkeypatch.setattr(hc, "_run_powershell", lambda cmd, timeout=20: "False")
        result = auditor.check_smb1()
        assert result.status == "PASS"

    def test_non_windows_not_applicable(self, auditor, monkeypatch):
        monkeypatch.setattr(hc, "IS_WINDOWS", False)
        assert auditor.check_smb1().status == "NOT_APPLICABLE"


class TestUacCheck:
    POLICY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"

    def test_enabled_with_prompt_passes(self, auditor, on_windows, monkeypatch):
        _patch_registry(monkeypatch, {
            (self.POLICY, "EnableLUA"): 1,
            (self.POLICY, "ConsentPromptBehaviorAdmin"): 5,
        })
        assert auditor.check_uac().status == "PASS"

    def test_disabled_fails(self, auditor, on_windows, monkeypatch):
        _patch_registry(monkeypatch, {(self.POLICY, "EnableLUA"): 0})
        assert auditor.check_uac().status == "FAIL"

    def test_silent_elevation_warns(self, auditor, on_windows, monkeypatch):
        _patch_registry(monkeypatch, {
            (self.POLICY, "EnableLUA"): 1,
            (self.POLICY, "ConsentPromptBehaviorAdmin"): 0,
        })
        assert auditor.check_uac().status == "WARNING"


class TestRdpCheck:
    TS = r"SYSTEM\CurrentControlSet\Control\Terminal Server"
    RDP_TCP = TS + r"\WinStations\RDP-Tcp"

    def test_rdp_disabled_passes(self, auditor, on_windows, monkeypatch):
        _patch_registry(monkeypatch, {(self.TS, "fDenyTSConnections"): 1})
        assert auditor.check_rdp_hardening().status == "PASS"

    def test_rdp_enabled_without_nla_fails(self, auditor, on_windows,
                                           monkeypatch):
        _patch_registry(monkeypatch, {
            (self.TS, "fDenyTSConnections"): 0,
            (self.RDP_TCP, "UserAuthentication"): 0,
        })
        result = auditor.check_rdp_hardening()
        assert result.status == "FAIL"
        assert "Network Level Authentication" in result.details

    def test_rdp_enabled_with_nla_passes(self, auditor, on_windows,
                                         monkeypatch):
        _patch_registry(monkeypatch, {
            (self.TS, "fDenyTSConnections"): 0,
            (self.RDP_TCP, "UserAuthentication"): 1,
            (self.RDP_TCP, "SecurityLayer"): 2,
        })
        assert auditor.check_rdp_hardening().status == "PASS"


class TestLlmnrCheck:
    DNS = r"SOFTWARE\Policies\Microsoft\Windows NT\DNSClient"
    NBT = r"SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces"

    def test_both_disabled_passes(self, auditor, on_windows, monkeypatch):
        _patch_registry(monkeypatch, {
            (self.DNS, "EnableMulticast"): 0,
            (self.NBT + r"\Tcpip_1", "NetbiosOptions"): 2,
        })
        monkeypatch.setattr(hc, "_reg_subkeys", lambda path: ["Tcpip_1"])
        assert auditor.check_llmnr_netbios().status == "PASS"

    def test_both_enabled_fails(self, auditor, on_windows, monkeypatch):
        _patch_registry(monkeypatch, {
            (self.NBT + r"\Tcpip_1", "NetbiosOptions"): 0,
        })
        monkeypatch.setattr(hc, "_reg_subkeys", lambda path: ["Tcpip_1"])
        result = auditor.check_llmnr_netbios()
        assert result.status == "FAIL"


class TestServiceChecks:
    def test_remote_registry_running_fails(self, auditor, on_windows,
                                           monkeypatch):
        monkeypatch.setattr(hc, "_service_state", lambda name: "RUNNING")
        assert auditor.check_remote_registry().status == "FAIL"

    def test_remote_registry_disabled_passes(self, auditor, on_windows,
                                             monkeypatch):
        monkeypatch.setattr(hc, "_service_state", lambda name: "DISABLED")
        assert auditor.check_remote_registry().status == "PASS"

    def test_spooler_stopped_passes(self, auditor, on_windows, monkeypatch):
        monkeypatch.setattr(hc, "_service_state", lambda name: "STOPPED")
        assert auditor.check_print_spooler().status == "PASS"


class TestLegacyTls:
    BASE = (r"SYSTEM\CurrentControlSet\Control\SecurityProviders"
            r"\Schannel\Protocols")

    def test_explicitly_disabled_passes(self, auditor, on_windows, monkeypatch):
        _patch_registry(monkeypatch, {
            (self.BASE + r"\TLS 1.0\Server", "Enabled"): 0,
            (self.BASE + r"\TLS 1.1\Server", "Enabled"): 0,
        })
        assert auditor.check_legacy_tls().status == "PASS"

    def test_explicitly_enabled_fails(self, auditor, on_windows, monkeypatch):
        _patch_registry(monkeypatch, {
            (self.BASE + r"\TLS 1.0\Server", "Enabled"): 1,
        })
        assert auditor.check_legacy_tls().status == "FAIL"

    def test_os_default_warns(self, auditor, on_windows, monkeypatch):
        _patch_registry(monkeypatch, {})
        assert auditor.check_legacy_tls().status == "WARNING"


class TestRunAll:
    def test_run_all_returns_14_checks(self, auditor):
        report = auditor.run_all()
        assert len(report.checks) == 14
        ids = [c.check_id for c in report.checks]
        assert ids == [f"HRD-{i:02d}" for i in range(1, 15)]

    def test_run_all_non_windows_grade(self, auditor, monkeypatch):
        monkeypatch.setattr(hc, "IS_WINDOWS", False)
        report = auditor.run_all()
        assert all(c.status == "NOT_APPLICABLE" for c in report.checks)
        assert report.grade == "NOT APPLICABLE"


# ---------------------------------------------------------------------------
# Remediation catalogue coverage
# ---------------------------------------------------------------------------


class TestRemediationCoverage:
    def test_every_hardening_check_has_guidance(self):
        for i in range(1, 15):
            check_id = f"HRD-{i:02d}"
            guidance = get_remediation(check_id)
            assert guidance is not None, f"{check_id} missing remediation"
            assert guidance["title"]
            assert guidance["advice"]

    def test_unknown_id_returns_none(self):
        assert get_remediation("HRD-99") is None
