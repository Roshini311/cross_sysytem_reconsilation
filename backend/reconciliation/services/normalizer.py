import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple


def normalize_record_ref(raw_ref: Optional[str]) -> str:
    """
    Normalizes dirty record reference strings.
    
    Examples:
    "REC-001" -> "REC-001"
    " rec_001 " -> "REC-001"
    "REC001" -> "REC-001"
    "001" -> "REC-001"
    """
    if not raw_ref:
        return ""
    
    clean = str(raw_ref).strip().upper()
    if not clean:
        return ""
    
    if clean.startswith("REC-"):
        return clean
    elif clean.startswith("REC_"):
        return "REC-" + clean[4:]
    elif clean.startswith("REC") and clean[3:].isdigit():
        return "REC-" + clean[3:]
    elif clean.isdigit():
        return f"REC-{clean.zfill(3)}"
    
    return clean


def normalize_decimal(raw_val: Optional[str]) -> Tuple[Optional[Decimal], Optional[str]]:
    """
    Parses currency and numeric string representations into a Decimal.
    
    Handles:
    "$120.50" -> Decimal('120.50')
    "1,200.00" -> Decimal('1200.00')
    " N/A ", "NULL", "", "-" -> (None, error_reason)
    """
    if raw_val is None:
        return None, "Null value"
    
    s = str(raw_val).strip()
    if not s or s.upper() in ["N/A", "NULL", "NONE", "-"]:
        return None, f"Non-numeric value: '{raw_val}'"
    
    # Strip currency symbol ($) and thousands separator (,)
    cleaned = s.replace("$", "").replace(",", "").strip()
    
    try:
        dec = Decimal(cleaned)
        # Quantize to 2 decimal places if needed or keep exact
        return dec.quantize(Decimal("0.01")), None
    except (InvalidOperation, ValueError):
        return None, f"Invalid numeric format: '{raw_val}'"
