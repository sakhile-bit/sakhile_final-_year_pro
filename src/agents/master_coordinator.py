"""
Master Coordinator — distributed fleet scanning
===============================================
Runs on the **master node**. Given an inventory of connected infrastructure
nodes (each running ``node_agent``), it triggers a scan on every node
concurrently, collects the reports, and rolls them up into a single
``FleetReport`` with a *weakest-link* view of the whole estate.

The guiding idea of the project: a business is only as safe as the least
hygienic machine in its infrastructure. This module makes that weakest link
visible across many nodes from one place.

Node inventory format (YAML or JSON)::

    nodes:
      - name: file-server
        url: http://192.168.1.10:8765
        token: shared-secret
      - name: pos-backoffice
        url: http://192.168.1.11:8765
        token: shared-secret

A top-level ``token`` may be given as a default for nodes that omit one.
"""
from __future__ import annotations

import concurrent.futures
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_PORT = 8765
NODE_STATUS_ONLINE = "online"
NODE_STATUS_OFFLINE = "offline"
NODE_STATUS_UNAUTHORIZED = "unauthorized"
NODE_STATUS_ERROR = "error"


@dataclass
class Node:
    """A single infrastructure node the master can scan."""
    name: str
    url: str
    token: str = ""

    @property
    def scan_url(self) -> str:
        return self.url.rstrip("/") + "/scan"

    @property
    def health_url(self) -> str:
        return self.url.rstrip("/") + "/health"


@dataclass
class NodeResult:
    """Outcome of scanning one node."""
    name: str
    url: str
    status: str                       # online / offline / unauthorized / error
    hostname: Optional[str] = None
    cert_level: Optional[str] = None
    hardening_grade: Optional[str] = None
    hardening_score: Optional[int] = None
    readiness_verdict: Optional[str] = None
    critical_failures: int = 0
    error: Optional[str] = None
    report: Optional[Dict[str, Any]] = field(default=None, repr=False)

    @property
    def reachable(self) -> bool:
        return self.status == NODE_STATUS_ONLINE

    def to_dict(self, include_report: bool = False) -> Dict[str, Any]:
        d = {
            "name": self.name,
            "url": self.url,
            "status": self.status,
            "hostname": self.hostname,
            "cert_level": self.cert_level,
            "hardening_grade": self.hardening_grade,
            "hardening_score": self.hardening_score,
            "readiness_verdict": self.readiness_verdict,
            "critical_failures": self.critical_failures,
            "error": self.error,
        }
        if include_report:
            d["report"] = self.report
        return d


# Order used to find the "weakest" node — worst first
_HARDENING_RANK = {"AT RISK": 0, "NEEDS ATTENTION": 1, "HARDENED": 2,
                   "NOT APPLICABLE": 3, None: 4}


@dataclass
class FleetReport:
    """Aggregate of scanning every node in the fleet."""
    results: List[NodeResult] = field(default_factory=list)
    scanned_at: str = ""

    def __post_init__(self):
        self.scanned_at = self.scanned_at or datetime.now(
            timezone.utc).isoformat().replace("+00:00", "Z")

    @property
    def total_nodes(self) -> int:
        return len(self.results)

    @property
    def online(self) -> List[NodeResult]:
        return [r for r in self.results if r.reachable]

    @property
    def unreachable(self) -> List[NodeResult]:
        return [r for r in self.results if not r.reachable]

    @property
    def nodes_at_risk(self) -> List[NodeResult]:
        return [r for r in self.online if r.hardening_grade == "AT RISK"]

    @property
    def total_critical_failures(self) -> int:
        return sum(r.critical_failures for r in self.online)

    @property
    def average_hardening_score(self) -> int:
        scores = [r.hardening_score for r in self.online
                  if r.hardening_score is not None]
        return round(sum(scores) / len(scores)) if scores else 0

    @property
    def weakest_node(self) -> Optional[NodeResult]:
        """The online node representing the fleet's weakest link."""
        if not self.online:
            return None
        return min(
            self.online,
            key=lambda r: (
                _HARDENING_RANK.get(r.hardening_grade, 4),
                r.hardening_score if r.hardening_score is not None else 100,
                -r.critical_failures,
            ),
        )

    @property
    def fleet_grade(self) -> str:
        """Fleet grade is governed by the weakest reachable node.

        If any node could not be reached we cannot certify the fleet, so the
        grade is INCOMPLETE — an unknown node is an unmanaged risk.
        """
        if not self.online:
            return "NO DATA"
        if self.unreachable:
            return "INCOMPLETE"
        weakest = self.weakest_node
        grade = weakest.hardening_grade if weakest else None
        return grade or "NO DATA"

    def to_dict(self, include_reports: bool = False) -> Dict[str, Any]:
        weakest = self.weakest_node
        return {
            "scanned_at": self.scanned_at,
            "fleet_grade": self.fleet_grade,
            "summary": {
                "total_nodes": self.total_nodes,
                "online": len(self.online),
                "unreachable": len(self.unreachable),
                "nodes_at_risk": len(self.nodes_at_risk),
                "total_critical_failures": self.total_critical_failures,
                "average_hardening_score": self.average_hardening_score,
                "weakest_node": weakest.name if weakest else None,
            },
            "nodes": [r.to_dict(include_report=include_reports)
                      for r in self.results],
        }


# ---------------------------------------------------------------------------
# Node inventory loading
# ---------------------------------------------------------------------------


def load_nodes(path: str) -> List[Node]:
    """Load a node inventory from a YAML or JSON file."""
    text = Path(path).read_text(encoding="utf-8")
    data: Any
    if path.lower().endswith((".yaml", ".yml")):
        import yaml
        data = yaml.safe_load(text)
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            import yaml
            data = yaml.safe_load(text)
    return parse_nodes(data)


def parse_nodes(data: Any) -> List[Node]:
    """Turn a parsed inventory structure into a list of Node objects."""
    if isinstance(data, dict):
        default_token = data.get("token", "")
        raw_nodes = data.get("nodes", [])
    elif isinstance(data, list):
        default_token = ""
        raw_nodes = data
    else:
        raise ValueError("Node inventory must be a mapping or a list")

    nodes: List[Node] = []
    for i, entry in enumerate(raw_nodes):
        if isinstance(entry, str):
            url = entry
            name = entry
            token = default_token
        elif isinstance(entry, dict):
            url = entry.get("url") or entry.get("host") or ""
            if url and "://" not in url:
                url = f"http://{url}"
                if url.count(":") < 2:  # no explicit port
                    url = f"{url}:{DEFAULT_PORT}"
            name = entry.get("name") or url or f"node-{i + 1}"
            token = entry.get("token", default_token)
        else:
            raise ValueError(f"Invalid node entry: {entry!r}")
        if not url:
            raise ValueError(f"Node '{name}' is missing a url")
        nodes.append(Node(name=name, url=url, token=token))
    if not nodes:
        raise ValueError("Node inventory contains no nodes")
    return nodes


# ---------------------------------------------------------------------------
# HTTP transport (prefers requests, falls back to urllib)
# ---------------------------------------------------------------------------


def _http_post_json(url: str, token: str, timeout: float) -> Any:
    """POST to a node's /scan endpoint. Returns (status_code, json_body).

    Raises the underlying exception on connection failure.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        import requests  # type: ignore[import]
        resp = requests.post(url, headers=headers, json={}, timeout=timeout)
        try:
            body = resp.json()
        except ValueError:
            body = {}
        return resp.status_code, body
    except ImportError:
        req = urllib.request.Request(
            url, data=b"{}", headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, json.loads(r.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as exc:
            try:
                body = json.loads(exc.read().decode("utf-8") or "{}")
            except Exception:
                body = {}
            return exc.code, body


def scan_node(node: Node, timeout: float = 60.0) -> NodeResult:
    """Trigger a scan on a single node and summarise the result."""
    logger.info("Scanning node %s (%s)", node.name, node.url)
    try:
        status_code, body = _http_post_json(node.scan_url, node.token, timeout)
    except Exception as exc:
        logger.warning("Node %s unreachable: %s", node.name, exc)
        return NodeResult(name=node.name, url=node.url,
                          status=NODE_STATUS_OFFLINE, error=str(exc))

    if status_code == 401:
        return NodeResult(name=node.name, url=node.url,
                          status=NODE_STATUS_UNAUTHORIZED,
                          error="Authentication failed — check the node token")
    if status_code != 200 or body.get("status") != "ok":
        return NodeResult(
            name=node.name, url=node.url, status=NODE_STATUS_ERROR,
            error=body.get("error", f"HTTP {status_code}"))

    report = body.get("report", {})
    assessment = report.get("assessment", {})
    hardening = report.get("hardening", {})
    readiness = report.get("readiness", {})
    return NodeResult(
        name=node.name, url=node.url, status=NODE_STATUS_ONLINE,
        hostname=report.get("hostname"),
        cert_level=assessment.get("certification_level"),
        hardening_grade=hardening.get("grade"),
        hardening_score=hardening.get("score_percent"),
        readiness_verdict=readiness.get("verdict"),
        critical_failures=hardening.get("summary", {}).get(
            "critical_failures", 0),
        report=report,
    )


def check_node_health(node: Node, timeout: float = 5.0) -> bool:
    """Return True if a node's /health endpoint responds ok."""
    try:
        req = urllib.request.Request(node.health_url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8") or "{}")
            return data.get("status") == "ok"
    except Exception:
        return False


def scan_fleet(nodes: List[Node], timeout: float = 60.0,
               max_workers: int = 10,
               progress=None) -> FleetReport:
    """Scan every node concurrently and aggregate into a FleetReport.

    Args:
        nodes: node inventory to scan.
        timeout: per-node scan timeout in seconds.
        max_workers: max concurrent node scans.
        progress: optional callback ``progress(done, total, node_result)``
            invoked after each node completes (for GUIs/CLIs).
    """
    results: List[NodeResult] = []
    total = len(nodes)
    workers = max(1, min(max_workers, total))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_node = {
            pool.submit(scan_node, node, timeout): node for node in nodes
        }
        for future in concurrent.futures.as_completed(future_to_node):
            node = future_to_node[future]
            try:
                result = future.result()
            except Exception as exc:  # pragma: no cover - defensive
                result = NodeResult(name=node.name, url=node.url,
                                    status=NODE_STATUS_ERROR, error=str(exc))
            results.append(result)
            if progress is not None:
                try:
                    progress(len(results), total, result)
                except Exception:
                    pass

    # Keep the original inventory order for stable presentation
    order = {node.name: i for i, node in enumerate(nodes)}
    results.sort(key=lambda r: order.get(r.name, 0))
    report = FleetReport(results=results)
    logger.info(
        "Fleet scan complete: %s — %d/%d online, weakest=%s",
        report.fleet_grade, len(report.online), total,
        report.weakest_node.name if report.weakest_node else "n/a")
    return report
