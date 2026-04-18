"""
Appetite Evaluation Tests — Entity-Scoped

Validates that the entity-based pre-qualification gate correctly accepts
submissions within appetite and rejects those outside it — before the model runs.

Appetite is defined per-entity in commercial/entities/{entity}.yaml, within
each CoverageBinding's max_single_limit and constraints fields.

Run: pytest tests/unit/test_appetite.py -v
"""

import pytest

from layers.risk.appetite import evaluate_appetite, AppetiteResult
from infrastructure.models.commercial_schema import (
    CommercialEntity,
    CoverageBinding,
    AppetiteConstraint,
    DistributionConfig,
    DistributionType,
    CommissionStructure,
    TaxesAndLevies,
    load_entity,
    load_all_entities,
)


# =============================================================================
# FIXTURES — reusable entity configurations
# =============================================================================

@pytest.fixture
def cyber_entity():
    """US MGA writing cyber with $100M max limit and revenue constraint."""
    return CommercialEntity(
        id="test_cyber_mga",
        name="Test Cyber MGA",
        market="us",
        base_currency="USD",
        coverages=[
            CoverageBinding(
                coverage="cyber",
                max_single_limit=100_000_000,
                constraints=[
                    AppetiteConstraint(
                        field="revenue",
                        operator="<=",
                        value=500_000_000_000,
                        reason="Revenue exceeds cyber underwriting authority",
                    ),
                ],
            ),
        ],
        commission=CommissionStructure(brokerage_rate=0.15),
        taxes_and_levies=TaxesAndLevies(insurance_premium_tax_rate=0.03),
    )


@pytest.fixture
def fi_entity():
    """Entity writing financial institutions with total_assets constraint."""
    return CommercialEntity(
        id="test_fi_entity",
        name="Test FI Entity",
        market="us",
        base_currency="USD",
        coverages=[
            CoverageBinding(
                coverage="financial_institutions",
                max_single_limit=500_000_000,
                constraints=[
                    AppetiteConstraint(
                        field="total_assets",
                        operator="<=",
                        value=2_000_000_000_000,
                        reason="Total assets exceed FI underwriting authority",
                    ),
                ],
            ),
        ],
        commission=CommissionStructure(brokerage_rate=0.15),
        taxes_and_levies=TaxesAndLevies(insurance_premium_tax_rate=0.03),
    )


# =============================================================================
# LIMIT ENFORCEMENT
# =============================================================================

class TestLimitEnforcement:
    """Verify max_single_limit catches excessive limit requests."""

    def test_limit_within_appetite(self, cyber_entity):
        """$50M cyber limit is within $100M appetite."""
        result = evaluate_appetite(
            "cyber",
            {"limit": 50_000_000, "revenue": 1_000_000_000},
            entity=cyber_entity,
        )
        assert result.fit is True
        assert result.reasons == []

    def test_limit_at_boundary(self, cyber_entity):
        """Limit exactly at max_single_limit should pass."""
        result = evaluate_appetite("cyber", {
            "limit": 100_000_000,
            "revenue": 1_000_000_000,
        }, entity=cyber_entity)
        assert result.fit is True

    def test_limit_exceeds_appetite(self, cyber_entity):
        """$2B cyber limit should be rejected."""
        result = evaluate_appetite("cyber", {
            "limit": 2_000_000_000,
            "revenue": 1_000_000_000,
        }, entity=cyber_entity)
        assert result.fit is False
        assert len(result.reasons) >= 1
        assert "exceeds maximum" in result.reasons[0].lower() or "limit" in result.reasons[0].lower()

    def test_no_limit_in_submission(self, cyber_entity):
        """Missing limit field should not trigger rejection."""
        result = evaluate_appetite("cyber", {
            "revenue": 1_000_000_000,
        }, entity=cyber_entity)
        assert result.fit is True


# =============================================================================
# CONSTRAINT ENFORCEMENT
# =============================================================================

class TestConstraintEnforcement:
    """Verify field-level constraints work correctly."""

    def test_revenue_within_constraint(self, cyber_entity):
        """$10B revenue is within cyber's $500B constraint."""
        result = evaluate_appetite("cyber", {
            "limit": 25_000_000,
            "revenue": 10_000_000_000,
        }, entity=cyber_entity)
        assert result.fit is True

    def test_revenue_exceeds_constraint(self, cyber_entity):
        """$1T revenue should be rejected by cyber appetite."""
        result = evaluate_appetite("cyber", {
            "limit": 25_000_000,
            "revenue": 1_000_000_000_000,
        }, entity=cyber_entity)
        assert result.fit is False
        assert any("revenue" in r.lower() or "Revenue" in r for r in result.reasons)

    def test_fi_total_assets_constraint(self, fi_entity):
        """$5T total assets should be rejected by FI appetite."""
        result = evaluate_appetite("financial_institutions", {
            "limit": 100_000_000,
            "total_assets": 5_000_000_000_000,
        }, entity=fi_entity)
        assert result.fit is False
        assert any("assets" in r.lower() for r in result.reasons)

    def test_multiple_violations(self, cyber_entity):
        """Both limit and constraint violations should be reported."""
        result = evaluate_appetite("cyber", {
            "limit": 5_000_000_000,             # Way over $100M max
            "revenue": 1_000_000_000_000,       # Way over $500B constraint
        }, entity=cyber_entity)
        assert result.fit is False
        assert len(result.reasons) == 2

    def test_missing_constraint_field_passes(self, fi_entity):
        """If the constrained field isn't in submission, don't reject."""
        result = evaluate_appetite("financial_institutions", {
            "limit": 10_000_000,
            # total_assets not provided
        }, entity=fi_entity)
        assert result.fit is True


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge cases and integration behaviour."""

    def test_no_entity_means_no_constraints(self):
        """No entity provided should accept anything (with warning)."""
        result = evaluate_appetite("nonexistent_xyz", {
            "limit": 999_999_999_999,
        })
        assert result.fit is True

    def test_unknown_coverage_rejected(self, cyber_entity):
        """Entity that doesn't write the coverage should reject."""
        result = evaluate_appetite("marine", {
            "limit": 1_000_000,
        }, entity=cyber_entity)
        assert result.fit is False
        assert any("does not write" in r for r in result.reasons)

    def test_result_includes_coverage(self, cyber_entity):
        """AppetiteResult should include the coverage for audit trail."""
        result = evaluate_appetite("cyber", {"limit": 25_000_000}, entity=cyber_entity)
        assert result.coverage == "cyber"

    def test_result_dataclass_fields(self):
        """AppetiteResult should have expected fields."""
        result = AppetiteResult(fit=True, reasons=[], coverage="test")
        assert result.fit is True
        assert result.reasons == []
        assert result.coverage == "test"


# =============================================================================
# ENTITY YAML LOADING INTEGRATION
# =============================================================================

class TestEntityYAMLAppetite:
    """Verify appetite works with real entity YAML files."""

    def test_mga_appetite_within(self):
        """MGA entity should accept submissions within its appetite."""
        entity = load_entity("mga_us_cyber")
        if entity is None:
            pytest.skip("mga_us_cyber.yaml not found")
        result = evaluate_appetite("cyber", {
            "limit": 10_000_000,
            "revenue": 1_000_000_000,
        }, entity=entity)
        assert result.fit is True

    def test_mga_appetite_exceeded(self):
        """MGA entity should reject limits exceeding its max_single_limit."""
        entity = load_entity("mga_us_cyber")
        if entity is None:
            pytest.skip("mga_us_cyber.yaml not found")
        result = evaluate_appetite("cyber", {
            "limit": 500_000_000,  # Well above MGA's 25M max
        }, entity=entity)
        assert result.fit is False

    def test_syndicate_appetite_within(self):
        """Syndicate should accept submissions within its appetite."""
        entity = load_entity("syndicate_example")
        if entity is None:
            pytest.skip("syndicate_example.yaml not found")
        result = evaluate_appetite("energy", {
            "limit": 100_000_000,
            "tiv": 10_000_000_000,
        }, entity=entity)
        assert result.fit is True

    def test_syndicate_appetite_exceeded(self):
        """Syndicate should reject excessive TIV."""
        entity = load_entity("syndicate_example")
        if entity is None:
            pytest.skip("syndicate_example.yaml not found")
        result = evaluate_appetite("energy", {
            "limit": 100_000_000,
            "tiv": 500_000_000_000,  # Way above 100B constraint
        }, entity=entity)
        assert result.fit is False

    def test_all_loaded_entities_have_coverages(self):
        """All entities should have at least one coverage binding."""
        entities = load_all_entities()
        for entity_id, entity in entities.items():
            assert len(entity.coverages) > 0, f"{entity_id} has no coverages"


# =============================================================================
# SEED COMPANY VALIDATION
# =============================================================================

class TestSeedCompanyAppetite:
    """Verify seed companies pass appetite check (entity-based or no-entity fallback)."""

    def test_all_seed_companies_within_appetite(self):
        """All companies in the seed dataset should be within appetite.

        With entity-based appetite, no-entity submissions pass by default.
        This test verifies the seed script's evaluate_appetite calls succeed.
        """
        from seed.bench import COMPANIES, build_submission_data
        failures = []
        for co in COMPANIES:
            submission_data = build_submission_data(co)
            # No entity provided — matches seed script behaviour (legacy compat)
            result = evaluate_appetite(co["coverage"], submission_data)
            if not result.fit:
                failures.append(
                    f"{co['entity_name']} ({co['coverage']}): {result.reasons}"
                )
        assert not failures, (
            f"{len(failures)} seed companies outside appetite:\n"
            + "\n".join(failures)
        )
