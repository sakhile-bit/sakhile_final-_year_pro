"""Tests for certificate rendering helpers and report verification sections."""

import types

import pytest

from src.security.certs import render
from src.reporting.generator import ReportGenerator


# ── verify URL / QR helpers ─────────────────────────────────────────────────────

def test_verify_url_default(monkeypatch):
    monkeypatch.delenv("VERIFY_BASE_URL", raising=False)
    monkeypatch.delenv("PORTAL_BASE_URL", raising=False)
    assert render.verify_url("ZDH-2026-AAAA-BBBB-CCCC") == (
        "http://localhost:5000/verify/ZDH-2026-AAAA-BBBB-CCCC")


def test_verify_url_env_override(monkeypatch):
    monkeypatch.setenv("VERIFY_BASE_URL", "https://verify.example.org/")
    assert render.verify_url("X1").startswith("https://verify.example.org/verify/X1")


def test_verify_url_explicit_base_wins(monkeypatch):
    monkeypatch.setenv("VERIFY_BASE_URL", "https://env.example")
    assert render.verify_url("X1", base="http://127.0.0.1:8000/") == (
        "http://127.0.0.1:8000/verify/X1")


def test_qr_png_bytes_is_png():
    png = render.qr_png_bytes("https://example.org/verify/X1")
    assert png is not None
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_qr_data_uri_format():
    uri = render.qr_data_uri("https://example.org/verify/X1")
    assert uri is not None
    assert uri.startswith("data:image/png;base64,")


# ── report generator verification section ───────────────────────────────────────

def _fake_results(with_cert: bool):
    r = types.SimpleNamespace(
        score=104, total_possible=120, certification_level="GOLD",
        controls={}, recommendations=[], critical_failures=0,
        assessment_tier="automated",
    )
    if with_cert:
        r.certificate = {
            "certificate_number": "ZDH-2026-1234-5678-9ABC",
            "verify_url": "http://localhost:5000/verify/ZDH-2026-1234-5678-9ABC",
            "verification_block": "eyJwIjp7fSwicyI6IiJ9",
        }
    return r


def _biz():
    return types.SimpleNamespace(name="Acme Ltd", id="REG-1", industry="ICT",
                                 contact_person="A", contact_email="a@x.z",
                                 contact_phone="123", province="Lusaka",
                                 address="1 St")


def test_html_report_includes_verification_when_cert_present():
    gen = ReportGenerator(output_dir="reports")
    html = gen._build_html(_fake_results(with_cert=True), _biz())
    assert "Certificate Verification" in html
    assert "ZDH-2026-1234-5678-9ABC" in html
    assert "data:image/png;base64," in html          # QR embedded
    assert "Offline verification code" in html


def test_html_report_omits_verification_without_cert():
    gen = ReportGenerator(output_dir="reports")
    html = gen._build_html(_fake_results(with_cert=False), _biz())
    assert "Certificate Verification" not in html


def test_pdf_report_with_certificate(tmp_path):
    pytest.importorskip("reportlab")
    gen = ReportGenerator(output_dir=str(tmp_path))
    path = gen.generate_pdf_report(_fake_results(with_cert=True), _biz(), "rep")
    assert path.endswith(".pdf")
    from pathlib import Path
    assert Path(path).exists() and Path(path).stat().st_size > 0
