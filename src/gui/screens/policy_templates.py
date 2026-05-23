"""Policy Template Library — downloadable security policy templates for Zambian SMBs."""

import customtkinter as ctk
from tkinter import filedialog
from src.gui.theme import (
    CLR_BG, CLR_SURFACE, CLR_SURFACE_ALT, CLR_ACCENT, CLR_TEXT, CLR_MUTED,
    CLR_BORDER, CLR_SUCCESS,
    FONT_HEADING, FONT_BODY, FONT_SMALL, PAD,
)

# ─────────────────────────────────────────────────────────────────────────────
# Built-in policy templates (Zambia-contextualised)
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "id": "aup",
        "icon": "📋",
        "title": "Acceptable Use Policy (AUP)",
        "description": "Rules governing how staff may use company computers, internet, and devices.",
        "framework": "CIS Control 14 · ISO 27001 A.8",
        "content": """\
ACCEPTABLE USE POLICY
=====================
[BUSINESS NAME]
Effective Date: [DATE]
Version: 1.0
Approved by: [MANAGEMENT NAME / TITLE]

1. PURPOSE
   This policy defines acceptable use of [BUSINESS NAME]'s information technology
   resources to protect the organisation, its employees, partners, and customers.

2. SCOPE
   This policy applies to ALL employees, contractors, and third parties who access
   [BUSINESS NAME]'s IT systems, networks, or data.

3. ACCEPTABLE USE
   3.1 IT resources shall be used primarily for legitimate business purposes.
   3.2 Limited personal use is permitted provided it does not interfere with work
       or consume excessive bandwidth.
   3.3 Users must keep passwords confidential and not share them with others.
   3.4 Users must lock their computer screen when leaving their workstation.

4. PROHIBITED ACTIVITIES
   The following are strictly prohibited:
   4.1 Accessing, downloading, or distributing illegal, offensive, or inappropriate content.
   4.2 Installing unlicensed software on company devices.
   4.3 Sharing company data or credentials with unauthorised persons.
   4.4 Using company email for personal business or chain letters.
   4.5 Attempting to bypass security controls or access unauthorised systems.
   4.6 Using company systems for cryptocurrency mining or personal financial gain.
   4.7 Connecting personal USB drives or unapproved devices without IT approval.

5. MOBILE DEVICES
   5.1 All company mobile devices must have a PIN/password lock.
   5.2 Employees must report lost or stolen devices to management immediately.
   5.3 Only apps from official app stores (Google Play / Apple App Store) may be installed.

6. SOCIAL MEDIA
   6.1 Employees must not post confidential company information on social media.
   6.2 Personal social media should not be accessed on company devices during work hours.

7. DATA PROTECTION
   7.1 Customer data must be handled in accordance with the Zambia Data Protection
       Act No. 3 of 2021.
   7.2 Sensitive data must not be stored on personal devices or unapproved cloud services.

8. INCIDENT REPORTING
   All suspected security incidents, policy breaches, or suspicious activity must be
   reported immediately to [IT CONTACT NAME] at [CONTACT EMAIL / PHONE].
   ZICTA: +260 211 369 000 | CERT-ZM: cert@zicta.zm

9. CONSEQUENCES
   Violations of this policy may result in disciplinary action up to and including
   termination of employment, and where applicable, referral to law enforcement
   under the Cyber Security and Cyber Crimes Act, 2021.

10. ACKNOWLEDGEMENT
    I, [EMPLOYEE NAME], have read, understood, and agree to comply with this policy.

    Signature: ___________________________   Date: _______________
    Printed Name: ________________________   Department: __________
""",
    },
    {
        "id": "irp",
        "icon": "🚨",
        "title": "Incident Response Plan (IRP)",
        "description": "Step-by-step plan for responding to cybersecurity incidents.",
        "framework": "CIS Control 17 · NIST RS.RP-1 · ISO 27001 A.16",
        "content": """\
INCIDENT RESPONSE PLAN
=======================
[BUSINESS NAME]
Effective Date: [DATE]
Version: 1.0
Plan Owner: [IT MANAGER / OWNER NAME]

1. PURPOSE
   This plan defines how [BUSINESS NAME] will detect, respond to, and recover from
   cybersecurity incidents to minimise damage and restore normal operations quickly.

2. INCIDENT TYPES COVERED
   - Data breach or unauthorised access
   - Ransomware or malware infection
   - Phishing attack (successful or attempted)
   - Loss or theft of devices containing company data
   - System outage caused by a cyberattack
   - Unauthorised changes to systems or data

3. RESPONSE TEAM
   Incident Commander:  [NAME] — [PHONE] — [EMAIL]
   IT Support Contact:  [NAME / COMPANY] — [PHONE]
   Management Notifier: [NAME] — [PHONE]
   Legal/Compliance:    [NAME / LAW FIRM] — [PHONE]

4. EXTERNAL CONTACTS
   ZICTA (Zambia ICT Authority):  +260 211 369 000  |  info@zicta.zm
   CERT-ZM:                       cert@zicta.zm
   Zambia Police (Cybercrime):    +260 211 251 222
   Data Protection Commission:    [DPC CONTACT]

5. INCIDENT RESPONSE STEPS

   STEP 1 — IDENTIFY (First 15 minutes)
   □ Who noticed the incident? _________________ Time: _________
   □ What systems/data are affected?
   □ Is the incident still ongoing?
   □ Assign Incident Commander.

   STEP 2 — CONTAIN (First 1 hour)
   □ Disconnect affected computers from the network (unplug network cable / disable Wi-Fi).
   □ Do NOT turn off the computer unless ransomware is actively encrypting files.
   □ Preserve evidence — take photos of error messages.
   □ Change passwords for affected accounts from a clean device.
   □ Alert management and IT support.

   STEP 3 — ERADICATE (Hours 1–24)
   □ Run a full antivirus scan on affected systems.
   □ Remove malware or malicious software identified.
   □ Patch any vulnerability that was exploited.
   □ Reset all potentially compromised credentials.

   STEP 4 — RECOVER (Hours 24–72)
   □ Restore data from the most recent clean backup.
   □ Verify systems are clean before reconnecting to the network.
   □ Monitor systems closely for 48 hours after recovery.
   □ Test that all business operations are functioning normally.

   STEP 5 — REPORT & LEARN (Within 7 days)
   □ Report to ZICTA / CERT-ZM if systems or customer data were breached.
   □ Notify affected customers if their data was exposed (required by DPA 2021).
   □ Document what happened, timeline, impact, and actions taken.
   □ Update this plan and implement lessons learned.

6. DATA BREACH NOTIFICATION (Zambia DPA 2021)
   If personal data of customers or employees is breached:
   - Notify the Data Protection Commissioner within 72 hours of discovery.
   - Notify affected individuals without undue delay.
   - Record the breach in the company's data breach register.

7. TESTING
   This plan shall be tested at least once per year via a tabletop exercise.
   Last tested: [DATE]   Next test due: [DATE]

8. PLAN REVIEW
   This plan is reviewed annually or after any significant incident.
   Last reviewed: [DATE]   Next review: [DATE]
""",
    },
    {
        "id": "acp",
        "icon": "🔑",
        "title": "Access Control Policy",
        "description": "Policy for managing who can access company systems and data.",
        "framework": "CIS Control 5 · NIST PR.AC-4 · ISO 27001 A.9",
        "content": """\
ACCESS CONTROL POLICY
======================
[BUSINESS NAME]
Effective Date: [DATE]
Version: 1.0
Policy Owner: [IT MANAGER / OWNER NAME]

1. PURPOSE
   To ensure that access to [BUSINESS NAME]'s information systems and data is
   granted on a need-to-know, least-privilege basis.

2. SCOPE
   Applies to all employees, contractors, and third parties accessing any
   [BUSINESS NAME] system, application, or data — on-premises or in the cloud.

3. ACCESS PRINCIPLES
   3.1 Least Privilege: Users are granted only the minimum access required for their role.
   3.2 Need to Know: Access to sensitive data is restricted to those with a legitimate need.
   3.3 Separation of Duties: Critical tasks require approval from more than one person.

4. USER ACCOUNT MANAGEMENT
   4.1 New Accounts
       □ Access requests must be approved by the employee's manager in writing.
       □ Accounts are created by [IT CONTACT] only.
       □ Default accounts and vendor accounts must be disabled or secured.

   4.2 Account Changes
       □ Role changes must trigger an access review within 5 business days.
       □ Access no longer needed must be removed immediately.

   4.3 Account Termination
       □ When an employee leaves, their access must be revoked on their LAST DAY.
       □ Shared passwords must be changed when an employee with that access leaves.

5. PASSWORD REQUIREMENTS
   □ Minimum 8 characters (12 recommended).
   □ Must include: uppercase, lowercase, numbers, and special characters.
   □ Passwords expire every 90 days.
   □ Accounts lock after 5 failed login attempts.
   □ Password reuse: last 5 passwords may not be reused.
   □ Multi-Factor Authentication (MFA) required for: [LIST SYSTEMS].

6. PRIVILEGED ACCESS
   6.1 Administrator accounts must be separate from regular user accounts.
   6.2 Privileged access must be logged and reviewed monthly.
   6.3 Remote privileged access requires MFA and VPN.

7. REMOTE ACCESS
   7.1 Remote access is permitted only through approved VPN or remote desktop solution.
   7.2 Personal devices used for work must comply with the BYOD policy.
   7.3 Remote sessions must be logged.

8. ACCESS REVIEWS
   Access rights for all users shall be reviewed every 6 months.
   Next review due: [DATE]
   Reviewer: [NAME / TITLE]

9. THIRD-PARTY ACCESS
   9.1 Third-party access is time-limited and revoked immediately after the task is complete.
   9.2 Third parties must sign a confidentiality / NDA agreement before access is granted.
   9.3 Third-party access must be monitored during the session.

10. VIOLATIONS
    Unauthorised access or sharing of credentials is a disciplinary offence and may
    constitute an offence under the Cyber Security and Cyber Crimes Act, 2021.
""",
    },
    {
        "id": "pwd",
        "icon": "🔐",
        "title": "Password & MFA Policy",
        "description": "Rules for creating strong passwords and using multi-factor authentication.",
        "framework": "CIS Control 5 · NIST PR.AC-1 · ISO 27001 A.9.4",
        "content": """\
PASSWORD AND MULTI-FACTOR AUTHENTICATION (MFA) POLICY
=======================================================
[BUSINESS NAME]
Effective Date: [DATE]
Version: 1.0

1. PURPOSE
   Strong passwords and MFA are the first line of defence against unauthorised access.
   This policy ensures that all users protect accounts with strong credentials.

2. PASSWORD REQUIREMENTS
   All system passwords at [BUSINESS NAME] must meet the following minimum standards:

   MINIMUM LENGTH:        8 characters (12+ strongly recommended)
   COMPLEXITY:            At least one of each: uppercase (A-Z), lowercase (a-z),
                          number (0-9), and special character (!@#$%^&*)
   MAXIMUM AGE:           90 days — passwords must be changed every 3 months
   HISTORY:               Cannot reuse any of the last 5 passwords
   LOCKOUT:               Account locked after 5 consecutive failed attempts
   LOCKOUT DURATION:      30 minutes (or until reset by IT)

3. RECOMMENDED APPROACH — PASSPHRASES
   Consider using a passphrase — a string of 4+ random words.
   Example: "ZambiaCloud2024Secure!" is stronger than "P@ss123".
   Use a free password manager (Bitwarden, KeePass) to store complex passwords safely.

4. PROHIBITED PASSWORDS
   The following are NOT allowed:
   □ Passwords containing your name, business name, or username
   □ Common passwords: "password", "123456", "qwerty", "zambia", "lusaka"
   □ Keyboard patterns: "qwerty", "asdfgh"
   □ Repeated characters: "aaaa", "1111"
   □ Any password from the previous 5

5. MULTI-FACTOR AUTHENTICATION (MFA)
   MFA is MANDATORY for:
   □ Email accounts (Gmail, Outlook, Zoho)
   □ Banking and mobile money applications
   □ Cloud storage (Google Drive, OneDrive, Dropbox)
   □ Social media business accounts
   □ Any VPN or remote access system
   □ [ADD OTHER SYSTEMS]

   Recommended MFA apps: Google Authenticator, Microsoft Authenticator, Authy.
   Avoid SMS OTP where possible — use an authenticator app instead.

6. PASSWORD SHARING
   Passwords must NEVER be:
   □ Shared with colleagues, managers, or IT staff
   □ Written on paper and left visible
   □ Sent via email, WhatsApp, or SMS in plain text
   □ Stored in an unprotected spreadsheet or text file

7. SUSPECTED COMPROMISE
   If you believe your password has been compromised:
   1. Change it immediately on all affected accounts.
   2. Enable MFA on the account if not already done.
   3. Report the incident to [IT CONTACT] at [EMAIL/PHONE].
   4. Check https://haveibeenpwned.com to see if your email appeared in a data breach.

8. REVIEW
   This policy is reviewed annually. Last reviewed: [DATE]
""",
    },
    {
        "id": "dpp",
        "icon": "🛡",
        "title": "Data Protection Policy",
        "description": "How the business collects, stores, and protects personal data under Zambia's DPA 2021.",
        "framework": "Zambia DPA 2021 · GDPR-aligned · ISO 27001 A.18",
        "content": """\
DATA PROTECTION POLICY
=======================
[BUSINESS NAME]
Effective Date: [DATE]
Version: 1.0
Data Controller: [OWNER / MANAGEMENT NAME]

1. COMMITMENT
   [BUSINESS NAME] is committed to protecting the personal data of its customers,
   employees, and partners in compliance with the Zambia Data Protection Act
   No. 3 of 2021 and the Cyber Security and Cyber Crimes Act, 2021.

2. WHAT DATA WE COLLECT
   We may collect the following personal data:
   □ Name, contact details (phone, email, address)
   □ National Registration Card (NRC) number where required by law
   □ Financial information (bank account, mobile money) — for payment purposes only
   □ Employment records (for employees)
   □ CCTV footage (if applicable)
   □ [LIST ANY OTHER DATA YOUR BUSINESS COLLECTS]

3. WHY WE COLLECT IT (LAWFUL BASIS)
   We collect data only for the following legitimate purposes:
   □ To provide our products or services to customers
   □ To manage employee records and payroll
   □ To comply with legal obligations (ZICTA, ZRA, PACRA, etc.)
   □ [ADD OTHER PURPOSES]

4. HOW WE PROTECT DATA
   □ Data is stored on password-protected systems.
   □ Sensitive data is encrypted at rest where technically feasible.
   □ Access to personal data is restricted to authorised staff only.
   □ Paper records containing personal data are kept in locked storage.
   □ We do not share personal data with third parties without consent,
     except where required by law.

5. DATA RETENTION
   Data is kept only as long as necessary for the stated purpose:
   □ Customer records:   [X] years after last transaction
   □ Employee records:   [X] years after employment ends (as required by Zambian law)
   □ CCTV footage:       [30] days, then automatically overwritten
   □ Financial records:  [7] years (ZIMRA / ZRA requirements)

6. DATA SUBJECT RIGHTS
   Under the Zambia DPA 2021, individuals have the right to:
   □ Access their personal data held by us
   □ Correct inaccurate data
   □ Request deletion of data (where applicable)
   □ Object to certain types of processing
   To exercise these rights, contact: [EMAIL / PHONE]
   We will respond within 14 days.

7. DATA BREACH RESPONSE
   In the event of a data breach:
   1. The incident is reported to management immediately.
   2. The Data Protection Commissioner is notified within 72 hours if required.
   3. Affected individuals are notified without undue delay if there is high risk to them.
   4. The breach is recorded in our Data Breach Register.

8. THIRD PARTIES
   We only share data with third parties who:
   □ Have a legitimate need to process it on our behalf
   □ Have signed a Data Processing Agreement with us
   □ Comply with Zambian data protection law

9. REGISTRATION
   [BUSINESS NAME] is registered with the Data Protection Commission (DPC) Zambia.
   Registration Number: [DPC REG NUMBER] (or: Application pending)

10. CONTACT
    Data queries and complaints: [EMAIL] | [PHONE]
    Data Protection Commission Zambia: [DPC WEBSITE / PHONE]

11. REVIEW
    This policy is reviewed annually or when there are significant changes in data
    processing activities. Last reviewed: [DATE]
""",
    },
]


class PolicyTemplatesScreen(ctk.CTkFrame):
    """Library of downloadable security policy templates for Zambian SMBs."""

    def __init__(self, master, on_back):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self._on_back = on_back
        self._build()

    # ------------------------------------------------------------------ build
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=84)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="Security Policy Template Library",
            font=FONT_HEADING, text_color=CLR_TEXT,
        ).grid(row=0, column=0, padx=PAD, pady=(16, 4), sticky="w")
        ctk.CTkLabel(
            hdr,
            text="Download and customise these templates for your business — "
                 "replace [PLACEHOLDERS] with your details.",
            font=FONT_SMALL, text_color=CLR_MUTED,
        ).grid(row=1, column=0, padx=PAD, pady=(0, 14), sticky="w")

        scroll = ctk.CTkScrollableFrame(self, fg_color=CLR_BG, corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        tip = ctk.CTkFrame(scroll, fg_color=CLR_SURFACE_ALT, corner_radius=12,
                           border_width=1, border_color=CLR_BORDER)
        tip.grid(row=0, column=0, padx=PAD, pady=(PAD, 12), sticky="ew")
        ctk.CTkLabel(
            tip,
            text="💡  Tip: Having written policies signed by staff is required for "
                 "Silver and Gold certification under the ZDCHP framework. "
                 "These templates are aligned to CIS Controls v8, ISO 27001, "
                 "and Zambia's Data Protection Act 2021.",
            font=FONT_SMALL, text_color=CLR_MUTED, wraplength=820, justify="left",
        ).grid(row=0, column=0, padx=14, pady=10, sticky="w")

        for i, tmpl in enumerate(TEMPLATES):
            self._add_card(scroll, i + 1, tmpl)

        # Nav
        nav = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0, height=64)
        nav.grid(row=2, column=0, sticky="ew")
        ctk.CTkButton(
            nav, text="← Back to Home", font=FONT_BODY,
            fg_color="transparent", border_color=CLR_MUTED, border_width=1,
            text_color=CLR_TEXT, hover_color="#243447", width=150, height=38,
            command=self._on_back,
        ).grid(row=0, column=0, padx=PAD, pady=14)

    def _add_card(self, parent, row_idx: int, tmpl: dict):
        card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=16,
                            border_width=1, border_color=CLR_BORDER)
        card.grid(row=row_idx, column=0, padx=PAD, pady=8, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # Icon
        ctk.CTkLabel(
            card, text=tmpl["icon"], font=("Segoe UI Emoji", 30),
        ).grid(row=0, column=0, rowspan=3, padx=(18, 12), pady=18, sticky="n")

        # Title + description
        ctk.CTkLabel(
            card, text=tmpl["title"],
            font=("Segoe UI", 13, "bold"), text_color=CLR_TEXT, anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=(16, 2))

        ctk.CTkLabel(
            card, text=tmpl["description"],
            font=FONT_SMALL, text_color=CLR_MUTED, anchor="w",
        ).grid(row=1, column=1, sticky="w")

        ctk.CTkLabel(
            card, text=f"📌 {tmpl['framework']}",
            font=("Segoe UI", 9), text_color=CLR_ACCENT, anchor="w",
        ).grid(row=2, column=1, sticky="w", pady=(2, 14))

        # Buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=0, column=2, rowspan=3, padx=(0, 14), pady=14, sticky="e")

        ctk.CTkButton(
            btn_frame, text="👁 Preview", width=100, height=34,
            font=FONT_SMALL,
            fg_color=CLR_SURFACE_ALT, hover_color=CLR_BORDER,
            text_color=CLR_TEXT, corner_radius=10,
            command=lambda t=tmpl: self._preview(t),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="⬇ Download", width=110, height=34,
            font=("Segoe UI", 11, "bold"),
            fg_color=CLR_ACCENT, hover_color="#7D70D6",
            text_color="#000000", corner_radius=10,
            command=lambda t=tmpl: self._download(t),
        ).pack(side="left")

    # ---------------------------------------------------------------- actions
    def _preview(self, tmpl: dict):
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Preview — {tmpl['title']}")
        dlg.geometry("720x560")
        dlg.configure(fg_color=CLR_BG)

        hdr = ctk.CTkFrame(dlg, fg_color=CLR_SURFACE, corner_radius=0, height=56)
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text=f"{tmpl['icon']}  {tmpl['title']}",
            font=("Segoe UI", 13, "bold"), text_color=CLR_ACCENT,
        ).pack(side="left", padx=PAD, pady=14)
        ctk.CTkButton(
            hdr, text="⬇ Download", width=110, height=32,
            fg_color=CLR_ACCENT, hover_color="#7D70D6", text_color="#000000",
            command=lambda: self._download(tmpl),
        ).pack(side="right", padx=PAD)

        tb = ctk.CTkTextbox(
            dlg, font=("Consolas", 11), fg_color=CLR_SURFACE,
            text_color=CLR_TEXT, corner_radius=0,
            wrap="word",
        )
        tb.pack(fill="both", expand=True, padx=12, pady=12)
        tb.insert("1.0", tmpl["content"])
        tb.configure(state="disabled")

    def _download(self, tmpl: dict):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"{tmpl['id']}_template.txt",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(tmpl["content"])

        dlg = ctk.CTkToplevel(self)
        dlg.title("Saved")
        dlg.geometry("420x130")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CLR_SURFACE)
        ctk.CTkLabel(
            dlg, text=f"✔  {tmpl['title']} saved!",
            font=FONT_HEADING, text_color=CLR_SUCCESS,
        ).pack(pady=(22, 4))
        ctk.CTkLabel(
            dlg, text=path, font=FONT_SMALL, text_color=CLR_MUTED, wraplength=380,
        ).pack(pady=(0, 14))
        ctk.CTkButton(
            dlg, text="OK", fg_color=CLR_ACCENT, text_color="#000000",
            command=dlg.destroy,
        ).pack()
