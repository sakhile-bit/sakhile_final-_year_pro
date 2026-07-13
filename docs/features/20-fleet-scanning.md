# Feature: Distributed Fleet Scanning (Master / Node)

## Overview
A single business rarely runs on one machine — it has a file server, a POS back office, a domain controller, workstations. **The business is only as safe as its least hygienic machine.** Fleet Scanning lets one **master node** trigger a full digital-hygiene + hardening scan on every connected **node** across the network, concurrently, and rolls the results up into a single fleet grade governed by the weakest reachable machine.

**Node agent:** [`src/agents/node_agent.py`](../../src/agents/node_agent.py)
**Master coordinator:** [`src/agents/master_coordinator.py`](../../src/agents/master_coordinator.py)
**GUI:** [`src/gui/screens/fleet_scan.py`](../../src/gui/screens/fleet_scan.py) (welcome tile "🖧 Fleet Scan")
**CLI:** `python cli.py node-agent …` (on each node) and `python cli.py fleet-scan --nodes nodes.yaml` (on the master)

---

## Architecture

```
                    ┌──────────────────────────┐
                    │       MASTER NODE        │
                    │  (desktop app or CLI)    │
                    │  master_coordinator.py   │
                    └───────────┬──────────────┘
              concurrent HTTP POST /scan (Bearer token)
        ┌───────────────┬───────┴───────┬───────────────┐
        ▼               ▼               ▼               ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
   │ node    │    │ node    │    │ node    │    │ node    │
   │ agent   │    │ agent   │    │ agent   │    │ agent   │
   │ :8765   │    │ :8765   │    │ :8765   │    │ :8765   │
   └─────────┘    └─────────┘    └─────────┘    └─────────┘
   file-server    pos-backoffice   domain-ctl     workstation
```

Each node runs the **same scan engine** already used locally (`windows_agent.collect_local_report` → assessment + hardening + readiness). The master aggregates the returned JSON — it never runs anything *on* the node beyond that one fixed scan.

---

## Security Model

This is a security tool, so the remote surface is deliberately minimal and locked down:

| Control | Detail |
|---|---|
| **Bearer-token auth** | `POST /scan` requires `Authorization: Bearer <token>`; compared with `hmac.compare_digest` (no timing leak). Missing/wrong token → `401`. |
| **No remote command execution** | `/scan` runs exactly one fixed operation. The caller cannot supply commands, paths, or arguments — it cannot be used as an RCE backdoor. |
| **Unauthenticated `/health` only** | Returns hostname + agent version for liveness/discovery; nothing sensitive. |
| **Node is read-only to the master** | The master collects results; it cannot change node configuration. |
| **Per-node token override** | The inventory can give each node its own secret instead of a shared one. |

Run the agent bound to a trusted interface, and prefer a VPN/LAN rather than exposing `8765` to the internet.

---

## Fleet Grade Logic

```
NO DATA      when  no node could be scanned
INCOMPLETE   when  any node was unreachable  (an unknown node is an unmanaged risk)
<grade>      otherwise = the hardening grade of the WEAKEST reachable node
                        (AT RISK ‹ NEEDS ATTENTION ‹ HARDENED)
```

The weakest node is chosen by (worst hardening grade → lowest score → most critical failures). CLI exit code: `0` only when the whole fleet is `HARDENED`.

---

## Node Inventory (YAML or JSON)

```yaml
token: shared-secret-default        # default token for nodes that omit their own
nodes:
  - name: file-server
    url: http://192.168.1.10:8765
  - name: domain-controller
    url: http://192.168.1.12:8765
    token: a-different-secret       # optional per-node override
  - 192.168.1.20:8765               # shorthand; uses the default token + default port
```

See [`nodes.example.yaml`](../../nodes.example.yaml).

---

## Usage

**On each infrastructure node:**
```bash
set NODE_AGENT_TOKEN=your-strong-secret
python cli.py node-agent --host 0.0.0.0 --port 8765
```

**On the master node:**
```bash
python cli.py fleet-scan --nodes nodes.yaml            # formatted table + verdict
python cli.py fleet-scan --nodes nodes.yaml --json-out # machine-readable
python cli.py fleet-scan --nodes nodes.yaml -o fleet.json
```

Or use the desktop app: **🖧 Fleet Scan** tile. No inventory file needed —
enter the shared token, then click **🔍 Discover** to auto-detect every node
agent on your local /24 network (each host is probed on the agent port's
`/health` endpoint). Detected nodes appear as a checklist; **select multiple**
(or "Select all"), optionally **add a host manually** by IP, then click
**▶ Scan Selected**. Results show a fleet grade hero, a summary strip, and
per-node cards (the weakest link is highlighted). Fleet reports are saved to
local history and can be exported as HTML.

### Auto-discovery API

```python
from src.agents.master_coordinator import discover_nodes, probe_node

discover_nodes(port=8765, timeout=0.7)   # scan local /24 → list of node dicts
probe_node("192.168.1.10", 8765)         # probe one host's /health
```

`discover_nodes` derives the master's own /24 from its IP (or takes an explicit
`cidr24=`), probes all 254 hosts concurrently, and returns those whose
`/health` identifies a node agent (`{host, port, url, hostname, agent_version}`).
Discovery uses only the unauthenticated `/health` endpoint; the token is still
required for the actual scan.

---

## Data Structures

```python
@dataclass
class NodeResult:
    name: str; url: str; status: str          # online/offline/unauthorized/error
    hostname, cert_level, hardening_grade: str | None
    hardening_score: int | None
    readiness_verdict: str | None
    critical_failures: int
    report: dict | None                        # full node report (optional)

@dataclass
class FleetReport:
    results: list[NodeResult]
    # computed: total_nodes, online, unreachable, nodes_at_risk,
    #           total_critical_failures, average_hardening_score,
    #           weakest_node, fleet_grade — plus to_dict()
```

Persisted via `save_fleet_report` / `load_fleet_report` / `list_fleet_reports` in
[`src/utils/local_db.py`](../../src/utils/local_db.py) (`fleet_reports` table).

---

## Tests

[`tests/test_fleet.py`](../../tests/test_fleet.py) — 25 tests: node-agent auth (health open,
scan requires valid token), inventory parsing (defaults, overrides, shorthand, errors),
`scan_node` result parsing for online/unauthorized/offline/error with mocked HTTP,
`FleetReport` weakest-link + INCOMPLETE/NO DATA logic, concurrent `scan_fleet` ordering
and progress callback, and DB round-trip.

---

## Controls Reference
- [tool-specific-controls.md](../controls/tool-specific-controls.md) — the C21 governance controls (fleet asset inventory, scan cadence, weakest-node remediation) that pair with fleet scanning.
