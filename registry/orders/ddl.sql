-- =============================================================================
-- AUTO-GENERATED SNOWFLAKE DDL BY STEP 2 DDL GENERATOR AGENT: orders (v0.1.0)
-- Architecture: ADLS -> Snowpipe (RAW) -> STAGE Dynamic Table (STAGING) -> GOLD Dynamic Table (CURATED)
-- =============================================================================

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

-- =============================================================================
-- LAYER 2 (STAGE): ONE DYNAMIC TABLE PER XML ENTITY FROM RAW (orders v0.1.0) [Schema: STAGING]
-- Entities: order, audit_event, line, installment
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS STAGING;

-- Entity `order` (/Order)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_orders
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_orders: root entity order (PK order_pk)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256)) AS order_pk,
    r.raw_xml:"@orderType"::VARCHAR AS order_type,
    TRY_TO_DECIMAL(r.raw_xml:"@version"::VARCHAR, 18, 4) AS version,
    r.raw_xml:"@currency"::VARCHAR AS currency_code,
    r.raw_xml:"@channel"::VARCHAR AS channel,
    r.raw_xml:"@region"::VARCHAR AS region,
    TRY_TO_NUMBER(XMLGET(r.raw_xml, 'OrderId'):"$"::VARCHAR, 18, 0) AS order_id,
    XMLGET(r.raw_xml, 'ExternalPurchaseOrderNumber'):"$"::VARCHAR AS external_purchase_order_number,
    TRY_TO_DATE(XMLGET(r.raw_xml, 'OrderDate'):"$"::VARCHAR) AS order_date,
    TRY_TO_TIMESTAMP_NTZ(XMLGET(r.raw_xml, 'OrderTimestamp'):"$"::VARCHAR) AS order_timestamp,
    XMLGET(r.raw_xml, 'OrderStatus'):"$"::VARCHAR AS order_status,
    TRY_TO_BOOLEAN(XMLGET(r.raw_xml, 'IsExpedited'):"$"::VARCHAR) AS is_expedited,
    TRY_TO_BOOLEAN(XMLGET(r.raw_xml, 'IsBackorderAllowed'):"$"::VARCHAR) AS is_backorder_allowed,
    TRY_TO_NUMBER(XMLGET(r.raw_xml, 'PriorityScore'):"$"::VARCHAR, 18, 0) AS priority_score,
    TRY_TO_DECIMAL(XMLGET(r.raw_xml, 'TotalAmount'):"$"::VARCHAR, 18, 4) AS total_amount,
    TRY_TO_DECIMAL(XMLGET(r.raw_xml, 'DiscountAmount'):"$"::VARCHAR, 18, 4) AS discount_amount,
    TRY_TO_DECIMAL(XMLGET(r.raw_xml, 'TaxAmount'):"$"::VARCHAR, 18, 4) AS tax_amount,
    TRY_TO_DECIMAL(XMLGET(r.raw_xml, 'FreightAmount'):"$"::VARCHAR, 18, 4) AS freight_amount,
    TRY_TO_DECIMAL(XMLGET(r.raw_xml, 'NetPayableAmount'):"$"::VARCHAR, 18, 4) AS net_payable_amount,
    XMLGET(r.raw_xml, 'ShippingNotes'):"$"::VARCHAR AS shipping_notes,
    XMLGET(XMLGET(r.raw_xml, 'Header'), 'SourceSystem'):"$"::VARCHAR AS source_system,
    XMLGET(XMLGET(r.raw_xml, 'Header'), 'SalesOrgCode'):"$"::VARCHAR AS sales_org_code,
    TRY_TO_NUMBER(XMLGET(XMLGET(r.raw_xml, 'Header'), 'DistributionChannel'):"$"::VARCHAR, 18, 0) AS distribution_channel,
    TRY_TO_NUMBER(XMLGET(XMLGET(r.raw_xml, 'Header'), 'DivisionCode'):"$"::VARCHAR, 18, 0) AS division_code,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'Header'), 'ContractReference'), 'MasterAgreementId'):"$"::VARCHAR AS master_agreement_id,
    TRY_TO_DATE(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Header'), 'ContractReference'), 'ContractEffectiveDate'):"$"::VARCHAR) AS contract_effective_date,
    TRY_TO_DATE(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Header'), 'ContractReference'), 'ContractExpirationDate'):"$"::VARCHAR) AS contract_expiration_date,
    TRY_TO_DECIMAL(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Header'), 'ContractReference'), 'DiscountTierPercentage'):"$"::VARCHAR, 18, 4) AS discount_tier_percentage,
    TRY_TO_BOOLEAN(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Header'), 'ContractReference'), 'IsAutoRenew'):"$"::VARCHAR) AS is_auto_renew,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'Header'), 'SalesRepresentative'), 'RepId'):"$"::VARCHAR AS rep_id,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'Header'), 'SalesRepresentative'), 'RepName'):"$"::VARCHAR AS rep_name,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'Header'), 'SalesRepresentative'), 'RepEmail'):"$"::VARCHAR AS rep_email,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'Header'), 'SalesRepresentative'), 'TerritoryCode'):"$"::VARCHAR AS territory_code,
    TRY_TO_DECIMAL(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Header'), 'SalesRepresentative'), 'CommissionRate'):"$"::VARCHAR, 18, 4) AS commission_rate,
    XMLGET(r.raw_xml, 'Customer'):"@customerTier"::VARCHAR AS customer_customer_tier,
    TRY_TO_BOOLEAN(XMLGET(r.raw_xml, 'Customer'):"@taxExempt"::VARCHAR) AS customer_tax_exempt,
    TRY_TO_BOOLEAN(XMLGET(r.raw_xml, 'Customer'):"@kycVerified"::VARCHAR) AS customer_kyc_verified,
    XMLGET(XMLGET(r.raw_xml, 'Customer'), 'CustomerId'):"$"::VARCHAR AS customer_id,
    XMLGET(XMLGET(r.raw_xml, 'Customer'), 'AccountNumber'):"$"::VARCHAR AS account_number,
    XMLGET(XMLGET(r.raw_xml, 'Customer'), 'CompanyName'):"$"::VARCHAR AS company_name,
    TRY_TO_NUMBER(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'DunsNumber'):"$"::VARCHAR, 18, 0) AS duns_number,
    XMLGET(XMLGET(r.raw_xml, 'Customer'), 'TaxRegistrationNumber'):"$"::VARCHAR AS tax_registration_number,
    TRY_TO_DATE(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'AccountCreatedDate'):"$"::VARCHAR) AS account_created_date,
    TRY_TO_DECIMAL(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'CreditProfile'), 'CreditLimit'):"$"::VARCHAR, 18, 4) AS credit_limit,
    TRY_TO_DECIMAL(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'CreditProfile'), 'CurrentBalance'):"$"::VARCHAR, 18, 4) AS current_balance,
    TRY_TO_DECIMAL(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'CreditProfile'), 'AvailableCredit'):"$"::VARCHAR, 18, 4) AS available_credit,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'CreditProfile'), 'RiskRating'):"$"::VARCHAR AS risk_rating,
    TRY_TO_NUMBER(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'CreditProfile'), 'PaymentTermsDays'):"$"::VARCHAR, 18, 0) AS payment_terms_days,
    TRY_TO_BOOLEAN(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'CreditProfile'), 'IsCreditHold'):"$"::VARCHAR) AS is_credit_hold,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Contacts'), 'PrimaryContact'), 'ContactId'):"$"::VARCHAR AS primary_contact_contact_id,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Contacts'), 'PrimaryContact'), 'FullName'):"$"::VARCHAR AS primary_contact_full_name,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Contacts'), 'PrimaryContact'), 'JobTitle'):"$"::VARCHAR AS primary_contact_job_title,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Contacts'), 'PrimaryContact'), 'Email'):"$"::VARCHAR AS primary_contact_email,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Contacts'), 'PrimaryContact'), 'Phone'):"$"::VARCHAR AS primary_contact_phone,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Contacts'), 'AccountsPayableContact'), 'ContactId'):"$"::VARCHAR AS accounts_payable_contact_contact_id,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Contacts'), 'AccountsPayableContact'), 'FullName'):"$"::VARCHAR AS accounts_payable_contact_full_name,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Contacts'), 'AccountsPayableContact'), 'JobTitle'):"$"::VARCHAR AS accounts_payable_contact_job_title,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Contacts'), 'AccountsPayableContact'), 'Email'):"$"::VARCHAR AS accounts_payable_contact_email,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Contacts'), 'AccountsPayableContact'), 'Phone'):"$"::VARCHAR AS accounts_payable_contact_phone,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'BillingAddress'):"@addressType"::VARCHAR AS billing_address_address_type,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'BillingAddress'), 'AddressId'):"$"::VARCHAR AS billing_address_address_id,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'BillingAddress'), 'AttentionLine'):"$"::VARCHAR AS billing_address_attention_line,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'BillingAddress'), 'StreetLine1'):"$"::VARCHAR AS billing_address_street_line1,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'BillingAddress'), 'StreetLine2'):"$"::VARCHAR AS billing_address_street_line2,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'BillingAddress'), 'City'):"$"::VARCHAR AS billing_address_city,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'BillingAddress'), 'StateProvince'):"$"::VARCHAR AS billing_address_state_province,
    TRY_TO_NUMBER(XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'BillingAddress'), 'PostalCode'):"$"::VARCHAR, 18, 0) AS billing_address_postal_code,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'BillingAddress'), 'CountryCode'):"$"::VARCHAR AS billing_address_country_code,
    TRY_TO_DECIMAL(XMLGET(XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'BillingAddress'), 'GeoCoordinates'), 'Latitude'):"$"::VARCHAR, 18, 4) AS geo_coordinates_latitude,
    TRY_TO_DECIMAL(XMLGET(XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'BillingAddress'), 'GeoCoordinates'), 'Longitude'):"$"::VARCHAR, 18, 4) AS geo_coordinates_longitude,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'):"@addressType"::VARCHAR AS shipping_address_address_type,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'AddressId'):"$"::VARCHAR AS shipping_address_address_id,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'FacilityName'):"$"::VARCHAR AS facility_name,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'AttentionLine'):"$"::VARCHAR AS shipping_address_attention_line,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'StreetLine1'):"$"::VARCHAR AS shipping_address_street_line1,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'StreetLine2'):"$"::VARCHAR AS shipping_address_street_line2,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'City'):"$"::VARCHAR AS shipping_address_city,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'StateProvince'):"$"::VARCHAR AS shipping_address_state_province,
    TRY_TO_NUMBER(XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'PostalCode'):"$"::VARCHAR, 18, 0) AS shipping_address_postal_code,
    XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'CountryCode'):"$"::VARCHAR AS shipping_address_country_code,
    TRY_TO_BOOLEAN(XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'IsResidential'):"$"::VARCHAR) AS is_residential,
    TRY_TO_BOOLEAN(XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'RequiresLiftgate'):"$"::VARCHAR) AS requires_liftgate,
    TRY_TO_BOOLEAN(XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'RequiresInsideDelivery'):"$"::VARCHAR) AS requires_inside_delivery,
    TRY_TO_DECIMAL(XMLGET(XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'GeoCoordinates'), 'Latitude'):"$"::VARCHAR, 18, 4) AS geo_coordinates_latitude_2,
    TRY_TO_DECIMAL(XMLGET(XMLGET(XMLGET(XMLGET(XMLGET(r.raw_xml, 'Customer'), 'Addresses'), 'ShippingAddress'), 'GeoCoordinates'), 'Longitude'):"$"::VARCHAR, 18, 4) AS geo_coordinates_longitude_2,
    TRY_TO_DATE(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'RequestedDeliveryDate'):"$"::VARCHAR) AS requested_delivery_date,
    TRY_TO_DATE(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'PromisedShipDate'):"$"::VARCHAR) AS promised_ship_date,
    XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'Incoterms'):"$"::VARCHAR AS incoterms,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'OriginWarehouse'), 'WarehouseId'):"$"::VARCHAR AS warehouse_id,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'OriginWarehouse'), 'WarehouseName'):"$"::VARCHAR AS warehouse_name,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'OriginWarehouse'), 'TimeZone'):"$"::VARCHAR AS time_zone,
    XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'CarrierRouting'):"@carrierCode"::VARCHAR AS carrier_routing_carrier_code,
    XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'CarrierRouting'):"@serviceLevel"::VARCHAR AS carrier_routing_service_level,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'CarrierRouting'), 'CarrierName'):"$"::VARCHAR AS carrier_name,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'CarrierRouting'), 'ScacCode'):"$"::VARCHAR AS scac_code,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'CarrierRouting'), 'BolNumber'):"$"::VARCHAR AS bol_number,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'CarrierRouting'), 'ProNumber'):"$"::VARCHAR AS pro_number,
    TRY_TO_NUMBER(XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'CarrierRouting'), 'EstimatedTransitDays'):"$"::VARCHAR, 18, 0) AS estimated_transit_days,
    TRY_TO_NUMBER(XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'CarrierRouting'), 'TotalPalletCount'):"$"::VARCHAR, 18, 0) AS total_pallet_count,
    TRY_TO_DECIMAL(XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'CarrierRouting'), 'TotalGrossWeightKg'):"$"::VARCHAR, 18, 4) AS total_gross_weight_kg,
    TRY_TO_BOOLEAN(XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'CarrierRouting'), 'IsTemperatureControlled'):"$"::VARCHAR) AS is_temperature_controlled,
    TRY_TO_DECIMAL(XMLGET(XMLGET(XMLGET(r.raw_xml, 'FulfillmentPlan'), 'CarrierRouting'), 'InsuranceCoverageAmount'):"$"::VARCHAR, 18, 4) AS insurance_coverage_amount,
    XMLGET(r.raw_xml, 'PaymentDetails'):"@paymentMethod"::VARCHAR AS payment_details_payment_method,
    XMLGET(XMLGET(r.raw_xml, 'PaymentDetails'), 'PaymentStatus'):"$"::VARCHAR AS payment_status,
    XMLGET(XMLGET(r.raw_xml, 'PaymentDetails'), 'AuthorizationCode'):"$"::VARCHAR AS authorization_code,
    TRY_TO_TIMESTAMP_NTZ(XMLGET(XMLGET(r.raw_xml, 'PaymentDetails'), 'AuthorizedTimestamp'):"$"::VARCHAR) AS authorized_timestamp,
    XMLGET(XMLGET(r.raw_xml, 'PaymentDetails'), 'BillingCurrency'):"$"::VARCHAR AS billing_currency,
    TRY_TO_DECIMAL(XMLGET(XMLGET(r.raw_xml, 'PaymentDetails'), 'ExchangeRateToUsd'):"$"::VARCHAR, 18, 4) AS exchange_rate_to_usd,
    TRY_TO_BOOLEAN(XMLGET(XMLGET(r.raw_xml, 'ComplianceAndGovernance'), 'IsExportControlled'):"$"::VARCHAR) AS is_export_controlled,
    XMLGET(XMLGET(r.raw_xml, 'ComplianceAndGovernance'), 'ExportControlClassification'):"$"::VARCHAR AS export_control_classification,
    TRY_TO_BOOLEAN(XMLGET(XMLGET(r.raw_xml, 'ComplianceAndGovernance'), 'SanctionsScreeningPassed'):"$"::VARCHAR) AS sanctions_screening_passed,
    XMLGET(XMLGET(r.raw_xml, 'ComplianceAndGovernance'), 'ScreeningReferenceId'):"$"::VARCHAR AS screening_reference_id,
    TRY_TO_BOOLEAN(XMLGET(XMLGET(XMLGET(r.raw_xml, 'ComplianceAndGovernance'), 'DataPrivacy'), 'ContainsPii'):"$"::VARCHAR) AS contains_pii,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'ComplianceAndGovernance'), 'DataPrivacy'), 'PiiClassification'):"$"::VARCHAR AS pii_classification,
    TRY_TO_BOOLEAN(XMLGET(XMLGET(XMLGET(r.raw_xml, 'ComplianceAndGovernance'), 'DataPrivacy'), 'GdprApplicable'):"$"::VARCHAR) AS gdpr_applicable,
    TRY_TO_NUMBER(XMLGET(XMLGET(XMLGET(r.raw_xml, 'ComplianceAndGovernance'), 'DataPrivacy'), 'RetentionPolicyYears'):"$"::VARCHAR, 18, 0) AS retention_policy_years,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._load_ts AS _staged_ts
FROM RAW.raw_orders r;

-- Entity `audit_event` (/Order/AuditTrail/AuditEvent)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_orders_audit_event
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_orders_audit_event: child of STAGING.staging_orders via order_fk -> STAGING.staging_orders.order_pk (logical FK)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a1.index::VARCHAR)) AS audit_event_pk,
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256)) AS order_fk,
    TRY_TO_NUMBER(a1.value:"@sequence"::VARCHAR, 18, 0) AS sequence,
    XMLGET(a1.value, 'EventId'):"$"::VARCHAR AS event_id,
    XMLGET(a1.value, 'EventType'):"$"::VARCHAR AS event_type,
    TRY_TO_TIMESTAMP_NTZ(XMLGET(a1.value, 'EventTimestamp'):"$"::VARCHAR) AS event_timestamp,
    XMLGET(a1.value, 'ActorId'):"$"::VARCHAR AS actor_id,
    XMLGET(a1.value, 'EventNotes'):"$"::VARCHAR AS event_notes,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._load_ts AS _staged_ts
FROM RAW.raw_orders r,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(XMLGET(r.raw_xml, 'AuditTrail'), '$')), GET(XMLGET(r.raw_xml, 'AuditTrail'), '$'), ARRAY_CONSTRUCT(GET(XMLGET(r.raw_xml, 'AuditTrail'), '$')))) a1
WHERE GET(a1.value, '@')::VARCHAR = 'AuditEvent';

-- Entity `line` (/Order/LineItems/LineItem)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_orders_line
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_orders_line: child of STAGING.staging_orders via order_fk -> STAGING.staging_orders.order_pk (logical FK)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a1.index::VARCHAR)) AS line_pk,
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256)) AS order_fk,
    TRY_TO_NUMBER(a1.value:"@lineNumber"::VARCHAR, 18, 0) AS line_number,
    a1.value:"@itemCategory"::VARCHAR AS item_category,
    TRY_TO_BOOLEAN(a1.value:"@hazmat"::VARCHAR) AS hazmat,
    XMLGET(a1.value, 'LineItemId'):"$"::VARCHAR AS id,
    XMLGET(a1.value, 'ProductCode'):"$"::VARCHAR AS product_code,
    XMLGET(a1.value, 'ManufacturerPartNumber'):"$"::VARCHAR AS manufacturer_part_number,
    XMLGET(a1.value, 'ProductName'):"$"::VARCHAR AS product_name,
    XMLGET(a1.value, 'ProductFamily'):"$"::VARCHAR AS product_family,
    XMLGET(a1.value, 'UnitOfMeasure'):"$"::VARCHAR AS unit_of_measure,
    TRY_TO_NUMBER(XMLGET(a1.value, 'Quantity'):"$"::VARCHAR, 18, 0) AS quantity,
    TRY_TO_DECIMAL(XMLGET(a1.value, 'UnitPrice'):"$"::VARCHAR, 18, 4) AS unit_price,
    TRY_TO_DECIMAL(XMLGET(a1.value, 'LineDiscountAmount'):"$"::VARCHAR, 18, 4) AS line_discount_amount,
    TRY_TO_DECIMAL(XMLGET(a1.value, 'LineTaxRate'):"$"::VARCHAR, 18, 4) AS line_tax_rate,
    TRY_TO_DECIMAL(XMLGET(a1.value, 'LineTaxAmount'):"$"::VARCHAR, 18, 4) AS line_tax_amount,
    TRY_TO_DECIMAL(XMLGET(a1.value, 'ExtendedNetAmount'):"$"::VARCHAR, 18, 4) AS extended_net_amount,
    TRY_TO_BOOLEAN(XMLGET(a1.value, 'IsTaxable'):"$"::VARCHAR) AS is_taxable,
    TRY_TO_BOOLEAN(XMLGET(a1.value, 'IsDropShip'):"$"::VARCHAR) AS is_drop_ship,
    TRY_TO_DATE(XMLGET(a1.value, 'RequestedShipDate'):"$"::VARCHAR) AS requested_ship_date,
    TRY_TO_DECIMAL(XMLGET(XMLGET(a1.value, 'PhysicalSpecs'), 'UnitWeightKg'):"$"::VARCHAR, 18, 4) AS unit_weight_kg,
    XMLGET(XMLGET(a1.value, 'PhysicalSpecs'), 'DimensionsCm'):"$"::VARCHAR AS dimensions_cm,
    XMLGET(XMLGET(a1.value, 'PhysicalSpecs'), 'CountryOfOrigin'):"$"::VARCHAR AS country_of_origin,
    XMLGET(XMLGET(a1.value, 'PhysicalSpecs'), 'HarmonizedTariffCode'):"$"::VARCHAR AS harmonized_tariff_code,
    XMLGET(XMLGET(a1.value, 'InventoryAllocation'), 'AllocatedWarehouseId'):"$"::VARCHAR AS allocated_warehouse_id,
    XMLGET(XMLGET(a1.value, 'InventoryAllocation'), 'BinLocation'):"$"::VARCHAR AS bin_location,
    XMLGET(XMLGET(a1.value, 'InventoryAllocation'), 'LotNumber'):"$"::VARCHAR AS lot_number,
    XMLGET(XMLGET(a1.value, 'InventoryAllocation'), 'AllocationStatus'):"$"::VARCHAR AS allocation_status,
    TRY_TO_TIMESTAMP_NTZ(XMLGET(XMLGET(a1.value, 'InventoryAllocation'), 'AllocationTimestamp'):"$"::VARCHAR) AS allocation_timestamp,
    XMLGET(XMLGET(a1.value, 'Warranty'), 'WarrantyPlanCode'):"$"::VARCHAR AS warranty_plan_code,
    TRY_TO_NUMBER(XMLGET(XMLGET(a1.value, 'Warranty'), 'WarrantyDurationMonths'):"$"::VARCHAR, 18, 0) AS warranty_duration_months,
    TRY_TO_BOOLEAN(XMLGET(XMLGET(a1.value, 'Warranty'), 'IncludesOnsiteResponse'):"$"::VARCHAR) AS includes_onsite_response,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._load_ts AS _staged_ts
FROM RAW.raw_orders r,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(XMLGET(r.raw_xml, 'LineItems'), '$')), GET(XMLGET(r.raw_xml, 'LineItems'), '$'), ARRAY_CONSTRUCT(GET(XMLGET(r.raw_xml, 'LineItems'), '$')))) a1
WHERE GET(a1.value, '@')::VARCHAR = 'LineItem';

-- Entity `installment` (/Order/PaymentDetails/InstallmentSchedule/Installment)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_orders_installment
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_orders_installment: child of STAGING.staging_orders via order_fk -> STAGING.staging_orders.order_pk (logical FK)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a1.index::VARCHAR)) AS installment_pk,
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256)) AS order_fk,
    TRY_TO_NUMBER(a1.value:"@installmentNumber"::VARCHAR, 18, 0) AS installment_number,
    XMLGET(a1.value, 'InstallmentId'):"$"::VARCHAR AS id,
    TRY_TO_DATE(XMLGET(a1.value, 'DueDate'):"$"::VARCHAR) AS due_date,
    TRY_TO_DECIMAL(XMLGET(a1.value, 'InstallmentPercentage'):"$"::VARCHAR, 18, 4) AS percentage,
    TRY_TO_DECIMAL(XMLGET(a1.value, 'InstallmentAmount'):"$"::VARCHAR, 18, 4) AS amount,
    XMLGET(a1.value, 'InstallmentStatus'):"$"::VARCHAR AS status,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._load_ts AS _staged_ts
FROM RAW.raw_orders r,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(XMLGET(XMLGET(r.raw_xml, 'PaymentDetails'), 'InstallmentSchedule'), '$')), GET(XMLGET(XMLGET(r.raw_xml, 'PaymentDetails'), 'InstallmentSchedule'), '$'), ARRAY_CONSTRUCT(GET(XMLGET(XMLGET(r.raw_xml, 'PaymentDetails'), 'InstallmentSchedule'), '$')))) a1
WHERE GET(a1.value, '@')::VARCHAR = 'Installment';

-- =============================================================================
-- LAYER 3 (CURATED): ONE DYNAMIC TABLE PER XML ENTITY FROM STAGE (orders v0.1.0) [Schema: CURATED]
-- Entities: order, audit_event, line, installment
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS CURATED;

-- Entity `order` (/Order)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_orders
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_orders: root entity order (PK order_pk)'
AS
WITH versioned AS (
    SELECT
        order_pk,
        order_type,
        version,
        currency_code,
        channel,
        region,
        order_id,
        external_purchase_order_number,
        order_date,
        order_timestamp,
        order_status,
        is_expedited,
        is_backorder_allowed,
        priority_score,
        total_amount,
        discount_amount,
        tax_amount,
        freight_amount,
        net_payable_amount,
        shipping_notes,
        source_system,
        sales_org_code,
        distribution_channel,
        division_code,
        master_agreement_id,
        contract_effective_date,
        contract_expiration_date,
        discount_tier_percentage,
        is_auto_renew,
        rep_id,
        rep_name,
        rep_email,
        territory_code,
        commission_rate,
        customer_customer_tier,
        customer_tax_exempt,
        customer_kyc_verified,
        customer_id,
        account_number,
        company_name,
        duns_number,
        tax_registration_number,
        account_created_date,
        credit_limit,
        current_balance,
        available_credit,
        risk_rating,
        payment_terms_days,
        is_credit_hold,
        primary_contact_contact_id,
        primary_contact_full_name,
        primary_contact_job_title,
        primary_contact_email,
        primary_contact_phone,
        accounts_payable_contact_contact_id,
        accounts_payable_contact_full_name,
        accounts_payable_contact_job_title,
        accounts_payable_contact_email,
        accounts_payable_contact_phone,
        billing_address_address_type,
        billing_address_address_id,
        billing_address_attention_line,
        billing_address_street_line1,
        billing_address_street_line2,
        billing_address_city,
        billing_address_state_province,
        billing_address_postal_code,
        billing_address_country_code,
        geo_coordinates_latitude,
        geo_coordinates_longitude,
        shipping_address_address_type,
        shipping_address_address_id,
        facility_name,
        shipping_address_attention_line,
        shipping_address_street_line1,
        shipping_address_street_line2,
        shipping_address_city,
        shipping_address_state_province,
        shipping_address_postal_code,
        shipping_address_country_code,
        is_residential,
        requires_liftgate,
        requires_inside_delivery,
        geo_coordinates_latitude_2,
        geo_coordinates_longitude_2,
        requested_delivery_date,
        promised_ship_date,
        incoterms,
        warehouse_id,
        warehouse_name,
        time_zone,
        carrier_routing_carrier_code,
        carrier_routing_service_level,
        carrier_name,
        scac_code,
        bol_number,
        pro_number,
        estimated_transit_days,
        total_pallet_count,
        total_gross_weight_kg,
        is_temperature_controlled,
        insurance_coverage_amount,
        payment_details_payment_method,
        payment_status,
        authorization_code,
        authorized_timestamp,
        billing_currency,
        exchange_rate_to_usd,
        is_export_controlled,
        export_control_classification,
        sanctions_screening_passed,
        screening_reference_id,
        contains_pii,
        pii_classification,
        gdpr_applicable,
        retention_policy_years,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(order_type), ''), COALESCE(TO_VARCHAR(version), ''), COALESCE(TO_VARCHAR(currency_code), ''), COALESCE(TO_VARCHAR(channel), ''), COALESCE(TO_VARCHAR(region), ''), COALESCE(TO_VARCHAR(external_purchase_order_number), ''), COALESCE(TO_VARCHAR(order_date), ''), COALESCE(TO_VARCHAR(order_timestamp), ''), COALESCE(TO_VARCHAR(order_status), ''), COALESCE(TO_VARCHAR(is_expedited), ''), COALESCE(TO_VARCHAR(is_backorder_allowed), ''), COALESCE(TO_VARCHAR(priority_score), ''), COALESCE(TO_VARCHAR(total_amount), ''), COALESCE(TO_VARCHAR(discount_amount), ''), COALESCE(TO_VARCHAR(tax_amount), ''), COALESCE(TO_VARCHAR(freight_amount), ''), COALESCE(TO_VARCHAR(net_payable_amount), ''), COALESCE(TO_VARCHAR(shipping_notes), ''), COALESCE(TO_VARCHAR(source_system), ''), COALESCE(TO_VARCHAR(sales_org_code), ''), COALESCE(TO_VARCHAR(distribution_channel), ''), COALESCE(TO_VARCHAR(division_code), ''), COALESCE(TO_VARCHAR(master_agreement_id), ''), COALESCE(TO_VARCHAR(contract_effective_date), ''), COALESCE(TO_VARCHAR(contract_expiration_date), ''), COALESCE(TO_VARCHAR(discount_tier_percentage), ''), COALESCE(TO_VARCHAR(is_auto_renew), ''), COALESCE(TO_VARCHAR(rep_id), ''), COALESCE(TO_VARCHAR(rep_name), ''), COALESCE(TO_VARCHAR(rep_email), ''), COALESCE(TO_VARCHAR(territory_code), ''), COALESCE(TO_VARCHAR(commission_rate), ''), COALESCE(TO_VARCHAR(customer_customer_tier), ''), COALESCE(TO_VARCHAR(customer_tax_exempt), ''), COALESCE(TO_VARCHAR(customer_kyc_verified), ''), COALESCE(TO_VARCHAR(customer_id), ''), COALESCE(TO_VARCHAR(account_number), ''), COALESCE(TO_VARCHAR(company_name), ''), COALESCE(TO_VARCHAR(duns_number), ''), COALESCE(TO_VARCHAR(tax_registration_number), ''), COALESCE(TO_VARCHAR(account_created_date), ''), COALESCE(TO_VARCHAR(credit_limit), ''), COALESCE(TO_VARCHAR(current_balance), ''), COALESCE(TO_VARCHAR(available_credit), ''), COALESCE(TO_VARCHAR(risk_rating), ''), COALESCE(TO_VARCHAR(payment_terms_days), ''), COALESCE(TO_VARCHAR(is_credit_hold), ''), COALESCE(TO_VARCHAR(primary_contact_contact_id), ''), COALESCE(TO_VARCHAR(primary_contact_full_name), ''), COALESCE(TO_VARCHAR(primary_contact_job_title), ''), COALESCE(TO_VARCHAR(primary_contact_email), ''), COALESCE(TO_VARCHAR(primary_contact_phone), ''), COALESCE(TO_VARCHAR(accounts_payable_contact_contact_id), ''), COALESCE(TO_VARCHAR(accounts_payable_contact_full_name), ''), COALESCE(TO_VARCHAR(accounts_payable_contact_job_title), ''), COALESCE(TO_VARCHAR(accounts_payable_contact_email), ''), COALESCE(TO_VARCHAR(accounts_payable_contact_phone), ''), COALESCE(TO_VARCHAR(billing_address_address_type), ''), COALESCE(TO_VARCHAR(billing_address_address_id), ''), COALESCE(TO_VARCHAR(billing_address_attention_line), ''), COALESCE(TO_VARCHAR(billing_address_street_line1), ''), COALESCE(TO_VARCHAR(billing_address_street_line2), ''), COALESCE(TO_VARCHAR(billing_address_city), ''), COALESCE(TO_VARCHAR(billing_address_state_province), ''), COALESCE(TO_VARCHAR(billing_address_postal_code), ''), COALESCE(TO_VARCHAR(billing_address_country_code), ''), COALESCE(TO_VARCHAR(geo_coordinates_latitude), ''), COALESCE(TO_VARCHAR(geo_coordinates_longitude), ''), COALESCE(TO_VARCHAR(shipping_address_address_type), ''), COALESCE(TO_VARCHAR(shipping_address_address_id), ''), COALESCE(TO_VARCHAR(facility_name), ''), COALESCE(TO_VARCHAR(shipping_address_attention_line), ''), COALESCE(TO_VARCHAR(shipping_address_street_line1), ''), COALESCE(TO_VARCHAR(shipping_address_street_line2), ''), COALESCE(TO_VARCHAR(shipping_address_city), ''), COALESCE(TO_VARCHAR(shipping_address_state_province), ''), COALESCE(TO_VARCHAR(shipping_address_postal_code), ''), COALESCE(TO_VARCHAR(shipping_address_country_code), ''), COALESCE(TO_VARCHAR(is_residential), ''), COALESCE(TO_VARCHAR(requires_liftgate), ''), COALESCE(TO_VARCHAR(requires_inside_delivery), ''), COALESCE(TO_VARCHAR(geo_coordinates_latitude_2), ''), COALESCE(TO_VARCHAR(geo_coordinates_longitude_2), ''), COALESCE(TO_VARCHAR(requested_delivery_date), ''), COALESCE(TO_VARCHAR(promised_ship_date), ''), COALESCE(TO_VARCHAR(incoterms), ''), COALESCE(TO_VARCHAR(warehouse_id), ''), COALESCE(TO_VARCHAR(warehouse_name), ''), COALESCE(TO_VARCHAR(time_zone), ''), COALESCE(TO_VARCHAR(carrier_routing_carrier_code), ''), COALESCE(TO_VARCHAR(carrier_routing_service_level), ''), COALESCE(TO_VARCHAR(carrier_name), ''), COALESCE(TO_VARCHAR(scac_code), ''), COALESCE(TO_VARCHAR(bol_number), ''), COALESCE(TO_VARCHAR(pro_number), ''), COALESCE(TO_VARCHAR(estimated_transit_days), ''), COALESCE(TO_VARCHAR(total_pallet_count), ''), COALESCE(TO_VARCHAR(total_gross_weight_kg), ''), COALESCE(TO_VARCHAR(is_temperature_controlled), ''), COALESCE(TO_VARCHAR(insurance_coverage_amount), ''), COALESCE(TO_VARCHAR(payment_details_payment_method), ''), COALESCE(TO_VARCHAR(payment_status), ''), COALESCE(TO_VARCHAR(authorization_code), ''), COALESCE(TO_VARCHAR(authorized_timestamp), ''), COALESCE(TO_VARCHAR(billing_currency), ''), COALESCE(TO_VARCHAR(exchange_rate_to_usd), ''), COALESCE(TO_VARCHAR(is_export_controlled), ''), COALESCE(TO_VARCHAR(export_control_classification), ''), COALESCE(TO_VARCHAR(sanctions_screening_passed), ''), COALESCE(TO_VARCHAR(screening_reference_id), ''), COALESCE(TO_VARCHAR(contains_pii), ''), COALESCE(TO_VARCHAR(pii_classification), ''), COALESCE(TO_VARCHAR(gdpr_applicable), ''), COALESCE(TO_VARCHAR(retention_policy_years), '')), 256) AS _row_hash,
        _staged_ts AS is_valid_start,
        LEAD(_staged_ts) OVER (
            PARTITION BY order_id
            ORDER BY _staged_ts ASC
        ) AS is_valid_end,
        CASE
            WHEN LEAD(_staged_ts) OVER (
                PARTITION BY order_id
                ORDER BY _staged_ts ASC
            ) IS NULL THEN TRUE
            ELSE FALSE
        END AS is_current,
        _staged_ts AS system_start_time,
        LEAD(_staged_ts) OVER (
            PARTITION BY order_id
            ORDER BY _staged_ts ASC
        ) AS system_end_time,
        _file_name AS _source_file
    FROM STAGING.staging_orders
)
SELECT * FROM versioned;

-- Entity `audit_event` (/Order/AuditTrail/AuditEvent)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_orders_audit_event
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_orders_audit_event: child of CURATED.curated_orders via order_fk -> CURATED.curated_orders.order_pk (logical FK)'
AS
SELECT
        audit_event_pk,
        order_fk,
        sequence,
        event_id,
        event_type,
        event_timestamp,
        actor_id,
        event_notes,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(sequence), ''), COALESCE(TO_VARCHAR(event_id), ''), COALESCE(TO_VARCHAR(event_type), ''), COALESCE(TO_VARCHAR(event_timestamp), ''), COALESCE(TO_VARCHAR(actor_id), ''), COALESCE(TO_VARCHAR(event_notes), '')), 256) AS _row_hash,
        _staged_ts AS system_start_time,
        _file_name AS _source_file
FROM STAGING.staging_orders_audit_event;

-- Entity `line` (/Order/LineItems/LineItem)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_orders_line
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_orders_line: child of CURATED.curated_orders via order_fk -> CURATED.curated_orders.order_pk (logical FK)'
AS
SELECT
        line_pk,
        order_fk,
        line_number,
        item_category,
        hazmat,
        id,
        product_code,
        manufacturer_part_number,
        product_name,
        product_family,
        unit_of_measure,
        quantity,
        unit_price,
        line_discount_amount,
        line_tax_rate,
        line_tax_amount,
        extended_net_amount,
        is_taxable,
        is_drop_ship,
        requested_ship_date,
        unit_weight_kg,
        dimensions_cm,
        country_of_origin,
        harmonized_tariff_code,
        allocated_warehouse_id,
        bin_location,
        lot_number,
        allocation_status,
        allocation_timestamp,
        warranty_plan_code,
        warranty_duration_months,
        includes_onsite_response,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(line_number), ''), COALESCE(TO_VARCHAR(item_category), ''), COALESCE(TO_VARCHAR(hazmat), ''), COALESCE(TO_VARCHAR(id), ''), COALESCE(TO_VARCHAR(product_code), ''), COALESCE(TO_VARCHAR(manufacturer_part_number), ''), COALESCE(TO_VARCHAR(product_name), ''), COALESCE(TO_VARCHAR(product_family), ''), COALESCE(TO_VARCHAR(unit_of_measure), ''), COALESCE(TO_VARCHAR(quantity), ''), COALESCE(TO_VARCHAR(unit_price), ''), COALESCE(TO_VARCHAR(line_discount_amount), ''), COALESCE(TO_VARCHAR(line_tax_rate), ''), COALESCE(TO_VARCHAR(line_tax_amount), ''), COALESCE(TO_VARCHAR(extended_net_amount), ''), COALESCE(TO_VARCHAR(is_taxable), ''), COALESCE(TO_VARCHAR(is_drop_ship), ''), COALESCE(TO_VARCHAR(requested_ship_date), ''), COALESCE(TO_VARCHAR(unit_weight_kg), ''), COALESCE(TO_VARCHAR(dimensions_cm), ''), COALESCE(TO_VARCHAR(country_of_origin), ''), COALESCE(TO_VARCHAR(harmonized_tariff_code), ''), COALESCE(TO_VARCHAR(allocated_warehouse_id), ''), COALESCE(TO_VARCHAR(bin_location), ''), COALESCE(TO_VARCHAR(lot_number), ''), COALESCE(TO_VARCHAR(allocation_status), ''), COALESCE(TO_VARCHAR(allocation_timestamp), ''), COALESCE(TO_VARCHAR(warranty_plan_code), ''), COALESCE(TO_VARCHAR(warranty_duration_months), ''), COALESCE(TO_VARCHAR(includes_onsite_response), '')), 256) AS _row_hash,
        _staged_ts AS system_start_time,
        _file_name AS _source_file
FROM STAGING.staging_orders_line;

-- Entity `installment` (/Order/PaymentDetails/InstallmentSchedule/Installment)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_orders_installment
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_orders_installment: child of CURATED.curated_orders via order_fk -> CURATED.curated_orders.order_pk (logical FK)'
AS
SELECT
        installment_pk,
        order_fk,
        installment_number,
        id,
        due_date,
        percentage,
        amount,
        status,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(installment_number), ''), COALESCE(TO_VARCHAR(id), ''), COALESCE(TO_VARCHAR(due_date), ''), COALESCE(TO_VARCHAR(percentage), ''), COALESCE(TO_VARCHAR(amount), ''), COALESCE(TO_VARCHAR(status), '')), 256) AS _row_hash,
        _staged_ts AS system_start_time,
        _file_name AS _source_file
FROM STAGING.staging_orders_installment;

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
