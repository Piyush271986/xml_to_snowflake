-- =============================================================================
-- LAYER 1 (RAW): NORMAL TABLE + ADLS SNOWPIPE (analytics v0.1.0) [Schema: RAW]
-- Record XPath: /ASSETS/ASSET/BND_CORP (loaded record-by-record into separate VARIANT rows)
-- Preserved Top-Level Tags: /ASSETS/@ASOF_DATE, /ASSETS/@CREATE_DATE, /ASSETS/@RECORDS
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS RAW;

CREATE TABLE IF NOT EXISTS RAW.raw_analytics (
    _file_name          VARCHAR(512)    NOT NULL,
    _file_sha256        VARCHAR(64)     NOT NULL,
    _record_index       NUMBER(18,0)    NOT NULL DEFAULT 0,
    _source_system      VARCHAR(128)    NOT NULL,
    _ingestion_ts            TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    raw_xml             VARIANT         NOT NULL,
    CONSTRAINT uq_raw_analytics_file_hash UNIQUE (_file_name, _file_sha256, _record_index)
);

-- Snowpipe: ADLS to RAW Normal Table (Created PAUSED during onboarding; enabled at Stage 9 Go-Live)
CREATE PIPE IF NOT EXISTS RAW.pipe_analytics
    AUTO_INGEST = TRUE
    COMMENT = 'Snowpipe for analytics XML ingestion from ADLS into RAW.raw_analytics (record path: /ASSETS/ASSET/BND_CORP)'
AS
COPY INTO RAW.raw_analytics (_file_name, _file_sha256, _source_system, raw_xml)
FROM (
    SELECT
        METADATA$FILENAME,
        METADATA$FILE_CONTENT_KEY,
        'analytics',
        $1
    FROM @RAW.ADLS_XML_STAGE/analytics/
)
FILE_FORMAT = (TYPE = 'XML' STRIP_OUTER_ELEMENT = TRUE);

ALTER PIPE IF EXISTS RAW.pipe_analytics SET PIPE_EXECUTION_PAUSED = TRUE;
