# Step 1: Data Steward & Modeling Report — `enterprise_orders`

> **Status:** Pending Human Approval (`PENDING_HUMAN_APPROVAL`). **No SQL DDL has been generated yet.**
> Once approved at C3, the **DDL Generator Agent (Step 2)** will compile the Snowpipe and Dynamic Table SQLs.

## Proposed 3-Layer Medallion Data Model (YAML Schemas)

| Layer | YAML Schema File | Table Name | Snowflake Object Type | Ingestion / Refresh |
|---|---|---|---|---|
| **1. RAW** | `raw_schema.yaml` | `raw_enterprise_orders` | `NORMAL_TABLE` | `SNOWPIPE` (`ADLS -> RAW`) |
| **2. STAGE** | `staging_schema.yaml` | `staging_enterprise_orders` | `DYNAMIC_TABLE` (`TARGET_LAG = '5 minutes'`) | `DYNAMIC_TABLE_REFRESH` (`RAW -> STAGE`) |
| **3. GOLD** | `gold_schema.yaml` | `curated_enterprise_orders` | `DYNAMIC_TABLE` (`TARGET_LAG = '15 minutes'`) | `DYNAMIC_TABLE_REFRESH` (`STAGE -> GOLD`) |

- **Samples Analyzed:** 1 valid XML files
- **Root Element:** `/Order`
- **Inferred Business Keys:** `order_id, line_item_id`
- **Total Inferred Fields:** 157 (42 array fields)
- **Low-Confidence Fields (< 0.8):** 0

## Inferred Field Inventory

| XPath | Column | Snowflake Type | Required | Array (`LATERAL FLATTEN`) | Confidence | Status |
|---|---|---|---|---|---|---|
| `/Order/@orderType` | `order_type` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/@version` | `version` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/@currency` | `currency_code` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/@channel` | `channel` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/@region` | `region` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/OrderId` | `order_id` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/ExternalPurchaseOrderNumber` | `external_purchase_order_number` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/OrderDate` | `order_date` | `DATE` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/OrderTimestamp` | `order_timestamp` | `TIMESTAMP_NTZ` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/OrderStatus` | `order_status` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/IsExpedited` | `is_expedited` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/IsBackorderAllowed` | `is_backorder_allowed` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/PriorityScore` | `priority_score` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/TotalAmount` | `total_amount` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/DiscountAmount` | `discount_amount` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/TaxAmount` | `tax_amount` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FreightAmount` | `freight_amount` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/NetPayableAmount` | `net_payable_amount` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/ShippingNotes` | `shipping_notes` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/SourceSystem` | `source_system` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/SalesOrgCode` | `sales_org_code` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/DistributionChannel` | `distribution_channel` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/DivisionCode` | `division_code` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/ContractReference/MasterAgreementId` | `master_agreement_id` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/ContractReference/ContractEffectiveDate` | `contract_effective_date` | `DATE` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/ContractReference/ContractExpirationDate` | `contract_expiration_date` | `DATE` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/ContractReference/DiscountTierPercentage` | `discount_tier_percentage` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/ContractReference/IsAutoRenew` | `is_auto_renew` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/SalesRepresentative/RepId` | `rep_id` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/SalesRepresentative/RepName` | `rep_name` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/SalesRepresentative/RepEmail` | `rep_email` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/SalesRepresentative/TerritoryCode` | `territory_code` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Header/SalesRepresentative/CommissionRate` | `commission_rate` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/@customerTier` | `customer_customer_tier` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/@taxExempt` | `customer_tax_exempt` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/@kycVerified` | `customer_kyc_verified` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/CustomerId` | `customer_id` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/AccountNumber` | `account_number` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/CompanyName` | `company_name` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/DunsNumber` | `duns_number` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/TaxRegistrationNumber` | `tax_registration_number` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/AccountCreatedDate` | `account_created_date` | `DATE` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/CreditProfile/CreditLimit` | `credit_limit` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/CreditProfile/CurrentBalance` | `current_balance` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/CreditProfile/AvailableCredit` | `available_credit` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/CreditProfile/RiskRating` | `risk_rating` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/CreditProfile/PaymentTermsDays` | `payment_terms_days` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/CreditProfile/IsCreditHold` | `is_credit_hold` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Contacts/PrimaryContact/ContactId` | `primary_contact_contact_id` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Contacts/PrimaryContact/FullName` | `primary_contact_full_name` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Contacts/PrimaryContact/JobTitle` | `primary_contact_job_title` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Contacts/PrimaryContact/Email` | `primary_contact_email` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Contacts/PrimaryContact/Phone` | `primary_contact_phone` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Contacts/AccountsPayableContact/ContactId` | `accounts_payable_contact_contact_id` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Contacts/AccountsPayableContact/FullName` | `accounts_payable_contact_full_name` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Contacts/AccountsPayableContact/JobTitle` | `accounts_payable_contact_job_title` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Contacts/AccountsPayableContact/Email` | `accounts_payable_contact_email` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Contacts/AccountsPayableContact/Phone` | `accounts_payable_contact_phone` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/BillingAddress/@addressType` | `billing_address_address_type` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/BillingAddress/AddressId` | `billing_address_address_id` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/BillingAddress/AttentionLine` | `billing_address_attention_line` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/BillingAddress/StreetLine1` | `billing_address_street_line1` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/BillingAddress/StreetLine2` | `billing_address_street_line2` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/BillingAddress/City` | `billing_address_city` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/BillingAddress/StateProvince` | `billing_address_state_province` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/BillingAddress/PostalCode` | `billing_address_postal_code` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/BillingAddress/CountryCode` | `billing_address_country_code` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/BillingAddress/GeoCoordinates/Latitude` | `geo_coordinates_latitude` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/BillingAddress/GeoCoordinates/Longitude` | `geo_coordinates_longitude` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/@addressType` | `shipping_address_address_type` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/AddressId` | `shipping_address_address_id` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/FacilityName` | `facility_name` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/AttentionLine` | `shipping_address_attention_line` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/StreetLine1` | `shipping_address_street_line1` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/StreetLine2` | `shipping_address_street_line2` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/City` | `shipping_address_city` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/StateProvince` | `shipping_address_state_province` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/PostalCode` | `shipping_address_postal_code` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/CountryCode` | `shipping_address_country_code` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/IsResidential` | `is_residential` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/RequiresLiftgate` | `requires_liftgate` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/RequiresInsideDelivery` | `requires_inside_delivery` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/GeoCoordinates/Latitude` | `geo_coordinates_latitude_2` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/Customer/Addresses/ShippingAddress/GeoCoordinates/Longitude` | `geo_coordinates_longitude_2` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/RequestedDeliveryDate` | `requested_delivery_date` | `DATE` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/PromisedShipDate` | `promised_ship_date` | `DATE` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/Incoterms` | `incoterms` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/OriginWarehouse/WarehouseId` | `warehouse_id` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/OriginWarehouse/WarehouseName` | `warehouse_name` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/OriginWarehouse/TimeZone` | `time_zone` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/CarrierRouting/@carrierCode` | `carrier_routing_carrier_code` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/CarrierRouting/@serviceLevel` | `carrier_routing_service_level` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/CarrierRouting/CarrierName` | `carrier_name` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/CarrierRouting/ScacCode` | `scac_code` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/CarrierRouting/BolNumber` | `bol_number` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/CarrierRouting/ProNumber` | `pro_number` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/CarrierRouting/EstimatedTransitDays` | `estimated_transit_days` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/CarrierRouting/TotalPalletCount` | `total_pallet_count` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/CarrierRouting/TotalGrossWeightKg` | `total_gross_weight_kg` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/CarrierRouting/IsTemperatureControlled` | `is_temperature_controlled` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/FulfillmentPlan/CarrierRouting/InsuranceCoverageAmount` | `insurance_coverage_amount` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/@paymentMethod` | `payment_details_payment_method` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/PaymentStatus` | `payment_status` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/AuthorizationCode` | `authorization_code` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/AuthorizedTimestamp` | `authorized_timestamp` | `TIMESTAMP_NTZ` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/BillingCurrency` | `billing_currency` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/ExchangeRateToUsd` | `exchange_rate_to_usd` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/@installmentNumber` | `installment_installment_number` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/InstallmentId` | `installment_id` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/DueDate` | `installment_due_date` | `DATE` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/InstallmentPercentage` | `installment_percentage` | `NUMBER(18,4)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/InstallmentAmount` | `installment_amount` | `NUMBER(18,4)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/InstallmentStatus` | `installment_status` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/@lineNumber` | `line_item_line_number` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/@itemCategory` | `line_item_item_category` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/@hazmat` | `line_item_hazmat` | `BOOLEAN` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/LineItemId` | `line_item_id` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/ProductCode` | `line_item_product_code` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/ManufacturerPartNumber` | `line_item_manufacturer_part_number` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/ProductName` | `line_item_product_name` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/ProductFamily` | `line_item_product_family` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/UnitOfMeasure` | `line_item_unit_of_measure` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/Quantity` | `line_item_quantity` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/UnitPrice` | `line_item_unit_price` | `NUMBER(18,4)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/LineDiscountAmount` | `line_item_line_discount_amount` | `NUMBER(18,4)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/LineTaxRate` | `line_item_line_tax_rate` | `NUMBER(18,4)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/LineTaxAmount` | `line_item_line_tax_amount` | `NUMBER(18,4)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/ExtendedNetAmount` | `line_item_extended_net_amount` | `NUMBER(18,4)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/IsTaxable` | `line_item_is_taxable` | `BOOLEAN` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/IsDropShip` | `line_item_is_drop_ship` | `BOOLEAN` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/RequestedShipDate` | `line_item_requested_ship_date` | `DATE` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/PhysicalSpecs/UnitWeightKg` | `line_item_unit_weight_kg` | `NUMBER(18,4)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/PhysicalSpecs/DimensionsCm` | `line_item_dimensions_cm` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/PhysicalSpecs/CountryOfOrigin` | `line_item_country_of_origin` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/PhysicalSpecs/HarmonizedTariffCode` | `line_item_harmonized_tariff_code` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/InventoryAllocation/AllocatedWarehouseId` | `line_item_allocated_warehouse_id` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/InventoryAllocation/BinLocation` | `line_item_bin_location` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/InventoryAllocation/LotNumber` | `line_item_lot_number` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/InventoryAllocation/AllocationStatus` | `line_item_allocation_status` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/InventoryAllocation/AllocationTimestamp` | `line_item_allocation_timestamp` | `TIMESTAMP_NTZ` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/Warranty/WarrantyPlanCode` | `line_item_warranty_plan_code` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/Warranty/WarrantyDurationMonths` | `line_item_warranty_duration_months` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/Warranty/IncludesOnsiteResponse` | `line_item_includes_onsite_response` | `BOOLEAN` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/ComplianceAndGovernance/IsExportControlled` | `is_export_controlled` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/ComplianceAndGovernance/ExportControlClassification` | `export_control_classification` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/ComplianceAndGovernance/SanctionsScreeningPassed` | `sanctions_screening_passed` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/ComplianceAndGovernance/ScreeningReferenceId` | `screening_reference_id` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/ComplianceAndGovernance/DataPrivacy/ContainsPii` | `contains_pii` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/ComplianceAndGovernance/DataPrivacy/PiiClassification` | `pii_classification` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/ComplianceAndGovernance/DataPrivacy/GdprApplicable` | `gdpr_applicable` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/ComplianceAndGovernance/DataPrivacy/RetentionPolicyYears` | `retention_policy_years` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/AuditTrail/AuditEvent/@sequence` | `audit_event_sequence` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/AuditTrail/AuditEvent/EventId` | `audit_event_event_id` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/AuditTrail/AuditEvent/EventType` | `audit_event_event_type` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/AuditTrail/AuditEvent/EventTimestamp` | `audit_event_event_timestamp` | `TIMESTAMP_NTZ` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/AuditTrail/AuditEvent/ActorId` | `audit_event_actor_id` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/AuditTrail/AuditEvent/EventNotes` | `audit_event_event_notes` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
