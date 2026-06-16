# Feature: Policy Template Library

## Overview
A built-in library of **ready-to-use security policy templates** written specifically for Zambian small and medium businesses. Each template is a complete, editable policy document that the business can download as a `.txt` file and customise with their own name and details. Templates map to the manual controls (C06–C15) of the assessment framework.

**File:** [`src/gui/screens/policy_templates.py`](../../src/gui/screens/policy_templates.py)

---

## Available Templates

| Icon | Title | Framework Mapping |
|---|---|---|
| 📋 | Acceptable Use Policy (AUP) | CIS Control 14 · ISO 27001 A.8 |
| 🔐 | Password & Access Control Policy | CIS Control 5 · ISO 27001 A.9 |
| 🛡 | Incident Response Plan | CIS Control 17 · ISO 27001 A.16 |
| 💾 | Data Backup & Recovery Policy | CIS Control 11 · ISO 27001 A.12 |
| 📱 | Mobile Device & Remote Work Policy | CIS Control 4 · ISO 27001 A.6 |
| 🔒 | Data Protection Policy (Zambia DPA 2021) | Zambia DPA No. 3 of 2021 |

---

## How It Works

### Browsing Templates
Each template is displayed as a **card** showing:
- Icon and title
- One-line description
- Framework tag (e.g. "CIS Control 14 · ISO 27001 A.8")
- A **Preview** button and a **Download** button

### Previewing
Clicking **Preview** opens a `CTkToplevel` popup with the full template text rendered in a scrollable `CTkTextbox`. The text is read-only; users can scroll through to review it before downloading.

### Downloading
Clicking **Download** opens a `filedialog.asksaveasfilename` dialog. The template is written to the chosen `.txt` file path. A toast notification confirms the download.

---

## Template Format
All templates use a structured plain-text format with:
- Title block with placeholders (`[BUSINESS NAME]`, `[DATE]`, `[MANAGEMENT NAME]`)
- Numbered sections (PURPOSE, SCOPE, POLICY STATEMENTS, RESPONSIBILITIES, REVIEW)
- Zambia-specific clauses (DPA 2021 references, ZICTA/CERT-ZM contacts, mobile money guidance)

Example header:
```
ACCEPTABLE USE POLICY
=====================
[BUSINESS NAME]
Effective Date: [DATE]
Version: 1.0
Approved by: [MANAGEMENT NAME / TITLE]
```

---

## Zambia Data Protection Policy
The DPA 2021 template is the most specialised:
- Covers lawful bases for processing personal data under Zambian law
- References the Data Protection Commission (DPC) registration requirement
- Includes data subject rights (access, correction, erasure)
- Specifies breach notification requirements (72-hour window)
- Provides contact details placeholder for the Data Protection Officer

---

## Policy-to-Control Mapping

| Template | Assessment Control |
|---|---|
| Acceptable Use Policy | C13 – Acceptable Use Policy |
| Password & Access Control | C07 – Access Control Policy |
| Incident Response Plan | C08 – Incident Response Plan |
| Data Backup & Recovery | C05 – Backup System |
| Mobile Device Policy | C10 – Mobile Device Security |
| Data Protection Policy | C15 – Regulatory Compliance |

Having a downloaded / customised policy for any of these controls is evidence that can be provided during a manual verification (Tier 3) assessment.

---

## Technical Implementation

Templates are stored as Python string literals inside `policy_templates.py` in a `TEMPLATES` list. Each entry is a dict:

```python
{
    "id":          "aup",
    "icon":        "📋",
    "title":       "Acceptable Use Policy (AUP)",
    "description": "Rules governing how staff may use company computers...",
    "framework":   "CIS Control 14 · ISO 27001 A.8",
    "content":     "ACCEPTABLE USE POLICY\n...",   # full template text
}
```

This means the library works **fully offline** — no internet connection or file system dependencies required.

---

## Related Features
- [Digital Hygiene Assessment](01-digital-hygiene-assessment.md) — C06–C15 require these policies
- [Zambia Risk Assessment](08-zambia-risk-assessment.md) — DPA compliance controls
- [Report Generation](13-report-generation.md) — PDF reports reference policy gaps
