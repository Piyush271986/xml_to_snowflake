-- =============================================================================
-- OPERATIONAL TABLES: O3 QUARANTINE & O1 DQ RESULTS [Schema: OPS]
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS OPS;

CREATE TABLE IF NOT EXISTS OPS.quarantine_orders (
    quarantine_id       VARCHAR(64)     DEFAULT UUID_STRING(),
    dataset             VARCHAR(128)    NOT NULL,
    file_name           VARCHAR(512)    NOT NULL,
    file_sha256         VARCHAR(64)     NOT NULL,
    gate_id             VARCHAR(8)      NOT NULL, -- G1, G2, G3
    failure_reason      VARCHAR(2048)   NOT NULL,
    raw_payload         VARIANT         NULL,
    quarantined_at      TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    replayed            BOOLEAN         DEFAULT FALSE,
    replayed_at         TIMESTAMP_NTZ   NULL
);

CREATE TABLE IF NOT EXISTS OPS.dq_results_orders (
    check_id            VARCHAR(64)     DEFAULT UUID_STRING(),
    dataset             VARCHAR(128)    NOT NULL,
    file_name           VARCHAR(512)    NOT NULL,
    gate_id             VARCHAR(8)      NOT NULL,
    check_name          VARCHAR(256)    NOT NULL,
    passed              BOOLEAN         NOT NULL,
    details             VARCHAR(2048)   NULL,
    checked_at          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
);
