"""
Marine Extractors - Sanctions, Environmental, Corporate Footprint, Structured Data, Categorical

Stub extractors for marine insurance signals.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict

from ...base import StubExtractor


# =============================================================================
# SANCTIONS COMPLIANCE EXTRACTORS
# =============================================================================

class SanctionsStatusExtractor(StubExtractor):
    """Extract direct sanctions status."""
    
    DEFAULT_TTL_SECONDS = 3600  # Hourly - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        is_sanctioned = random.random() < 0.02
        
        return {
            "entity_id": entity_id,
            "ofac_listed": is_sanctioned and random.random() > 0.5,
            "eu_listed": is_sanctioned and random.random() > 0.5,
            "un_listed": is_sanctioned and random.random() > 0.7,
            "uk_listed": is_sanctioned and random.random() > 0.6,
            "any_sanctions_listing": is_sanctioned,
            "sanctions_program": random.choice(["Russia", "Iran", "North Korea", "Venezuela"]) if is_sanctioned else None,
            "vessels_sanctioned": random.randint(1, 5) if is_sanctioned else 0,
            "sanctions_status_score": 0 if is_sanctioned else 100,
            "data_source": "ofac_eu_un_sanctions_lists",
            "extracted_at": datetime.utcnow().isoformat()
        }


class OwnershipTransparencyExtractor(StubExtractor):
    """Extract beneficial ownership transparency."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        transparency = random.choices(
            ["full", "partial", "limited", "opaque"],
            weights=[0.4, 0.35, 0.15, 0.10]
        )[0]
        
        return {
            "entity_id": entity_id,
            "ownership_transparency": transparency,
            "beneficial_owner_identified": transparency in ["full", "partial"],
            "corporate_layers": random.randint(1, 8),
            "offshore_jurisdictions": random.randint(0, 4),
            "pep_connection": random.random() < 0.05,
            "ownership_changes_24mo": random.randint(0, 3),
            "ownership_transparency_score": 95 if transparency == "full" else 70 if transparency == "partial" else 40 if transparency == "limited" else 20,
            "data_source": "corporate_registry_kyc",
            "extracted_at": datetime.utcnow().isoformat()
        }


class JurisdictionRiskExtractor(StubExtractor):
    """Extract high-risk jurisdiction exposure."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        high_risk_countries = ["Iran", "North Korea", "Syria", "Cuba", "Venezuela", "Russia", "Belarus"]
        
        has_exposure = random.random() < 0.08
        
        return {
            "entity_id": entity_id,
            "sanctioned_jurisdiction_calls": random.randint(1, 10) if has_exposure else 0,
            "high_risk_jurisdictions_visited": random.sample(high_risk_countries, k=random.randint(1, 3)) if has_exposure else [],
            "russian_port_calls_12mo": random.randint(0, 20) if has_exposure else random.randint(0, 2),
            "iranian_port_calls_12mo": random.randint(0, 5) if has_exposure and random.random() > 0.7 else 0,
            "jurisdiction_risk_score": random.randint(15, 45) if has_exposure else random.randint(75, 100),
            "data_source": "ais_jurisdiction_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class STSPatternExtractor(StubExtractor):
    """Extract ship-to-ship transfer patterns."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_sts = random.random() > 0.6  # Many tankers do legitimate STS
        suspicious = random.random() < 0.05
        
        return {
            "entity_id": entity_id,
            "sts_operations_12mo": random.randint(5, 50) if has_sts else 0,
            "sts_in_sanctioned_waters": random.randint(1, 10) if suspicious else 0,
            "sts_with_dark_vessels": random.randint(0, 5) if suspicious else 0,
            "sts_notification_compliance": random.random() > 0.3 if has_sts else True,
            "suspicious_sts_patterns": suspicious,
            "sts_pattern_score": random.randint(20, 50) if suspicious else random.randint(70, 100),
            "data_source": "ais_sts_monitoring",
            "extracted_at": datetime.utcnow().isoformat()
        }


class HistoricalSanctionsExtractor(StubExtractor):
    """Extract historical sanctions connections."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_history = random.random() < 0.08
        
        return {
            "entity_id": entity_id,
            "previously_sanctioned": has_history and random.random() > 0.5,
            "connection_to_sanctioned_entity": has_history and random.random() > 0.6,
            "former_owners_sanctioned": has_history and random.random() > 0.7,
            "name_changes_suspicious": has_history and random.random() > 0.8,
            "flag_hopping_pattern": random.random() < 0.03,
            "historical_sanctions_score": random.randint(40, 70) if has_history else random.randint(85, 100),
            "data_source": "historical_sanctions_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# ENVIRONMENTAL EXTRACTORS
# =============================================================================

class IMO2020ComplianceExtractor(StubExtractor):
    """Extract IMO 2020 sulphur compliance."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        compliance_method = random.choices(
            ["compliant_fuel", "scrubber", "lng", "methanol", "non_compliant"],
            weights=[0.55, 0.30, 0.08, 0.02, 0.05]
        )[0]
        
        return {
            "entity_id": entity_id,
            "imo2020_compliance_method": compliance_method,
            "scrubber_fitted_pct": round(random.uniform(0.2, 0.8), 2) if compliance_method == "scrubber" else 0,
            "compliant_fuel_only_pct": round(random.uniform(0.5, 1.0), 2) if compliance_method == "compliant_fuel" else 0,
            "compliance_violations": random.randint(0, 3) if compliance_method == "non_compliant" else 0,
            "imo2020_score": 95 if compliance_method in ["compliant_fuel", "lng", "methanol"] else 85 if compliance_method == "scrubber" else 30,
            "data_source": "imo_gisis_compliance",
            "extracted_at": datetime.utcnow().isoformat()
        }


class BWMComplianceExtractor(StubExtractor):
    """Extract ballast water management compliance."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "bwm_convention_compliant": random.random() > 0.1,
            "bwts_installed_pct": round(random.uniform(0.5, 1.0), 2),
            "bwts_installation_planned": random.random() > 0.3,
            "exchange_method_only_pct": round(random.uniform(0, 0.3), 2),
            "bwm_deficiencies_psc": random.randint(0, 2),
            "bwm_compliance_score": random.randint(70, 98),
            "data_source": "class_bwm_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class CIIRatingExtractor(StubExtractor):
    """Extract Carbon Intensity Indicator rating."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        rating = random.choices(
            ["A", "B", "C", "D", "E"],
            weights=[0.10, 0.25, 0.40, 0.18, 0.07]
        )[0]
        
        return {
            "entity_id": entity_id,
            "cii_rating": rating,
            "fleet_average_cii_rating": rating,
            "cii_improvement_trend": random.choice(["improving", "stable", "declining"]),
            "vessels_rated_d_or_e_pct": round(random.uniform(0, 0.3), 2) if rating in ["D", "E"] else round(random.uniform(0, 0.1), 2),
            "cii_corrective_action_required": rating in ["D", "E"],
            "cii_rating_score": {"A": 100, "B": 85, "C": 70, "D": 45, "E": 25}.get(rating, 70),
            "data_source": "imo_dcs_cii",
            "extracted_at": datetime.utcnow().isoformat()
        }


class EnvironmentalIncidentExtractor(StubExtractor):
    """Extract environmental incident history."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_incidents = random.random() < 0.08
        
        return {
            "entity_id": entity_id,
            "pollution_incidents_5yr": random.randint(1, 4) if has_incidents else 0,
            "oil_spills": random.randint(0, 2) if has_incidents else 0,
            "environmental_fines_usd": random.randint(10000, 500000) if has_incidents else 0,
            "cargo_release_incidents": random.randint(0, 2) if has_incidents else 0,
            "environmental_prosecution": has_incidents and random.random() > 0.7,
            "environmental_incident_score": random.randint(50, 75) if has_incidents else random.randint(85, 100),
            "data_source": "itopf_environmental_database",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# CORPORATE FOOTPRINT EXTRACTORS
# =============================================================================

class MarineWebsiteQualityExtractor(StubExtractor):
    """Extract website quality indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_website = random.random() > 0.1
        
        return {
            "entity_id": entity_id,
            "has_website": has_website,
            "website_quality": random.choice(["professional", "adequate", "basic", "poor"]) if has_website else "none",
            "ssl_certificate": has_website and random.random() > 0.2,
            "contact_information_complete": has_website and random.random() > 0.6,
            "management_team_disclosed": has_website and random.random() > 0.4,
            "website_quality_score": random.randint(60, 95) if has_website else 30,
            "data_source": "website_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FleetListDisclosureExtractor(StubExtractor):
    """Extract fleet list disclosure status."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        disclosure = random.choices(
            ["full", "partial", "minimal", "none"],
            weights=[0.35, 0.30, 0.20, 0.15]
        )[0]
        
        return {
            "entity_id": entity_id,
            "fleet_list_disclosure": disclosure,
            "vessel_names_public": disclosure in ["full", "partial"],
            "imo_numbers_disclosed": disclosure == "full",
            "technical_specs_available": disclosure == "full" and random.random() > 0.5,
            "fleet_list_score": {"full": 95, "partial": 70, "minimal": 45, "none": 20}.get(disclosure, 50),
            "data_source": "company_website_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class MarineSustainabilityExtractor(StubExtractor):
    """Extract sustainability reporting quality."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_report = random.random() > 0.4
        
        return {
            "entity_id": entity_id,
            "sustainability_report_published": has_report,
            "poseidon_principles_signatory": has_report and random.random() > 0.4,
            "sea_cargo_charter_signatory": has_report and random.random() > 0.3,
            "getting_to_zero_coalition": has_report and random.random() > 0.2,
            "carbon_disclosure": has_report and random.random() > 0.5,
            "sustainability_score": random.randint(60, 95) if has_report else random.randint(30, 50),
            "data_source": "sustainability_databases",
            "extracted_at": datetime.utcnow().isoformat()
        }


class SafetyCultureExtractor(StubExtractor):
    """Extract safety culture communication evidence."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "safety_policy_published": random.random() > 0.5,
            "safety_statistics_disclosed": random.random() > 0.3,
            "ltir_disclosed": random.random() > 0.25,
            "near_miss_reporting_mentioned": random.random() > 0.4,
            "safety_awards": random.randint(0, 3),
            "safety_culture_score": random.randint(45, 90),
            "data_source": "company_communications",
            "extracted_at": datetime.utcnow().isoformat()
        }


class CrewWelfareExtractor(StubExtractor):
    """Extract crew welfare visibility."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "crew_welfare_policy_visible": random.random() > 0.4,
            "crew_change_commitment": random.random() > 0.5,
            "neptune_declaration_signatory": random.random() > 0.15,
            "mental_health_programs": random.random() > 0.3,
            "crew_connectivity_provided": random.random() > 0.6,
            "crew_welfare_score": random.randint(45, 90),
            "data_source": "company_communications",
            "extracted_at": datetime.utcnow().isoformat()
        }


class MarineIndustryPresenceExtractor(StubExtractor):
    """Extract industry presence indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "conference_presence": random.random() > 0.4,
            "industry_publications": random.randint(0, 5),
            "speaking_engagements": random.randint(0, 3),
            "awards_received": random.randint(0, 4),
            "media_mentions_12mo": random.randint(0, 20),
            "industry_presence_score": random.randint(40, 85),
            "data_source": "industry_news_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# STRUCTURED DATA EXTRACTORS
# =============================================================================

class VettingExtractor(StubExtractor):
    """Extract RightShip and vetting scores."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        rightship_stars = random.choices([1, 2, 3, 4, 5], weights=[0.02, 0.08, 0.25, 0.40, 0.25])[0]
        
        return {
            "entity_id": entity_id,
            "rightship_stars": rightship_stars,
            "rightship_ghg_rating": random.choice(["A", "B", "C", "D", "E"]),
            "sire_inspection_count_12mo": random.randint(0, 10),
            "sire_observations_avg": round(random.uniform(5, 25), 1),
            "oil_major_approvals": random.randint(0, 6),
            "vetting_score": rightship_stars * 20,
            "data_source": "rightship_sire_databases",
            "extracted_at": datetime.utcnow().isoformat()
        }


class MarineESGRatingExtractor(StubExtractor):
    """Extract maritime ESG ratings."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "poseidon_principles_score": round(random.uniform(50, 100), 1) if random.random() > 0.5 else None,
            "sea_cargo_charter_alignment": round(random.uniform(0.8, 1.2), 2) if random.random() > 0.6 else None,
            "sustainalytics_score": random.randint(20, 50) if random.random() > 0.4 else None,
            "cdp_climate_score": random.choice(["A", "A-", "B", "B-", "C", "D"]) if random.random() > 0.5 else None,
            "esg_rating_score": random.randint(50, 90),
            "data_source": "esg_rating_providers",
            "extracted_at": datetime.utcnow().isoformat()
        }


class MarineCreditRatingExtractor(StubExtractor):
    """Extract credit rating for shipping companies."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_rating = random.random() > 0.6
        ratings = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "NR"]
        weights = [0.01, 0.05, 0.10, 0.25, 0.30, 0.20, 0.05, 0.04]
        
        return {
            "entity_id": entity_id,
            "has_credit_rating": has_rating,
            "sp_rating": random.choices(ratings, weights=weights)[0] if has_rating else "NR",
            "moodys_rating": random.choices(["Aaa", "Aa", "A", "Baa", "Ba", "B", "Caa", "NR"], weights=weights)[0] if has_rating else "NR",
            "rating_outlook": random.choice(["stable", "positive", "negative", "watch"]) if has_rating else None,
            "credit_rating_score": random.randint(50, 90) if has_rating else 40,
            "data_source": "rating_agencies",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# CATEGORICAL EXTRACTORS
# =============================================================================

class OperatorClassificationExtractor(StubExtractor):
    """Extract operator type classification."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        types = ["MAJOR_LINER", "MAJOR_TANKER", "MAJOR_BULK", "REGIONAL_OPERATOR", 
                "INDEPENDENT", "STATE_OWNED", "UNKNOWN"]
        weights = [0.05, 0.08, 0.10, 0.30, 0.35, 0.07, 0.05]
        
        return {
            "entity_id": entity_id,
            "operator_type": random.choices(types, weights=weights)[0],
            "fleet_size": random.randint(1, 200),
            "listed_company": random.random() > 0.7,
            "data_source": "clarkson_operator_database",
            "extracted_at": datetime.utcnow().isoformat()
        }


class VesselCategoryExtractor(StubExtractor):
    """Extract primary vessel category."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        categories = ["CONTAINER", "TANKER", "DRY_BULK", "LNG_LPG", "OFFSHORE", 
                     "PASSENGER", "GENERAL_CARGO", "MIXED"]
        weights = [0.15, 0.25, 0.25, 0.08, 0.10, 0.05, 0.07, 0.05]
        
        return {
            "entity_id": entity_id,
            "vessel_category": random.choices(categories, weights=weights)[0],
            "sub_category": random.choice(["crude", "product", "chemical"]) if random.random() > 0.7 else None,
            "data_source": "equasis_vessel_data",
            "extracted_at": datetime.utcnow().isoformat()
        }


class TradingPatternExtractor(StubExtractor):
    """Extract trading pattern classification."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        patterns = ["LINER_REGULAR", "SPOT_TRAMP", "INDUSTRIAL", "MIXED"]
        weights = [0.25, 0.40, 0.20, 0.15]
        
        return {
            "entity_id": entity_id,
            "trading_pattern": random.choices(patterns, weights=weights)[0],
            "time_charter_pct": round(random.uniform(0, 0.8), 2),
            "voyage_charter_pct": round(random.uniform(0.2, 1.0), 2),
            "data_source": "ais_trading_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FlagStateQualityExtractor(StubExtractor):
    """Extract flag state quality classification."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        lists = ["WHITE_LIST", "GREY_LIST", "BLACK_LIST"]
        weights = [0.55, 0.35, 0.10]
        
        return {
            "entity_id": entity_id,
            "flag_state_quality": random.choices(lists, weights=weights)[0],
            "fleet_primary_flag": random.choice(["Marshall Islands", "Panama", "Liberia", "Bahamas", "Singapore"]),
            "data_source": "paris_mou_performance",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FleetAgeBandExtractor(StubExtractor):
    """Extract fleet age band classification."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        bands = ["AGE_0_5", "AGE_5_10", "AGE_10_15", "AGE_15_20", "AGE_20_25", "AGE_25_PLUS"]
        weights = [0.10, 0.25, 0.30, 0.20, 0.10, 0.05]
        
        return {
            "entity_id": entity_id,
            "fleet_age_band": random.choices(bands, weights=weights)[0],
            "weighted_average_age": round(random.uniform(3, 25), 1),
            "data_source": "equasis_fleet_age",
            "extracted_at": datetime.utcnow().isoformat()
        }
