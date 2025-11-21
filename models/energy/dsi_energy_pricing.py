"""
Digital Signal Intelligence (DSI) Pricing Models for Energy Sector
===================================================================

Upstream, Midstream, and Downstream energy coverage pricing models
based on digital footprint analysis and network intelligence.

Author: John Walker
Date: November 2025
Version: 1.0
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum


class EnergySegment(Enum):
    """Energy sector segments"""
    UPSTREAM = "upstream"  # Exploration & Production
    MIDSTREAM = "midstream"  # Transportation & Storage
    DOWNSTREAM = "downstream"  # Refining & Distribution


class CoverageType(Enum):
    """Insurance coverage types"""
    OPERATORS_EXTRA_EXPENSE = "OEE"
    CONTROL_OF_WELL = "COW"
    POLLUTION_LIABILITY = "POLL"
    PROPERTY_DAMAGE = "PD"
    BUSINESS_INTERRUPTION = "BI"
    GENERAL_LIABILITY = "GL"


@dataclass
class DigitalSignals:
    """Container for digital signal scores"""
    # Infrastructure Signals (0-100)
    ssl_score: float = 0.0
    security_headers: float = 0.0
    domain_age: float = 0.0
    tech_stack_modernity: float = 0.0
    uptime_reliability: float = 0.0
    mobile_optimization: float = 0.0
    
    # Content Signals (0-100)
    update_frequency: float = 0.0
    transparency_score: float = 0.0
    governance_disclosure: float = 0.0
    multilingual_presence: float = 0.0
    certification_visibility: float = 0.0
    incident_response: float = 0.0
    
    # Network Signals (0-100)
    backlink_quality: float = 0.0
    domain_authority: float = 0.0
    industry_citations: float = 0.0
    partnership_quality: float = 0.0
    social_engagement: float = 0.0
    supplier_diversity: float = 0.0
    
    # Behavioral Signals (0-100)
    digital_transformation: float = 0.0
    innovation_signals: float = 0.0
    operational_consistency: float = 0.0
    compliance_history: float = 0.0
    ir_sophistication: float = 0.0
    sustainability_commitment: float = 0.0
    
    def get_category_score(self, category: str) -> float:
        """Calculate average score for a signal category"""
        if category == "infrastructure":
            signals = [self.ssl_score, self.security_headers, self.domain_age,
                      self.tech_stack_modernity, self.uptime_reliability, 
                      self.mobile_optimization]
        elif category == "content":
            signals = [self.update_frequency, self.transparency_score,
                      self.governance_disclosure, self.multilingual_presence,
                      self.certification_visibility, self.incident_response]
        elif category == "network":
            signals = [self.backlink_quality, self.domain_authority,
                      self.industry_citations, self.partnership_quality,
                      self.social_engagement, self.supplier_diversity]
        elif category == "behavioral":
            signals = [self.digital_transformation, self.innovation_signals,
                      self.operational_consistency, self.compliance_history,
                      self.ir_sophistication, self.sustainability_commitment]
        else:
            return 0.0
        
        return np.mean([s for s in signals if s > 0])
    
    def get_composite_score(self) -> float:
        """Calculate composite DSI score (0-1000 scale)"""
        categories = ["infrastructure", "content", "network", "behavioral"]
        scores = [self.get_category_score(cat) for cat in categories]
        # Convert from 0-100 to 0-1000 scale
        return np.mean(scores) * 10


@dataclass
class CompanyProfile:
    """Company information and characteristics"""
    company_name: str
    segment: EnergySegment
    country: str
    annual_revenue: float  # USD
    employees: int
    years_operating: int
    public_traded: bool
    state_owned: bool
    
    # Traditional risk factors
    loss_history_mod: float = 1.0  # Loss history modifier
    claims_frequency: float = 0.0  # Claims per year
    largest_loss: float = 0.0  # USD
    
    # Operational characteristics
    production_volume: Optional[float] = None  # BOE/day for upstream
    pipeline_miles: Optional[float] = None  # Miles for midstream
    refining_capacity: Optional[float] = None  # Barrels/day for downstream
    
    # Digital signals
    signals: DigitalSignals = field(default_factory=DigitalSignals)


@dataclass
class PricingResult:
    """Output of pricing calculation"""
    company_name: str
    segment: str
    coverage: str
    
    # Pricing components
    base_rate: float
    dsi_modifier: float
    loss_history_modifier: float
    size_modifier: float
    territory_modifier: float
    
    # Final pricing
    technical_rate: float
    exposure_base: float
    annual_premium: float
    
    # Risk assessment
    composite_score: float
    risk_tier: str
    confidence_level: float
    expected_loss_ratio: float
    
    # Recommendation
    recommendation: str
    reasoning: str


class DSIEnergyPricingModel:
    """
    Base pricing model for energy sector coverages using Digital Signal Intelligence
    """
    
    def __init__(self, segment: EnergySegment, coverage: CoverageType):
        self.segment = segment
        self.coverage = coverage
        self.base_rates = self._initialize_base_rates()
        self.weights = self._initialize_weights()
        
    def _initialize_base_rates(self) -> Dict[str, float]:
        """Initialize base rates per $1M exposure by segment and coverage"""
        rates = {
            # Upstream rates (per $1M of property value or revenue)
            ("upstream", "OEE"): 1250.0,
            ("upstream", "COW"): 3500.0,
            ("upstream", "POLL"): 2800.0,
            ("upstream", "PD"): 850.0,
            ("upstream", "BI"): 1100.0,
            ("upstream", "GL"): 650.0,
            
            # Midstream rates
            ("midstream", "OEE"): 950.0,
            ("midstream", "POLL"): 2200.0,
            ("midstream", "PD"): 720.0,
            ("midstream", "BI"): 890.0,
            ("midstream", "GL"): 580.0,
            
            # Downstream rates
            ("downstream", "OEE"): 1100.0,
            ("downstream", "POLL"): 1950.0,
            ("downstream", "PD"): 680.0,
            ("downstream", "BI"): 950.0,
            ("downstream", "GL"): 520.0,
        }
        return rates
    
    def _initialize_weights(self) -> Dict[str, Dict[str, float]]:
        """Initialize signal category weights by segment"""
        return {
            "upstream": {
                "infrastructure": 0.20,
                "content": 0.25,
                "network": 0.30,
                "behavioral": 0.25
            },
            "midstream": {
                "infrastructure": 0.25,
                "content": 0.25,
                "network": 0.25,
                "behavioral": 0.25
            },
            "downstream": {
                "infrastructure": 0.22,
                "content": 0.28,
                "network": 0.25,
                "behavioral": 0.25
            }
        }
    
    def calculate_dsi_modifier(self, signals: DigitalSignals) -> Tuple[float, float]:
        """
        Calculate DSI-based rate modifier
        Returns: (modifier, composite_score)
        """
        # Get weighted composite score
        weights = self.weights[self.segment.value]
        
        infra = signals.get_category_score("infrastructure")
        content = signals.get_category_score("content")
        network = signals.get_category_score("network")
        behavioral = signals.get_category_score("behavioral")
        
        composite = (infra * weights["infrastructure"] + 
                    content * weights["content"] +
                    network * weights["network"] +
                    behavioral * weights["behavioral"])
        
        # Convert to 0-1000 scale
        composite_score = composite * 10
        
        # Calculate modifier based on score
        # Score ranges: 0-500 (high risk), 500-650 (elevated), 650-750 (standard), 750+ (preferred)
        if composite_score >= 750:
            modifier = 0.70 + (1000 - composite_score) / 1000 * 0.15  # 0.70-0.85
        elif composite_score >= 650:
            modifier = 0.85 + (750 - composite_score) / 100 * 0.15  # 0.85-1.00
        elif composite_score >= 500:
            modifier = 1.00 + (650 - composite_score) / 150 * 0.25  # 1.00-1.25
        else:
            modifier = 1.25 + (500 - composite_score) / 500 * 0.50  # 1.25-1.75
        
        return modifier, composite_score
    
    def calculate_size_modifier(self, company: CompanyProfile) -> float:
        """Calculate size-based modifier"""
        revenue_mm = company.annual_revenue / 1_000_000
        
        if revenue_mm < 100:
            return 1.25
        elif revenue_mm < 500:
            return 1.15
        elif revenue_mm < 2000:
            return 1.00
        elif revenue_mm < 10000:
            return 0.92
        else:
            return 0.85
    
    def calculate_territory_modifier(self, country: str) -> float:
        """Calculate territory-based modifier"""
        # Simplified territory scoring
        tier1 = ["United States", "Canada", "United Kingdom", "Norway", 
                "Australia", "Netherlands"]
        tier2 = ["Brazil", "Mexico", "Saudi Arabia", "UAE", "Qatar", "Singapore"]
        tier3 = ["Russia", "China", "India", "Indonesia", "Malaysia", "Nigeria"]
        
        if country in tier1:
            return 0.90
        elif country in tier2:
            return 1.10
        elif country in tier3:
            return 1.35
        else:
            return 1.20
    
    def determine_risk_tier(self, composite_score: float) -> str:
        """Determine risk tier from composite score"""
        if composite_score >= 750:
            return "Tier 1 - Preferred"
        elif composite_score >= 650:
            return "Tier 2 - Standard"
        elif composite_score >= 500:
            return "Tier 3 - Elevated"
        else:
            return "Tier 4 - High Risk"
    
    def calculate_confidence(self, signals: DigitalSignals) -> float:
        """Calculate confidence level in the pricing"""
        # Count non-zero signals
        all_signals = [
            signals.ssl_score, signals.security_headers, signals.domain_age,
            signals.tech_stack_modernity, signals.uptime_reliability,
            signals.mobile_optimization, signals.update_frequency,
            signals.transparency_score, signals.governance_disclosure,
            signals.multilingual_presence, signals.certification_visibility,
            signals.incident_response, signals.backlink_quality,
            signals.domain_authority, signals.industry_citations,
            signals.partnership_quality, signals.social_engagement,
            signals.supplier_diversity, signals.digital_transformation,
            signals.innovation_signals, signals.operational_consistency,
            signals.compliance_history, signals.ir_sophistication,
            signals.sustainability_commitment
        ]
        
        non_zero = sum(1 for s in all_signals if s > 0)
        signal_coverage = non_zero / len(all_signals)
        
        # Base confidence on signal coverage
        if signal_coverage >= 0.80:
            return 0.95
        elif signal_coverage >= 0.60:
            return 0.85
        elif signal_coverage >= 0.40:
            return 0.72
        else:
            return 0.60
    
    def estimate_loss_ratio(self, composite_score: float, 
                           loss_history_mod: float) -> float:
        """Estimate expected loss ratio"""
        # Base loss ratio by composite score
        if composite_score >= 750:
            base_lr = 0.45
        elif composite_score >= 650:
            base_lr = 0.55
        elif composite_score >= 500:
            base_lr = 0.68
        else:
            base_lr = 0.82
        
        # Adjust for loss history
        adjusted_lr = base_lr * loss_history_mod
        
        return min(adjusted_lr, 0.95)  # Cap at 95%
    
    def generate_recommendation(self, composite_score: float, 
                                confidence: float,
                                expected_lr: float) -> Tuple[str, str]:
        """Generate underwriting recommendation and reasoning"""
        if composite_score >= 750 and confidence >= 0.85:
            rec = "Auto-Approve - Preferred Pricing"
            reason = f"Exceptional digital maturity (score: {composite_score:.0f}). Strong signals across all categories indicate robust operational discipline and risk management. Expected LR: {expected_lr:.1%}."
        elif composite_score >= 650 and confidence >= 0.80:
            rec = "Auto-Approve - Standard Pricing"
            reason = f"Good digital maturity (score: {composite_score:.0f}). Signals indicate adequate operational controls and transparency. Expected LR: {expected_lr:.1%}."
        elif composite_score >= 500 and confidence >= 0.70:
            rec = "Manual Review - Elevated Risk"
            reason = f"Moderate digital maturity (score: {composite_score:.0f}). Some concerning signals require underwriter review. Expected LR: {expected_lr:.1%}."
        elif confidence < 0.70:
            rec = "Manual Review - Insufficient Data"
            reason = f"Low signal coverage (confidence: {confidence:.0%}). Insufficient digital footprint for automated decisioning. Requires traditional underwriting."
        else:
            rec = "Decline - High Risk"
            reason = f"Poor digital maturity (score: {composite_score:.0f}). Multiple risk indicators suggest inadequate operational controls. Expected LR: {expected_lr:.1%}."
        
        return rec, reason
    
    def calculate_exposure_base(self, company: CompanyProfile) -> float:
        """Calculate exposure base for premium calculation"""
        if self.segment == EnergySegment.UPSTREAM:
            # Use revenue as proxy for upstream
            return company.annual_revenue / 1_000_000  # Per million
        elif self.segment == EnergySegment.MIDSTREAM:
            # Use pipeline miles or revenue
            if company.pipeline_miles:
                return company.pipeline_miles * 100  # $100k per mile equivalent
            return company.annual_revenue / 1_000_000
        else:  # DOWNSTREAM
            # Use refining capacity or revenue
            if company.refining_capacity:
                return company.refining_capacity * 50  # $50k per barrel/day
            return company.annual_revenue / 1_000_000
    
    def price(self, company: CompanyProfile) -> PricingResult:
        """
        Generate complete pricing for a company
        """
        # Get base rate
        rate_key = (self.segment.value, self.coverage.value)
        base_rate = self.base_rates.get(rate_key, 1000.0)
        
        # Calculate modifiers
        dsi_mod, composite = self.calculate_dsi_modifier(company.signals)
        size_mod = self.calculate_size_modifier(company)
        terr_mod = self.calculate_territory_modifier(company.country)
        loss_mod = company.loss_history_mod
        
        # Calculate technical rate
        tech_rate = base_rate * dsi_mod * size_mod * terr_mod * loss_mod
        
        # Calculate exposure and premium
        exposure = self.calculate_exposure_base(company)
        premium = tech_rate * exposure
        
        # Risk assessment
        risk_tier = self.determine_risk_tier(composite)
        confidence = self.calculate_confidence(company.signals)
        expected_lr = self.estimate_loss_ratio(composite, loss_mod)
        
        # Generate recommendation
        recommendation, reasoning = self.generate_recommendation(
            composite, confidence, expected_lr
        )
        
        return PricingResult(
            company_name=company.company_name,
            segment=self.segment.value,
            coverage=self.coverage.value,
            base_rate=base_rate,
            dsi_modifier=dsi_mod,
            loss_history_modifier=loss_mod,
            size_modifier=size_mod,
            territory_modifier=terr_mod,
            technical_rate=tech_rate,
            exposure_base=exposure,
            annual_premium=premium,
            composite_score=composite,
            risk_tier=risk_tier,
            confidence_level=confidence,
            expected_loss_ratio=expected_lr,
            recommendation=recommendation,
            reasoning=reasoning
        )


class UpstreamPricingModel(DSIEnergyPricingModel):
    """Specialized pricing model for upstream (E&P) operations"""
    
    def __init__(self, coverage: CoverageType):
        super().__init__(EnergySegment.UPSTREAM, coverage)
        # Adjust weights for upstream specifics
        self.weights["upstream"]["network"] = 0.35  # Network critical for E&P
        self.weights["upstream"]["behavioral"] = 0.30  # Safety culture paramount


class MidstreamPricingModel(DSIEnergyPricingModel):
    """Specialized pricing model for midstream (transportation/storage) operations"""
    
    def __init__(self, coverage: CoverageType):
        super().__init__(EnergySegment.MIDSTREAM, coverage)
        # Adjust weights for midstream specifics
        self.weights["midstream"]["infrastructure"] = 0.30  # Infrastructure critical
        self.weights["midstream"]["behavioral"] = 0.30  # Operational consistency key


class DownstreamPricingModel(DSIEnergyPricingModel):
    """Specialized pricing model for downstream (refining/distribution) operations"""
    
    def __init__(self, coverage: CoverageType):
        super().__init__(EnergySegment.DOWNSTREAM, coverage)
        # Adjust weights for downstream specifics
        self.weights["downstream"]["content"] = 0.32  # Transparency critical
        self.weights["downstream"]["behavioral"] = 0.28  # Compliance focus


def create_pricing_models(segment: EnergySegment) -> Dict[str, DSIEnergyPricingModel]:
    """Factory function to create all pricing models for a segment"""
    if segment == EnergySegment.UPSTREAM:
        return {
            "OEE": UpstreamPricingModel(CoverageType.OPERATORS_EXTRA_EXPENSE),
            "COW": UpstreamPricingModel(CoverageType.CONTROL_OF_WELL),
            "POLL": UpstreamPricingModel(CoverageType.POLLUTION_LIABILITY),
            "PD": UpstreamPricingModel(CoverageType.PROPERTY_DAMAGE),
            "BI": UpstreamPricingModel(CoverageType.BUSINESS_INTERRUPTION),
            "GL": UpstreamPricingModel(CoverageType.GENERAL_LIABILITY),
        }
    elif segment == EnergySegment.MIDSTREAM:
        return {
            "OEE": MidstreamPricingModel(CoverageType.OPERATORS_EXTRA_EXPENSE),
            "POLL": MidstreamPricingModel(CoverageType.POLLUTION_LIABILITY),
            "PD": MidstreamPricingModel(CoverageType.PROPERTY_DAMAGE),
            "BI": MidstreamPricingModel(CoverageType.BUSINESS_INTERRUPTION),
            "GL": MidstreamPricingModel(CoverageType.GENERAL_LIABILITY),
        }
    else:  # DOWNSTREAM
        return {
            "OEE": DownstreamPricingModel(CoverageType.OPERATORS_EXTRA_EXPENSE),
            "POLL": DownstreamPricingModel(CoverageType.POLLUTION_LIABILITY),
            "PD": DownstreamPricingModel(CoverageType.PROPERTY_DAMAGE),
            "BI": DownstreamPricingModel(CoverageType.BUSINESS_INTERRUPTION),
            "GL": DownstreamPricingModel(CoverageType.GENERAL_LIABILITY),
        }


# Example usage
if __name__ == "__main__":
    # Create example company with strong digital signals (like Petrobras)
    petrobras_signals = DigitalSignals(
        ssl_score=95, security_headers=90, domain_age=95,
        tech_stack_modernity=88, uptime_reliability=92, mobile_optimization=90,
        update_frequency=95, transparency_score=92, governance_disclosure=88,
        multilingual_presence=85, certification_visibility=90, incident_response=87,
        backlink_quality=95, domain_authority=92, industry_citations=90,
        partnership_quality=88, social_engagement=85, supplier_diversity=87,
        digital_transformation=92, innovation_signals=88, operational_consistency=90,
        compliance_history=85, ir_sophistication=93, sustainability_commitment=87
    )
    
    petrobras = CompanyProfile(
        company_name="Petróleo Brasileiro S.A.",
        segment=EnergySegment.UPSTREAM,
        country="Brazil",
        annual_revenue=102_000_000_000,  # $102B
        employees=45000,
        years_operating=71,
        public_traded=True,
        state_owned=True,
        loss_history_mod=0.92,
        claims_frequency=1.2,
        largest_loss=45_000_000,
        production_volume=2_500_000,  # BOE/day
        signals=petrobras_signals
    )
    
    # Price all upstream coverages
    models = create_pricing_models(EnergySegment.UPSTREAM)
    
    print("=" * 80)
    print(f"DSI PRICING ANALYSIS: {petrobras.company_name}")
    print("=" * 80)
    print(f"Segment: {petrobras.segment.value.upper()}")
    print(f"Composite DSI Score: {petrobras.signals.get_composite_score():.0f}/1000")
    print()
    
    for cov_name, model in models.items():
        result = model.price(petrobras)
        print(f"\n{result.coverage} Coverage:")
        print(f"  Base Rate: ${result.base_rate:,.2f} per $1M")
        print(f"  DSI Modifier: {result.dsi_modifier:.3f}x")
        print(f"  Technical Rate: ${result.technical_rate:,.2f} per $1M")
        print(f"  Exposure Base: ${result.exposure_base:,.0f}M")
        print(f"  Annual Premium: ${result.annual_premium:,.0f}")
        print(f"  Risk Tier: {result.risk_tier}")
        print(f"  Confidence: {result.confidence_level:.0%}")
        print(f"  Expected LR: {result.expected_loss_ratio:.1%}")
        print(f"  Recommendation: {result.recommendation}")
        print(f"  Reasoning: {result.reasoning}")
