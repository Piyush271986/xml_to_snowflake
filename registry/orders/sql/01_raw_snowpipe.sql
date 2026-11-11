-- =============================================================================
-- LAYER 1 (RAW): NORMAL TABLE + ADLS SNOWPIPE (orders v0.1.0) [Schema: RAW]
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS RAW;

CREATE TABLE IF NOT EXISTS RAW.raw_orders (
    _file_name          VARCHAR(512)    NOT NULL,
    _file_sha256        VARCHAR(64)     NOT NULL,
    _source_system      VARCHAR(128)    NOT NULL,
    _load_ts            TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    raw_xml             VARIANT         NOT NULL,
    CONSTRAINT uq_raw_orders_file_hash UNIQUE (_file_name, _file_sha256)
);

-- Snowpipe: ADLS to RAW Normal Table (Created PAUSED during onboarding; enabled at Stage 9 Go-Live)
CREATE PIPE IF NOT EXISTS RAW.pipe_orders
    AUTO_INGEST = TRUE
    COMMENT = 'Snowpipe for orders XML ingestion from ADLS into RAW.raw_orders'
AS
COPY INTO RAW.raw_orders (_file_name, _file_sha256, _source_system, raw_xml)
FROM (
    SELECT
        METADATA$FILENAME,
        METADATA$FILE_CONTENT_KEY,
        'orders',
        $1
    FROM @RAW.ADLS_XML_STAGE/orders/
)
FILE_FORMAT = (TYPE = 'XML' STRIP_OUTER_ELEMENT = FALSE);

ALTER PIPE IF EXISTS RAW.pipe_orders SET PIPE_EXECUTION_PAUSED = TRUE;
