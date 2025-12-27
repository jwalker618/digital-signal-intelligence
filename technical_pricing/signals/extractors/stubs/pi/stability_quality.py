"""
PI Extractors - Firm Stability & Practice Quality

Stub extractors for Professional Indemnity coverage signals.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ...base import StubExtractor


# =============================================================================
# FIRM STABILITY EXTRACTORS
# =============================================================================

class YearsInPracticeExtractor(StubExtractor):
    """Extract firm establishment and longevity."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        years = random.choices(
            [2, 5, 10, 20, 35, 50],
            weights=[0.15, 0.2, 0.25, 0.2, 0.12, 0.08]
        )[0] + random.randint(-1, 3)
        
        return {
            "entity_id": entity_id,
            "years_established": max(1, years),
            "founding_date": (datetime.utcnow() - timedelta(days=years*365)).year,
            "continuous_operation": random.random() > 0.05,
            "predecessor_firms": random.randint(0, 2),
            "name_changes": random.randint(0, 3),
            "data_source": "business_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PartnerStabilityExtractor(StubExtractor):
    """Extract partner/principal stability indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        partner_count = random.randint(1, 50)
        departures = random.randint(0, max(1, partner_count // 5))
        
        return {
            "entity_id": entity_id,
            "partner_count": partner_count,
            "departures_3yr": departures,
            "turnover_rate": round(departures / max(1, partner_count) * 100, 1),
            "avg_partner_tenure_years": round(random.uniform(3, 20), 1),
            "founding_partners_remaining": random.random() > 0.3,
            "recent_lateral_hires": random.randint(0, 5),
            "equity_partner_pct": round(random.uniform(30, 80), 1),
            "data_source": "linkedin_firm_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class StaffRetentionExtractor(StubExtractor):
    """Extract associate/staff retention signals."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        staff_count = random.randint(2, 200)
        
        return {
            "entity_id": entity_id,
            "total_staff": staff_count,
            "professional_staff": random.randint(1, staff_count),
            "avg_tenure_years": round(random.uniform(1.5, 8), 1),
            "turnover_rate_pct": round(random.uniform(8, 35), 1),
            "glassdoor_rating": round(random.uniform(2.5, 4.8), 1),
            "reviews_count": random.randint(5, 200),
            "hiring_trend": random.choice(["growing", "stable", "contracting"]),
            "data_source": "linkedin_glassdoor",
            "extracted_at": datetime.utcnow().isoformat()
        }


class OfficeStabilityExtractor(StubExtractor):
    """Extract office location stability."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        offices = random.randint(1, 15)
        
        return {
            "entity_id": entity_id,
            "office_count": offices,
            "primary_office_years": random.randint(2, 30),
            "office_changes_5yr": random.randint(0, 3),
            "expansions_3yr": random.randint(0, 2),
            "closures_3yr": random.randint(0, 2),
            "virtual_only": random.random() < 0.1,
            "data_source": "business_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PIFinancialStabilityExtractor(StubExtractor):
    """Extract financial health indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "credit_score_proxy": random.choice(["excellent", "good", "fair", "poor"]),
            "liens_judgments": random.randint(0, 3),
            "tax_liens": random.random() < 0.05,
            "bankruptcy_history": random.random() < 0.03,
            "payment_history": random.choice(["excellent", "good", "fair", "poor"]),
            "collections_actions": random.randint(0, 2),
            "revenue_trend": random.choice(["growing", "stable", "declining"]),
            "data_source": "credit_business_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class SuccessionPlanningExtractor(StubExtractor):
    """Extract observable succession planning indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "managing_partner_age_proxy": random.choice(["under_50", "50_60", "60_65", "over_65"]),
            "visible_succession_plan": random.random() > 0.6,
            "next_gen_partners": random.randint(0, 10),
            "partnership_track_visible": random.random() > 0.5,
            "recent_promotions": random.randint(0, 5),
            "founding_partner_active": random.random() > 0.4,
            "data_source": "firm_website_linkedin",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# PRACTICE QUALITY EXTRACTORS
# =============================================================================

class OutcomePatternsExtractor(StubExtractor):
    """Extract matter outcome patterns."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "case_win_rate": round(random.uniform(50, 90), 1),
            "settlement_rate": round(random.uniform(40, 80), 1),
            "transaction_completion_rate": round(random.uniform(85, 99), 1),
            "on_time_delivery": round(random.uniform(75, 98), 1),
            "notable_wins": random.randint(0, 20),
            "published_decisions": random.randint(0, 15),
            "data_source": "court_records_dockets",
            "extracted_at": datetime.utcnow().isoformat()
        }


class ClientReviewsExtractor(StubExtractor):
    """Extract client ratings on professional platforms."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        rating = round(random.uniform(3.0, 5.0), 1)
        
        return {
            "entity_id": entity_id,
            "average_rating": rating,
            "review_count": random.randint(5, 200),
            "five_star_pct": round(random.uniform(40, 80), 1),
            "one_star_pct": round(random.uniform(2, 15), 1),
            "response_rate": round(random.uniform(20, 80), 1),
            "recommendation_rate": round(random.uniform(60, 95), 1),
            "platforms_present": random.randint(2, 6),
            "data_source": "avvo_google_yelp",
            "extracted_at": datetime.utcnow().isoformat()
        }


class WorkQualityExtractor(StubExtractor):
    """Extract observable work quality indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "sanctions_for_work_quality": random.randint(0, 2),
            "court_admonishments": random.randint(0, 3),
            "quality_awards": random.randint(0, 5),
            "pro_bono_recognition": random.random() > 0.4,
            "benchmark_matters": random.randint(0, 10),
            "expert_witness_qualifications": random.randint(0, 5),
            "data_source": "court_records_awards",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FeeDisputeExtractor(StubExtractor):
    """Extract fee dispute history."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_disputes = random.random() < 0.15
        
        return {
            "entity_id": entity_id,
            "has_fee_disputes": has_disputes,
            "arbitration_filings_5yr": random.randint(0, 3) if has_disputes else 0,
            "fee_suits_filed": random.randint(0, 2) if has_disputes else 0,
            "fee_suits_against": random.randint(0, 2) if has_disputes else 0,
            "collection_actions": random.randint(0, 5) if has_disputes else 0,
            "dispute_rate_proxy": "low" if not has_disputes else random.choice(["moderate", "high"]),
            "data_source": "court_arbitration_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class ComplaintHistoryExtractor(StubExtractor):
    """Extract complaints to professional bodies."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - important
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_complaints = random.random() < 0.2
        
        return {
            "entity_id": entity_id,
            "has_complaint_history": has_complaints,
            "complaints_filed_5yr": random.randint(1, 5) if has_complaints else 0,
            "complaints_dismissed": random.randint(0, 3) if has_complaints else 0,
            "complaints_substantiated": random.randint(0, 2) if has_complaints else 0,
            "pending_complaints": random.randint(0, 1) if has_complaints else 0,
            "complaint_types": random.sample(["communication", "competence", "fees", "ethics"], 
                                            k=random.randint(1, 3)) if has_complaints else [],
            "data_source": "bar_board_complaints",
            "extracted_at": datetime.utcnow().isoformat()
        }
