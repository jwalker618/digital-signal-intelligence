"""
Marine Extractors - Network Authority & Operational Telemetry

Stub extractors for marine insurance signals.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict

from ...base import StubExtractor


# =============================================================================
# NETWORK AUTHORITY EXTRACTORS
# =============================================================================

class ClassificationSocietyExtractor(StubExtractor):
    """Extract classification society information."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        iacs_members = ["Lloyd's Register", "DNV", "Bureau Veritas", "ABS", "ClassNK", 
                       "RINA", "Korean Register", "CCS", "Indian Register", "PRS"]
        non_iacs = ["International Register of Shipping", "Phoenix Register", "Other"]
        
        is_iacs = random.random() > 0.15
        society = random.choice(iacs_members) if is_iacs else random.choice(non_iacs)
        
        return {
            "entity_id": entity_id,
            "classification_society": society,
            "is_iacs_member": is_iacs,
            "fleet_percentage_iacs": random.randint(85, 100) if is_iacs else random.randint(30, 70),
            "class_notation_quality": random.choice(["enhanced", "standard", "basic"]),
            "dual_class": random.random() < 0.1,
            "data_source": "equasis_class_society_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PIClubExtractor(StubExtractor):
    """Extract P&I Club membership information."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        ig_clubs = ["Gard", "Britannia", "North", "Standard", "Steamship Mutual",
                   "UK P&I", "West of England", "Skuld", "Swedish Club", "Japan P&I",
                   "American Club", "London P&I", "Shipowners"]
        fixed_premium = ["Fixed premium insurer", "Non-IG mutual"]
        
        is_ig = random.random() > 0.2
        club = random.choice(ig_clubs) if is_ig else random.choice(fixed_premium)
        
        return {
            "entity_id": entity_id,
            "pi_club": club,
            "is_ig_member": is_ig,
            "membership_years": random.randint(1, 30) if is_ig else random.randint(1, 10),
            "claims_record": random.choice(["excellent", "good", "average", "below_average"]),
            "coverage_limit_mm": random.choice([500, 1000, 3000]) if is_ig else random.randint(50, 500),
            "data_source": "ig_club_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class ChartererQualityExtractor(StubExtractor):
    """Extract charterer relationship quality."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        oil_majors = ["Shell", "BP", "ExxonMobil", "Chevron", "TotalEnergies", "Equinor"]
        commodity_traders = ["Vitol", "Trafigura", "Glencore", "Gunvor", "Mercuria"]
        liner_majors = ["Maersk", "MSC", "CMA CGM", "COSCO", "Hapag-Lloyd"]
        
        has_major = random.random() > 0.4
        
        return {
            "entity_id": entity_id,
            "has_oil_major_approval": has_major and random.random() > 0.5,
            "approved_by": random.sample(oil_majors + commodity_traders, k=random.randint(0, 4)) if has_major else [],
            "liner_relationships": random.sample(liner_majors, k=random.randint(0, 2)),
            "charterer_quality_score": random.randint(60, 95) if has_major else random.randint(30, 65),
            "time_charter_ratio": round(random.uniform(0, 0.8), 2),
            "data_source": "rightship_charterer_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class MarineBankingExtractor(StubExtractor):
    """Extract ship finance relationships."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        tier1_banks = ["DNB", "Nordea", "ABN AMRO", "ING", "Credit Suisse", "Citi"]
        tier2_banks = ["Danish Ship Finance", "KfW IPEX", "CEXIM", "K-Sure backed"]
        tier3_banks = ["Regional bank", "Private equity", "Lease finance"]
        
        tier = random.choices([1, 2, 3], weights=[0.25, 0.40, 0.35])[0]
        banks = {1: tier1_banks, 2: tier2_banks, 3: tier3_banks}
        
        return {
            "entity_id": entity_id,
            "primary_lender": random.choice(banks[tier]),
            "lender_tier": tier,
            "loan_to_value": round(random.uniform(0.4, 0.75), 2),
            "covenant_compliance": random.choice(["compliant", "waiver", "breach"]),
            "refinancing_recent": random.random() < 0.2,
            "data_source": "marine_finance_databases",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FlagStateExtractor(StubExtractor):
    """Extract flag state quality information."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        white_list = ["Bahamas", "Marshall Islands", "Singapore", "Hong Kong", "Norway", 
                     "Denmark", "UK", "Netherlands", "Japan", "Germany"]
        grey_list = ["Panama", "Liberia", "Malta", "Cyprus", "Antigua", "Bermuda"]
        black_list = ["Cameroon", "Comoros", "Moldova", "Tanzania", "Togo"]
        
        list_type = random.choices(["white", "grey", "black"], weights=[0.55, 0.35, 0.10])[0]
        flags = {"white": white_list, "grey": grey_list, "black": black_list}
        
        return {
            "entity_id": entity_id,
            "primary_flag": random.choice(flags[list_type]),
            "paris_mou_list": list_type.upper() + "_LIST",
            "tokyo_mou_status": random.choice(["white", "grey", "black"]).upper(),
            "fleet_flag_consistency": random.random() > 0.3,
            "flag_state_inspections": random.randint(0, 5),
            "data_source": "paris_mou_tokyo_mou",
            "extracted_at": datetime.utcnow().isoformat()
        }


class MarineIndustryAssociationExtractor(StubExtractor):
    """Extract industry association membership."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        associations = ["BIMCO", "Intertanko", "Intercargo", "ICS", "IMCA", 
                       "IADC", "OCIMF", "CDI", "WSC"]
        
        memberships = random.sample(associations, k=random.randint(0, 4))
        
        return {
            "entity_id": entity_id,
            "memberships": memberships,
            "membership_count": len(memberships),
            "committee_participation": random.randint(0, 3),
            "years_active": random.randint(2, 25) if memberships else 0,
            "data_source": "association_directories",
            "extracted_at": datetime.utcnow().isoformat()
        }


class TechnicalManagerExtractor(StubExtractor):
    """Extract technical manager quality."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        tier1_managers = ["V.Ships", "Anglo-Eastern", "Bernhard Schulte", "Fleet Management", "Columbia"]
        tier2_managers = ["Wallem", "Thome", "OSM Maritime", "Intership Navigation"]
        
        is_third_party = random.random() > 0.4
        tier = random.choices([1, 2, 3], weights=[0.3, 0.4, 0.3])[0] if is_third_party else None
        
        return {
            "entity_id": entity_id,
            "third_party_managed": is_third_party,
            "manager_name": random.choice(tier1_managers if tier == 1 else tier2_managers) if is_third_party and tier in [1, 2] else ("In-house" if not is_third_party else "Small manager"),
            "manager_tier": tier,
            "fleet_under_management": random.randint(50, 500) if is_third_party else None,
            "iso_certified": random.random() > 0.3,
            "data_source": "ship_manager_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PortRelationshipExtractor(StubExtractor):
    """Extract port and terminal relationships."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        major_ports = ["Singapore", "Rotterdam", "Shanghai", "Ningbo", "Busan", 
                      "Hong Kong", "Antwerp", "Los Angeles", "Hamburg", "Jebel Ali"]
        
        return {
            "entity_id": entity_id,
            "regular_ports": random.sample(major_ports, k=random.randint(3, 8)),
            "preferred_terminal_agreements": random.randint(0, 5),
            "port_state_relationships": random.choice(["excellent", "good", "standard"]),
            "average_port_stay_efficiency": round(random.uniform(0.7, 1.0), 2),
            "data_source": "ais_port_call_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# OPERATIONAL TELEMETRY EXTRACTORS
# =============================================================================

class AISComplianceExtractor(StubExtractor):
    """Extract AIS transmission compliance data."""
    
    DEFAULT_TTL_SECONDS = 3600  # Hourly - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        compliance_rate = random.uniform(0.85, 1.0)
        
        return {
            "entity_id": entity_id,
            "ais_compliance_rate": round(compliance_rate, 3),
            "fleet_average_transmission_gaps_per_month": random.randint(0, 10),
            "max_gap_hours": random.randint(0, 48),
            "intentional_gaps_suspected": compliance_rate < 0.92,
            "ais_quality_score": round(compliance_rate * 100, 1),
            "data_source": "ais_tracking_services",
            "extracted_at": datetime.utcnow().isoformat()
        }


class DarkActivityExtractor(StubExtractor):
    """Extract dark activity patterns from AIS data."""
    
    DEFAULT_TTL_SECONDS = 3600  # Hourly - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_dark_activity = random.random() < 0.15
        
        return {
            "entity_id": entity_id,
            "dark_activity_events_12mo": random.randint(0, 20) if has_dark_activity else random.randint(0, 3),
            "suspicious_location_gaps": random.randint(0, 5) if has_dark_activity else 0,
            "high_risk_area_gaps": random.randint(0, 3) if has_dark_activity else 0,
            "dark_sts_suspected": has_dark_activity and random.random() > 0.6,
            "dark_activity_score": random.randint(20, 50) if has_dark_activity else random.randint(80, 100),
            "data_source": "windward_pole_star",
            "extracted_at": datetime.utcnow().isoformat()
        }


class RouteRiskExtractor(StubExtractor):
    """Extract trading route risk profile."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        high_risk_areas = ["Gulf of Aden", "West Africa", "Strait of Malacca", 
                         "South China Sea", "Black Sea", "Red Sea"]
        
        return {
            "entity_id": entity_id,
            "high_risk_area_calls_12mo": random.randint(0, 30),
            "war_risk_area_exposure_pct": round(random.uniform(0, 0.25), 2),
            "piracy_area_transits": random.randint(0, 20),
            "high_risk_areas_visited": random.sample(high_risk_areas, k=random.randint(0, 3)),
            "route_risk_score": random.randint(50, 95),
            "data_source": "ais_route_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PSCRegionExtractor(StubExtractor):
    """Extract PSC region exposure from trading patterns."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "paris_mou_calls_pct": round(random.uniform(0.2, 0.5), 2),
            "tokyo_mou_calls_pct": round(random.uniform(0.2, 0.4), 2),
            "uscg_calls_pct": round(random.uniform(0.05, 0.2), 2),
            "high_targeting_region_exposure": random.random() < 0.3,
            "psc_region_risk_score": random.randint(60, 90),
            "data_source": "port_call_psc_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class OperationalEfficiencyExtractor(StubExtractor):
    """Extract operational efficiency indicators."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "average_speed_efficiency": round(random.uniform(0.7, 0.95), 2),
            "slow_steaming_adoption": random.random() > 0.4,
            "voyage_optimization_evidence": random.random() > 0.5,
            "fuel_efficiency_vs_peers": random.choice(["above_average", "average", "below_average"]),
            "port_turnaround_efficiency": round(random.uniform(0.75, 0.98), 2),
            "operational_discipline_score": random.randint(55, 95),
            "data_source": "ais_speed_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class WeatherRoutingExtractor(StubExtractor):
    """Extract weather routing behavior evidence."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "weather_routing_service_used": random.random() > 0.5,
            "deviation_for_weather_evidence": random.random() > 0.6,
            "heavy_weather_damage_claims_5yr": random.randint(0, 3),
            "seasonal_route_adjustment": random.random() > 0.5,
            "weather_routing_score": random.randint(50, 90),
            "data_source": "voyage_weather_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }
