"""Tests for the Active Directory hygiene auditor.

ldap3 is faked with an in-memory connection, so these run on any OS with no
directory available.
"""

from datetime import datetime, timedelta, timezone

import pytest

import src.security.active_directory.checks as ad
from src.security.active_directory.checks import (
    ADAuditor, ADFinding, ADReport, build_base_dn,
)

RECENT = datetime.now(timezone.utc) - timedelta(days=5)
OLD = datetime.now(timezone.utc) - timedelta(days=200)


# --------------------------------------------------------------------------
# Fake ldap3 connection
# --------------------------------------------------------------------------


class _Entry:
    def __init__(self, attrs):
        self.entry_attributes_as_dict = {k: [v] for k, v in attrs.items()}


class _Std:
    def __init__(self, conn):
        self._conn = conn

    def paged_search(self, search_base, search_filter, search_scope=None,
                     attributes=None, paged_size=None, generator=False):
        return self._conn._paged_for(search_filter)


class _Extend:
    def __init__(self, conn):
        self.standard = _Std(conn)


class FakeConn:
    def __init__(self, data):
        self.data = data
        self.extend = _Extend(self)
        self.entries = []

    def _paged_for(self, flt):
        if "1.2.840.113556" in flt:                 # stale (enabled users)
            return [{"attributes": u} for u in self.data["users"]]
        if "cn=Domain Admins" in flt:
            return [{"attributes": {"member": self.data["domain_admins"]}}]
        if "krbtgt" in flt:
            return [{"attributes": {"pwdLastSet": self.data["krbtgt"]}}]
        return [{"attributes": u} for u in self.data["users"]]  # risky flags

    def search(self, base, flt, search_scope=None, attributes=None):
        self.entries = [_Entry(
            {"ms-DS-MachineAccountQuota": self.data["machine_quota"]})]
        return True

    def unbind(self):
        pass


def _clean_data():
    return {
        "users": [
            {"sAMAccountName": "alice", "lastLogonTimestamp": RECENT,
             "userAccountControl": 0x0200},   # NORMAL_ACCOUNT
            {"sAMAccountName": "bob", "lastLogonTimestamp": RECENT,
             "userAccountControl": 0x0200},
        ],
        "domain_admins": ["CN=Administrator,DC=corp"],
        "krbtgt": RECENT,
        "machine_quota": 0,
    }


@pytest.fixture(autouse=True)
def _force_ldap(monkeypatch):
    monkeypatch.setattr(ad, "_HAS_LDAP", True)


def _auditor(monkeypatch, data, anon_open=None):
    a = ADAuditor(domain="corp.example.com")
    conn = FakeConn(data)
    monkeypatch.setattr(a, "_connect", lambda: conn)
    # Default: anonymous bind refused (secure).
    if anon_open is None:
        def _refuse_anon():
            raise ConnectionError("anonymous bind refused")
        anon_open = _refuse_anon
    monkeypatch.setattr(a, "_open_anonymous", anon_open)
    return a


# --------------------------------------------------------------------------
# Report model
# --------------------------------------------------------------------------


class TestADReport:
    def test_grade_healthy(self):
        r = ADReport(findings=[
            ADFinding("AD-01", "x", ad.PASS, "HIGH", "ok"),
            ADFinding("AD-02", "y", ad.PASS, "MEDIUM", "ok"),
        ])
        assert r.grade == "HEALTHY"
        assert r.score_percent == 100

    def test_any_critical_fail_is_at_risk(self):
        r = ADReport(findings=[
            ADFinding("AD-01", "x", ad.PASS, "HIGH", "ok"),
            ADFinding("AD-03", "y", ad.FAIL, "CRITICAL", "bad"),
        ])
        assert r.critical_failures == 1
        assert r.grade == "AT RISK"

    def test_skip_excluded_from_scoring(self):
        r = ADReport(findings=[
            ADFinding("AD-00", "x", ad.SKIP, "LOW", "n/a"),
        ])
        assert r.grade == "NOT APPLICABLE"
        assert r.score_percent == 0


# --------------------------------------------------------------------------
# Environment gating
# --------------------------------------------------------------------------


class TestGating:
    def test_no_ldap_skips(self, monkeypatch):
        monkeypatch.setattr(ad, "_HAS_LDAP", False)
        report = ADAuditor(domain="corp.example.com").run()
        assert report.findings[0].status == ad.SKIP
        assert "ldap3" in report.findings[0].details

    def test_no_domain_skips(self):
        report = ADAuditor(domain="").run()
        assert report.findings[0].status == ad.SKIP

    def test_connect_failure_is_error(self, monkeypatch):
        a = ADAuditor(domain="corp.example.com")

        def boom():
            raise ConnectionError("no route to DC")
        monkeypatch.setattr(a, "_connect", boom)
        report = a.run()
        assert report.findings[0].check_id == "AD-01"
        assert report.findings[0].status == ad.ERROR


# --------------------------------------------------------------------------
# Individual checks
# --------------------------------------------------------------------------


class TestChecks:
    def _ids(self, report):
        return {f.check_id: f for f in report.findings}

    def test_clean_domain_is_healthy(self, monkeypatch):
        report = _auditor(monkeypatch, _clean_data()).run()
        assert report.grade == "HEALTHY"
        assert all(f.status == ad.PASS for f in report.applicable)

    def test_stale_accounts_flagged(self, monkeypatch):
        data = _clean_data()
        data["users"][1]["lastLogonTimestamp"] = OLD
        report = _auditor(monkeypatch, data).run()
        f = self._ids(report)["AD-02"]
        assert f.status == ad.FAIL
        assert "1 of 2" in f.details

    def test_too_many_domain_admins(self, monkeypatch):
        data = _clean_data()
        data["domain_admins"] = [f"CN=admin{i},DC=corp" for i in range(9)]
        report = _auditor(monkeypatch, data).run()
        f = self._ids(report)["AD-03"]
        assert f.status == ad.FAIL
        assert f.severity == "CRITICAL"
        assert report.grade == "AT RISK"

    def test_machine_account_quota(self, monkeypatch):
        data = _clean_data()
        data["machine_quota"] = 10
        report = _auditor(monkeypatch, data).run()
        f = self._ids(report)["AD-04"]
        assert f.status == ad.FAIL
        assert "10" in f.details

    def test_old_krbtgt_warns(self, monkeypatch):
        data = _clean_data()
        data["krbtgt"] = OLD
        report = _auditor(monkeypatch, data).run()
        f = self._ids(report)["AD-05"]
        assert f.status == ad.WARN

    def test_risky_account_flags(self, monkeypatch):
        data = _clean_data()
        # give bob PASSWD_NOTREQD (0x20) on top of NORMAL_ACCOUNT
        data["users"][1]["userAccountControl"] = 0x0200 | 0x0020
        report = _auditor(monkeypatch, data).run()
        f = self._ids(report)["AD-06"]
        assert f.status == ad.FAIL
        assert "password not required" in f.details

    def test_anonymous_bind_allowed_fails(self, monkeypatch):
        class AnonConn:
            def __init__(self):
                self.entries = [object()]

            def search(self, *a, **k):
                return True

            def unbind(self):
                pass
        report = _auditor(monkeypatch, _clean_data(),
                          anon_open=lambda: AnonConn()).run()
        f = self._ids(report)["AD-07"]
        assert f.status == ad.FAIL

    def test_anonymous_bind_refused_passes(self, monkeypatch):
        report = _auditor(monkeypatch, _clean_data()).run()
        assert self._ids(report)["AD-07"].status == ad.PASS


def test_build_base_dn():
    assert build_base_dn("corp.example.com") == "DC=corp,DC=example,DC=com"
    assert build_base_dn("") == ""
