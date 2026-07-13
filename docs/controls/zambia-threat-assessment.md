# Zambia Local Threat Assessment

**Source:** `src/gui/screens/zambia_risk.py` (`CATEGORIES`)
**Layer:** Business (local threat & compliance awareness)
**Grade:** `LOW RISK` → `MEDIUM RISK` → `HIGH RISK`, based on how many items
are unchecked.

A Zambia-specific self-assessment covering the digital threats and legal
obligations most relevant to Zambian SMEs. 16 yes/no items across 4 categories;
each carries a plain-language rationale.

## 📱 Mobile Money & SIM Security

| Key | Question (summary) |
|-----|--------------------|
| `sim_swap_protection` | SIM PIN set on all company SIMs and registered for SIM-swap alerts. |
| `mobile_money_limits` | Daily transaction limits set on Airtel Money / MTN MoMo / Zamtel Kwacha. |
| `mobile_money_2fa` | Each mobile money / banking account has a unique, unshared PIN. |
| `mobile_money_policy` | Written policy for mobile money transactions (approvals, limits, authorisers). |

## 📧 Email & Phishing Protection

| Key | Question (summary) |
|-----|--------------------|
| `phishing_training` | Staff trained in the last 12 months to spot phishing / social engineering. |
| `email_mfa` | MFA enabled on all business email accounts. |
| `spf_dmarc` | SPF and DMARC DNS records configured to prevent domain spoofing. |
| `whatsapp_fraud_awareness` | Staff warned about WhatsApp impersonation ("manager" payment) scams. |

## ⚖️ Zambia Legal Compliance

| Key | Question (summary) |
|-----|--------------------|
| `dpa_registered` | Registered with the Data Protection Commission under the DPA No. 3 of 2021. |
| `dpa_policy` | Written Data Protection Policy covering collection, use and protection of data. |
| `cyber_crimes_act` | Staff aware of the Cyber Security and Cyber Crimes Act 2021 and its penalties. |
| `zicta_alerts` | Subscribed to ZICTA security alerts and CERT-ZM notifications. |

## 💼 Business Continuity

| Key | Question (summary) |
|-----|--------------------|
| `backup_offsite` | Backups stored off-site / in the cloud, not only on-premises. |
| `disaster_recovery` | Written plan for operating if all computers were destroyed or stolen. |
| `supplier_security` | Key technology suppliers verified to have their own security controls. |
| `cyber_insurance` | Cyber insurance held, or its suitability formally assessed by management. |

This assessment feeds tool-specific control `C19` (Zambia Risk) in the manual
assessment — see [tool-specific-controls.md](tool-specific-controls.md).

---
**Feature docs:** [08 Zambia Risk Assessment](../features/08-zambia-risk-assessment.md) · [controls catalogue](README.md)
