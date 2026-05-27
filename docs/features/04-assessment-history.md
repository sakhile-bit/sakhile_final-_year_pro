# Feature: Assessment History

## Overview
The History screen lists every past assessment stored in the local database, lets the user drill into the full control breakdown of any individual assessment, and offers a **side-by-side comparison** of any two assessments to visualise progress over time.

**File:** [`src/gui/screens/history.py`](../../src/gui/screens/history.py)  
**Database:** [`src/utils/local_db.py`](../../src/utils/local_db.py)

---

## History List

Each row in the list shows:

| Field | Example |
|---|---|
| Tier badge (coloured stripe) | 🥈 SILVER |
| Business name | Acme Technologies Ltd |
| Date | 2026-05-15 |
| Industry | Technology |
| Score | 78 / 120 (65%) |
| Action buttons | View Details · Compare |

Rows are sorted newest-first. The list uses a `CTkScrollableFrame` so it handles any number of past assessments.

---

## View Details
Clicking **View Details** opens a `CTkToplevel` popup with:

- Header: business name, tier, score, date
- Full 15-control breakdown table (control ID, name, status icon, score, details text)
- Prioritised recommendations list

---

## Side-by-Side Comparison (`_show_compare`)

The comparison view opens when the user clicks **Compare** on a history row. It shows two assessments columns next to each other:

```
┌─────────────────────────┬─────────────────────────┐
│  Assessment A (older)   │  Assessment B (newer)   │
│  Acme Ltd — 2026-03-01  │  Acme Ltd — 2026-05-15  │
│  BRONZE · 48/120 (40%)  │  SILVER · 78/120 (65%)  │
├─────────────────────────┼─────────────────────────┤
│ C01 ✔ PASS  10/10       │ C01 ✔ PASS  10/10       │
│ C02 ✖ FAIL   0/15       │ C02 ⚠ WARN   9/15       │  ← improvement shown
│ C03 ✔ PASS   9/10       │ C03 ✔ PASS  10/10       │
│ ...                     │ ...                     │
└─────────────────────────┴─────────────────────────┘
```

**Colour coding:**
- Green highlight: control improved between the two assessments
- Red highlight: control regressed
- No highlight: unchanged

The comparison is built from two calls to `local_db.get_assessment(id)`, with the full `controls_json` decoded and rendered side-by-side in a scrollable grid.

---

## Database Operations

| Function | Purpose |
|---|---|
| `list_assessments(limit)` | Fetch most recent N assessments (default: all) |
| `get_assessment(id)` | Fetch one full assessment record by primary key |
| `assessment_count()` | Count total stored assessments |
| `delete_assessment(id)` | Remove a single record |

Schema (SQLite table `assessments`):

```sql
CREATE TABLE assessments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    biz_name        TEXT NOT NULL,
    biz_id          TEXT,
    industry        TEXT,
    province        TEXT,
    score           INTEGER,
    total_possible  INTEGER,
    pct             INTEGER,
    tier            TEXT,
    controls_json   TEXT,
    recommendations_json TEXT,
    saved_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## History Button on Welcome Screen
The **📋 History** tool button on the Welcome screen shows the count of stored assessments in brackets (e.g. `📋 History (7)`). Clicking navigates to this screen.

---

## Related Features
- [Digital Hygiene Assessment](01-digital-hygiene-assessment.md) — creates the records shown here
- [Results & Certification](03-results-certification.md) — the screen that saves to history
- [Welcome Dashboard](14-welcome-dashboard.md) — shows the most recent result card
