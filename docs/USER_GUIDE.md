# Zambia Digital Hygiene Certification Programme — User Guide

**Version:** 1.0  
**Date:** 2026-06-18  
**Audience:** SME business owners, IT managers, and security assessors

---

## Table of Contents

1. [What Is This Programme?](#1-what-is-this-programme)
2. [Two Ways to Use the App](#2-two-ways-to-use-the-app)
3. [Desktop App — Getting Started](#3-desktop-app--getting-started)
   - 3.1 [First Launch — Creating Your Account](#31-first-launch--creating-your-account)
   - 3.2 [Logging In](#32-logging-in)
   - 3.3 [The Welcome Dashboard](#33-the-welcome-dashboard)
4. [Running a Full Assessment (5 Steps)](#4-running-a-full-assessment-5-steps)
   - 4.1 [Step 1 — Business Information](#41-step-1--business-information)
   - 4.2 [Step 2 — Security Tools Profile](#42-step-2--security-tools-profile)
   - 4.3 [Step 3 — Automated Security Scan](#43-step-3--automated-security-scan)
   - 4.4 [Step 4 — Manual Security Questions](#44-step-4--manual-security-questions)
   - 4.5 [Step 5 — Your Results](#45-step-5--your-results)
5. [Understanding Your Score and Certificate](#5-understanding-your-score-and-certificate)
6. [Acting on Your Results](#6-acting-on-your-results)
7. [Additional Desktop Tools](#7-additional-desktop-tools)
   - 7.1 [Assessment History](#71-assessment-history)
   - 7.2 [Remediation Guidance](#72-remediation-guidance)
   - 7.3 [Infrastructure Scanner](#73-infrastructure-scanner)
   - 7.4 [Network Scanner](#74-network-scanner)
   - 7.5 [Pre-Deployment Checker](#75-pre-deployment-checker)
   - 7.6 [Zambia Risk Assessment](#76-zambia-risk-assessment)
   - 7.7 [Policy Templates](#77-policy-templates)
   - 7.8 [Active Directory Checks](#78-active-directory-checks)
   - 7.9 [Assessment Dashboard](#79-assessment-dashboard)
   - 7.10 [Export Reports](#710-export-reports)
   - 7.11 [Audit Logs](#711-audit-logs)
   - 7.12 [Settings](#712-settings)
8. [Web Portal](#8-web-portal)
   - 8.1 [Registering and Logging In](#81-registering-and-logging-in)
   - 8.2 [User Roles](#82-user-roles)
   - 8.3 [Business Owner Workflow](#83-business-owner-workflow)
   - 8.4 [Assessor Workflow](#84-assessor-workflow)
   - 8.5 [Admin Panel](#85-admin-panel)
   - 8.6 [Multi-Factor Authentication (MFA)](#86-multi-factor-authentication-mfa)
   - 8.7 [Downloading Reports and Certificates](#87-downloading-reports-and-certificates)
9. [The 15 Security Controls Explained](#9-the-15-security-controls-explained)
10. [Certification Tiers](#10-certification-tiers)
11. [Exporting Reports](#11-exporting-reports)
12. [CLI Reference (Advanced)](#12-cli-reference-advanced)
13. [Frequently Asked Questions](#13-frequently-asked-questions)
14. [Getting Help — ZICTA & CERT-ZM Contacts](#14-getting-help--zicta--cert-zm-contacts)

---

## 1. What Is This Programme?

The **Zambia Digital Hygiene Certification Programme** helps small and medium enterprises (SMEs) in Zambia measure, improve, and prove their cybersecurity posture. It:

- **Automatically checks** your Windows computer for common security weaknesses (antivirus, firewall, updates, passwords, backups).
- **Guides you through 10 interview questions** about how your business handles security.
- **Scores your business** out of 120 points across 15 international security controls.
- **Awards a certification** — GOLD, SILVER, BRONZE, or guidance to improve — valid for 6 or 12 months.
- **Tells you exactly what to fix** with plain-English instructions and one-click repair scripts.

The assessment aligns to four internationally recognised frameworks:

| Framework | Why It Matters |
|---|---|
| NIST Cybersecurity Framework v1.1 | Globally accepted US government standard |
| CIS Critical Security Controls v8 | Practical, prioritised top-18 controls |
| ISO/IEC 27001:2022 | International information security standard |
| Zambia DPA 2021 & Cyber Crimes Act 2021 | Legal requirements for Zambian businesses |

---

## 2. Two Ways to Use the App

| | Desktop App | Web Portal |
|---|---|---|
| **Best for** | Running an assessment on your own computer | Multi-user teams, remote assessors, admin oversight |
| **Access** | Installed `.exe` on Windows | Browser at your organisation's URL |
| **Works offline** | Yes | No — requires internet/network |
| **Who uses it** | Business owner, IT staff, on-site assessor | Admins, assessors, business owners |
| **Data stored** | Local SQLite database | MySQL database (server) |

This guide covers both. Start with the Desktop App (sections 3–7) if you are doing a self-assessment, then see section 8 for the Web Portal.

---

## 3. Desktop App — Getting Started

### 3.1 First Launch — Creating Your Account

The very first time you open the application you will see the **First-Time Setup** screen. You must create an administrator account before using the app. This account protects your assessment data — it stays on your computer and is never sent anywhere.

**Steps:**

1. Enter a **Username** (minimum 3 characters, e.g. your first name or initials).
2. Enter a **Password** (minimum 8 characters). The live strength meter shows you how strong your password is:

   | Meter | Label | Meaning |
   |---|---|---|
   | 1 bar (red) | Weak | Too short or simple — add length |
   | 2 bars (orange) | Fair | Acceptable but improvable |
   | 3 bars (yellow) | Good | Includes uppercase + numbers |
   | 4 bars (green) | Strong | Includes special characters (!@#$) |

3. Re-enter the same password in **Confirm Password**.
4. Click **Create Account & Continue**.

The app saves your credentials securely (the password is hashed — the plain text is never stored) and takes you straight to the Welcome Dashboard.

> **If you forget your password:** Your credentials are stored in the local database at `%APPDATA%\ZambiaDigitalHygiene\history.db`. Delete this file to reset the app to first-run mode and create a new account. Note that this also clears your assessment history.

---

### 3.2 Logging In

Every subsequent launch shows the **Login** screen.

1. Your **Username** is pre-filled (greyed out).
2. Enter your **Password**.
3. Click **Sign In**.

You have **5 attempts**. After 5 failed attempts the application closes automatically — relaunch it and try again.

---

### 3.3 The Welcome Dashboard

After logging in you arrive at the **Welcome Dashboard**. This is your home base. The left panel shows the programme overview and scoring summary. The right panel has 13 buttons — one for each major feature:

| Button | What It Does |
|---|---|
| **Start New Assessment** | Begin a 5-step cybersecurity assessment |
| **Assessment History** | Review all past assessments |
| **Infra Security Scanner** | Check your website/domain's security posture |
| **Zambia Risk Assessment** | Zambia-specific threats and DPA compliance |
| **Policy Templates** | Download 6 ready-to-use security policy documents |
| **Network Scanner** | Discover all devices on your local network |
| **Pre-Deployment Checker** | 15-point gate before going live with new software |
| **Remediation Guidance** | Step-by-step fix instructions for each control |
| **Active Directory Checks** | AD password policies, stale and privileged accounts |
| **Export Reports** | Bulk export past assessments as PDF/CSV/JSON |
| **Audit Logs** | See a log of all activity inside the app |
| **Settings** | Configure preferences and database options |
| **Assessment Dashboard** | Charts and trends across all your assessments |

---

## 4. Running a Full Assessment (5 Steps)

Click **Start New Assessment** from the Welcome Dashboard. The assessment takes approximately **15–25 minutes** to complete. You will move through 5 screens in order.

The progress indicator at the top of every screen shows your position: `● ● ○ ○ ○` (filled dots = completed steps).

---

### 4.1 Step 1 — Business Information

Enter the details about the business being assessed.

| Field | Required | Notes |
|---|---|---|
| Business Name | Yes | The legal trading name |
| Business Registration ID | Yes | PACRA registration number |
| Industry | No | Dropdown — select the closest match |
| Province | No | Dropdown — where the business operates |
| Contact Person | No | Name of primary IT/security contact |
| Contact Email | No | Must be a valid email address if entered |
| Contact Phone | No | Phone number with country code |
| Number of Employees | No | Whole number |
| Address | No | Street address |

Click **Next** when done. You cannot proceed without a Business Name and Registration ID.

---

### 4.2 Step 2 — Security Tools Profile

This optional step asks whether your business uses any advanced security tools or infrastructure. Each tool you select **adds extra scored controls** (C16–C20) to the assessment, raising the maximum possible score.

You do **not** need to select any of these — the standard 15-control, 120-point assessment is complete on its own.

| Toggle | Adds Control | What It Assesses | Extra Points |
|---|---|---|---|
| Active Directory | C16 | AD password policies, privileged accounts, stale accounts | +8 pts |
| Network Scanning | C17 | Network device inventory, segmentation, port exposure | +7 pts |
| Infrastructure Security | C18 | SSL/TLS certificates, HTTP security headers, risky ports | +7 pts |
| Zambia Local Threats | C19 | SIM swap controls, mobile money security, DPA training | +8 pts |
| Remediation Process | C20 | Findings register, SLA adherence, evidence collection | +6 pts |

**How to decide:** Select a tool only if it genuinely applies to your business. Selecting it and answering "No" to every sub-question will lower your score. When in doubt, leave it unselected.

Click **Next** to continue. Click **Back** to return to Business Information.

---

### 4.3 Step 3 — Automated Security Scan

The app now automatically inspects your computer. You do not need to do anything — watch the live checklist update as each check completes.

**What is being checked:**

| Control | What the App Looks For | Possible Outcome |
|---|---|---|
| **C01 — OS Updates** | Is Windows Update running? How old is the last patch? | ✔ Up to date / ⚠ Overdue / ✖ Disabled |
| **C02 — Antivirus** | Is Windows Defender or another AV active with current definitions? | ✔ Active & current / ⚠ Definitions old / ✖ Disabled |
| **C03 — Firewall** | Is the firewall on for all 3 network profiles (Domain, Private, Public)? | ✔ All on / ⚠ Partial / ✖ Off |
| **C04 — Password Policy** | Local policy: min 8 chars, expiry ≤90 days, lockout ≤5 attempts | ✔ Compliant / ⚠ Weak policy / ✖ No policy |
| **C05 — Backups** | Backup software installed, VSS shadows present, cloud sync detected | ✔ Covered / ⚠ Partial / ✖ None found |

**Status icons:**

| Icon | Meaning |
|---|---|
| ✔ (green) | PASS — control fully met |
| ⚠ (amber) | WARNING — partially met, improvement needed |
| ✖ (red) | FAIL — control not met |

**One-click fixes:** If a check fails, a **Fix** button appears next to it. Clicking it opens a script that attempts to automatically resolve the issue (e.g. enable Windows Update, turn on the firewall). These scripts require administrator privileges — Windows will ask you to confirm.

**Extended checks (bonus, not scored):** Below the 5 main checks you will see 5 additional checks (ransomware protection, local account audit, USB AutoRun, Windows Hello, pending updates count). These are informational only and do not affect your score.

Click **Next** when scanning is complete, or **Skip** to jump straight to Results (controls C06–C15 will be marked NOT ASSESSED).

---

### 4.4 Step 4 — Manual Security Questions

You are now asked 10 questions about how your business operates. These cover the areas that cannot be checked automatically (training, policies, physical security, etc.).

**How to answer:** Each question has three buttons:

| Button | Meaning | Score Awarded |
|---|---|---|
| **Yes — Fully** | Your business fully meets this requirement | 100% of the control's weight |
| **Partially** | You have something in place but it is incomplete | 50% of the control's weight |
| **No** | This is not in place | 0 points |

Answer honestly — the assessment is most useful when it reflects your real situation.

**The 10 questions:**

| # | Control | Business-Friendly Question |
|---|---|---|
| 1 | **C06 — Security Training** | Do ALL staff receive annual cybersecurity awareness training and phishing simulations? |
| 2 | **C07 — Access Control** | Is there a documented least-privilege access policy that is reviewed annually? |
| 3 | **C08 — Incident Response** | Do you have a tested incident response plan with ZICTA/CERT-ZM contact numbers? |
| 4 | **C09 — Encryption** | Is sensitive data encrypted at rest (BitLocker) and in transit (HTTPS)? |
| 5 | **C10 — Mobile Security** | Are all business phones protected with screen locks, encryption, and mobile management? |
| 6 | **C11 — Physical Security** | Is your server/IT area access-controlled with visitor logs and CCTV? |
| 7 | **C12 — Network Security** | Does your business use WPA2/WPA3 Wi-Fi with a separate guest network? |
| 8 | **C13 — Acceptable Use** | Is there a documented acceptable use policy signed by all staff? |
| 9 | **C14 — Vendor Risk** | Do supplier contracts include security clauses and formal risk assessments? |
| 10 | **C15 — Compliance** | Is your business compliant with the Zambia Data Protection Act 2021 and ZICTA regulations? |

**If you selected tool controls in Step 2**, additional sections appear below the core 10 questions, one section per selected tool. Answer them the same way (Yes / Partially / No). The live score display at the top updates as you answer.

Click **Next** when all questions are answered.

---

### 4.5 Step 5 — Your Results

Your results screen shows everything about this assessment at a glance.

**Top card:**
- Your **certification tier badge** (GOLD / SILVER / BRONZE / NOT CERTIFIED) with a colour-coded stripe.
- Your **score** — e.g. "95 / 120 points · 79%"
- A **ring chart** showing your percentage visually.
- A **summary row**: controls passed (green), controls needing attention (amber), controls failed (red).

**Control breakdown table:** Scroll down to see every control with its score, weight, and status. Controls are split into two sections:

1. **Core Controls (C01–C15)** — always present.
2. **Advanced Tool Assessments (C16–C20)** — shown only if you selected tools in Step 2.

**Recommendations panel:** Below the table you will find a prioritised action list. Each recommendation shows:
- The control it relates to.
- A plain-English description of what to do.
- An effort badge: ⚡ Quick Fix / 📅 This Week / 📆 This Month / 🔁 Ongoing.

**Export buttons:** At the bottom of the results screen you can download your results in four formats:
- **PDF** — a branded report suitable for printing or sharing with a bank/auditor.
- **HTML** — an interactive report that opens in a web browser.
- **JSON** — raw data for technical staff or integration into other systems.
- **CSV** — a spreadsheet-compatible table of all controls and scores.

Your results are also automatically saved to the local database and will appear in Assessment History.

---

## 5. Understanding Your Score and Certificate

### Scoring

Your score is the sum of points awarded across all controls. Each control has a **weight** (maximum points). For example:

- C02 Antivirus has a weight of **15** — the most important single control.
- C11 Physical Security has a weight of **5**.

A "PASS" scores 100% of the weight. A "WARNING" scores 50–75%. A "FAIL" scores 0–25%.

**Maximum scores:**

| Scenario | Max Points |
|---|---|
| 15 core controls only | 120 |
| All 5 tool controls selected | 156 |

### Certification Tiers

| Tier | Score % Required | Critical Failures Allowed | Certificate Valid For |
|---|---|---|---|
| 🥇 **GOLD** | ≥ 80% | 0 | 12 months |
| 🥈 **SILVER** | ≥ 60% | ≤ 1 | 12 months |
| 🥉 **BRONZE** | ≥ 40% | ≤ 2 | 6 months |
| ✕ **NOT CERTIFIED** | < 40% | Any | — |

**Critical failures** are automatic failures on the 5 highest-weight automated controls (OS Updates, Antivirus, Firewall, Password Policy, Backups). Even a high total score cannot achieve GOLD if any of these five fail completely.

### Certificate Number

Certificates are issued with a unique reference number in the format `ZDH-YYYY-XXXXXX` (e.g. `ZDH-2026-001234`). You can share this number with customers, partners, or regulators as proof of your certification.

---

## 6. Acting on Your Results

### Priority order

1. Fix any **red (FAIL)** controls first — these cost the most points and block certification.
2. Then address **amber (WARNING)** controls to move from BRONZE to SILVER or GOLD.
3. Finally, work through the recommendations panel in order of the effort badges.

### Using the Remediation Guidance tool

From the Welcome Dashboard, click **Remediation Guidance**. Select any failed or warning control from the tree on the left. You will see:

- **Plain English Fix** — step-by-step instructions any staff member can follow (e.g. "Go to Settings → Windows Update → turn on 'Automatic Updates'").
- **PowerShell Script** — a one-click script for IT staff. Click **Copy** to copy to clipboard, or **Run** to execute immediately (requires administrator privileges).
- **Effort estimate** — how long the fix typically takes.
- **Suggested owner** — who in your business should be responsible.

### Re-running the assessment

After making improvements, return to the Welcome Dashboard and click **Start New Assessment**. Run the same business through the assessment again. Your history screen will show both results side by side so you can see your improvement.

---

## 7. Additional Desktop Tools

### 7.1 Assessment History

Click **Assessment History** from the Welcome Dashboard to see all past assessments.

- Each entry shows: business name, assessment date, certification tier badge, and score.
- Use the **search bar** to find a specific business by name or registration ID.
- Use the **filter** buttons to show only a specific tier (GOLD, SILVER, etc.).
- Click **View** on any entry to reopen the full results screen.
- Click **Compare** on two entries to see them side by side.

---

### 7.2 Remediation Guidance

Step-by-step fixes for every control. See section 6 above for full details.

---

### 7.3 Infrastructure Scanner

Use this tool to check the security of any domain or website your business owns or relies on.

**How to use:**
1. Click **Infra Security Scanner** from the Welcome Dashboard.
2. Enter a domain name in the input field (e.g. `example.co.zm`).
3. Click **Scan**.

**What it checks:**

| Check | What It Means | What a Good Result Looks Like |
|---|---|---|
| DNS Resolution | Can the domain be found on the internet? | "Resolves to 203.0.113.1" |
| SPF Record | Is email spoofing protection configured? | "SPF record found" |
| DMARC Record | Is email authentication policy set? | "DMARC record found" |
| SSL/TLS Certificate | Is the website's security certificate valid and not about to expire? | "Valid, expires in 287 days" |
| TLS Version | Is the website using modern, secure encryption? | "Only TLS 1.2+ accepted" |
| HTTPS Redirect | Does `http://` automatically redirect to `https://`? | "Redirects to HTTPS" |
| Security Headers | Are browser security protections configured? | "HSTS: Present, CSP: Present, X-Frame-Options: Present" |
| Open Ports | Which network ports are publicly accessible? | "80, 443 open" |
| Risky Ports | Are dangerous ports (Telnet, FTP, RDP, MySQL) exposed to the internet? | "No risky ports open" |

Results can be downloaded as PDF, JSON, or CSV.

---

### 7.4 Network Scanner

Discover all devices connected to your office network and identify anything suspicious.

**How to use:**
1. Click **Network Scanner** from the Welcome Dashboard.
2. Enter your network range (e.g. `192.168.1.0/24`) or click **Auto-detect**.
3. Click **Scan**.

**Results:**
- A table of every discovered device showing IP address, MAC address, device name, manufacturer, and status.
- Click any device to see its open ports.
- The **Topology Map** panel shows a visual layout of all devices on the network.

**What to look for:**
- Devices you do not recognise (potential intruders or unauthorised equipment).
- Devices with risky ports open (e.g. RDP/3389 should never be open on a business PC).
- Devices that are "Online" outside business hours.

Results can be exported as CSV or PDF.

---

### 7.5 Pre-Deployment Checker

Run this before launching any new website, application, or system. It performs 15 automated checks and gives a clear READY / NOT READY verdict.

**How to use:**
1. Click **Pre-Deployment Checker** from the Welcome Dashboard.
2. The checker runs automatically — no input needed.
3. Review the checklist. Each item shows: PASS / WARNING / FAIL / ERROR, the severity, the finding, and a remediation step.

**Overall verdict:**
- 🟢 **READY** — all critical checks passed. Safe to go live.
- 🔴 **NOT READY** — one or more critical checks failed. Resolve these before going live.

The report can be downloaded as PDF or JSON.

---

### 7.6 Zambia Risk Assessment

A specialised checklist focused on threats specific to Zambia: SIM swap fraud, mobile money scams, and compliance with local laws.

**How to use:**
1. Click **Zambia Risk Assessment** from the Welcome Dashboard.
2. Work through the 12 checklist items — tick each one your business has addressed.
3. Click **Calculate Risk**.

**Checklist items include:**
- SIM swap fraud mitigation (SIM PIN enabled on business SIM cards).
- Mobile money account controls (daily transaction limits, no shared PINs).
- Staff trained on WhatsApp fraud and phishing.
- Compliance with the **Data Protection Act 2021**.
- Compliance with the **Cyber Security & Cyber Crimes Act 2021**.

**Risk levels:**

| Score | Level | Action |
|---|---|---|
| ≥ 80% | 🟢 LOW RISK | Good posture — maintain and review annually |
| 50–79% | 🟡 MEDIUM RISK | Address remaining items within 3 months |
| < 50% | 🔴 HIGH RISK | Immediate action required |

---

### 7.7 Policy Templates

Six ready-to-use policy documents your business can download, customise with your company name, and distribute to staff.

**Available policies:**

| # | Policy | Who Should Sign It |
|---|---|---|
| 1 | **Security Awareness Training Policy** | Management, HR |
| 2 | **Acceptable Use Policy** | All staff |
| 3 | **Incident Response Plan** | IT Manager, Management |
| 4 | **Access Control Policy** | IT Manager, HR |
| 5 | **Mobile Device Security Policy** | All staff with business phones |
| 6 | **Vendor Risk Management Policy** | Procurement, Management |

**How to use:**
1. Click **Policy Templates** from the Welcome Dashboard.
2. Click **Download & Customize** on any policy to download it (Word + PDF).
3. Open the Word file and replace all `[COMPANY NAME]` and `[CONTACT]` placeholders with your details.
4. Print and have relevant staff sign.

All policies reference Zambia-specific laws (DPA 2021, ZICTA regulations) and include local contact information for ZICTA and CERT-ZM.

> **Tip:** Implementing all 6 policies and having staff sign them will directly improve your scores for C06, C07, C08, C10, C13, and C14.

---

### 7.8 Active Directory Checks

For businesses that use Microsoft Active Directory (AD) to manage staff accounts.

**How to use:**
1. Click **Active Directory Checks** from the Welcome Dashboard.
2. Enter your **Domain Name** (e.g. `mybusiness.local`).
3. Enter an **Administrator username and password** (read-only access is sufficient).
4. Click **Connect**.

**What it checks:**

| Check | Why It Matters |
|---|---|
| Password Policy | Min 12 chars, 90-day expiry, lockout after 5 failures |
| Privileged Accounts | Who has Domain Admin rights? Are they the right people? |
| Stale Accounts | Ex-staff accounts still active (a significant security risk) |
| Password Age | Accounts with passwords that have never changed |
| MFA Status | How many accounts have multi-factor authentication enabled |

Results can be exported as CSV for your audit records.

---

### 7.9 Assessment Dashboard

A statistics overview of all assessments you have run.

**Charts shown:**
- **Certification tier breakdown** (pie chart: how many GOLD, SILVER, BRONZE, NOT CERTIFIED).
- **Score trend** (line chart: how scores have changed over the last 12 months).
- **Control performance** (bar chart: which controls consistently fail across assessments).

**Use this to:**
- Track improvement over time.
- Identify which controls are most commonly failed by the businesses you assess.
- Present programme impact data to management or funders.

---

### 7.10 Export Reports

Bulk export multiple past assessments at once.

**How to use:**
1. Click **Export Reports** from the Welcome Dashboard.
2. Use the checkboxes to select the assessments you want to export (or click **Select All**).
3. Choose a format from the dropdown (PDF / HTML / JSON / CSV).
4. Click **Export**.

The app creates a ZIP file containing all selected reports. The file is saved to your Downloads folder (or a location you choose).

---

### 7.11 Audit Logs

A chronological record of everything that has happened inside the app: logins, assessments, exports, settings changes, and more.

**Columns:** Timestamp / User / Action / Details

You can:
- Filter by date range.
- Export the full log as CSV for compliance records.

---

### 7.12 Settings

Access from the Welcome Dashboard → **Settings**.

**General tab:**
- **Theme** — Dark or Light mode.
- **Reassessment reminder** — toggle to be reminded when a certificate is approaching expiry.
- **Auto-save results** — automatically save results to the database after each assessment.

**Database tab:**
- **Database location** — shows where your data is stored.
- **Export database** — create a backup copy of your entire assessment history.
- **Clear old assessments** — delete assessments older than a date you choose (permanent).

**Export tab:**
- **Default format** — choose which format to default to when downloading reports.
- **Default location** — where downloaded reports are saved.

---

## 8. Web Portal

The Web Portal provides a multi-user, multi-business platform accessible from any browser. It is suitable for organisations where assessors visit different businesses and need to record results centrally, or where an administrator oversees multiple assessments.

### 8.1 Registering and Logging In

**Register:**
1. Navigate to the portal URL provided by your administrator.
2. Click **Register**.
3. Fill in: Username, Email, Password (minimum 12 characters), Confirm Password, and Role.
4. Click **Submit**. Your account is created immediately.

**Log in:**
1. Enter your **Username** and **Password**.
2. If MFA is enabled on your account, you will be prompted for a 6-digit code from your authenticator app.
3. Click **Sign In**.

**Rate limiting:** 5 failed login attempts within 5 minutes will temporarily lock your account.

---

### 8.2 User Roles

| Role | What They Can Do |
|---|---|
| **Admin** | Full access: manage all users, businesses, assessments, certificates, audit logs, and system settings |
| **Assessor** | Run assessments, view and download their own assessment reports, accept assessment requests, manage remediation tasks |
| **Business Owner** | View their own business's assessments and certificates, request new assessments, download their reports |

---

### 8.3 Business Owner Workflow

**1. Register your business:**
- After logging in, go to **My Business** from the dashboard menu.
- Fill in your business name, registration number, industry, province, and contact details.
- Click **Save Business**.

**2. Request an assessment:**
- From **My Business**, click **Request Assessment**.
- Select the assessment type (Automated or Full) and a preferred date.
- Add any notes for the assessor (e.g. "Please arrive at 9am, ask for John").
- Click **Submit Request**. An assessor will be assigned and will contact you.

**3. View your results:**
- Once an assessor has completed your assessment, it appears in the **My Business** page under Past Assessments.
- Click **View** to see the full results, including your tier badge, scores, and recommendations.
- Click **Download** to save your report as PDF, HTML, JSON, or CSV.

**4. Download your certificate:**
- If you achieved GOLD, SILVER, or BRONZE, a certificate row appears under **Active Certificates**.
- Click **Download Certificate** to get a printable PDF certificate with your certificate number and expiry date.

---

### 8.4 Assessor Workflow

**1. Accept an assessment request:**
- From your dashboard, click **Assessment Requests**.
- Find a pending request and click **Accept**. The request is now assigned to you and moves to "In Progress".

**2. Run the assessment:**
- Go to the business's premises.
- Open the Desktop App on the business's computer and complete the 5-step assessment (sections 4.1–4.5).
- Or, use the Web Portal's **New Assessment** form (`/assess`) to enter results directly.

**3. Submit results:**
- If using the Web Portal form, complete all sections and click **Submit Assessment**.
- Results are saved automatically to the database.

**4. Track remediation:**
- From the results page, click **Add Remediation** to create remediation tasks for failed controls.
- Assign tasks to the business owner or their IT staff.
- Monitor progress from the **Remediations** page.

---

### 8.5 Admin Panel

Accessible from the top navigation bar (Admin only). Sections:

**Users:**
- View all registered users (table: name, email, role, active, MFA, registered date).
- Click **Edit** to change a user's role or reset their password.
- Click **Disable** to prevent a user from logging in (does not delete their data).

**Businesses:**
- View all registered businesses.
- Add a business manually (for cases where the business owner cannot register themselves).
- Click any business to see all their assessments.
- Delete a business and all its data (permanent — requires confirmation).

**Certificates:**
- View all issued certificates across all businesses.
- Issue a certificate manually for a specific assessment.
- Click **Revoke** to invalidate a certificate before its expiry date.

**Audit Logs:**
- Full chronological log of every action by every user.
- Filterable by user, action type, and date range.
- Export as CSV or PDF.

**Settings:**
- Database backup.
- Session timeout length.
- Password policy (minimum length, complexity requirements, expiry in days).
- SIEM forwarder webhook URL (for organisations forwarding audit logs to a security monitoring platform).

---

### 8.6 Multi-Factor Authentication (MFA)

MFA adds a second layer of security to your web portal login. After entering your password, you must also enter a 6-digit code from an authenticator app on your phone.

**Enabling MFA:**
1. Click your username in the top navigation bar → **Profile**.
2. Under **Multi-Factor Authentication**, click **Enable MFA**.
3. A QR code appears on screen.
4. Open your authenticator app (Google Authenticator, Microsoft Authenticator, or Authy) and scan the QR code.
5. Enter the 6-digit code shown in your app to confirm it is working.
6. Click **Confirm & Enable**.

MFA is now active. Every login will require a code from your app.

**Disabling MFA:**
1. Go to **Profile** → **Multi-Factor Authentication** → **Disable MFA**.
2. Confirm with your password.

---

### 8.7 Downloading Reports and Certificates

From any assessment results page (web portal):

| Format | Best For | Button |
|---|---|---|
| **PDF** | Sharing with auditors, banks, regulators, printing | Download PDF |
| **HTML** | Browsing interactively, archiving on a website | Download HTML |
| **JSON** | Developers, API integration, automated processing | Download JSON |
| **CSV** | Spreadsheet analysis, importing to Excel | Download CSV |

To bulk-export multiple assessments: go to **Export Data** in the navigation menu, select a format, and click **Export**. A ZIP file is downloaded containing all your assessments.

---

## 9. The 15 Security Controls Explained

The following table explains each control in plain English so you know what you are being assessed on.

### Technical Controls (Automated)

| Control | Name | Weight | What It Checks |
|---|---|---|---|
| **C01** | OS Updates | 10 pts | Is Windows fully patched? Critical patches should be applied within 30 days of release. |
| **C02** | Antivirus | 15 pts | Is an antivirus program running with up-to-date virus definitions? This is the single highest-weighted control. |
| **C03** | Firewall | 10 pts | Is the Windows Firewall switched on for all network types? A firewall is your first line of network defence. |
| **C04** | Password Policy | 10 pts | Does Windows enforce strong passwords? Min 8 characters, maximum 90-day expiry, locks after 5 wrong attempts. |
| **C05** | Backups | 10 pts | Are your files backed up? The app looks for backup software, cloud sync (OneDrive/Google Drive), or shadow copies. |

### Administrative Controls (Manual Questions)

| Control | Name | Weight | What You Are Asked |
|---|---|---|---|
| **C06** | Security Training | 8 pts | Do all staff receive annual cybersecurity awareness training and phishing simulations? |
| **C07** | Access Control | 7 pts | Is there a written policy controlling who can access what, reviewed annually? |
| **C08** | Incident Response | 7 pts | Do you have a written, tested plan for responding to a cyberattack? Does it include ZICTA/CERT-ZM contacts? |
| **C09** | Encryption | 7 pts | Is sensitive data encrypted on devices (BitLocker) and protected in transit (HTTPS websites)? |
| **C10** | Mobile Security | 5 pts | Are all business phones secured with screen locks, remote wipe, and approved apps only? |
| **C11** | Physical Security | 5 pts | Is your server or networking equipment in a locked room with visitor logs? |
| **C12** | Network Security | 5 pts | Do you use strong Wi-Fi encryption (WPA2/WPA3) with a separate network for guests? |
| **C13** | Acceptable Use | 5 pts | Do staff have written rules about using company computers and data? |
| **C14** | Vendor Risk | 8 pts | Do IT supplier contracts include security obligations? Have you assessed their security risks? |
| **C15** | Compliance | 8 pts | Does your business comply with the Zambia Data Protection Act 2021 and the Cyber Security & Cyber Crimes Act 2021? |

### Optional Tool Controls

| Control | Name | Weight | When to Include |
|---|---|---|---|
| **C16** | Active Directory Security | 8 pts | If you use Microsoft Active Directory |
| **C17** | Network Assessment | 7 pts | If you conduct regular network security reviews |
| **C18** | Infrastructure Security | 7 pts | If you operate public-facing websites or web services |
| **C19** | Zambia Local Threats | 8 pts | All Zambian businesses — covers SIM swap, mobile money, DPA |
| **C20** | Remediation Process | 6 pts | If you formally track and close security findings |

---

## 10. Certification Tiers

### GOLD — ≥ 80%, zero critical failures

Your business demonstrates excellent cybersecurity hygiene. You have all five automated controls passing, strong policies in place, and no critical gaps. This certification signals to customers, partners, and regulators that you take security seriously. Certificate valid for **12 months**.

### SILVER — ≥ 60%, at most 1 critical failure

Your business has strong foundations with minor gaps remaining. One critical automated control may be partially failing but everything else is in good shape. Focus on the amber controls to reach GOLD at your next assessment. Certificate valid for **12 months**.

### BRONZE — ≥ 40%, at most 2 critical failures

Your business has basic cybersecurity controls in place. There are clear improvement areas — particularly in policies, training, and one or two automated controls. Use the Remediation Guidance tool to close the gaps. Certificate valid for **6 months** — a follow-up assessment is recommended sooner.

### NOT CERTIFIED — below 40% or 3+ critical failures

Your business has significant cybersecurity gaps that pose real risk. This is not a penalty — it is a clear signal of where to focus. Start with the automated controls (C01–C05) as they are the quickest to fix using the one-click fix buttons. Then work through the Remediation Guidance for administrative controls. A re-assessment after 1–3 months of improvements typically achieves at least BRONZE.

---

## 11. Exporting Reports

Reports can be downloaded from the Results screen (desktop or web) in four formats:

### PDF Report

The PDF is a branded, print-ready document containing:
- Cover page with your certification tier badge and score.
- Business details and assessment date.
- Executive summary.
- Full control breakdown table.
- Prioritised recommendations.
- Framework alignment (NIST / CIS / ISO 27001 / DPA 2021).
- ZICTA and CERT-ZM contact information.

**Use the PDF** when sharing results with banks, auditors, customers, or regulators, and when printing for your physical records.

### HTML Report

An interactive file that opens in any web browser. Useful for:
- Archiving on your company intranet.
- Browsing the full report interactively.
- Printing from a browser with custom margins.

### JSON Report

A machine-readable file containing every data point from the assessment. Use this if:
- You have a developer integrating your results into another system.
- You want to import results into a spreadsheet tool using a JSON importer.
- You want to store raw data for compliance records.

### CSV Report

A spreadsheet table with one row per control. Columns include: Control ID, Name, Score, Weight, Status, Details, Category, Verification Type, and Evidence. Open directly in Microsoft Excel or Google Sheets.

---

## 12. CLI Reference (Advanced)

The CLI is intended for IT staff and developers who prefer working from the terminal.

Open a Command Prompt or PowerShell window in the project directory and run:

```
python cli.py --help
```

### Available commands

| Command | What It Does |
|---|---|
| `python cli.py assess` | Run a full 15-control assessment with prompted business details |
| `python cli.py scan` | Quick automated system security scan (C01–C05 only) |
| `python cli.py zambia` | Interactive Zambia-specific risk assessment |
| `python cli.py predeploy` | Run the 15-check pre-deployment gate |
| `python cli.py web` | Start the Flask web portal server |
| `python cli.py init-db` | Create all database tables and default admin user |
| `python cli.py users list` | List all registered web portal users |
| `python cli.py users create` | Create a new web portal user |
| `python cli.py users reset-password` | Reset a user's web portal password |
| `python cli.py manual` | Generate an on-site assessment guide as PDF |
| `python cli.py status` | Show project and environment status |

**Examples:**

```bash
# Run a full assessment from the terminal
python cli.py assess --business-name "Acme Ltd" --business-id "REG-001"

# Start the web portal on port 8080
python cli.py web --host 0.0.0.0 --port 8080

# Create a new assessor user
python cli.py users create --username john --password Secure@123 --role assessor
```

---

## 13. Frequently Asked Questions

**Q: How long does an assessment take?**  
A: The automated scan (Step 3) takes 30–90 seconds. Answering the 10 manual questions (Step 4) takes 10–20 minutes if the business owner is prepared. Allow 15–25 minutes in total.

**Q: Can I pause the assessment and come back to it?**  
A: Not mid-assessment. Complete all 5 steps in one session. Your past completed assessments are always available in Assessment History.

**Q: Can I run the assessment on multiple computers in one business?**  
A: The automated scan checks the specific computer you are running the app on. For a multi-computer business, run the assessment on the primary or most business-critical machine, and use the Manual Questions to capture organisation-wide policies.

**Q: The automated scan gave a WARNING for antivirus — is that bad?**  
A: A WARNING means the control is partially met. Common reasons: antivirus is active but definitions are more than 3 days old, or real-time protection is on but the last scan was more than 7 days ago. Click the **Fix** button or update your antivirus definitions manually to move to a PASS.

**Q: What is a "critical failure" and why does it block certification?**  
A: Critical failures occur on the 5 highest-weight controls (C01–C05). These cover the most fundamental technical protections. A business with, say, antivirus disabled is considered high-risk regardless of what score the other controls achieve. Fixing these 5 controls is always the first priority.

**Q: My certificate says it expires in 6 months. Can I re-assess sooner?**  
A: Yes. You can run a new assessment at any time. If you improve your score above the GOLD threshold before your BRONZE certificate expires, a new certificate is issued with the updated tier and a fresh 12-month validity.

**Q: Can I share my certificate with customers?**  
A: Yes. The certificate PDF is designed for sharing. It includes a unique certificate number (`ZDH-YYYY-XXXXXX`) that can be verified. You can display the certificate on your website, include it in tender documents, or share it with any stakeholder.

**Q: I got NOT CERTIFIED. What should I do first?**  
A: Open the **Remediation Guidance** tool and go straight to C01–C05 (the automated controls). These are fixable in under an hour using the one-click fix buttons. Once those are passing, re-run the assessment — you are likely to reach BRONZE. Then work on the manual controls (C06–C15) to aim for SILVER.

**Q: Is my data sent to the internet?**  
A: The Desktop App stores all data locally on your computer (`%APPDATA%\ZambiaDigitalHygiene\history.db`). No assessment data is transmitted externally. The Infrastructure Scanner and Network Scanner make outbound connections to the targets you specify, but no results leave your computer.

**Q: How do I update the app?**  
A: Download the latest `.exe` from the official source and replace the existing file. Your local database and assessment history are not affected by updates.

---

## 14. Getting Help — ZICTA & CERT-ZM Contacts

For cybersecurity incidents or regulatory guidance, contact these Zambian authorities:

**ZICTA — Zambia Information and Communications Technology Authority**  
- Website: [www.zicta.zm](https://www.zicta.zm)  
- Role: Regulator for ICT and cyber security in Zambia. Report cyber crimes, seek regulatory guidance, register as a data controller under the DPA 2021.

**CERT-ZM — Zambia Computer Emergency Response Team**  
- Website: [www.cert.zicta.zm](https://cert.zicta.zm)  
- Role: National incident response team. Contact for active cyber incidents, ransomware, data breaches, and coordinated attacks.

**Reporting obligations under the Cyber Security & Cyber Crimes Act 2021:**  
Businesses must report significant cybersecurity incidents to ZICTA within a reasonable time. The **Incident Response Plan** policy template (see section 7.7) includes the correct notification steps.

**Data Protection Act 2021:**  
If your business collects, stores, or processes personal data about Zambian residents, you are required to register as a data controller with the Office of the Data Protection Commissioner. Contact ZICTA for registration guidance.

---

*End of User Guide.*
