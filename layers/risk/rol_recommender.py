"""ROL-Driven Dual Recommendation Engine — Phase C.

Replaces the median-of-menu limit selection with an economically driven
approach that produces two recommendations:

1. **Upper recommendation** — The highest limit where the ROL is still
   within appetite, offering the client best value (most coverage per
   dollar of premium).

2. **Lower recommendation** — The minimum adequate limit based on the
   client's requested limit, at a competitive ROL.

Output includes ``attachment``, ``participation_pct``, and
``structure_type`` fields from day one for future tower/subscription
compatibility (Phase E).

Usage:
    from layers.risk.rol_recommender import ROLRecommender
    from layers.risk.rol_validator import ROLValidator

    recommender = ROLRecommender(validator=ROLValidator())
    result = recommender.recommend(
        limit_premiums={"1000000": 8000, "5000000": 30000, "10000000": 55000},
        requested_limit=5_000_000,
    )
    print(result.upper.limit, result.upper.premium)
    print(result.lower.limit, result.lower.premium)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .rol_validator import ROLValidator, ROLValidationResult
from .types import LimitPremiumDetail

logger = logging.getLogger("dsi.rol_recommender")


# ---------------------------------------------------------------------------
# Recommendation output types
# ---------------------------------------------------------------------------

@dataclass
class LimitRecommendation:
    """A single limit recommendation."""
    limit: int = 0
    premium: float = 0.0
    rol: float = 0.0
    rol_percentile: float = 0.0  # 0-1, where in the appetite band this ROL sits
    band_label: str = ""
    rationale: str = ""

    # Phase E future fields (defaults for ground-up)
    attachment: int = 0
    participation_pct: float = 1.0
    structure_type: str = "ground_up"


@dataclass
class DualRecommendation:
    """Result of dual recommendation engine."""
    upper: LimitRecommendation  # Best value higher limit
    lower: LimitRecommendation  # Minimum adequate at client's request
    all_options: List[LimitRecommendation] = field(default_factory=list)
    requested_limit: int = 0

    # Phase E: multi-layer / subscription extensions
    structure_type: str = "ground_up"  # "ground_up", "tower", "subscription"
    layers: List[Any] = field(default_factory=list)  # List[LayerPremiumDetail]
    signed_line: Optional[float] = None
    role: Optional[str] = None  # "LEAD" or "FOLLOW"

    @property
    def spread(self) -> float:
        """Premium difference between upper and lower recommendations."""
        return self.upper.premium - self.lower.premium

    @property
    def limit_ratio(self) -> float:
        """Ratio of upper to lower limit."""
        if self.lower.limit > 0:
            return self.upper.limit / self.lower.limit
        return 0.0


# ---------------------------------------------------------------------------
# Recommender
# ---------------------------------------------------------------------------

class ROLRecommender:
    """Produces dual limit recommendations using ROL analysis.

    Replaces the median-of-menu approach with economically optimised
    recommendations based on ROL appetite bands.
    """

    def __init__(self, validator: ROLValidator):
        """
        Args:
            validator: ROLValidator instance with configured appetite bands
        """
        self.validator = validator

    def recommend(
        self,
        limit_premiums: Dict[str, float],
        requested_limit: int = 0,
        attachment: int = 0,
        limit_details: Optional[List[LimitPremiumDetail]] = None,
    ) -> DualRecommendation:
        """Produce dual recommendation from limit/premium menu.

        Args:
            limit_premiums: Dict mapping limit (str) to premium (float)
            requested_limit: Client's requested limit (0 if not specified)
            attachment: Attachment point (0 for ground-up)
            limit_details: Optional LimitPremiumDetail list for richer output

        Returns:
            DualRecommendation with upper and lower picks
        """
        if not limit_premiums:
            empty = LimitRecommendation(rationale="No limit options available")
            return DualRecommendation(upper=empty, lower=empty, requested_limit=requested_limit)

        # Build sorted options with ROL validation
        options: List[LimitRecommendation] = []
        for limit_str, premium in sorted(limit_premiums.items(), key=lambda x: int(float(x[0]))):
            limit = int(float(limit_str))
            if limit <= 0:
                continue

            validation = self.validator.validate_rol(premium, limit, attachment)
            rol_percentile = self._compute_rol_percentile(validation)

            options.append(LimitRecommendation(
                limit=limit,
                premium=premium,
                rol=validation.rol,
                rol_percentile=rol_percentile,
                band_label=validation.band_label,
                attachment=attachment,
            ))

        if not options:
            empty = LimitRecommendation(rationale="No valid limit options")
            return DualRecommendation(upper=empty, lower=empty, requested_limit=requested_limit)

        # Find upper recommendation: highest limit within appetite
        upper = self._find_upper(options)

        # Find lower recommendation: at or near requested limit
        lower = self._find_lower(options, requested_limit)

        # Add rationale
        upper.rationale = self._upper_rationale(upper, options)
        lower.rationale = self._lower_rationale(lower, requested_limit)

        return DualRecommendation(
            upper=upper,
            lower=lower,
            all_options=options,
            requested_limit=requested_limit,
        )

    def _find_upper(self, options: List[LimitRecommendation]) -> LimitRecommendation:
        """Find best-value higher limit within ROL appetite.

        Strategy: Walk from highest limit downward. Pick the highest limit
        whose ROL is within appetite (validated by the validator).  If none
        are within appetite, fall back to the option with the lowest ROL
        (best value).
        """
        # Options within appetite (ROL between floor and ceiling)
        within_appetite = []
        for opt in options:
            result = self.validator.validate_rol(opt.premium, opt.limit, opt.attachment)
            if result.within_appetite:
                within_appetite.append(opt)

        if within_appetite:
            # Highest limit within appetite
            return max(within_appetite, key=lambda o: o.limit)

        # Fallback: option with ROL closest to the midpoint of its band
        return min(options, key=lambda o: abs(o.rol_percentile - 0.5))

    def _find_lower(
        self,
        options: List[LimitRecommendation],
        requested_limit: int,
    ) -> LimitRecommendation:
        """Find minimum adequate limit near client's request.

        Strategy:
        - If requested_limit specified: pick exact match or nearest >= requested
        - If not specified: pick the option with the best (lowest) ROL
        """
        if requested_limit > 0:
            # Exact match
            for opt in options:
                if opt.limit == requested_limit:
                    return opt

            # Nearest limit >= requested
            above = [o for o in options if o.limit >= requested_limit]
            if above:
                return min(above, key=lambda o: o.limit)

            # Nothing at or above — take the highest available
            return max(options, key=lambda o: o.limit)

        # No requested limit — pick best value (lowest ROL)
        return min(options, key=lambda o: o.rol)

    def _compute_rol_percentile(self, validation: ROLValidationResult) -> float:
        """Compute where in the appetite band this ROL sits (0=floor, 1=ceiling)."""
        if validation.rol_ceiling <= validation.rol_floor:
            return 0.5
        if validation.rol_floor == 0 and validation.rol_ceiling == 0:
            return 0.5
        percentile = (validation.rol - validation.rol_floor) / (
            validation.rol_ceiling - validation.rol_floor
        )
        return max(0.0, min(1.0, percentile))

    def _upper_rationale(
        self,
        pick: LimitRecommendation,
        options: List[LimitRecommendation],
    ) -> str:
        """Generate rationale for upper recommendation."""
        higher_count = sum(1 for o in options if o.limit > pick.limit)
        if higher_count == 0:
            return (
                f"Highest available limit ({pick.limit:,}) at ROL {pick.rol:.4f} "
                f"within appetite [{pick.band_label}]"
            )
        return (
            f"Limit {pick.limit:,} offers best value at ROL {pick.rol:.4f} "
            f"[{pick.band_label}]. {higher_count} higher limit(s) exceed appetite."
        )

    def _lower_rationale(
        self,
        pick: LimitRecommendation,
        requested_limit: int,
    ) -> str:
        """Generate rationale for lower recommendation."""
        if requested_limit > 0:
            if pick.limit == requested_limit:
                return f"Matches requested limit ({requested_limit:,}) at ROL {pick.rol:.4f}"
            return (
                f"Nearest available limit ({pick.limit:,}) to requested "
                f"({requested_limit:,}) at ROL {pick.rol:.4f}"
            )
        return f"Best value option at limit {pick.limit:,} with ROL {pick.rol:.4f}"
