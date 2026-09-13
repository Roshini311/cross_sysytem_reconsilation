from decimal import Decimal
from typing import List, Dict, Any, Optional
from reconciliation.services.normalizer import normalize_record_ref, normalize_decimal


def reconcile_records(
    records_a: List[Any],
    records_b: List[Any],
    location_org_map: Dict[str, str],
    target_org_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Pure Python reconciliation engine.
    
    Receives lists of System A records and System B entries, along with
    location_id -> org_id mapping.
    
    If target_org_id is provided, filters inputs strictly to that tenant before matching.
    
    Returns a list of discrepancy dicts with keys:
      - record_id
      - location_id
      - org_id
      - reason
      - system_a_value
      - system_b_value
    """
    # 1. Filter by target_org_id if specified (Enforce strict tenant boundary)
    if target_org_id:
        records_a = [r for r in records_a if location_org_map.get(getattr(r, 'location_id', r.get('location_id') if isinstance(r, dict) else '')) == target_org_id]
        records_b = [r for r in records_b if location_org_map.get(getattr(r, 'location_id', r.get('location_id') if isinstance(r, dict) else '')) == target_org_id]

    # Helper getters for Model instances vs Dicts
    def get_attr(item: Any, name: str, default: Any = "") -> Any:
        if isinstance(item, dict):
            return item.get(name, default)
        return getattr(item, name, default)

    discrepancies: List[Dict[str, Any]] = []

    # Map records by (tenant_org_id, normalized_ref)
    a_by_key: Dict[tuple, List[Any]] = {}
    for a in records_a:
        loc_id = get_attr(a, 'location_id')
        org_id = location_org_map.get(loc_id, 'UNKNOWN_ORG')
        rec_id = get_attr(a, 'record_id')
        norm_id = normalize_record_ref(rec_id)
        key = (org_id, norm_id)
        a_by_key.setdefault(key, []).append(a)

    b_by_key: Dict[tuple, List[Any]] = {}
    for b in records_b:
        loc_id = get_attr(b, 'location_id')
        org_id = location_org_map.get(loc_id, 'UNKNOWN_ORG')
        rec_ref = get_attr(b, 'record_ref')
        norm_ref = get_attr(b, 'normalized_record_ref') or normalize_record_ref(rec_ref)
        key = (org_id, norm_ref)
        b_by_key.setdefault(key, []).append(b)

    all_keys = set(a_by_key.keys()).union(set(b_by_key.keys()))

    for key in sorted(all_keys, key=lambda k: (k[0], k[1])):
        org_id, norm_ref = key
        a_list = a_by_key.get(key, [])
        b_list = b_by_key.get(key, [])

        # PASS 1: DUPLICATES IN SYSTEM B
        if len(b_list) > 1:
            for b in b_list:
                loc_id = get_attr(b, 'location_id')
                raw_b_val = get_attr(b, 'raw_value')
                # If there's an A record, show its value; otherwise None
                sys_a_val = get_attr(a_list[0], 'raw_value') if len(a_list) == 1 else None
                discrepancies.append({
                    "record_id": get_attr(b, 'record_ref'),
                    "location_id": loc_id,
                    "org_id": org_id,
                    "reason": "DUPLICATE_IN_SYSTEM_B",
                    "system_a_value": sys_a_val,
                    "system_b_value": raw_b_val,
                })
            continue

        # PASS 2: MISSING IN SYSTEM B
        if len(a_list) > 0 and len(b_list) == 0:
            for a in a_list:
                loc_id = get_attr(a, 'location_id')
                raw_a_val = get_attr(a, 'raw_value')
                discrepancies.append({
                    "record_id": get_attr(a, 'record_id'),
                    "location_id": loc_id,
                    "org_id": org_id,
                    "reason": "MISSING_IN_SYSTEM_B",
                    "system_a_value": raw_a_val,
                    "system_b_value": None,
                })
            continue

        # PASS 3: ORPHAN IN SYSTEM B
        if len(a_list) == 0 and len(b_list) == 1:
            b = b_list[0]
            loc_id = get_attr(b, 'location_id')
            raw_b_val = get_attr(b, 'raw_value')
            discrepancies.append({
                "record_id": get_attr(b, 'record_ref'),
                "location_id": loc_id,
                "org_id": org_id,
                "reason": "ORPHAN_IN_SYSTEM_B",
                "system_a_value": None,
                "system_b_value": raw_b_val,
            })
            continue

        # PASS 4: VALUE MISMATCH (1-to-1 match within same tenant)
        if len(a_list) >= 1 and len(b_list) == 1:
            for a in a_list:
                b = b_list[0]
                loc_id = get_attr(a, 'location_id')

                a_dec = get_attr(a, 'normalized_value')
                b_dec = get_attr(b, 'normalized_value')
                raw_a = get_attr(a, 'raw_value')
                raw_b = get_attr(b, 'raw_value')

                # Parse Decimal if not already populated on dictionary objects
                if a_dec is None and raw_a != "":
                    a_dec, _ = normalize_decimal(raw_a)
                if b_dec is None and raw_b != "":
                    b_dec, _ = normalize_decimal(raw_b)

                is_mismatch = False

                if a_dec is not None and b_dec is not None:
                    if a_dec != b_dec:
                        is_mismatch = True
                else:
                    # Fallback to string comparison if one or both cannot be parsed to Decimal
                    if raw_a.strip() != raw_b.strip():
                        is_mismatch = True

                if is_mismatch:
                    discrepancies.append({
                        "record_id": get_attr(a, 'record_id'),
                        "location_id": loc_id,
                        "org_id": org_id,
                        "reason": "VALUE_MISMATCH",
                        "system_a_value": raw_a,
                        "system_b_value": raw_b,
                    })

    return discrepancies

