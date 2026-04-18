"""V6/B7 — pvt coverage unit tests.

Verifies the coverage compiles, exposes the expected sub-configs,
inference functions register, and routes a minimum-viable submission
end-to-end.
"""
from __future__ import annotations

import pytest


EXPECTED_SUBCONFIGS = {'pvt_country_risk', 'pvt_sector_exposed', 'pvt_high_value_asset', 'pvt_sme'}


def test_pvt_compiles_with_all_sub_configs():
    from infrastructure.models.compiler import get_compiled_configs
    configs = get_compiled_configs()
    cov = configs.get('pvt')
    assert cov is not None, "pvt not compiled"
    assert set(cov.configurations.keys()) == EXPECTED_SUBCONFIGS


def test_each_sub_config_has_at_least_22_signals():
    from infrastructure.models.compiler import get_compiled_configs
    cov = get_compiled_configs()['pvt']
    for sub_id, cfg in cov.configurations.items():
        assert len(cfg.signal_registry) >= 22, f"{sub_id}: {len(cfg.signal_registry)} signals"


def test_each_sub_config_has_guardrails():
    from infrastructure.models.compiler import get_compiled_configs
    cov = get_compiled_configs()['pvt']
    for sub_id, cfg in cov.configurations.items():
        g = cfg.guardrails
        assert g is not None, f"{sub_id}: missing guardrails"
        assert g.modifier_cap is not None
        assert g.max_premium_to_limit_ratio is not None


def test_inference_functions_registered_for_every_signal():
    """Every signal_registry[*].inference_utility_function must resolve."""
    from infrastructure.models.compiler import get_config
    from signal_architecture.signals.inference.registry import list_inference_functions
    import signal_architecture.signals.inference.functions.pvt  # noqa: F401

    registered = set(list_inference_functions())
    cfg = get_config('pvt', 'pvt_sector_exposed')
    needed = {s.inference_utility_function for s in cfg.signal_registry}
    missing = needed - registered
    assert not missing, f"pvt inference fns missing: {missing}"


def test_primary_sub_config_has_routing_constraint():
    from infrastructure.models.compiler import get_config
    cfg = get_config("pvt", "pvt_sector_exposed")
    constraints = cfg.metadata.routing_constraints
    assert any(
        getattr(rc, "field", None) == 'sector'
        for rc in constraints
    ), f"routing on {'sector'} missing from pvt_sector_exposed"

@pytest.mark.integration
def test_end_to_end_assessment_produces_valid_result():
    from infrastructure.models.compiler import get_config
    from layers.risk.workflow import get_workflow_engine

    config = get_config('pvt', 'pvt_sector_exposed')
    engine = get_workflow_engine()
    r = engine.run_workflow(
        entity_id="test-pvt",
        coverage='pvt',
        entity_name="PVT Test Entity",
        submission_data={
            'asset_tiv': 100000000,
            'limit': 50000000,
            'deductible': 1000000,
            'product_type': 'pvt_terrorism',
            'primary_country': 'US',
            'sector': 'energy',
        },
        config=config,
        skip_discovery=True,
        skip_input_validation=True,
    )
    assert r.is_valid
    assert 0 <= r.composite_score <= 1000
    assert isinstance(r.tier, int)
    assert r.recommended_premium > 0
