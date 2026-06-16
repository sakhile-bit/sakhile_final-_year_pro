# Feature: Zambia Local Threat Assessment

## Overview
A dedicated checklist assessment targeting **threats specific to Zambia** — mobile money fraud, WhatsApp impersonation scams, SIM swap attacks and local regulatory compliance. Users tick each control they have in place; the tool calculates an overall risk level and lists the gaps.

**GUI file:** [`src/gui/screens/zambia_risk.py`](../../src/gui/screens/zambia_risk.py)  
**Engine:** `ZambiaRiskAssessor` class in [`src/security/assessment/assessor.py`](../../src/security/assessment/assessor.py)

---

## Why Zambia-Specific?

Standard cybersecurity frameworks (NIST, CIS) don't address:
- **SIM swap fraud** — the leading cybercrime in Zambia, used to steal mobile money OTPs
- **Mobile money platforms** — Airtel Money, MTN MoMo, Zamtel Kwacha
- **WhatsApp executive impersonation** — "CEO fraud" via WhatsApp is extremely common in Zambian SMBs
- **Zambia Data Protection Act No. 3 of 2021** — local legal requirement
- **Cyber Security and Cyber Crimes Act 2021** — criminal penalties for system misuse
- **ZICTA / CERT-ZM** — free local security alert subscriptions

---

## Assessment Categories

### 📱 Mobile Money & SIM Security (4 controls)

| Key | Question |
|---|---|
| `sim_swap_protection` | SIM PIN set on all company SIMs; registered for swap alerts |
| `mobile_money_limits` | Daily transaction limits on Airtel Money, MTN MoMo, Zamtel Kwacha |
| `mobile_money_2fa` | Mobile money PIN not shared with anyone |
| `mobile_money_policy` | Written policy for mobile money approvals and authorisations |

### 📧 Email & Phishing Protection (4 controls)

| Key | Question |
|---|---|
| `phishing_training` | Staff trained in last 12 months to recognise phishing / social engineering |
| `email_mfa` | MFA enabled on all business email accounts |
| `spf_dmarc` | SPF and DMARC DNS records configured to prevent email spoofing |
| `whatsapp_fraud_awareness` | Staff warned about WhatsApp impersonation scams |

### ⚖️ Zambia Legal Compliance (4 controls)

| Key | Question |
|---|---|
| `dpa_registered` | Registered with the Data Protection Commission (DPC) |
| `dpa_policy` | Written Data Protection Policy in place |
| `cyber_crimes_act` | Staff aware of Cyber Security and Cyber Crimes Act 2021 |
| `zicta_alerts` | Subscribed to ZICTA / CERT-ZM security alerts |

### 💼 Business Continuity (4 controls)

| Key | Question |
|---|---|
| `backup_offsite` | Backups stored off-site or in the cloud |
| `disaster_recovery` | Written plan for operating if all computers destroyed |
| `supplier_security` | Key technology suppliers assessed for their own security |
| `cyber_insurance` | Cyber insurance in place or formally assessed |

---

## Risk Scoring

```
Controls ticked / 16 total → Score %

Score ≥ 75%  →  LOW RISK    (purple #6C5FC7)
Score ≥ 45%  →  MEDIUM RISK (amber #FFB800)
Score < 45%  →  HIGH RISK   (red #FF4C4C)
```

---

## Results Display

After clicking **Calculate Risk →**:

1. **Risk level badge** (LOW / MEDIUM / HIGH) in the appropriate colour
2. **Score bar** — `CTkProgressBar` showing percentage
3. **Mitigated count** — "X of 16 controls in place (Y%)"
4. **Gap list** — every unticked control listed with its full question text and a ✖ icon

The results panel inserts itself at the bottom of the scrollable form and the view scrolls to it automatically.

---

## Hint System
Every control card includes a **💡 hint** explaining:
- *Why* it matters in the Zambian context
- *What* the risk is if it's not in place

Example hint for SIM swap:
> *SIM swap fraud is a leading cybercrime in Zambia — attackers transfer your number to steal mobile money OTPs.*

---

## ZambiaRiskAssessor (assessor.py)

The `ZambiaRiskAssessor` class provides a programmatic interface:

```python
from src.security.assessment.assessor import ZambiaRiskAssessor

assessor = ZambiaRiskAssessor()
answers = {
    'sim_swap_protection': True,
    'mobile_money_limits': True,
    'email_mfa': False,
    # ... 16 keys total
}
result = assessor.assess(answers)
# Returns:
# {
#   'risk_level': 'MEDIUM RISK',
#   'score': 50.0,
#   'mitigated': 8,
#   'total': 16,
#   'gaps': ['email_mfa', ...]
# }
```

---

## Legal References

| Law | Relevance |
|---|---|
| **Zambia Data Protection Act No. 3 of 2021** | Registration with DPC required for businesses processing personal data |
| **Cyber Security and Cyber Crimes Act 2021** | Criminal penalties for misuse of computer systems |
| **ZICTA** | Zambia Information and Communication Technology Authority — free alerts |
| **CERT-ZM** | Computer Emergency Response Team Zambia — incident reporting and alerts |

---

## Related Features
- [Digital Hygiene Assessment](01-digital-hygiene-assessment.md) — C15 Regulatory Compliance maps to DPA/ZICTA
- [Policy Templates](08-policy-templates.md) — includes a Data Protection Policy template
