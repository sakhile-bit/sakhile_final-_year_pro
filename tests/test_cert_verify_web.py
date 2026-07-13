"""End-to-end tests for the public certificate verification surfaces."""

import json
from datetime import date, timedelta

import pytest

from src.web.app import create_app, db as _db
from src.web.app import Business, Assessment, Certificate, _issue_signed_certificate
from src.web import ratelimit
from src.security.certs import signing


@pytest.fixture(autouse=True)
def _signing_key(tmp_path, monkeypatch):
    """Back the signer with a throwaway key and reset rate limits per test."""
    monkeypatch.setenv("ZDH_SIGNING_KEY_FILE", str(tmp_path / "k.pem"))
    monkeypatch.delenv("ZDH_SIGNING_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("ZDH_PUBLIC_KEYS", raising=False)
    monkeypatch.setenv("ZDH_SIGNING_KEY_ID", "test-key-1")
    signing.reset_signer_for_tests()
    ratelimit.reset_for_tests()
    yield
    signing.reset_signer_for_tests()
    ratelimit.reset_for_tests()


@pytest.fixture
def app():
    application = create_app(db_uri='sqlite:///:memory:')
    application.config['TESTING'] = True
    application.config['WTF_CSRF_ENABLED'] = False
    with application.app_context():
        _db.create_all()
    yield application
    with application.app_context():
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _seed_cert(app, level="GOLD", score=104, expires_in_days=365):
    """Create a business + assessment + signed certificate; return its number."""
    with app.app_context():
        biz = Business(name="Acme Ltd", registration_number="REG-1")
        _db.session.add(biz)
        _db.session.commit()
        assessment = Assessment(
            business_id=biz.id,
            controls_results={'total_possible': 120},
            total_score=score,
            certification_level=level,
            status='completed',
        )
        _db.session.add(assessment)
        _db.session.commit()
        cert = _issue_signed_certificate(
            assessment=assessment, business=biz, level=level,
            score=score, total_possible=120, assessor_username="tester",
        )
        if expires_in_days != 365:
            cert.expiry_date = date.today() + timedelta(days=expires_in_days)
            _db.session.commit()
        return cert.certificate_number


def test_valid_certificate(app, client):
    num = _seed_cert(app)
    resp = client.get(f'/api/verify/{num}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['valid'] is True
    assert data['status'] == 'VALID'
    assert data['signature_valid'] is True
    assert data['business_name'] == 'Acme Ltd'
    assert data['level'] == 'GOLD'


def test_not_found(client):
    resp = client.get('/api/verify/ZDH-2026-0000-0000-0000')
    assert resp.status_code == 404
    data = resp.get_json()
    assert data['found'] is False
    assert data['status'] == 'NOT_FOUND'


def test_tampered_certificate_reads_invalid(app, client):
    num = _seed_cert(app)
    # Forge: bump the score in the stored signed payload.
    with app.app_context():
        from src.web.app import Certificate
        cert = Certificate.query.filter_by(certificate_number=num).first()
        assert cert is not None
        data = dict(cert.certificate_data)
        data['signature'] = dict(data['signature'])
        data['signature']['payload'] = dict(data['signature']['payload'])
        data['signature']['payload']['score'] = 120
        cert.certificate_data = data
        _db.session.commit()

    resp = client.get(f'/api/verify/{num}')
    data = resp.get_json()
    assert data['status'] == 'INVALID'
    assert data['valid'] is False
    assert data['signature_valid'] is False


def test_revoked_certificate(app, client):
    num = _seed_cert(app)
    with app.app_context():
        from src.web.app import Certificate
        cert = Certificate.query.filter_by(certificate_number=num).first()
        assert cert is not None
        cert.is_active = False
        _db.session.commit()
    data = client.get(f'/api/verify/{num}').get_json()
    assert data['status'] == 'REVOKED'
    assert data['valid'] is False


def test_expired_certificate(app, client):
    num = _seed_cert(app, expires_in_days=-1)
    data = client.get(f'/api/verify/{num}').get_json()
    assert data['status'] == 'EXPIRED'
    assert data['valid'] is False


def test_verify_page_renders_valid(app, client):
    num = _seed_cert(app)
    resp = client.get(f'/verify/{num}')
    assert resp.status_code == 200
    assert b'Certificate Valid' in resp.data
    assert b'Acme Ltd' in resp.data


def test_verify_home_shows_lookup_form(client):
    """The bare /verify entry point renders a form, not a bogus 'not found'."""
    resp = client.get('/verify')
    assert resp.status_code == 200
    assert b'Verify a Certificate' in resp.data
    assert b'name="q"' in resp.data                 # the lookup input
    assert b'Certificate Not Found' not in resp.data


def test_verify_home_redirects_to_result(client):
    """Submitting a number normalises it and hands off to the result page."""
    resp = client.get('/verify', query_string={'q': '  zdh-2026-aaaa-bbbb-cccc '})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/verify/ZDH-2026-AAAA-BBBB-CCCC')


def test_verify_home_valid_certificate_roundtrip(app, client):
    """Looking up a real certificate through the form reaches a VALID page."""
    num = _seed_cert(app)
    resp = client.get('/verify', query_string={'q': num}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Certificate Valid' in resp.data


def test_pubkey_published(client):
    resp = client.get('/verify/pubkey')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['algorithm'] == 'Ed25519'
    assert data['active_key_id'] == 'test-key-1'
    assert 'BEGIN PUBLIC KEY' in data['keys']['test-key-1']


def test_verify_rate_limited(app, client):
    num = _seed_cert(app)
    # Limit is 20/min for the HTML page; the 21st should be throttled.
    codes = [client.get(f'/verify/{num}').status_code for _ in range(25)]
    assert 429 in codes


def test_certificate_page_renders(app, client):
    num = _seed_cert(app)
    resp = client.get(f'/certificate/{num}')
    assert resp.status_code == 200
    body = resp.data
    assert num.encode() in body
    assert b'CERTIFICATE OF DIGITAL HYGIENE' in body
    assert b'Scan to verify' in body
    assert b'data:image/png;base64,' in body          # embedded QR
    assert b'Offline verification code' in body         # signed block present


def test_certificate_page_not_found(client):
    resp = client.get('/certificate/ZDH-2026-0000-0000-0000')
    assert resp.status_code == 404


def test_certificate_qr_points_at_request_host(app, client):
    num = _seed_cert(app)
    resp = client.get(f'/certificate/{num}')
    # The visible verify link/QR target should use the serving host.
    assert f'/verify/{num}'.encode() in resp.data


# ── desktop issuance API (Phase 3) ──────────────────────────────────────────────

_ISSUE = {
    'business_name': 'Ndola Foods Ltd', 'registration_number': 'PACRA-55010',
    'level': 'SILVER', 'score': 78, 'total_possible': 120, 'assessor': 'desktop',
}


def test_issue_requires_api_key(client):
    resp = client.post('/api/certificates/issue', json=_ISSUE)
    assert resp.status_code == 401


def test_issue_rejects_wrong_key(client):
    resp = client.post('/api/certificates/issue', json=_ISSUE,
                       headers={'X-API-Key': 'nope'})
    assert resp.status_code == 401


def test_issue_rejects_not_certifiable(client):
    body = dict(_ISSUE, level='NOT CERTIFIED')
    resp = client.post('/api/certificates/issue', json=body,
                       headers={'X-API-Key': 'dev-issue-key-change-me'})
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'not_certifiable'


def test_issue_missing_fields(client):
    resp = client.post('/api/certificates/issue', json={'level': 'GOLD'},
                       headers={'X-API-Key': 'dev-issue-key-change-me'})
    assert resp.status_code == 400


def test_issue_and_then_verify_roundtrip(client):
    resp = client.post('/api/certificates/issue', json=_ISSUE,
                       headers={'X-API-Key': 'dev-issue-key-change-me'})
    assert resp.status_code == 201
    data = resp.get_json()
    num = data['certificate_number']
    assert num.startswith('ZDH-')
    assert data['status'] == 'VALID'
    assert data['verification_block']
    assert f'/verify/{num}' in data['verify_url']

    # The freshly issued certificate must verify as VALID with a good signature.
    v = client.get(f'/api/verify/{num}').get_json()
    assert v['status'] == 'VALID'
    assert v['signature_valid'] is True
    assert v['business_name'] == 'Ndola Foods Ltd'


def test_offline_verifier_page(app, client):
    resp = client.get('/verify-offline')
    assert resp.status_code == 200
    body = resp.data
    assert b'Offline Certificate Verifier' in body
    assert b'BEGIN PUBLIC KEY' in body       # authority public key embedded
    assert b'verifyBlock' in body            # verifier JS inlined
    assert b'test-key-1' in body             # active key id embedded


def test_offline_verifier_prefill(client):
    resp = client.get('/verify-offline?block=SOME-PREFILLED-BLOCK')
    assert b'SOME-PREFILLED-BLOCK' in resp.data


def test_issue_works_with_csrf_enabled(app):
    # The M2M endpoint must be CSRF-exempt (desktop clients can't hold a token).
    app.config['WTF_CSRF_ENABLED'] = True
    c = app.test_client()
    resp = c.post('/api/certificates/issue', json=_ISSUE,
                  headers={'X-API-Key': 'dev-issue-key-change-me'})
    assert resp.status_code == 201


def test_issue_respects_env_api_key(client, monkeypatch):
    monkeypatch.setenv('ZDH_ISSUE_API_KEY', 'super-secret-key')
    # dev default no longer works
    assert client.post('/api/certificates/issue', json=_ISSUE,
                       headers={'X-API-Key': 'dev-issue-key-change-me'}).status_code == 401
    # configured key works
    assert client.post('/api/certificates/issue', json=_ISSUE,
                       headers={'X-API-Key': 'super-secret-key'}).status_code == 201


# ── Phase 5: rotation, revocation reasons, re-issue supersede ────────────────────

_KEY = {'X-API-Key': 'dev-issue-key-change-me'}


def test_reissue_supersedes_prior(client):
    body = dict(_ISSUE, level='GOLD', registration_number='PACRA-REISSUE')
    r1 = client.post('/api/certificates/issue', json=body, headers=_KEY).get_json()
    r2 = client.post('/api/certificates/issue', json=body, headers=_KEY).get_json()
    assert r1['certificate_number'] != r2['certificate_number']

    v1 = client.get(f"/api/verify/{r1['certificate_number']}").get_json()
    v2 = client.get(f"/api/verify/{r2['certificate_number']}").get_json()
    assert v1['status'] == 'SUPERSEDED'
    assert v1['valid'] is False
    assert r2['certificate_number'] in (v1.get('revocation_reason') or '')
    assert v2['status'] == 'VALID'


def test_revocation_reason_surfaced(app, client):
    num = _seed_cert(app)
    with app.app_context():
        cert = Certificate.query.filter_by(certificate_number=num).first()
        assert cert is not None
        cert.is_active = False
        data = dict(cert.certificate_data)
        data['revocation'] = {'type': 'revoked', 'reason': 'Business closed',
                              'revoked_by': 'admin'}
        cert.certificate_data = data
        _db.session.commit()

    v = client.get(f'/api/verify/{num}').get_json()
    assert v['status'] == 'REVOKED'
    assert v['revocation_reason'] == 'Business closed'
    page = client.get(f'/verify/{num}')
    assert b'Business closed' in page.data


def test_pubkey_publishes_all_keys(client, monkeypatch):
    kp = signing.generate_keypair()
    monkeypatch.setenv('ZDH_PUBLIC_KEYS', json.dumps({'retired-1': kp['public_pem']}))
    signing.reset_signer_for_tests()
    keys = client.get('/verify/pubkey').get_json()['keys']
    assert 'retired-1' in keys
    assert len(keys) >= 2                       # active + retired
    signing.reset_signer_for_tests()


# ── Security patches ─────────────────────────────────────────────────────────────

def test_issue_fails_closed_without_configured_key(app, monkeypatch):
    """In production (no ZDH_ISSUE_API_KEY, not debug/test), the published dev
    key must be rejected — issuance fails closed rather than open."""
    monkeypatch.delenv('ZDH_ISSUE_API_KEY', raising=False)
    app.config['TESTING'] = False
    app.config['DEBUG'] = False
    c = app.test_client()
    r = c.post('/api/certificates/issue', json=_ISSUE,
               headers={'X-API-Key': 'dev-issue-key-change-me'})
    assert r.status_code == 401


def test_ratelimit_ignores_spoofed_forwarded_for(app, monkeypatch):
    """Without TRUST_PROXY, a rotating X-Forwarded-For must not dodge the cap."""
    monkeypatch.delenv('TRUST_PROXY', raising=False)
    num = _seed_cert(app)
    c = app.test_client()
    codes = [c.get(f'/verify/{num}',
                   headers={'X-Forwarded-For': f'9.9.9.{i}'}).status_code
             for i in range(25)]
    assert 429 in codes                          # shared bucket by socket peer


def test_ratelimit_honours_forwarded_for_when_trusted(app, monkeypatch):
    """With TRUST_PROXY=1, each real client IP gets its own bucket."""
    monkeypatch.setenv('TRUST_PROXY', '1')
    num = _seed_cert(app)
    c = app.test_client()
    codes = [c.get(f'/verify/{num}',
                   headers={'X-Forwarded-For': f'9.9.9.{i}'}).status_code
             for i in range(25)]
    assert 429 not in codes                       # 25 distinct IPs, 1 hit each
