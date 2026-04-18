"""V6/E4 (stage 1.4) — live dsi-demo overlay smoke.

Exercises the real committed overlay file at
``coverages/cyber/overlays/dsi-demo.yaml`` through the full
`get_config(..., tenant_id="dsi-demo")` pipeline. Protects against
silent regressions where the overlay file drifts out of the allow-list.
"""
from __future__ import annotations


def test_dsi_demo_overlay_applies_cleanly():
    from infrastructure.models.compiler import get_config

    base = get_config("cyber", "cyber_general")
    overlay = get_config("cyber", "cyber_general", tenant_id="dsi-demo")

    # Guardrail overrides take effect
    assert overlay.guardrails.modifier_cap == 2.0
    assert overlay.guardrails.max_premium_to_limit_ratio == 0.25
    assert overlay.guardrails.max_premium_to_revenue_ratio == 0.0015

    # Base untouched (not mutated in place)
    assert base.guardrails.modifier_cap == 2.5
    assert base.guardrails.max_premium_to_limit_ratio == 0.35

    # Audit trail stamped
    assert getattr(overlay, "_overlay_version", None) == "dsi-demo-2026Q2-v1"
    assert getattr(overlay, "_overlay_tenant_id", None) == "dsi-demo"


def test_dsi_demo_overlay_weight_shift_visible_in_three_layer_groups():
    from infrastructure.models.compiler import get_config

    overlay = get_config("cyber", "cyber_general", tenant_id="dsi-demo")
    tla = overlay.groups.three_layer_assessment
    tech = next((g for g in tla if g.id == "technical_infrastructure"), None)
    assert tech is not None
    # Overlay over-weighted technical-infrastructure risk dimension.
    assert tech.risk.weight == 0.45


def test_unknown_tenant_is_noop_even_for_cyber():
    from infrastructure.models.compiler import get_config

    # dsi-demo exists, but an arbitrary unknown tenant should silently
    # fall back to the base config (no file = no overlay applied).
    out = get_config("cyber", "cyber_general", tenant_id="nonexistent-tenant")
    assert out.guardrails.modifier_cap == 2.5  # base value
