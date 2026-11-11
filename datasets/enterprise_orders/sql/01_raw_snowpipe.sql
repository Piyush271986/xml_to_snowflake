-- =============================================================================
-- LAYER 1 (RAW): NORMAL TABLE + ADLS SNOWPIPE (enterprise_orders v0.1.0)
-- =============================================================================

CREATE TABLE IF NOT EXISTS raw_enterprise_orders (
    _file_name          VARCHAR(512)    NOT NULL,
    _file_sha256        VARCHAR(64)     NOT NULL,
    _source_system      VARCHAR(128)    NOT NULL,
    _load_ts            TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    raw_xml             VARIANT         NOT NULL,
    CONSTRAINT uq_raw_enterprise_orders_file_hash UNIQUE (_file_name, _file_sha256)
);

-- Snowpipe: ADLS to RAW Normal Table (Created PAUSED during onboarding; enabled at Stage 9 Go-Live)
CREATE PIPE IF NOT EXISTS pipe_enterprise_orders
    AUTO_INGEST = TRUE
    COMMENT = 'Snowpipe for enterprise_orders XML ingestion from ADLS into raw_enterprise_orders'
AS
COPY INTO raw_enterprise_orders (_file_name, _file_sha256, _source_system, raw_xml)
FROM (
    SELECT
        METADATA$FILENAME,
        METADATA$FILE_CONTENT_KEY,
        'enterprise_orders',
        $1
    FROM @RAW.ADLS_XML_STAGE/enterprise_orders/
)
FILE_FORMAT = (TYPE = 'XML' STRIP_OUTER_ELEMENT = FALSE);

ALTER PIPE IF EXISTS pipe_enterprise_orders SET PIPE_EXECUTION_PAUSED = TRUE;
