"""
Aerospace Stub Extractors - Aviation-Specific Data Sources

These extractors simulate data from aviation-specific sources for the
aerospace coverage domain. They build on common extractors where applicable.

Signal Groups Covered:
- network_authority: Alliance, codeshare, lessor, OEM, MRO data
- safety_record: Accident/incident history, investigation findings

Data Sources Simulated:
- IATA Airline databases
- Aviation Safety Network (ASN)
- ICAO safety databases
- Aircraft registry data
- Airline partnerships and agreements
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from signal_architecture.signals.extractors.base import StubExtractor, utcnow
from signal_architecture.signals.types import ExtractorResult


# =============================================================================
# AIRLINE ALLIANCE EXTRACTOR
# Signal: network_authority.alliance_membership
# =============================================================================

class AirlineAllianceExtractor(StubExtractor):
    """
    STUB: Simulates airline alliance membership data.
    
    Real implementation would query:
    - IATA membership database
    - Alliance official websites (Star Alliance, oneworld, SkyTeam)
    - Airline partnership announcements
    
    Used for: alliance_membership signal
    """
    SOURCE_NAME = "iata_alliance_registry"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY  # Alliance status rarely changes
    
    ALLIANCES = [
        {"code": "STAR", "name": "Star Alliance", "tier": 3, "member_count": 26},
        {"code": "OW", "name": "oneworld", "tier": 3, "member_count": 14},
        {"code": "ST", "name": "SkyTeam", "tier": 3, "member_count": 19},
    ]
    
    MEMBERSHIP_TIERS = ["FOUNDING", "FULL", "CONNECTING_PARTNER", "AFFILIATE"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Major airlines more likely to be in alliance
        has_alliance = self._random_bool(0.35)
        
        alliance_data = None
        if has_alliance:
            alliance = self._random_choice(self.ALLIANCES)
            join_date = self._random_date_iso(years_back=15)
            
            alliance_data = {
                "alliance_code": alliance["code"],
                "alliance_name": alliance["name"],
                "alliance_tier": alliance["tier"],
                "membership_status": self._random_choice(["ACTIVE", "ACTIVE", "ACTIVE", "PENDING"]),
                "membership_tier": self._random_choice(self.MEMBERSHIP_TIERS, 
                    weights=[0.1, 0.6, 0.2, 0.1]),
                "join_date": join_date,
                "is_founding_member": self._random_bool(0.15),
                "codeshare_partners_in_alliance": self._random_int(5, alliance["member_count"]),
                "frequent_flyer_program_integrated": self._random_bool(0.9),
                "lounge_access_reciprocal": self._random_bool(0.95),
            }
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_alliance_membership": has_alliance,
                "alliance": alliance_data,
                "is_iata_member": self._random_bool(0.85),
                "iata_code": self._random_string(2) if self._random_bool(0.9) else None,
                "icao_code": self._random_string(3),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# CODESHARE PARTNERSHIP EXTRACTOR
# Signal: network_authority.codeshare_quality
# =============================================================================

class CodesharePartnershipExtractor(StubExtractor):
    """
    STUB: Simulates codeshare and interline partnership data.
    
    Real implementation would query:
    - Airline schedule databases (OAG)
    - IATA interline agreements
    - Published codeshare announcements
    
    Used for: codeshare_quality signal
    """
    SOURCE_NAME = "codeshare_registry"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    PARTNER_QUALITY_TIERS = ["TIER1_MAJOR", "TIER2_REGIONAL", "TIER3_LOW_COST", "TIER4_OTHER"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        num_partners = self._random_int(0, 30)
        
        partners = []
        for _ in range(num_partners):
            quality_tier = self._random_choice(self.PARTNER_QUALITY_TIERS,
                weights=[0.3, 0.35, 0.25, 0.1])
            
            # Assign safety score based on tier
            if quality_tier == "TIER1_MAJOR":
                safety_score = self._random_int(75, 95)
            elif quality_tier == "TIER2_REGIONAL":
                safety_score = self._random_int(60, 85)
            elif quality_tier == "TIER3_LOW_COST":
                safety_score = self._random_int(55, 80)
            else:
                safety_score = self._random_int(40, 70)
            
            partners.append({
                "partner_id": self._random_id("AIR"),
                "partner_iata_code": self._random_string(2),
                "quality_tier": quality_tier,
                "partnership_type": self._random_choice(["CODESHARE", "INTERLINE", "BLOCK_SPACE"]),
                "safety_score": safety_score,
                "iosa_registered": self._random_bool(0.7),
                "effective_date": self._random_date_iso(years_back=10),
                "routes_operated": self._random_int(1, 50),
            })
        
        # Calculate quality metrics
        if partners:
            avg_safety_score = sum(p["safety_score"] for p in partners) / len(partners)
            tier1_pct = sum(1 for p in partners if p["quality_tier"] == "TIER1_MAJOR") / len(partners)
            iosa_pct = sum(1 for p in partners if p["iosa_registered"]) / len(partners)
        else:
            avg_safety_score = 0
            tier1_pct = 0
            iosa_pct = 0
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "partner_count": num_partners,
                "partners": partners,
                "average_partner_safety_score": round(avg_safety_score, 1),
                "tier1_partner_percentage": round(tier1_pct * 100, 1),
                "iosa_registered_percentage": round(iosa_pct * 100, 1),
                "has_major_carrier_partnership": any(p["quality_tier"] == "TIER1_MAJOR" for p in partners),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# AIRCRAFT LESSOR EXTRACTOR
# Signal: network_authority.lessor_quality
# =============================================================================

class AircraftLessorExtractor(StubExtractor):
    """
    STUB: Simulates aircraft lessor relationship data.
    
    Real implementation would query:
    - Aircraft registry databases
    - Leasing company databases (GECAS, AerCap, etc.)
    - Fleet databases (Cirium, ch-aviation)
    
    Used for: lessor_quality signal
    """
    SOURCE_NAME = "aircraft_lessor_database"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    TIER1_LESSORS = ["AerCap", "GECAS", "SMBC Aviation", "BOC Aviation", "Avolon", "Air Lease Corp"]
    TIER2_LESSORS = ["ICBC Leasing", "BBAM", "CDB Aviation", "Dubai Aerospace"]
    TIER3_LESSORS = ["Regional Lessor A", "Specialty Lessor B", "Local Lessor C"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Determine ownership mix
        owned_pct = self._random_float(0, 0.8, 2)
        leased_pct = 1 - owned_pct
        
        lessors = []
        if leased_pct > 0:
            num_lessors = self._random_int(1, 5)
            remaining_pct = leased_pct
            
            for i in range(num_lessors):
                # Determine tier
                tier = self._random_choice([1, 2, 3], weights=[0.5, 0.35, 0.15])
                
                if tier == 1:
                    lessor_name = self._random_choice(self.TIER1_LESSORS)
                    credit_quality = self._random_choice(["AAA", "AA", "A"])
                elif tier == 2:
                    lessor_name = self._random_choice(self.TIER2_LESSORS)
                    credit_quality = self._random_choice(["A", "BBB", "BB"])
                else:
                    lessor_name = self._random_choice(self.TIER3_LESSORS)
                    credit_quality = self._random_choice(["BBB", "BB", "B", None])
                
                # Allocate percentage of fleet
                if i == num_lessors - 1:
                    pct = remaining_pct
                else:
                    pct = self._random_float(0.05, remaining_pct * 0.6, 2)
                    remaining_pct -= pct
                
                lessors.append({
                    "lessor_name": lessor_name,
                    "lessor_tier": tier,
                    "fleet_percentage": round(pct * 100, 1),
                    "aircraft_count": self._random_int(1, 50),
                    "lessor_credit_rating": credit_quality,
                    "relationship_years": self._random_int(1, 15),
                    "lease_type": self._random_choice(["OPERATING", "FINANCE", "SALE_LEASEBACK"]),
                })
        
        # Calculate quality metrics
        if lessors:
            avg_tier = sum(l["lessor_tier"] for l in lessors) / len(lessors)
            tier1_exposure = sum(l["fleet_percentage"] for l in lessors if l["lessor_tier"] == 1)
        else:
            avg_tier = 0
            tier1_exposure = 0
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "owned_fleet_percentage": round(owned_pct * 100, 1),
                "leased_fleet_percentage": round(leased_pct * 100, 1),
                "lessor_count": len(lessors),
                "lessors": lessors,
                "average_lessor_tier": round(avg_tier, 2) if lessors else None,
                "tier1_lessor_exposure_pct": round(tier1_exposure, 1),
                "has_tier1_lessor_relationship": any(l["lessor_tier"] == 1 for l in lessors),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# OEM RELATIONSHIP EXTRACTOR
# Signal: network_authority.oem_relationship
# =============================================================================

class OEMRelationshipExtractor(StubExtractor):
    """
    STUB: Simulates OEM (Original Equipment Manufacturer) relationship data.
    
    Real implementation would query:
    - Boeing/Airbus customer databases
    - Order backlog announcements
    - Maintenance agreement registries
    
    Used for: oem_relationship signal
    """
    SOURCE_NAME = "oem_relationship_database"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    OEMS = [
        {"name": "Boeing", "tier": 1, "support_quality": 95},
        {"name": "Airbus", "tier": 1, "support_quality": 95},
        {"name": "Embraer", "tier": 1, "support_quality": 90},
        {"name": "ATR", "tier": 2, "support_quality": 85},
        {"name": "Bombardier", "tier": 2, "support_quality": 85},
        {"name": "COMAC", "tier": 3, "support_quality": 70},
        {"name": "Textron Aviation", "tier": 2, "support_quality": 85},
        {"name": "Gulfstream", "tier": 1, "support_quality": 95},
        {"name": "Dassault", "tier": 1, "support_quality": 92},
    ]
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Select 1-3 OEMs for the fleet
        num_oems = self._random_int(1, 3)
        selected_oems = []
        
        for _ in range(num_oems):
            oem = self._random_choice(self.OEMS)
            if oem["name"] not in [o["oem_name"] for o in selected_oems]:
                selected_oems.append({
                    "oem_name": oem["name"],
                    "oem_tier": oem["tier"],
                    "fleet_percentage": self._random_float(10, 100 / num_oems, 1),
                    "relationship_type": self._random_choice([
                        "CUSTOMER", "LAUNCH_CUSTOMER", "PREFERRED_CUSTOMER"
                    ], weights=[0.7, 0.1, 0.2]),
                    "has_support_agreement": self._random_bool(0.7),
                    "support_agreement_type": self._random_choice([
                        "FLIGHT_HOUR", "COMPREHENSIVE", "BASIC", None
                    ]) if self._random_bool(0.7) else None,
                    "active_orders": self._random_int(0, 50),
                    "relationship_years": self._random_int(1, 40),
                    "oem_support_quality_score": oem["support_quality"],
                })
        
        # Calculate metrics
        has_tier1 = any(o["oem_tier"] == 1 for o in selected_oems)
        has_comprehensive_support = any(o.get("support_agreement_type") == "COMPREHENSIVE" for o in selected_oems)
        total_orders = sum(o["active_orders"] for o in selected_oems)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "oem_relationship_count": len(selected_oems),
                "oem_relationships": selected_oems,
                "has_tier1_oem": has_tier1,
                "has_comprehensive_support_agreement": has_comprehensive_support,
                "total_active_orders": total_orders,
                "is_launch_customer_any": any(o["relationship_type"] == "LAUNCH_CUSTOMER" for o in selected_oems),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# MRO PROVIDER EXTRACTOR  
# Signal: network_authority.mro_quality
# =============================================================================

class MROProviderExtractor(StubExtractor):
    """
    STUB: Simulates MRO (Maintenance, Repair, Overhaul) provider data.
    
    Real implementation would query:
    - MRO provider databases
    - FAA/EASA Part 145 certificate holders
    - Airline maintenance announcements
    
    Used for: mro_quality signal
    """
    SOURCE_NAME = "mro_database"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    TIER1_MROS = ["Lufthansa Technik", "AFI KLM E&M", "ST Engineering", "HAECO", "AAR Corp"]
    TIER2_MROS = ["MTU Aero Engines", "StandardAero", "FL Technics", "Magnetic MRO"]
    TIER3_MROS = ["Regional MRO A", "Local Provider B", "In-house Facility"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        has_in_house = self._random_bool(0.4)
        num_external_mros = self._random_int(1, 4)
        
        mro_providers = []
        
        if has_in_house:
            mro_providers.append({
                "provider_name": "In-house MRO",
                "provider_tier": 2 if self._random_bool(0.6) else 3,
                "is_in_house": True,
                "service_types": self._random_choice([
                    ["LINE", "BASE"],
                    ["LINE"],
                    ["LINE", "BASE", "ENGINE"],
                ]),
                "certifications": ["FAA_PART_145", "EASA_PART_145"] if self._random_bool(0.7) else ["FAA_PART_145"],
                "quality_rating": self._random_int(70, 90),
            })
        
        for _ in range(num_external_mros):
            tier = self._random_choice([1, 2, 3], weights=[0.4, 0.4, 0.2])
            
            if tier == 1:
                name = self._random_choice(self.TIER1_MROS)
                quality = self._random_int(85, 98)
            elif tier == 2:
                name = self._random_choice(self.TIER2_MROS)
                quality = self._random_int(70, 90)
            else:
                name = self._random_choice(self.TIER3_MROS)
                quality = self._random_int(55, 80)
            
            mro_providers.append({
                "provider_name": name,
                "provider_tier": tier,
                "is_in_house": False,
                "service_types": self._random_choice([
                    ["ENGINE"],
                    ["COMPONENT"],
                    ["BASE", "ENGINE"],
                    ["LINE", "BASE"],
                ]),
                "certifications": ["FAA_PART_145", "EASA_PART_145"],
                "quality_rating": quality,
                "contract_type": self._random_choice(["FLIGHT_HOUR", "TIME_MATERIAL", "FIXED_PRICE"]),
                "relationship_years": self._random_int(1, 15),
            })
        
        # Calculate metrics
        avg_quality = sum(m["quality_rating"] for m in mro_providers) / len(mro_providers)
        has_tier1 = any(m["provider_tier"] == 1 for m in mro_providers)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "mro_provider_count": len(mro_providers),
                "mro_providers": mro_providers,
                "has_in_house_mro": has_in_house,
                "has_tier1_mro": has_tier1,
                "average_mro_quality": round(avg_quality, 1),
                "all_easa_certified": all("EASA_PART_145" in m["certifications"] for m in mro_providers),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# AVIATION SAFETY DATABASE EXTRACTOR
# Signals: safety_record group (accident_history, incident_history, etc.)
# =============================================================================

class AviationSafetyDatabaseExtractor(StubExtractor):
    """
    STUB: Simulates aviation safety database queries.
    
    Real implementation would query:
    - Aviation Safety Network (ASN)
    - ICAO ADREP database
    - FAA Accident/Incident Database
    - NTSB investigation database
    - EASA Safety Recommendations
    
    Used for: accident_history, incident_history, accident_rate, 
              fatality_history, investigation_findings signals
    """
    SOURCE_NAME = "aviation_safety_database"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    ACCIDENT_CATEGORIES = [
        "HULL_LOSS", "SUBSTANTIAL_DAMAGE", "GEAR_UP_LANDING", 
        "RUNWAY_EXCURSION", "GROUND_COLLISION"
    ]
    
    INCIDENT_CATEGORIES = [
        "SERIOUS_INCIDENT", "AIRPROX", "RUNWAY_INCURSION", "TCAS_RA",
        "SMOKE_FIRE", "DEPRESSURIZATION", "ENGINE_FAILURE", "BIRD_STRIKE_SERIOUS"
    ]
    
    INVESTIGATION_FACTORS = [
        "PILOT_ERROR", "MECHANICAL_FAILURE", "MAINTENANCE_ERROR",
        "ATC_FACTOR", "WEATHER", "DESIGN_FLAW", "TRAINING_INADEQUATE"
    ]
    
    def _do_extract(self, entity_id: str, lookback_years: int = 10, **kwargs) -> ExtractorResult:
        # Generate accidents (rare)
        num_accidents = 0
        if self._random_bool(0.15):  # 15% have any accidents
            num_accidents = self._random_int(1, 3)
        
        accidents = []
        for _ in range(num_accidents):
            has_fatalities = self._random_bool(0.2)
            accidents.append({
                "event_id": self._random_id("ACC"),
                "event_date": self._random_date_iso(years_back=lookback_years),
                "category": self._random_choice(self.ACCIDENT_CATEGORIES),
                "aircraft_type": self._random_choice(["B737", "A320", "E190", "ATR72", "B777"]),
                "location": self._random_country_code(),
                "fatalities": self._random_int(0, 150) if has_fatalities else 0,
                "injuries": self._random_int(0, 50),
                "hull_loss": self._random_bool(0.4),
                "investigation_complete": self._random_bool(0.8),
                "operator_cited": self._random_bool(0.35),
                "primary_cause": self._random_choice(self.INVESTIGATION_FACTORS) if self._random_bool(0.8) else None,
            })
        
        # Generate incidents (more common)
        num_incidents = self._random_int(0, 15)
        incidents = []
        for _ in range(num_incidents):
            incidents.append({
                "event_id": self._random_id("INC"),
                "event_date": self._random_date_iso(years_back=lookback_years),
                "category": self._random_choice(self.INCIDENT_CATEGORIES),
                "severity": self._random_choice(["SERIOUS", "SIGNIFICANT", "MINOR"]),
                "aircraft_type": self._random_choice(["B737", "A320", "E190", "ATR72"]),
                "location": self._random_country_code(),
                "investigation_complete": self._random_bool(0.7),
                "contributing_factors": [self._random_choice(self.INVESTIGATION_FACTORS) 
                                        for _ in range(self._random_int(1, 3))],
            })
        
        # Calculate industry comparison metrics
        annual_departures = self._random_int(10000, 500000)
        total_accidents_10yr = num_accidents
        accident_rate = (total_accidents_10yr / (annual_departures * 10)) * 1000000 if annual_departures > 0 else 0
        industry_avg_rate = 0.18  # Industry average per million departures
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "lookback_years": lookback_years,
            "data": {
                # Accident data
                "total_accidents": num_accidents,
                "accidents": accidents,
                "fatal_accidents": sum(1 for a in accidents if a["fatalities"] > 0),
                "total_fatalities": sum(a["fatalities"] for a in accidents),
                "hull_losses": sum(1 for a in accidents if a["hull_loss"]),
                
                # Incident data
                "total_incidents": num_incidents,
                "incidents": incidents,
                "serious_incidents": sum(1 for i in incidents if i["severity"] == "SERIOUS"),
                
                # Rate analysis
                "annual_departures_estimate": annual_departures,
                "accident_rate_per_million_departures": round(accident_rate, 4),
                "industry_average_rate": industry_avg_rate,
                "rate_vs_industry": round(accident_rate / industry_avg_rate, 2) if industry_avg_rate > 0 else None,
                
                # Investigation findings
                "operator_cited_count": sum(1 for a in accidents if a["operator_cited"]),
                "years_since_last_accident": None,  # Would calculate from dates
                "years_since_fatal_accident": None,
            }
        }
        
        return self._create_success_result(data)
