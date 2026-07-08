-- ===========================================================================
--  Zambia Digital Hygiene — SQLite schema (DESKTOP LOCAL STORE)
-- ===========================================================================
--  This is the schema for the *self-contained desktop application's* local
--  database. The Windows app (ZambiaDigitalHygiene.exe) stores everything
--  here — it needs no server and no configuration.
--
--  Location (created automatically at runtime by src/utils/local_db.py):
--        Windows :  %APPDATA%\ZambiaDigitalHygiene\history.db
--        Linux   :  ~/.local/share/ZambiaDigitalHygiene/history.db
--
--  These tables are created on demand by local_db.py (init_db / the
--  _ensure_*_table helpers), so you never have to run this file — it is
--  provided as the reference schema for the self-contained local store.
--
--  This is a SEPARATE database from the web portal (schema_sqlite.sql); do not
--  apply both files to the same .db file (the `assessments` table differs).
-- ===========================================================================

-- ── Completed assessments (full result JSON in `payload`) ───────────────────
CREATE TABLE IF NOT EXISTS assessments (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    saved_at TEXT    NOT NULL,
    biz_name TEXT    NOT NULL,
    biz_id   TEXT    NOT NULL,
    province TEXT,
    industry TEXT,
    score    INTEGER NOT NULL,
    total    INTEGER NOT NULL,
    pct      INTEGER NOT NULL,
    tier     TEXT    NOT NULL,
    payload  TEXT    NOT NULL          -- full AssessmentResults as JSON
);

-- ── Local sign-in credentials (single operator; password is hashed) ─────────
CREATE TABLE IF NOT EXISTS credentials (
    key   TEXT PRIMARY KEY,            -- 'username' | 'password_hash'
    value TEXT NOT NULL
);

-- ── Windows agent reports (assessment + hardening + readiness JSON) ─────────
CREATE TABLE IF NOT EXISTS agent_reports (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname     TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    payload      TEXT NOT NULL         -- full node report as JSON
);

-- ── Fleet scan reports (distributed multi-node results) ─────────────────────
CREATE TABLE IF NOT EXISTS fleet_reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scanned_at  TEXT    NOT NULL,
    fleet_grade TEXT    NOT NULL,       -- HARDENED | NEEDS ATTENTION | AT RISK | INCOMPLETE | NO DATA
    total_nodes INTEGER NOT NULL,
    online      INTEGER NOT NULL,
    payload     TEXT    NOT NULL        -- full FleetReport as JSON
);

-- ── Key/value settings (e.g. reassessment reminder date) ────────────────────
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
