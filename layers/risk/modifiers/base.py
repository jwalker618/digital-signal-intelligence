"""
DSI Traditional Pricing Modifiers - Base Classes and Types

This module provides the base infrastructure for traditional pricing
modifiers that can be optionally applied after DSI base premium.

All inputs are OPTIONAL. Modifiers gracefully return factor=1.0
(no impact) when required data is unavailable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional

from ..types import CoverageConfig
from ...signals.types import InferenceContext


# =============================================================================
# INPUT DATA TYPES
# =============================================================================

@dataclass
class PolicyYear:
    """Historical policy year data for experience rating."""
    year: int
    premium: float
    incurred_losses: float
    paid_losses: float
    outstanding_reserves: float = 0.0
    claim_count: int = 0

    @property
    def loss_ratio(self) -> float:
        """Calculate loss ratio for this policy year."""
        if self.premium <= 0:
            return 0.0
        return self.incurred_losses / self.premium


@dataclass
class Claim:
    """Individual claim record."""
    claim_id: str
    occurrence_date: date
    incurred_amount: float
    paid_amount: float = 0.0
    status: str = "open"  # open, closed, reopened
    cause_code: str = ""
    is_large_loss: bool = False


@dataclass
class LossHistoryInput:
    """
    Loss history data for experience rating - ALL OPTIONAL.

    When policy_years is empty, the LossHistoryModifier returns
    factor=1.0 (no impact on premium).
    """
    policy_years: List[PolicyYear] = field(default_factory=list)
    claims: List[Claim] = field(default_factory=list)
    large_loss_threshold: float = 100_000.0
    credibility_factor: Optional[float] = None  # Override auto-calculated

    @property
    def has_data(self) -> bool:
        """Check if any loss history data is available."""
        return len(self.policy_years) > 0

    @property
    def total_premium(self) -> float:
        """Sum of all policy year premiums."""
        return sum(py.premium for py in self.policy_years)

    @property
    def total_incurred_losses(self) -> float:
        """Sum of all incurred losses."""
        return sum(py.incurred_losses for py in self.policy_years)

    @property
    def overall_loss_ratio(self) -> float:
        """Calculate overall loss ratio across all years."""
        if self.total_premium <= 0:
            return 0.0
        return self.total_incurred_losses / self.total_premium

    @classmethod
    def from_submission(cls, submission_data: Dict[str, Any]) -> "LossHistoryInput":
        """
        Extract loss history from submission data if available.

        Looks for keys: 'loss_history', 'policy_years', 'claims'
        """
        if not submission_data:
            return cls()

        # Check for nested loss_history object
        loss_data = submission_data.get("loss_history", {})
        if not loss_data and not submission_data.get("policy_years"):
            return cls()

        # Extract policy years
        policy_years_raw = loss_data.get("policy_years", submission_data.get("policy_years", []))
        policy_years = []
        for py in policy_years_raw:
            if isinstance(py, dict):
                policy_years.append(PolicyYear(
                    year=py.get("year", 0),
                    premium=py.get("premium", 0.0),
                    incurred_losses=py.get("incurred_losses", py.get("losses", 0.0)),
                    paid_losses=py.get("paid_losses", 0.0),
                    outstanding_reserves=py.get("outstanding_reserves", 0.0),
                    claim_count=py.get("claim_count", 0),
                ))

        # Extract claims
        claims_raw = loss_data.get("claims", submission_data.get("claims", []))
        large_loss_threshold = loss_data.get("large_loss_threshold", 100_000.0)
        claims = []
        for c in claims_raw:
            if isinstance(c, dict):
                incurred = c.get("incurred_amount", c.get("amount", 0.0))
                claims.append(Claim(
                    claim_id=c.get("claim_id", ""),
                    occurrence_date=c.get("occurrence_date", date.today()),
                    incurred_amount=incurred,
                    paid_amount=c.get("paid_amount", 0.0),
                    status=c.get("status", "open"),
                    cause_code=c.get("cause_code", ""),
                    is_large_loss=incurred >= large_loss_threshold,
                ))

        return cls(
            policy_years=policy_years,
            claims=claims,
            large_loss_threshold=large_loss_threshold,
            credibility_factor=loss_data.get("credibility_factor"),
        )


@dataclass
class ExposureInput:
    """
    Exposure metrics for rating - ALL FIELDS OPTIONAL.

    Two modes:
    - Streamlined (STP): Only needs revenue OR tiv for quick factor
    - Full: Uses all available data for detailed analysis

    When no exposure data is available, ExposureModifier returns
    factor=1.0 (no impact on premium).
    """
    # Core exposure (any ONE enables streamlined mode)
    tiv: Optional[float] = None
    revenue: Optional[float] = None

    # Additional metrics (for full mode)
    employee_count: Optional[int] = None
    payroll: Optional[float] = None
    fleet_size: Optional[int] = None
    fleet_average_age: Optional[float] = None
    locations_count: Optional[int] = None

    # Coverage-specific (optional)
    cyber_endpoints: Optional[int] = None
    vessels_count: Optional[int] = None
    aircraft_count: Optional[int] = None

    # Growth metrics (optional, for trend analysis)
    prior_year_revenue: Optional[float] = None
    prior_year_tiv: Optional[float] = None

    @property
    def has_minimal_data(self) -> bool:
        """Check if enough data for streamlined exposure factor."""
        return self.tiv is not None or self.revenue is not None

    @property
    def mode(self) -> str:
        """Determine analysis mode based on available data."""
        if not self.has_minimal_data:
            return "none"  # Skip exposure modifier
        # Check for full mode data
        full_fields = [self.employee_count, self.payroll, self.fleet_size, self.locations_count]
        if sum(1 for f in full_fields if f is not None) >= 2:
            return "full"
        return "streamlined"  # STP mode

    @property
    def primary_exposure(self) -> float:
        """Get the primary exposure metric (TIV preferred, then revenue)."""
        return self.tiv if self.tiv is not None else (self.revenue or 0.0)

    @property
    def revenue_growth(self) -> Optional[float]:
        """Calculate revenue growth rate if prior year data available."""
        if self.revenue is None or self.prior_year_revenue is None:
            return None
        if self.prior_year_revenue <= 0:
            return None
        return (self.revenue - self.prior_year_revenue) / self.prior_year_revenue

    @classmethod
    def from_submission(cls, submission_data: Dict[str, Any]) -> "ExposureInput":
        """
        Extract exposure metrics from submission data.

        Looks for common exposure keys in the submission.
        """
        if not submission_data:
            return cls()

        # Try nested exposure object first
        exposure_data = submission_data.get("exposure", submission_data)

        return cls(
            tiv=exposure_data.get("tiv", exposure_data.get("total_insured_value")),
            revenue=exposure_data.get("revenue", exposure_data.get("annual_revenue")),
            employee_count=exposure_data.get("employee_count", exposure_data.get("employees")),
            payroll=exposure_data.get("payroll"),
            fleet_size=exposure_data.get("fleet_size", exposure_data.get("vehicles")),
            fleet_average_age=exposure_data.get("fleet_average_age"),
            locations_count=exposure_data.get("locations_count", exposure_data.get("locations")),
            cyber_endpoints=exposure_data.get("cyber_endpoints", exposure_data.get("endpoints")),
            vessels_count=exposure_data.get("vessels_count", exposure_data.get("vessels")),
            aircraft_count=exposure_data.get("aircraft_count", exposure_data.get("aircraft")),
            prior_year_revenue=exposure_data.get("prior_year_revenue"),
            prior_year_tiv=exposure_data.get("prior_year_tiv"),
        )


# =============================================================================
# RESULT TYPE
# =============================================================================

@dataclass
class TraditionalModifierResult:
    """
    Output from traditional modifier calculation.

    A factor of 1.0 means no impact on premium.
    A factor of 1.25 means +25% loading.
    A factor of 0.85 means -15% credit.
    """
    modifier_type: str  # 'loss_history', 'exposure', 'external_rating'
    factor: float  # Multiplicative factor (1.0 = no change)
    confidence: float  # Data quality/credibility (0-1)
    components: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    skipped: bool = False  # True if modifier was skipped due to missing data

    @property
    def has_impact(self) -> bool:
        """Check if this modifier affects premium."""
        return abs(self.factor - 1.0) > 0.001 and not self.skipped

    @classmethod
    def neutral(cls, modifier_type: str, reason: str = "No data available") -> "TraditionalModifierResult":
        """Create a neutral result (factor=1.0) for when modifier is skipped."""
        return cls(
            modifier_type=modifier_type,
            factor=1.0,
            confidence=0.0,
            components={},
            notes=[f"{reason} - modifier skipped"],
            data_sources=[],
            skipped=True,
        )


# =============================================================================
# BASE MODIFIER CLASS
# =============================================================================

class TraditionalModifier(ABC):
    """
    Base class for traditional pricing modifiers.

    Traditional modifiers integrate actuarial data sources with DSI's
    digital signal-based pricing. They are applied after base premium
    (Step 10) and before DSI modifiers (Step 11).

    All modifiers must handle missing data gracefully by returning
    a neutral result (factor=1.0) when required inputs are unavailable.
    """

    @abstractmethod
    def calculate(
        self,
        entity_id: str,
        coverage: str,
        submission_data: Dict[str, Any],
        context: InferenceContext,
        config: Optional[CoverageConfig] = None,
    ) -> TraditionalModifierResult:
        """
        Calculate the modifier factor.

        Args:
            entity_id: The entity being priced
            coverage: Coverage type (e.g., "aerospace", "cyber")
            submission_data: Submission data from broker
            context: Inference context with discovery data
            config: Optional coverage configuration

        Returns:
            TraditionalModifierResult with factor, confidence, and audit trail
        """
        pass

    @property
    @abstractmethod
    def modifier_type(self) -> str:
        """Type identifier for this modifier (e.g., 'loss_history')."""
        pass

    @property
    def is_enabled(self) -> bool:
        """Check if this modifier is enabled. Override for config-based control."""
        return True

    def validate_input(self, submission_data: Dict[str, Any]) -> bool:
        """
        Validate that required input data is available.

        Override in subclasses for specific validation.
        Returns True if data is sufficient to calculate modifier.
        """
        return True
