"""v8 Phase 7 -- demo-reset module structure + pure helpers.

The full reset path requires a live DB; that's exercised manually
(or in Phase 7's smoke tests). These tests confirm the module is
loadable, the configuration constants line up with the demo storyboard,
and the pure modifier-building helper produces the right shape.
"""
from __future__ import annotations

import pytest

from seed import demo_reset
from seed.demo_reset import (
    COHORT_POOL_PER_BAND,
    DEMO_CLIENT_TENANTS,
    DEMO_PASSWORD_DEFAULT,
    DEMO_RNG_SEED_DEFAULT,
    MARSH_BROKER_SLUG,
    MARSH_TENANT_SLUG,
    _build_drag_modifiers,
)


class TestModuleStructure:
    def test_run_callable(self):
        assert callable(demo_reset.run)

    def test_reset_demo_state_callable(self):
        assert callable(demo_reset.reset_demo_state)

    def test_constants(self):
        assert MARSH_TENANT_SLUG == "marsh-demo"
        assert MARSH_BROKER_SLUG == "marsh"
        assert DEMO_PASSWORD_DEFAULT == "demo-pass-2026"
        assert DEMO_RNG_SEED_DEFAULT == 42

    def test_cohort_per_band_meets_min_threshold(self):
        # Must exceed MIN_COHORT_SIZE in the cohort engine so percentiles
        # compute (10) and feel realistic for a demo (>>10).
        from layers.cohort.service import MIN_COHORT_SIZE
        assert COHORT_POOL_PER_BAND >= MIN_COHORT_SIZE
        assert COHORT_POOL_PER_BAND >= 30  # generous so demo looks substantial

    def test_three_demo_clients(self):
        assert len(DEMO_CLIENT_TENANTS) == 3


class TestDemoStoryboardAlignment:
    """Spec the demo storyboard's narrative bones into tests."""

    def test_clients_have_distinct_naics_sections(self):
        sections = {t["naics_section"] for t in DEMO_CLIENT_TENANTS}
        assert len(sections) == 3  # tech, healthcare, manufacturing

    def test_clients_span_revenue_bands(self):
        bands = {t["revenue_band"] for t in DEMO_CLIENT_TENANTS}
        assert "50-250M" in bands
        assert "250M-1B" in bands

    def test_acme_is_demo_anchor(self):
        acme = next(t for t in DEMO_CLIENT_TENANTS if "Acme" in t["entity_name"])
        # Acme is below cohort mean (~720), at REFER tier with MFA drags
        assert acme["composite_score"] < 720.0
        assert acme["tier"] == 4
        assert acme["open_referral"] is True
        assert "mfa_enabled" in acme["drag_modifier_signal_ids"]

    def test_only_acme_has_open_referral(self):
        open_count = sum(1 for t in DEMO_CLIENT_TENANTS if t["open_referral"])
        assert open_count == 1

    def test_northwind_above_cohort_mean(self):
        nw = next(t for t in DEMO_CLIENT_TENANTS if "Northwind" in t["entity_name"])
        assert nw["composite_score"] > 720.0  # above cohort mean -> looks clean

    def test_entity_keys_unique(self):
        keys = {t["entity_name"].strip().lower() for t in DEMO_CLIENT_TENANTS}
        assert len(keys) == len(DEMO_CLIENT_TENANTS)


class TestBuildDragModifiers:
    """Pure modifier-builder used to hand-tune demo quotes."""

    def test_no_drags_returns_unchanged(self):
        modifiers, final = _build_drag_modifiers([], base_premium=100_000)
        assert modifiers == []
        assert final == 100_000

    def test_single_drag_compounds(self):
        modifiers, final = _build_drag_modifiers(["mfa_enabled"], base_premium=100_000)
        assert len(modifiers) == 1
        # 100k * 1.08 = 108k
        assert final == 108_000.0

    def test_multiple_drags_compound(self):
        modifiers, final = _build_drag_modifiers(
            ["mfa_enabled", "security_training"], base_premium=100_000,
        )
        assert len(modifiers) == 2
        # 100k * 1.08 * 1.08 = 116640
        assert final == pytest.approx(116_640.0, abs=1)

    def test_modifier_shape_matches_phase3_expectations(self):
        # Each modifier must have source / source_id / factor / before / after
        # so compute_impact_breakdown can classify it.
        modifiers, _ = _build_drag_modifiers(["mfa_enabled"], base_premium=100_000)
        m = modifiers[0]
        assert m["source"] == "direct_query"
        assert m["source_id"] == "mfa_enabled"
        assert m["factor"] == 1.08
        assert "premium_before" in m
        assert "premium_after" in m

    def test_drag_modifier_is_above_phase3_deadband(self):
        # Phase 3 classifies modifiers above 1.02 as DRAG. Our 1.08 must
        # land above the threshold.
        from layers.risk.impact_breakdown import DEADBAND_UPPER
        modifiers, _ = _build_drag_modifiers(["mfa_enabled"], base_premium=100_000)
        assert modifiers[0]["factor"] > DEADBAND_UPPER


class TestCliRegistration:
    def test_cli_includes_demo_reset(self):
        from seed.cli import _build_parser
        parser = _build_parser()
        # The subparser should know about demo-reset; argparse stores it
        # under the action's choices
        sub = next(
            a for a in parser._actions if hasattr(a, "choices") and a.choices
        )
        assert "demo-reset" in sub.choices
