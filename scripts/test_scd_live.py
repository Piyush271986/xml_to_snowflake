import os
from pathlib import Path
from src.snowflake_client import SnowflakeConnectionConfig, connect_snowflake_external_browser

cfg = SnowflakeConnectionConfig(
    mode="externalbrowser",
    authenticator="snowflake",
    account="YLDULXM-DC69211",
    user="welcometopiyush",
    password=os.environ.get("SNOWFLAKE_PASSWORD", "Mahiraa@2016"),
    role="ACCOUNTADMIN",
    warehouse="COMPUTE_WH",
    database="ENTERPRISE_DW",
    schema_raw="RAW",
    schema_staging="STAGING",
    schema_curated="CURATED",
    schema_ops="OPS",
    adls_stage="@RAW.ADLS_XML_STAGE",
)

conn = connect_snowflake_external_browser(cfg)
cur = conn.cursor()

print("=== 1. BASELINE CHECK ===")
cur.execute("SELECT count(*) FROM RAW.raw_analytics")
print("RAW count:", cur.fetchone()[0])
cur.execute("SELECT count(*) FROM CURATED.curated_analytics")
print("CURATED total count:", cur.fetchone()[0])

cur.execute("""
SELECT cusip, coupon_fix, issue_price, _source_file 
FROM CURATED.curated_analytics 
WHERE cusip IS NOT NULL AND coupon_fix IS NOT NULL
LIMIT 1
""")
target_cusip, old_coupon, old_price, orig_file = cur.fetchone()
print(f"Tracking target CUSIP: {target_cusip} (old coupon: {old_coupon}, old price: {old_price})")

print("\n=== 2. TEST A: INGEST EXACT SAME FILE (Duplicate Drop) ===")
# Dropping the identical file again with an updated timestamp
cur.execute("""
INSERT INTO RAW.raw_analytics (_file_name, _file_sha256, _record_index, _source_system, _ingestion_ts, raw_xml)
SELECT _file_name, _file_sha256, _record_index, _source_system, DATEADD('minute', 1, _ingestion_ts), raw_xml
FROM RAW.raw_analytics
WHERE XMLGET(raw_xml, 'CUSIP'):"$"::VARCHAR = %s
""", (target_cusip,))
print("Inserted duplicate row into RAW.raw_analytics.")

cur.execute("ALTER DYNAMIC TABLE STAGING.staging_analytics REFRESH")
cur.execute("ALTER DYNAMIC TABLE CURATED.curated_analytics REFRESH")

cur.execute("""
SELECT count(*), count(DISTINCT _row_hash) 
FROM CURATED.curated_analytics 
WHERE cusip = %s
""", (target_cusip,))
cnt, distinct_hashes = cur.fetchone()
print(f"Result for duplicate drop on {target_cusip}: rows in CURATED = {cnt}, distinct versions = {distinct_hashes}")
if cnt == 1:
    print("SUCCESS: Duplicate drop with identical payload did NOT create a phantom SCD2 row!")

print("\n=== 3. TEST B: INGEST UPDATED FILE (SCD Type 2 Version Trigger) ===")
# Ingest same CUSIP with modified COUPON_FIX value = 8.7500
cur.execute("""
INSERT INTO RAW.raw_analytics (_file_name, _file_sha256, _record_index, _source_system, _ingestion_ts, raw_xml)
SELECT 
    'analytics_update_v2.xml',
    'sha256_v2_new_payload_hash',
    _record_index,
    _source_system,
    DATEADD('hour', 3, _ingestion_ts),
    PARSE_XML(REGEXP_REPLACE(TO_VARCHAR(raw_xml), '<COUPON_FIX>[^<]+</COUPON_FIX>', '<COUPON_FIX>8.7500</COUPON_FIX>'))
FROM RAW.raw_analytics
WHERE XMLGET(raw_xml, 'CUSIP'):"$"::VARCHAR = %s
LIMIT 1
""", (target_cusip,))
print("Inserted modified record with new coupon rate 8.7500 into RAW.raw_analytics.")

cur.execute("ALTER DYNAMIC TABLE STAGING.staging_analytics REFRESH")
cur.execute("ALTER DYNAMIC TABLE CURATED.curated_analytics REFRESH")

cur.execute("""
SELECT 
    cusip,
    coupon_fix,
    valid_start_time,
    valid_end_time,
    is_current,
    _source_file
FROM CURATED.curated_analytics
WHERE cusip = %s
ORDER BY valid_start_time ASC
""", (target_cusip,))

versions = cur.fetchall()
print(f"\nSCD Type 2 Timeline for CUSIP '{target_cusip}':")
for v in versions:
    print(f"  - Version | Coupon: {v[1]} | ValidStart: {v[2]} | ValidEnd: {v[3]} | IsCurrent: {v[4]} | SourceFile: {v[5]}")

cur.close()
conn.close()
