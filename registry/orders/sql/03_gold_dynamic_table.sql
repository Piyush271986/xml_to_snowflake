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
