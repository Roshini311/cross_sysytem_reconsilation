from decimal import Decimal
import pytest
from reconciliation.services.comparator import reconcile_records
from reconciliation.services.normalizer import normalize_record_ref, normalize_decimal


LOCATION_ORG_MAP = {
    "LOC_101": "ORG_ALPHA",
    "LOC_102": "ORG_ALPHA",
    "LOC_201": "ORG_BETA",
}


def test_detects_record_missing_in_system_b():
    records_a = [
        {"record_id": "REC-001", "location_id": "LOC_101", "raw_value": "100.00", "normalized_value": Decimal("100.00")}
    ]
    records_b = []

    results = reconcile_records(records_a, records_b, LOCATION_ORG_MAP)

    assert len(results) == 1
    assert results[0]["reason"] == "MISSING_IN_SYSTEM_B"
    assert results[0]["record_id"] == "REC-001"
    assert results[0]["org_id"] == "ORG_ALPHA"
    assert results[0]["system_a_value"] == "100.00"
    assert results[0]["system_b_value"] is None


def test_detects_orphan_record_in_system_b():
    records_a = []
    records_b = [
        {"record_ref": "REC-999", "normalized_record_ref": "REC-999", "location_id": "LOC_101", "raw_value": "50.00", "normalized_value": Decimal("50.00")}
    ]

    results = reconcile_records(records_a, records_b, LOCATION_ORG_MAP)

    assert len(results) == 1
    assert results[0]["reason"] == "ORPHAN_IN_SYSTEM_B"
    assert results[0]["record_id"] == "REC-999"
    assert results[0]["org_id"] == "ORG_ALPHA"
    assert results[0]["system_a_value"] is None
    assert results[0]["system_b_value"] == "50.00"


def test_detects_duplicate_entries_in_system_b():
    records_a = [
        {"record_id": "REC-001", "location_id": "LOC_101", "raw_value": "100.00", "normalized_value": Decimal("100.00")}
    ]
    records_b = [
        {"record_ref": "REC-001", "normalized_record_ref": "REC-001", "location_id": "LOC_101", "raw_value": "100.00", "normalized_value": Decimal("100.00")},
        {"record_ref": "REC-001", "normalized_record_ref": "REC-001", "location_id": "LOC_101", "raw_value": "105.00", "normalized_value": Decimal("105.00")},
    ]

    results = reconcile_records(records_a, records_b, LOCATION_ORG_MAP)

    assert len(results) == 2
    for item in results:
        assert item["reason"] == "DUPLICATE_IN_SYSTEM_B"
        assert item["record_id"] == "REC-001"
        assert item["org_id"] == "ORG_ALPHA"


def test_detects_value_mismatch():
    records_a = [
        {"record_id": "REC-001", "location_id": "LOC_101", "raw_value": "100.00", "normalized_value": Decimal("100.00")}
    ]
    records_b = [
        {"record_ref": "REC-001", "normalized_record_ref": "REC-001", "location_id": "LOC_101", "raw_value": "120.00", "normalized_value": Decimal("120.00")}
    ]

    results = reconcile_records(records_a, records_b, LOCATION_ORG_MAP)

    assert len(results) == 1
    assert results[0]["reason"] == "VALUE_MISMATCH"
    assert results[0]["system_a_value"] == "100.00"
    assert results[0]["system_b_value"] == "120.00"


def test_formatted_decimal_equivalence_is_not_mismatch():
    # A=100.00, B="$100.00" must NOT be flagged as mismatch
    records_a = [
        {"record_id": "REC-001", "location_id": "LOC_101", "raw_value": "100.00", "normalized_value": Decimal("100.00")}
    ]
    records_b = [
        {"record_ref": "REC-001", "normalized_record_ref": "REC-001", "location_id": "LOC_101", "raw_value": "$100.00", "normalized_value": Decimal("100.00")}
    ]

    results = reconcile_records(records_a, records_b, LOCATION_ORG_MAP)

    assert len(results) == 0  # Perfect match after Decimal normalization!


def test_tenant_boundary_isolation():
    # System A record belongs to ORG_ALPHA (LOC_101)
    # System B entry has same reference but belongs to ORG_BETA (LOC_201)
    records_a = [
        {"record_id": "REC-001", "location_id": "LOC_101", "raw_value": "100.00", "normalized_value": Decimal("100.00")}
    ]
    records_b = [
        {"record_ref": "REC-001", "normalized_record_ref": "REC-001", "location_id": "LOC_201", "raw_value": "100.00", "normalized_value": Decimal("100.00")}
    ]

    # Querying for ORG_ALPHA only
    alpha_results = reconcile_records(records_a, records_b, LOCATION_ORG_MAP, target_org_id="ORG_ALPHA")
    assert len(alpha_results) == 1
    assert alpha_results[0]["reason"] == "MISSING_IN_SYSTEM_B"
    assert alpha_results[0]["org_id"] == "ORG_ALPHA"

    # Querying for ORG_BETA only
    beta_results = reconcile_records(records_a, records_b, LOCATION_ORG_MAP, target_org_id="ORG_BETA")
    assert len(beta_results) == 1
    assert beta_results[0]["reason"] == "ORPHAN_IN_SYSTEM_B"
    assert beta_results[0]["org_id"] == "ORG_BETA"


def test_dirty_reference_normalization_matching():
    # Variants: "REC-001", " rec_001 ", "REC001", "001"
    assert normalize_record_ref("REC-001") == "REC-001"
    assert normalize_record_ref(" rec_001 ") == "REC-001"
    assert normalize_record_ref("REC001") == "REC-001"
    assert normalize_record_ref("001") == "REC-001"

    records_a = [
        {"record_id": "REC-001", "location_id": "LOC_101", "raw_value": "100.00", "normalized_value": Decimal("100.00")}
    ]
    records_b = [
        {"record_ref": " rec_001 ", "normalized_record_ref": "REC-001", "location_id": "LOC_101", "raw_value": "100.00", "normalized_value": Decimal("100.00")}
    ]

    results = reconcile_records(records_a, records_b, LOCATION_ORG_MAP)
    assert len(results) == 0  # Dirty reference matched successfully!
