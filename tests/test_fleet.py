"""Tests for distributed multi-node fleet scanning."""

import pytest

import src.agents.master_coordinator as mc
from src.agents.master_coordinator import (
    FleetReport,
    Node,
    NodeResult,
    parse_nodes,
    scan_fleet,
    scan_node,
)
from src.agents.node_agent import create_node_app


# ---------------------------------------------------------------------------
# Node agent — authentication and endpoints
# ---------------------------------------------------------------------------


class TestNodeAgent:
    @pytest.fixture
    def client(self):
        app = create_node_app(token="secret", business_name="unit-test")
        return app.test_client()

    def test_health_is_unauthenticated(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "ok"
        assert "hostname" in body

    def test_scan_without_token_rejected(self, client):
        resp = client.post("/scan")
        assert resp.status_code == 401

    def test_scan_with_wrong_token_rejected(self, client):
        resp = client.post("/scan", headers={"Authorization": "Bearer nope"})
        assert resp.status_code == 401

    def test_scan_with_valid_token_succeeds(self, client):
        resp = client.post("/scan", headers={"Authorization": "Bearer secret"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "ok"
        assert "report" in body
        assert "hardening" in body["report"]

    def test_empty_token_rejected_at_construction(self):
        with pytest.raises(ValueError):
            create_node_app(token="")


# ---------------------------------------------------------------------------
# Node inventory parsing
# ---------------------------------------------------------------------------


class TestParseNodes:
    def test_dict_with_default_token(self):
        nodes = parse_nodes({
            "token": "shared",
            "nodes": [
                {"name": "a", "url": "http://10.0.0.1:8765"},
                {"name": "b", "url": "http://10.0.0.2:8765", "token": "own"},
            ],
        })
        assert nodes[0].token == "shared"
        assert nodes[1].token == "own"

    def test_bare_host_string_gets_scheme_and_port(self):
        nodes = parse_nodes({"nodes": ["10.0.0.5:8765"]})
        assert nodes[0].url == "10.0.0.5:8765" or nodes[0].url.startswith("10.0.0.5")

    def test_host_without_port_gets_default(self):
        nodes = parse_nodes({"nodes": [{"name": "x", "url": "10.0.0.9"}]})
        assert nodes[0].url == f"http://10.0.0.9:{mc.DEFAULT_PORT}"

    def test_plain_list(self):
        nodes = parse_nodes([{"name": "a", "url": "http://h:8765"}])
        assert len(nodes) == 1

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parse_nodes({"nodes": []})

    def test_missing_url_raises(self):
        with pytest.raises(ValueError):
            parse_nodes({"nodes": [{"name": "no-url"}]})

    def test_node_scan_and_health_urls(self):
        n = Node(name="a", url="http://h:8765/")
        assert n.scan_url == "http://h:8765/scan"
        assert n.health_url == "http://h:8765/health"


# ---------------------------------------------------------------------------
# scan_node — with the HTTP layer mocked
# ---------------------------------------------------------------------------


def _report_body(grade="HARDENED", score=90, crit=0, cert="GOLD"):
    return {
        "status": "ok",
        "report": {
            "hostname": "HOST1",
            "assessment": {"certification_level": cert},
            "hardening": {
                "grade": grade,
                "score_percent": score,
                "summary": {"critical_failures": crit},
            },
            "readiness": {"verdict": "READY"},
        },
    }


class TestScanNode:
    def test_online_result_parsed(self, monkeypatch):
        monkeypatch.setattr(mc, "_http_post_json",
                            lambda url, token, timeout: (200, _report_body()))
        r = scan_node(Node("n", "http://h:8765", "t"))
        assert r.status == "online"
        assert r.hardening_grade == "HARDENED"
        assert r.hardening_score == 90
        assert r.cert_level == "GOLD"
        assert r.reachable

    def test_unauthorized(self, monkeypatch):
        monkeypatch.setattr(mc, "_http_post_json",
                            lambda url, token, timeout: (401, {"error": "unauthorized"}))
        r = scan_node(Node("n", "http://h:8765", "bad"))
        assert r.status == "unauthorized"
        assert not r.reachable

    def test_offline_on_connection_error(self, monkeypatch):
        def boom(url, token, timeout):
            raise ConnectionError("refused")
        monkeypatch.setattr(mc, "_http_post_json", boom)
        r = scan_node(Node("n", "http://h:8765", "t"))
        assert r.status == "offline"
        assert "refused" in (r.error or "")

    def test_server_error(self, monkeypatch):
        monkeypatch.setattr(mc, "_http_post_json",
                            lambda url, token, timeout: (500, {"status": "error", "error": "boom"}))
        r = scan_node(Node("n", "http://h:8765", "t"))
        assert r.status == "error"


# ---------------------------------------------------------------------------
# FleetReport aggregation + weakest-link logic
# ---------------------------------------------------------------------------


def _nr(name, status="online", grade="HARDENED", score=90, crit=0):
    return NodeResult(name=name, url=f"http://{name}:8765", status=status,
                      hostname=name.upper(), hardening_grade=grade,
                      hardening_score=score, critical_failures=crit)


class TestFleetReport:
    def test_all_hardened_fleet_hardened(self):
        rep = FleetReport(results=[_nr("a"), _nr("b")])
        assert rep.fleet_grade == "HARDENED"
        assert rep.average_hardening_score == 90

    def test_weakest_link_governs_grade(self):
        rep = FleetReport(results=[
            _nr("a", grade="HARDENED", score=90),
            _nr("b", grade="AT RISK", score=40),
        ])
        assert rep.fleet_grade == "AT RISK"
        assert rep.weakest_node.name == "b"
        assert len(rep.nodes_at_risk) == 1

    def test_unreachable_makes_fleet_incomplete(self):
        rep = FleetReport(results=[
            _nr("a", grade="HARDENED"),
            _nr("b", status="offline", grade=None, score=None),
        ])
        assert rep.fleet_grade == "INCOMPLETE"
        assert len(rep.unreachable) == 1

    def test_no_online_nodes_is_no_data(self):
        rep = FleetReport(results=[_nr("a", status="offline", grade=None, score=None)])
        assert rep.fleet_grade == "NO DATA"

    def test_critical_failures_summed(self):
        rep = FleetReport(results=[_nr("a", crit=1), _nr("b", crit=2)])
        assert rep.total_critical_failures == 3

    def test_to_dict_shape(self):
        rep = FleetReport(results=[_nr("a"), _nr("b", grade="AT RISK", score=30)])
        d = rep.to_dict()
        assert d["fleet_grade"] == "AT RISK"
        assert d["summary"]["total_nodes"] == 2
        assert d["summary"]["weakest_node"] == "b"
        assert len(d["nodes"]) == 2
        # reports excluded by default
        assert "report" not in d["nodes"][0]


# ---------------------------------------------------------------------------
# scan_fleet — concurrency + ordering
# ---------------------------------------------------------------------------


class TestScanFleet:
    def test_scans_all_nodes_and_preserves_order(self, monkeypatch):
        def fake_scan(node, timeout):
            grade = "AT RISK" if node.name == "b" else "HARDENED"
            return _nr(node.name, grade=grade,
                       score=40 if grade == "AT RISK" else 90)
        monkeypatch.setattr(mc, "scan_node", fake_scan)
        nodes = [Node("a", "http://a:8765"), Node("b", "http://b:8765"),
                 Node("c", "http://c:8765")]
        rep = scan_fleet(nodes, timeout=5, max_workers=3)
        assert [r.name for r in rep.results] == ["a", "b", "c"]
        assert rep.fleet_grade == "AT RISK"
        assert rep.weakest_node.name == "b"

    def test_progress_callback_invoked(self, monkeypatch):
        monkeypatch.setattr(mc, "scan_node",
                            lambda node, timeout: _nr(node.name))
        seen = []
        scan_fleet([Node("a", "http://a:8765")], progress=lambda d, t, r: seen.append((d, t)))
        assert seen == [(1, 1)]


# ---------------------------------------------------------------------------
# Local DB persistence
# ---------------------------------------------------------------------------


class TestFleetPersistence:
    def test_save_and_load_roundtrip(self):
        from src.utils import local_db
        rep = FleetReport(results=[_nr("a"), _nr("b", grade="AT RISK", score=30)])
        fid = local_db.save_fleet_report(rep.to_dict())
        assert fid > 0
        loaded = local_db.load_fleet_report(fid)
        assert loaded["fleet_grade"] == "AT RISK"
        listing = local_db.list_fleet_reports(limit=5)
        assert any(row["id"] == fid for row in listing)
