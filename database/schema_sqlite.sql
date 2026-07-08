-- ===========================================================================
--  Zambia Digital Hygiene Assessment Tool — SQLite schema (WEB PORTAL)
-- ===========================================================================
--  This is the self-contained SQLite counterpart to init.sql (MySQL).
--
--  The web portal (src/web/app.py) uses SQLite by default and only switches
--  to MySQL/Postgres when DATABASE_URL or MySQL credentials are configured.
--  When running on SQLite the database lives at:  instance/digital_hygiene.db
--
--  You normally do NOT need to run this file by hand — the schema is created
--  automatically by:
--        python cli.py init-db        (SQLAlchemy create_all + admin user)
--  or:   python database/setup_sqlite.py
--
--  It is provided here as the authoritative, human-readable reference schema
--  (generated to match the SQLAlchemy models exactly) and for tooling that
--  prefers raw SQL.  Table definitions mirror the ORM models in src/web/app.py
--  and include the two tables that were missing from init.sql:
--  `remediations` and `assessment_requests`.
--
--  Apply with:   sqlite3 instance/digital_hygiene.db < database/schema_sqlite.sql
-- ===========================================================================

PRAGMA foreign_keys = ON;

-- ── Businesses ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS businesses (
    id                  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name                VARCHAR(255) NOT NULL,
    registration_number VARCHAR(50),
    address             TEXT,
    contact_person      VARCHAR(100),
    contact_email       VARCHAR(100),
    contact_phone       VARCHAR(20),
    industry            VARCHAR(100),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (registration_number)
);

-- ── Users (authentication + MFA) ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    username      VARCHAR(80) NOT NULL,
    email         VARCHAR(120) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20) NOT NULL DEFAULT 'assessor',   -- admin | assessor | viewer | business_owner
    is_active     BOOLEAN DEFAULT 1,
    mfa_secret    VARCHAR(32),
    mfa_enabled   BOOLEAN DEFAULT 0,
    business_id   INTEGER,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (username),
    UNIQUE (email),
    FOREIGN KEY (business_id) REFERENCES businesses (id)
);

-- ── Assessments (15-control framework results, JSON payloads) ───────────────
CREATE TABLE IF NOT EXISTS assessments (
    id                  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    business_id         INTEGER NOT NULL,
    assessor_id         INTEGER,
    assessment_date     DATETIME DEFAULT CURRENT_TIMESTAMP,
    system_info         JSON,
    controls_results    JSON NOT NULL,
    total_score         INTEGER NOT NULL,
    certification_level VARCHAR(20) NOT NULL,                -- GOLD | SILVER | BRONZE | NOT CERTIFIED
    recommendations     JSON,
    status              VARCHAR(20) NOT NULL DEFAULT 'completed',  -- draft | completed | certified
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES businesses (id) ON DELETE CASCADE,
    FOREIGN KEY (assessor_id) REFERENCES users (id) ON DELETE SET NULL
);

-- ── Assessment requests (booking / assignment workflow) ─────────────────────
CREATE TABLE IF NOT EXISTS assessment_requests (
    id              INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    business_id     INTEGER NOT NULL,
    requested_by    INTEGER NOT NULL,
    assigned_to     INTEGER,
    assessment_tier VARCHAR(20),
    status          VARCHAR(20) DEFAULT 'pending',
    notes           TEXT,
    preferred_date  DATE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id)  REFERENCES businesses (id),
    FOREIGN KEY (requested_by) REFERENCES users (id),
    FOREIGN KEY (assigned_to)  REFERENCES users (id)
);

-- ── Certificates ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS certificates (
    id                 INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    assessment_id      INTEGER NOT NULL,
    certificate_number VARCHAR(50) NOT NULL,
    issued_date        DATE,
    expiry_date        DATE,
    certificate_data   JSON,
    is_active          BOOLEAN DEFAULT 1,
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (certificate_number),
    FOREIGN KEY (assessment_id) REFERENCES assessments (id) ON DELETE CASCADE
);

-- ── Remediations (tracked fixes per control) ────────────────────────────────
CREATE TABLE IF NOT EXISTS remediations (
    id            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    control_id    VARCHAR(10) NOT NULL,
    control_name  VARCHAR(100),
    status        VARCHAR(20) DEFAULT 'open',      -- open | in_progress | resolved
    priority      VARCHAR(10) DEFAULT 'medium',    -- low | medium | high | critical
    assigned_to   INTEGER,
    notes         TEXT,
    due_date      DATE,
    resolved_at   DATETIME,
    created_by    INTEGER NOT NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments (id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to)   REFERENCES users (id),
    FOREIGN KEY (created_by)    REFERENCES users (id)
);

-- ── Audit logs ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER,
    action        VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id   INTEGER,
    details       JSON,
    ip_address    VARCHAR(45),
    user_agent    TEXT,
    timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- ── Indexes ────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_assessments_business_id  ON assessments (business_id);
CREATE INDEX IF NOT EXISTS idx_assessments_date         ON assessments (assessment_date);
CREATE INDEX IF NOT EXISTS idx_assessments_level        ON assessments (certification_level);
CREATE INDEX IF NOT EXISTS idx_requests_business_id     ON assessment_requests (business_id);
CREATE INDEX IF NOT EXISTS idx_requests_status          ON assessment_requests (status);
CREATE INDEX IF NOT EXISTS idx_certificates_assessment  ON certificates (assessment_id);
CREATE INDEX IF NOT EXISTS idx_remediations_assessment  ON remediations (assessment_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp     ON audit_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user          ON audit_logs (user_id);

-- ===========================================================================
--  Seed data (optional)
-- ===========================================================================
--  NOTE ON THE ADMIN USER:
--  We deliberately do NOT seed a login with a hard-coded password here — a
--  fixed default password is a security risk (and would not match the app's
--  Werkzeug password hashing). Create the admin account with:
--
--        python cli.py init-db
--
--  which generates a strong random password (or honours ADMIN_DEFAULT_PASSWORD)
--  and prints it once.
--
--  The sample businesses below are harmless demo data — remove this block for
--  a clean production database.
INSERT OR IGNORE INTO businesses (id, name, registration_number, industry) VALUES
    (1, 'Zambia Tech Solutions Ltd',   'ZT2024001', 'Information Technology'),
    (2, 'Lusaka Manufacturing Co.',    'LM2024002', 'Manufacturing'),
    (3, 'Copperbelt Mining Supplies',  'CM2024003', 'Mining');
