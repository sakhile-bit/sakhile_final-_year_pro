# Feature: Results & Certification

## Overview
After the assessment completes, the Results screen presents a visual score summary, issues a **digital certification badge** (Gold / Silver / Bronze / Not Certified), shows a full control-by-control breakdown with effort labels, and allows the business to **export** their certificate or full report.

**File:** [`src/gui/screens/results.py`](../../src/gui/screens/results.py)

---

## Certification Tiers

| Tier | Minimum Score | Critical Failures Allowed | Badge |
|---|---|---|---|
| 🥇 GOLD | ≥ 80% (96/120) | 0 | Gold medal |
| 🥈 SILVER | ≥ 60% (72/120) | ≤ 1 | Silver medal |
| 🥉 BRONZE | ≥ 40% (48/120) | ≤ 2 | Bronze medal |
| ✕ NOT CERTIFIED | < 40% | any | Red cross |

A **critical failure** is any of C01–C05 scoring 0 (completely failed critical control). Critical failures act as a gate: a business cannot achieve Gold with even one critical failure, regardless of total score.

---

## Ring Chart Widget

A custom `_RingChart` class drawn on a `tk.Canvas` renders a circular progress ring:

- **Arc** drawn from 270° (12 o'clock) sweeping clockwise proportional to the score percentage  
- **Colour** matches the certification tier (`#FFD700` Gold, `#C0C0C0` Silver, `#CD7F32` Bronze, `#E84040` Not Certified)
- **Centre text** shows the percentage (e.g. `78%`)
- **Size** defaults to 140 × 140 px, configurable

```python
class _RingChart(tk.Canvas):
    def __init__(self, parent, pct, colour, size=140, bg=CLR_SURFACE)
```

---

## Screen Sections

### Header Card
- Business name, assessment date and industry
- Tier badge with colour stripe
- Total score `XX / 120 pts`

### Ring Chart + Tier Badge
Side-by-side layout:
- Left: animated ring chart with percentage
- Right: large tier icon, tier label, score label, recommendations count

### Control Breakdown Table
All 15 controls listed with:
- Status icon (✔ / ⚠ / ✖ / –)
- Control name and score `pts / weight`
- **Effort label** indicating how long the fix will take:
  - ⚡ Quick Fix (C01–C03) — can be resolved today
  - 📅 This Week (C04, C05, C09, C10, C12)
  - 📆 This Month (C06–C08, C11, C13)
  - 🔁 Ongoing (C14, C15)

### Recommendations Panel
Prioritised list of actionable steps ordered by:
1. Critical FAIL controls first
2. Then by potential score uplift (highest weight failures)
3. Manual unanswered controls
4. Zambia-specific compliance reminders (DPA, ZICTA)

### Reassessment Reminder
Sets a recommended reassessment date **90 days** from today and saves it to the local database. A banner appears on the Welcome screen when the date is within 30 days.

---

## Export Options

| Format | Description |
|---|---|
| 📄 PDF Certificate | One-page certificate with business name, tier badge, score, date. Requires `reportlab`. |
| 📊 HTML Report | Full interactive report with all 15 controls, recommendations, framework references |
| 📋 JSON | Machine-readable assessment data for SIEM ingestion or archiving |
| 📝 CSV | Spreadsheet-friendly control-by-control breakdown |

Exports are saved to a user-selected directory via a file dialog (`tkinter.filedialog.asksaveasfilename`).

---

## Data Storage
On completion, results are saved to `instance/digital_hygiene.db` (SQLite) via `src/utils/local_db.save_assessment()`. The record includes:

```json
{
  "biz_name": "Acme Ltd",
  "industry": "Finance",
  "score": 78,
  "pct": 65,
  "tier": "SILVER",
  "controls_json": "{...}",
  "recommendations_json": "[...]",
  "saved_at": "2026-05-27T10:30:00"
}
```

---

## Related Features
- [Digital Hygiene Assessment](01-digital-hygiene-assessment.md) — produces the results object
- [Assessment History](04-assessment-history.md) — view this result later
- [Report Generation](13-report-generation.md) — PDF/HTML export engine
- [Welcome Screen](14-welcome-dashboard.md) — shows last assessment card
