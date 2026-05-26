from src.agents.windows_agent import collect_local_report


def test_agent_runs():
    # Run agent; it will create a report file. We just assert structure.
    r = collect_local_report('test-local')
    assert 'report_path' in r
    assert 'report' in r
    rep = r['report']
    assert 'hostname' in rep
    assert 'readiness' in rep
