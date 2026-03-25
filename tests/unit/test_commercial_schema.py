"""Tests for infrastructure.models.commercial_schema — commercial entity definitions."""

import pytest
from pathlib import Path

from infrastructure.models.commercial_schema import (
    CommercialEntity,
    CoverageBinding,
    AppetiteConstraint,
    DistributionConfig,
    DistributionType,
    CommissionStructure,
    TaxesAndLevies,
    SubscriptionTerms,
    TowerTerms,
    TowerLayerTemplate,
    BundledTerms,
    BundledPackage,
    DecoupledTerms,
    FrontingTerms,
    PricingAdjustments,
    load_entity,
    load_all_entities,
)


class TestCoverageBinding:
    """Tests for coverage binding with appetite constraints."""

    def test_basic_binding(self):
        binding = CoverageBinding(coverage="cyber", configs=["cyber_general"])
        assert binding.coverage == "cyber"
        assert binding.configs == ["cyber_general"]

    def test_binding_with_constraints(self):
        binding = CoverageBinding(
            coverage="energy",
            max_single_limit=500_000_000,
            constraints=[
                AppetiteConstraint(
                    field="tiv",
                    operator="<=",
                    value=100_000_000_000,
                    reason="TIV too high",
                ),
            ],
        )
        assert binding.max_single_limit == 500_000_000
        assert len(binding.constraints) == 1
        assert binding.constraints[0].field == "tiv"


class TestCommercialEntity:
    """Tests for CommercialEntity construction and appetite evaluation."""

    @pytest.fixture
    def entity(self):
        return CommercialEntity(
            id="test_entity",
            name="Test Entity",
            market="us",
            base_currency="USD",
            coverages=[
                CoverageBinding(
                    coverage="cyber",
                    configs=["cyber_general"],
                    max_single_limit=50_000_000,
                    constraints=[
                        AppetiteConstraint(
                            field="revenue",
                            operator="<=",
                            value=10_000_000_000,
                            reason="Revenue too high",
                        ),
                    ],
                ),
            ],
            commission=CommissionStructure(brokerage_rate=0.15),
            taxes_and_levies=TaxesAndLevies(insurance_premium_tax_rate=0.03),
        )

    def test_writes_coverage(self, entity):
        assert entity.writes_coverage("cyber") is True
        assert entity.writes_coverage("marine") is False

    def test_get_coverage_binding(self, entity):
        binding = entity.get_coverage_binding("cyber")
        assert binding is not None
        assert binding.max_single_limit == 50_000_000

    def test_evaluate_appetite_within(self, entity):
        """Submission within appetite should pass."""
        fit, reasons = entity.evaluate_appetite("cyber", {
            "limit": 25_000_000,
            "revenue": 1_000_000_000,
        })
        assert fit is True
        assert reasons == []

    def test_evaluate_appetite_limit_exceeded(self, entity):
        """Submission exceeding max_single_limit should fail."""
        fit, reasons = entity.evaluate_appetite("cyber", {
            "limit": 100_000_000,
            "revenue": 1_000_000_000,
        })
        assert fit is False
        assert any("exceeds maximum" in r for r in reasons)

    def test_evaluate_appetite_constraint_violated(self, entity):
        """Submission violating field constraint should fail."""
        fit, reasons = entity.evaluate_appetite("cyber", {
            "limit": 25_000_000,
            "revenue": 50_000_000_000,
        })
        assert fit is False
        assert any("Revenue too high" in r for r in reasons)

    def test_evaluate_appetite_unknown_coverage(self, entity):
        """Unknown coverage should fail."""
        fit, reasons = entity.evaluate_appetite("marine", {"limit": 1_000_000})
        assert fit is False
        assert any("does not write" in r for r in reasons)

    def test_evaluate_appetite_missing_field_ignored(self, entity):
        """Missing submission fields should not cause constraint violations."""
        fit, reasons = entity.evaluate_appetite("cyber", {
            "limit": 25_000_000,
            # No revenue field
        })
        assert fit is True


class TestDistributionConfig:
    """Tests for distribution configuration types."""

    def test_subscription_distribution(self):
        config = DistributionConfig(
            type=DistributionType.SUBSCRIPTION,
            subscription=SubscriptionTerms(
                minimum_line=0.05,
                maximum_line=0.25,
                default_signed_line=0.10,
            ),
        )
        assert config.type == DistributionType.SUBSCRIPTION
        assert config.subscription.default_signed_line == 0.10

    def test_tower_distribution(self):
        config = DistributionConfig(
            type=DistributionType.TOWER,
            tower=TowerTerms(
                layer_templates=[
                    TowerLayerTemplate(id=1, label="Primary", attachment_pct=0.0, limit_pct=0.20),
                    TowerLayerTemplate(id=2, label="Excess", attachment_pct=0.20, limit_pct=0.80),
                ],
            ),
        )
        assert len(config.tower.layer_templates) == 2

    def test_bundled_distribution(self):
        config = DistributionConfig(
            type=DistributionType.BUNDLED,
            bundled=BundledTerms(
                packages=[
                    BundledPackage(id=1, label="Basic", limit=1_000_000, deductible=10_000),
                    BundledPackage(id=2, label="Premium", limit=5_000_000, deductible=25_000),
                ],
            ),
        )
        assert len(config.bundled.packages) == 2


class TestTaxesAndLevies:
    """Tests for taxes and levies calculation."""

    def test_total_rate(self):
        taxes = TaxesAndLevies(
            insurance_premium_tax_rate=0.12,
            stamp_duty_rate=0.005,
            regulatory_levy_rate=0.01,
        )
        expected = 0.12 + 0.005 + 0.01
        assert abs(taxes.total_rate - expected) < 0.0001


class TestEntityYAMLLoading:
    """Tests for loading entity YAML files."""

    def test_load_syndicate_example(self):
        entity = load_entity("syndicate_example")
        if entity is None:
            pytest.skip("syndicate_example.yaml not found")
        assert entity.id == "syndicate_example"
        assert entity.base_currency == "GBP"
        assert entity.writes_coverage("energy")

    def test_load_mga_example(self):
        entity = load_entity("mga_us_cyber")
        if entity is None:
            pytest.skip("mga_us_cyber.yaml not found")
        assert entity.id == "mga_us_cyber"
        assert entity.base_currency == "USD"
        assert entity.writes_coverage("cyber")

    def test_load_all_entities(self):
        entities = load_all_entities()
        assert isinstance(entities, dict)
        # Should find at least the two example entities
        assert len(entities) >= 2

    def test_load_nonexistent_entity(self):
        entity = load_entity("nonexistent_entity_xyz")
        assert entity is None
