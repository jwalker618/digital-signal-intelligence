"""
Unit tests for DSI Cyber Insurance Pricing Model

Run with: python -m pytest test_dsi_cyber_pricing.py -v
"""

import pytest
from dsi_cyber_pricing import (
    CompanySize,
    CyberCompanyProfile,
    CyberCoverageType,
    CyberInsurancePricingModel,
    CyberSecuritySignals,
    IndustryVertical,
)


@pytest.fixture
def strong_security_signals():
    """Fixture for company with excellent security posture"""
    return CyberSecuritySignals(
        ssl_certificate=95,
        tls_version=100,
        security_headers=90,
        dnssec_implementation=85,
        spf_dmarc_dkim=92,
        web_application_firewall=88,
        open_ports_score=90,
        outdated_software=88,
        known_vulnerabilities=92,
        exposed_databases=100,
        leaked_credentials=95,
        breached_history=100,
        security_certifications=90,
        privacy_policy_quality=88,
        incident_response_plan=85,
        bug_bounty_program=92,
        security_team_visibility=87,
        security_blog_activity=80,
        vendor_security_standards=85,
        supply_chain_transparency=82,
        cloud_provider_quality=95,
        third_party_integrations=88,
        data_processor_agreements=85,
        patch_discipline=90,
        security_investment=88,
        employee_training=85,
        mfa_adoption=95,
        backup_procedures=90,
        monitoring_capabilities=92,
    )


@pytest.fixture
def vulnerable_signals():
    """Fixture for company with critical vulnerabilities"""
    return CyberSecuritySignals(
        ssl_certificate=75,
        tls_version=60,
        security_headers=55,
        dnssec_implementation=40,
        spf_dmarc_dkim=50,
        web_application_firewall=45,
        open_ports_score=45,
        outdated_software=38,
        known_vulnerabilities=35,  # CRITICAL
        exposed_databases=40,
        leaked_credentials=30,
        breached_history=35,  # CRITICAL
        security_certifications=55,
        privacy_policy_quality=60,
        incident_response_plan=45,
        bug_bounty_program=0,
        security_team_visibility=50,
        security_blog_activity=30,
        vendor_security_standards=48,
        supply_chain_transparency=42,
        cloud_provider_quality=65,
        third_party_integrations=50,
        data_processor_agreements=45,
        patch_discipline=35,
        security_investment=40,
        employee_training=45,
        mfa_adoption=50,
        backup_procedures=55,
        monitoring_capabilities=48,
    )


@pytest.fixture
def tech_company_secure(strong_security_signals):
    """Secure technology company"""
    return CyberCompanyProfile(
        company_name="SecureTech Inc",
        industry=IndustryVertical.TECHNOLOGY,
        country="United States",
        annual_revenue=100_000_000,
        employees=500,
        size_category=CompanySize.SMALL,
        records_stored=1_000_000,
        pii_volume="medium",
        phi_handler=False,
        pci_scope=False,
        cloud_percentage=85,
        legacy_systems=False,
        bring_your_own_device=False,
        remote_workforce_pct=50,
        prior_incidents=0,
        cyber_insurance_history=2,
        it_budget_pct=15.0,
        signals=strong_security_signals,
    )


@pytest.fixture
def healthcare_vulnerable(vulnerable_signals):
    """Healthcare company with vulnerabilities"""
    return CyberCompanyProfile(
        company_name="Regional Hospital",
        industry=IndustryVertical.HEALTHCARE,
        country="United States",
        annual_revenue=500_000_000,
        employees=3000,
        size_category=CompanySize.MEDIUM,
        records_stored=5_000_000,
        pii_volume="critical",
        phi_handler=True,
        pci_scope=True,
        cloud_percentage=40,
        legacy_systems=True,
        bring_your_own_device=True,
        remote_workforce_pct=30,
        prior_incidents=2,
        cyber_insurance_history=1,
        it_budget_pct=5.0,
        signals=vulnerable_signals,
    )


class TestCyberSecuritySignals:
    """Test suite for CyberSecuritySignals class"""

    def test_category_score_calculation(self, strong_security_signals):
        """Test category score calculations"""
        infra = strong_security_signals.get_category_score("infrastructure")
        vuln = strong_security_signals.get_category_score("vulnerability")
        org = strong_security_signals.get_category_score("organizational")

        assert 85 <= infra <= 95
        assert 85 <= vuln <= 95
        assert 80 <= org <= 90

    def test_composite_score_strong_signals(self, strong_security_signals):
        """Test composite score for strong signals"""
        composite = strong_security_signals.get_composite_score()
        assert 800 <= composite <= 900  # Should be Tier 1

    def test_composite_score_vulnerable(self, vulnerable_signals):
        """Test composite score for vulnerable company"""
        composite = vulnerable_signals.get_composite_score()
        assert 400 <= composite <= 550  # Should be Tier 4/5

    def test_vulnerability_score_critical(self, vulnerable_signals):
        """Test that critical vulnerabilities are detected"""
        vuln_score = vulnerable_signals.get_category_score("vulnerability")
        assert vuln_score < 50  # Should be critically low


class TestCyberPricingModel:
    """Test suite for core pricing model"""

    def test_model_initialization(self):
        """Test model initializes with correct parameters"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)
        assert model.coverage_type == CyberCoverageType.COMPREHENSIVE
        assert len(model.base_rates) == 3  # 3 coverage types
        assert len(model.industry_multipliers) > 0

    def test_base_rates_structure(self):
        """Test base rates are properly structured"""
        model = CyberInsurancePricingModel(CyberCoverageType.FIRST_PARTY)

        # Check all size categories exist
        for coverage in ["first_party", "third_party", "comprehensive"]:
            assert coverage in model.base_rates
            for size in ["small", "medium", "large", "enterprise"]:
                assert size in model.base_rates[coverage]
                assert model.base_rates[coverage][size] > 0

    def test_industry_multipliers_coverage(self):
        """Test all industries have multipliers"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        for industry in IndustryVertical:
            assert industry in model.industry_multipliers
            assert 0.5 <= model.industry_multipliers[industry] <= 2.0

    def test_cyber_maturity_modifier_strong(self, tech_company_secure):
        """Test maturity modifier for strong security"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)
        modifier, score = model.calculate_cyber_maturity_modifier(tech_company_secure.signals)

        assert 0.60 <= modifier <= 0.85  # Should get credit
        assert 800 <= score <= 900

    def test_cyber_maturity_modifier_weak(self, healthcare_vulnerable):
        """Test maturity modifier for weak security"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)
        modifier, score = model.calculate_cyber_maturity_modifier(healthcare_vulnerable.signals)

        assert 1.20 <= modifier <= 2.50  # Should get debit
        assert 400 <= score <= 550


class TestVulnerabilityAssessment:
    """Test suite for vulnerability-specific assessments"""

    def test_vulnerability_modifier_secure(self, strong_security_signals):
        """Test vulnerability modifier for secure company"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)
        modifier, score = model.calculate_vulnerability_modifier(strong_security_signals)

        assert 0.70 <= modifier <= 0.95
        assert score >= 85

    def test_vulnerability_modifier_critical(self, vulnerable_signals):
        """Test vulnerability modifier for critical vulnerabilities"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)
        modifier, score = model.calculate_vulnerability_modifier(vulnerable_signals)

        assert modifier >= 1.60  # Heavy penalty for vulnerabilities
        assert score < 50

    def test_vulnerability_trumps_maturity(self, strong_security_signals):
        """Test that critical vulnerabilities override good overall maturity"""
        # Create signals with good maturity but critical vulnerability
        mixed_signals = CyberSecuritySignals(**strong_security_signals.__dict__)
        mixed_signals.exposed_databases = 20  # Critical vulnerability
        mixed_signals.leaked_credentials = 25  # Critical vulnerability

        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        # Maturity should still be good
        maturity_mod, maturity_score = model.calculate_cyber_maturity_modifier(mixed_signals)
        assert maturity_score >= 700

        # But vulnerability should be bad
        vuln_mod, vuln_score = model.calculate_vulnerability_modifier(mixed_signals)
        assert vuln_score < 60
        assert vuln_mod >= 1.30


class TestDataSensitivityPricing:
    """Test suite for data sensitivity modifiers"""

    def test_pii_volume_impact(self):
        """Test PII volume affects pricing"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        base_company = CyberCompanyProfile(
            company_name="Test",
            industry=IndustryVertical.OTHER,
            country="US",
            annual_revenue=10_000_000,
            employees=100,
            size_category=CompanySize.SMALL,
            pii_volume="low",
        )

        low_mod = model.calculate_data_sensitivity_modifier(base_company)

        base_company.pii_volume = "critical"
        critical_mod = model.calculate_data_sensitivity_modifier(base_company)

        assert critical_mod > low_mod
        assert critical_mod >= 1.50

    def test_phi_handler_premium(self):
        """Test PHI handling increases premium"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        company = CyberCompanyProfile(
            company_name="Test",
            industry=IndustryVertical.HEALTHCARE,
            country="US",
            annual_revenue=10_000_000,
            employees=100,
            size_category=CompanySize.SMALL,
            phi_handler=False,
        )

        no_phi_mod = model.calculate_data_sensitivity_modifier(company)

        company.phi_handler = True
        phi_mod = model.calculate_data_sensitivity_modifier(company)

        assert phi_mod > no_phi_mod
        assert phi_mod / no_phi_mod >= 1.35  # Should be at least 35% higher

    def test_record_volume_impact(self):
        """Test large record volumes increase premium"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        small_records = CyberCompanyProfile(
            company_name="Test",
            industry=IndustryVertical.OTHER,
            country="US",
            annual_revenue=10_000_000,
            employees=100,
            size_category=CompanySize.SMALL,
            records_stored=10_000,
        )

        large_records = CyberCompanyProfile(
            company_name="Test",
            industry=IndustryVertical.OTHER,
            country="US",
            annual_revenue=10_000_000,
            employees=100,
            size_category=CompanySize.SMALL,
            records_stored=100_000_000,
        )

        small_mod = model.calculate_data_sensitivity_modifier(small_records)
        large_mod = model.calculate_data_sensitivity_modifier(large_records)

        assert large_mod > small_mod


class TestBreachProbability:
    """Test suite for breach probability estimation"""

    def test_breach_probability_by_score(self):
        """Test breach probability varies correctly by score"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        high_score_prob = model.estimate_breach_probability(850, IndustryVertical.TECHNOLOGY, 0)
        low_score_prob = model.estimate_breach_probability(350, IndustryVertical.TECHNOLOGY, 0)

        assert low_score_prob > high_score_prob
        assert high_score_prob <= 0.05  # <5% for excellent security
        assert low_score_prob >= 0.40  # >40% for poor security

    def test_industry_affects_probability(self):
        """Test industry adjusts breach probability"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        # Same score, different industries
        healthcare_prob = model.estimate_breach_probability(600, IndustryVertical.HEALTHCARE, 0)
        manufacturing_prob = model.estimate_breach_probability(
            600, IndustryVertical.MANUFACTURING, 0
        )

        assert healthcare_prob > manufacturing_prob  # Healthcare more targeted

    def test_prior_incidents_increase_probability(self):
        """Test prior incidents dramatically increase probability"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        no_incidents = model.estimate_breach_probability(650, IndustryVertical.RETAIL, 0)
        one_incident = model.estimate_breach_probability(650, IndustryVertical.RETAIL, 1)
        two_incidents = model.estimate_breach_probability(650, IndustryVertical.RETAIL, 2)

        assert two_incidents > one_incident > no_incidents
        assert one_incident >= no_incidents * 1.40  # At least 40% increase


class TestPolicyStructure:
    """Test suite for policy structure recommendations"""

    def test_limit_recommendation_scales_with_loss(self, tech_company_secure):
        """Test recommended limits scale with expected loss"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        breach_prob = 0.05
        expected_loss = 5_000_000

        limit, deductible, sublimits = model.recommend_policy_structure(
            tech_company_secure, expected_loss
        )

        assert limit >= expected_loss  # Should cover expected loss
        assert limit >= 1_000_000  # Minimum viable limit
        assert deductible >= 10_000  # Minimum deductible
        assert deductible < limit * 0.10  # Deductible should be reasonable

    def test_sublimits_sum_correctly(self, tech_company_secure):
        """Test sublimits don't exceed policy limit"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        expected_loss = 10_000_000
        limit, deductible, sublimits = model.recommend_policy_structure(
            tech_company_secure, expected_loss
        )

        # Each sublimit should be <= policy limit
        for coverage, amount in sublimits.items():
            assert amount <= limit
            assert amount > 0


class TestRiskTierDetermination:
    """Test suite for risk tier classification"""

    def test_tier_1_requirements(self):
        """Test Tier 1 requires high scores"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        tier = model.determine_risk_tier(850, 90)
        assert "Tier 1" in tier

    def test_tier_5_critical_vulnerabilities(self):
        """Test Tier 5 triggered by critical vulnerabilities"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        # Even with good composite, critical vulns = Tier 5
        tier = model.determine_risk_tier(750, 45)
        assert "Tier 5" in tier or "Critical" in tier

    def test_tier_boundaries(self):
        """Test tier boundary conditions"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        # Test each tier boundary
        assert "Tier 1" in model.determine_risk_tier(800, 85)
        assert "Tier 2" in model.determine_risk_tier(750, 75)
        assert "Tier 3" in model.determine_risk_tier(650, 65)
        assert "Tier 4" in model.determine_risk_tier(550, 55)
        assert "Tier 5" in model.determine_risk_tier(450, 50)


class TestFullPricing:
    """Test suite for complete pricing calculations"""

    def test_pricing_secure_tech_company(self, tech_company_secure):
        """Test full pricing for secure tech company"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)
        result = model.price(tech_company_secure)

        assert result.annual_premium > 0
        assert result.composite_score >= 800
        assert result.vulnerability_score >= 85
        assert "Auto-Approve" in result.recommendation
        assert result.breach_probability < 0.05
        assert result.confidence_level >= 0.85

    def test_pricing_vulnerable_healthcare(self, healthcare_vulnerable):
        """Test full pricing for vulnerable healthcare company"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)
        result = model.price(healthcare_vulnerable)

        assert result.annual_premium > 0
        assert result.composite_score < 600
        assert result.vulnerability_score < 55
        assert "Decline" in result.recommendation or "Manual Review" in result.recommendation
        assert result.breach_probability > 0.25
        assert len(result.conditions) > 0  # Should have conditions

    def test_premium_increases_with_vulnerabilities(self, tech_company_secure):
        """Test premium increases as vulnerabilities worsen"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        # Baseline
        baseline = model.price(tech_company_secure)

        # Add vulnerabilities
        vuln_company = CyberCompanyProfile(**tech_company_secure.__dict__)
        vuln_signals = CyberSecuritySignals(**tech_company_secure.signals.__dict__)
        vuln_signals.known_vulnerabilities = 45
        vuln_signals.exposed_databases = 40
        vuln_company.signals = vuln_signals

        vulnerable = model.price(vuln_company)

        assert vulnerable.annual_premium > baseline.annual_premium * 1.5

    def test_prior_incidents_impact(self, tech_company_secure):
        """Test prior incidents significantly increase premium"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        no_incidents = model.price(tech_company_secure)

        with_incidents = CyberCompanyProfile(**tech_company_secure.__dict__)
        with_incidents.prior_incidents = 2

        incidents_result = model.price(with_incidents)

        assert incidents_result.annual_premium > no_incidents.annual_premium * 1.5
        assert incidents_result.breach_probability > no_incidents.breach_probability * 2


class TestCoverageTypeComparison:
    """Test suite comparing different coverage types"""

    def test_comprehensive_most_expensive(self, tech_company_secure):
        """Test comprehensive coverage is most expensive"""
        first_party = CyberInsurancePricingModel(CyberCoverageType.FIRST_PARTY)
        third_party = CyberInsurancePricingModel(CyberCoverageType.THIRD_PARTY)
        comprehensive = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        fp_result = first_party.price(tech_company_secure)
        tp_result = third_party.price(tech_company_secure)
        comp_result = comprehensive.price(tech_company_secure)

        assert comp_result.annual_premium > fp_result.annual_premium
        assert comp_result.annual_premium > tp_result.annual_premium

    def test_all_coverage_types_price(self, tech_company_secure):
        """Test all coverage types produce valid pricing"""
        for coverage_type in CyberCoverageType:
            model = CyberInsurancePricingModel(coverage_type)
            result = model.price(tech_company_secure)

            assert result.annual_premium > 0
            assert result.composite_score > 0
            assert result.recommendation is not None


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""

    def test_zero_signals_handling(self):
        """Test model handles company with no digital footprint"""
        zero_signals = CyberSecuritySignals()  # All zeros

        company = CyberCompanyProfile(
            company_name="No Presence Corp",
            industry=IndustryVertical.OTHER,
            country="United States",
            annual_revenue=10_000_000,
            employees=50,
            size_category=CompanySize.SMALL,
            signals=zero_signals,
        )

        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)
        result = model.price(company)

        assert result.annual_premium > 0
        assert result.confidence_level < 0.60
        assert (
            "Manual Review" in result.recommendation or "Insufficient Data" in result.recommendation
        )

    def test_extreme_revenue_handling(self):
        """Test model handles extreme revenue values"""
        model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)

        # Very small company
        tiny = CyberCompanyProfile(
            company_name="Tiny",
            industry=IndustryVertical.OTHER,
            country="US",
            annual_revenue=1_000_000,
            employees=5,
            size_category=CompanySize.SMALL,
            signals=CyberSecuritySignals(),
        )

        # Giant company
        giant = CyberCompanyProfile(
            company_name="Giant",
            industry=IndustryVertical.TECHNOLOGY,
            country="US",
            annual_revenue=100_000_000_000,
            employees=200000,
            size_category=CompanySize.ENTERPRISE,
            signals=CyberSecuritySignals(),
        )

        tiny_result = model.price(tiny)
        giant_result = model.price(giant)

        assert tiny_result.annual_premium > 0
        assert giant_result.annual_premium > tiny_result.annual_premium


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
