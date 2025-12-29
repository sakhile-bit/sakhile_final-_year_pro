# manual_assessment_guide.py
"""
Manual Assessment Guide for Zambia Digital Hygiene Certification
For assessors to use when automated tools cannot be used
"""

MANUAL_ASSESSMENT_GUIDE = """
================================================================================
ZAMBIA DIGITAL HYGIENE CERTIFICATION
Manual Assessment Guide for SME Assessors
================================================================================

Purpose:
This guide helps assessors evaluate SMEs' digital hygiene when automated tools
cannot be used or for verification purposes.

Assessment Process:
1. Schedule assessment with business owner/manager
2. Conduct on-site visit (if possible) or remote interview
3. Review documentation and physical evidence
4. Complete assessment checklist
5. Provide recommendations
6. Issue certification (if qualified)

================================================================================
SECTION 1: BUSINESS INFORMATION
================================================================================

Business Name: _________________________________________________________

Business Registration Number: __________________________________________

Address: _____________________________________________________________

Contact Person: ________________________ Position: ____________________

Contact Email: ________________________ Phone: ________________________

Assessment Date: ______________________ Assessor: _____________________

================================================================================
SECTION 2: DIGITAL HYGIENE CONTROLS ASSESSMENT
================================================================================

CONTROL 1: OPERATING SYSTEM UPDATES
-------------------------------------------------------------------------------
Assessment Questions:
1. Are Windows/Mac updates set to automatic? ❑ Yes ❑ No ❑ Don't know
2. When was the last system update installed? ____________________
3. How often are updates checked? ❑ Daily ❑ Weekly ❑ Monthly ❑ Never

Evidence to Verify:
- Show Windows Update settings
- View update history
- Check last update timestamp

Scoring:
- Automatic updates enabled & updated in last 30 days: 10 points
- Manual updates but updated in last 30 days: 7 points
- Updated in last 90 days: 5 points
- No updates in 90+ days: 0 points

Score: ___/10

CONTROL 2: ANTIVIRUS PROTECTION
-------------------------------------------------------------------------------
Assessment Questions:
1. Is antivirus software installed? ❑ Yes ❑ No
2. If yes, which product? _________________________________________
3. Is it updated regularly? ❑ Yes ❑ No ❑ Automatic
4. When was last virus definition update? _________________________

Evidence to Verify:
- Show antivirus software interface
- Check update status
- Verify real-time protection is enabled

Scoring:
- Commercial antivirus with auto-updates: 15 points
- Windows Defender with auto-updates: 12 points
- Antivirus installed but not updated: 5 points
- No antivirus: 0 points

Score: ___/15

CONTROL 3: FIREWALL CONFIGURATION
-------------------------------------------------------------------------------
Assessment Questions:
1. Is firewall enabled on all computers? ❑ Yes ❑ No ❑ Some
2. Is router/firewall device used? ❑ Yes ❑ No
3. Are unnecessary ports closed? ❑ Yes ❑ No ❑ Don't know

Evidence to Verify:
- Show Windows Firewall settings
- Check router configuration (if accessible)
- Verify no open ports to internet (if possible)

Scoring:
- Both software and hardware firewalls enabled: 10 points
- Software firewall enabled on all devices: 8 points
- Firewall enabled on some devices: 4 points
- No firewall: 0 points

Score: ___/10

CONTROL 4: PASSWORD POLICY
-------------------------------------------------------------------------------
Assessment Questions:
1. Minimum password length: ________ characters
2. Password change frequency: ________ days
3. Account lockout after failures: ________ attempts
4. Are default passwords changed? ❑ Yes ❑ No

Evidence to Verify:
- Show password policy settings
- Check router/admin passwords changed
- Interview staff about password practices

Scoring:
- Minimum 8 chars, change 90 days, lockout 5 attempts: 10 points
- Minimum 8 chars, change 90 days: 7 points
- Minimum 6 chars: 4 points
- No password policy: 0 points

Score: ___/10

CONTROL 5: BACKUP SYSTEM
-------------------------------------------------------------------------------
Assessment Questions:
1. Are regular backups performed? ❑ Yes ❑ No
2. Backup frequency: ❑ Daily ❑ Weekly ❑ Monthly ❑ Never
3. Where are backups stored? ❑ On-site ❑ Off-site ❑ Cloud
4. When was last backup tested/restored? _______________________

Evidence to Verify:
- Show backup software/schedule
- Demonstrate backup restoration
- Verify off-site/cloud backup

Scoring:
- Daily backups with off-site storage: 5 points
- Weekly backups with off-site: 4 points
- Manual backups: 2 points
- No backups: 0 points

Score: ___/5

================================================================================
SECTION 3: ADDITIONAL CONTROLS (OPTIONAL)
================================================================================

CONTROL 6: EMPLOYEE AWARENESS
-------------------------------------------------------------------------------
Questions:
1. Has staff received cybersecurity training? ❑ Yes ❑ No
2. Are phishing emails reported? ❑ Yes ❑ No
3. Clear desk policy for sensitive documents? ❑ Yes ❑ No

Score: ___/5 (Bonus)

CONTROL 7: PHYSICAL SECURITY
-------------------------------------------------------------------------------
Questions:
1. Are computers locked when unattended? ❑ Yes ❑ No
2. Server room/equipment locked? ❑ Yes ❑ No ❑ N/A
3. Visitor access controlled? ❑ Yes ❑ No

Score: ___/5 (Bonus)

================================================================================
SECTION 4: TOTAL SCORE & CERTIFICATION
================================================================================

TOTAL SCORE: ______ / 50
Additional Bonus: ______ / 10
GRAND TOTAL: ______ / 60

CERTIFICATION LEVEL:
- 48-60 points: GOLD CERTIFICATION
- 36-47 points: SILVER CERTIFICATION
- 24-35 points: BRONZE CERTIFICATION
- Below 24: NOT CERTIFIED (Requires improvement)

Certification Level: ________________________________

================================================================================
SECTION 5: RECOMMENDATIONS
================================================================================

Based on assessment, recommend the following improvements:

1. ______________________________________________________________________
   Timeline: ❑ Immediate ❑ 30 days ❑ 90 days

2. ______________________________________________________________________
   Timeline: ❑ Immediate ❑ 30 days ❑ 90 days

3. ______________________________________________________________________
   Timeline: ❑ Immediate ❑ 30 days ❑ 90 days

================================================================================
SECTION 6: SIGNATURES
================================================================================

Assessor Signature: ___________________________ Date: _________________

Business Representative: ______________________ Date: _________________

================================================================================
"""

def generate_manual_checklist():
    """Generate a printable manual assessment checklist"""
    import os
    from datetime import datetime
    
    filename = f"manual_assessment_checklist_{datetime.now().strftime('%Y%m%d')}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(MANUAL_ASSESSMENT_GUIDE)
    
    print(f"Manual assessment checklist saved to: {filename}")
    return filename

if __name__ == "__main__":
    generate_manual_checklist()