"""Generates representative sample XML files for onboarding and drift testing."""
from __future__ import annotations

from pathlib import Path


def generate_samples(base_dir: Path) -> None:
    orders_dir = base_dir / "samples" / "orders"
    drift_dir = base_dir / "samples" / "orders_drift"
    orders_dir.mkdir(parents=True, exist_ok=True)
    drift_dir.mkdir(parents=True, exist_ok=True)

    samples = [
        {
            "file": "order_001.xml",
            "currency": "USD",
            "order_id": "10001",
            "customer_id": "CUST-501",
            "order_date": "2026-10-15",
            "order_ts": "2026-10-15T09:14:22",
            "expedited": "true",
            "total": "249.50",
            "discount": "15.00",
            "notes": "Leave at front desk",
            "items": [
                ("SKU-101", "2", "99.75"),
                ("SKU-204", "1", "50.00"),
            ],
        },
        {
            "file": "order_002.xml",
            "currency": "EUR",
            "order_id": "10002",
            "customer_id": "CUST-502",
            "order_date": "2026-10-15",
            "order_ts": "2026-10-15T10:30:00",
            "expedited": "false",
            "total": "89.99",
            "discount": None,
            "notes": None,
            "items": [
                ("SKU-305", "1", "89.99"),
            ],
        },
        {
            "file": "order_003.xml",
            "currency": "USD",
            "order_id": "10003",
            "customer_id": "CUST-503",
            "order_date": "2026-10-16",
            "order_ts": "2026-10-16T11:45:10",
            "expedited": "true",
            "total": "420.00",
            "discount": "20.00",
            "notes": "Signature required",
            "items": [
                ("SKU-101", "3", "100.00"),
                ("SKU-410", "2", "60.00"),
            ],
        },
        {
            "file": "order_004.xml",
            "currency": "GBP",
            "order_id": "10004",
            "customer_id": "CUST-504",
            "order_date": "2026-10-16",
            "order_ts": "2026-10-16T14:20:05",
            "expedited": "false",
            "total": "150.25",
            "discount": None,
            "notes": "Call on arrival",
            "items": [
                ("SKU-204", "3", "50.08"),
            ],
        },
        {
            "file": "order_005.xml",
            "currency": "USD",
            "order_id": "10005",
            "customer_id": "CUST-501",
            "order_date": "2026-10-17",
            "order_ts": "2026-10-17T08:05:44",
            "expedited": "false",
            "total": "64.00",
            "discount": "5.00",
            "notes": None,
            "items": [
                ("SKU-512", "4", "16.00"),
            ],
        },
        {
            "file": "order_006.xml",
            "currency": "USD",
            "order_id": "10006",
            "customer_id": "CUST-506",
            "order_date": "2026-10-17",
            "order_ts": "2026-10-17T16:12:30",
            "expedited": "true",
            "total": "980.00",
            "discount": "50.00",
            "notes": "Fragile handle with care",
            "items": [
                ("SKU-900", "1", "500.00"),
                ("SKU-901", "2", "240.00"),
            ],
        },
        {
            "file": "order_007.xml",
            "currency": "CAD",
            "order_id": "10007",
            "customer_id": "CUST-507",
            "order_date": "2026-10-18",
            "order_ts": "2026-10-18T12:00:00",
            "expedited": "false",
            "total": "35.50",
            "discount": None,
            "notes": None,
            "items": [
                ("SKU-115", "1", "35.50"),
            ],
        },
        {
            "file": "order_008.xml",
            "currency": "USD",
            "order_id": "10008",
            "customer_id": "CUST-508",
            "order_date": "2026-10-18",
            "order_ts": "2026-10-18T17:40:19",
            "expedited": "true",
            "total": "310.75",
            "discount": "10.25",
            "notes": "Deliver to loading dock B",
            "items": [
                ("SKU-204", "2", "50.00"),
                ("SKU-305", "1", "89.99"),
                ("SKU-512", "5", "24.15"),
            ],
        },
        {
            "file": "order_009.xml",
            "currency": "EUR",
            "order_id": "10009",
            "customer_id": "CUST-509",
            "order_date": "2026-10-19",
            "order_ts": "2026-10-19T09:55:01",
            "expedited": "false",
            "total": "120.00",
            "discount": None,
            "notes": "Ring bell twice",
            "items": [
                ("SKU-410", "2", "60.00"),
            ],
        },
        {
            "file": "order_010.xml",
            "currency": "USD",
            "order_id": "10010",
            "customer_id": "CUST-510",
            "order_date": "2026-10-19",
            "order_ts": "2026-10-19T19:02:11",
            "expedited": "false",
            "total": "199.50",
            "discount": None,
            "notes": None,
            "items": [
                ("SKU-101", "2", "99.75"),
            ],
        },
    ]

    for s in samples:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<Order currency="{s["currency"]}">',
            f'    <OrderId>{s["order_id"]}</OrderId>',
            f'    <CustomerId>{s["customer_id"]}</CustomerId>',
            f'    <OrderDate>{s["order_date"]}</OrderDate>',
            f'    <OrderTimestamp>{s["order_ts"]}</OrderTimestamp>',
            f'    <IsExpedited>{s["expedited"]}</IsExpedited>',
            f'    <TotalAmount>{s["total"]}</TotalAmount>',
        ]
        if s["discount"] is not None:
            lines.append(f'    <DiscountAmount>{s["discount"]}</DiscountAmount>')
        if s["notes"] is not None:
            lines.append(f'    <ShippingNotes>{s["notes"]}</ShippingNotes>')
        lines.append("    <LineItems>")
        for sku, qty, price in s["items"]:
            lines.extend([
                "        <LineItem>",
                f"            <ProductCode>{sku}</ProductCode>",
                f"            <Quantity>{qty}</Quantity>",
                f"            <UnitPrice>{price}</UnitPrice>",
                "        </LineItem>",
            ])
        lines.append("    </LineItems>")
        lines.append("</Order>")
        (orders_dir / s["file"]).write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 1. Additive drift sample (adds optional PromoCode & LoyaltyTier)
    (drift_dir / "order_additive_drift.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<Order currency="USD">
    <OrderId>10011</OrderId>
    <CustomerId>CUST-511</CustomerId>
    <OrderDate>2026-10-20</OrderDate>
    <OrderTimestamp>2026-10-20T10:15:00</OrderTimestamp>
    <IsExpedited>true</IsExpedited>
    <TotalAmount>175.00</TotalAmount>
    <PromoCode>AUTUMN25</PromoCode>
    <LoyaltyTier>GOLD</LoyaltyTier>
    <LineItems>
        <LineItem>
            <ProductCode>SKU-101</ProductCode>
            <Quantity>1</Quantity>
            <UnitPrice>175.00</UnitPrice>
        </LineItem>
    </LineItems>
</Order>
""",
        encoding="utf-8",
    )

    # 2. Breaking drift sample (OrderId changed to alphanumeric string, required OrderDate removed, element renamed)
    (drift_dir / "order_breaking_drift.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<Order currency="USD">
    <OrderId>ORD-BREAKING-999</OrderId>
    <CustomerId>CUST-512</CustomerId>
    <OrderTimestamp>2026-10-20T11:00:00</OrderTimestamp>
    <IsExpedited>false</IsExpedited>
    <TotalOrderValue>320.00</TotalOrderValue>
    <LineItems>
        <LineItem>
            <ProductCode>SKU-204</ProductCode>
            <Quantity>TWO</Quantity>
            <UnitPrice>160.00</UnitPrice>
        </LineItem>
    </LineItems>
</Order>
""",
        encoding="utf-8",
    )

    # 3. Malformed XML sample (fails G1 File check)
    (drift_dir / "order_malformed.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<Order currency="USD">
    <OrderId>10013</OrderId>
    <CustomerId>CUST-513
    <!-- Missing closing tags -->
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    generate_samples(Path(__file__).resolve().parent.parent)
