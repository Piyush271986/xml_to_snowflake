-- =============================================================================
-- AUTO-GENERATED SNOWFLAKE DDL FROM C4 REGISTRY: orders (version 0.1.0)
-- Source: sample_inference | Root XML Element: /Order
-- =============================================================================

-- 1. D2: IMMUTABLE RAW LAYER (VARIANT + FILE METADATA)
CREATE TABLE IF NOT EXISTS raw_orders (
    _file_name          VARCHAR(512)    NOT NULL,
    _file_sha256        VARCHAR(64)     NOT NULL,
    _source_system      VARCHAR(128)    NOT NULL,
    _load_ts            TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    raw_xml             VARIANT         NOT NULL,
    CONSTRAINT uq_raw_orders_file_hash UNIQUE (_file_name, _file_sha256)
);

-- Snowpipe (Created PAUSED during onboarding; enabled at Stage 9 Go-Live)
CREATE PIPE IF NOT EXISTS pipe_orders
    AUTO_INGEST = TRUE
    COMMENT = 'Snowpipe for orders XML ingestion from ADLS'
AS
COPY INTO raw_orders (_file_name, _file_sha256, _source_system, raw_xml)
FROM (
    SELECT
        METADATA$FILENAME,
        METADATA$FILE_CONTENT_KEY,
        'orders',
        $1
    FROM @RAW.ADLS_XML_STAGE/orders/
)
FILE_FORMAT = (TYPE = 'XML' STRIP_OUTER_ELEMENT = FALSE);

ALTER PIPE IF EXISTS pipe_orders SET PIPE_EXECUTION_PAUSED = TRUE;

-- Stream on Raw Table for incremental D2 -> D3 processing
CREATE STREAM IF NOT EXISTS stream_raw_orders
    ON TABLE raw_orders
    APPEND_ONLY = TRUE;

-- 2. D3: TYPED STAGING TABLE (LATERAL FLATTEN)
CREATE TABLE IF NOT EXISTS staging_orders (
    currency_code                  VARCHAR          NULL,
    order_id                       NUMBER(18,0)     NOT NULL,
    customer_id                    VARCHAR          NULL,
    order_date                     DATE             NULL,
    order_timestamp                TIMESTAMP_NTZ    NULL,
    is_expedited                   BOOLEAN          NULL,
    total_amount                   NUMBER(18,4)     NULL,
    discount_amount                NUMBER(18,4)     NULL,
    shipping_notes                 VARCHAR          NULL,
    line_item_product_code         VARCHAR          NOT NULL,
    line_item_quantity             NUMBER(18,0)     NULL,
    line_item_unit_price           NUMBER(18,4)     NULL,
    _file_name          VARCHAR(512)    NOT NULL,
    _file_sha256        VARCHAR(64)     NOT NULL,
    _staged_ts          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
);

-- Task to flatten XML from Stream into Typed Staging
CREATE OR REPLACE TASK task_flatten_orders
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('stream_raw_orders')
AS
INSERT INTO staging_orders (
    currency_code, order_id, customer_id, order_date, order_timestamp, is_expedited, total_amount, discount_amount, shipping_notes, line_item_product_code, line_item_quantity, line_item_unit_price,
    _file_name,
    _file_sha256
)
SELECT
    raw_xml:"@currency"::VARCHAR AS currency_code,
    TRY_TO_NUMBER(XMLGET(raw_xml, 'OrderId'):"$"::VARCHAR, 18, 0) AS order_id,
    XMLGET(raw_xml, 'CustomerId'):"$"::VARCHAR AS customer_id,
    TRY_TO_DATE(XMLGET(raw_xml, 'OrderDate'):"$"::VARCHAR) AS order_date,
    TRY_TO_TIMESTAMP_NTZ(XMLGET(raw_xml, 'OrderTimestamp'):"$"::VARCHAR) AS order_timestamp,
    TRY_TO_BOOLEAN(XMLGET(raw_xml, 'IsExpedited'):"$"::VARCHAR) AS is_expedited,
    TRY_TO_DECIMAL(XMLGET(raw_xml, 'TotalAmount'):"$"::VARCHAR, 18, 4) AS total_amount,
    TRY_TO_DECIMAL(XMLGET(raw_xml, 'DiscountAmount'):"$"::VARCHAR, 18, 4) AS discount_amount,
    XMLGET(raw_xml, 'ShippingNotes'):"$"::VARCHAR AS shipping_notes,
    XMLGET(item.value, 'ProductCode'):"$"::VARCHAR AS line_item_product_code,
    TRY_TO_NUMBER(XMLGET(item.value, 'Quantity'):"$"::VARCHAR, 18, 0) AS line_item_quantity,
    TRY_TO_DECIMAL(XMLGET(item.value, 'UnitPrice'):"$"::VARCHAR, 18, 4) AS line_item_unit_price,
    r._file_name,
    r._file_sha256
FROM stream_raw_orders r,
    LATERAL FLATTEN(INPUT => XMLGET(r.raw_xml, 'LineItems'):'$') item
WHERE GET(item.value, '@') = 'LineItem';

-- 3. D4: CURATED DATASET WITH CDC SCD TYPE 2
CREATE TABLE IF NOT EXISTS curated_orders (
    currency_code                  VARCHAR          NULL,
    order_id                       NUMBER(18,0)     NOT NULL,
    customer_id                    VARCHAR          NULL,
    order_date                     DATE             NULL,
    order_timestamp                TIMESTAMP_NTZ    NULL,
    is_expedited                   BOOLEAN          NULL,
    total_amount                   NUMBER(18,4)     NULL,
    discount_amount                NUMBER(18,4)     NULL,
    shipping_notes                 VARCHAR          NULL,
    line_item_product_code         VARCHAR          NOT NULL,
    line_item_quantity             NUMBER(18,0)     NULL,
    line_item_unit_price           NUMBER(18,4)     NULL,
    _row_hash           VARCHAR(64)     NOT NULL,
    is_valid_start      TIMESTAMP_NTZ   NOT NULL,
    is_valid_end        TIMESTAMP_NTZ   NULL,
    is_current          BOOLEAN         NOT NULL DEFAULT TRUE,
    system_start_time   TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    system_end_time     TIMESTAMP_NTZ   NULL,
    _source_file        VARCHAR(512)    NOT NULL
);

-- Task to apply SCD Type 2 (close changed current rows, insert new version)
CREATE OR REPLACE TASK task_scd2_orders
    WAREHOUSE = COMPUTE_WH
    AFTER task_flatten_orders
AS
BEGIN
    -- Step A: Close existing current rows where non-key attributes changed
    UPDATE curated_orders tgt
    SET
        tgt.is_valid_end = CURRENT_TIMESTAMP(),
        tgt.is_current = FALSE,
        tgt.system_end_time = CURRENT_TIMESTAMP()
    FROM (
        SELECT
            currency_code, order_id, customer_id, order_date, order_timestamp, is_expedited, total_amount, discount_amount, shipping_notes, line_item_product_code, line_item_quantity, line_item_unit_price,
            SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(currency_code), ''), COALESCE(TO_VARCHAR(customer_id), ''), COALESCE(TO_VARCHAR(order_date), ''), COALESCE(TO_VARCHAR(order_timestamp), ''), COALESCE(TO_VARCHAR(is_expedited), ''), COALESCE(TO_VARCHAR(total_amount), ''), COALESCE(TO_VARCHAR(discount_amount), ''), COALESCE(TO_VARCHAR(shipping_notes), ''), COALESCE(TO_VARCHAR(line_item_quantity), ''), COALESCE(TO_VARCHAR(line_item_unit_price), '')), 256) AS _row_hash
        FROM staging_orders
    ) src
    WHERE tgt.order_id = src.order_id AND tgt.line_item_product_code = src.line_item_product_code
      AND tgt.is_current = TRUE
      AND tgt._row_hash <> src._row_hash;

    -- Step B: Insert brand-new keys or newly versioned rows
    INSERT INTO curated_orders (
        currency_code, order_id, customer_id, order_date, order_timestamp, is_expedited, total_amount, discount_amount, shipping_notes, line_item_product_code, line_item_quantity, line_item_unit_price,
        _row_hash,
        is_valid_start,
        is_valid_end,
        is_current,
        system_start_time,
        system_end_time,
        _source_file
    )
    SELECT
        src.currency_code, src.order_id, src.customer_id, src.order_date, src.order_timestamp, src.is_expedited, src.total_amount, src.discount_amount, src.shipping_notes, src.line_item_product_code, src.line_item_quantity, src.line_item_unit_price,
        src._row_hash,
        CURRENT_TIMESTAMP(),
        NULL,
        TRUE,
        CURRENT_TIMESTAMP(),
        NULL,
        src._file_name
    FROM (
        SELECT
            currency_code, order_id, customer_id, order_date, order_timestamp, is_expedited, total_amount, discount_amount, shipping_notes, line_item_product_code, line_item_quantity, line_item_unit_price,
            _file_name,
            SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(currency_code), ''), COALESCE(TO_VARCHAR(customer_id), ''), COALESCE(TO_VARCHAR(order_date), ''), COALESCE(TO_VARCHAR(order_timestamp), ''), COALESCE(TO_VARCHAR(is_expedited), ''), COALESCE(TO_VARCHAR(total_amount), ''), COALESCE(TO_VARCHAR(discount_amount), ''), COALESCE(TO_VARCHAR(shipping_notes), ''), COALESCE(TO_VARCHAR(line_item_quantity), ''), COALESCE(TO_VARCHAR(line_item_unit_price), '')), 256) AS _row_hash
        FROM staging_orders
    ) src
    LEFT JOIN curated_orders tgt
      ON tgt.order_id = src.order_id AND tgt.line_item_product_code = src.line_item_product_code AND tgt.is_current = TRUE
    WHERE tgt.order_id IS NULL;
END;

-- 4. O3: QUARANTINE TABLE & O1: DQ RESULTS TABLE
CREATE TABLE IF NOT EXISTS quarantine_orders (
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

CREATE TABLE IF NOT EXISTS dq_results_orders (
    check_id            VARCHAR(64)     DEFAULT UUID_STRING(),
    dataset             VARCHAR(128)    NOT NULL,
    file_name           VARCHAR(512)    NOT NULL,
    gate_id             VARCHAR(8)      NOT NULL,
    check_name          VARCHAR(256)    NOT NULL,
    passed              BOOLEAN         NOT NULL,
    details             VARCHAR(2048)   NULL,
    checked_at          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
);
