"""Certificate signing & verification — the anti-forgery core.

Issued certificates carry an Ed25519 signature over their material facts
(number, business, level, score, issue/expiry). Anyone can verify a
certificate with the *public* key alone — online via the portal, or offline
against the published key — while only the authority can issue new ones.
"""

from src.security.certs.signing import (
    CERT_PAYLOAD_VERSION,
    SigningUnavailable,
    build_certificate_payload,
    canonical_bytes,
    decode_verification_block,
    encode_verification_block,
    get_signer,
    sign_certificate,
    verify_block,
    verify_certificate,
)

__all__ = [
    "CERT_PAYLOAD_VERSION",
    "SigningUnavailable",
    "build_certificate_payload",
    "canonical_bytes",
    "decode_verification_block",
    "encode_verification_block",
    "get_signer",
    "sign_certificate",
    "verify_block",
    "verify_certificate",
]
