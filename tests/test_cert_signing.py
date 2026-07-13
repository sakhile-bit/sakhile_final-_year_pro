"""Unit tests for the Ed25519 certificate signing service."""

import json
from typing import Any

import pytest

from src.security.certs import signing


@pytest.fixture()
def signer(tmp_path, monkeypatch):
    """A signer backed by a throwaway key file per test."""
    key_file = tmp_path / "signing_key.pem"
    monkeypatch.setenv("ZDH_SIGNING_KEY_FILE", str(key_file))
    monkeypatch.delenv("ZDH_SIGNING_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("ZDH_SIGNING_KEY_ID", "test-key-1")
    signing.reset_signer_for_tests()
    yield signing.get_signer()
    signing.reset_signer_for_tests()


def _payload(**over):
    base: dict[str, Any] = dict(
        cert_number="ZDH-2026-AAAA-BBBB-CCCC",
        business_name="Acme Ltd",
        registration_number="REG-123",
        level="GOLD",
        score=104,
        total_possible=120,
        issued="2026-07-12",
        expires="2027-07-12",
    )
    base.update(over)
    return signing.build_certificate_payload(**base)


def test_sign_and_verify_roundtrip(signer):
    signed = signer.sign(_payload())
    assert signed["alg"] == "Ed25519"
    assert signed["key_id"] == "test-key-1"
    assert signer.verify(signed) is True


def test_tampered_payload_fails(signer):
    signed = signer.sign(_payload())
    # Attacker bumps the score on the printed certificate.
    signed["payload"]["score"] = 120
    assert signer.verify(signed) is False


def test_tampered_business_fails(signer):
    signed = signer.sign(_payload())
    signed["payload"]["biz"] = "Someone Else Ltd"
    assert signer.verify(signed) is False


def test_bad_signature_fails(signer):
    signed = signer.sign(_payload())
    signed["signature"] = "AAAA" + signed["signature"][4:]
    assert signer.verify(signed) is False


def test_unknown_key_id_fails(signer):
    signed = signer.sign(_payload())
    signed["key_id"] = "no-such-key"
    assert signer.verify(signed) is False


def test_canonical_bytes_are_order_independent():
    a = signing.canonical_bytes({"b": 1, "a": 2})
    b = signing.canonical_bytes({"a": 2, "b": 1})
    assert a == b


def test_verification_block_roundtrip(signer):
    signed = signer.sign(_payload())
    block = signing.encode_verification_block(signed)
    decoded = signing.decode_verification_block(block)
    assert decoded["payload"] == signed["payload"]
    assert decoded["signature"] == signed["signature"]
    assert signer.verify(decoded) is True


def test_verify_block_valid(signer):
    block = signing.encode_verification_block(signer.sign(_payload()))
    out = signing.verify_block(block)
    assert out["valid"] is True
    assert out["payload"]["cert"] == "ZDH-2026-AAAA-BBBB-CCCC"


def test_verify_block_tampered(signer):
    signed = signer.sign(_payload())
    signed["payload"]["score"] = 120        # forge before encoding the block
    block = signing.encode_verification_block(signed)
    out = signing.verify_block(block)
    assert out["valid"] is False
    assert out["payload"] is None           # forged facts are never surfaced


def test_verify_block_garbage(signer):
    assert signing.verify_block("not-a-real-block")["valid"] is False


def test_key_is_stable_across_reload(tmp_path, monkeypatch):
    key_file = tmp_path / "signing_key.pem"
    monkeypatch.setenv("ZDH_SIGNING_KEY_FILE", str(key_file))
    monkeypatch.delenv("ZDH_SIGNING_PRIVATE_KEY", raising=False)

    signing.reset_signer_for_tests()
    s1 = signing.get_signer()
    signed = s1.sign(_payload())
    pub1 = s1.public_key_pem

    # New process simulation: same file must load the same key and still verify.
    signing.reset_signer_for_tests()
    s2 = signing.get_signer()
    assert s2.public_key_pem == pub1
    assert s2.verify(signed) is True


def test_public_keys_pem_active_only(signer):
    keys = signer.public_keys_pem
    assert "test-key-1" in keys
    assert "BEGIN PUBLIC KEY" in keys["test-key-1"]


def test_generate_keypair():
    kp = signing.generate_keypair()
    assert "BEGIN PRIVATE KEY" in kp["private_pem"]
    assert "BEGIN PUBLIC KEY" in kp["public_pem"]


def test_key_rotation_old_certs_still_verify(tmp_path, monkeypatch):
    # --- Original key "k1" signs a certificate ---
    monkeypatch.setenv("ZDH_SIGNING_KEY_FILE", str(tmp_path / "a.pem"))
    monkeypatch.delenv("ZDH_SIGNING_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("ZDH_PUBLIC_KEYS", raising=False)
    monkeypatch.setenv("ZDH_SIGNING_KEY_ID", "k1")
    signing.reset_signer_for_tests()
    s1 = signing.get_signer()
    old_signed = s1.sign(_payload())
    pub1 = s1.public_key_pem

    # --- Rotate to new key "k2", retaining k1's public key for verification ---
    kp = signing.generate_keypair()
    monkeypatch.setenv("ZDH_SIGNING_PRIVATE_KEY", kp["private_pem"])
    monkeypatch.delenv("ZDH_SIGNING_KEY_FILE", raising=False)
    monkeypatch.setenv("ZDH_SIGNING_KEY_ID", "k2")
    monkeypatch.setenv("ZDH_PUBLIC_KEYS", json.dumps({"k1": pub1}))
    signing.reset_signer_for_tests()
    s2 = signing.get_signer()

    assert s2.key_id == "k2"
    assert s2.verify(old_signed) is True               # old cert still verifies
    assert set(s2.public_keys_pem) == {"k1", "k2"}     # both published

    new_signed = s2.sign(_payload())
    assert new_signed["key_id"] == "k2"                # new certs use the new key
    assert s2.verify(new_signed) is True
    signing.reset_signer_for_tests()


def test_public_key_from_env_pem(tmp_path, monkeypatch):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    priv = Ed25519PrivateKey.generate()
    pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    monkeypatch.setenv("ZDH_SIGNING_PRIVATE_KEY", pem)
    monkeypatch.delenv("ZDH_SIGNING_KEY_FILE", raising=False)
    signing.reset_signer_for_tests()
    s = signing.get_signer()
    signed = s.sign(_payload())
    assert s.verify(signed) is True
    signing.reset_signer_for_tests()
