-- =============================================================================
-- O2 MONITORING ALERTS & O5 SLA DASHBOARD FOR DATASET: orders
-- =============================================================================

-- O5: SLA Dashboard View (Latency, Volume, Quarantine & Drift Trends)
CREATE OR REPLACE VIEW v_sla_dashboard_orders AS
SELECT
    DATE_TRUNC('HOUR', r._load_ts)                          AS load_hour,
    COUNT(DISTINCT r._file_name)                            AS files_ingested,
    COUNT(c.order_id)                     AS curated_active_rows,
    AVG(DATEDIFF('SECOND', r._load_ts, c.system_start_time)) AS avg_e2e_latency_sec,
    (SELECT COUNT(*) FROM quarantine_orders q WHERE q.replayed = FALSE) AS open_quarantine_count
FROM raw_orders r
LEFT JOIN curated_orders c
  ON c._source_file = r._file_name AND c.is_current = TRUE
GROUP BY 1;

-- O2: Freshness Alert Check (fires if no new files within 24h SLA)
SELECT
    'orders' AS dataset,
    DATEDIFF('HOUR', MAX(_load_ts), CURRENT_TIMESTAMP()) AS hours_since_last_load,
    'platform-oncall@enterprise.io' AS alert_owner
FROM raw_orders
HAVING hours_since_last_load > 24;
