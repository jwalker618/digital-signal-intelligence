"""
DSI Appetite Evaluator — Step 0 Pre-qualification Gate

Evaluates whether a submission falls within underwriting appetite BEFORE
the model runs. This is distinct from pricing configuration:

  - appetite.yaml  → Underwriting owns. "Do we write this at all?"
  - config.yaml    → Actuarial owns. "How do we price it?"

Appetite is defined per coverage (not per config) because it reflects
the book-level risk appetite, not the model calibration.

Usage:
    from layers.risk.appetite import evaluate_appetite

    result = evaluate_appetite("cyber", submission_data)
    if not result.fit:
        # Outside appetite — do not run the model
        print(result.reasons)
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger("dsi.appetite")

COVERAGES_DIR = Path(__file__).parent.parent.parent / "coverages"

# Maps coverage names used in seed data to directory names
COVERAGE_DIR_ALIASES = {
    "directors_officers": "do",
    "financial_institutions": "fi",
    "professional_indemnity": "pi",
}


# =============================================================================
# SCHEMA
# =============================================================================

class AppetiteConstraint(BaseModel):
    """Single appetite constraint evaluated against submission data."""
    field: str
    operator: str  # <=, >=, <, >, ==, !=, in
    value: Any
    reason: str = ""


class CoverageAppetite(BaseModel):
    """Appetite definition for a single coverage line."""
    max_single_limit: Optional[int] = Field(
        default=None,
        description="Maximum limit for any single policy. None = no cap.",
    )
    max_aggregate_limit: Optional[int] = Field(
        default=None,
        description="Maximum aggregate across all limits. None = no cap.",
    )
    constraints: List[AppetiteConstraint] = Field(
        default_factory=list,
        description="Additional field-level constraints.",
    )


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

def _resolve_coverage_dir(coverage: str) -> str:
    """Resolve coverage name to its directory name."""
    return COVERAGE_DIR_ALIASES.get(coverage, coverage)


def load_appetite(coverage: str) -> Optional[CoverageAppetite]:
    """Load appetite.yaml for a coverage.

    Returns None if no appetite file exists (no constraints enforced).
    """
    coverage_dir = _resolve_coverage_dir(coverage)
    appetite_path = COVERAGES_DIR / coverage_dir / "appetite.yaml"

    if not appetite_path.exists():
        return None

    with open(appetite_path) as f:
        raw = yaml.safe_load(f)

    if not raw or "appetite" not in raw:
        return None

    return CoverageAppetite(**raw["appetite"])


def _evaluate_constraint(
    constraint: AppetiteConstraint,
    submission_data: Dict[str, Any],
) -> Optional[str]:
    """Evaluate a single constraint. Returns reason string if violated, None if OK."""
    value = submission_data.get(constraint.field)
    if value is None:
        return None  # Field not present — can't evaluate, not a violation

    op = constraint.operator
    threshold = constraint.value

    violated = False
    if op in ("<=", "le"):
        violated = not (value <= threshold)
    elif op in (">=", "ge"):
        violated = not (value >= threshold)
    elif op in ("<", "lt"):
        violated = not (value < threshold)
    elif op in (">", "gt"):
        violated = not (value > threshold)
    elif op in ("==", "=", "eq"):
        violated = not (value == threshold)
    elif op in ("!=", "ne"):
        violated = not (value != threshold)
    elif op in ("in", "IN"):
        violated = value not in threshold
    elif op in ("not_in", "NOT_IN"):
        violated = value in threshold
    else:
        logger.warning("Unknown appetite constraint operator: %s", op)
        return None

    if violated:
        reason = constraint.reason or (
            f"{constraint.field} value {value} violates appetite constraint "
            f"({constraint.field} {op} {threshold})"
        )
        return reason

    return None


def evaluate_appetite(
    coverage: str,
    submission_data: Dict[str, Any],
) -> AppetiteResult:
    """Evaluate whether a submission falls within underwriting appetite.

    Args:
        coverage: Coverage identifier (e.g., "cyber", "marine")
        submission_data: Submission fields including limit, revenue, tiv, etc.

    Returns:
        AppetiteResult with fit=True if within appetite, fit=False with reasons if not.
    """
    appetite = load_appetite(coverage)
    if appetite is None:
        return AppetiteResult(fit=True, coverage=coverage)

    reasons: List[str] = []

    # Check max single limit
    requested_limit = submission_data.get("limit")
    if appetite.max_single_limit is not None and requested_limit is not None:
        if requested_limit > appetite.max_single_limit:
            reasons.append(
                f"Requested limit ${requested_limit:,.0f} exceeds maximum single "
                f"limit of ${appetite.max_single_limit:,.0f}"
            )

    # Check max aggregate limit (if multiple limits provided)
    if appetite.max_aggregate_limit is not None:
        aggregate = submission_data.get("aggregate_limit", requested_limit or 0)
        if aggregate > appetite.max_aggregate_limit:
            reasons.append(
                f"Aggregate limit ${aggregate:,.0f} exceeds maximum aggregate "
                f"of ${appetite.max_aggregate_limit:,.0f}"
            )

    # Evaluate field-level constraints
    for constraint in appetite.constraints:
        reason = _evaluate_constraint(constraint, submission_data)
        if reason:
            reasons.append(reason)

    fit = len(reasons) == 0

    if not fit:
        logger.info(
            "Submission outside appetite for %s: %s",
            coverage, "; ".join(reasons),
        )

    return AppetiteResult(fit=fit, reasons=reasons, coverage=coverage)
