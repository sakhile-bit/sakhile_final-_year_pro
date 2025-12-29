# scoring_rubric.py
"""
Scoring Rubric for Zambia Digital Hygiene Certification
"""

SCORING_RUBRIC = {
    "certification_levels": {
        "GOLD": {
            "min_score": 40,
            "max_score": 50,
            "description": "Excellent digital hygiene. All critical controls implemented and maintained.",
            "validity": "12 months",
            "requirements": [
                "All 5 core controls implemented",
                "Score ≥ 80%",
                "No critical failures"
            ]
        },
        "SILVER": {
            "min_score": 30,
            "max_score": 39,
            "description": "Good digital hygiene. Most controls implemented with minor gaps.",
            "validity": "12 months",
            "requirements": [
                "At least 4 core controls implemented",
                "Score ≥ 60%",
                "No more than 1 critical failure"
            ]
        },
        "BRONZE": {
            "min_score": 20,
            "max_score": 29,
            "description": "Basic digital hygiene. Foundational controls in place.",
            "validity": "6 months",
            "requirements": [
                "At least 3 core controls implemented",
                "Score ≥ 40%",
                "No more than 2 critical failures"
            ]
        },
        "NOT_CERTIFIED": {
            "min_score": 0,
            "max_score": 19,
            "description": "Needs significant improvement.",
            "validity": "0 months",
            "requirements": [
                "Score < 40%",
                "Critical gaps in security"
            ]
        }
    },
    
    "control_weights": {
        "os_updates": {
            "weight": 10,
            "critical": True,
            "failure_threshold": 3  # Score below this is critical failure
        },
        "antivirus": {
            "weight": 15,
            "critical": True,
            "failure_threshold": 5
        },
        "firewall": {
            "weight": 10,
            "critical": True,
            "failure_threshold": 3
        },
        "password_policy": {
            "weight": 10,
            "critical": False,
            "failure_threshold": 3
        },
        "backup_system": {
            "weight": 5,
            "critical": True,
            "failure_threshold": 2
        }
    },
    
    "bonus_points": {
        "employee_training": {
            "description": "Regular cybersecurity training for staff",
            "points": 3,
            "evidence_required": ["Training records", "Attendance sheets"]
        },
        "incident_response_plan": {
            "description": "Documented incident response procedure",
            "points": 3,
            "evidence_required": ["Response plan document", "Test records"]
        },
        "data_classification": {
            "description": "Data classified by sensitivity",
            "points": 2,
            "evidence_required": ["Data classification policy", "Labels"]
        },
        "secure_disposal": {
            "description": "Secure disposal of sensitive data",
            "points": 2,
            "evidence_required": ["Shredding records", "Disposal certificates"]
        }
    }
}

def calculate_certification_level(score, critical_failures=0):
    """Calculate certification level based on score and critical failures"""
    percentage = (score / 50) * 100
    
    if percentage >= 80 and critical_failures == 0:
        return "GOLD"
    elif percentage >= 60 and critical_failures <= 1:
        return "SILVER"
    elif percentage >= 40 and critical_failures <= 2:
        return "BRONZE"
    else:
        return "NOT CERTIFIED"

def generate_certificate_template(business_info, level, score):
    """Generate a certificate template"""
    certificate = f"""
    ====================================================================
                      ZAMBIA DIGITAL HYGIENE CERTIFICATE
    ====================================================================
    
    This is to certify that
    
    {business_info['name']}
    {business_info.get('address', '')}
    
    Registration Number: {business_info.get('registration', 'N/A')}
    
    has achieved
    
    {level} LEVEL CERTIFICATION
    
    in recognition of implementing and maintaining essential digital
    hygiene controls to protect against cyber threats.
    
    Assessment Score: {score}/50 ({int((score/50)*100)}%)
    Certification ID: ZDH-{datetime.datetime.now().strftime('%Y%m')}-{business_info.get('id', '0000')}
    Issue Date: {datetime.datetime.now().strftime('%d %B %Y')}
    Valid Until: {(datetime.datetime.now() + datetime.timedelta(days=365)).strftime('%d %B %Y')}
    
    This certification demonstrates commitment to cybersecurity best
    practices and helps build trust with customers and partners.
    
    ====================================================================
    Issued by: Zambia Digital Hygiene Certification Program
    Assessor: __________________________
    ====================================================================
    """
    return certificate

if __name__ == "__main__":
    import json
    
    # Save scoring rubric to file
    with open('scoring_rubric.json', 'w') as f:
        json.dump(SCORING_RUBRIC, f, indent=2)
    
    print("Scoring rubric saved to scoring_rubric.json")