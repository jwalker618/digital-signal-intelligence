"""
PI Extractors - Network Authority & Regulatory Standing

Stub extractors for Professional Indemnity coverage signals.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ...base import StubExtractor


# =============================================================================
# NETWORK AUTHORITY EXTRACTORS
# =============================================================================

class PeerRankingExtractor(StubExtractor):
    """Extract peer recognition and rankings data."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        rankings = ["Chambers", "Legal 500", "Best Lawyers", "Super Lawyers", 
                   "Martindale-Hubbell", "AM Best", "Engineering News-Record"]
        
        num_rankings = random.choices([0, 1, 2, 3, 4], weights=[0.3, 0.25, 0.2, 0.15, 0.1])[0]
        
        return {
            "entity_id": entity_id,
            "rankings_count": num_rankings,
            "rankings": random.sample(rankings, k=min(num_rankings, len(rankings))),
            "top_tier_rankings": random.randint(0, num_rankings),
            "individual_recognitions": random.randint(0, 10),
            "years_ranked": random.randint(0, 15) if num_rankings > 0 else 0,
            "data_source": "professional_directories",
            "extracted_at": datetime.utcnow().isoformat()
        }


class ClientQualityExtractor(StubExtractor):
    """Extract client quality indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "fortune_500_clients": random.random() > 0.7,
            "public_company_clients": random.random() > 0.5,
            "government_clients": random.random() > 0.4,
            "institutional_clients_pct": round(random.uniform(10, 70), 1),
            "client_concentration_top5": round(random.uniform(20, 80), 1),
            "notable_engagements": random.randint(0, 10),
            "data_source": "client_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class ReferralQualityExtractor(StubExtractor):
    """Extract referral network quality."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "referral_network_size": random.randint(5, 100),
            "top_tier_referrers": random.randint(0, 15),
            "reciprocal_referrals": random.random() > 0.5,
            "cross_practice_referrals": random.random() > 0.4,
            "referral_quality_score": round(random.uniform(40, 95), 1),
            "data_source": "network_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class AssociationLeadershipExtractor(StubExtractor):
    """Extract professional association leadership roles."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        associations = ["ABA", "AICPA", "AIA", "ASCE", "State Bar", "Local Bar", 
                       "Specialty Section", "Industry Group"]
        
        memberships = random.randint(1, 5)
        leadership = random.randint(0, min(memberships, 3))
        
        return {
            "entity_id": entity_id,
            "association_memberships": memberships,
            "leadership_positions": leadership,
            "committee_chairs": random.randint(0, leadership),
            "board_positions": random.randint(0, min(leadership, 2)),
            "years_active": random.randint(1, 20),
            "associations": random.sample(associations, k=min(memberships, len(associations))),
            "data_source": "association_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class ThoughtLeadershipExtractor(StubExtractor):
    """Extract thought leadership indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "publications_count": random.randint(0, 50),
            "speaking_engagements_yr": random.randint(0, 20),
            "cle_presentations": random.randint(0, 15),
            "media_mentions_yr": random.randint(0, 30),
            "podcast_appearances": random.randint(0, 10),
            "quoted_as_expert": random.random() > 0.4,
            "data_source": "media_publications",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PanelMembershipExtractor(StubExtractor):
    """Extract insurance defense panel and approved list memberships."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        panels = ["Major Insurer Panel", "Bank Approved", "Title Company Panel",
                 "Corporate Preferred", "Government Contractor"]
        
        num_panels = random.choices([0, 1, 2, 3], weights=[0.4, 0.3, 0.2, 0.1])[0]
        
        return {
            "entity_id": entity_id,
            "panel_memberships": num_panels,
            "panels": random.sample(panels, k=min(num_panels, len(panels))),
            "years_on_panels": random.randint(0, 15) if num_panels > 0 else 0,
            "preferred_counsel_status": random.random() > 0.7 if num_panels > 0 else False,
            "data_source": "panel_directories",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# REGULATORY STANDING EXTRACTORS
# =============================================================================

class LicenseStatusExtractor(StubExtractor):
    """Extract professional license status."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        status = random.choices(
            ["active", "active", "active", "inactive", "suspended", "probation"],
            weights=[0.85, 0.05, 0.03, 0.03, 0.02, 0.02]
        )[0]
        
        return {
            "entity_id": entity_id,
            "license_status": status,
            "all_licenses_active": status == "active",
            "license_count": random.randint(1, 5),
            "jurisdictions": random.randint(1, 10),
            "years_licensed": random.randint(1, 40),
            "license_restrictions": random.random() < 0.05,
            "pending_renewal": random.random() < 0.1,
            "data_source": "state_licensing_boards",
            "extracted_at": datetime.utcnow().isoformat()
        }


class DisciplinaryHistoryExtractor(StubExtractor):
    """Extract disciplinary history from regulatory bodies."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_discipline = random.random() < 0.12
        
        return {
            "entity_id": entity_id,
            "has_disciplinary_history": has_discipline,
            "sanctions_count": random.randint(1, 3) if has_discipline else 0,
            "public_reprimands": random.randint(0, 2) if has_discipline else 0,
            "private_reprimands": random.randint(0, 2) if has_discipline else 0,
            "suspensions": random.randint(0, 1) if has_discipline else 0,
            "probation_periods": random.randint(0, 1) if has_discipline else 0,
            "most_recent_action_years": random.randint(1, 10) if has_discipline else None,
            "severity": random.choice(["minor", "moderate", "serious"]) if has_discipline else None,
            "data_source": "disciplinary_databases",
            "extracted_at": datetime.utcnow().isoformat()
        }


class MalpracticeRecordExtractor(StubExtractor):
    """Extract public malpractice record."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_record = random.random() < 0.15
        
        return {
            "entity_id": entity_id,
            "has_malpractice_record": has_record,
            "public_judgments": random.randint(0, 2) if has_record else 0,
            "disclosed_settlements": random.randint(0, 3) if has_record else 0,
            "total_payout_disclosed": random.randint(50000, 500000) if has_record else 0,
            "most_recent_years": random.randint(1, 10) if has_record else None,
            "data_source": "court_records_npdb",
            "extracted_at": datetime.utcnow().isoformat()
        }


class CEComplianceExtractor(StubExtractor):
    """Extract continuing education compliance."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        compliant = random.random() > 0.08
        
        return {
            "entity_id": entity_id,
            "ce_compliant": compliant,
            "ce_credits_current": random.randint(20, 50) if compliant else random.randint(5, 20),
            "ce_credits_required": random.randint(20, 40),
            "ethics_credits_current": random.randint(2, 10),
            "specialty_credits": random.randint(0, 15),
            "compliance_streak_years": random.randint(1, 15) if compliant else 0,
            "data_source": "licensing_board_ce",
            "extracted_at": datetime.utcnow().isoformat()
        }


class SpecialtyCertificationExtractor(StubExtractor):
    """Extract specialty certifications and designations."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        certifications = ["Board Certified", "CPA", "PE", "AIA", "CFP", "CFA", 
                         "LEED", "PMP", "CISSP", "Specialty Bar"]
        
        num_certs = random.choices([0, 1, 2, 3], weights=[0.3, 0.35, 0.25, 0.1])[0]
        
        return {
            "entity_id": entity_id,
            "certification_count": num_certs,
            "certifications": random.sample(certifications, k=min(num_certs, len(certifications))),
            "board_certified": random.random() > 0.7 if num_certs > 0 else False,
            "specialty_designations": random.randint(0, num_certs),
            "certifications_current": num_certs > 0 and random.random() > 0.1,
            "data_source": "certification_bodies",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PeerReviewExtractor(StubExtractor):
    """Extract AICPA peer review rating (accounting firms)."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        rating = random.choices(
            ["pass", "pass_with_deficiencies", "fail", "not_applicable"],
            weights=[0.7, 0.15, 0.05, 0.1]
        )[0]
        
        return {
            "entity_id": entity_id,
            "peer_review_rating": rating,
            "review_date": (datetime.utcnow() - timedelta(days=random.randint(30, 730))).isoformat(),
            "deficiencies_noted": random.randint(0, 3) if rating == "pass_with_deficiencies" else 0,
            "corrective_actions_required": rating == "pass_with_deficiencies" or rating == "fail",
            "enrolled_in_program": rating != "not_applicable",
            "data_source": "aicpa_peer_review",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PCAOBStandingExtractor(StubExtractor):
    """Extract PCAOB/SEC registration and inspection results."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        is_registered = random.random() > 0.7  # Many firms not PCAOB registered
        
        return {
            "entity_id": entity_id,
            "pcaob_registered": is_registered,
            "sec_registered": random.random() > 0.8 if is_registered else False,
            "inspection_deficiencies": random.randint(0, 5) if is_registered else 0,
            "last_inspection_date": (datetime.utcnow() - timedelta(days=random.randint(180, 1095))).isoformat() if is_registered else None,
            "enforcement_actions": random.randint(0, 1) if is_registered else 0,
            "quality_control_criticisms": random.randint(0, 3) if is_registered else 0,
            "data_source": "pcaob_sec_records",
            "extracted_at": datetime.utcnow().isoformat()
        }
