
================================================================================
ZAMBIA DIGITAL HYGIENE CERTIFICATION PROGRAM
Automated Assessment Tool
================================================================================

OVERVIEW
--------
This tool helps Zambian Small and Medium Enterprises (SMEs) assess their
cybersecurity hygiene and work toward certification. The tool evaluates
5 critical security controls based on international standards adapted for
the Zambian context.

FEATURES
--------
1. Automated assessment of 5 key security controls
2. Manual assessment guide for comprehensive evaluation
3. Scoring system with certification levels (Gold, Silver, Bronze)
4. Detailed recommendations for improvement
5. Certificate generation for qualifying businesses

REQUIREMENTS
------------
- Windows 7 or higher (some features require Windows 10)
- Python 3.6 or higher
- Administrator privileges (for some checks)

INSTALLATION
------------
1. Install Python from https://python.org
2. Open Command Prompt as Administrator
3. Install required packages:
   
   pip install psutil wmi

4. Download the assessment tool files:
   - digital_hygiëne_assessment.py
   - manual_assessment_guide.py
   - scoring_rubric.py

USAGE
-----
Option 1: Automated Assessment (Recommended)
--------------------------------------------
1. Run as Administrator:
   
   python digital_hygiene_assessment.py

2. Follow the prompts to enter business information
3. The tool will run 5 automated checks
4. Review the results and recommendations
5. Save the report for your records

Option 2: Manual Assessment
---------------------------
1. Run the manual assessment guide:
   
   python manual_assessment_guide.py

2. Print the generated checklist
3. Conduct assessment with business representative
4. Complete all sections of the checklist
5. Calculate final score and determine certification level

ASSESSMENT CONTROLS
-------------------
1. Operating System Updates (10 points)
   - Automatic updates enabled
   - Recent updates installed

2. Antivirus Protection (15 points)
   - Antivirus software installed
   - Real-time protection enabled
   - Regular definition updates

3. Firewall Configuration (10 points)
   - Firewall enabled on all devices
   - Unnecessary ports closed

4. Password Policy (10 points)
   - Minimum 8 character passwords
   - Regular password changes
   - Account lockout after failures

5. Backup System (5 points)
   - Regular backups performed
   - Off-site/cloud backup storage
   - Backup testing and restoration

CERTIFICATION LEVELS
--------------------
- GOLD (40-50 points): Excellent digital hygiene
- SILVER (30-39 points): Good digital hygiene
- BRONZE (20-29 points): Basic digital hygiene
- NOT CERTIFIED (<20 points): Needs improvement

NEXT STEPS AFTER ASSESSMENT
---------------------------
1. Implement recommendations from the assessment
2. Contact Zambia Digital Hygiene Program for formal certification
3. Display certification to build customer trust
4. Schedule reassessment annually or after major changes

SUPPORT AND CONTACT
-------------------
For technical support or certification inquiries:
Email: digitalhygiene@zambia.gov.zm
Phone: +260 211 123456

ETHICAL USE
-----------
This tool is for assessment purposes only. Do not use it to:
- Assess systems without permission
- Bypass security controls
- Collect sensitive information
- Harm computer systems

Always obtain written permission before assessing any system.

VERSION HISTORY
---------------
v1.0 (2024): Initial release
- Basic assessment of 5 controls
- Manual assessment guide
- Certificate generation

LICENSE
-------
This tool is provided as part of the Zambia Digital Hygiene Certification
Program. Free for use by Zambian SMEs and certified assessors.

================================================================================
