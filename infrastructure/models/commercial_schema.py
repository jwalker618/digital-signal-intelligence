"""
Commercial Terms Schema — Distribution Economics & Gross Premium Assembly

Commercial terms sit between technical pricing and what the market sees.
They capture entity-specific economics: brokerage, commission, taxes,
distribution structure, and reporting treatment.

Architecture:
    config.yaml (technical)  →  pricer  →  technical_premium (USD)
                                               ↓
    commercial_terms.yaml    →  assembly →  gross_premium (local CCY)

Key principles:
    - Technical pricing is country-agnostic and always in USD
    - Commercial terms are entity-specific (syndicate, MGA, branch, etc.)
    - One entity can write multiple coverages
    - Distribution type (tower/subscription/bundled/decoupled) is a
      commercial concern, not a technical pricing concern
    - The same technical premium can be distributed through different
      market structures by different entities
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("dsi.commercial")

COMMERCIAL_DIR = Path(__file__).parent.parent.parent / "commercial" / "entities"


# =============================================================================
# ENUMS
# =============================================================================

class DistributionType(str, Enum):
    """How the entity distributes risk to market."""
    SUBSCRIPTION = "SUBSCRIPTION"  # Lloyd's / syndicate participation
    TOWER = "TOWER"                # Layered excess-of-loss
    BUNDLED = "BUNDLED"            # SME menu packages
    DECOUPLED = "DECOUPLED"       # Independent limit/deductible selection
    DIRECT = "DIRECT"             # Direct writer / binding authority


class EntityRole(str, Enum):
    """Role in subscription/tower markets."""
    LEAD = "LEAD"
    FOLLOW = "FOLLOW"


# =============================================================================
# DISTRIBUTION STRUCTURES
# =============================================================================

class SubscriptionTerms(BaseModel):
    """Terms for subscription (Lloyd's) market distribution."""
    minimum_line: float = Field(default=0.05, ge=0.0, le=1.0,
                                description="Minimum participation percentage")
    maximum_line: float = Field(default=0.25, ge=0.0, le=1.0,
                                description="Maximum participation percentage")
    default_signed_line: float = Field(default=0.10, ge=0.0, le=1.0,
                                       description="Default signed line if not specified")
    role: EntityRole = EntityRole.FOLLOW
    lead_loading_factor: float = Field(default=1.0, ge=1.0, le=2.0,
                                        description="Premium loading for lead role")


class TowerLayerTemplate(BaseModel):
    """Template for a single tower layer."""
    id: int
    label: str
    attachment_pct: float = Field(ge=0.0, description="Attachment as % of total limit")
    limit_pct: float = Field(gt=0.0, description="Layer limit as % of total limit")


class TowerTerms(BaseModel):
    """Terms for tower (layered excess) distribution."""
    layer_templates: List[TowerLayerTemplate] = Field(
        default_factory=list,
        description="Default layer structure. If empty, layers are bespoke per submission.",
    )
    subscription: Optional[SubscriptionTerms] = Field(
        default=None,
        description="If this tower also uses subscription (common in London market)",
    )


class BundledPackage(BaseModel):
    """A fixed limit/deductible package for SME distribution."""
    id: Union[int, str]
    label: str
    limit: int
    deductible: int
    target_segment: Optional[str] = None


class BundledTerms(BaseModel):
    """Terms for bundled (menu) distribution."""
    packages: List[BundledPackage] = Field(default_factory=list)


class DecoupledTerms(BaseModel):
    """Terms for decoupled (independent selection) distribution."""
    min_limit: int = 1_000_000
    max_limit: int = 100_000_000
    min_deductible: int = 10_000
    max_deductible: int = 1_000_000


class DistributionConfig(BaseModel):
    """Distribution configuration for the entity."""
    type: DistributionType = DistributionType.DECOUPLED
    subscription: Optional[SubscriptionTerms] = None
    tower: Optional[TowerTerms] = None
    bundled: Optional[BundledTerms] = None
    decoupled: Optional[DecoupledTerms] = None


# =============================================================================
# COMMISSION & FEE STRUCTURE
# =============================================================================

class CommissionStructure(BaseModel):
    """Brokerage and commission economics."""
    brokerage_rate: float = Field(default=0.0, ge=0.0, le=0.50,
                                   description="Brokerage commission as fraction of gross")
    overrider_rate: float = Field(default=0.0, ge=0.0, le=0.10,
                                   description="Overrider commission rate")
    profit_commission_rate: float = Field(default=0.0, ge=0.0, le=0.30,
                                           description="Profit commission rate")
    profit_commission_threshold: float = Field(
        default=0.70, ge=0.0, le=1.0,
        description="Loss ratio threshold below which profit commission triggers",
    )


class TaxesAndLevies(BaseModel):
    """Jurisdiction-specific taxes and levies.

    These are applied to the gross premium. Different jurisdictions have
    very different tax regimes (UK IPT 12%, US varies by state, Bermuda 0%).
    """
    insurance_premium_tax_rate: float = Field(default=0.0, ge=0.0, le=0.25,
                                               description="Insurance premium tax (IPT)")
    stamp_duty_rate: float = Field(default=0.0, ge=0.0, le=0.05)
    regulatory_levy_rate: float = Field(default=0.0, ge=0.0, le=0.05,
                                         description="FCA levy, Lloyd's central fund, etc.")
    fire_service_levy_rate: float = Field(default=0.0, ge=0.0, le=0.05)

    @property
    def total_rate(self) -> float:
        return (self.insurance_premium_tax_rate
                + self.stamp_duty_rate
                + self.regulatory_levy_rate
                + self.fire_service_levy_rate)


class FrontingTerms(BaseModel):
    """Terms for fronted arrangements."""
    enabled: bool = False
    fronting_fee_rate: float = Field(default=0.05, ge=0.0, le=0.15)
    fronting_carrier: str = ""


# =============================================================================
# PRICING ADJUSTMENTS
# =============================================================================

class PricingAdjustments(BaseModel):
    """Entity-level adjustments to technical premium."""
    offered_premium_discretion: float = Field(
        default=0.0, ge=0.0, le=0.25,
        description="Maximum deviation from technical premium (±%). "
        "Allows underwriter discretion in final offered price.",
    )
    minimum_gross_premium: float = Field(
        default=0, ge=0,
        description="Minimum gross premium in entity's base currency",
    )


# =============================================================================
# APPETITE (entity-scoped, replaces per-coverage appetite.yaml)
# =============================================================================

class AppetiteConstraint(BaseModel):
    """Single appetite constraint evaluated against submission data."""
    field: str = Field(description="Submission field to evaluate (e.g., 'revenue', 'tiv')")
    operator: str = Field(description="Comparison operator: <=, >=, <, >, ==, !=, in, not_in")
    value: Any = Field(description="Threshold value")
    reason: str = Field(default="", description="Human-readable decline reason")


# =============================================================================
# COVERAGE BINDING
# =============================================================================

class CoverageBinding(BaseModel):
    """Declares which coverages/configs this entity writes, with appetite."""
    coverage: str = Field(description="Coverage line (e.g., 'energy', 'cyber')")
    configs: List[str] = Field(
        default_factory=list,
        description="Specific configs within coverage (empty = all configs in coverage)",
    )
    max_single_limit: Optional[int] = Field(
        default=None,
        description="Entity-specific max limit for this coverage",
    )
    max_aggregate_limit: Optional[int] = Field(
        default=None,
        description="Maximum aggregate across all limits. None = no cap.",
    )
    constraints: List[AppetiteConstraint] = Field(
        default_factory=list,
        description="Entity-specific appetite constraints for this coverage",
    )


def _evaluate_constraint(operator: str, value: Any, threshold: Any) -> bool:
    """Evaluate a single constraint. Returns True if violated."""
    op = operator
    if op in ("<=", "le"):
        return not (value <= threshold)
    elif op in (">=", "ge"):
        return not (value >= threshold)
    elif op in ("<", "lt"):
        return not (value < threshold)
    elif op in (">", "gt"):
        return not (value > threshold)
    elif op in ("==", "=", "eq"):
        return not (value == threshold)
    elif op in ("!=", "ne"):
        return not (value != threshold)
    elif op in ("in", "IN"):
        return value not in threshold
    elif op in ("not_in", "NOT_IN"):
        return value in threshold
    return False


# =============================================================================
# ENTITY — top-level commercial terms
# =============================================================================

class CommercialEntity(BaseModel):
    """Commercial terms for a single internal entity.

    An entity represents a distribution platform, syndicate, branch,
    or MGA that writes business using DSI's technical pricing. Each
    entity has its own economics (commission, taxes, distribution type)
    and writes a specific set of coverages.
    """
    id: str = Field(description="Unique entity identifier")
    name: str = Field(description="Display name")
    market: str = Field(default="", description="Market identifier (lloyds, us, eu, apac)")
    base_currency: str = Field(default="USD", description="Entity's operating currency")

    coverages: List[CoverageBinding] = Field(
        default_factory=list,
        description="Which coverages this entity writes",
    )

    distribution: DistributionConfig = Field(default_factory=DistributionConfig)
    commission: CommissionStructure = Field(default_factory=CommissionStructure)
    taxes_and_levies: TaxesAndLevies = Field(default_factory=TaxesAndLevies)
    fronting: FrontingTerms = Field(default_factory=FrontingTerms)
    pricing_adjustments: PricingAdjustments = Field(default_factory=PricingAdjustments)

    def writes_coverage(self, coverage: str) -> bool:
        """Check if this entity writes a given coverage."""
        return any(c.coverage == coverage for c in self.coverages)

    def get_coverage_binding(self, coverage: str) -> Optional[CoverageBinding]:
        """Get coverage binding for a specific coverage."""
        for c in self.coverages:
            if c.coverage == coverage:
                return c
        return None

    def evaluate_appetite(self, coverage: str, submission_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Evaluate whether a submission falls within this entity's appetite.

        Returns:
            Tuple of (fit, reasons). fit=True if within appetite.
        """
        binding = self.get_coverage_binding(coverage)
        if binding is None:
            return False, [f"Entity {self.id} does not write {coverage}"]

        reasons: List[str] = []

        # Check max single limit
        requested_limit = submission_data.get("limit")
        if binding.max_single_limit is not None and requested_limit is not None:
            if requested_limit > binding.max_single_limit:
                reasons.append(
                    f"Requested limit ${requested_limit:,.0f} exceeds maximum single "
                    f"limit of ${binding.max_single_limit:,.0f}"
                )

        # Check max aggregate limit
        if binding.max_aggregate_limit is not None:
            aggregate = submission_data.get("aggregate_limit", requested_limit or 0)
            if aggregate and aggregate > binding.max_aggregate_limit:
                reasons.append(
                    f"Aggregate limit ${aggregate:,.0f} exceeds maximum aggregate "
                    f"of ${binding.max_aggregate_limit:,.0f}"
                )

        # Evaluate field-level constraints
        for constraint in binding.constraints:
            value = submission_data.get(constraint.field)
            if value is None:
                continue
            violated = _evaluate_constraint(constraint.operator, value, constraint.value)
            if violated:
                reason = constraint.reason or (
                    f"{constraint.field} value {value} violates appetite constraint "
                    f"({constraint.field} {constraint.operator} {constraint.value})"
                )
                reasons.append(reason)

        return len(reasons) == 0, reasons


# =============================================================================
# LOADER
# =============================================================================

def load_entity(entity_id: str) -> Optional[CommercialEntity]:
    """Load commercial terms for an entity from YAML.

    Args:
        entity_id: Entity identifier (matches filename without .yaml)

    Returns:
        CommercialEntity or None if not found.
    """
    entity_path = COMMERCIAL_DIR / f"{entity_id}.yaml"
    if not entity_path.exists():
        logger.warning("Commercial terms not found: %s", entity_path)
        return None

    with open(entity_path) as f:
        raw = yaml.safe_load(f)

    if not raw or "entity" not in raw:
        logger.warning("Invalid commercial terms file: %s", entity_path)
        return None

    return CommercialEntity(**raw["entity"])


def load_all_entities() -> Dict[str, CommercialEntity]:
    """Load all commercial entity definitions."""
    entities = {}
    if not COMMERCIAL_DIR.exists():
        return entities

    for path in sorted(COMMERCIAL_DIR.glob("*.yaml")):
        try:
            with open(path) as f:
                raw = yaml.safe_load(f)
            if raw and "entity" in raw:
                entity = CommercialEntity(**raw["entity"])
                entities[entity.id] = entity
        except Exception as e:
            logger.error("Failed to load commercial terms %s: %s", path, e)

    return entities
