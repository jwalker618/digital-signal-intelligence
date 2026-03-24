"""ROL (Rate on Line) Curve Validator — Phase C.

Replaces PremiumValidator with per-coverage ROL appetite bands keyed by
(attachment_range, limit_range).  The core operation is:

    ROL = premium / limit

The validator checks whether the observed ROL falls within the configured
appetite bands.  For ground-up business, attachment is always 0.  The
signature accepts ``attachment`` as a parameter so that Phase E (tower
pricing) can reuse the same validator without redesign.

Usage:
    from layers.risk.rol_validator import ROLValidator

    validator = ROLValidator()
    result = validator.validate_rol(premium=50_000, limit=5_000_000)
    if not result.within_appetite:
        print(result.reason)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("dsi.rol_validator")


# ---------------------------------------------------------------------------
# Default ROL appetite bands
#
# Keyed by (attachment_range, limit_range).  For ground-up business the
# attachment_range is always (0, 0).  The limit_range defines the cohort.
#
# ROL = premium / limit.  Appetite bands express the range of ROL values
# that represent well-calibrated pricing for each cohort.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ROLAppetiteBand:
    """A single ROL appetite band definition."""
    label: str
    attachment_min: int = 0
    attachment_max: int = 0
    limit_min: int = 0
    limit_max: int = 0  # 0 = unbounded
    rol_floor: float = 0.001
    rol_ceiling: float = 0.25
    warning_floor: float = 0.0005  # soft floor (warning, not fail)
    warning_ceiling: float = 0.30   # soft ceiling (warning, not fail)


# Default bands for ground-up business (attachment = 0)
DEFAULT_ROL_APPETITE: List[ROLAppetiteBand] = [
    ROLAppetiteBand(
        label="MICRO",
        limit_min=0, limit_max=2_000_000,
        rol_floor=0.001, rol_ceiling=0.08,
        warning_floor=0.0005, warning_ceiling=0.10,
    ),
    ROLAppetiteBand(
        label="SMALL",
        limit_min=2_000_001, limit_max=10_000_000,
        rol_floor=0.002, rol_ceiling=0.12,
        warning_floor=0.001, warning_ceiling=0.15,
    ),
    ROLAppetiteBand(
        label="MEDIUM",
        limit_min=10_000_001, limit_max=50_000_000,
        rol_floor=0.005, rol_ceiling=0.15,
        warning_floor=0.003, warning_ceiling=0.18,
    ),
    ROLAppetiteBand(
        label="LARGE",
        limit_min=50_000_001, limit_max=250_000_000,
        rol_floor=0.005, rol_ceiling=0.18,
        warning_floor=0.003, warning_ceiling=0.22,
    ),
    ROLAppetiteBand(
        label="JUMBO",
        limit_min=250_000_001, limit_max=1_000_000_000,
        rol_floor=0.005, rol_ceiling=0.20,
        warning_floor=0.003, warning_ceiling=0.25,
    ),
    ROLAppetiteBand(
        label="MEGA",
        limit_min=1_000_000_001, limit_max=0,
        rol_floor=0.005, rol_ceiling=0.25,
        warning_floor=0.003, warning_ceiling=0.30,
    ),
]


# ---------------------------------------------------------------------------
# Validation result types
# ---------------------------------------------------------------------------

@dataclass
class ROLValidationResult:
    """Result of a single ROL validation."""
    premium: float
    limit: int
    attachment: int = 0
    rol: float = 0.0
    band_label: str = ""
    rol_floor: float = 0.0
    rol_ceiling: float = 0.0
    within_appetite: bool = True
    within_warning: bool = True
    severity: str = "OK"  # OK, WARNING, FAIL
    reason: str = ""

    @property
    def summary(self) -> str:
        return (
            f"ROL={self.rol:.4f} [{self.band_label}] "
            f"appetite=[{self.rol_floor:.4f},{self.rol_ceiling:.4f}] "
            f"→ {self.severity}"
        )


@dataclass
class ROLBatchResult:
    """Result of validating multiple ROL checks."""
    results: List[ROLValidationResult] = field(default_factory=list)
    fail_count: int = 0
    warning_count: int = 0
    ok_count: int = 0

    @property
    def all_passed(self) -> bool:
        return self.fail_count == 0

    @property
    def pass_rate(self) -> float:
        total = len(self.results)
        return (total - self.fail_count) / total if total > 0 else 1.0


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class ROLValidator:
    """Validates premium-to-limit ratios (ROL) against appetite bands.

    Replaces PremiumValidator with a cleaner ROL-centric approach that
    supports both ground-up and tower (excess layer) pricing via the
    ``attachment`` parameter.
    """

    def __init__(
        self,
        appetite_bands: Optional[List[ROLAppetiteBand]] = None,
    ):
        """
        Args:
            appetite_bands: Per-cohort ROL appetite definitions.
                Defaults to DEFAULT_ROL_APPETITE for ground-up business.
        """
        self.appetite_bands = appetite_bands or list(DEFAULT_ROL_APPETITE)

    def get_band(self, limit: int, attachment: int = 0) -> Optional[ROLAppetiteBand]:
        """Find the appetite band for a given limit and attachment.

        Matching logic:
        1. Filter bands where attachment falls within [attachment_min, attachment_max]
        2. Among those, find the band where limit falls within [limit_min, limit_max]
           (limit_max=0 means unbounded)
        """
        for band in self.appetite_bands:
            # Check attachment range
            if attachment < band.attachment_min:
                continue
            if band.attachment_max > 0 and attachment > band.attachment_max:
                continue
            # Check limit range
            if limit < band.limit_min:
                continue
            if band.limit_max > 0 and limit > band.limit_max:
                continue
            return band
        return None

    def validate_rol(
        self,
        premium: float,
        limit: int,
        attachment: int = 0,
    ) -> ROLValidationResult:
        """Validate a single premium/limit combination.

        Args:
            premium: The premium amount
            limit: The policy limit
            attachment: The attachment point (0 for ground-up)

        Returns:
            ROLValidationResult with pass/warn/fail status
        """
        if limit <= 0:
            return ROLValidationResult(
                premium=premium,
                limit=limit,
                attachment=attachment,
                severity="FAIL",
                reason="Limit must be positive",
            )

        rol = premium / limit
        band = self.get_band(limit, attachment)

        if band is None:
            return ROLValidationResult(
                premium=premium,
                limit=limit,
                attachment=attachment,
                rol=rol,
                severity="WARNING",
                reason=f"No appetite band found for limit={limit:,} attachment={attachment:,}",
                within_appetite=False,
                within_warning=True,
            )

        within_appetite = band.rol_floor <= rol <= band.rol_ceiling
        within_warning = band.warning_floor <= rol <= band.warning_ceiling

        if within_appetite:
            severity = "OK"
            reason = ""
        elif within_warning:
            severity = "WARNING"
            if rol < band.rol_floor:
                reason = f"ROL {rol:.4f} below floor {band.rol_floor:.4f} (within warning band)"
            else:
                reason = f"ROL {rol:.4f} above ceiling {band.rol_ceiling:.4f} (within warning band)"
        else:
            severity = "FAIL"
            if rol < band.warning_floor:
                reason = f"ROL {rol:.4f} below warning floor {band.warning_floor:.4f}"
            else:
                reason = f"ROL {rol:.4f} above warning ceiling {band.warning_ceiling:.4f}"

        return ROLValidationResult(
            premium=premium,
            limit=limit,
            attachment=attachment,
            rol=rol,
            band_label=band.label,
            rol_floor=band.rol_floor,
            rol_ceiling=band.rol_ceiling,
            within_appetite=within_appetite,
            within_warning=within_warning,
            severity=severity,
            reason=reason,
        )

    def validate_limit_menu(
        self,
        limit_premiums: Dict[str, float],
        attachment: int = 0,
    ) -> ROLBatchResult:
        """Validate all limit/premium pairs from a pricing result.

        Args:
            limit_premiums: Dict mapping limit (str) to premium (float)
            attachment: Attachment point (0 for ground-up)

        Returns:
            ROLBatchResult with per-limit validation and summary counts
        """
        results = []
        fail_count = 0
        warning_count = 0
        ok_count = 0

        for limit_str, premium in sorted(limit_premiums.items(), key=lambda x: float(x[0])):
            limit = int(float(limit_str))
            result = self.validate_rol(premium, limit, attachment)
            results.append(result)

            if result.severity == "FAIL":
                fail_count += 1
            elif result.severity == "WARNING":
                warning_count += 1
            else:
                ok_count += 1

        return ROLBatchResult(
            results=results,
            fail_count=fail_count,
            warning_count=warning_count,
            ok_count=ok_count,
        )
