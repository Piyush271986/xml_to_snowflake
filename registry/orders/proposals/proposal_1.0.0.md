# C2 Schema Drift Proposal — `orders` (`v1.0.0`)

- **Status:** `PENDING_C3_APPROVAL`
- **Created At:** `2026-11-11T03:15:10.305829+00:00`

## Drift Findings

| XPath | Change Type | Classification | Expected | Observed | Sample Value | Source File |
|---|---|---|---|---|---|---|
| `/Order/@channel` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `EDI_850` | `enterprise_order_001.xml` |
| `/Order/@orderType` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `B2B_ENTERPRISE` | `enterprise_order_001.xml` |
| `/Order/@region` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `NA-EAST` | `enterprise_order_001.xml` |
| `/Order/@version` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `2.4` | `enterprise_order_001.xml` |
| `/Order/AuditTrail/AuditEvent/@sequence` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `1` | `enterprise_order_001.xml` |
| `/Order/AuditTrail/AuditEvent/ActorId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `SYS-EDI-GATEWAY-01` | `enterprise_order_001.xml` |
| `/Order/AuditTrail/AuditEvent/EventId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `EVT-90010458-001` | `enterprise_order_001.xml` |
| `/Order/AuditTrail/AuditEvent/EventNotes` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Inbound EDI 850 document validated against partner trading profile.` | `enterprise_order_001.xml` |
| `/Order/AuditTrail/AuditEvent/EventTimestamp` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `TIMESTAMP_NTZ` | `2026-11-10T14:22:35Z` | `enterprise_order_001.xml` |
| `/Order/AuditTrail/AuditEvent/EventType` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `ORDER_RECEIVED_EDI` | `enterprise_order_001.xml` |
| `/Order/ComplianceAndGovernance/DataPrivacy/ContainsPii` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `true` | `enterprise_order_001.xml` |
| `/Order/ComplianceAndGovernance/DataPrivacy/GdprApplicable` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `false` | `enterprise_order_001.xml` |
| `/Order/ComplianceAndGovernance/DataPrivacy/PiiClassification` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `BUSINESS_CONTACT_ONLY` | `enterprise_order_001.xml` |
| `/Order/ComplianceAndGovernance/DataPrivacy/RetentionPolicyYears` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `7` | `enterprise_order_001.xml` |
| `/Order/ComplianceAndGovernance/ExportControlClassification` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `EAR99` | `enterprise_order_001.xml` |
| `/Order/ComplianceAndGovernance/IsExportControlled` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `false` | `enterprise_order_001.xml` |
| `/Order/ComplianceAndGovernance/SanctionsScreeningPassed` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `true` | `enterprise_order_001.xml` |
| `/Order/ComplianceAndGovernance/ScreeningReferenceId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `OFAC-SCR-20261110-8812` | `enterprise_order_001.xml` |
| `/Order/Customer/@customerTier` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `PLATINUM` | `enterprise_order_001.xml` |
| `/Order/Customer/@kycVerified` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `true` | `enterprise_order_001.xml` |
| `/Order/Customer/@taxExempt` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `false` | `enterprise_order_001.xml` |
| `/Order/Customer/AccountCreatedDate` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `DATE` | `2021-06-01` | `enterprise_order_001.xml` |
| `/Order/Customer/AccountNumber` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `ACCT-US-9920144` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/BillingAddress/@addressType` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `CORPORATE_HQ` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/BillingAddress/AddressId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `ADDR-BILL-701` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/BillingAddress/AttentionLine` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Attn: Accounts Payable Dept` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/BillingAddress/City` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Cambridge` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/BillingAddress/CountryCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `US` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/BillingAddress/GeoCoordinates/Latitude` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `42.3629` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/BillingAddress/GeoCoordinates/Longitude` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `-71.0921` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/BillingAddress/PostalCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `02139` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/BillingAddress/StateProvince` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `MA` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/BillingAddress/StreetLine1` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `450 Technology Square` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/BillingAddress/StreetLine2` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Suite 1800` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/@addressType` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `DATA_CENTER_SITE` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/AddressId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `ADDR-SHIP-709` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/AttentionLine` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Attn: Hardware Provisioning Dock B` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/City` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Ashburn` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/CountryCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `US` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/FacilityName` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Apex Ashburn Hyperscale Facility DC-04` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/GeoCoordinates/Latitude` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `39.0163` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/GeoCoordinates/Longitude` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `-77.4590` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/IsResidential` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `false` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/PostalCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `20147` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/RequiresInsideDelivery` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `true` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/RequiresLiftgate` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `false` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/StateProvince` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `VA` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/StreetLine1` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `21700 Filigree Court` | `enterprise_order_001.xml` |
| `/Order/Customer/Addresses/ShippingAddress/StreetLine2` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Building C, Bay 4` | `enterprise_order_001.xml` |
| `/Order/Customer/CompanyName` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Apex Global Cloud Infrastructure Corp` | `enterprise_order_001.xml` |
| `/Order/Customer/Contacts/AccountsPayableContact/ContactId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `CNT-102` | `enterprise_order_001.xml` |
| `/Order/Customer/Contacts/AccountsPayableContact/Email` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `ap-invoices@apexcloud.example.com` | `enterprise_order_001.xml` |
| `/Order/Customer/Contacts/AccountsPayableContact/FullName` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `David Chen` | `enterprise_order_001.xml` |
| `/Order/Customer/Contacts/AccountsPayableContact/JobTitle` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Senior AP Controller` | `enterprise_order_001.xml` |
| `/Order/Customer/Contacts/AccountsPayableContact/Phone` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `+1-617-555-0148` | `enterprise_order_001.xml` |
| `/Order/Customer/Contacts/PrimaryContact/ContactId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `CNT-101` | `enterprise_order_001.xml` |
| `/Order/Customer/Contacts/PrimaryContact/Email` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `elena.rostova@apexcloud.example.com` | `enterprise_order_001.xml` |
| `/Order/Customer/Contacts/PrimaryContact/FullName` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Elena Rostova` | `enterprise_order_001.xml` |
| `/Order/Customer/Contacts/PrimaryContact/JobTitle` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `VP of Data Center Procurement` | `enterprise_order_001.xml` |
| `/Order/Customer/Contacts/PrimaryContact/Phone` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `+1-617-555-0192` | `enterprise_order_001.xml` |
| `/Order/Customer/CreditProfile/AvailableCredit` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `357149.7500` | `enterprise_order_001.xml` |
| `/Order/Customer/CreditProfile/CreditLimit` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `500000.0000` | `enterprise_order_001.xml` |
| `/Order/Customer/CreditProfile/CurrentBalance` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `142850.2500` | `enterprise_order_001.xml` |
| `/Order/Customer/CreditProfile/IsCreditHold` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `false` | `enterprise_order_001.xml` |
| `/Order/Customer/CreditProfile/PaymentTermsDays` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `45` | `enterprise_order_001.xml` |
| `/Order/Customer/CreditProfile/RiskRating` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `LOW` | `enterprise_order_001.xml` |
| `/Order/Customer/CustomerId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `CUST-88401` | `enterprise_order_001.xml` |
| `/Order/Customer/DunsNumber` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `149028831` | `enterprise_order_001.xml` |
| `/Order/Customer/TaxRegistrationNumber` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `US-EIN-84-2901145` | `enterprise_order_001.xml` |
| `/Order/ExternalPurchaseOrderNumber` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `PO-2026-GLB-88412` | `enterprise_order_001.xml` |
| `/Order/FreightAmount` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `685.5000` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/CarrierRouting/@carrierCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `FEDEX_FREIGHT` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/CarrierRouting/@serviceLevel` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `PRIORITY_FREIGHT` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/CarrierRouting/BolNumber` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `BOL-2026-1110-9941` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/CarrierRouting/CarrierName` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `FedEx Freight Priority` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/CarrierRouting/EstimatedTransitDays` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `2` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/CarrierRouting/InsuranceCoverageAmount` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `75000.0000` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/CarrierRouting/IsTemperatureControlled` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `false` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/CarrierRouting/ProNumber` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `PRO-778291044` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/CarrierRouting/ScacCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `FXFE` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/CarrierRouting/TotalGrossWeightKg` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `842.6000` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/CarrierRouting/TotalPalletCount` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `4` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/Incoterms` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `DDP` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/OriginWarehouse/TimeZone` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `America/New_York` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/OriginWarehouse/WarehouseId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `WH-NJ-02` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/OriginWarehouse/WarehouseName` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Newark Enterprise Distribution Hub` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/PromisedShipDate` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `DATE` | `2026-11-12` | `enterprise_order_001.xml` |
| `/Order/FulfillmentPlan/RequestedDeliveryDate` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `DATE` | `2026-11-18` | `enterprise_order_001.xml` |
| `/Order/Header/ContractReference/ContractEffectiveDate` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `DATE` | `2024-01-15` | `enterprise_order_001.xml` |
| `/Order/Header/ContractReference/ContractExpirationDate` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `DATE` | `2027-12-31` | `enterprise_order_001.xml` |
| `/Order/Header/ContractReference/DiscountTierPercentage` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `5.0000` | `enterprise_order_001.xml` |
| `/Order/Header/ContractReference/IsAutoRenew` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `true` | `enterprise_order_001.xml` |
| `/Order/Header/ContractReference/MasterAgreementId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `MSA-2024-9921` | `enterprise_order_001.xml` |
| `/Order/Header/DistributionChannel` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `10` | `enterprise_order_001.xml` |
| `/Order/Header/DivisionCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `02` | `enterprise_order_001.xml` |
| `/Order/Header/SalesOrgCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `US10` | `enterprise_order_001.xml` |
| `/Order/Header/SalesRepresentative/CommissionRate` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `0.0325` | `enterprise_order_001.xml` |
| `/Order/Header/SalesRepresentative/RepEmail` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `m.vance@enterprise-supply.io` | `enterprise_order_001.xml` |
| `/Order/Header/SalesRepresentative/RepId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `REP-4409` | `enterprise_order_001.xml` |
| `/Order/Header/SalesRepresentative/RepName` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `Marcus Vance` | `enterprise_order_001.xml` |
| `/Order/Header/SalesRepresentative/TerritoryCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `US-NE-ENTERPRISE` | `enterprise_order_001.xml` |
| `/Order/Header/SourceSystem` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `SAP_S4HANA_ERP` | `enterprise_order_001.xml` |
| `/Order/IsBackorderAllowed` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `false` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/@hazmat` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `false` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/@itemCategory` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `HARDWARE_COMPUTE` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/@lineNumber` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `10` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/ExtendedNetAmount` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `24510.0000` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/InventoryAllocation/AllocatedWarehouseId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `WH-NJ-02` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/InventoryAllocation/AllocationStatus` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `HARD_RESERVED` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/InventoryAllocation/AllocationTimestamp` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `TIMESTAMP_NTZ` | `2026-11-10T14:23:12Z` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/InventoryAllocation/BinLocation` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `AISLE-04-RACK-12-B` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/InventoryAllocation/LotNumber` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `LOT-2026-Q4-881` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/IsDropShip` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `false` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/IsTaxable` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `true` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/LineDiscountAmount` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `1290.0000` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/LineItemId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `LI-90010458-010` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/LineTaxAmount` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `1960.8000` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/LineTaxRate` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `0.0800` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/ManufacturerPartNumber` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `DELL-PE-R760-X1` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/PhysicalSpecs/CountryOfOrigin` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `US` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/PhysicalSpecs/DimensionsCm` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `73.4x48.2x8.7` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/PhysicalSpecs/HarmonizedTariffCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `8471.50.0150` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/PhysicalSpecs/UnitWeightKg` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `28.4000` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/ProductFamily` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `ENTERPRISE_SERVERS` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/ProductName` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `2U Rackmount Enterprise Compute Node Dual Xeon 64GB` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/RequestedShipDate` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `DATE` | `2026-11-12` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/UnitOfMeasure` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `EA` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/Warranty/IncludesOnsiteResponse` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `BOOLEAN` | `true` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/Warranty/WarrantyDurationMonths` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `36` | `enterprise_order_001.xml` |
| `/Order/LineItems/LineItem/Warranty/WarrantyPlanCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `PRO-SUPPORT-3YR-NBD` | `enterprise_order_001.xml` |
| `/Order/NetPayableAmount` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `50931.5620` | `enterprise_order_001.xml` |
| `/Order/OrderStatus` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `APPROVED_FOR_FULFILLMENT` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/@paymentMethod` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `CORPORATE_ACH` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/AuthorizationCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `AUTH-99482710` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/AuthorizedTimestamp` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `TIMESTAMP_NTZ` | `2026-11-10T14:23:01Z` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/BillingCurrency` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `USD` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/ExchangeRateToUsd` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `1.0000` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/@installmentNumber` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `1` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/DueDate` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `DATE` | `2026-11-25` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/InstallmentAmount` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `25465.7810` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/InstallmentId` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `INST-90010458-01` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/InstallmentPercentage` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `50.0000` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/InstallmentSchedule/Installment/InstallmentStatus` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `SCHEDULED` | `enterprise_order_001.xml` |
| `/Order/PaymentDetails/PaymentStatus` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `AUTHORIZED` | `enterprise_order_001.xml` |
| `/Order/PriorityScore` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,0)` | `1` | `enterprise_order_001.xml` |
| `/Order/TaxAmount` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `3903.4120` | `enterprise_order_001.xml` |
| `/Order/CustomerId` | `MISSING_REQUIRED_ELEMENT` | **BREAKING** | `VARCHAR` | `-` | `-` | `enterprise_order_001.xml` |

## Proposed Snowflake DDL Changes

```sql
-- Additive drift column for Dynamic Table staging_orders: channel (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: order_type (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: region (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: version (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: audit_event_sequence (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: actor_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: event_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: event_notes (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: event_timestamp (TIMESTAMP_NTZ)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: event_type (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: contains_pii (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: gdpr_applicable (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: pii_classification (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: retention_policy_years (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: export_control_classification (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: is_export_controlled (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: sanctions_screening_passed (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: screening_reference_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: customer_customer_tier (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: customer_kyc_verified (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: customer_tax_exempt (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: account_created_date (DATE)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: account_number (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: billing_address_address_type (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: address_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: attention_line (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: city (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: country_code (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: latitude (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: longitude (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: postal_code (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: state_province (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: street_line1 (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: street_line2 (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: shipping_address_address_type (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: address_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: attention_line (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: city (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: country_code (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: facility_name (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: latitude (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: longitude (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: is_residential (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: postal_code (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: requires_inside_delivery (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: requires_liftgate (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: state_province (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: street_line1 (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: street_line2 (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: company_name (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: contact_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: email (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: full_name (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: job_title (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: phone (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: contact_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: email (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: full_name (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: job_title (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: phone (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: available_credit (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: credit_limit (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: current_balance (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: is_credit_hold (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: payment_terms_days (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: risk_rating (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: customer_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: duns_number (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: tax_registration_number (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: external_purchase_order_number (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: freight_amount (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: carrier_routing_carrier_code (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: carrier_routing_service_level (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: bol_number (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: carrier_name (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: estimated_transit_days (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: insurance_coverage_amount (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: is_temperature_controlled (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: pro_number (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: scac_code (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: total_gross_weight_kg (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: total_pallet_count (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: incoterms (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: time_zone (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: warehouse_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: warehouse_name (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: promised_ship_date (DATE)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: requested_delivery_date (DATE)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: contract_effective_date (DATE)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: contract_expiration_date (DATE)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: discount_tier_percentage (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: is_auto_renew (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: master_agreement_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: distribution_channel (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: division_code (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: sales_org_code (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: commission_rate (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: rep_email (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: rep_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: rep_name (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: territory_code (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: source_system (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: is_backorder_allowed (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: line_item_hazmat (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: line_item_item_category (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: line_item_line_number (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: extended_net_amount (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: allocated_warehouse_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: allocation_status (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: allocation_timestamp (TIMESTAMP_NTZ)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: bin_location (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: lot_number (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: is_drop_ship (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: is_taxable (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: line_discount_amount (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: line_item_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: line_tax_amount (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: line_tax_rate (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: manufacturer_part_number (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: country_of_origin (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: dimensions_cm (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: harmonized_tariff_code (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: unit_weight_kg (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: product_family (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: product_name (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: requested_ship_date (DATE)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: unit_of_measure (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: includes_onsite_response (BOOLEAN)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: warranty_duration_months (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: warranty_plan_code (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: net_payable_amount (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: order_status (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: payment_details_payment_method (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: authorization_code (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: authorized_timestamp (TIMESTAMP_NTZ)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: billing_currency (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: exchange_rate_to_usd (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: installment_installment_number (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: due_date (DATE)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: installment_amount (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: installment_id (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: installment_percentage (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: installment_status (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: payment_status (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: priority_score (NUMBER(18,0))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: tax_amount (NUMBER(18,4))
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- BREAKING: drop NOT NULL / required contract on /Order/CustomerId (customer_id)
ALTER TABLE staging_orders ALTER COLUMN customer_id DROP NOT NULL;
```

## Downstream Impact (Read from DataHub at C3)

- Staging Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,staging_orders,PROD)
- Curated SCD2 Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,curated_orders,PROD)
- SLA Dashboard: v_sla_dashboard_orders
- Data Steward: data-steward@enterprise.io
- Engineering Owner: data-eng@enterprise.io
