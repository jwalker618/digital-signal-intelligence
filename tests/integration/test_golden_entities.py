"""V6/E5 — Golden-Entity Regression Suite.

Runs every fixture under ``tests/fixtures/golden_entities/`` through the
full assessment pipeline and asserts the output matches the snapshot
within the fixture's declared tolerance.

Regenerate or refresh a fixture with::

    python tests/fixtures/golden_entities/_generator.py --all --refresh

Per the V6 plan, tightening a tolerance or refreshing a fixture requires a
signed-off PR (tracked in code review, not enforced programmatically).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.fixtures.golden_entities._schema import GoldenEntity, discover  # noqa: E402


GOLDEN_ENTITIES = discover()


def _ids(entities):
    return [f"{e.coverage}/{e.entity_id}" for e in entities]


def _run_pipeline(entity: GoldenEntity):
    from infrastructure.models.compiler import get_config
    from layers.risk.workflow import get_workflow_engine

    config = None
    if entity.config_id:
        config = get_config(entity.coverage, entity.config_id)

    engine = get_workflow_engine()
    return engine.run_workflow(
        entity_id=entity.entity_id,
        coverage=entity.coverage,
        entity_name=entity.name,
        submission_data=dict(entity.minimum_viable_input),
        config=config,
        skip_discovery=True,
        skip_input_validation=True,
    )


@pytest.mark.integration
@pytest.mark.parametrize("entity", GOLDEN_ENTITIES, ids=_ids(GOLDEN_ENTITIES))
def test_golden_entity_assessment(entity: GoldenEntity):
    result = _run_pipeline(entity)

    exp = entity.expected
    tol = entity.tolerance

    # Composite score
    assert abs(result.composite_score - exp.composite_score) <= tol.score_points, (
        f"{entity.coverage}/{entity.entity_id}: composite score "
        f"{result.composite_score} vs expected {exp.composite_score} "
        f"(tolerance ±{tol.score_points})"
    )

    # Tier
    actual_tier = int(result.tier)
    assert abs(actual_tier - exp.tier) <= tol.tier_spread, (
        f"{entity.coverage}/{entity.entity_id}: tier {actual_tier} "
        f"vs expected {exp.tier} (tolerance ±{tol.tier_spread})"
    )

    # Decision
    decision_actual = (
        result.decision.value if hasattr(result.decision, "value") else str(result.decision)
    )
    assert decision_actual.lower() == exp.decision.lower(), (
        f"{entity.coverage}/{entity.entity_id}: decision {decision_actual} "
        f"vs expected {exp.decision}"
    )

    # Premium within basis-point tolerance
    exp_premium = exp.recommended_premium
    actual_premium = float(result.recommended_premium)
    if exp_premium > 0:
        delta_bps = abs(actual_premium - exp_premium) / exp_premium * 10_000
    else:
        delta_bps = 10_000 if actual_premium != 0 else 0
    assert delta_bps <= tol.premium_bps, (
        f"{entity.coverage}/{entity.entity_id}: premium "
        f"${actual_premium:,.2f} vs expected ${exp_premium:,.2f} "
        f"(Δ={delta_bps:.1f} bps > tolerance {tol.premium_bps:.0f} bps)"
    )


def test_every_coverage_has_at_least_one_golden():
    coverages_with_configs = {
        p.parent.name
        for p in (REPO_ROOT / "coverages").glob("*/config.yaml")
    }
    golden_coverages = {e.coverage for e in GOLDEN_ENTITIES}
    missing = coverages_with_configs - golden_coverages
    assert not missing, (
        f"Coverages with no golden entity: {sorted(missing)}. "
        f"Add manifest entries in tests/fixtures/golden_entities/_manifest.yaml "
        f"and regenerate fixtures."
    )
