"""
Node Agent — remote scan endpoint
==================================
A small, hardened HTTP server that runs on each infrastructure node so a
central **master node** can trigger a digital-hygiene + hardening scan of
that machine over the network and collect the results.

Security model
--------------
- Every scan request must present a shared secret as ``Authorization:
  Bearer <token>``; the token is compared with ``hmac.compare_digest`` to
  avoid timing leaks. Requests without a valid token get 401.
- The agent NEVER executes commands supplied by the caller. ``/scan`` runs
  exactly one fixed operation — the local scan — so it can't be used as a
  remote-code-execution backdoor.
- ``/health`` is unauthenticated (liveness/discovery only) and returns no
  sensitive data beyond hostname and version.

Usage
-----
    from src.agents.node_agent import run_node_agent
    run_node_agent(host="0.0.0.0", port=8765, token="shared-secret")

or via the CLI:  ``python cli.py node-agent --port 8765 --token <secret>``
"""
from __future__ import annotations

import hmac
import os
import socket
import threading
import time
from functools import wraps
from typing import Optional

from flask import Flask, jsonify, request

from src.agents.windows_agent import collect_local_report
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

AGENT_VERSION = "1.0"
TOKEN_ENV = "NODE_AGENT_TOKEN"


def _extract_bearer(header: Optional[str]) -> str:
    if not header:
        return ""
    parts = header.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return header.strip()


def create_node_app(token: str, business_name: str = "") -> Flask:
    """Create the node agent Flask application.

    Args:
        token: shared secret required on the ``/scan`` endpoint.
        business_name: optional label recorded in scan reports; defaults
            to the machine hostname.
    """
    if not token:
        raise ValueError("A non-empty token is required to start the node agent")

    app = Flask(__name__)
    app.config["NODE_TOKEN"] = token
    app.config["NODE_BUSINESS_NAME"] = business_name or socket.gethostname()

    # A scan is CPU/time heavy. Serialise it so two masters (or a retry)
    # can't pile multiple full scans onto one host at once.
    scan_lock = threading.Lock()

    def require_token(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            supplied = _extract_bearer(request.headers.get("Authorization"))
            expected = app.config["NODE_TOKEN"]
            if not supplied or not hmac.compare_digest(supplied, expected):
                logger.warning(
                    "Rejected unauthenticated scan request from %s",
                    request.remote_addr)
                return jsonify({"error": "unauthorized"}), 401
            return view(*args, **kwargs)
        return wrapper

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "hostname": socket.gethostname(),
            "agent_version": AGENT_VERSION,
        })

    @app.post("/scan")
    @require_token
    def scan():
        if not scan_lock.acquire(blocking=False):
            logger.info("Rejected concurrent scan from %s — already scanning",
                        request.remote_addr)
            return jsonify({
                "status": "busy",
                "error": "a scan is already in progress on this node",
            }), 409
        logger.info("Master node %s requested a scan", request.remote_addr)
        try:
            # save=False — the master node is the system of record
            started = time.monotonic()
            result = collect_local_report(
                business_name=app.config["NODE_BUSINESS_NAME"], save=False)
            duration = round(time.monotonic() - started, 1)
            logger.info("Scan completed in %.1fs for %s",
                        duration, request.remote_addr)
            return jsonify({
                "status": "ok",
                "agent_version": AGENT_VERSION,
                "duration_seconds": duration,
                "report": result["report"],
            })
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Scan failed")
            return jsonify({"status": "error", "error": str(exc)}), 500
        finally:
            scan_lock.release()

    return app


def run_node_agent(host: str = "0.0.0.0", port: int = 8765,
                   token: Optional[str] = None,
                   business_name: str = "") -> None:
    """Start the node agent server (blocking).

    The token is taken from the ``token`` argument or the
    ``NODE_AGENT_TOKEN`` environment variable.
    """
    token = token or os.environ.get(TOKEN_ENV, "")
    app = create_node_app(token, business_name=business_name)
    logger.info("Node agent listening on %s:%s (host=%s)",
                host, port, socket.gethostname())

    # Prefer the production-grade waitress server when available; fall back
    # to the Flask/Werkzeug dev server otherwise.
    try:
        from waitress import serve  # type: ignore[import]
        serve(app, host=host, port=port)
    except ImportError:
        app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the node scan agent")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--token", default=os.environ.get(TOKEN_ENV, ""))
    parser.add_argument("--name", default="", help="Business/node label")
    args = parser.parse_args()

    if not args.token:
        parser.error(
            "A token is required: pass --token or set NODE_AGENT_TOKEN")
    run_node_agent(args.host, args.port, args.token, args.name)
