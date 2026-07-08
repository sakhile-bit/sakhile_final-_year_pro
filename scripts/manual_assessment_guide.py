# manual_assessment_guide.py
"""
Manual Assessment Guide for Zambia Digital Hygiene Certification Program

Comprehensive on-site assessment checklist covering all 15 controls
(C01–C15) for use by assessors during Tier 3 manual verification.

Reference: Project Proposal Sections 8.3 & Appendix A
"""

MANUAL_ASSESSMENT_GUIDE = """
================================================================================
         ZAMBIA DIGITAL HYGIENE CERTIFICATION PROGRAM
         Manual Assessment Guide for SME Assessors – v2.0
================================================================================

PURPOSE
-------
This guide provides step-by-step instructions for assessors to evaluate
an SME's digital hygiene posture.  It covers all 15 controls defined in
the Zambia Digital Hygiene Framework aligned with NIST CSF, CIS Controls
v8, and ISO 27001:2022 Annex A.

ASSESSMENT TIERS
----------------
  Tier 1: Self-Assessment   – Web-based or PDF checklist (initial awareness)
  Tier 2: Automated Script  – Python script verifies C01-C05 technically
  Tier 3: Manual Verification – This guide; on-site assessor evaluates C01-C15

ASSESSMENT PROCESS
------------------
  1. Schedule assessment with the business owner/manager
  2. Explain the program, obtain signed consent (see Appendix E)
  3. Run the automated assessment tool for C01-C05
  4. Conduct on-site walkthrough and interview for C06-C15
  5. Collect evidence (screenshots, photos, documents)
  6. Complete scoring table below
  7. Provide verbal recommendations on-site
  8. Submit results and issue certification (if qualified)

TOTAL TIME: ≤ 30 minutes per SME

================================================================================
SECTION 1: BUSINESS INFORMATION
================================================================================

Business Name: _________________________________________________________

Business Registration Number: __________________________________________

Address: _______________________________________________________________

Province:  [ ] Lusaka   [ ] Copperbelt   [ ] Other: ____________

Number of Employees: ________   Years in Operation: ________

Industry Sector: [ ] Technology  [ ] Finance  [ ] Retail
                 [ ] Agriculture [ ] Manufacturing [ ] Mining
                 [ ] Healthcare  [ ] Education     [ ] Other: ____________

Contact Person: ________________________ Position: ____________________

Contact Email: _________________________ Phone: _______________________

Assessment Date: ______________________ Assessor Name: ________________

================================================================================
SECTION 2: AUTOMATED TECHNICAL CONTROLS (C01–C05)
================================================================================
These controls are verified by the Python assessment tool.  Record the
automated results here for the complete assessment record.

CONTROL C01: OPERATING SYSTEM UPDATES (Weight: 10 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Are Windows/OS updates set to automatic?  [ ] Yes  [ ] No  [ ] Don't know
  2. When was the last system update installed? ____________________
  3. How often are updates checked?  [ ] Daily  [ ] Weekly  [ ] Monthly  [ ] Never

Evidence to Verify:
  - Show Windows Update settings (Settings > Update & Security)
  - View update history
  - Check last update timestamp

Scoring:
  10 pts  – Automatic updates enabled & updated in last 30 days
   7 pts  – Manual updates, updated within 30 days
   5 pts  – Updated within last 90 days
   0 pts  – No updates in 90+ days or updates disabled

Score: ___/10     Automated Result: ___/10

CONTROL C02: ANTIVIRUS PROTECTION (Weight: 15 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Is antivirus software installed?  [ ] Yes  [ ] No
  2. Product name: _________________________________________
  3. Is it updated regularly?  [ ] Yes  [ ] No  [ ] Automatic
  4. Is real-time protection enabled?  [ ] Yes  [ ] No
  5. When was the last virus definition update? _________________________

Evidence to Verify:
  - Show antivirus software main interface
  - Confirm real-time protection status
  - Check signature/definition date

Scoring:
  15 pts  – Commercial antivirus with auto-updates and real-time protection
  12 pts  – Windows Defender with auto-updates and real-time protection
   7 pts  – Antivirus installed but definitions outdated (> 7 days)
   5 pts  – Antivirus installed but real-time protection disabled
   0 pts  – No antivirus software detected

Score: ___/15     Automated Result: ___/15

CONTROL C03: FIREWALL CONFIGURATION (Weight: 10 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Software firewall enabled on all computers?  [ ] Yes  [ ] No  [ ] Some
  2. Router/hardware firewall device in use?  [ ] Yes  [ ] No
  3. Default router admin password changed?  [ ] Yes  [ ] No  [ ] Don't know
  4. Are unnecessary ports closed?  [ ] Yes  [ ] No  [ ] Don't know

Evidence to Verify:
  - Show Windows Firewall settings for all profiles
  - Check router configuration page (if accessible)
  - Run 'netsh advfirewall show allprofiles state' from command prompt

Scoring:
  10 pts  – Both software and hardware firewalls enabled + router password changed
   8 pts  – Software firewall enabled on all devices
   4 pts  – Firewall enabled on some devices only
   0 pts  – No firewall enabled

Score: ___/10     Automated Result: ___/10

CONTROL C04: PASSWORD POLICY (Weight: 10 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Minimum password length enforced: ________ characters
  2. Password change frequency: ________ days
  3. Account lockout after failures: ________ attempts
  4. Are default passwords changed on all devices?  [ ] Yes  [ ] No
  5. Is multi-factor authentication used?  [ ] Yes  [ ] No  [ ] Some systems

Evidence to Verify:
  - Run 'net accounts' from command prompt
  - Check router/admin passwords changed from defaults
  - Interview staff about password practices

Scoring:
  10 pts  – Min 8 chars, change ≤90 days, lockout ≤5 attempts, defaults changed
   7 pts  – Min 8 chars, change ≤90 days, no lockout
   4 pts  – Min 6 chars, no expiry policy
   0 pts  – No password policy

Score: ___/10     Automated Result: ___/10

CONTROL C05: BACKUP SYSTEM (Weight: 10 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Are regular backups performed?  [ ] Yes  [ ] No
  2. Backup frequency:  [ ] Daily  [ ] Weekly  [ ] Monthly  [ ] Never
  3. Where are backups stored?  [ ] On-site  [ ] Off-site  [ ] Cloud  [ ] USB
  4. When was the last backup tested/restored? _______________________
  5. Are backups encrypted?  [ ] Yes  [ ] No  [ ] Don't know

Evidence to Verify:
  - Show backup software/schedule
  - Demonstrate or describe backup restoration process
  - Verify off-site/cloud backup location

Scoring:
  10 pts  – Daily automated backups with off-site/cloud storage, tested
   8 pts  – Weekly backups with off-site storage
   5 pts  – Manual backups performed regularly (at least monthly)
   2 pts  – Occasional manual backups, no schedule
   0 pts  – No backups

Score: ___/10     Automated Result: ___/10


================================================================================
SECTION 3: MANUAL / ADMINISTRATIVE CONTROLS (C06–C15)
================================================================================
These controls require on-site inspection, staff interviews, and
document review.

CONTROL C06: ADMIN ACCOUNT MANAGEMENT (Weight: 8 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. How many admin/privileged accounts exist? ________
  2. Are admin accounts separate from daily-use accounts?  [ ] Yes  [ ] No
  3. Is there a process for removing accounts when staff leave?  [ ] Yes  [ ] No
  4. Are shared accounts used?  [ ] Yes  [ ] No

Evidence to Verify:
  - Show user account list (lusrmgr.msc or Settings > Accounts)
  - Check for shared or generic accounts
  - Ask about offboarding process

Scoring:
   8 pts  – ≤2 admin accounts, separate from user accounts, offboarding process
   6 pts  – Limited admin accounts, separation attempted
   3 pts  – Multiple admin accounts, some separation
   0 pts  – Everyone uses admin accounts / no management

Score: ___/8

CONTROL C07: THIRD-PARTY SOFTWARE UPDATES (Weight: 7 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Are browsers (Chrome/Edge/Firefox) auto-updated?  [ ] Yes  [ ] No
  2. Are productivity tools (Office) updated?  [ ] Yes  [ ] No
  3. Is Java/Adobe/Flash removed or updated?  [ ] Yes  [ ] No  [ ] N/A
  4. Is there an inventory of installed software?  [ ] Yes  [ ] No

Evidence to Verify:
  - Check browser version (Help > About)
  - Check installed programs list for outdated software
  - Look for known-vulnerable software (old Java, Flash Player)

Scoring:
   7 pts  – All third-party software current, software inventory exists
   5 pts  – Most software updated, no inventory
   3 pts  – Some outdated software found
   0 pts  – Widespread outdated/vulnerable software

Score: ___/7

CONTROL C08: WI-FI SECURITY (Weight: 7 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Wi-Fi encryption standard:  [ ] WPA3  [ ] WPA2  [ ] WPA  [ ] WEP  [ ] Open
  2. Default SSID changed?  [ ] Yes  [ ] No
  3. Default router password changed?  [ ] Yes  [ ] No
  4. Guest Wi-Fi network separated from business?  [ ] Yes  [ ] No  [ ] N/A
  5. Wi-Fi password shared with non-staff?  [ ] Yes  [ ] No

Evidence to Verify:
  - Check Wi-Fi connection properties for encryption type
  - Verify router SSID is not manufacturer default
  - Check for guest network separation

Scoring:
   7 pts  – WPA2/WPA3, defaults changed, guest network separated
   5 pts  – WPA2/WPA3, defaults changed
   3 pts  – WPA2/WPA3 but defaults not changed
   0 pts  – WEP/Open or no password protection

Score: ___/7

CONTROL C09: EMAIL SECURITY (Weight: 7 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Is a spam filter enabled?  [ ] Yes  [ ] No  [ ] Don't know
  2. Can staff identify phishing emails?  [ ] Yes  [ ] Some  [ ] No
  3. Is there a procedure for reporting suspicious emails?  [ ] Yes  [ ] No
  4. Are email attachments from unknown senders blocked?  [ ] Yes  [ ] No

Evidence to Verify:
  - Check email settings for spam/junk filter
  - Ask staff to describe what they'd do with a suspicious email
  - Review any documented phishing awareness materials

Scoring:
   7 pts  – Spam filter on, staff trained, reporting procedure exists
   5 pts  – Spam filter on, some staff awareness
   3 pts  – Spam filter on, no training
   0 pts  – No spam filter, no awareness

Score: ___/7

CONTROL C10: DEVICE LOCKING (Weight: 5 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Is screensaver/screen lock enabled?  [ ] Yes  [ ] No
  2. Screen lock timeout: ________ minutes
  3. Do staff manually lock devices when leaving?  [ ] Yes  [ ] No  [ ] Sometimes
  4. Are mobile devices also locked?  [ ] Yes  [ ] No  [ ] N/A

Evidence to Verify:
  - Check Windows screensaver settings
  - Observe staff behaviour during visit
  - Check mobile device lock screen configuration

Scoring:
   5 pts  – Auto-lock ≤5 min, staff practice manual locking
   3 pts  – Auto-lock enabled but >5 min, or inconsistent locking
   1 pt   – Some devices have lock, poor practice
   0 pts  – No screen lock configured

Score: ___/5

CONTROL C11: PHYSICAL SECURITY (Weight: 5 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Is server/network equipment in a locked room?  [ ] Yes  [ ] No  [ ] N/A
  2. Is there a visitor log or sign-in?  [ ] Yes  [ ] No
  3. Are CCTV cameras installed?  [ ] Yes  [ ] No
  4. Are doors/windows secured after hours?  [ ] Yes  [ ] No

Evidence to Verify:
  - Inspect server room / equipment location
  - Check visitor log book
  - Walk the premises

Scoring:
   5 pts  – Equipment locked, visitor log, good physical security
   3 pts  – Equipment secured, no visitor log
   1 pt   – Basic security only
   0 pts  – Equipment accessible to anyone

Score: ___/5

CONTROL C12: DATA CLASSIFICATION (Weight: 5 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Are different types of data identified?  [ ] Yes  [ ] No
  2. Is sensitive data labelled?  [ ] Yes  [ ] No
  3. Is there a data handling policy?  [ ] Yes  [ ] No
  4. Are staff aware of which data is sensitive?  [ ] Yes  [ ] Some  [ ] No

Evidence to Verify:
  - Ask to see data classification policy/document
  - Check if file folders are labelled
  - Ask staff what data they consider sensitive

Scoring:
   5 pts  – Data classified, labelled, policy documented, staff aware
   3 pts  – Some classification exists, staff partially aware
   1 pt   – Informal understanding only
   0 pts  – No data classification

Score: ___/5

CONTROL C13: SECURE DISPOSAL (Weight: 5 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Are paper records shredded?  [ ] Yes  [ ] No  [ ] N/A
  2. Are old devices securely wiped before disposal?  [ ] Yes  [ ] No
  3. Are disposal records maintained?  [ ] Yes  [ ] No
  4. Is there a process for returning company devices?  [ ] Yes  [ ] No

Evidence to Verify:
  - Check for shredder presence
  - Ask about old computer/phone disposal process
  - Review any disposal certificates or records

Scoring:
   5 pts  – Paper shredded, devices wiped, disposal records kept
   3 pts  – Some secure disposal practices in place
   1 pt   – Minimal disposal practices
   0 pts  – No secure disposal procedures

Score: ___/5

CONTROL C14: INCIDENT RESPONSE PLAN (Weight: 8 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Does a written incident response plan exist?  [ ] Yes  [ ] No
  2. Is a designated incident contact person identified?  [ ] Yes  [ ] No
     Contact: ________________________ Phone: ________________________
  3. Has the plan been tested/rehearsed?  [ ] Yes  [ ] No  [ ] When: ________
  4. Are staff aware of the plan?  [ ] Yes  [ ] Some  [ ] No
  5. Are ZICTA/CERT-ZM reporting contacts documented?  [ ] Yes  [ ] No

Evidence to Verify:
  - Ask to see the incident response plan document
  - Interview staff about response procedures
  - Check for emergency contact lists posted

Scoring:
   8 pts  – Written plan, designated contact, tested annually, staff aware
   6 pts  – Written plan, designated contact, not tested
   3 pts  – Informal plan, some awareness
   0 pts  – No incident response plan

Score: ___/8

CONTROL C15: STAFF SECURITY TRAINING (Weight: 8 pts)
-------------------------------------------------------------------------------
Assessment Questions:
  1. Has security awareness training been conducted?  [ ] Yes  [ ] No
  2. When was the last training?  ____________________
  3. Training covers:  [ ] Phishing  [ ] Passwords  [ ] Social engineering
                       [ ] Data handling  [ ] Incident reporting  [ ] Mobile safety
  4. Are training records/attendance maintained?  [ ] Yes  [ ] No
  5. Are new employees given security orientation?  [ ] Yes  [ ] No

Evidence to Verify:
  - Ask to see training records or attendance sheets
  - Interview staff about what they learned
  - Check for training materials

Scoring:
   8 pts  – Annual training, all topics, records kept, new employee orientation
   6 pts  – Training conducted in past year, most topics covered
   3 pts  – Some informal training, limited topics
   0 pts  – No security training conducted

Score: ___/8


================================================================================
SECTION 4: SCORING SUMMARY & CERTIFICATION DECISION
================================================================================

                              TECHNICAL CONTROLS  (C01–C05)
                              ─────────────────────────────
  C01 Operating System Updates ............... ___/10
  C02 Antivirus Protection .................. ___/15
  C03 Firewall Configuration ................ ___/10
  C04 Password Policy ....................... ___/10
  C05 Backup System ......................... ___/10
                                    Subtotal: ___/55

                              ADMINISTRATIVE CONTROLS (C06–C15)
                              ──────────────────────────────────
  C06 Admin Account Management .............. ___/8
  C07 Third-Party Software Updates .......... ___/7
  C08 Wi-Fi Security ........................ ___/7
  C09 Email Security ........................ ___/7
  C10 Device Locking ........................ ___/5
  C11 Physical Security ..................... ___/5
  C12 Data Classification ................... ___/5
  C13 Secure Disposal ....................... ___/5
  C14 Incident Response Plan ................ ___/8
  C15 Staff Security Training ............... ___/8
                                    Subtotal: ___/65

  ═══════════════════════════════════════════
  TOTAL SCORE: _______ / 120  ( _______ % )
  Critical Failures: _______
  ═══════════════════════════════════════════

  CERTIFICATION THRESHOLDS:
  ─────────────────────────
  GOLD   :  ≥ 80% (≥96 pts) AND 0 critical failures  – Valid 12 months
  SILVER :  ≥ 60% (≥72 pts) AND ≤1 critical failure   – Valid 12 months
  BRONZE :  ≥ 40% (≥48 pts) AND ≤2 critical failures  – Valid 6 months
  NOT CERTIFIED: Below 40% or too many critical failures

  Certification Level Awarded: ________________________________


================================================================================
SECTION 5: RECOMMENDATIONS
================================================================================

Priority recommendations based on assessment findings:

1. ______________________________________________________________________
   Category: [ ] Technical  [ ] Administrative  [ ] Physical
   Timeline: [ ] Immediate  [ ] 30 days  [ ] 90 days

2. ______________________________________________________________________
   Category: [ ] Technical  [ ] Administrative  [ ] Physical
   Timeline: [ ] Immediate  [ ] 30 days  [ ] 90 days

3. ______________________________________________________________________
   Category: [ ] Technical  [ ] Administrative  [ ] Physical
   Timeline: [ ] Immediate  [ ] 30 days  [ ] 90 days

4. ______________________________________________________________________
   Category: [ ] Technical  [ ] Administrative  [ ] Physical
   Timeline: [ ] Immediate  [ ] 30 days  [ ] 90 days

5. ______________________________________________________________________
   Category: [ ] Technical  [ ] Administrative  [ ] Physical
   Timeline: [ ] Immediate  [ ] 30 days  [ ] 90 days

Zambia-specific guidance:
  - Register for ZICTA cyber alerts: https://www.zicta.zm/
  - Report incidents to CERT-ZM: https://www.cert.gov.zm/
  - Review Data Protection Act No. 3 of 2021 compliance
  - Review Cyber Security and Cyber Crimes Act, 2021 obligations

Reassessment recommended in: _______ months


================================================================================
SECTION 6: ZAMBIAN REGULATORY COMPLIANCE CHECK
================================================================================

Data Protection Act No. 3 of 2021:
  [ ] Data processing activities identified
  [ ] Privacy notices provided to customers
  [ ] Consent mechanisms in place
  [ ] Data breach notification process exists

Cyber Security and Cyber Crimes Act, 2021:
  [ ] Critical information infrastructure requirements reviewed
  [ ] Incident reporting obligations understood
  [ ] Staff aware of cybercrime provisions


================================================================================
SECTION 7: SIGNATURES & DECLARATION
================================================================================

Assessor Declaration:
I confirm that this assessment was conducted accurately and impartially
in accordance with the Zambia Digital Hygiene Certification Program
procedures.

Assessor Signature: ___________________________ Date: _________________

Assessor Name: _____________________________  ID: ____________________


Business Representative Declaration:
I confirm that the information provided during this assessment is
accurate and complete to the best of my knowledge.

Business Representative: ______________________ Date: _________________

Name: ________________________________________ Position: ______________

================================================================================
  Zambia Digital Hygiene Certification Program v2.0
  Aligned with NIST CSF | CIS Controls | ISO 27001
  Licensed under MIT License – Open Source
================================================================================
"""


def generate_manual_checklist():
    """Generate a printable manual assessment checklist."""
    from datetime import datetime

    filename = f"manual_assessment_checklist_{datetime.now().strftime('%Y%m%d')}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(MANUAL_ASSESSMENT_GUIDE)

    print(f"Manual assessment checklist saved to: {filename}")
    print(f"Controls covered: 15 (C01-C15)")
    print(f"Total possible score: 120 points")
    return filename


if __name__ == "__main__":
    generate_manual_checklist()