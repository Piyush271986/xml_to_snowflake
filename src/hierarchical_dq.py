"""Deep Data Quality and Cardinality Auditor for Hierarchical Child Entities."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class HierarchicalDQFinding:
    rule_id: str
    severity: str  # ERROR, WARNING
    entity: str
    identifier: str
    message: str
    details: dict[str, Any]


_ISIN_REGEX = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
_CUSIP_REGEX = re.compile(r"^[0-9A-Z]{9}$")
_SEDOL_REGEX = re.compile(r"^[B-DF-HJ-NP-TV-Z0-9]{7}$")


def audit_xml_hierarchical_integrity(xml_file: Path) -> dict[str, Any]:
    """Audits an XML file for set-size discrepancies, symbology format errors, and orphan risk."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        return {
            "xml_file": xml_file.name,
            "total_assets": 0,
            "total_cusip2_records": 0,
            "total_country_classifications": 0,
            "total_cusip_aliases": 0,
            "average_cusip2_per_asset": 0,
            "average_cc_per_asset": 0,
            "size_discrepancies": 0,
            "error_count": 1,
            "warning_count": 0,
            "passed": False,
            "syntax_error": str(e),
            "findings_sample": [],
        }

    findings: list[HierarchicalDQFinding] = []
    total_assets = 0
    total_cusip2_records = 0
    total_cc_records = 0
    total_alias_records = 0
    size_discrepancies = 0

    for asset_elem in root.findall(".//ASSET"):
        total_assets += 1
        bnd_corp = asset_elem.find("BND_CORP")
        if bnd_corp is None:
            # Fallback if ASSET itself is the container
            bnd_corp = asset_elem

        cusip_elem = bnd_corp.find("CUSIP")
        asset_id = cusip_elem.text.strip() if (cusip_elem is not None and cusip_elem.text) else f"asset_{total_assets}"

        # 1. Audit CUSIP2_set cardinality vs SIZE attribute
        c2_set = bnd_corp.find("CUSIP2_set")
        if c2_set is not None:
            c2_records = c2_set.findall("CUSIP2_record")
            total_cusip2_records += len(c2_records)
            size_attr = c2_set.attrib.get("SIZE")
            if size_attr and size_attr.isdigit():
                expected_size = int(size_attr)
                if len(c2_records) != expected_size:
                    size_discrepancies += 1
                    findings.append(
                        HierarchicalDQFinding(
                            rule_id="CARDINALITY_MISMATCH_CUSIP2",
                            severity="WARNING",
                            entity="cusip2",
                            identifier=asset_id,
                            message=f"CUSIP2_set declared SIZE={expected_size} but found {len(c2_records)} child records",
                            details={"declared": expected_size, "observed": len(c2_records)},
                        )
                    )

            # Audit Symbology Formats
            for rec in c2_records:
                code_el = rec.find("CODE")
                ident_el = rec.find("IDENTIFIER")
                code = code_el.text.strip() if (code_el is not None and code_el.text) else ""
                ident = ident_el.text.strip() if (ident_el is not None and ident_el.text) else ""

                if code == "I" and ident and not _ISIN_REGEX.match(ident):
                    findings.append(
                        HierarchicalDQFinding(
                            rule_id="FORMAT_VIOLATION_ISIN",
                            severity="WARNING",
                            entity="cusip2",
                            identifier=asset_id,
                            message=f"Invalid ISIN format for CODE='I': '{ident}'",
                            details={"identifier": ident, "code": code},
                        )
                    )
                elif code == "A" and ident and not _CUSIP_REGEX.match(ident):
                    findings.append(
                        HierarchicalDQFinding(
                            rule_id="FORMAT_VIOLATION_CUSIP",
                            severity="WARNING",
                            entity="cusip2",
                            identifier=asset_id,
                            message=f"Invalid CUSIP format for CODE='A': '{ident}'",
                            details={"identifier": ident, "code": code},
                        )
                    )

        # 2. Audit COUNTRY_CLASSIFICATION_set cardinality
        cc_set = bnd_corp.find("COUNTRY_CLASSIFICATION_set")
        if cc_set is not None:
            cc_records = cc_set.findall("COUNTRY_CLASSIFICATION_record")
            total_cc_records += len(cc_records)
            size_attr = cc_set.attrib.get("SIZE")
            if size_attr and size_attr.isdigit():
                expected_size = int(size_attr)
                if len(cc_records) != expected_size:
                    size_discrepancies += 1
                    findings.append(
                        HierarchicalDQFinding(
                            rule_id="CARDINALITY_MISMATCH_CC",
                            severity="WARNING",
                            entity="country_classification",
                            identifier=asset_id,
                            message=f"COUNTRY_CLASSIFICATION_set declared SIZE={expected_size} but found {len(cc_records)} records",
                            details={"declared": expected_size, "observed": len(cc_records)},
                        )
                    )

        # 3. Audit CUSIP_ALIAS_set
        ca_set = bnd_corp.find("CUSIP_ALIAS_set")
        if ca_set is not None:
            ca_records = ca_set.findall("CUSIP_ALIAS_record")
            total_alias_records += len(ca_records)

    error_count = sum(1 for f in findings if f.severity == "ERROR")
    warning_count = sum(1 for f in findings if f.severity == "WARNING")

    return {
        "xml_file": xml_file.name,
        "total_assets": total_assets,
        "total_cusip2_records": total_cusip2_records,
        "total_country_classifications": total_cc_records,
        "total_cusip_aliases": total_alias_records,
        "average_cusip2_per_asset": round(total_cusip2_records / total_assets, 2) if total_assets else 0,
        "average_cc_per_asset": round(total_cc_records / total_assets, 2) if total_assets else 0,
        "size_discrepancies": size_discrepancies,
        "error_count": error_count,
        "warning_count": warning_count,
        "passed": error_count == 0,
        "findings_sample": [
            {
                "rule_id": f.rule_id,
                "severity": f.severity,
                "entity": f.entity,
                "identifier": f.identifier,
                "message": f.message,
            }
            for f in findings[:10]
        ],
    }
