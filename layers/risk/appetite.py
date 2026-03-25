"""
DSI Appetite Evaluator — Step 0 Pre-qualification Gate

Evaluates whether a submission falls within underwriting appetite BEFORE
the model runs.

Appetite is entity-scoped and lives in commercial entity definitions
(commercial/entities/{entity}.yaml), alongside distribution, commission,
and other commercial terms. Each entity declares per-coverage appetite
constraints within its CoverageBinding.

Usage:
    from infrastructure.models.commercial_schema import load_entity
    entity = load_entity("mga_us_cyber")
    fit, reasons = entity.evaluate_appetite("cyber", submission_data)

    # Or via the evaluate_appetite wrapper:
    from layers.risk.appetite import evaluate_appetite
    result = evaluate_appetite("cyber", submission_data, entity=entity)
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger("dsi.appetite")


# =============================================================================
# RESULT
# =============================================================================

@dataclass
class AppetiteResult:
    """Result of an appetite evaluation."""
    fit: bool = True
    reasons: List[str] = field(default_factory=list)
    coverage: str = ""


# =============================================================================
# EVALUATOR
# =============================================================================

def evaluate_appetite(
    coverage: str,
    submission_data: Dict[str, Any],
    entity=None,
) -> AppetiteResult:
    """Evaluate whether a submission falls within underwriting appetite.

    Appetite is entity-scoped. The entity's CoverageBinding defines
    max_single_limit, max_aggregate_limit, and field-level constraints
    per coverage line.

    Args:
        coverage: Coverage identifier (e.g., "cyber", "marine")
        submission_data: Submission fields including limit, revenue, tiv, etc.
        entity: CommercialEntity defining appetite for this coverage.
                Required — returns fit=True with a warning if not provided.

    Returns:
        AppetiteResult with fit=True if within appetite, fit=False with reasons if not.
    """
    if entity is None:
        logger.warning(
            "No entity provided for appetite evaluation on %s — "
            "skipping appetite check. Provide a CommercialEntity for "
            "proper appetite evaluation.",
            coverage,
        )
        return AppetiteResult(fit=True, coverage=coverage)

    fit, reasons = entity.evaluate_appetite(coverage, submission_data)

    if not fit:
        logger.info(
            "Submission outside appetite for %s (entity=%s): %s",
            coverage, entity.id, "; ".join(reasons),
        )

    return AppetiteResult(fit=fit, reasons=reasons, coverage=coverage)
