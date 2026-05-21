"""v8 Phase 2: revenue band + NAICS section helpers.

Pure functions -- no DB, no imports outside stdlib.
"""
from __future__ import annotations

import math
from typing import Optional


# Lower-inclusive, upper-exclusive bands. The label is the canonical
# string stored in cohort_membership.revenue_band.
REVENUE_BANDS: list[tuple[str, float, float]] = [
    ("<10M",     0.0,            10_000_000.0),
    ("10-50M",   10_000_000.0,   50_000_000.0),
    ("50-250M",  50_000_000.0,   250_000_000.0),
    ("250M-1B",  250_000_000.0,  1_000_000_000.0),
    (">1B",      1_000_000_000.0, math.inf),
]


def band_for_revenue(revenue: Optional[float]) -> Optional[str]:
    """Return the canonical revenue-band label, or None if revenue is missing/invalid.

    Boundary rule: lower-inclusive, upper-exclusive. Negative values
    and non-finite values return None.
    """
    if revenue is None:
        return None
    try:
        r = float(revenue)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(r) or r < 0:
        return None
    for label, lo, hi in REVENUE_BANDS:
        if lo <= r < hi:
            return label
    return None


def naics_section_for(naics_code: Optional[str | int]) -> Optional[str]:
    """Return the 2-digit NAICS section for any NAICS code length.

    Accepts string or int. Strips whitespace, validates that the first
    two characters are digits, and returns them. Returns None on any
    invalid input.

    Examples:
      "5112"   -> "51"
      511210   -> "51"
      "31-33"  -> "31"   (manufacturing range -- normalised to lower bound)
      "abc"    -> None
      ""       -> None
    """
    if naics_code is None:
        return None
    s = str(naics_code).strip()
    if len(s) < 2:
        return None
    head = s[:2]
    if not head.isdigit():
        return None
    return head
