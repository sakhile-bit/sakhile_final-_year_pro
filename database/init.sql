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
        role ENUM ('admin', 'assessor', 'viewer') DEFAULT 'assessor',
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
        certification_level ENUM ('GOLD', 'SILVER', 'BRONZE', 'NOT_CERTIFIED') NOT NULL,
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

-- Insert sample assessment data
INSERT IGNORE INTO assessments (
    business_id,
    total_score,
    certification_level,
    controls_results
)
VALUES
    (
        1,
        45,
        'GOLD',
        '{"os_updates": {"score": 10, "status": "PASS"}, "antivirus": {"score": 15, "status": "PASS"}, "firewall": {"score": 10, "status": "PASS"}, "password_policy": {"score": 7, "status": "WARNING"}, "backup_system": {"score": 3, "status": "WARNING"}}'
    ),
    (
        2,
        32,
        'SILVER',
        '{"os_updates": {"score": 8, "status": "WARNING"}, "antivirus": {"score": 12, "status": "PASS"}, "firewall": {"score": 5, "status": "WARNING"}, "password_policy": {"score": 5, "status": "FAIL"}, "backup_system": {"score": 2, "status": "FAIL"}}'
    ),
    (
        3,
        28,
        'BRONZE',
        '{"os_updates": {"score": 5, "status": "WARNING"}, "antivirus": {"score": 10, "status": "PASS"}, "firewall": {"score": 8, "status": "PASS"}, "password_policy": {"score": 3, "status": "FAIL"}, "backup_system": {"score": 2, "status": "FAIL"}}'
    );