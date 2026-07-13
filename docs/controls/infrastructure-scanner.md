# Infrastructure Scanner — Public-Facing Findings

**Source:** `src/security/assessment/assessor.py` (`InfrastructureAssessor`,
`_build_findings`)
**Layer:** Infrastructure (a public-facing domain / host, scanned remotely)
**Grade:** `SECURE` (score ≥ 85) → `NEEDS ATTENTION` (score ≥ 55) → `AT RISK`.
Any **CRITICAL** finding forces `AT RISK` — stricter than the hardening audit
because these are internet-exposed.

**Scoring:** start at 100 and subtract per finding —
CRITICAL −30, HIGH −18, MEDIUM −9, LOW −4 (clamped to 0–100).

Unlike the other families these are *findings* (only raised when a problem is
detected) rather than always-run pass/fail checks. Each has a stable finding
ID, a category, a severity, and remediation guidance.

| Finding ID | Category | Severity | Raised when |
|------------|----------|----------|-------------|
| `TLS-CERT` | tls | CRITICAL / HIGH / MEDIUM | Certificate expired (CRITICAL), missing/untrusted (HIGH), or expiring soon (MEDIUM). |
| `TLS-SELF` | tls | HIGH | Certificate is self-signed (issuer matches subject). |
| `TLS-HOST` | tls | HIGH | Certificate does not match the hostname (SAN mismatch). |
| `TLS-PROTO` | tls | HIGH | Server accepts deprecated TLS 1.0 / 1.1. |
| `HTTP-REDIR` | tls | MEDIUM | Plain HTTP does not redirect to HTTPS. |
| `HDR-<name>` | headers | MEDIUM / LOW | A security header is missing. HSTS & CSP → MEDIUM; X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy → LOW. |
| `HTTP-TRACE` | headers | MEDIUM | HTTP TRACE method enabled (Cross-Site Tracing / XST). |
| `HTTP-BANNER` | headers | LOW | Server / X-Powered-By headers disclose software versions. |
| `HTTP-COOKIE` | headers | MEDIUM | Cookies set without `Secure` / `HttpOnly` flags. |
| `HTTP-HSTS-AGE` | tls | LOW | HSTS `max-age` under 180 days (15 552 000 s). |
| `DNS-SPF` | email | MEDIUM | No SPF record (domain can be spoofed in email). |
| `DNS-DMARC` | email | MEDIUM | No DMARC record (no anti-phishing enforcement). |
| `DNS-CAA` | dns | LOW | No CAA record naming authorised certificate authorities. |
| `PORT` | ports | CRITICAL / HIGH / MEDIUM | A risky port is exposed; severity carried from the port's risk rating. |

## What else the scan collects

Beyond findings, a scan run (`run_checks()`) returns the raw evidence the
findings are built from, retained for the web app and templates:

- DNS resolution, DNS security (SPF/DMARC/CAA), certificate inspection
  (issuer, self-signed, hostname match, days left), TLS version, HTTPS
  redirect, security headers, HTTP methods, HTTP meta (banner, cookies, HSTS).
- `target_ip` / `scanner_ip` / `reverse_dns`, open ports with service names
  (`PORT_SERVICES`), and risky-port list.
- Aggregate `score` and `grade`.

> A separate lightweight helper lives in `src/security/infra_scanner.py`; the
> graded engine documented here is `assessment/assessor.py`.

---
**Feature docs:** [06 Infrastructure Scanner](../features/06-infra-scanner.md) · [controls catalogue](README.md)
