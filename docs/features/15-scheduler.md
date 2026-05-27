# Feature: Simple Scheduler

## Overview
The `SimpleScheduler` runs any Python callable on a fixed time interval in a background daemon thread. It is intentionally minimal — no external dependencies, no persistence. For production deployments, consider replacing it with APScheduler or a system service (Windows Task Scheduler / cron).

**File:** [`src/utils/scheduler.py`](../../src/utils/scheduler.py)

---

## Class: `SimpleScheduler`

```python
class SimpleScheduler:
    def add_job(self, func: Callable, interval_seconds: int) -> None
    def start(self) -> None
    def stop(self) -> None
```

---

## How It Works

1. `add_job()` appends `(func, interval_seconds)` to an internal list.
2. `start()` launches a single background daemon thread.
3. The thread wakes every **1 second** and checks each job's last-run time.
4. If `now - last_run >= interval`, the job's callable is invoked.
5. Exceptions are **silently swallowed** — a failing job never stops the scheduler.
6. The thread is a **daemon thread** — it exits automatically when the main program exits (no explicit `stop()` required in desktop-app mode).
7. `stop()` sets a flag that causes the loop to exit on its next 1-second tick.

---

## Usage Examples

### Run the Windows agent every hour

```python
from src.agents.windows_agent import collect_local_report
from src.utils.scheduler import SimpleScheduler

sched = SimpleScheduler()
sched.add_job(lambda: collect_local_report('nightly-check'), interval_seconds=3600)
sched.start()
# Reports accumulate in instance/agent_reports/ every hour
```

### Multiple jobs at different intervals

```python
sched = SimpleScheduler()
sched.add_job(quick_health_check, interval_seconds=300)   # every 5 min
sched.add_job(full_scan,          interval_seconds=86400) # every 24 h
sched.start()
```

### Stopping the scheduler

```python
sched.stop()
# The background thread exits within 1 second
```

---

## Integration with Windows Agent

The scheduler is the standard way to run the Windows Agent on a recurring basis for continuous monitoring:

```python
from src.agents.windows_agent import collect_local_report
from src.utils.scheduler import SimpleScheduler

sched = SimpleScheduler()
sched.add_job(
    lambda: collect_local_report('Acme Ltd'),
    interval_seconds=3600,
)
sched.start()
```

Reports accumulate in `instance/agent_reports/` and can be ingested by:
- The web dashboard (via [Remote Collector](10-windows-agent.md#remote-collector))
- A SIEM (via [SIEM Forwarder](11-siem-forwarder.md))

---

## Design Decisions

| Decision | Rationale |
|---|---|
| 1-second polling tick | Low overhead; gives ≤1 s latency for triggering |
| Daemon thread | App exit automatically stops the loop — no `atexit` needed |
| Silent exception swallow | One failing job should never kill the others |
| No persistence | State is in-memory only; interval resets on app restart |
| No thread pool | One job runs at a time; overlapping long jobs will delay subsequent jobs |

---

## Limitations

- **No persistence** — interval counters reset on restart.
- **No missed-run catch-up** — if the app was down when a job was due, the job simply runs at the next opportunity after startup.
- **No concurrency** — jobs run sequentially within the loop; a very slow job delays the next one.

For persistent, reliable scheduling use Windows Task Scheduler or a Python service with APScheduler.

---

## Related Features
- [Windows Agent](10-windows-agent.md) — primary consumer of the scheduler
- [SIEM Forwarder](11-siem-forwarder.md) — can be scheduled to forward reports
