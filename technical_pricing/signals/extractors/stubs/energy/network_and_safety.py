"""
Energy Stub Extractors - Network Authority & Safety Performance

NETWORK AUTHORITY signals:
- partner_quality: JV partner quality
- contractor_quality: Drilling/service contractor relationships
- banking_relationship: Banking/financing relationships
- insurance_history: Insurance market reputation
- industry_association: API, IOGP membership
- regulator_relationship: Regulatory relationship quality
- customer_quality: Offtake/customer quality

SAFETY PERFORMANCE signals:
- osha_trir: OSHA Total Recordable Incident Rate
- osha_violations: Serious/willful OSHA violations
- bsee_incident: BSEE offshore incidents
- process_safety: Tier 1/2 process safety events
- fatality: Work-related fatality history
- major_incident: Explosions, blowouts, major spills
- near_miss: Near-miss reporting culture
"""

from typing import Any, Dict, List, Optional
import random

from ...base import StubExtractor, utcnow


# =============================================================================
# NETWORK AUTHORITY EXTRACTORS
# =============================================================================

class EnergyPartnerQualityExtractor(StubExtractor):
    """STUB: Simulates JV partner quality assessment."""
    SOURCE_NAME = "jv_partner_analysis"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    SUPERMAJORS = ["ExxonMobil", "Shell", "BP", "Chevron", "TotalEnergies"]
    MAJORS = ["ConocoPhillips", "EOG", "Occidental", "Devon", "Pioneer"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_partners = self._random_bool(0.7)
        if has_partners:
            partner_count = self._random_int(1, 5)
            tier1_count = self._random_int(0, min(2, partner_count))
        else:
            partner_count = 0
            tier1_count = 0
            
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_jv_partners": has_partners,
                "partner_count": partner_count,
                "tier1_partner_count": tier1_count,
                "supermajor_partner": self._random_bool(0.2) if has_partners else False,
                "average_partner_rating": self._random_float(50, 95) if has_partners else None,
                "partner_quality_score": self._random_float(40, 95) if has_partners else 40,
            }
        }
        return self._create_success_result(data)


class ContractorQualityExtractor(StubExtractor):
    """STUB: Simulates drilling/service contractor quality."""
    SOURCE_NAME = "contractor_analysis"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    TIER1_CONTRACTORS = ["Schlumberger", "Halliburton", "Baker Hughes", "Transocean", "Noble"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        tier1_pct = self._random_float(20, 90)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "primary_contractors": self._random_sample(self.TIER1_CONTRACTORS, self._random_int(1, 3)),
                "tier1_contractor_pct": round(tier1_pct, 1),
                "contractor_safety_record": self._random_choice(["EXCELLENT", "GOOD", "AVERAGE", "BELOW_AVERAGE"]),
                "long_term_contracts": self._random_bool(0.6),
                "contractor_quality_score": tier1_pct * 0.9 + self._random_float(0, 15),
            }
        }
        return self._create_success_result(data)


class EnergyBankingRelationshipExtractor(StubExtractor):
    """STUB: Simulates banking/financing relationship quality."""
    SOURCE_NAME = "energy_banking"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_rbf = self._random_bool(0.6)  # Reserve-based lending
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_reserve_based_facility": has_rbf,
                "facility_size": self._random_int(50_000_000, 2_000_000_000) if has_rbf else 0,
                "lead_bank_tier": self._random_choice([1, 2, 3], weights=[0.3, 0.4, 0.3]),
                "syndicate_size": self._random_int(3, 15) if has_rbf else 0,
                "covenant_compliant": self._random_bool(0.9) if has_rbf else None,
                "banking_relationship_score": self._random_float(40, 90),
            }
        }
        return self._create_success_result(data)


class InsuranceHistoryExtractor(StubExtractor):
    """STUB: Simulates insurance market reputation."""
    SOURCE_NAME = "insurance_history"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        years_insured = self._random_int(1, 30)
        claims_count = self._random_int(0, 10)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "years_continuously_insured": years_insured,
                "claims_count_5yr": claims_count,
                "large_claims": self._random_int(0, 2),
                "market_reputation": self._random_choice(["PREFERRED", "STANDARD", "CHALLENGED"]),
                "coverage_stability": self._random_bool(0.85),
                "insurance_history_score": max(20, 100 - claims_count * 8),
            }
        }
        return self._create_success_result(data)


class RegulatorRelationshipExtractor(StubExtractor):
    """STUB: Simulates regulatory relationship quality."""
    SOURCE_NAME = "regulator_relationship"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        enforcement_actions = self._random_int(0, 5)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "enforcement_actions_5yr": enforcement_actions,
                "voluntary_compliance_programs": self._random_bool(0.4),
                "regulatory_engagement_level": self._random_choice(["HIGH", "MODERATE", "LOW"]),
                "permit_approval_rate": self._random_float(70, 100),
                "regulator_relationship_score": max(30, 100 - enforcement_actions * 15),
            }
        }
        return self._create_success_result(data)


class OfftakeQualityExtractor(StubExtractor):
    """STUB: Simulates offtake/customer quality."""
    SOURCE_NAME = "offtake_quality"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_long_term_contracts": self._random_bool(0.6),
                "contract_coverage_pct": self._random_float(20, 90),
                "investment_grade_customers_pct": self._random_float(30, 90),
                "customer_concentration": self._random_choice(["LOW", "MODERATE", "HIGH"]),
                "offtake_quality_score": self._random_float(45, 90),
            }
        }
        return self._create_success_result(data)


# =============================================================================
# SAFETY PERFORMANCE EXTRACTORS
# =============================================================================

class OSHATRIRExtractor(StubExtractor):
    """STUB: Simulates OSHA TRIR lookup."""
    SOURCE_NAME = "osha_trir"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        trir = self._random_float(0.2, 4.0)
        industry_benchmark = 1.5
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "trir": round(trir, 2),
                "industry_benchmark": industry_benchmark,
                "vs_benchmark": round((trir / industry_benchmark) * 100, 1),
                "trir_trend": self._random_choice(["IMPROVING", "STABLE", "WORSENING"]),
                "dart_rate": round(trir * self._random_float(0.4, 0.7), 2),
                "trir_score": max(0, 100 - (trir / industry_benchmark) * 50),
            }
        }
        return self._create_success_result(data)


class OSHAViolationsExtractor(StubExtractor):
    """STUB: Simulates OSHA violations lookup."""
    SOURCE_NAME = "osha_violations"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        serious = self._random_int(0, 8)
        willful = self._random_int(0, 2)
        repeat = self._random_int(0, 3)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "serious_violations_5yr": serious,
                "willful_violations_5yr": willful,
                "repeat_violations_5yr": repeat,
                "other_violations_5yr": self._random_int(0, 15),
                "total_penalties": self._random_int(0, 500_000) if serious + willful > 0 else 0,
                "osha_violations_score": max(0, 100 - serious * 8 - willful * 25 - repeat * 10),
            }
        }
        return self._create_success_result(data)


class BSEEIncidentExtractor(StubExtractor):
    """STUB: Simulates BSEE offshore incidents lookup."""
    SOURCE_NAME = "bsee_incidents"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_offshore = self._random_bool(0.3)
        
        if has_offshore:
            incidents = self._random_int(0, 5)
            incs = self._random_int(0, 3)
        else:
            incidents = 0
            incs = 0
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_offshore_operations": has_offshore,
                "panel_incidents_5yr": incidents,
                "incs_5yr": incs,
                "loss_of_well_control": self._random_bool(0.05) if has_offshore else False,
                "bsee_score": 100 if not has_offshore else max(20, 100 - incidents * 12 - incs * 8),
            }
        }
        return self._create_success_result(data)


class ProcessSafetyExtractor(StubExtractor):
    """STUB: Simulates process safety events lookup."""
    SOURCE_NAME = "process_safety"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        tier1 = self._random_int(0, 3)
        tier2 = self._random_int(0, 8)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "tier1_events_3yr": tier1,
                "tier2_events_3yr": tier2,
                "tier1_rate": round(tier1 / 3, 2),
                "api_reporting": self._random_bool(0.7),
                "pse_trend": self._random_choice(["IMPROVING", "STABLE", "WORSENING"]),
                "process_safety_score": max(0, 100 - tier1 * 25 - tier2 * 5),
            }
        }
        return self._create_success_result(data)


class FatalityHistoryExtractor(StubExtractor):
    """STUB: Simulates fatality history lookup."""
    SOURCE_NAME = "fatality_history"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        fatalities = self._random_choice([0, 0, 0, 0, 0, 1, 1, 2], weights=[0.6, 0.1, 0.1, 0.05, 0.05, 0.05, 0.03, 0.02])
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "fatalities_5yr": fatalities,
                "contractor_fatalities": self._random_int(0, max(0, fatalities - 1)) if fatalities > 0 else 0,
                "years_since_fatality": self._random_float(0.5, 10) if fatalities > 0 else None,
                "fatality_score": 100 if fatalities == 0 else max(20, 100 - fatalities * 35),
            }
        }
        return self._create_success_result(data)


class MajorIncidentExtractor(StubExtractor):
    """STUB: Simulates major incident history lookup."""
    SOURCE_NAME = "major_incidents"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_major = self._random_bool(0.15)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "major_incidents_10yr": self._random_int(1, 3) if has_major else 0,
                "explosion": self._random_bool(0.3) if has_major else False,
                "blowout": self._random_bool(0.2) if has_major else False,
                "major_spill": self._random_bool(0.4) if has_major else False,
                "years_since_major": self._random_float(1, 10) if has_major else None,
                "major_incident_score": 40 if has_major else 100,
            }
        }
        return self._create_success_result(data)


class NearMissReportingExtractor(StubExtractor):
    """STUB: Simulates near-miss reporting culture."""
    SOURCE_NAME = "near_miss_culture"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_program = self._random_bool(0.6)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_near_miss_program": has_program,
                "reporting_rate_disclosed": self._random_bool(0.3) if has_program else False,
                "near_miss_ratio": self._random_float(5, 20) if has_program else None,
                "learning_culture_indicators": self._random_bool(0.5) if has_program else False,
                "near_miss_score": 75 if has_program else 40,
            }
        }
        return self._create_success_result(data)
