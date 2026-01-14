"""
DSI Traditional Pricing Modifiers - External Rating Modifier

Integrates external rating sources into pricing:
- Credit ratings (D&B, Experian, Equifax)
- Financial strength ratings (AM Best, S&P, Moody's, Fitch)
- ESG scores (optional)

When no external rating data is available, returns factor=1.0 (no impact).

This modifier is typically disabled by default and enabled when
integration with external rating providers is configured.
"""

import logging
from typing import Any, Dict, List, Optional

from .base import (
    TraditionalModifier,
    TraditionalModifierResult,
)
from ..types import CoverageConfig
from signal_architecture.signals.types import InferenceContext


logger = logging.getLogger("dsi.modifiers.external_rating")


# =============================================================================
# RATING MAPPINGS
# =============================================================================

# Credit score to factor mapping (simplified)
# Higher credit score = lower risk = credit
CREDIT_SCORE_FACTORS: Dict[str, float] = {
    "excellent": 0.90,    # 750+
    "good": 0.95,         # 700-749
    "fair": 1.00,         # 650-699 (base)
    "poor": 1.10,         # 600-649
    "very_poor": 1.25,    # <600
}

# D&B PAYDEX score mapping
# PAYDEX ranges 1-100, 80+ is good
PAYDEX_FACTORS: List[tuple] = [
    (90, 0.92),   # 90-100: Excellent
    (80, 0.96),   # 80-89: Good
    (70, 1.00),   # 70-79: Average (base)
    (50, 1.08),   # 50-69: Below average
    (0, 1.20),    # <50: Poor
]

# Financial strength rating mapping (AM Best style)
FSR_FACTORS: Dict[str, float] = {
    # Superior
    "A++": 0.85,
    "A+": 0.88,
    # Excellent
    "A": 0.92,
    "A-": 0.95,
    # Good
    "B++": 0.98,
    "B+": 1.00,  # Base
    # Fair
    "B": 1.05,
    "B-": 1.10,
    # Marginal
    "C++": 1.15,
    "C+": 1.20,
    # Weak
    "C": 1.30,
    "C-": 1.40,
    # Poor
    "D": 1.50,
    # Not rated / Unable to rate
    "NR": 1.00,
    "U": 1.05,
}

# S&P/Moody's style ratings
CREDIT_RATING_FACTORS: Dict[str, float] = {
    # Investment grade
    "AAA": 0.85,
    "AA+": 0.88,
    "AA": 0.90,
    "AA-": 0.92,
    "A+": 0.94,
    "A": 0.96,
    "A-": 0.98,
    "BBB+": 1.00,  # Base
    "BBB": 1.02,
    "BBB-": 1.05,
    # Speculative grade
    "BB+": 1.10,
    "BB": 1.15,
    "BB-": 1.20,
    "B+": 1.25,
    "B": 1.30,
    "B-": 1.35,
    "CCC+": 1.45,
    "CCC": 1.55,
    "CCC-": 1.65,
    "CC": 1.75,
    "C": 1.85,
    "D": 2.00,  # Default
    # Not rated
    "NR": 1.00,
}


class ExternalRatingModifier(TraditionalModifier):
    """
    External rating integration modifier.

    Incorporates ratings from external providers into pricing.
    Typically disabled by default until integrations are configured.

    Supported rating types:
    - credit_score: Numeric credit score (300-850)
    - paydex: D&B PAYDEX score (1-100)
    - fsr: Financial strength rating (A++, A+, A, etc.)
    - credit_rating: S&P/Moody's style (AAA, AA, BBB, etc.)

    Configuration:
        enabled: Whether this modifier is active (default: False)
        weight_credit: Weight for credit-based ratings (default: 0.5)
        weight_financial: Weight for financial strength (default: 0.5)
        cap_factor: Maximum loading (default: 1.50)
        floor_factor: Maximum credit (default: 0.80)
    """

    def __init__(
        self,
        enabled: bool = False,  # Disabled by default
        weight_credit: float = 0.50,
        weight_financial: float = 0.50,
        cap_factor: float = 1.50,
        floor_factor: float = 0.80,
    ):
        """
        Initialize ExternalRatingModifier.

        Args:
            enabled: Whether this modifier is active
            weight_credit: Weight for credit-based ratings
            weight_financial: Weight for financial strength ratings
            cap_factor: Maximum loading factor
            floor_factor: Maximum credit factor
        """
        self._enabled = enabled
        self.weight_credit = weight_credit
        self.weight_financial = weight_financial
        self.cap_factor = cap_factor
        self.floor_factor = floor_factor

    @property
    def modifier_type(self) -> str:
        return "external_rating"

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def calculate(
        self,
        entity_id: str,
        coverage: str,
        submission_data: Dict[str, Any],
        context: InferenceContext,
        config: Optional[CoverageConfig] = None,
    ) -> TraditionalModifierResult:
        """
        Calculate external rating modifier.

        Returns neutral result (factor=1.0) if:
        - Modifier is disabled
        - No rating data available
        """
        if not self._enabled:
            return TraditionalModifierResult.neutral(
                self.modifier_type,
                "External rating modifier disabled"
            )

        # Extract rating data from submission
        rating_data = self._extract_rating_data(submission_data)

        if not rating_data:
            logger.debug(f"No external rating data for {entity_id} - returning neutral")
            return TraditionalModifierResult.neutral(
                self.modifier_type,
                "No external rating data"
            )

        # Calculate component factors
        components: Dict[str, float] = {}
        notes: List[str] = []
        factors: List[tuple] = []  # (factor, weight)

        # Credit-based ratings
        if "credit_score" in rating_data:
            factor = self._credit_score_factor(rating_data["credit_score"])
            components["credit_score"] = rating_data["credit_score"]
            components["credit_score_factor"] = factor
            factors.append((factor, self.weight_credit))
            notes.append(f"Credit score: {rating_data['credit_score']}")

        if "paydex" in rating_data:
            factor = self._paydex_factor(rating_data["paydex"])
            components["paydex"] = rating_data["paydex"]
            components["paydex_factor"] = factor
            factors.append((factor, self.weight_credit))
            notes.append(f"PAYDEX: {rating_data['paydex']}")

        # Financial strength ratings
        if "fsr" in rating_data:
            factor = FSR_FACTORS.get(rating_data["fsr"].upper(), 1.00)
            components["fsr"] = 0.0  # Can't store string
            components["fsr_factor"] = factor
            factors.append((factor, self.weight_financial))
            notes.append(f"FSR: {rating_data['fsr']}")

        if "credit_rating" in rating_data:
            factor = CREDIT_RATING_FACTORS.get(rating_data["credit_rating"].upper(), 1.00)
            components["credit_rating_factor"] = factor
            factors.append((factor, self.weight_financial))
            notes.append(f"Credit rating: {rating_data['credit_rating']}")

        if not factors:
            return TraditionalModifierResult.neutral(
                self.modifier_type,
                "No recognized rating types"
            )

        # Weighted average of factors
        total_weight = sum(w for _, w in factors)
        if total_weight <= 0:
            combined = 1.0
        else:
            combined = sum(f * w for f, w in factors) / total_weight

        # Apply cap and floor
        final = max(self.floor_factor, min(self.cap_factor, combined))

        if final != combined:
            notes.append(f"Factor capped from {combined:.3f} to {final:.3f}")

        # Confidence based on number of rating sources
        confidence = min(0.90, 0.60 + (len(factors) * 0.15))

        components["combined_factor"] = combined
        components["rating_count"] = float(len(factors))

        logger.info(
            f"External rating for {entity_id}: factor={final:.3f}, "
            f"sources={len(factors)}"
        )

        return TraditionalModifierResult(
            modifier_type=self.modifier_type,
            factor=final,
            confidence=confidence,
            components=components,
            notes=notes,
            data_sources=["external_rating"] + list(rating_data.keys()),
        )

    def _extract_rating_data(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract rating data from submission."""
        if not submission_data:
            return {}

        # Check for nested rating object
        ratings = submission_data.get("external_ratings", submission_data.get("ratings", {}))

        result = {}

        # Credit score (numeric, 300-850)
        credit_score = ratings.get("credit_score", submission_data.get("credit_score"))
        if credit_score is not None and isinstance(credit_score, (int, float)):
            if 300 <= credit_score <= 850:
                result["credit_score"] = float(credit_score)

        # PAYDEX (numeric, 1-100)
        paydex = ratings.get("paydex", submission_data.get("paydex"))
        if paydex is not None and isinstance(paydex, (int, float)):
            if 1 <= paydex <= 100:
                result["paydex"] = float(paydex)

        # Financial strength rating (string)
        fsr = ratings.get("fsr", ratings.get("financial_strength", submission_data.get("fsr")))
        if fsr and isinstance(fsr, str):
            result["fsr"] = fsr.strip()

        # Credit rating (string)
        credit_rating = ratings.get(
            "credit_rating",
            ratings.get("sp_rating", ratings.get("moodys_rating", submission_data.get("credit_rating")))
        )
        if credit_rating and isinstance(credit_rating, str):
            result["credit_rating"] = credit_rating.strip()

        return result

    def _credit_score_factor(self, score: float) -> float:
        """Map credit score to factor."""
        if score >= 750:
            return CREDIT_SCORE_FACTORS["excellent"]
        elif score >= 700:
            return CREDIT_SCORE_FACTORS["good"]
        elif score >= 650:
            return CREDIT_SCORE_FACTORS["fair"]
        elif score >= 600:
            return CREDIT_SCORE_FACTORS["poor"]
        else:
            return CREDIT_SCORE_FACTORS["very_poor"]

    def _paydex_factor(self, paydex: float) -> float:
        """Map PAYDEX score to factor."""
        for threshold, factor in PAYDEX_FACTORS:
            if paydex >= threshold:
                return factor
        return 1.20  # Default for very poor

    def validate_input(self, submission_data: Dict[str, Any]) -> bool:
        """Check if any rating data is available."""
        return bool(self._extract_rating_data(submission_data))
