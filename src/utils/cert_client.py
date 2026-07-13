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

import json
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


def build_issue_payload(result: Any) -> dict:
    """The JSON body the portal signs for an assessment.

    Exposed publicly so a certificate that could not be issued offline can be
    stored with its request payload and registered later by a background sync,
    without re-running the scan.
    """
    return _payload_from_result(result)


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
    return _post_issue(build_issue_payload(result), timeout)


def _post_issue(payload: dict, timeout: float) -> Optional[dict]:
    """POST a pre-built issuance payload to the portal; return the signed
    certificate dict, or ``None`` if the portal is offline / rejects it.

    Shared by live issuance and the deferred sync so both hit the endpoint the
    same way. Never raises.
    """
    try:
        import requests
    except Exception:
        logger.info("requests not available — certificate stays provisional")
        return None

    url = f"{portal_base_url()}/api/certificates/issue"
    try:
        resp = requests.post(
            url, json=payload,
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


def _stored_issue_payload(row: dict) -> Optional[dict]:
    """Pull the queued issuance payload out of a stored provisional cert row."""
    raw = row.get("payload")
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    ip = data.get("issue_payload") if isinstance(data, dict) else None
    return ip if isinstance(ip, dict) else None


def _payload_from_assessment(row_id: int) -> Optional[dict]:
    """Rebuild an issuance payload from a stored assessment.

    Fallback for certificates that went provisional *before* the queued payload
    was persisted (legacy rows): the assessment itself still holds every signed
    fact (business, level, score, totals), so they can be registered without
    re-running the scan. Returns ``None`` if the assessment is missing or does
    not qualify for a certificate.
    """
    try:
        from src.utils.local_db import get_assessment
        a = get_assessment(row_id)
    except Exception:
        return None
    if not a:
        return None
    level = a.get("certification_level")
    if not level or level == "NOT CERTIFIED":
        return None
    biz = a.get("business") or {}
    return {
        "business_name": biz.get("name", ""),
        "registration_number": biz.get("id", "") or "",
        "contact_person": biz.get("contact_person"),
        "industry": biz.get("industry"),
        "province": biz.get("province"),
        "level": level,
        "score": a.get("score", 0),
        "total_possible": a.get("total_possible", 0),
        "critical_failures": a.get("critical_failures", 0),
        "assessment_tier": "automated",
        "assessor": "desktop",
    }


def sync_provisional_certificates(timeout: float = 6.0) -> int:
    """Register any certificates left provisional while the portal was offline.

    For each provisional row that carries its queued issuance payload, re-POST
    it; on success the local mirror is upgraded from PROVISIONAL to REGISTERED
    with the portal's real signature. Returns the number upgraded.

    Meant to run in the background at startup (and any time connectivity may
    have returned). Never raises — if the portal is still unreachable the rows
    simply stay provisional for the next attempt.
    """
    try:
        from src.utils.local_db import (
            list_provisional_certificates, save_certificate)
    except Exception:
        return 0
    try:
        rows = list_provisional_certificates()
    except Exception:
        logger.info("Could not list provisional certificates", exc_info=True)
        return 0
    if not rows:
        return 0

    synced = 0
    for row in rows:
        aid = row.get("assessment_id")
        if aid is None:
            continue
        # Prefer the payload queued at assessment time; fall back to rebuilding
        # it from the stored assessment for legacy rows that predate queuing.
        payload = _stored_issue_payload(row) or _payload_from_assessment(aid)
        if not payload:
            continue        # not certifiable / assessment gone
        cert = _post_issue(payload, timeout)
        if not cert or not cert.get("certificate_number"):
            continue        # portal still offline / rejected — try again later
        try:
            save_certificate(aid, "REGISTERED", cert)
            synced += 1
        except Exception:
            logger.warning("Failed to persist synced certificate for "
                           "assessment %s", aid, exc_info=True)
    if synced:
        logger.info("Auto-registered %d previously-provisional certificate(s)",
                    synced)
    return synced
