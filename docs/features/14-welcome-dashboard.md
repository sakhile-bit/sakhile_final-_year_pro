# Feature: Welcome / Home Dashboard

## Overview
The Welcome screen is the first thing users see when the desktop application launches. It is a **two-column professional layout**: a fixed left brand panel and a right action panel. It shows the user's last assessment result at a glance and provides quick-launch buttons for every tool in the application.

**File:** [`src/gui/screens/welcome.py`](../../src/gui/screens/welcome.py)

---

## Layout

```
┌────────────────────────┬──────────────────────────────────────────────────┐
│  Left Brand Panel      │  Right Action Panel                              │
│  (290 px fixed)        │  (grows to fill window)                          │
│                        │                                                  │
│  🛡 Shield mark        │  Your Digital Hygiene Dashboard                  │
│                        │  Assess, remediate and certify your business...  │
│  Zambia                │                                                  │
│  Digital Hygiene       │  ┌─ Last Assessment Card ──────────────────────┐ │
│  Certification         │  │ 🥇  My Company · 82%  GOLD CERTIFICATION    │ │
│  Program               │  │ 2026-05-27  ·  Finance                      │ │
│                        │  └────────────────────────────────────────────┘ │
│  ── Stats ──           │                                                  │
│  15  Security Controls │  ▶  Start New Assessment                         │
│   3  Cert Tiers        │                                                  │
│  120 Max Score Points  │  ⏰  Reassessment due in 12 day(s) — 08 Jun 2026 │
│                        │                                                  │
│  NIST CSF  CIS v8      │  ┌────────────┬────────────┬────────────────┐   │
│  ISO 27001  DPA 2021   │  │📋 History  │🌐 Network  │🔍 Infra Scan   │   │
│                        │  ├────────────┼────────────┼────────────────┤   │
│  v1.0  University of   │  │🇿🇲 Zambia  │📄 Policy   │🚀 Deploy Check │   │
│  Zambia                │  └────────────┴────────────┴────────────────┘   │
└────────────────────────┴──────────────────────────────────────────────────┘
```

---

## Left Brand Panel

Displays:
- **Shield icon** (🛡) in the accent colour (`#6C5FC7`)
- **Programme name** — "Zambia Digital Hygiene Certification Program"
- **Key stats** — three stat cards:
  - 15 Security Controls (purple)
  - 3 Certification Tiers (amber)
  - 120 Max Score Points (blue)
- **Framework tags** — NIST CSF · CIS Controls v8 · ISO 27001 · Zambia DPA 2021
- **Footer** — version and University of Zambia attribution

---

## Last Assessment Card

Reads the most recent saved assessment from `local_db.list_assessments(limit=1)`.

**If an assessment exists**, shows:
- Left tier colour stripe (GOLD=#F5C518 / SILVER=#C0CDD8 / BRONZE=#D4873A / NOT CERTIFIED=#E84040)
- Business name, assessment date, industry
- Score percentage and tier badge pill

**If no assessment exists**, shows four feature preview pills instead:
- 🔧 One-click auto-remediation
- 🏅 Gold / Silver / Bronze cert
- 🔍 Infrastructure web scanner
- 📄 Policy template library

---

## Reassessment Reminder Banner

Reads the scheduled reassessment date from `local_db.get_reassessment_date()`.

- If due within 30 days → amber `⏰ Reassessment due in N day(s)` banner
- If overdue → red `🔴 Reassessment overdue` banner
- Otherwise → no banner shown

Reassessment date is set automatically to **+6 months** when the ResultsScreen auto-saves.

---

## Primary CTA

A large `▶  Start New Assessment` button that launches the assessment wizard (`on_start` callback → `business_info.py`).

---

## Tool Grid

Six quick-launch buttons in a 2×3 grid, each coloured by function:

| Button | Colour | Destination |
|---|---|---|
| 📋 History | Purple `#6C5FC7` | Assessment history screen |
| 🌐 Network Scan | Cyan `#00B0D0` | Local network scanner |
| 🔍 Infra Scan | Blue `#2485E8` | Infrastructure / external host scanner |
| 🇿🇲 Zambia Risk | Amber `#FFB800` | Zambia-specific risk assessment |
| 📄 Policy Docs | Orange `#CD8A3A` | Policy template library |
| 🚀 Deploy Check | Green `#39D353` | Pre-deployment checker |

---

## Constructor

```python
WelcomeScreen(
    master,
    on_start,           # Callable — launches assessment wizard
    on_history=None,    # Callable — opens history screen
    on_infra=None,      # Callable — opens infra scanner
    on_zambia_risk=None,# Callable — opens Zambia risk screen
    on_policies=None,   # Callable — opens policy templates
    on_network=None,    # Callable — opens network scanner
    on_deploy=None,     # Callable — opens deployment checker
)
```

---

## Related Features
- [Digital Hygiene Assessment](01-digital-hygiene-assessment.md) — launched from `▶ Start New Assessment`
- [Assessment History](04-assessment-history.md) — launched from History tile
- [Network Scanner](05-network-scanner.md) — launched from Network Scan tile
- [Infrastructure Scanner](06-infra-scanner.md) — launched from Infra Scan tile
- [Zambia Risk Assessment](08-zambia-risk-assessment.md) — launched from Zambia Risk tile
- [Policy Templates](09-policy-templates.md) — launched from Policy Docs tile
- [Deployment Checker](07-deployment-checker.md) — launched from Deploy Check tile
