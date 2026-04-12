"""
WE-5d: Portfolio-Aware CAF Enrichment

Adjusts an entity's CAF upward when the entity contributes to portfolio
concentration. Activates ONLY at SIMULATE maturity -- the portfolio view
is authoritative enough to feed pricing at that stage, not before.

Maximum enrichment is capped at CONCENTRATION_LOADING_CAP (1.15 = +15%).
The overall CAF remains bounded by the active ConstraintRegime (usually
[0.80, 1.50] initially, widening over time but never beyond [0.60, 2.00]).

Operation:
1. If maturity < SIMULATE, return base CAF unchanged.
2. Query registry for portfolio concentrations this entity participates in.
3. For each concentration the entity is in, add a severity-weighted loading.
4. Sum the loadings (capped). Multiply into base CAF.
5. Re-clamp against the active ConstraintRegime.
6. Return the enriched CAF with provenance.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from world_engine.causal_pricing.constraints import ConstraintCalibrator
from world_engine.maturity import MaturityEvaluator
from world_engine.registry import IntelligenceRegistry
from world_engine.types import CausalAdjustmentFactor

logger = logging.getLogger("dsi.world_engine.portfolio.caf_enrichment")


CONCENTRATION_LOADING_CAP: float = 1.15


class PortfolioCafEnricher:
    """Enriches a base CAF with a portfolio-aware concentration loading."""

    def __init__(
        self,
        registry: IntelligenceRegistry,
        maturity_evaluator: Optional[MaturityEvaluator] = None,
    ):
        self.registry = registry
        self.db: Session = registry.db
        self.maturity_evaluator = maturity_evaluator or MaturityEvaluator()

    def enrich(
        self,
        base_caf: CausalAdjustmentFactor,
        entity_name: str,
        commercial_entity_id: str,
    ) -> CausalAdjustmentFactor:
        """Return a potentially-enriched copy of the base CAF.

        If the maturity stage does not unlock concentration-aware CAF,
        return the base CAF unchanged.
        """
        # Gate: only activate at SIMULATE maturity
        maturity = self.maturity_evaluator.evaluate(self.db)
        if not maturity.capabilities.get("concentration_aware_caf", False):
            return base_caf

        # Only enrich a CAF that actually used relationships -- a neutral
        # CAF (CAF=1.0 due to no matches) should not be pushed away from
        # neutral purely by concentration.
        if base_caf.caf_value == 1.0 and base_caf.relationships_evaluated == 0:
            return base_caf

        concentrations = self.registry.get_portfolio_concentrations(commercial_entity_id)
        # Only count concentrations that include this entity
        affecting = [c for c in concentrations if entity_name in (c.affected_entities or [])]
        if not affecting:
            return base_caf

        # Concentration loading: severity-weighted sum across dimensions,
        # capped at CONCENTRATION_LOADING_CAP. Each dimension contributes
        # independently (so 3 high-severity dimensions compound, but not
        # without bound).
        loading = 1.0
        reasons: list[str] = []
        for conc in affecting:
            # Each concentration contributes at most (CAP - 1.0) / 4
            # (so even four max-severity concentrations stop at the cap).
            max_per_dimension = (CONCENTRATION_LOADING_CAP - 1.0) / 4.0
            dimension_loading = 1.0 + (conc.severity * max_per_dimension)
            loading *= dimension_loading
            reasons.append(f"{conc.dimension}:{conc.severity:.2f}")

        loading = min(loading, CONCENTRATION_LOADING_CAP)

        enriched_raw = base_caf.raw_caf * loading

        # Re-clamp against the active constraint regime
        regime = ConstraintCalibrator(self.db).get_active_regime()
        final_caf, constrained = regime.clamp(enriched_raw)

        logger.info(
            "Portfolio CAF enrichment: base=%.3f loading=%.3f raw=%.3f final=%.3f (%s)",
            base_caf.caf_value, loading, enriched_raw, final_caf,
            ", ".join(reasons),
        )

        # Append concentration details to the existing CAF's precursors
        # metadata via a new CAF object. The active_precursors list is kept
        # as-is; concentration info rides in constraint_regime as a tag.
        new_regime_name = f"{regime.regime_name}+portfolio[{len(affecting)}]"

        return CausalAdjustmentFactor(
            entity_id=base_caf.entity_id,
            assessment_id=base_caf.assessment_id,
            caf_value=float(final_caf),
            confidence=base_caf.confidence,
            active_precursors=base_caf.active_precursors,
            trajectory=base_caf.trajectory,
            relationships_evaluated=base_caf.relationships_evaluated,
            constrained=bool(constrained or base_caf.constrained),
            raw_caf=float(enriched_raw),
            constraint_regime=new_regime_name,
            computed_at=datetime.now(timezone.utc),
        )
