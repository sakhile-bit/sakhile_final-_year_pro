# scoring_rubric.py
"""
Scoring Rubric for Zambia Digital Hygiene Certification Program

Implements the three-tier certification model (Bronze / Silver / Gold)
with 15 essential security controls totalling 120 points.

Reference: Project Proposal Section 8.2 – Assessment Design
"""

import datetime
import json
from typing import Any, Dict

# ──────────────────────────────────────────────────────────────────
# Total possible score across all 15 controls = 120 points
# ──────────────────────────────────────────────────────────────────

SCORING_RUBRIC: Dict[str, Any] = {
    "program": {
        "name": "Zambia Digital Hygiene Certification Program",
        "version": "1.0.0",
        "total_possible": 120,
        "frameworks": [
            "NIST Cybersecurity Framework v1.1",
            "CIS Critical Security Controls v8 (IG1)",
            "ISO/IEC 27001:2022 Annex A",
            "UK Cyber Essentials",
            "Australian Essential Eight",
        ],
        "legislation": [
            "Zambia Data Protection Act No. 3 of 2021",
            "Cyber Security and Cyber Crimes Act, 2021",
        ],
    },

    "certification_levels": {
        "GOLD": {
            "min_percentage": 80,
            "max_critical_failures": 0,
            "description": "Excellent digital hygiene. All critical controls implemented and maintained.",
            "validity_months": 12,
            "colour": "#FFD700",
            "requirements": [
                "All 5 core automated controls pass",
                "Score >= 80% (>=96/120)",
                "No critical failures",
                "Manual controls verified by assessor",
            ],
        },
        "SILVER": {
            "min_percentage": 60,
            "max_critical_failures": 1,
            "description": "Good digital hygiene. Most controls implemented with minor gaps.",
            "validity_months": 12,
            "colour": "#C0C0C0",
            "requirements": [
                "At least 4 core controls implemented",
                "Score >= 60% (>=72/120)",
                "No more than 1 critical failure",
            ],
        },
        "BRONZE": {
            "min_percentage": 40,
            "max_critical_failures": 2,
            "description": "Basic digital hygiene. Foundational controls in place.",
            "validity_months": 6,
            "colour": "#CD7F32",
            "requirements": [
                "At least 3 core controls implemented",
                "Score >= 40% (>=48/120)",
                "No more than 2 critical failures",
            ],
        },
        "NOT_CERTIFIED": {
            "min_percentage": 0,
            "max_critical_failures": 99,
            "description": "Significant improvement needed. Not eligible for certification.",
            "validity_months": 0,
            "colour": "#DC3545",
            "requirements": [
                "Score < 40%",
                "Critical gaps in security posture",
            ],
        },
    },

    # ── Full 15-control weight table ────────────────────────────────
    "control_weights": {
        # Automated / technical controls (C01-C05)
        "C01_os_updates": {
            "id": "C01", "weight": 10, "critical": True,
            "failure_threshold": 3,
            "category": "technical", "verification": "automated",
        },
        "C02_antivirus": {
            "id": "C02", "weight": 15, "critical": True,
            "failure_threshold": 5,
            "category": "technical", "verification": "automated",
        },
        "C03_firewall": {
            "id": "C03", "weight": 10, "critical": True,
            "failure_threshold": 3,
            "category": "technical", "verification": "automated",
        },
        "C04_password_policy": {
            "id": "C04", "weight": 10, "critical": True,
            "failure_threshold": 3,
            "category": "technical", "verification": "automated",
        },
        "C05_backups": {
            "id": "C05", "weight": 10, "critical": True,
            "failure_threshold": 3,
            "category": "technical", "verification": "automated",
        },
        # Manual / administrative controls (C06-C15)
        "C06_admin_accounts": {
            "id": "C06", "weight": 8, "critical": False,
            "failure_threshold": 2,
            "category": "administrative", "verification": "manual",
        },
        "C07_software_updates": {
            "id": "C07", "weight": 7, "critical": False,
            "failure_threshold": 2,
            "category": "technical", "verification": "manual",
        },
        "C08_wifi_security": {
            "id": "C08", "weight": 7, "critical": False,
            "failure_threshold": 2,
            "category": "technical", "verification": "manual",
        },
        "C09_email_security": {
            "id": "C09", "weight": 7, "critical": False,
            "failure_threshold": 2,
            "category": "administrative", "verification": "manual",
        },
        "C10_device_locking": {
            "id": "C10", "weight": 5, "critical": False,
            "failure_threshold": 1,
            "category": "physical", "verification": "manual",
        },
        "C11_physical_security": {
            "id": "C11", "weight": 5, "critical": False,
            "failure_threshold": 1,
            "category": "physical", "verification": "manual",
        },
        "C12_data_classification": {
            "id": "C12", "weight": 5, "critical": False,
            "failure_threshold": 1,
            "category": "administrative", "verification": "manual",
        },
        "C13_secure_disposal": {
            "id": "C13", "weight": 5, "critical": False,
            "failure_threshold": 1,
            "category": "administrative", "verification": "manual",
        },
        "C14_incident_response": {
            "id": "C14", "weight": 8, "critical": False,
            "failure_threshold": 2,
            "category": "administrative", "verification": "manual",
        },
        "C15_staff_training": {
            "id": "C15", "weight": 8, "critical": False,
            "failure_threshold": 2,
            "category": "administrative", "verification": "manual",
        },
    },
}


def calculate_certification_level(score: int, critical_failures: int = 0) -> str:
    """Calculate certification level based on score and critical failures.

    Args:
        score: Total score out of 120.
        critical_failures: Number of critical control failures.

    Returns:
        Certification level string.
    """
    total = SCORING_RUBRIC["program"]["total_possible"]
    percentage = (score / total) * 100 if total > 0 else 0

    for level_name in ("GOLD", "SILVER", "BRONZE"):
        level = SCORING_RUBRIC["certification_levels"][level_name]
        if percentage >= level["min_percentage"] and critical_failures <= level["max_critical_failures"]:
            return level_name

    return "NOT CERTIFIED"


def get_level_details(level: str) -> dict:
    """Return metadata for a certification level."""
    return SCORING_RUBRIC["certification_levels"].get(level, SCORING_RUBRIC["certification_levels"]["NOT_CERTIFIED"])


def generate_certificate_template(business_info: dict, level: str, score: int) -> str:
    """Generate a text-based certificate template.

    Args:
        business_info: Dict with keys 'name', 'address', 'registration', 'id'.
        level: Certification level (GOLD/SILVER/BRONZE).
        score: Achieved score out of 120.

    Returns:
        Formatted certificate string.
    """
    total = SCORING_RUBRIC["program"]["total_possible"]
    pct = int((score / total) * 100) if total else 0
    level_meta = get_level_details(level)
    validity_months = level_meta.get("validity_months", 0)
    expiry = datetime.datetime.now() + datetime.timedelta(days=validity_months * 30)
    cert_id = f"ZDH-{datetime.datetime.now().strftime('%Y%m')}-{business_info.get('id', '0000')}"

    certificate = f"""
    ====================================================================
                ZAMBIA DIGITAL HYGIENE CERTIFICATION PROGRAM
    ====================================================================

    This is to certify that

    {business_info.get('name', 'N/A')}
    {business_info.get('address', '')}

    Registration Number: {business_info.get('registration', 'N/A')}

    has achieved

                    *  {level} LEVEL CERTIFICATION  *

    in recognition of implementing and maintaining essential digital
    hygiene controls to protect against cyber threats, as assessed
    against the Zambia Digital Hygiene Framework aligned with NIST CSF,
    CIS Controls, and ISO 27001.

    Assessment Score: {score}/{total} ({pct}%)
    Controls Assessed: 15
    Certification ID: {cert_id}
    Issue Date: {datetime.datetime.now().strftime('%d %B %Y')}
    Valid Until: {expiry.strftime('%d %B %Y')} ({validity_months} months)

    This certification demonstrates commitment to cybersecurity best
    practices and helps build trust with customers and partners.

    ====================================================================
    Issued by: Zambia Digital Hygiene Certification Program
    In Partnership with: ____________________________________________
    Assessor: __________________________ Signature: _________________
    ====================================================================
    """
    return certificate


if __name__ == "__main__":
    # Save scoring rubric to JSON for reference
    with open('scoring_rubric.json', 'w') as f:
        json.dump(SCORING_RUBRIC, f, indent=2)

    print(f"Scoring rubric saved to scoring_rubric.json")
    print(f"Total possible score: {SCORING_RUBRIC['program']['total_possible']}")
    print(f"Number of controls: {len(SCORING_RUBRIC['control_weights'])}")
    for level, details in SCORING_RUBRIC["certification_levels"].items():
        print(f"  {level}: >={details['min_percentage']}% | max {details['max_critical_failures']} critical failures | valid {details['validity_months']}mo")