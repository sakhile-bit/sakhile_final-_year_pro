# Feature: Certificate Signing & Verification (Anti-Forgery)

## Overview
Certificates issued by the program are **cryptographically signed** and **centrally registered**, so they cannot be forged and any inspector can verify one — online by scanning a QR code, or offline against a published public key. Every certificate carries an Ed25519 signature over its material facts (business, level, score, dates); altering any printed field breaks the signature and the certificate reads as **tampered**.

The signing key lives only on the server. The distributed Windows `.exe` never holds it — instead the desktop **registers** a completed assessment with the portal, which signs it and returns the authoritative certificate.

**Signing engine:** [`src/security/certs/signing.py`](../../src/security/certs/signing.py)
**Rendering (QR / URLs):** [`src/security/certs/render.py`](../../src/security/certs/render.py)
**Desktop client:** [`src/utils/cert_client.py`](../../src/utils/cert_client.py)
**Web routes:** [`src/web/app.py`](../../src/web/app.py)

---

## Threat Model — what "forged" means

| Attack | Defence |
|---|---|
| Invent a fake certificate number | Not in the registry → **NOT FOUND** |
| Edit score/level/business on a copy of a real certificate | Signature no longer matches → **INVALID (tampering detected)** |
| Enumerate `/verify/ZDH-…` to harvest valid numbers | 48-bit random IDs + per-IP rate limiting |
| Reuse an expired / revoked / replaced certificate | Surfaced as **EXPIRED / REVOKED / SUPERSEDED** |
| Desktop-issued forgery | Desktop cannot sign; only the server-held key can |

---

## How It Works

### 1 — Signing (the anti-forgery core)
On issue, the server builds a canonical JSON payload of the certificate's facts and signs it with the authority's Ed25519 private key:

```json
{ "v":1, "cert":"ZDH-2026-…", "biz":"Acme Ltd", "reg":"PACRA-…",
  "level":"GOLD", "score":104, "total":120,
  "issued":"2026-07-12", "expires":"2027-07-12", "framework":"ZDH-1.0" }
```

The signature, `key_id`, and a compact **verification block** (base64) are stored in the certificate record and embedded in the document. Canonicalisation is deterministic (sorted keys, no whitespace, UTF‑8) so the signer and every verifier agree byte-for-byte.

### 2 — Issuance
- **Web** — a passing assessment auto-issues a signed certificate (`_issue_signed_certificate`).
- **Desktop** — after a certified assessment, the app POSTs to the portal's issuance API (`POST /api/certificates/issue`, authenticated with an API key). It receives the signed certificate and mirrors it locally. If the portal is unreachable, the certificate stays **PROVISIONAL** until it syncs.

### 3 — Online verification (inspector scans QR / types number)
`/verify/<number>` looks up the registry, **re-checks the signature**, and shows a clear status banner plus the officially recorded fields to compare against the paper:

| Status | Meaning |
|---|---|
| **VALID** | Registered, signature valid, not expired/revoked |
| **EXPIRED** | Genuine but past its expiry date |
| **REVOKED** | Revoked by the authority (with reason) |
| **SUPERSEDED** | Replaced by a newer certificate after re-assessment |
| **INVALID** | Signature does not match — altered/forged |
| **NOT FOUND** | Number not in the registry |

### 4 — Offline verification (no connectivity)
`/verify-offline` is a **fully self-contained page** (inline JS + embedded public keys, no external requests). An inspector loads or saves it once, then pastes the certificate's verification block; Ed25519 verification runs entirely in the browser. Documents also carry the block as text and a QR link to this page.

**Verifier script:** [`src/web/static/js/offline_verify.js`](../../src/web/static/js/offline_verify.js) — its canonicalisation matches the Python signer byte-for-byte (cross-validated under Node in the test suite).

### 5 — QR codes & documents
The printable web certificate ([`/certificate/<number>`](../../src/web/templates/certificate.html)) and the desktop PDF/HTML reports ([`src/reporting/generator.py`](../../src/reporting/generator.py)) embed a QR code pointing at the verification page, plus the offline verification block.

---

## Certificate Lifecycle

- **Issued** — signed, registered, `VALID`, with a validity window (12 months Gold/Silver, 6 months Bronze).
- **Re-assessed** — issuing a new certificate for the same business marks the previous one **SUPERSEDED** (soft, points at the replacement). One valid certificate per business.
- **Revoked** — an admin revokes with a **reason** (stored with who/when), surfaced on all verification pages.
- **Expired** — derived from the expiry date at verification time.

Revocation UI: [`src/web/admin/routes.py`](../../src/web/admin/routes.py) → admin certificates page.

---

## Key Management & Rotation

- The **private key** is resolved (first match wins): `ZDH_SIGNING_PRIVATE_KEY` (PEM in env) → `ZDH_SIGNING_KEY_FILE` (path) → `instance/signing_key.pem` (dev, auto-generated once and reused).
- Each signature embeds a `key_id`. To rotate: set a new private key + `key_id`, and keep the **old public key** in `ZDH_PUBLIC_KEYS` so already-issued certificates still verify. `/verify/pubkey` publishes all public keys (active + retired).
- Helper: `python scripts/rotate_signing_key.py` prints the new key config and the `ZDH_PUBLIC_KEYS` entry to retain the old key. See [`scripts/rotate_signing_key.py`](../../scripts/rotate_signing_key.py).

---

## Configuration (environment variables)

| Variable | Where | Purpose |
|---|---|---|
| `ZDH_SIGNING_PRIVATE_KEY` | Portal | Signing private key (PEM). **Production: set this.** |
| `ZDH_SIGNING_KEY_FILE` | Portal | Alternative: path to the private key file |
| `ZDH_SIGNING_KEY_ID` | Portal | Current key id (default `zdh-ed25519-1`) |
| `ZDH_PUBLIC_KEYS` | Portal | JSON `{key_id: pem}` of retired keys (rotation) |
| `ZDH_ISSUE_API_KEY` | Portal + Desktop | Shared key for the desktop issuance API. **Required in production** — see below |
| `VERIFY_BASE_URL` / `PORTAL_API_URL` | Desktop | Portal URL (default `http://localhost:5000`) |
| `TRUST_PROXY` | Portal | Set to `1` only when behind a trusted reverse proxy, so `X-Forwarded-For` is used for rate-limiting |

> **Dev defaults**: without config, the portal generates a stable local signing key and both sides use a shared dev API key (`dev-issue-key-change-me`). Set real values before production.

### Issuance auth fails closed
The dev API key is accepted **only** in debug/test mode. In production (debug off), if `ZDH_ISSUE_API_KEY` is not set, the issuance endpoint **rejects all requests** rather than falling back to the source-published dev key — so a forgotten key can never leave issuance open. Set `ZDH_ISSUE_API_KEY` to a strong secret on both the portal and desktop clients.

### Rate-limit source IP
Rate limiting keys on the socket peer by default. `X-Forwarded-For` is honoured only when `TRUST_PROXY=1`, so a client cannot spoof the header to bypass the per-IP cap. Enable it when the portal genuinely sits behind a proxy (Render/Railway/Nginx).

---

## API Reference

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/certificates/issue` | POST | `X-API-Key` | Register + sign a certificate (desktop → portal) |
| `/verify/<number>` | GET | public | Human verification page |
| `/api/verify/<number>` | GET | public | Machine-readable verification (JSON) |
| `/certificate/<number>` | GET | public | Printable certificate with QR + block |
| `/verify-offline` | GET | public | Self-contained offline verifier page |
| `/verify/pubkey` | GET | public | Published public key(s) (active + retired) |

Public endpoints are per-IP rate limited ([`src/web/ratelimit.py`](../../src/web/ratelimit.py)) and verification attempts are written to the audit log.

---

## Local Development

1. Run the portal (`localhost:5000`); a stable dev signing key is generated on first use.
2. Complete a certified assessment in the desktop app — it auto-registers against the portal (dev API key matches out of the box).
3. Verify at `http://localhost:5000/verify/<number>`, view the printable certificate at `/certificate/<number>`, or test offline at `/verify-offline`.
4. Point QR codes at a real domain later by setting `VERIFY_BASE_URL` (desktop) — the web certificate page already uses its own serving host.

---

## Tests

| File | Covers |
|---|---|
| [`tests/test_cert_signing.py`](../../tests/test_cert_signing.py) | Sign/verify, tamper detection, blocks, rotation, keypair |
| [`tests/test_cert_verify_web.py`](../../tests/test_cert_verify_web.py) | Verify pages/API, issuance API, supersede, revocation reasons |
| [`tests/test_cert_client.py`](../../tests/test_cert_client.py) | Desktop client (offline-safe) + local persistence |
| [`tests/test_cert_render.py`](../../tests/test_cert_render.py) | QR/URL helpers + report verification sections |
| [`tests/test_cert_offline_js.py`](../../tests/test_cert_offline_js.py) | Browser verifier (Node) vs Python signer, incl. non-ASCII |

---

## Related Files

- Signing: [`src/security/certs/signing.py`](../../src/security/certs/signing.py), [`src/security/certs/render.py`](../../src/security/certs/render.py)
- Web: [`src/web/app.py`](../../src/web/app.py), [`src/web/ratelimit.py`](../../src/web/ratelimit.py), templates `verify.html`, `verify_offline.html`, `certificate.html`
- Desktop: [`src/utils/cert_client.py`](../../src/utils/cert_client.py), [`src/utils/local_db.py`](../../src/utils/local_db.py), [`src/gui/screens/results.py`](../../src/gui/screens/results.py)
- Ops: [`scripts/rotate_signing_key.py`](../../scripts/rotate_signing_key.py)
