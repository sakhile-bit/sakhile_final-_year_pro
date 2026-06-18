# Changelog — Zambia Digital Hygiene Certification App

---

## 2026-06-18 — Refactor: SQLite Local Storage (replaces JSON files)

**Author:** Development Session (Claude Code)

All local persistent state previously stored in JSON files (`instance/credentials.json`, `instance/agent_reports/*.json`) has been moved into the existing SQLite database (`history.db`). Two new tables were added: `credentials` and `agent_reports`. The `instance/agent_reports/` directory and `instance/credentials.json` file are no longer created or read.

**Files changed:**

| File | Change |
|---|---|
| `src/utils/local_db.py` | Added `credentials` and `agent_reports` tables + CRUD functions |
| `src/utils/auth.py` | Rewritten — delegates all I/O to `local_db`; no file access |
| `src/agents/windows_agent.py` | Saves reports to SQLite; returns `report_id` instead of `report_path` |
| `src/security/assessment/remote_collector.py` | `load_agent_report` now takes an int id; added `list_agent_reports` |
| `tests/test_windows_agent.py` | Updated assertion from `report_path` to `report_id` |

See [sqlite_migration.md](sqlite_migration.md) for full details.

---

## 2026-05-31 — Bug fixes and extended assessment flow

**Author:** Development Session (Claude Code)  
**Branch:** main

---

## Table of Contents

1. [Bug Fix — Geometry Manager Conflicts (TclError)](#1-bug-fix--geometry-manager-conflicts-tclerror)
2. [Bug Fix — Window Centering Overlaps Windows Taskbar](#2-bug-fix--window-centering-overlaps-windows-taskbar)
3. [Feature — Extended Assessment Flow (Steps 1→5, Tool Controls C16–C20)](#3-feature--extended-assessment-flow-steps-15-tool-controls-c16c20)
4. [File-by-File Reference](#4-file-by-file-reference)

---

## 1. Bug Fix — Geometry Manager Conflicts (TclError)

### What was wrong

Tkinter (and by extension CustomTkinter) has a strict rule: **you cannot mix `.pack()` and `.grid()` on widgets that share the same parent container.** If any widget in a frame uses `.grid()`, every sibling widget in that frame must also use `.grid()`, and vice versa.

Every screen in the app imports `_header()` from `business_info.py`. That helper places the header bar into the parent using:

```python
hdr.grid(row=0, column=0, sticky="ew")
```

So as soon as `_header(self, ...)` is called on a screen class (where `self` is a `CTkFrame`), the geometry manager for `self` is committed to **grid**. Any subsequent call to `.pack()` on a direct child of `self` raises:

```
TclError: cannot use geometry manager pack inside .auditlogviewerscreen
which already has slaves managed by grid
```

This crash appeared every time one of the affected buttons was clicked in the welcome screen.

### What was fixed

Six screen files had their `main_frame` and `footer` widgets changed from `.pack()` to `.grid()`, and `pack_propagate(False)` was replaced with `grid_propagate(False)` where applicable.

#### Files changed

| File | What changed |
|---|---|
| `src/gui/screens/audit_log_viewer.py` | `main_frame.pack(...)` → `main_frame.grid(row=1, ...)` · `footer.pack(...)` → `footer.grid(row=2, ...)` · added `self.grid_columnconfigure/rowconfigure` |
| `src/gui/screens/assessment_dashboard.py` | Same pattern |
| `src/gui/screens/export_reports.py` | Same pattern |
| `src/gui/screens/remediation_guidance.py` | Same pattern **+** `accent_bar.pack_propagate(False)` → `accent_bar.grid_propagate(False)` (accent bar is placed with `.grid()`, so `pack_propagate` is the wrong API) |
| `src/gui/screens/settings.py` | Same pattern |
| `src/gui/screens/active_directory.py` | Same pattern |

#### Pattern applied to every affected screen

```python
# BEFORE (broken)
def _build(self):
    _header(self, "Screen Title", "", 0.0)          # uses grid internally

    main_frame = ctk.CTkFrame(self, ...)
    main_frame.pack(fill="both", expand=True, ...)  # ← CONFLICT

    footer = ctk.CTkFrame(self, height=NAV_H, ...)
    footer.pack(side="bottom", fill="x")            # ← CONFLICT
    footer.pack_propagate(False)

# AFTER (fixed)
def _build(self):
    self.grid_columnconfigure(0, weight=1)
    self.grid_rowconfigure(1, weight=1)             # main_frame row expands

    _header(self, "Screen Title", "", 0.0)          # grid row=0

    main_frame = ctk.CTkFrame(self, ...)
    main_frame.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=PAD)  # ✓

    footer = ctk.CTkFrame(self, height=NAV_H, ...)
    footer.grid(row=2, column=0, sticky="ew")       # ✓
    footer.grid_propagate(False)
```

> **Rule of thumb for future screens:** once `_header(self, ...)` is called, always use `.grid()` for every other direct child of `self`. Widgets *inside* sub-frames (like buttons inside a footer) can freely use `.pack()` among themselves.

---

## 2. Bug Fix — Window Centering Overlaps Windows Taskbar

### What was wrong

`app.py` centred the app window using the full screen height:

```python
y = (self.winfo_screenheight() - WIN_H) // 2
```

On a 1366×768 display with a 40 px Windows taskbar, the available vertical work area is only ~728 px. `WIN_H = 700` plus the ~32 px title bar gives a total window height of ~732 px — larger than the work area. The result: the window's footer nav bar was hidden behind the taskbar. Users (and automated tests) could not see or click the **Back** button.

### What was fixed

`app.py` now queries the OS for the usable work area using `SystemParametersInfoW` (Windows API `SPI_GETWORKAREA`, code `48`) and centres within that rectangle instead of the raw screen dimensions.

```python
# src/gui/app.py — __init__
import sys
if sys.platform == "win32":
    import ctypes, ctypes.wintypes
    wa = ctypes.wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(wa), 0)
    work_w = wa.right  - wa.left
    work_h = wa.bottom - wa.top
    x = wa.left + max(0, (work_w - WIN_W) // 2)
    y = wa.top  + max(0, (work_h - WIN_H) // 2)
else:
    x = (self.winfo_screenwidth()  - WIN_W) // 2
    y = (self.winfo_screenheight() - WIN_H) // 2
self.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")
```

The `else` branch keeps the old behaviour on macOS/Linux where the taskbar situation is different.

---

## 3. Feature — Extended Assessment Flow (Steps 1→5, Tool Controls C16–C20)

### Overview

Previously the certification assessment was a fixed 4-step, 15-control flow:

```
Step 1  Business Info
Step 2  Automated Scan     (C01–C05)
Step 3  Manual Questions   (C06–C15)
Step 4  Results
```

The total possible score was always **120 points** (sum of weights for C01–C15).

**After this change**, the flow is 5 steps and the business can opt into up to 5 additional scored controls (C16–C20), raising the total possible score to a maximum of **156 points**:

```
Step 1  Business Info
Step 2  Security Tools & Infrastructure   ← NEW
Step 3  Automated Scan     (C01–C05)
Step 4  Manual Questions   (C06–C15 + selected tool questions)
Step 5  Results            (core section + Advanced Tools section)
```

The 5 additional controls are **optional** — they only appear if the business declares that tool/infrastructure applies to them. Businesses that select none of the tools still go through the same 15-control, 120-point assessment.

### Step 2 — Security Tools & Infrastructure (`tools_profile.py`)

**New file:** `src/gui/screens/tools_profile.py`

This screen presents 5 toggle cards. Each card shows:
- An icon, tool name, and control ID badge (C16–C20)
- A one-sentence description of what the tool covers
- A note on what the selection adds to the certification

The entire card is clickable (not just the switch). The selection is returned as a plain Python `set[str]` of tool IDs:

```python
{"active_dir", "network_scan", "infra_scan", "zambia_risk", "remediation"}
```

The mapping of tool IDs to controls:

| Tool ID | Control | Name | Weight |
|---|---|---|---|
| `active_dir` | C16 | Active Directory Security | 8 pts |
| `network_scan` | C17 | Network Architecture Assessment | 7 pts |
| `infra_scan` | C18 | Infrastructure Security Assessment | 7 pts |
| `zambia_risk` | C19 | Zambia Local Threat Mitigation | 8 pts |
| `remediation` | C20 | Remediation Process | 6 pts |

### Step Indicator — `_header()` in `business_info.py`

The shared `_header()` helper previously hard-coded 4 dots for the progress indicator. It now parses the total from the step string:

```python
# Before
for i in range(4):          # hard-coded
    ...

# After
parts = step.split(" of ")  # "2 of 5" → step_num=2, total_steps=5
step_num = int(parts[0])
total_steps = int(parts[1]) if len(parts) == 2 else 4
for i in range(total_steps):
    ...
```

Step strings were updated across all assessment screens:

| Screen | Old | New |
|---|---|---|
| `business_info.py` | `"1 of 4"` | `"1 of 5"` |
| `tools_profile.py` | — | `"2 of 5"` |
| `scanning.py` | `"2 of 4"` | `"3 of 5"` |
| `manual_checks.py` | `"3 of 4"` | `"4 of 5"` |
| `results.py` | `"4 of 4"` | `"5 of 5"` |

### Assessor — Optional Controls (`assessor.py`)

**New constant:** `TOOL_CONTROLS` — a dict of 5 control definitions in the same schema as `CONTROL_CATALOGUE`.

**New constant:** `TOOL_ID_TO_CONTROL` — reverse-lookup map from tool ID to control key.

`DigitalHygieneAssessor.__init__` now accepts `selected_tools: set | None`. When provided, the matching tool controls are merged into `self.controls` alongside the core 15:

```python
assessor = DigitalHygieneAssessor(
    business_info,
    manual_answers=scores,
    assessment_tier="full",
    selected_tools={"active_dir", "zambia_risk"},   # ← new param
)
```

`run_assessment()` evaluates C16–C20 using the same `_evaluate_manual()` helper as C06–C15. The `total_possible` score is computed dynamically:

```python
total_possible = TOTAL_POSSIBLE_SCORE + sum(
    TOOL_CONTROLS[k]["weight"]
    for k in TOOL_CONTROLS
    if TOOL_CONTROLS[k]["tool_id"] in self.selected_tools
)
```

Certification thresholds (Gold ≥ 80%, Silver ≥ 60%, Bronze ≥ 40%) remain percentage-based, so selecting more tools does not make certification easier or harder — a business must perform well across the extended set to achieve the same tier.

### Manual Checks — Tool Questions (`manual_checks.py`)

`ManualChecksScreen.__init__` now accepts `selected_tools=None`. Two new module-level dicts drive the extended questions:

#### `TOOL_QUESTIONS`

Maps each tool ID to a list of question tuples `(ctrl_key, cid, name, question, hint)`. Each tool has 2–3 sub-questions:

| Tool | Sub-questions |
|---|---|
| `active_dir` | C16 — AD password policies · C16b — Privileged account review · C16c — Stale account management |
| `network_scan` | C17 — Network device inventory · C17b — Network segmentation · C17c — Port & service exposure |
| `infra_scan` | C18 — SSL/TLS validity · C18b — HTTP security headers · C18c — Risky port closure |
| `zambia_risk` | C19 — Zambia threat training · C19b — Regulatory compliance · C19c — Mobile money controls |
| `remediation` | C20 — Findings tracking register · C20b — Remediation SLA adherence |

#### `_TOOL_Q_WEIGHTS` and `_TOOL_Q_PARENT`

Sub-question weights are proportional to the parent control's total weight. `_TOOL_Q_PARENT` maps each sub-question key back to its parent control key. The submit method aggregates sub-question scores into the parent:

```python
# Weighted aggregation of sub-questions → parent control score
ctrl_weight = TOOL_CONTROLS[parent]["weight"]
manual_scores[parent] = round(ctrl_weight * sub_total / sub_max)
```

The live score display updates the maximum points label dynamically based on which tools were selected.

#### Rendering

Tool sections are rendered **below** the core C06–C15 questions, separated by a coloured section divider that matches the tool's accent colour. Each section shows the tool name and lists its questions using the same `_make_question()` card used for the core controls.

### Results Screen (`results.py`)

#### New `TOOL_CONTROL_KEYS` constant

```python
TOOL_CONTROL_KEYS = {
    "C16_active_directory", "C17_network_scan",
    "C18_infra_scan", "C19_zambia_risk", "C20_remediation",
}
```

Used to split the control breakdown into two sections.

#### Effort labels

Five new entries added to the `EFFORT` dict so that the Action Plan section assigns a remediation effort badge to each tool control:

```python
"C16_active_directory":  ("📅 This Week",  "#6C5FC7"),
"C17_network_scan":      ("📆 This Month", "#2485E8"),
"C18_infra_scan":        ("📆 This Month", "#5A7490"),
"C19_zambia_risk":       ("📆 This Month", "#F0A500"),
"C20_remediation":       ("🔁 Ongoing",    "#27AE60"),
```

#### Two-section breakdown

The control breakdown loop was refactored from a single flat list to two sections:

1. **Core Controls (C01–C15)** — always present
2. **Advanced Tool Assessments (C16–C20)** — rendered only when the assessment included tool controls

A shared inner function `_render_ctrl_row()` is used by both sections to avoid code duplication.

### App Wiring (`app.py`)

- `self._selected_tools: set` stored on the app instance (next to `_business_info` and `_auto_results`)
- New method `_show_tools_profile(business_info)` swaps in `ToolsProfileScreen`
- `_show_business_info()` now routes to `_show_tools_profile` on submit (was `_show_scanning`)
- `_show_scanning(selected_tools=None)` saves `selected_tools` before swapping in the scan screen
- `_show_manual(auto_results)` passes `selected_tools=self._selected_tools` to `ManualChecksScreen`
- `_show_results(...)` passes `selected_tools=self._selected_tools` to `DigitalHygieneAssessor`

---

## 4. File-by-File Reference

| File | Type | Summary |
|---|---|---|
| `src/gui/screens/tools_profile.py` | **New** | Step 2 of 5 — tool selection cards |
| `src/gui/screens/business_info.py` | Modified | `_header` supports variable step count; step updated to 1 of 5 |
| `src/gui/screens/scanning.py` | Modified | Step updated to 3 of 5 |
| `src/gui/screens/manual_checks.py` | Modified | Accepts `selected_tools`; adds `TOOL_QUESTIONS`, `_TOOL_Q_WEIGHTS`, `_TOOL_Q_PARENT`; extended scoring |
| `src/gui/screens/results.py` | Modified | `TOOL_CONTROL_KEYS`; effort labels C16–C20; two-section breakdown |
| `src/gui/screens/audit_log_viewer.py` | Modified | `pack` → `grid` geometry fix |
| `src/gui/screens/assessment_dashboard.py` | Modified | `pack` → `grid` geometry fix |
| `src/gui/screens/export_reports.py` | Modified | `pack` → `grid` geometry fix |
| `src/gui/screens/remediation_guidance.py` | Modified | `pack` → `grid` geometry fix + `pack_propagate` → `grid_propagate` on accent bar |
| `src/gui/screens/settings.py` | Modified | `pack` → `grid` geometry fix |
| `src/gui/screens/active_directory.py` | Modified | `pack` → `grid` geometry fix |
| `src/gui/app.py` | Modified | Work-area centring; `_selected_tools` state; `_show_tools_profile()` wired in; `selected_tools` threaded through flow |
| `src/security/assessment/assessor.py` | Modified | `TOOL_CONTROLS` dict (C16–C20); `TOOL_ID_TO_CONTROL` lookup; `DigitalHygieneAssessor` accepts `selected_tools`; dynamic `total_possible` |

---

## Scoring Reference

### Core controls (unchanged)

| Control | Name | Weight | Critical |
|---|---|---|---|
| C01 | OS Updates | 10 | Yes |
| C02 | Antivirus | 15 | Yes |
| C03 | Firewall | 10 | Yes |
| C04 | Password Policy | 10 | Yes |
| C05 | Backup System | 10 | Yes |
| C06 | Security Training | 8 | No |
| C07 | Access Control | 7 | No |
| C08 | Incident Response | 7 | No |
| C09 | Encryption | 7 | No |
| C10 | Mobile Security | 5 | No |
| C11 | Physical Security | 5 | No |
| C12 | Network Security | 5 | No |
| C13 | Acceptable Use | 5 | No |
| C14 | Vendor Risk | 8 | No |
| C15 | Regulatory Compliance | 8 | No |
| **Total** | | **120** | |

### Tool controls (optional, additive)

| Control | Name | Weight | Tool ID |
|---|---|---|---|
| C16 | Active Directory Security | 8 | `active_dir` |
| C17 | Network Architecture Assessment | 7 | `network_scan` |
| C18 | Infrastructure Security Assessment | 7 | `infra_scan` |
| C19 | Zambia Local Threat Mitigation | 8 | `zambia_risk` |
| C20 | Remediation Process | 6 | `remediation` |
| **Max additional** | | **36** | |

### Certification thresholds (percentage-based, unchanged)

| Tier | Score % | Critical Failures Allowed |
|---|---|---|
| Gold | ≥ 80% | 0 |
| Silver | ≥ 60% | ≤ 1 |
| Bronze | ≥ 40% | ≤ 2 |
| Not Certified | < 40% | any |

---

*End of changelog.*
