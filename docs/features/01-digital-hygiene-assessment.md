# Feature: Digital Hygiene Assessment (15-Control Framework)

## Overview
The core feature of the Zambia Digital Hygiene Certification Program. Evaluates a business against **15 security controls** worth a total of **120 points**, producing a certification tier (Gold / Silver / Bronze / Not Certified). Aligned to four international frameworks and tailored for Zambian SMBs.

---

## How It Works

### 1 — Business Information Collection
Before the assessment begins, the user fills in a business profile:

| Field | Required | Purpose |
|---|---|---|
| Business Name | Yes | Appears on certificate and reports |
| Business ID / Registration | Yes | Unique identifier for the assessment record |
| Industry | Yes | Contextualises recommendations |
| Province | No | Zambia-specific localisation |
| Contact Person / Email | No | Included in PDF output |
| Number of Employees | No | Used in risk weighting |

**File:** [`src/gui/screens/business_info.py`](../../src/gui/screens/business_info.py)

---

### 2 — Automated Checks (C01–C05)
Five controls are verified automatically on Windows using subprocess calls, registry reads and PowerShell queries. No manual input required.

| ID | Control | Weight | What is checked |
|---|---|---|---|
| C01 | OS Updates | 10 pts | Windows Update service state, last patch date, pending restart flag |
| C02 | Antivirus | 15 pts | Windows Defender: enabled, real-time on, definition age |
| C03 | Firewall | 10 pts | Domain, Private and Public profile states (netsh) |
| C04 | Password Policy | 10 pts | Min length ≥ 8, expiry ≤ 90 days, lockout ≤ 5 failures |
| C05 | Backup System | 10 pts | Backup software in registry, VSS shadow copies, cloud sync folders |

**File:** [`src/security/assessment/assessor.py`](../../src/security/assessment/assessor.py)

---

### 3 — Manual / Interview Controls (C06–C15)
Ten controls are scored through a guided question-and-answer interview. The assessor or business owner answers each question; partial scores are awarded proportionally.

| ID | Control | Weight | Category |
|---|---|---|---|
| C06 | Security Awareness Training | 8 pts | Administrative |
| C07 | Access Control Policy | 7 pts | Administrative |
| C08 | Incident Response Plan | 7 pts | Administrative |
| C09 | Data Encryption | 7 pts | Technical |
| C10 | Mobile Device Security | 5 pts | Technical |
| C11 | Physical Security | 5 pts | Physical |
| C12 | Network Security | 5 pts | Technical |
| C13 | Acceptable Use Policy | 5 pts | Administrative |
| C14 | Vendor / Third-Party Risk | 8 pts | Administrative |
| C15 | Regulatory Compliance | 8 pts | Administrative |

**File:** [`src/gui/screens/manual_checks.py`](../../src/gui/screens/manual_checks.py)

---

### 4 — Scoring & Certification

```
Score %   | Critical Failures | Tier
----------|-------------------|----------
≥ 80%     | 0                 | 🥇 GOLD
≥ 60%     | ≤ 1               | 🥈 SILVER
≥ 40%     | ≤ 2               | 🥉 BRONZE
< 40%     | any               | ✕ NOT CERTIFIED
```

**Critical failures** (any C01–C05 scoring 0) act as a gate: even a high total score cannot achieve Gold if a critical control fails.

---

### 5 — Enrichment Checks
Two controls are automatically enriched with live evidence even before manual answers arrive:

- **C09 Encryption** — enriched with BitLocker status + screen lock policy
- **C12 Network Security** — enriched with USB policy + admin shares + RDP exposure

---

## Framework Alignment

| Framework | Mapping |
|---|---|
| NIST CSF v1.1 | Identify / Protect / Detect / Respond / Recover |
| CIS Controls v8 IG1 | Implementation Group 1 (foundational) |
| ISO/IEC 27001:2022 | Annex A controls |
| UK Cyber Essentials | Five technical controls |
| Zambia DPA 2021 | Data protection requirements |
| ZICTA / CERT-ZM | Local regulatory guidance |

---

## Data Flow

```
BusinessInfo form
      ↓
DigitalHygieneAssessor.run_assessment()
      ├─ _check_os_updates()          → C01 ControlResult
      ├─ _check_antivirus_enhanced()  → C02 ControlResult
      ├─ _check_firewall_enhanced()   → C03 ControlResult
      ├─ _check_password_policy()     → C04 ControlResult
      ├─ _check_backup_system()       → C05 ControlResult
      ├─ _enrich_encryption_control() → C09 enriched
      ├─ _enrich_network_control()    → C12 enriched
      └─ _evaluate_manual() × 10     → C06–C15 ControlResult
            ↓
      AssessmentResults
      (score, tier, recommendations, controls dict)
            ↓
      Saved to local SQLite  →  Results screen  →  PDF / HTML export
```

---

## Key Classes

| Class | File | Purpose |
|---|---|---|
| `BusinessInfo` | assessor.py | Dataclass for business metadata |
| `ControlResult` | assessor.py | Single control outcome (score, status, details) |
| `AssessmentResults` | assessor.py | Complete assessment snapshot |
| `DigitalHygieneAssessor` | assessor.py | Orchestrates all 15 checks |
| `CONTROL_CATALOGUE` | assessor.py | Static registry of all 15 controls and weights |

---

## Storage
Results are saved to a local SQLite database at `instance/digital_hygiene.db` via `src/utils/local_db.py`. Each record stores the full control breakdown as JSON alongside the score, tier, timestamp and business metadata.

---

## Related Features
- [Automated Scanning](02-automated-scanning.md) — runs C01–C05
- [Results & Certification](03-results-certification.md) — displays score and issues certificate
- [Assessment History](04-assessment-history.md) — recalls past assessments
- [Report Generation](13-report-generation.md) — exports PDF/HTML

## Controls Reference
Every control this framework scores is catalogued in
[docs/controls/](../controls/README.md) — see
[endpoint-core-controls.md](../controls/endpoint-core-controls.md) (C01–C05),
[governance-controls.md](../controls/governance-controls.md) (C06–C15) and
[tool-specific-controls.md](../controls/tool-specific-controls.md) (C16–C22).
