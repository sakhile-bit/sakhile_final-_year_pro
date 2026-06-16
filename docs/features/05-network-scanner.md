# Feature: Network Scanner

## Overview
The Network Scanner discovers every device on the local network using ARP cache inspection and ping sweeping, port-scans each discovered host against 16 well-known ports, risk-rates every finding, and draws an **interactive topology map** on a canvas. Users can click any node to see full port details.

**File:** [`src/gui/screens/network_scanner.py`](../../src/gui/screens/network_scanner.py)

---

## Discovery Phase

Two methods run concurrently in a thread pool:

### 1. ARP Cache
```
arp -a  (Windows)
```
Parses the ARP table to extract all IP ↔ MAC address pairs on the local subnet. This is instantaneous and covers all recently-communicated hosts.

### 2. Ping Sweep
Sends ICMP pings to every host in the local `/24` subnet (e.g. `192.168.1.1` – `192.168.1.254`). Hosts that respond are added to the device list. Uses `subprocess` with a short timeout (1 second per host) and a `ThreadPoolExecutor` to run up to 64 probes simultaneously.

```python
SCAN_PORTS = [21, 22, 23, 25, 53, 80, 135, 139,
              443, 445, 1433, 3306, 3389, 5432, 8080, 8443]
```

---

## Port Scanning

Each discovered host is scanned against 16 ports. For each open port the scanner looks up:

| Port | Service | Risk | Notes |
|---|---|---|---|
| 21 | FTP | HIGH | Unencrypted file transfer |
| 22 | SSH | INFO | Secure remote access |
| 23 | Telnet | CRITICAL | Unencrypted — disable now |
| 25 | SMTP | MEDIUM | Open relay risk |
| 53 | DNS | INFO | Resolver |
| 80 | HTTP | LOW | Redirect to HTTPS |
| 135 | MS-RPC | HIGH | Restrict to internal |
| 139 | NetBIOS | HIGH | Legacy Windows sharing |
| 443 | HTTPS | INFO | Secure web |
| 445 | SMB | CRITICAL | Prime ransomware vector |
| 1433 | MS-SQL | HIGH | Restrict DB access |
| 3306 | MySQL | HIGH | Restrict DB access |
| 3389 | RDP | CRITICAL | Critical ransomware risk |
| 5432 | PostgreSQL | HIGH | Restrict DB access |
| 8080 | HTTP-alt | LOW | Alternative web |
| 8443 | HTTPS-alt | INFO | Alternative HTTPS |

---

## Topology Map

A `tk.Canvas` draws an interactive network diagram:

- **Router node** at the centre (IP gateway)
- **Host nodes** arranged in a circle around it, connected by lines
- **Node colour** reflects highest risk found:

| Risk Level | Colour |
|---|---|
| CRITICAL | `#E84040` Red |
| HIGH | `#E87000` Orange |
| MEDIUM | `#F0A500` Amber |
| LOW | `#78C840` Green |
| SAFE (no risky ports) | `#6C5FC7` Purple |
| SCANNING | `#5A7490` Grey |

Clicking a node opens a **detail panel** listing every open port, its service name, risk level and advice.

---

## Device Data Model

```python
@dataclass
class Device:
    ip:        str
    mac:       str = ''
    hostname:  str = ''
    open_ports: list[int] = field(default_factory=list)
    risk:      str = 'UNKNOWN'     # CRITICAL / HIGH / MEDIUM / LOW / SAFE
    vendor:    str = ''
    last_seen: datetime = None
```

---

## Risk Assessment Logic

The overall risk level assigned to a device is the **highest severity** port found:

```python
RISK_ORDER = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO', 'SAFE']
device.risk = max(open_port_risks, key=lambda r: RISK_ORDER.index(r))
```

---

## Export
Results can be exported to a **JSON file** (`filedialog.asksaveasfilename`) containing all discovered devices, their MAC addresses, hostnames, open ports and risk levels.

---

## Execution Flow

```
User clicks "Start Scan"
        ↓
Background thread
        ├─ arp -a (instant)         ─┐
        ├─ ping sweep /24            ├─ Device list assembled
        └─ hostname lookups (async) ─┘
        ↓
For each device (ThreadPoolExecutor):
    ├─ TCP connect to each of 16 ports (0.3s timeout)
    └─ self.after(0, _update_node_colour)
        ↓
Canvas redraws as results arrive
        ↓
Scan complete → summary stats update
```

---

## Thread Safety
All canvas and widget updates use `self.after(0, callback)` to post updates to the tkinter main loop from the background scanning thread.

---

## Related Features
- [Infrastructure Scanner](06-infra-scanner.md) — scans external hosts
- [Deployment Checker](07-deployment-checker.md) — checks open ports on localhost
