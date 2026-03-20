"""
Appetite Evaluation Tests

Validates that the pre-qualification gate correctly accepts submissions
within appetite and rejects those outside it — before the model runs.

Run: pytest tests/unit/test_appetite.py -v
"""

import pytest
from pathlib import Path

from layers.risk.appetite import (
    evaluate_appetite,
    load_appetite,
    CoverageAppetite,
)


COVERAGES_DIR = Path(__file__).parent.parent.parent / "coverages"


# =============================================================================
# APPETITE FILE LOADING
# =============================================================================

class TestAppetiteLoading:
    """Verify appetite files load correctly for all coverages."""

    @pytest.mark.parametrize("coverage,directory", [
        ("cyber", "cyber"),
        ("directors_officers", "do"),
        ("financial_institutions", "fi"),
        ("professional_indemnity", "pi"),
        ("energy", "energy"),
        ("marine", "marine"),
        ("aerospace", "aerospace"),
    ])
    def test_appetite_file_exists_and_loads(self, coverage, directory):
        """Each coverage must have a valid appetite.yaml."""
        appetite_path = COVERAGES_DIR / directory / "appetite.yaml"
        assert appetite_path.exists(), f"Missing appetite.yaml for {coverage}"

        appetite = load_appetite(coverage)
        assert appetite is not None
        assert isinstance(appetite, CoverageAppetite)

    @pytest.mark.parametrize("coverage", [
        "cyber", "directors_officers", "financial_institutions",
        "professional_indemnity", "energy", "marine", "aerospace",
    ])
    def test_max_single_limit_is_set(self, coverage):
        """Every coverage must define a max_single_limit."""
        appetite = load_appetite(coverage)
        assert appetite is not None
        assert appetite.max_single_limit is not None
        assert appetite.max_single_limit > 0

    def test_nonexistent_coverage_returns_none(self):
        """Unknown coverage with no appetite file returns None (no constraints)."""
        appetite = load_appetite("nonexistent_coverage_xyz")
        assert appetite is None


# =============================================================================
# LIMIT ENFORCEMENT
# =============================================================================

class TestLimitEnforcement:
    """Verify max_single_limit catches excessive limit requests."""

    def test_limit_within_appetite(self):
        """$50M cyber limit is within $100M appetite."""
        result = evaluate_appetite("cyber", {"limit": 50_000_000, "revenue": 1_000_000_000})
        assert result.fit is True
        assert result.reasons == []

    def test_limit_at_boundary(self):
        """Limit exactly at max_single_limit should pass."""
        appetite = load_appetite("cyber")
        result = evaluate_appetite("cyber", {
            "limit": appetite.max_single_limit,
            "revenue": 1_000_000_000,
        })
        assert result.fit is True

    def test_limit_exceeds_appetite(self):
        """$2B cyber limit should be rejected."""
        result = evaluate_appetite("cyber", {"limit": 2_000_000_000, "revenue": 1_000_000_000})
        assert result.fit is False
        assert len(result.reasons) == 1
        assert "limit" in result.reasons[0].lower()

    def test_no_limit_in_submission(self):
        """Missing limit field should not trigger rejection."""
        result = evaluate_appetite("cyber", {"revenue": 1_000_000_000})
        assert result.fit is True

    @pytest.mark.parametrize("coverage,bad_limit", [
        ("cyber", 500_000_000),          # $500M > $100M cyber max
        ("marine", 5_000_000_000),       # $5B > $1B marine max
        ("aerospace", 10_000_000_000),   # $10B > $2.5B aerospace max
    ])
    def test_excessive_limits_rejected_across_coverages(self, coverage, bad_limit):
        """Clearly excessive limits are caught for each coverage."""
        result = evaluate_appetite(coverage, {"limit": bad_limit})
        assert result.fit is False


# =============================================================================
# CONSTRAINT ENFORCEMENT
# =============================================================================

class TestConstraintEnforcement:
    """Verify field-level constraints work correctly."""

    def test_revenue_within_constraint(self):
        """$10B revenue is within cyber's $500B constraint."""
        result = evaluate_appetite("cyber", {
            "limit": 25_000_000,
            "revenue": 10_000_000_000,
        })
        assert result.fit is True

    def test_revenue_exceeds_constraint(self):
        """$1T revenue should be rejected by cyber appetite."""
        result = evaluate_appetite("cyber", {
            "limit": 25_000_000,
            "revenue": 1_000_000_000_000,
        })
        assert result.fit is False
        assert any("revenue" in r.lower() for r in result.reasons)

    def test_fi_total_assets_constraint(self):
        """$5T total assets should be rejected by FI appetite."""
        result = evaluate_appetite("financial_institutions", {
            "limit": 100_000_000,
            "total_assets": 5_000_000_000_000,
        })
        assert result.fit is False
        assert any("assets" in r.lower() for r in result.reasons)

    def test_multiple_violations(self):
        """Both limit and constraint violations should be reported."""
        result = evaluate_appetite("cyber", {
            "limit": 5_000_000_000,             # Way over $100M max
            "revenue": 1_000_000_000_000,       # Way over $500B constraint
        })
        assert result.fit is False
        assert len(result.reasons) == 2

    def test_missing_constraint_field_passes(self):
        """If the constrained field isn't in submission, don't reject."""
        result = evaluate_appetite("financial_institutions", {
            "limit": 10_000_000,
            # total_assets not provided
        })
        assert result.fit is True


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge cases and integration behaviour."""

    def test_no_appetite_file_means_no_constraints(self):
        """Coverage without appetite.yaml should accept anything."""
        result = evaluate_appetite("nonexistent_xyz", {
            "limit": 999_999_999_999,
        })
        assert result.fit is True

    def test_result_includes_coverage(self):
        """AppetiteResult should include the coverage for audit trail."""
        result = evaluate_appetite("cyber", {"limit": 25_000_000})
        assert result.coverage == "cyber"

    def test_all_seed_companies_within_appetite(self):
        """All companies in the seed dataset should be within appetite.

        If a seed company is outside appetite, either the appetite is too
        restrictive or the seed data needs updating.
        """
        from seed_dsi_bench import COMPANIES, build_submission_data
        failures = []
        for co in COMPANIES:
            submission_data = build_submission_data(co)
            result = evaluate_appetite(co["coverage"], submission_data)
            if not result.fit:
                failures.append(
                    f"{co['entity_name']} ({co['coverage']}): {result.reasons}"
                )
        assert not failures, (
            f"{len(failures)} seed companies outside appetite:\n"
            + "\n".join(failures)
        )
