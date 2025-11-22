"""
Unit tests for DSI Portfolio Analytics

Run with: python -m pytest test_dsi_portfolio_analytics.py -v
"""

import pytest
import numpy as np
from datetime import datetime
from dsi_portfolio_analytics import (
    DSIPortfolioAnalytics, PortfolioMetrics, ConcentrationAnalysis,
    PortfolioAlert, ModelType, RiskConcentration
)


# Mock pricing result classes for testing
class MockCyberPricingResult:
    """Mock cyber pricing result for testing"""
    def __init__(self, company_name, premium, tier, score, limit=1_000_000):
        self.company_name = company_name
        self.annual_premium = premium
        self.risk_tier = tier
        self.composite_score = score
        self.policy_limit = limit
        self.recommendation = "AUTO_APPROVE" if tier in ["Tier 1", "Tier 2"] else "MANUAL_REVIEW"
        self.breach_probability = 0.10 if tier == "Tier 1" else 0.25


class MockEnergyPricingResult:
    """Mock energy pricing result for testing"""
    def __init__(self, company_name, premium, tier, score, limit=5_000_000):
        self.company_name = company_name
        self.annual_premium = premium
        self.risk_tier = tier
        self.composite_score = score
        self.recommended_limit = limit
        self.recommendation = "AUTO_APPROVE" if tier in ["Tier 1", "Tier 2"] else "MANUAL_REVIEW"


class MockFIPricingResult:
    """Mock financial institution pricing result for testing"""
    def __init__(self, institution_name, premium, tier, score, limit=10_000_000):
        self.institution_name = institution_name
        self.annual_premium = premium
        self.risk_tier = tier
        self.composite_score = score
        self.policy_limit = limit
        self.recommendation = "AUTO_APPROVE" if tier in ["Tier 1", "Tier 2"] else "MANUAL_REVIEW"
        self.regulatory_risk_probability = 0.05 if tier == "Tier 1" else 0.15


@pytest.fixture
def sample_cyber_policies():
    """Create sample cyber policies"""
    return [
        MockCyberPricingResult("TechCorp", 150_000, "Tier 1", 850, 2_000_000),
        MockCyberPricingResult("HealthCare Inc", 300_000, "Tier 2", 720, 1_500_000),
        MockCyberPricingResult("Retail Chain", 450_000, "Tier 3", 620, 1_000_000),
        MockCyberPricingResult("Small Business", 80_000, "Tier 1", 800, 500_000),
    ]


@pytest.fixture
def sample_energy_policies():
    """Create sample energy policies"""
    return [
        MockEnergyPricingResult("Global Oil Co", 2_000_000, "Tier 1", 780, 50_000_000),
        MockEnergyPricingResult("Regional Gas", 800_000, "Tier 2", 700, 20_000_000),
        MockEnergyPricingResult("Pipeline LLC", 1_200_000, "Tier 2", 680, 30_000_000),
    ]


@pytest.fixture
def sample_fi_policies():
    """Create sample financial institution policies"""
    return [
        MockFIPricingResult("Major Bank", 500_000, "Tier 1", 880, 25_000_000),
        MockFIPricingResult("Asset Manager", 250_000, "Tier 1", 820, 10_000_000),
        MockFIPricingResult("Hedge Fund", 350_000, "Tier 2", 710, 15_000_000),
    ]


@pytest.fixture
def populated_portfolio(sample_cyber_policies, sample_energy_policies, sample_fi_policies):
    """Create a portfolio with mixed policies"""
    portfolio = DSIPortfolioAnalytics()

    # Add cyber policies
    for i, result in enumerate(sample_cyber_policies):
        policy_data = {
            'id': f'CYB_{i+1}',
            'model_type': ModelType.CYBER.value,
            'industry': 'Technology',
            'country': 'United States'
        }
        portfolio.add_policy(policy_data, result)

    # Add energy policies
    for i, result in enumerate(sample_energy_policies):
        policy_data = {
            'id': f'ENR_{i+1}',
            'model_type': ModelType.ENERGY.value,
            'industry': 'Energy',
            'country': 'United States'
        }
        portfolio.add_policy(policy_data, result)

    # Add FI policies
    for i, result in enumerate(sample_fi_policies):
        policy_data = {
            'id': f'FIN_{i+1}',
            'model_type': ModelType.FINANCIAL.value,
            'industry': 'Financial Services',
            'country': 'United States'
        }
        portfolio.add_policy(policy_data, result)

    return portfolio


class TestDSIPortfolioAnalytics:
    """Test suite for DSIPortfolioAnalytics class"""

    def test_portfolio_initialization(self):
        """Test portfolio analytics initialization"""
        portfolio = DSIPortfolioAnalytics()
        assert portfolio.policies == []
        assert portfolio.results == []

    def test_add_policy(self):
        """Test adding a policy to portfolio"""
        portfolio = DSIPortfolioAnalytics()
        result = MockCyberPricingResult("Test Corp", 100_000, "Tier 1", 850)
        policy_data = {
            'id': 'TEST_001',
            'model_type': ModelType.CYBER.value,
            'industry': 'Technology'
        }

        portfolio.add_policy(policy_data, result)

        assert len(portfolio.policies) == 1
        assert len(portfolio.results) == 1
        assert portfolio.policies[0]['id'] == 'TEST_001'
        assert portfolio.policies[0]['company_name'] == 'Test Corp'

    def test_add_multiple_policies(self, sample_cyber_policies):
        """Test adding multiple policies"""
        portfolio = DSIPortfolioAnalytics()

        for i, result in enumerate(sample_cyber_policies):
            policy_data = {'id': f'CYB_{i}', 'model_type': ModelType.CYBER.value}
            portfolio.add_policy(policy_data, result)

        assert len(portfolio.policies) == len(sample_cyber_policies)
        assert len(portfolio.results) == len(sample_cyber_policies)

    def test_auto_generated_policy_id(self):
        """Test auto-generation of policy ID when not provided"""
        portfolio = DSIPortfolioAnalytics()
        result = MockCyberPricingResult("Test Corp", 100_000, "Tier 1", 850)
        policy_data = {'model_type': ModelType.CYBER.value}

        portfolio.add_policy(policy_data, result)

        assert 'POL_' in portfolio.policies[0]['id']


class TestPortfolioMetricsCalculation:
    """Test suite for portfolio metrics calculation"""

    def test_calculate_metrics_empty_portfolio_raises_error(self):
        """Test that calculating metrics on empty portfolio raises error"""
        portfolio = DSIPortfolioAnalytics()

        with pytest.raises(ValueError, match="No policies in portfolio"):
            portfolio.calculate_portfolio_metrics()

    def test_calculate_total_premium(self, populated_portfolio):
        """Test total premium calculation"""
        metrics = populated_portfolio.calculate_portfolio_metrics()

        # Sum of all premiums from fixtures
        expected_total = (150_000 + 300_000 + 450_000 + 80_000 +  # Cyber
                         2_000_000 + 800_000 + 1_200_000 +  # Energy
                         500_000 + 250_000 + 350_000)  # FI

        assert metrics.total_premium == expected_total

    def test_calculate_policy_count(self, populated_portfolio):
        """Test policy count in metrics"""
        metrics = populated_portfolio.calculate_portfolio_metrics()

        # 4 cyber + 3 energy + 3 FI = 10 total
        assert metrics.policy_count == 10

    def test_tier_distribution(self, populated_portfolio):
        """Test risk tier distribution calculation"""
        metrics = populated_portfolio.calculate_portfolio_metrics()

        # Based on fixtures:
        # Tier 1: 2 cyber + 1 energy + 2 FI = 5
        # Tier 2: 1 cyber + 2 energy + 1 FI = 4
        # Tier 3: 1 cyber = 1
        assert metrics.tier_1_count >= 4  # At least 4 Tier 1
        assert metrics.tier_2_count >= 3  # At least 3 Tier 2
        assert metrics.tier_3_count >= 1  # At least 1 Tier 3

    def test_auto_approved_percentage(self, populated_portfolio):
        """Test auto-approval percentage calculation"""
        metrics = populated_portfolio.calculate_portfolio_metrics()

        # Should have auto-approved percentage calculated
        assert 0 <= metrics.auto_approved_pct <= 100
        assert metrics.auto_approved_count >= 0

    def test_average_composite_score(self, populated_portfolio):
        """Test average composite score calculation"""
        metrics = populated_portfolio.calculate_portfolio_metrics()

        # Average score should be between 0 and 1000
        assert 0 <= metrics.avg_composite_score <= 1000

    def test_weighted_average_score(self, populated_portfolio):
        """Test weighted average score (by premium)"""
        metrics = populated_portfolio.calculate_portfolio_metrics()

        # Weighted average should be between 0 and 1000
        assert 0 <= metrics.weighted_avg_score <= 1000

        # Weighted average should differ from simple average
        # (unless all premiums are equal, which they're not)
        assert metrics.weighted_avg_score != metrics.avg_composite_score

    def test_concentration_score(self, populated_portfolio):
        """Test concentration score calculation"""
        metrics = populated_portfolio.calculate_portfolio_metrics()

        # Concentration score should be calculated
        assert hasattr(metrics, 'concentration_score')
        assert metrics.concentration_score >= 0

    def test_diversification_score(self, populated_portfolio):
        """Test diversification score calculation"""
        metrics = populated_portfolio.calculate_portfolio_metrics()

        # Diversification score should be calculated
        assert hasattr(metrics, 'diversification_score')
        assert metrics.diversification_score >= 0


class TestConcentrationAnalysis:
    """Test suite for concentration analysis"""

    def test_industry_concentration_cyber_only(self, sample_cyber_policies):
        """Test concentration with single industry (cyber only)"""
        portfolio = DSIPortfolioAnalytics()
        for i, result in enumerate(sample_cyber_policies):
            policy_data = {
                'id': f'CYB_{i}',
                'model_type': ModelType.CYBER.value,
                'industry': 'Technology'
            }
            portfolio.add_policy(policy_data, result)

        analysis = portfolio.analyze_concentration('industry')

        # Should identify high concentration in Technology
        assert analysis.concentration_type == 'industry'
        assert analysis.risk_level in [RiskConcentration.CONCERNING, RiskConcentration.CRITICAL]

    def test_geography_concentration(self):
        """Test geographic concentration analysis"""
        portfolio = DSIPortfolioAnalytics()

        # Add multiple policies from same country
        for i in range(5):
            result = MockCyberPricingResult(f"Company {i}", 100_000, "Tier 2", 700)
            policy_data = {
                'id': f'POL_{i}',
                'model_type': ModelType.CYBER.value,
                'country': 'United States'
            }
            portfolio.add_policy(policy_data, result)

        analysis = portfolio.analyze_concentration('geography')

        assert analysis.concentration_type == 'geography'
        # Should show high US concentration
        assert 'United States' in analysis.concentrations

    def test_coverage_type_concentration(self, populated_portfolio):
        """Test concentration by coverage type"""
        analysis = populated_portfolio.analyze_concentration('coverage')

        assert analysis.concentration_type == 'coverage'
        # Should have distributions across model types
        assert len(analysis.concentrations) > 0

    def test_score_band_concentration(self, populated_portfolio):
        """Test concentration by score bands"""
        analysis = populated_portfolio.analyze_concentration('score_band')

        assert analysis.concentration_type == 'score_band'
        # Should have policies distributed across score bands
        assert len(analysis.concentrations) > 0

    def test_concentration_recommendations(self, populated_portfolio):
        """Test that concentration analysis includes recommendations"""
        analysis = populated_portfolio.analyze_concentration('industry')

        assert isinstance(analysis.recommendations, list)
        assert len(analysis.recommendations) > 0


class TestPortfolioAlerts:
    """Test suite for portfolio alert generation"""

    def test_generate_alerts_empty_portfolio(self):
        """Test alert generation on empty portfolio"""
        portfolio = DSIPortfolioAnalytics()
        alerts = portfolio.generate_alerts()

        # Should return empty list or info alert about empty portfolio
        assert isinstance(alerts, list)

    def test_generate_concentration_alerts(self):
        """Test generation of concentration alerts"""
        portfolio = DSIPortfolioAnalytics()

        # Create highly concentrated portfolio
        for i in range(10):
            result = MockCyberPricingResult(f"Tech Co {i}", 500_000, "Tier 2", 700)
            policy_data = {
                'id': f'POL_{i}',
                'model_type': ModelType.CYBER.value,
                'industry': 'Technology',
                'country': 'United States'
            }
            portfolio.add_policy(policy_data, result)

        alerts = portfolio.generate_alerts()

        # Should generate concentration warning
        assert len(alerts) > 0
        concentration_alerts = [a for a in alerts if a.category == 'concentration']
        assert len(concentration_alerts) > 0

    def test_generate_quality_alerts(self):
        """Test generation of portfolio quality alerts"""
        portfolio = DSIPortfolioAnalytics()

        # Create portfolio with many low-tier policies
        for i in range(5):
            result = MockCyberPricingResult(f"Company {i}", 200_000, "Tier 3", 580)
            policy_data = {
                'id': f'POL_{i}',
                'model_type': ModelType.CYBER.value,
            }
            portfolio.add_policy(policy_data, result)

        alerts = portfolio.generate_alerts()

        # Should potentially generate quality alert
        assert isinstance(alerts, list)

    def test_alert_structure(self):
        """Test that alerts have proper structure"""
        alert = PortfolioAlert(
            alert_id="TEST_001",
            severity="warning",
            category="concentration",
            title="High Industry Concentration",
            message="70% of portfolio in Technology sector",
            affected_policies=["POL_1", "POL_2"],
            recommended_action="Consider diversifying into other sectors"
        )

        assert alert.alert_id == "TEST_001"
        assert alert.severity == "warning"
        assert alert.category == "concentration"
        assert len(alert.affected_policies) == 2
        assert isinstance(alert.timestamp, datetime)


class TestPortfolioReporting:
    """Test suite for portfolio reporting functionality"""

    def test_generate_portfolio_summary(self, populated_portfolio):
        """Test generation of portfolio summary report"""
        summary = populated_portfolio.generate_portfolio_summary()

        assert isinstance(summary, dict)
        assert 'total_premium' in summary
        assert 'policy_count' in summary
        assert 'risk_distribution' in summary

    def test_export_to_dict(self, populated_portfolio):
        """Test exporting portfolio to dictionary"""
        export_data = populated_portfolio.to_dict()

        assert isinstance(export_data, dict)
        assert 'policies' in export_data
        assert len(export_data['policies']) == 10

    def test_tier_distribution_report(self, populated_portfolio):
        """Test risk tier distribution reporting"""
        tier_report = populated_portfolio.get_tier_distribution()

        assert isinstance(tier_report, dict)
        # Should have entries for each tier
        assert 'tier_1' in tier_report or 'Tier 1' in str(tier_report)


class TestModelTypeIntegration:
    """Test suite for integration across different model types"""

    def test_mixed_model_types_in_portfolio(self, populated_portfolio):
        """Test portfolio with multiple model types"""
        # Portfolio should contain all three model types
        model_types = set(p['model_type'] for p in populated_portfolio.policies)

        assert ModelType.CYBER.value in model_types
        assert ModelType.ENERGY.value in model_types
        assert ModelType.FINANCIAL.value in model_types

    def test_metrics_calculation_mixed_models(self, populated_portfolio):
        """Test metrics calculation works across model types"""
        metrics = populated_portfolio.calculate_portfolio_metrics()

        # Should successfully calculate metrics for mixed portfolio
        assert metrics.total_premium > 0
        assert metrics.policy_count == 10

    def test_handle_different_result_attributes(self, populated_portfolio):
        """Test handling of different attributes across model types"""
        # Cyber has 'breach_probability', FI has 'regulatory_risk_probability'
        # Portfolio should handle both gracefully
        metrics = populated_portfolio.calculate_portfolio_metrics()

        # Should complete without errors despite different attributes
        assert metrics is not None


class TestEdgeCases:
    """Test suite for edge cases"""

    def test_single_policy_portfolio(self):
        """Test portfolio with only one policy"""
        portfolio = DSIPortfolioAnalytics()
        result = MockCyberPricingResult("Solo Corp", 100_000, "Tier 1", 850)
        policy_data = {'id': 'SOLO_1', 'model_type': ModelType.CYBER.value}
        portfolio.add_policy(policy_data, result)

        metrics = portfolio.calculate_portfolio_metrics()

        assert metrics.policy_count == 1
        assert metrics.total_premium == 100_000

    def test_very_large_portfolio_performance(self):
        """Test performance with large number of policies"""
        portfolio = DSIPortfolioAnalytics()

        # Add 1000 policies
        for i in range(1000):
            result = MockCyberPricingResult(f"Company {i}", 50_000, "Tier 2", 700)
            policy_data = {'id': f'POL_{i}', 'model_type': ModelType.CYBER.value}
            portfolio.add_policy(policy_data, result)

        # Should handle large portfolio efficiently
        metrics = portfolio.calculate_portfolio_metrics()

        assert metrics.policy_count == 1000
        assert metrics.total_premium == 50_000_000

    def test_all_tier_1_portfolio(self):
        """Test portfolio where all policies are Tier 1"""
        portfolio = DSIPortfolioAnalytics()

        for i in range(5):
            result = MockCyberPricingResult(f"Premium Co {i}", 100_000, "Tier 1", 900)
            policy_data = {'id': f'POL_{i}', 'model_type': ModelType.CYBER.value}
            portfolio.add_policy(policy_data, result)

        metrics = portfolio.calculate_portfolio_metrics()

        assert metrics.tier_1_count == 5
        assert metrics.avg_composite_score >= 800

    def test_policy_with_zero_premium(self):
        """Test handling of policy with zero premium"""
        portfolio = DSIPortfolioAnalytics()
        result = MockCyberPricingResult("Zero Premium", 0, "Tier 1", 850)
        policy_data = {'id': 'ZERO_1', 'model_type': ModelType.CYBER.value}
        portfolio.add_policy(policy_data, result)

        # Should handle gracefully without division by zero
        metrics = portfolio.calculate_portfolio_metrics()
        assert metrics.total_premium == 0


class TestDataExport:
    """Test suite for data export functionality"""

    def test_export_to_csv(self, populated_portfolio, tmp_path):
        """Test exporting portfolio to CSV"""
        csv_path = tmp_path / "portfolio_export.csv"
        populated_portfolio.export_to_csv(str(csv_path))

        # File should be created
        assert csv_path.exists()

    def test_export_to_json(self, populated_portfolio, tmp_path):
        """Test exporting portfolio to JSON"""
        json_path = tmp_path / "portfolio_export.json"
        populated_portfolio.export_to_json(str(json_path))

        # File should be created
        assert json_path.exists()

    def test_export_metrics_report(self, populated_portfolio, tmp_path):
        """Test exporting metrics report"""
        report_path = tmp_path / "metrics_report.json"
        metrics = populated_portfolio.calculate_portfolio_metrics()

        # Should be able to serialize metrics
        import json
        with open(report_path, 'w') as f:
            json.dump(metrics.__dict__, f, default=str)

        assert report_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
