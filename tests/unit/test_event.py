"""V6/B6 — event coverage unit tests.

Verifies the coverage compiles, exposes the expected sub-configs,
inference functions register, and routes a minimum-viable submission
end-to-end.
"""
from __future__ import annotations

import pytest


EXPECTED_SUBCONFIGS = {'event_sports', 'event_concert', 'event_conference', 'event_broadcast', 'event_sme'}


def test_event_compiles_with_all_sub_configs():
    from infrastructure.models.compiler import get_compiled_configs
    configs = get_compiled_configs()
    cov = configs.get('event')
    assert cov is not None, "event not compiled"
    assert set(cov.configurations.keys()) == EXPECTED_SUBCONFIGS


def test_each_sub_config_has_at_least_22_signals():
    from infrastructure.models.compiler import get_compiled_configs
    cov = get_compiled_configs()['event']
    for sub_id, cfg in cov.configurations.items():
        assert len(cfg.signal_registry) >= 22, f"{sub_id}: {len(cfg.signal_registry)} signals"


def test_each_sub_config_has_guardrails():
    from infrastructure.models.compiler import get_compiled_configs
    cov = get_compiled_configs()['event']
    for sub_id, cfg in cov.configurations.items():
        g = cfg.guardrails
        assert g is not None, f"{sub_id}: missing guardrails"
        assert g.modifier_cap is not None
        assert g.max_premium_to_limit_ratio is not None


def test_inference_functions_registered_for_every_signal():
    """Every signal_registry[*].inference_utility_function must resolve."""
    from infrastructure.models.compiler import get_config
    from signal_architecture.signals.inference.registry import list_inference_functions
    import signal_architecture.signals.inference.functions.event  # noqa: F401

    registered = set(list_inference_functions())
    cfg = get_config('event', 'event_concert')
    needed = {s.inference_utility_function for s in cfg.signal_registry}
    missing = needed - registered
    assert not missing, f"event inference fns missing: {missing}"


def test_primary_sub_config_has_routing_constraint():
    from infrastructure.models.compiler import get_config
    cfg = get_config("event", "event_concert")
    constraints = cfg.metadata.routing_constraints
    assert any(
        getattr(rc, "field", None) == 'event_type'
        for rc in constraints
    ), f"routing on {'event_type'} missing from event_concert"

@pytest.mark.integration
def test_end_to_end_assessment_produces_valid_result():
    from infrastructure.models.compiler import get_config
    from layers.risk.workflow import get_workflow_engine

    config = get_config('event', 'event_concert')
    engine = get_workflow_engine()
    r = engine.run_workflow(
        entity_id="test-event",
        coverage='event',
        entity_name="EVENT Test Entity",
        submission_data={
            'gross_ticket_revenue': 5000000,
            'limit': 10000000,
            'deductible': 250000,
            'product_type': 'event_cancellation',
            'event_type': 'concert',
            'venue_country': 'US',
            'event_name': 'Test Tour 2026',
        },
        config=config,
        skip_discovery=True,
        skip_input_validation=True,
    )
    assert r.is_valid
    assert 0 <= r.composite_score <= 1000
    assert isinstance(r.tier, int)
    assert r.recommended_premium > 0
