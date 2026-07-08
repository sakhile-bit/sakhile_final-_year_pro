"""Tests for the agent-related CLI commands."""

from click.testing import CliRunner

import src.utils.cli as climod


_FAKE_REPORT = {
    "hostname": "TESTHOST",
    "collected_at": "2026-07-08T00:00:00Z",
    "assessment": {"score": 90, "total_possible": 120,
                   "certification_level": "SILVER"},
    "hardening": {"grade": "HARDENED", "score_percent": 88,
                  "summary": {"critical_failures": 0}},
    "readiness": {"verdict": "READY"},
}


def test_cli_lists_agent_commands():
    result = CliRunner().invoke(climod.cli, ["--help"])
    assert result.exit_code == 0
    for cmd in ("agent", "agent-reports", "node-agent", "fleet-scan", "harden"):
        assert cmd in result.output


def test_agent_command_runs(monkeypatch):
    import src.agents.windows_agent as wa
    monkeypatch.setattr(
        wa, "collect_local_report",
        lambda business_name="local-host", save=True: {
            "report_id": 1 if save else None, "report": _FAKE_REPORT})

    result = CliRunner().invoke(climod.cli, ["agent", "--no-save"])
    assert result.exit_code == 0, result.output
    assert "TESTHOST" in result.output
    assert "SILVER" in result.output
    assert "HARDENED" in result.output


def test_agent_json_out(monkeypatch):
    import src.agents.windows_agent as wa
    monkeypatch.setattr(
        wa, "collect_local_report",
        lambda business_name="local-host", save=True: {
            "report_id": None, "report": _FAKE_REPORT})

    result = CliRunner().invoke(climod.cli, ["agent", "--no-save", "--json-out"])
    assert result.exit_code == 0
    # Rich colourises JSON output, so assert on the values, not exact JSON text.
    assert "TESTHOST" in result.output
    assert "READY" in result.output


def test_agent_reports_empty(monkeypatch):
    monkeypatch.setattr(climod, "_json", climod._json)  # no-op, keep import
    import src.utils.local_db as db
    monkeypatch.setattr(db, "list_agent_reports", lambda limit=20: [])
    result = CliRunner().invoke(climod.cli, ["agent-reports"])
    assert result.exit_code == 0
    assert "No agent reports" in result.output


def test_agent_reports_lists(monkeypatch):
    import src.utils.local_db as db
    monkeypatch.setattr(
        db, "list_agent_reports",
        lambda limit=20: [{"id": 1, "hostname": "TESTHOST",
                           "collected_at": "2026-07-08T00:00:00Z"}])
    result = CliRunner().invoke(climod.cli, ["agent-reports"])
    assert result.exit_code == 0
    assert "TESTHOST" in result.output


def test_agent_reports_show_missing(monkeypatch):
    import src.utils.local_db as db
    monkeypatch.setattr(db, "load_agent_report", lambda rid: None)
    result = CliRunner().invoke(climod.cli, ["agent-reports", "--show", "999"])
    assert result.exit_code == 1
    assert "No agent report" in result.output
