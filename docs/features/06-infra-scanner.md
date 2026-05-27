# Feature: Infrastructure Scanner

## Overview
The Infrastructure Scanner lets users enter any **domain name or IP address** and performs a security audit of its internet-facing services: SSL/TLS certificate validity, open ports, HTTP security headers and DNS configuration. Designed for assessing web servers, SaaS providers and cloud endpoints.

**GUI file:** [`src/gui/screens/infra_scanner.py`](../../src/gui/screens/infra_scanner.py)  
**Engine file:** [`src/security/infra_scanner.py`](../../src/security/infra_scanner.py)  
**Assessor integration:** [`src/security/assessment/assessor.py`](../../src/security/assessment/assessor.py) — `InfrastructureAssessor` class

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

### 4. Open Ports
TCP connect scan against a configurable port list (default: 80, 443, 22, 3389, 3306, 5432). Returns which ports are open and attempts to grab a service banner.

### 5. External IP
Queries `https://api.ipify.org` (if `requests` is available) to show the public IP of the scanned host alongside its resolved DNS IP.

### 6. Security Headers *(InfrastructureAssessor)*
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

1. User types a domain or IP in the input field
2. Clicks **Scan →**
3. A spinner / progress indicator appears
4. Results render incrementally as each check completes:
   - DNS ✔ / ✖ with resolved IP
   - TLS ✔ / ✖ with expiry date and cipher
   - HTTP redirect ✔ / ✖
   - Open ports table
   - Security headers table (coloured PASS / FAIL per header)
5. An overall **risk rating** is computed from all findings

All network calls run in a `threading.Thread` to keep the GUI responsive.

---

## InfrastructureAssessor (assessor.py integration)

The `InfrastructureAssessor` class in `assessor.py` wraps the engine and is used by the web app:

```python
class InfrastructureAssessor:
    def __init__(self, target: str):
        self.target = target

    def run_checks(self) -> dict:
        return {
            'dns_resolution':  self._check_dns_resolution(),
            'ssl_certificate': self._check_ssl_certificate(),
            'https_redirect':  self._check_https_redirect(),
            'external_ip':     self._get_external_ip(),
            'open_ports':      self._scan_common_ports(),
        }
```

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
