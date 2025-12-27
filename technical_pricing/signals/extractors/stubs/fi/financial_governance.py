"""
FI Extractors - Financial Condition & Governance

Stub extractors for financial institution signals.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict

from ...base import StubExtractor


# =============================================================================
# FINANCIAL CONDITION EXTRACTORS
# =============================================================================

class CapitalRatioExtractor(StubExtractor):
    """Extract capital adequacy ratios from call reports."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        # Well-capitalized minimums: CET1 6.5%, Tier1 8%, Total 10%
        base_cet1 = random.uniform(7, 18)
        
        return {
            "entity_id": entity_id,
            "cet1_ratio": round(base_cet1, 2),
            "tier1_ratio": round(base_cet1 + random.uniform(0.5, 2), 2),
            "total_capital_ratio": round(base_cet1 + random.uniform(1.5, 4), 2),
            "leverage_ratio": round(random.uniform(6, 12), 2),
            "capital_conservation_buffer": round(random.uniform(2.5, 4), 2),
            "capital_category": random.choices(
                ["well_capitalized", "adequately_capitalized", "undercapitalized", "significantly_undercapitalized"],
                weights=[0.85, 0.10, 0.04, 0.01]
            )[0],
            "stress_test_result": random.choice(["pass", "pass", "pass", "conditional_pass", "fail"]) if random.random() > 0.7 else None,
            "prompt_corrective_action": random.random() < 0.02,
            "data_source": "ffiec_call_reports",
            "extracted_at": datetime.utcnow().isoformat()
        }


class AssetQualityExtractor(StubExtractor):
    """Extract asset quality metrics."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        npl_ratio = random.uniform(0.2, 5.0)
        
        return {
            "entity_id": entity_id,
            "npl_ratio": round(npl_ratio, 2),
            "nco_ratio": round(random.uniform(0.1, 2.0), 2),
            "allowance_to_npl": round(random.uniform(80, 200), 1),
            "allowance_to_loans": round(random.uniform(0.8, 2.5), 2),
            "classified_assets_ratio": round(random.uniform(1, 10), 2),
            "texas_ratio": round(random.uniform(5, 50), 1),
            "loan_loss_provision": round(random.uniform(0.2, 1.5), 2),
            "oreo_ratio": round(random.uniform(0, 1.5), 2),
            "tdr_ratio": round(random.uniform(0.1, 2.0), 2),
            "data_source": "ffiec_call_reports",
            "extracted_at": datetime.utcnow().isoformat()
        }


class LiquidityExtractor(StubExtractor):
    """Extract liquidity position metrics."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "liquidity_coverage_ratio": round(random.uniform(100, 180), 1) if random.random() > 0.3 else None,
            "net_stable_funding_ratio": round(random.uniform(100, 150), 1) if random.random() > 0.4 else None,
            "loan_to_deposit_ratio": round(random.uniform(60, 105), 1),
            "cash_to_assets": round(random.uniform(3, 20), 2),
            "securities_to_assets": round(random.uniform(10, 35), 2),
            "wholesale_funding_ratio": round(random.uniform(5, 40), 2),
            "core_deposits_ratio": round(random.uniform(55, 90), 1),
            "uninsured_deposits_ratio": round(random.uniform(15, 60), 1),
            "borrowing_capacity_available_mm": random.randint(50, 2000),
            "contingent_liquidity_sources": random.randint(2, 6),
            "data_source": "ffiec_call_reports",
            "extracted_at": datetime.utcnow().isoformat()
        }


class EarningsExtractor(StubExtractor):
    """Extract earnings quality metrics."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        roa = random.uniform(0.3, 1.8)
        
        return {
            "entity_id": entity_id,
            "roa": round(roa, 2),
            "roe": round(roa * random.uniform(8, 14), 2),
            "net_interest_margin": round(random.uniform(2.5, 4.5), 2),
            "efficiency_ratio": round(random.uniform(45, 85), 1),
            "pre_provision_net_revenue": round(random.uniform(1.0, 3.0), 2),
            "noninterest_income_ratio": round(random.uniform(15, 45), 1),
            "earnings_volatility": random.choice(["low", "moderate", "high"]),
            "earnings_trend": random.choice(["improving", "stable", "stable", "declining"]),
            "quarters_profitable": random.randint(8, 20),
            "dividend_payout_ratio": round(random.uniform(20, 60), 1) if random.random() > 0.3 else None,
            "data_source": "ffiec_call_reports",
            "extracted_at": datetime.utcnow().isoformat()
        }


class ConcentrationExtractor(StubExtractor):
    """Extract loan portfolio concentration metrics."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "cre_concentration": round(random.uniform(50, 400), 1),  # As % of capital
            "construction_concentration": round(random.uniform(10, 150), 1),
            "largest_borrower_pct": round(random.uniform(3, 20), 2),
            "top_10_borrowers_pct": round(random.uniform(15, 50), 2),
            "single_industry_concentration": round(random.uniform(10, 40), 1),
            "geographic_concentration": random.choice(["diversified", "regional", "concentrated", "single_market"]),
            "herfindahl_index": round(random.uniform(500, 3000), 0),
            "concentration_risk_rating": random.choices([1, 2, 3, 4, 5], weights=[0.2, 0.35, 0.30, 0.10, 0.05])[0],
            "data_source": "ffiec_call_reports",
            "extracted_at": datetime.utcnow().isoformat()
        }


class InterestRateRiskExtractor(StubExtractor):
    """Extract interest rate risk sensitivity metrics."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "eve_sensitivity_up200": round(random.uniform(-25, 5), 2),  # EVE change for +200bp
            "eve_sensitivity_down100": round(random.uniform(-10, 15), 2),
            "nim_sensitivity_up200": round(random.uniform(-0.5, 0.8), 2),  # NIM change for +200bp
            "asset_liability_gap_1yr": round(random.uniform(-20, 20), 2),  # As % of assets
            "duration_gap": round(random.uniform(-2, 4), 2),
            "repricing_mismatch": random.choice(["minimal", "moderate", "significant"]),
            "rate_sensitivity_position": random.choice(["asset_sensitive", "liability_sensitive", "neutral"]),
            "hedging_activity": random.choice(["active", "moderate", "minimal", "none"]),
            "data_source": "ffiec_ubpr_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class GrowthRateExtractor(StubExtractor):
    """Extract asset and loan growth rates."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        asset_growth = random.uniform(-5, 30)
        
        return {
            "entity_id": entity_id,
            "asset_growth_1yr": round(asset_growth, 2),
            "asset_growth_3yr_cagr": round(asset_growth * random.uniform(0.5, 1.2), 2),
            "loan_growth_1yr": round(random.uniform(-3, 35), 2),
            "deposit_growth_1yr": round(random.uniform(-5, 25), 2),
            "organic_vs_acquired": random.choice(["organic", "mixed", "acquisition_driven"]),
            "growth_sustainability": random.choice(["sustainable", "moderate_concern", "high_concern"]),
            "capital_supporting_growth": random.choice(["adequate", "stretched", "insufficient"]),
            "rapid_growth_flag": asset_growth > 20,
            "data_source": "ffiec_call_reports",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# GOVERNANCE EXTRACTORS
# =============================================================================

class FIBoardIndependenceExtractor(StubExtractor):
    """Extract board independence metrics for FIs."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        board_size = random.randint(7, 15)
        independent_count = random.randint(int(board_size * 0.5), int(board_size * 0.9))
        
        return {
            "entity_id": entity_id,
            "board_size": board_size,
            "independent_directors": independent_count,
            "independence_ratio": round(independent_count / board_size, 2),
            "independent_chair": random.random() > 0.4,
            "lead_independent_director": random.random() > 0.6,
            "insider_directors": board_size - independent_count,
            "recent_independence_change": random.random() < 0.15,
            "regulatory_independence_compliant": random.random() > 0.95,
            "data_source": "sec_proxy_statements",
            "extracted_at": datetime.utcnow().isoformat()
        }


class BoardExpertiseExtractor(StubExtractor):
    """Extract board expertise and qualifications."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        board_size = random.randint(7, 15)
        
        return {
            "entity_id": entity_id,
            "banking_experience_count": random.randint(2, min(8, board_size)),
            "regulatory_experience_count": random.randint(1, 4),
            "risk_management_experience": random.randint(1, 5),
            "audit_financial_experts": random.randint(2, 5),
            "technology_experience": random.randint(0, 4),
            "legal_experience": random.randint(1, 3),
            "ceo_experience": random.randint(1, 4),
            "average_tenure_years": round(random.uniform(4, 12), 1),
            "average_age": random.randint(55, 68),
            "diversity_metrics": {
                "gender_diversity_pct": round(random.uniform(15, 45), 1),
                "ethnic_diversity_pct": round(random.uniform(10, 35), 1),
                "age_diversity": random.choice(["good", "moderate", "limited"])
            },
            "data_source": "sec_proxy_statements",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FIExecutiveStabilityExtractor(StubExtractor):
    """Extract executive team stability metrics."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        ceo_tenure = random.randint(1, 20)
        
        return {
            "entity_id": entity_id,
            "ceo_tenure_years": ceo_tenure,
            "cfo_tenure_years": random.randint(1, 15),
            "cro_tenure_years": random.randint(1, 12),
            "cco_tenure_years": random.randint(1, 10),
            "c_suite_turnover_3yr": random.randint(0, 4),
            "ceo_change_recent": ceo_tenure < 2,
            "succession_plan_disclosed": random.random() > 0.6,
            "executive_team_avg_tenure": round(random.uniform(3, 12), 1),
            "key_person_dependency": random.choice(["low", "moderate", "high"]),
            "data_source": "sec_proxy_8k_filings",
            "extracted_at": datetime.utcnow().isoformat()
        }


class RiskCommitteeExtractor(StubExtractor):
    """Extract board risk committee quality metrics."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_risk_committee = random.random() > 0.15
        
        return {
            "entity_id": entity_id,
            "has_risk_committee": has_risk_committee,
            "risk_committee_independent": has_risk_committee and random.random() > 0.3,
            "risk_committee_size": random.randint(3, 7) if has_risk_committee else 0,
            "meetings_per_year": random.randint(4, 12) if has_risk_committee else 0,
            "risk_expert_chair": has_risk_committee and random.random() > 0.5,
            "cro_reports_to_committee": has_risk_committee and random.random() > 0.7,
            "committee_charter_public": has_risk_committee and random.random() > 0.8,
            "enterprise_risk_oversight": has_risk_committee and random.random() > 0.6,
            "cyber_risk_expertise": has_risk_committee and random.random() > 0.4,
            "data_source": "sec_proxy_statements",
            "extracted_at": datetime.utcnow().isoformat()
        }


class AuditCommitteeExtractor(StubExtractor):
    """Extract audit committee quality metrics."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "audit_committee_size": random.randint(3, 6),
            "all_independent": random.random() > 0.95,
            "financial_experts": random.randint(1, 4),
            "meetings_per_year": random.randint(6, 15),
            "chair_is_expert": random.random() > 0.8,
            "auditor_oversight_quality": random.choice(["strong", "satisfactory", "needs_improvement"]),
            "internal_audit_oversight": random.choice(["strong", "satisfactory", "needs_improvement"]),
            "whistleblower_oversight": random.random() > 0.85,
            "soc_report_oversight": random.random() > 0.7,
            "data_source": "sec_proxy_statements",
            "extracted_at": datetime.utcnow().isoformat()
        }


class RelatedPartyExtractor(StubExtractor):
    """Extract related party transaction oversight quality."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_rpt = random.random() > 0.3
        
        return {
            "entity_id": entity_id,
            "related_party_transactions": has_rpt,
            "rpt_policy_exists": random.random() > 0.85,
            "rpt_board_approval_required": random.random() > 0.90,
            "insider_loans_outstanding": random.randint(0, 10) if has_rpt else 0,
            "insider_loans_to_capital": round(random.uniform(0, 15), 2) if has_rpt else 0,
            "reg_o_compliance": random.random() > 0.98,
            "affiliate_transactions": random.randint(0, 5),
            "disclosure_quality": random.choice(["comprehensive", "adequate", "limited"]),
            "data_source": "sec_proxy_10k_filings",
            "extracted_at": datetime.utcnow().isoformat()
        }
