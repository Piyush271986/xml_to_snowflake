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
