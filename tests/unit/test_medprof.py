"""V6/B1 — Medprof coverage unit tests.

Verifies the coverage compiles, exposes the expected five sub-configs,
and routes a minimum-viable submission end-to-end.
"""
from __future__ import annotations

import pytest


EXPECTED_SUBCONFIGS = {
    "medprof_hospital",
    "medprof_physician_group",
    "medprof_nursing_home",
    "medprof_telehealth",
    "medprof_sme",
}


def test_medprof_compiles_with_all_sub_configs():
    from infrastructure.models.compiler import get_compiled_configs
    configs = get_compiled_configs()
    mp = configs.get("medprof")
    assert mp is not None, "medprof not compiled"
    assert set(mp.configurations.keys()) == EXPECTED_SUBCONFIGS


def test_each_sub_config_has_at_least_22_signals():
    from infrastructure.models.compiler import get_compiled_configs
    mp = get_compiled_configs()["medprof"]
    for sub_id, cfg in mp.configurations.items():
        assert len(cfg.signal_registry) >= 22, f"{sub_id}: {len(cfg.signal_registry)} signals"


def test_each_sub_config_has_guardrails():
    from infrastructure.models.compiler import get_compiled_configs
    mp = get_compiled_configs()["medprof"]
    for sub_id, cfg in mp.configurations.items():
        g = cfg.guardrails
        assert g is not None, f"{sub_id}: missing guardrails"
        assert g.modifier_cap is not None
        assert g.max_premium_to_limit_ratio is not None


def test_hospital_sub_config_routes_on_employee_count():
    from infrastructure.models.compiler import get_config
    cfg = get_config("medprof", "medprof_hospital")
    constraints = cfg.metadata.routing_constraints
    assert any(
        getattr(rc, "field", None) == "employee_count"
        for rc in constraints
    )


def test_inference_functions_registered_for_every_signal():
    """Every signal_registry[*].inference_utility_function must resolve."""
    from infrastructure.models.compiler import get_config
    from signal_architecture.signals.inference.registry import list_inference_functions
    # Trigger import-time registration
    import signal_architecture.signals.inference.functions.medprof  # noqa: F401

    registered = set(list_inference_functions())
    cfg = get_config("medprof", "medprof_hospital")
    needed = {s.inference_utility_function for s in cfg.signal_registry}
    missing = needed - registered
    assert not missing, f"medprof inference fns missing: {missing}"


@pytest.mark.integration
def test_end_to_end_assessment_produces_valid_result():
    from infrastructure.models.compiler import get_config
    from layers.risk.workflow import get_workflow_engine

    config = get_config("medprof", "medprof_hospital")
    engine = get_workflow_engine()
    r = engine.run_workflow(
        entity_id="test-hosp",
        coverage="medprof",
        entity_name="General Test Hospital",
        submission_data={
            "revenue": 500_000_000,
            "limit": 25_000_000,
            "deductible": 250_000,
            "product_type": "hospital_mpl",
            "employee_count": 5000,
            "facility_type": "hospital",
            "annual_patient_encounters": 2_500_000,
        },
        config=config,
        skip_discovery=True,
        skip_input_validation=True,
    )
    assert r.is_valid
    assert 0 <= r.composite_score <= 1000
    assert isinstance(r.tier, int)
    assert r.recommended_premium > 0
