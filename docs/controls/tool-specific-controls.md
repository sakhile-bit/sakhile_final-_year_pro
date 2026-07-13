# Tool-Specific Controls — `C16` … `C22`

**Source:** `src/gui/screens/manual_checks.py` (`TOOL_QUESTIONS`)
**Layer:** Business (governance around each advanced tool)

These controls appear **only when the business selects the corresponding tool**
in its profile. Each parent control (`C16`–`C22`) is assessed through 2–3
sub-questions (`a`/`b`/`c`) whose weights roll up proportionally into the
parent. They pair the technical scanners with the governance/process practices
that should surround them.

| Parent | Tool | Sub-controls | Focus |
|--------|------|--------------|-------|
| `C16` | Active Directory | `C16` AD password policy · `C16b` privileged account review · `C16c` stale account management | Are AD security practices enforced and reviewed. |
| `C17` | Network Scan | `C17` device inventory · `C17b` segmentation · `C17c` port/service exposure | Is the network mapped, segmented and minimally exposed. |
| `C18` | Infra Scan | `C18` SSL/TLS validity · `C18b` HTTP security headers · `C18c` risky port closure | Is the public web presence hardened. |
| `C19` | Zambia Risk | `C19` Zambia threat-awareness training · `C19b` regulatory compliance · `C19c` mobile money controls | Local threat and compliance governance. |
| `C20` | Remediation | `C20` findings-tracking register · `C20b` remediation SLA adherence | Are findings tracked and fixed on time. |
| `C21` | Fleet Scan | `C21` fleet asset inventory · `C21b` fleet-wide scan cadence · `C21c` weakest-node remediation | Is the whole estate inventoried and scanned regularly. |
| `C22` | Server Hardening | `C22` secure-config baseline (CIS) · `C22b` legacy service disablement · `C22c` server patch currency | Do servers follow a hardened baseline and stay patched. |

**Sub-question weights** (`_TOOL_Q_WEIGHTS`): the primary sub-question is
weighted 3, secondary ones 2–3, per `manual_checks.py`. Each sub-question maps
to its parent via `_TOOL_Q_PARENT`, so the parent control reflects the average
of its answered sub-questions.

These provide the *governance* counterpart to the automated technical families:
`C16 ↔ AD-xx`, `C18 ↔ TLS/HTTP/DNS findings`, `C22 ↔ HRD-xx`, etc.

---
**Feature docs:** [05 Network Scanner](../features/05-network-scanner.md) · [06 Infra Scanner](../features/06-infra-scanner.md) · [16 Active Directory](../features/16-active-directory-checks.md) · [19 Server Hardening](../features/19-server-hardening.md) · [20 Fleet Scanning](../features/20-fleet-scanning.md) · [controls catalogue](README.md)
