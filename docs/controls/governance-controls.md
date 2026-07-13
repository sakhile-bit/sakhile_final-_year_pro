# Governance / Manual Controls — `C06` … `C15`

**Source:** `src/gui/screens/manual_checks.py` (`MANUAL_CONTROLS`)
**Layer:** Business (policy, people, process)

These are **self-assessed** governance controls answered by the business during
the manual assessment. Each is answered `Yes – Fully` (1.0), `Partially` (0.5)
or `No` (0.0), and carries a weight used in the overall score. They are framed
for a Zambian SME audience, with plain-language hints and local references
(ZICTA / CERT-ZM, Data Protection Act 2021).

| ID | Control | Weight | Question (summary) |
|----|---------|--------|--------------------|
| `C06` | Security Awareness Training | 8 | All staff get ≥ annual cybersecurity awareness training and phishing simulations. |
| `C07` | Access Control Policy | 7 | Documented least-privilege access policy, reviewed at least annually. |
| `C08` | Incident Response Plan | 7 | A tested IR plan that includes ZICTA / CERT-ZM contacts. |
| `C09` | Data Encryption | 7 | Sensitive data encrypted at rest (BitLocker) and in transit (HTTPS). |
| `C10` | Mobile Device Security | 5 | Business mobiles protected with screen locks, encryption and MDM policy. |
| `C11` | Physical Security | 5 | Server / IT area access-controlled with visitor logs and CCTV. |
| `C12` | Network Security | 5 | WPA2/WPA3 Wi-Fi with a separate guest network. |
| `C13` | Acceptable Use Policy | 5 | Documented acceptable-use policy signed by all staff. |
| `C14` | Vendor / Third-Party Risk | 8 | Vendor contracts include security clauses and formal risk assessments. |
| `C15` | Regulatory Compliance | 8 | Compliant with Zambia's Data Protection Act and ZICTA regulations. |

**Answer scoring:** `Yes – Fully` = 1.0, `Partially` = 0.5, `No` = 0.0.
Weighted total (`_WEIGHTS`) = **65 points** across `C06`–`C15`.

Each question includes an evidence-capture option so assessors can attach
supporting files.

---
**Feature docs:** [01 Digital Hygiene Assessment](../features/01-digital-hygiene-assessment.md) · [03 Results & Certification](../features/03-results-certification.md) · [controls catalogue](README.md)
