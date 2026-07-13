"""Minimal in-process rate limiting for public endpoints.

The public certificate-verification endpoints are unauthenticated and expose a
lookup by certificate number, so they are the natural target for enumeration
("try every ZDH-2026-… and harvest the valid ones"). A per-IP sliding-window
cap makes bulk scraping impractical without adding an external dependency.

Scope note: state lives in this process only. That is sufficient for a single
worker; a multi-worker / multi-host deployment should move this to a shared
store (e.g. Redis) so the limit is enforced fleet-wide.
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from functools import wraps
from typing import Deque, Dict

from flask import jsonify, request

_lock = threading.Lock()
_hits: Dict[str, Deque[float]] = defaultdict(deque)

# Safety cap on distinct client keys tracked at once. Prevents a spoofed-IP
# flood from growing the map without bound (memory DoS); stale buckets are
# pruned when the cap is exceeded.
_MAX_TRACKED = 20000


def _trust_proxy() -> bool:
    return os.environ.get("TRUST_PROXY", "").lower() in ("1", "true", "yes", "on")


def _client_ip() -> str:
    # X-Forwarded-For is client-supplied and trivially spoofable, so only honour
    # it when the operator has declared the app sits behind a trusted proxy
    # (TRUST_PROXY=1, e.g. Render/Railway). Otherwise use the socket peer so an
    # attacker can't dodge the per-IP limit by rotating the header.
    if _trust_proxy():
        fwd = request.headers.get("X-Forwarded-For", "")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _prune_locked(cutoff: float) -> None:
    stale = [k for k, q in _hits.items() if not q or q[-1] < cutoff]
    for k in stale:
        del _hits[k]


def _allow(key: str, limit: int, window_s: float) -> bool:
    now = time.monotonic()
    cutoff = now - window_s
    with _lock:
        q = _hits[key]
        while q and q[0] < cutoff:
            q.popleft()
        allowed = len(q) < limit
        if allowed:
            q.append(now)
        if not q:                       # nothing recent — don't retain the key
            _hits.pop(key, None)
        elif len(_hits) > _MAX_TRACKED:
            _prune_locked(cutoff)
        return allowed


def rate_limit(limit: int = 30, window_s: float = 60.0, scope: str = "default"):
    """Decorator: allow at most ``limit`` requests per ``window_s`` per client IP.

    On breach returns HTTP 429. JSON for ``/api`` paths, otherwise a short text
    body, so it fits both the HTML page and the API endpoint.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = f"{scope}:{_client_ip()}"
            if not _allow(key, limit, window_s):
                retry = int(window_s)
                if request.path.startswith("/api"):
                    resp = jsonify({
                        "error": "rate_limited",
                        "message": "Too many requests. Please slow down.",
                    })
                else:
                    resp = ("Too many requests. Please wait a moment and try "
                            "again.", 429)
                    return resp
                resp.status_code = 429
                resp.headers["Retry-After"] = str(retry)
                return resp
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def reset_for_tests() -> None:
    with _lock:
        _hits.clear()
