"""
DSI Signal Library (Phase 13)

Reusable signal components for coverage building.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .types import (
    IndustryProfile,
    SignalGroupDefinition,
    SignalRecommendation,
    SignalTemplate,
)


logger = logging.getLogger("dsi.builder.library")


class SignalLibrary:
    """
    Library of reusable signal components.

    Provides:
    - Standard signal groups
    - Industry-specific recommendations
    - Signal templates for implementation
    """

    # Standard signal groups
    SIGNAL_GROUPS: Dict[str, SignalGroupDefinition] = {
        "technical_infrastructure": SignalGroupDefinition(
            group_id="technical_infrastructure",
            name="Technical Infrastructure",
            description="Security posture and technical capabilities",
            signals=[
                "security_headers",
                "tls_configuration",
                "email_authentication",
                "dns_security",
                "web_security",
                "ssl_certificate",
                "content_security_policy",
            ],
            applicable_industries=["technology", "financial", "healthcare", "retail"],
            default_weight=0.20,
        ),
        "corporate_footprint": SignalGroupDefinition(
            group_id="corporate_footprint",
            name="Corporate Footprint",
            description="Company presence and visibility",
            signals=[
                "website_quality",
                "security_disclosure",
                "leadership_visibility",
                "social_presence",
                "brand_reputation",
                "media_coverage",
                "investor_relations",
            ],
            applicable_industries=["all"],
            default_weight=0.15,
        ),
        "network_authority": SignalGroupDefinition(
            group_id="network_authority",
            name="Network Authority",
            description="Business relationships and ecosystem",
            signals=[
                "customer_quality",
                "partner_ecosystem",
                "certification_status",
                "vendor_relationships",
                "industry_associations",
                "supply_chain_visibility",
            ],
            applicable_industries=["all"],
            default_weight=0.15,
        ),
        "financial_health": SignalGroupDefinition(
            group_id="financial_health",
            name="Financial Health",
            description="Financial stability indicators",
            signals=[
                "revenue_growth",
                "profitability",
                "liquidity_ratio",
                "debt_ratio",
                "credit_rating",
                "stock_performance",
                "funding_status",
            ],
            applicable_industries=["all"],
            default_weight=0.20,
        ),
        "governance": SignalGroupDefinition(
            group_id="governance",
            name="Governance",
            description="Corporate governance and leadership",
            signals=[
                "board_composition",
                "leadership_stability",
                "executive_experience",
                "governance_disclosure",
                "audit_committee",
                "compensation_practices",
            ],
            applicable_industries=["public_company", "financial", "healthcare"],
            default_weight=0.15,
        ),
        "regulatory_compliance": SignalGroupDefinition(
            group_id="regulatory_compliance",
            name="Regulatory Compliance",
            description="Compliance and regulatory standing",
            signals=[
                "regulatory_filings",
                "enforcement_actions",
                "license_status",
                "compliance_certifications",
                "privacy_compliance",
                "industry_regulations",
            ],
            applicable_industries=["financial", "healthcare", "energy"],
            default_weight=0.15,
        ),
        "cyber_security": SignalGroupDefinition(
            group_id="cyber_security",
            name="Cyber Security",
            description="Cybersecurity posture and practices",
            signals=[
                "vulnerability_management",
                "incident_response",
                "security_certifications",
                "breach_history",
                "security_budget",
                "security_team",
                "penetration_testing",
            ],
            applicable_industries=["technology", "financial", "healthcare", "retail"],
            default_weight=0.20,
        ),
        "operational": SignalGroupDefinition(
            group_id="operational",
            name="Operational",
            description="Operational capabilities",
            signals=[
                "business_continuity",
                "disaster_recovery",
                "operational_resilience",
                "technology_stack",
                "process_maturity",
                "quality_management",
            ],
            applicable_industries=["all"],
            default_weight=0.10,
        ),
    }

    # Industry profiles
    INDUSTRY_PROFILES: Dict[str, IndustryProfile] = {
        "financial_services": IndustryProfile(
            industry="financial_services",
            primary_groups=["financial_health", "regulatory_compliance", "governance"],
            secondary_groups=["cyber_security", "operational"],
            risk_focus=["credit_risk", "market_risk", "regulatory_risk", "cyber_risk"],
            weight_adjustments={
                "regulatory_compliance": 0.25,
                "financial_health": 0.25,
                "governance": 0.20,
            },
        ),
        "technology": IndustryProfile(
            industry="technology",
            primary_groups=["technical_infrastructure", "cyber_security", "corporate_footprint"],
            secondary_groups=["financial_health", "network_authority"],
            risk_focus=["cyber_risk", "ip_risk", "technology_obsolescence"],
            weight_adjustments={
                "technical_infrastructure": 0.25,
                "cyber_security": 0.25,
            },
        ),
        "healthcare": IndustryProfile(
            industry="healthcare",
            primary_groups=["regulatory_compliance", "cyber_security", "operational"],
            secondary_groups=["governance", "financial_health"],
            risk_focus=["patient_safety", "data_privacy", "regulatory_compliance"],
            weight_adjustments={
                "regulatory_compliance": 0.25,
                "cyber_security": 0.20,
            },
        ),
        "manufacturing": IndustryProfile(
            industry="manufacturing",
            primary_groups=["operational", "network_authority", "financial_health"],
            secondary_groups=["technical_infrastructure", "corporate_footprint"],
            risk_focus=["supply_chain_risk", "product_liability", "environmental_risk"],
            weight_adjustments={
                "operational": 0.25,
                "network_authority": 0.20,
            },
        ),
        "retail": IndustryProfile(
            industry="retail",
            primary_groups=["cyber_security", "corporate_footprint", "operational"],
            secondary_groups=["financial_health", "network_authority"],
            risk_focus=["data_breach", "payment_security", "brand_reputation"],
            weight_adjustments={
                "cyber_security": 0.25,
                "corporate_footprint": 0.20,
            },
        ),
    }

    def __init__(self):
        """Initialize SignalLibrary."""
        self._custom_signals: Dict[str, Dict] = {}

    def get_signals_for_industry(
        self,
        industry: str,
    ) -> List[SignalRecommendation]:
        """
        Get recommended signals for an industry.

        Args:
            industry: Industry name

        Returns:
            List of signal recommendations ranked by relevance
        """
        recommendations: List[SignalRecommendation] = []

        # Get industry profile
        profile = self.get_industry_profile(industry)

        if profile:
            # Add signals from primary groups with high relevance
            for group_id in profile.primary_groups:
                group = self.SIGNAL_GROUPS.get(group_id)
                if group:
                    weight = profile.weight_adjustments.get(group_id, group.default_weight)
                    for signal in group.signals:
                        recommendations.append(SignalRecommendation(
                            signal_id=signal,
                            signal_name=self._format_signal_name(signal),
                            group_id=group_id,
                            relevance_score=0.9,
                            suggested_weight=weight / len(group.signals),
                        ))

            # Add signals from secondary groups with lower relevance
            for group_id in profile.secondary_groups:
                group = self.SIGNAL_GROUPS.get(group_id)
                if group:
                    weight = profile.weight_adjustments.get(group_id, group.default_weight * 0.7)
                    for signal in group.signals:
                        recommendations.append(SignalRecommendation(
                            signal_id=signal,
                            signal_name=self._format_signal_name(signal),
                            group_id=group_id,
                            relevance_score=0.7,
                            suggested_weight=weight / len(group.signals),
                        ))
        else:
            # Default: use all general groups
            for group_id, group in self.SIGNAL_GROUPS.items():
                if "all" in group.applicable_industries:
                    for signal in group.signals:
                        recommendations.append(SignalRecommendation(
                            signal_id=signal,
                            signal_name=self._format_signal_name(signal),
                            group_id=group_id,
                            relevance_score=0.6,
                            suggested_weight=group.default_weight / len(group.signals),
                        ))

        # Sort by relevance
        recommendations.sort(key=lambda r: r.relevance_score, reverse=True)

        return recommendations

    def get_industry_profile(self, industry: str) -> Optional[IndustryProfile]:
        """Get profile for industry."""
        industry_lower = industry.lower().replace(" ", "_")

        # Direct match
        if industry_lower in self.INDUSTRY_PROFILES:
            return self.INDUSTRY_PROFILES[industry_lower]

        # Partial match
        for key, profile in self.INDUSTRY_PROFILES.items():
            if key in industry_lower or industry_lower in key:
                return profile

        return None

    def get_signal_groups(self) -> List[SignalGroupDefinition]:
        """Get all available signal groups."""
        return list(self.SIGNAL_GROUPS.values())

    def get_signal_group(self, group_id: str) -> Optional[SignalGroupDefinition]:
        """Get a specific signal group."""
        return self.SIGNAL_GROUPS.get(group_id)

    def has_signal(self, signal_id: str) -> bool:
        """Check if signal exists in library."""
        for group in self.SIGNAL_GROUPS.values():
            if signal_id in group.signals:
                return True
        return signal_id in self._custom_signals

    def get_signal_template(self, signal_id: str) -> Optional[SignalTemplate]:
        """Get implementation template for a signal."""
        return SignalTemplate(
            signal_id=signal_id,
            signal_name=self._format_signal_name(signal_id),
            description=f"Signal for {signal_id}",
            extractor_template=self._get_extractor_template(signal_id),
            aggregator_template=self._get_aggregator_template(signal_id),
            inference_template=self._get_inference_template(signal_id),
            test_template=self._get_test_template(signal_id),
        )

    def add_custom_signal(
        self,
        signal_id: str,
        name: str,
        group_id: str,
        description: str = "",
    ) -> None:
        """Add a custom signal to the library."""
        self._custom_signals[signal_id] = {
            "name": name,
            "group_id": group_id,
            "description": description,
        }

    def _format_signal_name(self, signal_id: str) -> str:
        """Format signal ID as readable name."""
        return signal_id.replace("_", " ").title()

    def _get_extractor_template(self, signal_id: str) -> str:
        """Get extractor template."""
        return f'''async def extract_{signal_id}(entity_id: str) -> Dict[str, Any]:
    """Extract {signal_id} data for entity."""
    # TODO: Implement extraction logic
    return {{"raw_data": None, "extracted_at": datetime.utcnow()}}
'''

    def _get_aggregator_template(self, signal_id: str) -> str:
        """Get aggregator template."""
        return f'''def aggregate_{signal_id}(raw_data: Dict[str, Any]) -> float:
    """Aggregate {signal_id} to score (0-100)."""
    # TODO: Implement aggregation logic
    return 75.0
'''

    def _get_inference_template(self, signal_id: str) -> str:
        """Get inference template."""
        return f'''def infer_{signal_id}(score: float, context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate inference from {signal_id} score."""
    # TODO: Implement inference logic
    return {{"score": score, "insight": None}}
'''

    def _get_test_template(self, signal_id: str) -> str:
        """Get test template."""
        return f'''def test_{signal_id}_extraction():
    """Test {signal_id} extraction."""
    # TODO: Implement test
    assert True

def test_{signal_id}_aggregation():
    """Test {signal_id} aggregation."""
    # TODO: Implement test
    assert True
'''
