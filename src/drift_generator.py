"""On-Demand Synthetic XML Feed & Drift Generator for Hierarchical Bond Analytics."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import random
from typing import Literal

COUNTRIES = ["GB", "US", "DE", "FR", "JP", "CA", "AU", "CH", "NL", "SG", "IT", "ES", "BR", "IN"]
CNTRY_SRCS = ["L", "NL", "B", "M", "R", "IDX", "ISO"]
CNTRY_TYPES = ["IDX", "DOM", "RISK", "INCORP", "LEGAL"]
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"]
DATE_CONVS = ["30E360", "ACT360", "ACTACT", "30360"]
CALL_TYPES = ["A", "E", "B", "N", "X"]
CPN_TYPES = ["F", "V", "Z", "S"]
COUP_FREQS = ["S", "A", "Q", "M"]

COMPANIES = [
    "GLOBAL AUTO HOLDINGS PLC",
    "APEX FINANCIAL CORP",
    "TITAN ENERGY LOGISTICS LLC",
    "VORTEX PHARMACEUTICALS INC",
    "QUANTUM SEMICONDUCTOR NV",
    "BEACON REAL ESTATE TRUST",
    "SOLARIS INFRASTRUCTURE LTD",
    "NEXUS TELECOM GROUP SA",
    "ORION DEFENSE AEROSPACE PLC",
    "ZENITH MARITIME CARRIERS",
    "AURA RENEWABLE ASSETS INC",
    "HORIZON CYBERSECURITY GROUP",
]


def generate_synthetic_xml(
    output_path: Path,
    record_count: int = 500,
    drift_mode: Literal["none", "additive", "breaking", "corrupt_size", "rating_child_set"] = "none",
) -> dict[str, str | int]:
    """Generates an XML feed matching the production hierarchy with optional drift injection."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    today_str = datetime.now(timezone.utc).strftime("%m/%d/%Y")

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<ASSETS ASOF_DATE="{today_str}" CREATE_DATE="{today_str}" RECORDS="{record_count}">',
    ]

    for idx in range(1, record_count + 1):
        country = random.choice(COUNTRIES)
        company = random.choice(COMPANIES)
        amt_isu = random.choice([50000000, 100000000, 250000000, 500000000, 1000000000])
        coupon_fix = f"{random.uniform(2.5, 11.5):.3f}"
        cusip = f"{idx:04d}{random.choice(['AA', 'AB', 'BA', 'GAA'])}{random.randint(1, 9)}"

        # Breaking drift mutation on selected rows
        if drift_mode == "breaking" and idx % 25 == 0:
            amt_isu_str = f"INVALID_AMOUNT_${amt_isu:,}"
        else:
            amt_isu_str = str(amt_isu)

        # Build COUNTRY_CLASSIFICATION_record set
        cc_records = []
        for _ in range(2):
            c_src = random.choice(CNTRY_SRCS)
            c_type = random.choice(CNTRY_TYPES)
            cc_records.append(
                f"            <COUNTRY_CLASSIFICATION_record>\n"
                f"                <CNTRY>{country}</CNTRY>\n"
                f"                <CNTRY_SRC>{c_src}</CNTRY_SRC>\n"
                f"                <CNTRY_TYPE>{c_type}</CNTRY_TYPE>\n"
                f"            </COUNTRY_CLASSIFICATION_record>"
            )
        cc_block = "\n".join(cc_records)

        # Build CUSIP2_record cross symbologies
        isin = f"{country}{random.randint(100000000, 999999999)}{random.randint(0, 9)}"
        sedol = f"{random.choice(['B', 'C', 'D'])}{random.randint(10000, 99999)}{random.randint(0, 9)}"
        ric = f"0x{random.randint(10000000, 99999999):08x}cfc00ac{random.randint(1, 9)}"
        wkn = f"A{random.randint(100, 999)}T{random.randint(10, 99)}"

        c2_records = [
            f"            <CUSIP2_record>\n                <CODE>A</CODE>\n                <IDENTIFIER>{cusip}</IDENTIFIER>\n            </CUSIP2_record>",
            f"            <CUSIP2_record>\n                <CODE>C</CODE>\n                <IDENTIFIER>{sedol}</IDENTIFIER>\n            </CUSIP2_record>",
            f"            <CUSIP2_record>\n                <CODE>I</CODE>\n                <IDENTIFIER>{isin}</IDENTIFIER>\n            </CUSIP2_record>",
            f"            <CUSIP2_record>\n                <CODE>R</CODE>\n                <IDENTIFIER>{ric}</IDENTIFIER>\n            </CUSIP2_record>",
            f"            <CUSIP2_record>\n                <CODE>W</CODE>\n                <IDENTIFIER>{wkn}</IDENTIFIER>\n            </CUSIP2_record>",
        ]

        # In corrupt_size mode: inject cardinality mismatch
        declared_size = 5
        if drift_mode == "corrupt_size" and idx % 10 == 0:
            c2_records.pop()  # Remove 1 record so actual count = 4 while declared SIZE = 5

        c2_block = "\n".join(c2_records)

        # Build CUSIP_ALIAS_record
        alias_id = random.randint(100000000, 999999999)
        alias_block = (
            f"            <CUSIP_ALIAS_record>\n"
            f"                <CODE>{random.randint(8000, 8999)}</CODE>\n"
            f"                <IDENTIFIER>{alias_id}</IDENTIFIER>\n"
            f"                <PURPOSE>DEBTID</PURPOSE>\n"
            f"            </CUSIP_ALIAS_record>"
        )

        # Additive drift injection
        additive_tags = ""
        if drift_mode == "additive":
            esg_score = random.randint(45, 98)
            green_flag = random.choice(["Y", "N"])
            additive_tags = (
                f"            <ESG_SCORE>{esg_score}</ESG_SCORE>\n"
                f"            <GREEN_BOND_FLAG>{green_flag}</GREEN_BOND_FLAG>\n"
            )
        elif drift_mode == "rating_child_set":
            rating_moodys = random.choice(["Aaa", "Aa1", "Aa2", "A1", "Baa1"])
            rating_sp = random.choice(["AAA", "AA+", "AA", "A+", "BBB+"])
            additive_tags = (
                f"            <RATING_set SIZE=\"2\">\n"
                f"                <RATING_record>\n"
                f"                    <AGENCY>MOODYS</AGENCY>\n"
                f"                    <RATING>{rating_moodys}</RATING>\n"
                f"                </RATING_record>\n"
                f"                <RATING_record>\n"
                f"                    <AGENCY>SP</AGENCY>\n"
                f"                    <RATING>{rating_sp}</RATING>\n"
                f"                </RATING_record>\n"
                f"            </RATING_set>\n"
            )

        asset_block = f"""    <ASSET>
        <BND_CORP>
            <CLASS>BND_CORP</CLASS>
            <ACCRUAL_DT>1/22/2024</ACCRUAL_DT>
            <AMT_ISU>{amt_isu_str}</AMT_ISU>
            <ANNOUNCE_DT>1/8/2024</ANNOUNCE_DT>
            <CALC_TYPE>1</CALC_TYPE>
            <CALL_MANDATORY>N</CALL_MANDATORY>
            <CALL_TYPE>A</CALL_TYPE>
            <CD_INSTMT_TYPE>UNKNOWN</CD_INSTMT_TYPE>
            <CHANGE_DT>4/23/2026 16:37:39.590</CHANGE_DT>
            <COMPOUND_FLAG>0</COMPOUND_FLAG>
            <COUNTRY>{country}</COUNTRY>
            <COUNTRY_CLASSIFICATION_set SIZE="2">
{cc_block}
            </COUNTRY_CLASSIFICATION_set>
            <COUPON_FIX>{coupon_fix}</COUPON_FIX>
            <COUP_FREQ>S</COUP_FREQ>
            <CPN_TYPE>F</CPN_TYPE>
            <CURRENCY>USD</CURRENCY>
            <CUSIP>{cusip}</CUSIP>
            <CUSIP2_set SIZE="{declared_size}">
{c2_block}
            </CUSIP2_set>
            <CUSIP_ALIAS_set SIZE="1">
{alias_block}
            </CUSIP_ALIAS_set>
            <CUSIP_TYPE>CUSIP</CUSIP_TYPE>
            <DATE_CONV>30E360</DATE_CONV>
            <DESC_INSTMT>{company}</DESC_INSTMT>
            <END_ADJ_FLAG>N</END_ADJ_FLAG>
            <FIRST_PAY_DT>7/15/2024</FIRST_PAY_DT>
            <FIRST_SETTLE_DT>1/22/2024</FIRST_SETTLE_DT>
            <FLAG_144A>Y</FLAG_144A>
{additive_tags}        </BND_CORP>
    </ASSET>"""
        lines.append(asset_block)

    lines.append("</ASSETS>")
    full_xml = "\n".join(lines)
    output_path.write_text(full_xml, encoding="utf-8")

    return {
        "file_path": str(output_path),
        "file_size_bytes": len(full_xml.encode("utf-8")),
        "record_count": record_count,
        "drift_mode": drift_mode,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic XML Feed Generator")
    parser.add_argument("--output", "-o", default="samples/analytics/synthetic_feed.xml")
    parser.add_argument("--count", "-n", type=int, default=500)
    parser.add_argument("--drift", "-d", choices=["none", "additive", "breaking", "corrupt_size"], default="none")
    args = parser.parse_args()

    meta = generate_synthetic_xml(Path(args.output), args.count, args.drift)
    print(f"Generated synthetic XML: {meta['file_path']} ({meta['file_size_bytes']:,} bytes, {meta['record_count']} assets, drift={meta['drift_mode']})")


if __name__ == "__main__":
    main()
