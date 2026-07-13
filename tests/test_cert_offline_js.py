"""Cross-language validation of the browser offline verifier.

Runs the *actual* offline_verify.js (the code shipped to inspectors' browsers)
under Node against blocks produced by the Python signer. This proves the JS
canonicalisation and Ed25519 verification agree with Python byte-for-byte —
including a non-ASCII business name, the riskiest canonicalisation case.
"""

import json
import os
import shutil
import subprocess

import pytest

from src.security.certs import signing

NODE = shutil.which("node")
JS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "src", "web", "static", "js", "offline_verify.js",
)

pytestmark = pytest.mark.skipif(NODE is None, reason="node.js not installed")


@pytest.fixture()
def signer(tmp_path, monkeypatch):
    monkeypatch.setenv("ZDH_SIGNING_KEY_FILE", str(tmp_path / "k.pem"))
    monkeypatch.delenv("ZDH_SIGNING_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("ZDH_SIGNING_KEY_ID", "test-key-1")
    signing.reset_signer_for_tests()
    yield signing.get_signer()
    signing.reset_signer_for_tests()


def _payload():
    return signing.build_certificate_payload(
        cert_number="ZDH-2026-AAAA-BBBB-CCCC",
        business_name="Açme Ađżŕ Ltd",      # non-ASCII: stresses canonicalisation
        registration_number="REG-1", level="GOLD",
        score=104, total_possible=120,
        issued="2026-07-12", expires="2027-07-12",
    )


def _run_node(block, pem, tmp_path):
    assert NODE is not None      # guarded by the module-level skipif
    harness = tmp_path / "harness.cjs"
    harness.write_text(
        "const ov = require(process.argv[2]);\n"
        "ov.verifyBlock(process.argv[3], process.argv[4])\n"
        "  .then(r => process.stdout.write(JSON.stringify(r)))\n"
        "  .catch(e => process.stdout.write(JSON.stringify({error:String(e)})));\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [NODE, str(harness), JS_PATH, block, pem],
        capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_node_verifies_genuine_block(signer, tmp_path):
    block = signing.encode_verification_block(signer.sign(_payload()))
    res = _run_node(block, signer.public_key_pem, tmp_path)
    assert res.get("error") is None, res
    assert res["valid"] is True
    assert res["payload"]["cert"] == "ZDH-2026-AAAA-BBBB-CCCC"
    assert res["payload"]["biz"] == "Açme Ađżŕ Ltd"


def test_node_rejects_tampered_block(signer, tmp_path):
    signed = signer.sign(_payload())
    signed["payload"]["score"] = 120          # forge the score
    block = signing.encode_verification_block(signed)
    res = _run_node(block, signer.public_key_pem, tmp_path)
    assert res["valid"] is False


def test_node_rejects_wrong_key(signer, tmp_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    other_pub = Ed25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    block = signing.encode_verification_block(signer.sign(_payload()))
    res = _run_node(block, other_pub, tmp_path)     # verify against a different key
    assert res["valid"] is False
