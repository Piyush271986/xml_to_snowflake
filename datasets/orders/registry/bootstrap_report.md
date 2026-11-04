# C0 Schema Bootstrap Report — `orders`

- **Samples Analyzed:** 10 valid XML files
- **Root Element:** `/Order`
- **Inferred Business Keys:** `order_id, line_item_product_code`
- **Total Inferred Fields:** 12 (3 array fields)
- **Low-Confidence Fields (< 0.8):** 2

## Inferred Field Inventory

| XPath | Column | Snowflake Type | Required | Array (`LATERAL FLATTEN`) | Confidence | Status |
|---|---|---|---|---|---|---|
| `/Order/@currency` | `currency_code` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/OrderId` | `order_id` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/CustomerId` | `customer_id` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/OrderDate` | `order_date` | `DATE` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/OrderTimestamp` | `order_timestamp` | `TIMESTAMP_NTZ` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/IsExpedited` | `is_expedited` | `BOOLEAN` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/TotalAmount` | `total_amount` | `NUMBER(18,4)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/Order/DiscountAmount` | `discount_amount` | `NUMBER(18,4)` | `False` | `False` | `0.50` | ⚠️ Steward Review Needed |
| `/Order/ShippingNotes` | `shipping_notes` | `VARCHAR` | `False` | `False` | `0.60` | ⚠️ Steward Review Needed |
| `/Order/LineItems/LineItem/ProductCode` | `line_item_product_code` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/Quantity` | `line_item_quantity` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/Order/LineItems/LineItem/UnitPrice` | `line_item_unit_price` | `NUMBER(18,4)` | `True` | `True` | `1.00` | ✅ High Confidence |

## ⚠️ Low-Confidence Fields Flagged for C3 Steward Review

- **`discount_amount`** (`/Order/DiscountAmount`): observed in 5/10 samples (`confidence=0.5`). Marked `required: false` with type `NUMBER(18,4)`.
- **`shipping_notes`** (`/Order/ShippingNotes`): observed in 6/10 samples (`confidence=0.6`). Marked `required: false` with type `VARCHAR`.
