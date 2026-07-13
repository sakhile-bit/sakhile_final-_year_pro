"""Shared rendering helpers for certificates: verification URLs and QR codes.

Used by both the web certificate page and the desktop PDF/HTML report so the
QR code and "verify at…" link are produced the same way everywhere.

The verification base URL is configurable so the same code works against a
local server today and a real hosted portal later — set ``VERIFY_BASE_URL``
(or ``PORTAL_BASE_URL``) when the host exists; until then it defaults to the
local dev server.
"""
from __future__ import annotations

import base64
import io
import logging
import os

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "http://localhost:5000"


def verify_base_url() -> str:
    """Base URL of the verification portal (no trailing slash)."""
    base = (os.environ.get("VERIFY_BASE_URL")
            or os.environ.get("PORTAL_BASE_URL")
            or _DEFAULT_BASE_URL)
    return base.rstrip("/")


def verify_url(certificate_number: str, base: str | None = None) -> str:
    """Full public verification URL for a certificate number.

    ``base`` overrides the configured base (e.g. the web route passes the
    request's own host so a locally-served page yields a scannable link).
    """
    root = (base or verify_base_url()).rstrip("/")
    return f"{root}/verify/{certificate_number}"


def qr_png_bytes(data: str, box_size: int = 8, border: int = 2) -> bytes | None:
    """Render ``data`` to a PNG QR code, or ``None`` if qrcode is unavailable."""
    try:
        import qrcode
    except Exception:  # pragma: no cover - dependency missing
        logger.warning("qrcode not installed — QR code omitted", exc_info=True)
        return None
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()
    except Exception:  # pragma: no cover - defensive
        logger.warning("QR code generation failed", exc_info=True)
        return None


def qr_data_uri(data: str, box_size: int = 8, border: int = 2) -> str | None:
    """QR code as a ``data:image/png;base64,…`` URI for inline HTML embedding."""
    png = qr_png_bytes(data, box_size=box_size, border=border)
    if png is None:
        return None
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")
