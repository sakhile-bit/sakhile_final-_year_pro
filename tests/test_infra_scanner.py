from src.security.infra_scanner import scan_host_services


def test_scan_localhost():
    r = scan_host_services('127.0.0.1', ports=[80, 443])
    assert 'host' in r
    assert 'ports' in r
    assert isinstance(r['ports'], list)
