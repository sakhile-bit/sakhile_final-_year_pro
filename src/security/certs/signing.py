"""Ed25519 certificate signing service.

The authority holds one Ed25519 *private* key; the matching *public* key is
published so anyone can verify a certificate without being able to forge one.

Every certificate is signed over a canonical JSON payload of its material
facts. Change any printed field (business, level, score, dates…) and the
signature no longer matches — that is what makes a copied-and-edited PDF
detectable.

Key resolution (first match wins):

1. ``ZDH_SIGNING_PRIVATE_KEY`` — PEM text in an env var (hosted/prod: a Render
   / Railway secret). Never written to disk.
2. ``ZDH_SIGNING_KEY_FILE``   — path to a PEM file.
3. ``<project>/instance/signing_key.pem`` — dev default. Auto-generated **once**
   if absent (with a loud warning) and then reused, so a dev key stays stable.

Signatures embed a ``key_id`` so keys can be rotated without invalidating
already-issued certificates: verification looks up the public key by id.
Additional retired public keys can be supplied via ``ZDH_PUBLIC_KEYS`` (JSON
mapping ``{key_id: pem}``).
"""
from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, cast

logger = logging.getLogger(__name__)

# Bump when the signed payload shape changes so verifiers can branch on it.
CERT_PAYLOAD_VERSION = 1
_ALG = "Ed25519"
_DEFAULT_KEY_ID = "zdh-ed25519-1"


class SigningUnavailable(RuntimeError):
    """Raised when signing/verification cannot be performed.

    Signing must fail loudly rather than silently emit an unsigned (forgeable)
    certificate, so callers surface this instead of issuing a bad cert.
    """


# ── canonicalisation ───────────────────────────────────────────────────────────

def canonical_bytes(payload: Dict[str, Any]) -> bytes:
    """Deterministic byte encoding of a payload — identical at sign & verify.

    Sorted keys and no incidental whitespace, so two dicts with the same
    contents always produce the same bytes (and thus the same signature).
    """
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _b64e(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")  # type: ignore[arg-type]


def _b64d(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


# ── signer ──────────────────────────────────────────────────────────────────────

class CertSigner:
    """Holds the active private key plus a set of public keys for verifying."""

    def __init__(self) -> None:
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PrivateKey,
            )
        except Exception as exc:  # pragma: no cover - only if dep missing
            raise SigningUnavailable(
                "The 'cryptography' package is required for certificate "
                "signing. Install it with: pip install cryptography"
            ) from exc

        self._serialization = serialization
        self.key_id = os.environ.get("ZDH_SIGNING_KEY_ID", _DEFAULT_KEY_ID)

        priv = self._load_or_create_private_key(Ed25519PrivateKey, serialization)
        self._private = priv
        self._public_pem = priv.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")

        # Public keys usable for verification, keyed by id: the active key plus
        # any retired keys published via ZDH_PUBLIC_KEYS (for rotation).
        self._public_keys: Dict[str, Any] = {self.key_id: priv.public_key()}
        self._load_extra_public_keys(serialization)

    # -- key loading -----------------------------------------------------------
    def _load_or_create_private_key(self, Ed25519PrivateKey, serialization):
        pem_env = os.environ.get("ZDH_SIGNING_PRIVATE_KEY", "").strip()
        if pem_env:
            return serialization.load_pem_private_key(
                pem_env.encode("utf-8"), password=None
            )

        key_path = os.environ.get("ZDH_SIGNING_KEY_FILE", "").strip()
        path = Path(key_path) if key_path else self._default_key_path()

        if path.exists():
            return serialization.load_pem_private_key(
                path.read_bytes(), password=None
            )

        # Dev convenience: generate once and persist, then reuse. A regenerated
        # key would invalidate every previously issued certificate, so we only
        # ever create it when truly absent — and say so loudly.
        logger.warning(
            "No signing key found - generating a NEW Ed25519 key at %s. "
            "This is fine for development, but in production set "
            "ZDH_SIGNING_PRIVATE_KEY (or ZDH_SIGNING_KEY_FILE) so the key is "
            "stable and secret.", path,
        )
        priv = Ed25519PrivateKey.generate()
        pem = priv.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(pem)
            try:
                os.chmod(path, 0o600)   # best-effort; no-op on some platforms
            except OSError:
                pass
        except OSError:
            logger.warning("Could not persist signing key to %s — the key will "
                           "not survive a restart.", path, exc_info=True)
        return priv

    def _load_extra_public_keys(self, serialization) -> None:
        raw = os.environ.get("ZDH_PUBLIC_KEYS", "").strip()
        if not raw:
            return
        try:
            mapping = json.loads(raw)
            for kid, pem in mapping.items():
                self._public_keys[kid] = serialization.load_pem_public_key(
                    pem.encode("utf-8")
                )
        except Exception:  # pragma: no cover - defensive
            logger.warning("Could not parse ZDH_PUBLIC_KEYS", exc_info=True)

    @staticmethod
    def _default_key_path() -> Path:
        root = Path(__file__).resolve().parents[3]   # project root
        return root / "instance" / "signing_key.pem"

    # -- public surface --------------------------------------------------------
    @property
    def public_key_pem(self) -> str:
        return self._public_pem

    @property
    def public_keys_pem(self) -> Dict[str, str]:
        """All verification public keys as PEM, keyed by id (active + retired).

        Published so verifiers can still check certificates signed by a rotated
        (now-retired) key.
        """
        out: Dict[str, str] = {}
        for kid, pub in self._public_keys.items():
            try:
                out[kid] = pub.public_bytes(
                    self._serialization.Encoding.PEM,
                    self._serialization.PublicFormat.SubjectPublicKeyInfo,
                ).decode("ascii")
            except Exception:  # pragma: no cover - defensive
                continue
        return out

    def sign(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sign ``payload`` and return a self-describing signed envelope."""
        signer = getattr(self._private, "sign", None)
        if not callable(signer):
            raise SigningUnavailable("Loaded private key cannot sign payloads")
        signature: bytes = cast(bytes, signer(canonical_bytes(payload)))
        return {
            "payload": payload,
            "signature": _b64e(signature),
            "key_id": self.key_id,
            "alg": _ALG,
        }

    def verify(self, signed: Dict[str, Any]) -> bool:
        """Return True iff ``signed`` carries a valid signature we can check."""
        try:
            from cryptography.exceptions import InvalidSignature
        except Exception:  # pragma: no cover
            raise SigningUnavailable("cryptography is required for verification")

        if not isinstance(signed, dict):
            return False
        payload = signed.get("payload")
        sig_b64 = signed.get("signature")
        key_id = signed.get("key_id")
        if (not payload or not sig_b64 or not isinstance(key_id, str)
                or signed.get("alg", _ALG) != _ALG):
            return False

        public_key = self._public_keys.get(key_id)
        if public_key is None:
            logger.warning("No public key on record for key_id=%r", key_id)
            return False
        try:
            public_key.verify(_b64d(sig_b64), canonical_bytes(payload))
            return True
        except InvalidSignature:
            return False
        except Exception:  # pragma: no cover - malformed input
            return False


_signer: Optional[CertSigner] = None


def get_signer() -> CertSigner:
    """Return the process-wide signer, constructing it on first use."""
    global _signer
    if _signer is None:
        _signer = CertSigner()
    return _signer


def reset_signer_for_tests() -> None:
    """Drop the cached signer so a test can re-resolve keys from the env."""
    global _signer
    _signer = None


# ── module-level convenience API ────────────────────────────────────────────────

def sign_certificate(payload: Dict[str, Any]) -> Dict[str, Any]:
    return get_signer().sign(payload)


def verify_certificate(signed: Dict[str, Any]) -> bool:
    return get_signer().verify(signed)


# ── offline verification block ──────────────────────────────────────────────────
# A compact, URL-safe base64 string printed on the certificate. An inspector
# with no connectivity can paste it into the offline verifier, which checks the
# signature against the published public key — no server round-trip needed.

def encode_verification_block(signed: Dict[str, Any]) -> str:
    compact = {
        "p": signed["payload"],
        "s": signed["signature"],
        "k": signed.get("key_id"),
        "a": signed.get("alg", _ALG),
    }
    raw = json.dumps(compact, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_verification_block(block: str) -> Dict[str, Any]:
    raw = base64.urlsafe_b64decode(block.strip().encode("ascii"))
    compact = json.loads(raw.decode("utf-8"))
    return {
        "payload": compact.get("p"),
        "signature": compact.get("s"),
        "key_id": compact.get("k"),
        "alg": compact.get("a", _ALG),
    }


def verify_block(block: str) -> Dict[str, Any]:
    """Offline verification: decode a verification block and check its signature.

    Returns ``{"valid": bool, "payload": dict | None}``. ``payload`` is included
    only when the signature is valid, so a failed check can't surface forged
    facts as if they were trustworthy.
    """
    try:
        signed = decode_verification_block(block)
    except Exception:
        return {"valid": False, "payload": None}
    ok = False
    try:
        ok = verify_certificate(signed)
    except Exception:
        ok = False
    return {"valid": bool(ok), "payload": signed.get("payload") if ok else None}


def build_certificate_payload(
    *,
    cert_number: str,
    business_name: str,
    registration_number: str,
    level: str,
    score: int,
    total_possible: int,
    issued: str,
    expires: str,
    framework: str = "ZDH-1.0",
) -> Dict[str, Any]:
    """Assemble the canonical set of facts that get signed for a certificate.

    Keep this the single source of truth for the payload shape so the issuer
    and every verifier agree byte-for-byte.
    """
    return {
        "v": CERT_PAYLOAD_VERSION,
        "cert": cert_number,
        "biz": business_name or "",
        "reg": registration_number or "",
        "level": level,
        "score": int(score),
        "total": int(total_possible),
        "issued": issued,
        "expires": expires,
        "framework": framework,
    }


def generate_keypair() -> Dict[str, str]:
    """Generate a fresh Ed25519 key pair for key rotation.

    Returns ``{"private_pem": ..., "public_pem": ...}``. Rotation procedure:
    set the new private key as ``ZDH_SIGNING_PRIVATE_KEY`` and bump
    ``ZDH_SIGNING_KEY_ID``; append the *previous* public key to
    ``ZDH_PUBLIC_KEYS`` so certificates signed by it still verify.
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except Exception as exc:  # pragma: no cover
        raise SigningUnavailable("cryptography is required to generate keys") from exc

    priv = Ed25519PrivateKey.generate()
    private_pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("ascii")
    public_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return {"private_pem": private_pem, "public_pem": public_pem}
