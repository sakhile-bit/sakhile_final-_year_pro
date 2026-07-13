"""Tests for the desktop certificate client and local certificate persistence."""

import types

import pytest


@pytest.fixture(autouse=True)
def _local_db(tmp_path, monkeypatch):
    monkeypatch.setenv("ZDH_DB_PATH", str(tmp_path / "hist.db"))
    # Isolate portal config from the developer's environment.
    monkeypatch.delenv("PORTAL_API_URL", raising=False)
    monkeypatch.delenv("VERIFY_BASE_URL", raising=False)
    monkeypatch.delenv("ZDH_ISSUE_API_KEY", raising=False)
    yield


def _result(level="SILVER", provisional=False):
    bi = types.SimpleNamespace(name="Ndola Foods Ltd", id="PACRA-55010",
                               province="Copperbelt", industry="Retail",
                               contact_person="M. Banda", contact_email="m@nf.zm",
                               contact_phone="+260", address="Buteko Ave")
    return types.SimpleNamespace(
        business_info=bi, certification_level=level, score=78, total_possible=120,
        critical_failures=1, assessment_tier="automated", provisional=provisional,
    )


# ── cert_client ────────────────────────────────────────────────────────────────

def test_payload_shape():
    from src.utils import cert_client
    p = cert_client._payload_from_result(_result())
    assert p["business_name"] == "Ndola Foods Ltd"
    assert p["registration_number"] == "PACRA-55010"
    assert p["level"] == "SILVER"
    assert p["score"] == 78 and p["total_possible"] == 120


def test_defaults_local(monkeypatch):
    from src.utils import cert_client
    assert cert_client.portal_base_url() == "http://localhost:5000"
    assert cert_client.issue_api_key() == "dev-issue-key-change-me"


def test_config_via_settings(monkeypatch):
    from src.utils import cert_client, local_db
    local_db.set_setting("portal_url", "https://verify.gov.zm/")
    local_db.set_setting("issue_api_key", "k-123")
    assert cert_client.portal_base_url() == "https://verify.gov.zm"
    assert cert_client.issue_api_key() == "k-123"


def test_issue_skips_not_certified():
    from src.utils import cert_client
    assert cert_client.issue_certificate(_result(level="NOT CERTIFIED")) is None


def test_issue_skips_provisional():
    from src.utils import cert_client
    assert cert_client.issue_certificate(_result(provisional=True)) is None


def test_issue_posts_and_returns_json(monkeypatch):
    from src.utils import cert_client

    captured = {}

    class FakeResp:
        status_code = 201

        def json(self):
            return {"certificate_number": "ZDH-2026-AAAA-BBBB-CCCC",
                    "verify_url": "http://localhost:5000/verify/ZDH-2026-AAAA-BBBB-CCCC",
                    "verification_block": "abc"}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured.update(url=url, json=json, headers=headers)
        return FakeResp()

    monkeypatch.setattr("requests.post", fake_post, raising=False)
    out = cert_client.issue_certificate(_result())
    assert out is not None
    assert out["certificate_number"] == "ZDH-2026-AAAA-BBBB-CCCC"
    assert captured["url"].endswith("/api/certificates/issue")
    assert captured["headers"]["X-API-Key"] == "dev-issue-key-change-me"
    assert captured["json"]["level"] == "SILVER"


def test_issue_offline_returns_none(monkeypatch):
    from src.utils import cert_client

    def boom(*a, **k):
        raise OSError("no route to host")

    monkeypatch.setattr("requests.post", boom, raising=False)
    assert cert_client.issue_certificate(_result()) is None


def test_issue_rejection_returns_none(monkeypatch):
    from src.utils import cert_client

    class FakeResp:
        status_code = 401
        text = "unauthorized"

    monkeypatch.setattr("requests.post", lambda *a, **k: FakeResp(), raising=False)
    assert cert_client.issue_certificate(_result()) is None


# ── local_db certificate persistence ────────────────────────────────────────────

def test_save_and_get_certificate():
    from src.utils import local_db
    cert = {"certificate_number": "ZDH-2026-1111-2222-3333", "level": "SILVER",
            "issued_date": "2026-07-12", "expiry_date": "2027-07-12",
            "verify_url": "http://localhost:5000/verify/ZDH-2026-1111-2222-3333",
            "verification_block": "blk"}
    local_db.save_certificate(42, "REGISTERED", cert)
    row = local_db.get_certificate(42)
    assert row is not None
    assert row["cert_number"] == "ZDH-2026-1111-2222-3333"
    assert row["status"] == "REGISTERED"
    assert row["verify_url"].endswith("ZDH-2026-1111-2222-3333")


def test_provisional_then_registered_upserts():
    from src.utils import local_db
    local_db.save_certificate(7, "PROVISIONAL", None)
    prov = local_db.get_certificate(7)
    assert prov is not None and prov["status"] == "PROVISIONAL"
    assert len(local_db.list_provisional_certificates()) == 1

    local_db.save_certificate(7, "REGISTERED",
                              {"certificate_number": "ZDH-X", "level": "GOLD"})
    reg = local_db.get_certificate(7)
    assert reg is not None and reg["status"] == "REGISTERED"
    assert local_db.list_provisional_certificates() == []
