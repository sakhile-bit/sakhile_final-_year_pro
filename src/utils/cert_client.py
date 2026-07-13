"""Desktop → portal certificate issuance client.

The desktop app cannot sign certificates itself — the authority's private key
must never ship inside a distributed .exe, or anyone could forge certificates.
Instead the desktop registers a completed, passing assessment with the portal,
which signs it server-side and returns the authoritative certificate.

If the portal is unreachable (offline field use), issuance returns ``None`` and
the caller keeps the result *provisional* until it can sync.

Configuration (checked in order):
* portal URL — ``portal_url`` setting → ``PORTAL_API_URL`` → ``VERIFY_BASE_URL``
  → ``http://localhost:5000`` (the local server, for now).
* API key   — ``issue_api_key`` setting → ``ZDH_ISSUE_API_KEY`` env →
  a dev default that matches the server's dev default.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DEV_API_KEY = "dev-issue-key-change-me"       # must match the server default
_DEFAULT_PORTAL = "http://localhost:5000"


def portal_base_url() -> str:
    from src.utils.local_db import get_setting
    base = (get_setting("portal_url")
            or os.environ.get("PORTAL_API_URL")
            or os.environ.get("VERIFY_BASE_URL")
            or _DEFAULT_PORTAL)
    return base.rstrip("/")


def issue_api_key() -> str:
    from src.utils.local_db import get_setting
    return (get_setting("issue_api_key")
            or os.environ.get("ZDH_ISSUE_API_KEY")
            or _DEV_API_KEY)


def _payload_from_result(result: Any) -> dict:
    bi = result.business_info
    return {
        "business_name": getattr(bi, "name", ""),
        "registration_number": getattr(bi, "id", "") or "",
        "contact_person": getattr(bi, "contact_person", None),
        "contact_email": getattr(bi, "contact_email", None),
        "contact_phone": getattr(bi, "contact_phone", None),
        "industry": getattr(bi, "industry", None),
        "address": getattr(bi, "address", None),
        "province": getattr(bi, "province", None),
        "level": result.certification_level,
        "score": result.score,
        "total_possible": result.total_possible,
        "critical_failures": getattr(result, "critical_failures", 0),
        "assessment_tier": getattr(result, "assessment_tier", "automated"),
        "assessor": "desktop",
    }


def issue_certificate(result: Any, timeout: float = 6.0) -> Optional[dict]:
    """Register a certified assessment with the portal; return the signed
    certificate dict, or ``None`` if issuance failed / the portal is offline.

    Never raises — the desktop must keep working (and fall back to provisional)
    whether or not a portal is reachable.
    """
    if getattr(result, "certification_level", "NOT CERTIFIED") == "NOT CERTIFIED":
        return None
    if getattr(result, "provisional", False):
        return None      # unverified critical checks — not certifiable yet

    try:
        import requests
    except Exception:
        logger.info("requests not available — certificate stays provisional")
        return None

    url = f"{portal_base_url()}/api/certificates/issue"
    try:
        resp = requests.post(
            url, json=_payload_from_result(result),
            headers={"X-API-Key": issue_api_key()}, timeout=timeout,
        )
    except Exception:
        logger.info("Portal unreachable at %s — certificate stays provisional",
                    url, exc_info=True)
        return None

    if resp.status_code in (200, 201):
        try:
            return resp.json()
        except Exception:
            logger.warning("Issuance response was not valid JSON", exc_info=True)
            return None
    logger.warning("Certificate issuance rejected (%s): %s",
                   resp.status_code, resp.text[:200])
    return None
