# Feature: Infrastructure Scanner

## Overview
The Infrastructure Scanner lets users enter any **domain name or IP address** and audits its internet-facing services: SSL/TLS certificate validity & trust, deprecated TLS versions, HTTP→HTTPS redirect, HTTP security headers, email/DNS security (SPF, DMARC, CAA), reverse DNS, and open-port exposure with service identification. It rolls everything into **prioritised findings** and a single **SECURE / NEEDS ATTENTION / AT RISK** grade so a non-technical owner gets a clear verdict and a fix list, and the report can be exported to HTML.

**GUI file:** [`src/gui/screens/infra_scanner.py`](../../src/gui/screens/infra_scanner.py)
**Engine:** [`src/security/assessment/assessor.py`](../../src/security/assessment/assessor.py) — `InfrastructureAssessor` (drives the GUI). The small [`src/security/infra_scanner.py`](../../src/security/infra_scanner.py) provides standalone `scan_host_services()` port/TLS helpers.

---

## Grade & Findings

Each run produces a list of `InfraFinding` objects (id, category, severity, status, title, detail, remediation). Severity drives a score deducted from 100:

```
CRITICAL −30 · HIGH −18 · MEDIUM −9 · LOW −4 · INFO 0   (clamped 0–100)

AT RISK          when any CRITICAL finding exists, OR score < 55
SECURE           when score ≥ 85 and no CRITICAL
NEEDS ATTENTION  otherwise
```

Any single critical public-facing exposure (public database/RDP, unauthenticated Redis/Elasticsearch/MongoDB, expired certificate, Telnet/SMB open) is an immediate **AT RISK** verdict — for internet-facing services one critical is enough.

---

## What It Checks

### 1. DNS Resolution
```python
socket.getaddrinfo(host, 443, socket.AF_INET)
```
Verifies that the domain resolves to an IP address. Returns the resolved IP.

### 2. SSL/TLS Certificate
```python
ssl.create_default_context().wrap_socket(sock, server_hostname=host)
cert = ssock.getpeercert()
```
Checks:
- Certificate is valid (no expired, no self-signed errors)
- Expiry date (`notAfter` field)
- Subject Common Name / SAN
- Cipher suite in use

### 3. HTTPS Redirect
Issues an HTTP request to port 80 and checks whether the server responds with a `301` or `302` redirect to `https://`.

### 4. Open Ports (parallel, with service identification)
A **concurrent** TCP-connect scan (ThreadPoolExecutor) over ~30 common ports — the whole sweep runs in parallel and is cached for the run rather than scanned serially twice. Each open port is labelled with its service (`80 → HTTP`, `3306 → MySQL`, …). Ports dangerous to expose publicly are flagged with a severity: databases (MySQL/PostgreSQL/MSSQL/Oracle), unauthenticated data stores (Redis/Elasticsearch/MongoDB/Memcached), remote access (RDP/VNC/Telnet), and legacy Windows services (SMB/NetBIOS/MSRPC) → CRITICAL or HIGH.

### 5. Target & scanner IPs, reverse DNS
- `target_ip` — the **target's** resolved public IP (used by the web app's Shodan exposure lookup). *(Previously mislabelled: the old `_get_external_ip` returned the scanner's own LAN IP.)*
- `scanner_ip` — this scanner's egress IP, for context.
- `reverse_dns` — the PTR record for the target IP.

### 6. Deep certificate inspection
Beyond validity/expiry, `_inspect_certificate()` reports the **issuer organisation**, whether the cert is **self-signed** (issuer == subject) and whether it **fails hostname validation** — each surfaced as a HIGH finding.

### 7. Email / DNS security (SPF, DMARC, CAA)
TXT/CAA lookups via `nslookup` (Windows) / `dig` (Linux). Missing SPF or DMARC → MEDIUM (spoofing/phishing risk); missing CAA → LOW.

### 8. Security Headers *(InfrastructureAssessor)*
Sends an HTTP GET and inspects response headers:

| Header | Purpose |
|---|---|
| `Strict-Transport-Security` | Enforces HTTPS |
| `Content-Security-Policy` | Prevents XSS |
| `X-Frame-Options` | Prevents clickjacking |
| `X-Content-Type-Options` | Prevents MIME sniffing |
| `Referrer-Policy` | Controls referrer info |

---

## Data Classes

```python
@dataclass
class PortCheck:
    port:   int
    open:   bool
    banner: str | None = None

@dataclass
class TLSCheck:
    port:    int
    valid:   bool
    expires: str | None = None
    subject: str | None = None
    cipher:  str | None = None
```

---

## Engine API

```python
from src.security.infra_scanner import scan_host_services

result = scan_host_services('example.com', ports=[80, 443, 22])
# Returns:
# {
#   'host': 'example.com',
#   'ports': [{'port': 80, 'open': True, 'banner': 'nginx/1.18'},
#             {'port': 443, 'open': True, 'banner': None},
#             {'port': 22,  'open': False, 'banner': None}],
#   'tls': {'port': 443, 'valid': True, 'expires': 'Dec 31 00:00:00 2026 GMT',
#           'subject': 'example.com', 'cipher': 'ECDHE-RSA-AES256-GCM-SHA384'}
# }
```

---

## GUI Behaviour

1. User types a domain or IP and clicks **Scan** (or presses Enter)
2. The scan runs in a `threading.Thread` so the UI stays responsive
3. Results reveal as a gentle top-down **cascade** (`motion.stagger_grid`):
   - **Grade hero** — SECURE / NEEDS ATTENTION / AT RISK with a score %
   - **Findings** — cards sorted worst-first, each with a severity badge and a
     plain-language "Fix:" remediation
   - **DNS** — resolution, target IP, reverse DNS, SPF / DMARC / CAA
   - **SSL/TLS** — certificate, issuer, TLS version, HTTPS redirect
   - **HTTP security headers** — coloured PRESENT / MISSING
   - **Port exposure** — open ports with service names, risky ports highlighted
4. **📄 Export Report** writes a standalone dark-theme HTML report (verdict
   hero + findings table + scan details) and opens it.

The whole app scrolls with eased momentum (`motion.enable_global_smooth_scroll`
monkeypatches `CTkScrollableFrame` once at startup), and the scan progress and
screen transitions animate — see [UI Motion](21-ui-motion.md).

---

## InfrastructureAssessor (assessor.py integration)

`InfrastructureAssessor(target).run_checks()` returns a dict that **preserves the original keys** (`dns_resolution`, `dns_security`, `ssl_certificate`, `tls_version`, `https_redirect`, `security_headers`, `external_ip`, `open_ports`, `risky_ports`) for backward compatibility with the web app and templates, and adds:

| Key | Meaning |
|---|---|
| `grade` / `score` | Overall verdict and 0–100 score |
| `findings` | List of prioritised `InfraFinding` dicts (severity, title, detail, remediation) |
| `target_ip` / `scanner_ip` | Target's public IP / this scanner's egress IP |
| `reverse_dns` | PTR record of the target |
| `certificate` | Deep cert inspection (issuer, self_signed, hostname_mismatch, days_left) |
| `services` | `{port: service_name}` for each open port |
| `dns_security.caa` | CAA record status (alongside existing `spf`/`dmarc`) |

`risky_ports` entries now carry a trailing `[SEVERITY]` tag (e.g. `"Port 3389: RDP – … [CRITICAL]"`) so the GUI/report can colour them without re-deriving severity.

---

## CLI Usage

```bash
python -m src.utils.agent_cli scan example.com --ports 80,443,22,3389
```

Output is a JSON object with `host`, `ports` and `tls` keys.

---

## Related Features
- [Network Scanner](05-network-scanner.md) — scans local network devices
- [Deployment Checker](07-deployment-checker.md) — PDC-06 DNS and PDC-07 TLS checks
- [Windows Agent](09-windows-agent.md) — can include infra scan in reports

## Controls Reference
- [infrastructure-scanner.md](../controls/infrastructure-scanner.md) — every finding this scanner raises (TLS-*, HTTP-*, HDR-*, DNS-* and PORT) with severities and scoring.
- [tool-specific-controls.md](../controls/tool-specific-controls.md) — the paired C18 governance controls.
