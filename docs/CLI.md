# CLI Reference — `zamsec`

The command-line interface for the Zambia Digital Hygiene Assessment Tool.
One command, everything the tool does: assessments, system scans, hardening
audits with auto-fix, distributed fleet scanning, the web dashboard, user
and session management.

**Version:** 1.1.0 · **Command:** `zamsec` (alias: `zambia-hygiene`)

---

## Table of Contents

1. [Installation](#1-installation)
2. [Global Options](#2-global-options)
3. [Command Index](#3-command-index)
4. [Assessment Commands](#4-assessment-commands)
   — [`assess`](#assess) · [`scan`](#scan) · [`zambia`](#zambia) · [`manual`](#manual)
5. [Hardening & Deployment](#5-hardening--deployment)
   — [`harden`](#harden) · [`predeploy`](#predeploy)
6. [Agents & Fleet Scanning](#6-agents--fleet-scanning)
   — [`agent`](#agent) · [`agent-reports`](#agent-reports) · [`node-agent`](#node-agent) · [`fleet-scan`](#fleet-scan)
7. [Web Portal & Users](#7-web-portal--users)
   — [`web`](#web) · [`init-db`](#init-db) · [`users`](#users)
8. [Session Management](#8-session-management) — [`session`](#session)
9. [Utility Commands](#9-utility-commands)
   — [`status`](#status) · [`completion`](#completion) · [`upgrade`](#upgrade)
10. [Exit Codes & CI/CD Usage](#10-exit-codes--cicd-usage)
11. [Environment Variables](#11-environment-variables)

---

## 1. Installation

Install straight from your terminal (PowerShell, CMD, or bash) — see
[INSTALL_SCRIPTS.md](INSTALL_SCRIPTS.md) for full details and one-line
installer scripts:

```bash
pip install "https://github.com/sakhile-bit/sakhile_final-_year_pro/archive/refs/heads/main.zip"
zamsec --version
```

From a source checkout, `python cli.py <command>` behaves identically to
`zamsec <command>`.

> **Note:** the host-inspection commands (`scan`, `harden`, `agent`) read
> Windows-specific state (Defender, BitLocker, registry) and give the most
> complete results on Windows 10/11. `harden --fix*` requires an
> **Administrator** terminal.

---

## 2. Global Options

These come **before** the command name: `zamsec [GLOBAL OPTIONS] COMMAND [ARGS]`.

| Option | Description |
|---|---|
| `--version` | Print version, Python version, and OS, then exit |
| `--config PATH` | Load a YAML configuration file |
| `-v`, `--verbose` | Enable DEBUG-level log output |
| `--no-color` | Disable colored output (also honours the `NO_COLOR` env var) |
| `-h`, `--help` | Show help (works after any command too: `zamsec harden -h`) |

---

## 3. Command Index

| Command | What it does |
|---|---|
| [`assess`](#assess) | Full automated 15-control digital-hygiene assessment |
| [`scan`](#scan) | Quick system security scan (12 checks) |
| [`zambia`](#zambia) | Interactive Zambia-specific risk assessment |
| [`manual`](#manual) | Generate the on-site (manual) assessment guide |
| [`harden`](#harden) | Windows hardening audit (14 HRD checks) with auto-fix/undo |
| [`predeploy`](#predeploy) | Pre-deployment hygiene gate for CI/CD |
| [`agent`](#agent) | Scan THIS host (assessment + hardening + readiness) |
| [`agent-reports`](#agent-reports) | List/show saved agent reports |
| [`node-agent`](#node-agent) | Run this machine as a scannable fleet node |
| [`fleet-scan`](#fleet-scan) | Scan every node from the master and roll up a fleet grade |
| [`web`](#web) | Start the Flask web dashboard |
| [`init-db`](#init-db) | Create database tables + default admin user |
| [`users`](#users) | Manage web-portal users (`list`, `create`, `reset-password`) |
| [`session`](#session) | CLI sign-in session (`start`, `status`, `end`/`terminate`) |
| [`status`](#status) | Project & environment status summary |
| [`completion`](#completion) | Shell tab-completion setup (bash/zsh/fish/PowerShell) |
| [`upgrade`](#upgrade) | Self-update from GitHub |

---

## 4. Assessment Commands

### `assess`

Run the full automated cybersecurity assessment (15 controls, 120 points)
and generate reports.

```bash
zamsec assess --business-name "Acme Ltd" --business-id REG-001
zamsec assess --business-name "Acme Ltd" --business-id REG-001 -f json -f pdf -o reports --save-db
```

| Option | Default | Description |
|---|---|---|
| `--business-name TEXT` | *(prompted)* | Name of the business |
| `--business-id TEXT` | *(prompted)* | Business registration ID |
| `-o`, `--output-dir PATH` | `reports` | Output directory for reports |
| `-f`, `--format [json\|csv\|html\|pdf]` | `json` | Report format — repeat the flag for several |
| `--save-db` | off | Also save the assessment to the web-portal database |

Prints a per-control results table, overall score, certification level
(GOLD / SILVER / BRONZE / NOT_CERTIFIED), and recommendations.
PDF output requires the `pdf` extra (`pip install "zambia-digital-hygiene[pdf] @ …"`).

### `scan`

Quick system security scan — OS info, open ports, firewall, antivirus, disk
encryption, outdated packages, suspicious processes, SSL/TLS, backups, patch
status, and external IP.

```bash
zamsec scan
zamsec scan --domain example.com --backup-path D:\Backups
zamsec scan --json-out > scan.json
```

| Option | Default | Description |
|---|---|---|
| `-d`, `--domain TEXT` | `localhost` | Domain for the SSL/TLS check |
| `-b`, `--backup-path TEXT` | `/backups` | Folder to check for backup files |
| `-j`, `--json-out` | off | Raw JSON instead of the formatted table |

### `zambia`

Interactive Zambia-specific risk assessment. Asks yes/no questions about
local threat mitigations (SIM-swap fraud, mobile money, WhatsApp fraud, …)
and compliance with Zambian cyber laws, then prints a score and risk level.

```bash
zamsec zambia
zamsec zambia --json-out
```

| Option | Description |
|---|---|
| `-j`, `--json-out` | Raw JSON instead of the formatted summary |

### `manual`

Generate the printable on-site (manual) assessment guide for the 10
interview-based controls.

```bash
zamsec manual
```

---

## 5. Hardening & Deployment

### `harden`

Audit this Windows host against server hardening baselines — 14
infrastructure-grade checks (HRD-01 … HRD-14): SMBv1, SMB signing, RDP/NLA,
UAC, LLMNR/NetBIOS, PowerShell logging, legacy TLS, unquoted service paths,
Print Spooler, Remote Registry, audit policy, local accounts, LSA
protections, and anonymous enumeration.

```bash
zamsec harden                          # audit only
zamsec harden --list-fixes             # what can be fixed automatically
zamsec harden --fix-all-safe           # apply every safe fix (Administrator)
zamsec harden --fix HRD-05 --fix HRD-09
zamsec harden --undo-last              # roll back the last set of fixes
zamsec harden --json-out -o hardening.json
```

| Option | Description |
|---|---|
| `-j`, `--json-out` | Raw JSON instead of the formatted table |
| `-o`, `--output PATH` | Also write the JSON report to a file |
| `--fix HRD-XX` | Auto-fix a specific finding (repeatable) |
| `--fix-all-safe` | Apply every *safe*-tier auto-fix for current findings |
| `--include-caution` | With `--fix-all-safe`, also apply *caution*-tier fixes |
| `--undo-last` | Revert the most recent set of applied fixes |
| `--list-fixes` | List all available automatic fixes and exit |

Notes:

- Applying or undoing fixes requires an **Administrator** terminal.
- Every change is journaled; `--undo-last` restores the previous values.
- HRD-08 (unquoted service paths) and HRD-12 (local accounts) need manual
  judgement and have no automatic fix.
- After fixing, the host is re-audited so the exit code reflects the new state.

**Exit code:** `0` = HARDENED · `1` = NEEDS ATTENTION / AT RISK.

### `predeploy`

Pre-deployment digital hygiene gate. Scans the machine you are deploying
*from*: OS patches, firewall, antivirus, open ports, dependency
vulnerabilities, debug flags, and credential hygiene.

```bash
zamsec predeploy
zamsec predeploy --project-root ./myapp --json-out
```

| Option | Default | Description |
|---|---|---|
| `-p`, `--project-root PATH` | `.` | Project directory to scan |
| `-j`, `--json-out` | off | Raw JSON instead of the formatted table |

**Exit code:** `0` = READY · `1` = NOT READY.

---

## 6. Agents & Fleet Scanning

See [features/20-fleet-scanning.md](features/20-fleet-scanning.md) for the
full architecture.

### `agent`

Run the local host agent once — collects the same full report a fleet node
returns to a master (digital-hygiene assessment + hardening audit +
deployment readiness) and saves it to local history by default.

```bash
zamsec agent
zamsec agent --name "branch-office-pc" --json-out -o host.json
zamsec agent --no-save
```

| Option | Default | Description |
|---|---|---|
| `--name TEXT` | `local-host` | Business/host label recorded in the report |
| `-j`, `--json-out` | off | Print the full report as JSON |
| `-o`, `--output PATH` | — | Write the full report JSON to a file |
| `--save / --no-save` | `--save` | Save to local history |

### `agent-reports`

List agent reports saved in local history, or print one in full.

```bash
zamsec agent-reports
zamsec agent-reports --limit 50
zamsec agent-reports --show 3
```

| Option | Default | Description |
|---|---|---|
| `--limit INT` | `20` | Max reports to list |
| `--show ID` | — | Print the full JSON of one report |

### `node-agent`

Run this machine as a **scannable node**: starts a small authenticated HTTP
server so a central master can trigger scans over the network. Install and
run this on every machine you want covered by fleet scans.

```bash
zamsec node-agent --token <shared-secret>
zamsec node-agent --host 0.0.0.0 --port 8765 --token <secret> --name "till-pc-1"
set NODE_AGENT_TOKEN=<secret> && zamsec node-agent     # token via env var
```

| Option | Default | Description |
|---|---|---|
| `--host TEXT` | `0.0.0.0` | Interface to bind |
| `--port INT` | `8765` | Port to listen on |
| `--token TEXT` | `$NODE_AGENT_TOKEN` | Shared secret the master must present (**required**) |
| `--name TEXT` | — | Optional node/business label |

### `fleet-scan`

From the master machine, scan every node in an inventory file concurrently
and roll the results up into a fleet grade governed by the **weakest
reachable node**. Unreachable nodes are flagged as unmanaged risk.

```bash
zamsec fleet-scan --nodes nodes.yaml
zamsec fleet-scan --nodes nodes.yaml --timeout 120 --workers 5
zamsec fleet-scan --nodes nodes.yaml --json-out -o fleet.json
```

| Option | Default | Description |
|---|---|---|
| `-n`, `--nodes PATH` | *(required)* | YAML/JSON node inventory (see `nodes.example.yaml`) |
| `--timeout FLOAT` | `60` | Per-node scan timeout in seconds |
| `--workers INT` | `10` | Max concurrent node scans |
| `-j`, `--json-out` | off | Raw JSON instead of the formatted table |
| `-o`, `--output PATH` | — | Write the full fleet report (incl. per-node reports) to a file |
| `--save / --no-save` | `--save` | Save the fleet report to local history |

**Exit code:** `0` = fleet HARDENED · `1` = anything worse.

---

## 7. Web Portal & Users

### `web`

Start the Flask web dashboard (development server).

```bash
zamsec web                       # http://127.0.0.1:5000
zamsec web --host 0.0.0.0 --port 8080 --debug
```

| Option | Default | Description |
|---|---|---|
| `--host TEXT` | `127.0.0.1` | Server host |
| `--port INT` | `5000` | Server port |
| `--debug` | off | Flask debug mode |

For production use gunicorn (`server` extra) — see [DEPLOYMENT.md](DEPLOYMENT.md).

### `init-db`

Initialize the database: create all tables and a default `admin` user.

```bash
zamsec init-db
```

The admin password comes from the `ADMIN_DEFAULT_PASSWORD` environment
variable; if unset, a cryptographically random password is generated and
printed once — record it.

### `users`

Manage web-portal user accounts.

```bash
zamsec users list
zamsec users create --username john --email john@acme.co.zm --role assessor
zamsec users reset-password --username john
```

| Subcommand | Options |
|---|---|
| `list` | — (shows ID, username, email, role, active, MFA, created) |
| `create` | `--username`, `--email`, `--password` *(all prompted if omitted)*, `--role [admin\|assessor\|business_owner]` (default `assessor`) |
| `reset-password` | `--username`, `--password` *(prompted, hidden, confirmed)* |

---

## 8. Session Management

### `session`

Sign in / out of a CLI session using the same local credentials as the
desktop app (created on the desktop app's first launch). Five sign-in
attempts maximum, mirroring the desktop dialog.

```bash
zamsec session start            # sign in (default 8-hour session)
zamsec session start --hours 4
zamsec session status           # who is signed in, time remaining
zamsec session end              # sign out ('terminate' is an alias)
```

| Subcommand | Options |
|---|---|
| `start` | `--hours INT` (1–24, default 8) — session validity |
| `status` | — |
| `end` / `terminate` | — |

---

## 9. Utility Commands

### `status`

Project and environment status: version, Python, OS, project root, database
presence, core dependency check, `.env` presence, and the live list of all
available commands.

```bash
zamsec status
```

### `completion`

Print tab-completion setup for your shell. Without an argument it shows
instructions for all four shells.

```bash
zamsec completion               # all shells
zamsec completion powershell   # just PowerShell
zamsec completion bash
```

- **bash** — add `eval "$(_ZAMSEC_COMPLETE=bash_source zamsec)"` to `~/.bashrc`
- **zsh** — add `eval "$(_ZAMSEC_COMPLETE=zsh_source zamsec)"` to `~/.zshrc`
- **fish** — add `_ZAMSEC_COMPLETE=fish_source zamsec | source` to `~/.config/fish/completions/zamsec.fish`
- **powershell** — copy the printed `Register-ArgumentCompleter` block into
  your profile (`notepad $PROFILE`)

### `upgrade`

Self-update: re-installs the package with pip from the GitHub repository.
Works without git installed (downloads the branch archive over HTTPS).

```bash
zamsec upgrade
zamsec upgrade --branch develop
```

| Option | Default | Description |
|---|---|---|
| `--branch TEXT` | `main` | Git branch to upgrade from |

---

## 10. Exit Codes & CI/CD Usage

Commands designed as gates return a non-zero exit code on failure, so they
can be dropped straight into CI/CD pipelines or scheduled tasks:

| Command | `0` means | `1` means |
|---|---|---|
| `predeploy` | READY to deploy | NOT READY (failed checks) |
| `harden` | HARDENED | NEEDS ATTENTION / AT RISK |
| `fleet-scan` | fleet HARDENED | any node worse, or unreachable-node risk |
| everything else | success | error (bad input, failed operation) |

Example (GitHub Actions / any shell):

```bash
zamsec predeploy --json-out -p . || exit 1
zamsec harden --json-out -o artifacts/hardening.json
```

## 11. Environment Variables

| Variable | Used by | Purpose |
|---|---|---|
| `NODE_AGENT_TOKEN` | `node-agent` | Shared secret instead of `--token` |
| `ADMIN_DEFAULT_PASSWORD` | `init-db` | Password for the default admin (random if unset) |
| `NO_COLOR` | all commands | Disable colored output |

---

*See also: [USER_GUIDE.md](USER_GUIDE.md) (end-user guide) ·
[INSTALL_SCRIPTS.md](INSTALL_SCRIPTS.md) (installation) ·
[DEVELOPMENT.md](DEVELOPMENT.md) (contributing) ·
[features/](features/README.md) (feature deep-dives).*
