# Feature: Report Generation

## Overview
The Report Generation system produces assessment reports in four formats — **JSON**, **HTML**, **PDF**, and **CSV** — from a completed `AssessmentResults` object. It is available both from the desktop GUI's Results screen and from the Flask web application's download endpoint.

**Engine file:** [`src/reporting/generator.py`](../../src/reporting/generator.py)  
**Desktop GUI:** [`src/gui/screens/results.py`](../../src/gui/screens/results.py)  
**Web download route:** `/download/<assessment_id>/<format>` in [`src/web/app.py`](../../src/web/app.py)

---

## Report Formats

### JSON

Full machine-readable export of the assessment:

```json
{
  "business": {
    "name": "Acme Ltd",
    "id": "100/2024",
    "province": "Lusaka",
    "industry": "Finance",
    "contact_person": "Jane Doe"
  },
  "assessment_date": "2026-05-27",
  "score": 98,
  "total_possible": 120,
  "percentage": 82,
  "certification_level": "GOLD",
  "critical_failures": 0,
  "controls": {
    "C01_os_updates": {
      "id": "C01", "name": "Operating System Updates",
      "status": "PASS", "score": 10, "weight": 10,
      "details": "All updates current"
    }
  },
  "recommendations": [ "Review vendor risk management policy" ]
}
```

### HTML Report

A styled dark-theme HTML page with:
- Hero certification badge with tier colour
- Score percentage (large font)
- Control results table (Status / Score / Details per row)
- Recommendations list
- Footer with generation timestamp

Opens automatically in the default browser after saving.

### PDF Report

Uses `reportlab` to generate a professional PDF:
- Title page with business name and tier
- Score breakdown table
- Control results (status, score, details)
- Recommendations section

Falls back gracefully if `reportlab` is not installed (shows an error dialog in the GUI).

### CSV Report

Flat spreadsheet-friendly format:
```
ID,Business,Score,Level,Date
1,Acme Ltd,98,GOLD,2026-05-27
```

---

## Certificate Generation (HTML)

The Results screen also generates a **printable HTML certification document** for businesses that achieve GOLD, SILVER, or BRONZE:

```
┌─────────────────────────────────────────────────────────┐
│  University of Zambia · Dept. of Computing & Informatics│
│  Zambia Digital Hygiene Certification Programme          │
│  ─────────────────────────────────────────────────────  │
│               This certifies that                        │
│                     Acme Ltd                             │
│         100/2024  ·  Lusaka  ·  Finance                  │
│                  has achieved                            │
│                       🥇                                │
│                  GOLD CERTIFICATION                      │
│           ┌───────────────────────────┐                  │
│           │          82%              │                  │
│           │     98 / 120 points       │                  │
│           └───────────────────────────┘                  │
│        Assessed: 27 May 2026  ·  Valid until: 27 May 2027│
│  NIST CSF v1.1 · CIS Controls v8 · ISO 27001:2022 · DPA │
└─────────────────────────────────────────────────────────┘
```

The certificate:
- Is colour-coded by tier (gold/silver/bronze border and accents)
- Lists all passed controls
- Shows validity date (+1 year from assessment date)
- Opens automatically in the default browser after saving

---

## Desktop GUI Exports

From the **Results screen** navigation bar:

| Button | Format | Notes |
|---|---|---|
| 💾 JSON | `.json` | Always enabled |
| 📄 HTML Report | `.html` | Always enabled; opens browser |
| 📑 PDF Report | `.pdf` | Requires `reportlab` |
| 🏆 Certificate | `.html` | Only enabled for GOLD/SILVER/BRONZE |

All four use `filedialog.asksaveasfilename()` — the user picks the save location.

---

## Web Application Downloads

The web app serves reports via:

```
GET /download/<assessment_id>/<format>
```

Where `<format>` is one of `pdf`, `html`, `json`, or `csv`.

Access is restricted to:
- The assessor who performed the assessment
- Business owners (their own business only)
- Admins (any assessment)

---

## ReportGenerator API

```python
from src.reporting.generator import ReportGenerator

gen = ReportGenerator(output_dir='reports/')

# Generate files
pdf_path  = gen.generate_pdf_report(results, business_info, 'assessment_1')
html_path = gen.generate_html_report(results, business_info, 'assessment_1')

# In-memory
json_dict = gen.generate_json_report(results, business_info)
csv_rows  = gen.generate_csv_report(results, business_info)
```

---

## Auto-Save Behaviour

When `ResultsScreen` first loads, `_auto_save()` runs automatically:
- Saves the assessment to the local SQLite database via `local_db.save_assessment()`
- Sets the next reassessment due date to **+6 months** via `local_db.set_reassessment_date()`

This happens without any user action.

---

## Related Features
- [Results & Certification](03-results-certification.md) — the screen that hosts the export buttons
- [Digital Hygiene Assessment](01-digital-hygiene-assessment.md) — produces the `AssessmentResults` object
- [Web Application](18-web-application.md) — web download endpoint
