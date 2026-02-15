-- Database initialization script for Zambia Digital Hygiene Assessment Tool
-- Drop database if it exists (for clean reinstall)
DROP DATABASE IF EXISTS digital_hygiene;

-- Create database
CREATE DATABASE digital_hygiene CHARACTER
SET
    utf8mb4 COLLATE utf8mb4_unicode_ci;

USE digital_hygiene;

-- Users table for authentication
CREATE TABLE
    IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM ('admin', 'assessor', 'viewer', 'business_owner') DEFAULT 'assessor',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );

-- Businesses table
CREATE TABLE
    IF NOT EXISTS businesses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        registration_number VARCHAR(50) UNIQUE,
        address TEXT,
        contact_person VARCHAR(100),
        contact_email VARCHAR(100),
        contact_phone VARCHAR(20),
        industry VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );

-- Assessments table
CREATE TABLE
    IF NOT EXISTS assessments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        business_id INT NOT NULL,
        assessor_id INT,
        assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        system_info JSON,
        controls_results JSON NOT NULL,
        total_score INT NOT NULL,
        certification_level ENUM (
            'GOLD',
            'SILVER',
            'BRONZE',
            'NOT_CERTIFIED',
            'NOT CERTIFIED'
        ) NOT NULL,
        recommendations JSON,
        status ENUM ('draft', 'completed', 'certified') DEFAULT 'completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (business_id) REFERENCES businesses (id) ON DELETE CASCADE,
        FOREIGN KEY (assessor_id) REFERENCES users (id) ON DELETE SET NULL
    );

-- Certificates table
CREATE TABLE
    IF NOT EXISTS certificates (
        id INT AUTO_INCREMENT PRIMARY KEY,
        assessment_id INT NOT NULL,
        certificate_number VARCHAR(50) UNIQUE NOT NULL,
        issued_date DATE NOT NULL,
        expiry_date DATE NOT NULL,
        certificate_data JSON,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (assessment_id) REFERENCES assessments (id) ON DELETE CASCADE
    );

-- Audit logs table
CREATE TABLE
    IF NOT EXISTS audit_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        action VARCHAR(100) NOT NULL,
        resource_type VARCHAR(50),
        resource_id INT,
        details JSON,
        ip_address VARCHAR(45),
        user_agent TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
    );

-- Indexes for better performance
CREATE INDEX idx_assessments_business_id ON assessments (business_id);

CREATE INDEX idx_assessments_date ON assessments (assessment_date);

CREATE INDEX idx_assessments_level ON assessments (certification_level);

CREATE INDEX idx_certificates_assessment_id ON certificates (assessment_id);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs (timestamp);

CREATE INDEX idx_audit_logs_user ON audit_logs (user_id);

-- Insert default admin user (password: admin123)
INSERT IGNORE INTO users (username, email, password_hash, role)
VALUES
    (
        'admin',
        'admin@digitalhygiene.gov.zm',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uLjJc9sO3l6',
        'admin'
    );

-- Insert sample business data
INSERT IGNORE INTO businesses (name, registration_number, industry)
VALUES
    (
        'Zambia Tech Solutions Ltd',
        'ZT2024001',
        'Information Technology'
    ),
    (
        'Lusaka Manufacturing Co.',
        'LM2024002',
        'Manufacturing'
    ),
    (
        'Copperbelt Mining Supplies',
        'CM2024003',
        'Mining'
    );

-- Insert sample assessment data (15-control framework, 120 pts total)
INSERT IGNORE INTO assessments (
    business_id,
    total_score,
    certification_level,
    controls_results
)
VALUES
    (
        1,
        102,
        'GOLD',
        '{"controls":{"C01_os_updates":{"control_id":"C01","name":"OS Updates","score":10,"weight":10,"status":"PASS","category":"technical","verification":"automated","details":"System up to date"},"C02_antivirus":{"control_id":"C02","name":"Antivirus Protection","score":15,"weight":15,"status":"PASS","category":"technical","verification":"automated","details":"AV enabled and updated"},"C03_firewall":{"control_id":"C03","name":"Firewall Configuration","score":10,"weight":10,"status":"PASS","category":"technical","verification":"automated","details":"Firewall active"},"C04_password_policy":{"control_id":"C04","name":"Password Policy","score":8,"weight":10,"status":"WARNING","category":"technical","verification":"automated","details":"Partial compliance"},"C05_backup":{"control_id":"C05","name":"Backup Systems","score":7,"weight":10,"status":"WARNING","category":"technical","verification":"automated","details":"Irregular backups"},"C06_security_training":{"control_id":"C06","name":"Security Awareness Training","score":8,"weight":8,"status":"PASS","category":"administrative","verification":"manual","details":"Regular training"},"C07_access_control":{"control_id":"C07","name":"Access Control Policy","score":7,"weight":7,"status":"PASS","category":"administrative","verification":"manual","details":"Least-privilege enforced"},"C08_incident_response":{"control_id":"C08","name":"Incident Response Plan","score":7,"weight":7,"status":"PASS","category":"administrative","verification":"manual","details":"Documented and tested"},"C09_encryption":{"control_id":"C09","name":"Data Encryption","score":5,"weight":7,"status":"WARNING","category":"technical","verification":"manual","details":"Partial encryption"},"C10_mobile_security":{"control_id":"C10","name":"Mobile Device Security","score":5,"weight":5,"status":"PASS","category":"technical","verification":"manual","details":"MDM in place"},"C11_physical_security":{"control_id":"C11","name":"Physical Security","score":5,"weight":5,"status":"PASS","category":"physical","verification":"manual","details":"Access-controlled"},"C12_network_security":{"control_id":"C12","name":"Network Security","score":5,"weight":5,"status":"PASS","category":"technical","verification":"manual","details":"WPA3 + segmentation"},"C13_acceptable_use":{"control_id":"C13","name":"Acceptable Use Policy","score":3,"weight":5,"status":"WARNING","category":"administrative","verification":"manual","details":"Written but not signed"},"C14_vendor_risk":{"control_id":"C14","name":"Vendor/Third-Party Risk","score":5,"weight":8,"status":"WARNING","category":"administrative","verification":"manual","details":"Contracts include security"},"C15_regulatory_compliance":{"control_id":"C15","name":"Regulatory Compliance","score":2,"weight":8,"status":"FAIL","category":"administrative","verification":"manual","details":"Partial compliance"}},"total_possible":120,"critical_failures":0,"assessment_tier":"full"}'
    ),
    (
        2,
        72,
        'SILVER',
        '{"controls":{"C01_os_updates":{"control_id":"C01","name":"OS Updates","score":8,"weight":10,"status":"WARNING","category":"technical","verification":"automated","details":"Updates pending"},"C02_antivirus":{"control_id":"C02","name":"Antivirus Protection","score":12,"weight":15,"status":"PASS","category":"technical","verification":"automated","details":"AV enabled"},"C03_firewall":{"control_id":"C03","name":"Firewall Configuration","score":5,"weight":10,"status":"WARNING","category":"technical","verification":"automated","details":"Partial config"},"C04_password_policy":{"control_id":"C04","name":"Password Policy","score":5,"weight":10,"status":"FAIL","category":"technical","verification":"automated","details":"Weak policy"},"C05_backup":{"control_id":"C05","name":"Backup Systems","score":4,"weight":10,"status":"FAIL","category":"technical","verification":"automated","details":"No regular backup"},"C06_security_training":{"control_id":"C06","name":"Security Awareness Training","score":5,"weight":8,"status":"WARNING","category":"administrative","verification":"manual","details":"Annual training"},"C07_access_control":{"control_id":"C07","name":"Access Control Policy","score":5,"weight":7,"status":"WARNING","category":"administrative","verification":"manual","details":"Documented"},"C08_incident_response":{"control_id":"C08","name":"Incident Response Plan","score":5,"weight":7,"status":"WARNING","category":"administrative","verification":"manual","details":"Documented not tested"},"C09_encryption":{"control_id":"C09","name":"Data Encryption","score":5,"weight":7,"status":"WARNING","category":"technical","verification":"manual","details":"HTTPS only"},"C10_mobile_security":{"control_id":"C10","name":"Mobile Device Security","score":3,"weight":5,"status":"WARNING","category":"technical","verification":"manual","details":"Basic locks"},"C11_physical_security":{"control_id":"C11","name":"Physical Security","score":3,"weight":5,"status":"WARNING","category":"physical","verification":"manual","details":"Locked office"},"C12_network_security":{"control_id":"C12","name":"Network Security","score":3,"weight":5,"status":"WARNING","category":"technical","verification":"manual","details":"WPA2"},"C13_acceptable_use":{"control_id":"C13","name":"Acceptable Use Policy","score":2,"weight":5,"status":"WARNING","category":"administrative","verification":"manual","details":"Informal"},"C14_vendor_risk":{"control_id":"C14","name":"Vendor/Third-Party Risk","score":3,"weight":8,"status":"WARNING","category":"administrative","verification":"manual","details":"Informal"},"C15_regulatory_compliance":{"control_id":"C15","name":"Regulatory Compliance","score":4,"weight":8,"status":"WARNING","category":"administrative","verification":"manual","details":"Aware"}},"total_possible":120,"critical_failures":1,"assessment_tier":"full"}'
    ),
    (
        3,
        48,
        'BRONZE',
        '{"controls":{"C01_os_updates":{"control_id":"C01","name":"OS Updates","score":5,"weight":10,"status":"WARNING","category":"technical","verification":"automated","details":"Outdated"},"C02_antivirus":{"control_id":"C02","name":"Antivirus Protection","score":10,"weight":15,"status":"PASS","category":"technical","verification":"automated","details":"AV installed"},"C03_firewall":{"control_id":"C03","name":"Firewall Configuration","score":8,"weight":10,"status":"PASS","category":"technical","verification":"automated","details":"Active"},"C04_password_policy":{"control_id":"C04","name":"Password Policy","score":3,"weight":10,"status":"FAIL","category":"technical","verification":"automated","details":"Weak passwords"},"C05_backup":{"control_id":"C05","name":"Backup Systems","score":2,"weight":10,"status":"FAIL","category":"technical","verification":"automated","details":"No backup"},"C06_security_training":{"control_id":"C06","name":"Security Awareness Training","score":2,"weight":8,"status":"FAIL","category":"administrative","verification":"manual","details":"Ad-hoc"},"C07_access_control":{"control_id":"C07","name":"Access Control Policy","score":2,"weight":7,"status":"FAIL","category":"administrative","verification":"manual","details":"No formal policy"},"C08_incident_response":{"control_id":"C08","name":"Incident Response Plan","score":2,"weight":7,"status":"FAIL","category":"administrative","verification":"manual","details":"Informal"},"C09_encryption":{"control_id":"C09","name":"Data Encryption","score":2,"weight":7,"status":"FAIL","category":"technical","verification":"manual","details":"No encryption"},"C10_mobile_security":{"control_id":"C10","name":"Mobile Device Security","score":2,"weight":5,"status":"FAIL","category":"technical","verification":"manual","details":"Basic locks"},"C11_physical_security":{"control_id":"C11","name":"Physical Security","score":2,"weight":5,"status":"FAIL","category":"physical","verification":"manual","details":"Minimal"},"C12_network_security":{"control_id":"C12","name":"Network Security","score":2,"weight":5,"status":"FAIL","category":"technical","verification":"manual","details":"Default settings"},"C13_acceptable_use":{"control_id":"C13","name":"Acceptable Use Policy","score":2,"weight":5,"status":"FAIL","category":"administrative","verification":"manual","details":"None"},"C14_vendor_risk":{"control_id":"C14","name":"Vendor/Third-Party Risk","score":2,"weight":8,"status":"FAIL","category":"administrative","verification":"manual","details":"Not managed"},"C15_regulatory_compliance":{"control_id":"C15","name":"Regulatory Compliance","score":2,"weight":8,"status":"FAIL","category":"administrative","verification":"manual","details":"Not aware"}},"total_possible":120,"critical_failures":2,"assessment_tier":"full"}'
    );