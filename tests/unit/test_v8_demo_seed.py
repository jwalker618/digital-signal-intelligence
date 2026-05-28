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
    COHORT_DISTRIBUTIONS,
    COHORT_DISTRIBUTION_DEFAULT,
    COHORT_POOL_PER_BAND,
    DEMO_CLIENT_TENANTS,
    DEMO_PASSWORD_DEFAULT,
    DEMO_RNG_SEED_DEFAULT,
    MARSH_BROKER_SLUG,
    MARSH_TENANT_SLUG,
    _build_drag_modifiers,
    _enumerate_demo_cohorts,
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
        cyber = next(c for c in acme["coverages"] if c["coverage"] == "cyber")
        # Acme cyber is below cohort mean (~720), at REFER tier with MFA drag
        assert cyber["composite_score"] < 720.0
        assert cyber["tier"] == 4
        assert cyber["open_query"]["signal"] == "mfa_enabled"
        assert "mfa_enabled" in cyber["drag_modifier_signal_ids"]

    def test_each_client_has_multiple_coverages(self):
        for t in DEMO_CLIENT_TENANTS:
            assert len(t["coverages"]) >= 3, (
                f"{t['entity_name']} should have >=3 coverages for the "
                f"aggregation/drilldown narrative; has {len(t['coverages'])}"
            )

    def test_open_queries_scattered_across_book(self):
        # The Communications page needs multiple open queries across
        # clients to feel populated. Confirm at least 3 open queries
        # exist across the demo book.
        open_queries = [
            (t["entity_name"], cov["coverage"])
            for t in DEMO_CLIENT_TENANTS
            for cov in t["coverages"]
            if cov.get("open_query") is not None
        ]
        assert len(open_queries) >= 3

    def test_open_queries_have_required_fields(self):
        for t in DEMO_CLIENT_TENANTS:
            for cov in t["coverages"]:
                q = cov.get("open_query")
                if q is None:
                    continue
                assert "body" in q and q["body"].strip()
                assert "signal" in q

    def test_northwind_cyber_clean_state(self):
        nw = next(t for t in DEMO_CLIENT_TENANTS if "Northwind" in t["entity_name"])
        cyber = next(c for c in nw["coverages"] if c["coverage"] == "cyber")
        # Cyber is the clean / preferred coverage for Northwind
        assert cyber["composite_score"] > 720.0
        assert cyber["tier"] <= 2

    def test_entity_keys_unique(self):
        keys = {t["entity_name"].strip().lower() for t in DEMO_CLIENT_TENANTS}
        assert len(keys) == len(DEMO_CLIENT_TENANTS)

    def test_pioneer_has_cat_property(self):
        # Pioneer has the CAT-exposed property policy that exercises
        # the property_cat_exposed configuration -- demo richness.
        p = next(t for t in DEMO_CLIENT_TENANTS if "Pioneer" in t["entity_name"])
        cat = next(
            (c for c in p["coverages"] if c["configuration"] == "property_cat_exposed"),
            None,
        )
        assert cat is not None, "Pioneer should have a CAT property policy"


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


class TestCohortFodderCoverage:
    """v8.2-cohort: the demo seeds peer fodder for every (coverage,
    naics, band) the book touches -- not just cyber. Otherwise the
    portal's peer percentile / cohort mean / 'how you compare to top
    peers' analytics show 'Insufficient peers' on every non-cyber
    coverage."""

    def test_enumeration_includes_every_demo_coverage_pair(self):
        cohorts = _enumerate_demo_cohorts()
        # Every (coverage, naics, band) the demo book hits should be
        # there. Build the expected set from DEMO_CLIENT_TENANTS so the
        # test stays in sync if anyone adds a new demo policy.
        expected: set[tuple[str, str, str]] = set()
        for t in DEMO_CLIENT_TENANTS:
            for cov in t["coverages"]:
                expected.add(
                    (cov["coverage"], t["naics_section"], t["revenue_band"]),
                )
        assert set(cohorts) == expected
        # Sanity: with 3 demo clients and 4 coverages each, we should
        # be touching at least 8 distinct cohorts. (Some coverages
        # collide across clients -- e.g. cyber x 50-250M x section 51
        # is just one cohort even if multiple clients fall in it.)
        assert len(cohorts) >= 8

    def test_distribution_covers_every_demo_coverage(self):
        # Every coverage that appears in the demo book must have an
        # explicit distribution entry. Falling back to the default mean
        # for a demo coverage would break the narrative percentile
        # bands.
        demo_coverages = {
            cov["coverage"]
            for t in DEMO_CLIENT_TENANTS
            for cov in t["coverages"]
        }
        for cov in demo_coverages:
            assert cov in COHORT_DISTRIBUTIONS, (
                f"Coverage {cov!r} appears in the demo but has no entry "
                f"in COHORT_DISTRIBUTIONS; falling back to the default "
                f"would compress narrative percentile bands."
            )

    def test_distributions_match_market_cycle_narrative(self):
        # Market Pulse narrative: D&O + cyber softening (mean >720),
        # property + medprof hardening (mean <700), pi/casualty/prodlib
        # flat (mean ~700). Cohort distributions should mirror this so
        # the demo reads internally consistent.
        softening_mean_floor = 720.0
        hardening_mean_ceiling = 700.0
        # D&O is the most decisive softening line, cyber close behind
        assert COHORT_DISTRIBUTIONS["do"][0] >= softening_mean_floor
        assert COHORT_DISTRIBUTIONS["cyber"][0] >= softening_mean_floor
        # Property + medprof hardening
        assert COHORT_DISTRIBUTIONS["property"][0] <= hardening_mean_ceiling
        assert COHORT_DISTRIBUTIONS["medprof"][0] <= hardening_mean_ceiling

    def test_default_distribution_shape(self):
        mean, stddev = COHORT_DISTRIBUTION_DEFAULT
        # Default is a sensible flat-market neutral.
        assert 680 <= mean <= 720
        assert 30 <= stddev <= 80

    def test_pool_size_provides_meaningful_analytics(self):
        from layers.cohort.service import MIN_COHORT_SIZE
        # Must comfortably exceed MIN_COHORT_SIZE so percentiles are
        # stable and analytics like "cohort mean" don't snap around
        # between seeds.
        assert COHORT_POOL_PER_BAND >= MIN_COHORT_SIZE * 3


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
