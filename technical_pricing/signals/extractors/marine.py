"""
extractors/#coverage#.py - Coverage Inference Functions
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from .framework import (
    TTLCategory,
    TTLConfig,
    DataSource,
    SignalResult,
    ExtractionResult,
    MissingSignalStrategy,
    SignalWeightConfig,
    DataExtractor,

    EXTRACTOR_REGISTRY,

    register_extractor
)

logger = logging.getLogger(__name__)

# =============================================================================
# MARINE EXTRACTORS
# =============================================================================

@register_extractor
class EquasisOperatorExtractor(DataExtractor):
    """
    Equasis API - Fleet composition, ISM compliance, company details.
    
    Signals: operator_type, vessel_category, fleet_stability, management_consistency
    
    Alternative Sources:
    - IHS Markit: ownership/search
    - Clarksons: owners/profile
    - Lloyd's List: companies/search
    """
    source_name = "equasis"
    coverage = "marine"
    signals = ["operator_type", "vessel_category", "fleet_stability", "management_consistency", "fleet_age"]
    ttl_config = TTLConfig.dynamic("Fleet and company data refreshed daily")
    
    alternative_sources = [
        DataSource("api", "ihs_markit", "ownership/search", priority=2),
        DataSource("api", "clarksons", "owners/profile", priority=3),
        DataSource("api", "lloyd_list", "companies/search", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        fleet_size = self._weighted_choice([
            (self._rng.randint(1, 5), 0.30), (self._rng.randint(6, 20), 0.35),
            (self._rng.randint(21, 50), 0.20), (self._rng.randint(51, 200), 0.15),
        ])
        vessels = []
        for i in range(fleet_size):
            build_year = self._rng.randint(1995, 2024)
            vessels.append({
                "imo_number": str(self._rng.randint(9000000, 9999999)),
                "vessel_type": self._weighted_choice([
                    ("Container Ship", 0.25), ("Oil Tanker", 0.20), ("Bulk Carrier", 0.20),
                    ("Chemical Tanker", 0.12), ("LNG Carrier", 0.08), ("General Cargo", 0.10), ("Other", 0.05)
                ]),
                "gross_tonnage": self._rng.randint(5000, 180000),
                "build_year": build_year,
                "age_years": 2024 - build_year,
                "flag_state": self._weighted_choice([
                    ("Panama", 0.18), ("Liberia", 0.15), ("Marshall Islands", 0.14),
                    ("Singapore", 0.10), ("Hong Kong", 0.10), ("Malta", 0.08), ("Bahamas", 0.07), ("Other", 0.18)
                ]),
                "classification_society": self._weighted_choice([
                    ("DNV", 0.22), ("Lloyd's Register", 0.20), ("Bureau Veritas", 0.15),
                    ("ABS", 0.15), ("ClassNK", 0.12), ("Other", 0.16)
                ]),
            })
        
        # Determine operator type based on fleet characteristics
        avg_age = sum(v["age_years"] for v in vessels) / len(vessels) if vessels else 0
        type_counts = {}
        for v in vessels:
            t = v["vessel_type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        majority_type = max(type_counts, key=type_counts.get) if type_counts else "Unknown"
        
        # Operator classification logic
        if majority_type == "Container Ship" and fleet_size >= 50:
            operator_type = "major_liner"
        elif majority_type == "Oil Tanker" and fleet_size >= 30:
            operator_type = "major_tanker"
        elif majority_type == "Bulk Carrier" and fleet_size >= 40:
            operator_type = "major_bulk"
        elif fleet_size >= 10:
            operator_type = "regional_operator"
        else:
            operator_type = "tramp_operator"
        
        raw_data = {
            "company": {
                "imo_company_number": self.kwargs.get("company_id", self._random_id("IMO", 7)),
                "company_name": self.kwargs.get("company_name", self._random_company_name("Shipping")),
                "company_status": self._weighted_choice([("Active", 0.95), ("Inactive", 0.05)]),
                "role": self._weighted_choice([("Owner", 0.40), ("Operator", 0.35), ("Manager", 0.25)]),
                "year_established": self._rng.randint(1950, 2020),
            },
            "fleet": {
                "total_vessels": fleet_size,
                "vessels": vessels[:30],
                "average_age": round(avg_age, 1),
                "majority_type": majority_type,
                "type_distribution": type_counts,
            },
            "classification": {
                "operator_type": operator_type,
                "vessel_category": majority_type.lower().replace(" ", "_"),
            },
            "management_history": {
                "years_operating": self._rng.randint(5, 50),
                "manager_changes_5yr": self._weighted_choice([(0, 0.70), (1, 0.20), (2, 0.10)]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "fleet_size": fleet_size,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class PSCInspectionExtractor(DataExtractor):
    """
    Port State Control Database - Inspection history, deficiencies, detentions.
    
    Signals: psc_detention, psc_deficiency, safety_compliance
    
    Alternative Sources:
    - Paris MoU: inspections/search
    - Tokyo MoU: inspections/search  
    - US Coast Guard: psc/search
    """
    source_name = "psc_database"
    coverage = "marine"
    signals = ["psc_detention", "psc_deficiency", "safety_compliance"]
    ttl_config = TTLConfig.dynamic("PSC inspections updated daily")
    
    alternative_sources = [
        DataSource("api", "paris_mou", "inspections/search", priority=1),
        DataSource("api", "tokyo_mou", "inspections/search", priority=2),
        DataSource("api", "uscg", "psc/search", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        num_inspections = self._rng.randint(3, 15)
        inspections = []
        total_deficiencies = 0
        total_detentions = 0
        
        for _ in range(num_inspections):
            deficiency_count = self._weighted_choice([
                (0, 0.35), (self._rng.randint(1, 3), 0.35),
                (self._rng.randint(4, 8), 0.20), (self._rng.randint(9, 15), 0.10)
            ])
            detained = deficiency_count > 5 and self._rng.random() < 0.15
            total_deficiencies += deficiency_count
            total_detentions += 1 if detained else 0
            
            inspections.append({
                "inspection_date": self._random_date(1095, 0),
                "port": self._weighted_choice([
                    ("Rotterdam", 0.08), ("Singapore", 0.10), ("Shanghai", 0.08),
                    ("Houston", 0.07), ("Antwerp", 0.06), ("Other", 0.61)
                ]),
                "psc_regime": self._weighted_choice([
                    ("Paris MoU", 0.30), ("Tokyo MoU", 0.25),
                    ("US Coast Guard", 0.20), ("Indian Ocean MoU", 0.10), ("Other", 0.15)
                ]),
                "deficiency_count": deficiency_count,
                "deficiency_categories": self._generate_deficiencies(deficiency_count),
                "detained": detained,
                "detention_days": self._rng.randint(1, 10) if detained else 0,
            })
        
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "inspection_summary": {
                "total_inspections_3yr": num_inspections,
                "total_deficiencies_3yr": total_deficiencies,
                "total_detentions_3yr": total_detentions,
                "deficiency_ratio": round(total_deficiencies / num_inspections, 2) if num_inspections > 0 else 0,
                "detention_rate": round(total_detentions / num_inspections, 3) if num_inspections > 0 else 0,
            },
            "inspections": sorted(inspections, key=lambda x: x["inspection_date"], reverse=True),
            "banned": total_detentions >= 3 and self._rng.random() < 0.10,
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="database",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "inspections": num_inspections,
                "detentions": total_detentions,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )
    
    def _generate_deficiencies(self, count: int) -> List[str]:
        categories = [
            "Fire Safety", "Life-Saving Appliances", "Navigation",
            "Radio Communications", "Cargo Operations", "MARPOL Annex I",
            "MARPOL Annex II", "ISM", "ISPS", "MLC", "Structural", "Propulsion"
        ]
        return self._rng.sample(categories, min(count, len(categories)))


@register_extractor
class AISTrackingExtractor(DataExtractor):
    """
    AIS Tracking Data - Position history, port calls, dark activity, STS events.
    
    Signals: ais_compliance, dark_activity, route_risk, operational_efficiency
    
    Alternative Sources:
    - MarineTraffic: vessels/ais_quality, vessels/dark_events
    - Spire: vessels/transmission
    - Windward: risk/dark_activity
    - ExactEarth: coverage/analysis
    """
    source_name = "ais_tracking"
    coverage = "marine"
    signals = ["ais_compliance", "dark_activity", "route_risk", "operational_efficiency", "psc_region_exposure"]
    ttl_config = TTLConfig.dynamic("AIS data updated daily for pattern analysis")
    
    alternative_sources = [
        DataSource("api", "marinetraffic", "vessels/ais_quality", priority=1),
        DataSource("api", "spire", "vessels/transmission", priority=2),
        DataSource("api", "windward", "risk/dark_activity", priority=3),
        DataSource("api", "exactearth", "coverage/analysis", priority=4),
        DataSource("api", "pole_star", "ais_gaps/analysis", priority=5),
    ]

    def extract(self) -> ExtractionResult:
        num_port_calls = self._rng.randint(10, 40)
        countries = ["China", "Singapore", "USA", "Netherlands", "UAE", "South Korea", 
                    "Japan", "Germany", "Belgium", "UK", "Brazil", "India"]
        
        port_calls = []
        for _ in range(num_port_calls):
            port_calls.append({
                "port": f"Port_{self._random_id('', 4)}",
                "country": self._weighted_choice([(c, 1/len(countries)) for c in countries]),
                "arrival_date": self._random_date(365, 0),
                "departure_date": self._random_date(365, 0),
                "days_in_port": self._rng.randint(1, 7),
            })
        
        # AIS Gap Analysis
        ais_gaps = []
        num_gaps = self._weighted_choice([(0, 0.70), (1, 0.15), (2, 0.10), (self._rng.randint(3, 5), 0.05)])
        for _ in range(num_gaps):
            ais_gaps.append({
                "start_date": self._random_date(365, 30),
                "duration_hours": self._rng.randint(6, 168),
                "location_type": self._weighted_choice([("Coastal", 0.50), ("Open Ocean", 0.35), ("Anchorage", 0.15)]),
                "last_known_position": {"lat": round(self._rng.uniform(-60, 60), 4), "lon": round(self._rng.uniform(-180, 180), 4)},
                "risk_level": self._weighted_choice([("Low", 0.60), ("Medium", 0.25), ("High", 0.12), ("Critical", 0.03)]),
            })
        
        # STS (Ship-to-Ship) Transfer Events
        sts_events = []
        num_sts = self._weighted_choice([(0, 0.85), (1, 0.10), (2, 0.05)])
        for _ in range(num_sts):
            sts_events.append({
                "event_date": self._random_date(365, 0),
                "location": {"lat": round(self._rng.uniform(-60, 60), 4), "lon": round(self._rng.uniform(-180, 180), 4)},
                "location_risk": self._weighted_choice([("Low", 0.70), ("Medium", 0.20), ("High", 0.10)]),
                "counterparty_known": self._rng.random() > 0.3,
            })
        
        # Sanctions exposure
        high_risk_countries = ["Iran", "North Korea", "Syria", "Venezuela", "Russia"]
        sanctioned_exposure = self._rng.random() < 0.03
        high_risk_transits = self._rng.randint(0, 5)
        
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "port_calls": {
                "total_12mo": num_port_calls,
                "unique_countries": len(set(p["country"] for p in port_calls)),
                "calls": port_calls[:20],
            },
            "ais_gaps": {
                "total_gaps_12mo": num_gaps,
                "high_risk_gaps": sum(1 for g in ais_gaps if g["risk_level"] in ("High", "Critical")),
                "total_dark_hours": sum(g["duration_hours"] for g in ais_gaps),
                "gaps": ais_gaps,
            },
            "sts_events": {
                "total_12mo": num_sts,
                "high_risk_events": sum(1 for s in sts_events if s["location_risk"] == "High"),
                "events": sts_events,
            },
            "sanctions_exposure": {
                "sanctioned_area_visit": sanctioned_exposure,
                "high_risk_area_transits": high_risk_transits,
                "high_risk_countries_visited": self._rng.sample(high_risk_countries, min(high_risk_transits, len(high_risk_countries))) if high_risk_transits > 0 else [],
            },
            "operational_patterns": {
                "avg_speed_kts": round(self._rng.uniform(10, 18), 1),
                "utilization_pct": round(self._rng.uniform(60, 95), 1),
                "weather_routing_detected": self._rng.random() > 0.4,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "gaps": num_gaps,
                "sts": num_sts,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class SanctionsScreeningExtractor(DataExtractor):
    """
    Sanctions Screening - OFAC, EU, UN sanctions list checking.
    
    Signals: sanctions_status, ownership_transparency, jurisdiction_risk, historical_sanctions
    
    Alternative Sources:
    - OFAC: sdn/search
    - EU Sanctions: search
    - UN Sanctions: search
    - Windward: sanctions/check
    - Refinitiv: world_check
    """
    source_name = "sanctions_screening"
    coverage = "marine"
    signals = ["sanctions_status", "ownership_transparency", "jurisdiction_risk", "historical_sanctions"]
    ttl_config = TTLConfig.real_time("Sanctions data requires hourly refresh")
    
    alternative_sources = [
        DataSource("api", "ofac", "sdn/search", priority=1),
        DataSource("api", "eu_sanctions", "search", priority=1),
        DataSource("api", "un_sanctions", "search", priority=1),
        DataSource("api", "windward", "sanctions/check", priority=2),
        DataSource("api", "refinitiv", "world_check", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        # Sanctions screening results
        is_sanctioned = self._rng.random() < 0.02
        has_historical = self._rng.random() < 0.05
        
        hits = []
        if is_sanctioned or has_historical:
            num_hits = self._rng.randint(1, 3)
            for _ in range(num_hits):
                hits.append({
                    "list_name": self._weighted_choice([
                        ("OFAC SDN", 0.40), ("EU Consolidated", 0.30),
                        ("UN Security Council", 0.20), ("Other", 0.10)
                    ]),
                    "match_type": self._weighted_choice([("Exact", 0.30), ("Fuzzy", 0.50), ("Associated", 0.20)]),
                    "match_score": round(self._rng.uniform(0.75, 0.99), 2),
                    "status": "Active" if is_sanctioned else "Delisted",
                    "listed_date": self._random_date(2000, 365),
                    "reason": self._weighted_choice([
                        ("WMD Proliferation", 0.15), ("Terrorism", 0.20),
                        ("Narcotics", 0.15), ("Human Rights", 0.20),
                        ("Regional Sanctions", 0.30)
                    ]),
                })
        
        # Ownership transparency
        ownership_layers = self._weighted_choice([(1, 0.30), (2, 0.35), (3, 0.20), (4, 0.10), (5, 0.05)])
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "screening_result": {
                "status": "HIT" if is_sanctioned else ("CLEARED_HISTORICAL" if has_historical else "CLEAR"),
                "total_hits": len(hits),
                "active_hits": sum(1 for h in hits if h["status"] == "Active"),
                "hits": hits,
                "screened_lists": ["OFAC SDN", "EU Consolidated", "UN Security Council", "OFAC Non-SDN"],
                "screening_date": datetime.now().isoformat(),
            },
            "ownership_flags": {
                "high_risk_jurisdiction": self._rng.random() < 0.10,
                "complex_structure": ownership_layers >= 4,
                "ownership_layers": ownership_layers,
                "pep_connection": self._rng.random() < 0.05,
                "beneficial_owner_identified": ownership_layers <= 2,
            },
            "jurisdiction_analysis": {
                "registration_country": self._weighted_choice([
                    ("Panama", 0.15), ("Liberia", 0.12), ("Marshall Islands", 0.12),
                    ("British Virgin Islands", 0.08), ("Cyprus", 0.06), ("Other", 0.47)
                ]),
                "jurisdiction_risk_level": self._weighted_choice([("Low", 0.60), ("Medium", 0.25), ("High", 0.12), ("Very High", 0.03)]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "is_sanctioned": is_sanctioned,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class ClassificationSocietyExtractor(DataExtractor):
    """
    Classification Society Data - Class status, survey compliance, notations.
    
    Signals: class_status, classification_society, vessel_quality, survey_compliance
    
    Alternative Sources:
    - DNV: vessels/search
    - Lloyd's Register: vessels/search
    - Bureau Veritas: vessels/search
    - ABS: vessels/search
    - ClassNK: vessels/search
    - IACS: members/search
    """
    source_name = "classification_society"
    coverage = "marine"
    signals = ["class_status", "classification_society", "vessel_quality", "survey_compliance"]
    ttl_config = TTLConfig.dynamic("Class status updated daily")
    
    alternative_sources = [
        DataSource("api", "dnv", "vessels/search", priority=1),
        DataSource("api", "lloyd_register", "vessels/search", priority=1),
        DataSource("api", "bureau_veritas", "vessels/search", priority=2),
        DataSource("api", "abs", "vessels/search", priority=2),
        DataSource("api", "class_nk", "vessels/search", priority=3),
        DataSource("api", "iacs", "members/search", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        society = self._weighted_choice([
            ("DNV", 0.22), ("Lloyd's Register", 0.20), ("Bureau Veritas", 0.15),
            ("ABS", 0.15), ("ClassNK", 0.12), ("RINA", 0.05),
            ("Korean Register", 0.05), ("CCS", 0.04), ("Indian Register", 0.02)
        ])
        
        is_iacs = society in ["DNV", "Lloyd's Register", "Bureau Veritas", "ABS", "ClassNK", "RINA", "Korean Register", "CCS", "Indian Register"]
        
        class_status = self._weighted_choice([
            ("In Class", 0.92), ("Suspended", 0.04), ("Withdrawn", 0.03), ("Expired", 0.01)
        ])
        
        conditions = self._rng.randint(0, 5) if class_status == "In Class" else 0
        overdue = self._rng.randint(0, min(conditions, 2)) if conditions > 0 else 0
        
        surveys = []
        survey_types = ["Annual", "Intermediate", "Special", "Bottom", "Docking", "Class Renewal"]
        for stype in survey_types:
            if self._rng.random() > 0.3:
                surveys.append({
                    "survey_type": stype,
                    "due_date": self._random_date(-180, 365),
                    "completed_date": self._random_date(365, 0) if self._rng.random() > 0.15 else None,
                    "status": self._weighted_choice([("Completed", 0.85), ("Due", 0.10), ("Overdue", 0.05)]),
                })
        
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "classification": {
                "society_name": society,
                "society_code": society[:3].upper(),
                "is_iacs_member": is_iacs,
                "class_status": class_status,
                "class_notation": f"+{self._rng.randint(1, 100)}A1" if class_status == "In Class" else None,
                "machinery_notation": self._weighted_choice([("+MC", 0.80), ("+UMS", 0.15), (None, 0.05)]),
            },
            "conditions_of_class": {
                "total": conditions,
                "outstanding": conditions - overdue,
                "overdue": overdue,
                "categories": self._rng.sample(["Hull", "Machinery", "Navigation", "Safety", "Environmental"], min(conditions, 5)) if conditions > 0 else [],
            },
            "survey_history": {
                "surveys": surveys,
                "compliance_rate": round(1 - (overdue / max(len(surveys), 1)), 2),
                "last_survey_date": surveys[0]["completed_date"] if surveys and surveys[0]["completed_date"] else None,
            },
            "additional_notations": {
                "ice_class": self._weighted_choice([(None, 0.85), ("1A", 0.08), ("1A Super", 0.04), ("1B", 0.03)]),
                "dynamic_positioning": self._weighted_choice([(None, 0.90), ("DP1", 0.05), ("DP2", 0.04), ("DP3", 0.01)]),
                "green_passport": self._rng.random() > 0.60,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "society": society,
                "is_iacs": is_iacs,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class ISMComplianceExtractor(DataExtractor):
    """
    ISM Compliance Data - DOC status, SMS audits, safety management.
    
    Signals: ism_compliance, safety_management
    
    Alternative Sources:
    - IMO GISIS: ism/search
    - Flag State Databases
    """
    source_name = "ism_compliance"
    coverage = "marine"
    signals = ["ism_compliance", "safety_management"]
    ttl_config = TTLConfig.semi_static("ISM audits occur periodically")
    
    alternative_sources = [
        DataSource("api", "imo_gisis", "ism/search", priority=1),
        DataSource("registry", "flag_state_databases", "ism/status", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        doc_status = self._weighted_choice([
            ("Valid", 0.94), ("Expired", 0.03), ("Suspended", 0.02), ("Withdrawn", 0.01)
        ])
        
        # Audit history
        num_audits = self._rng.randint(2, 6)
        audits = []
        total_findings = 0
        major_nc = 0
        
        for i in range(num_audits):
            audit_type = "Initial" if i == 0 else self._weighted_choice([
                ("Annual", 0.50), ("Intermediate", 0.30), ("Additional", 0.20)
            ])
            findings = self._weighted_choice([(0, 0.50), (self._rng.randint(1, 3), 0.35), (self._rng.randint(4, 8), 0.15)])
            major = self._rng.randint(0, min(2, findings)) if findings > 2 else 0
            
            total_findings += findings
            major_nc += major
            
            audits.append({
                "audit_type": audit_type,
                "audit_date": self._random_date(1095, 30 * i),
                "findings": findings,
                "major_nonconformities": major,
                "observations": self._rng.randint(0, 5),
                "result": "Satisfactory" if major == 0 else "Conditional",
            })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("IMO", 7)),
            "doc_status": {
                "status": doc_status,
                "issue_date": self._random_date(1825, 365),
                "expiry_date": self._random_date(-365, -30) if doc_status == "Expired" else self._random_date(-30, 730),
                "issuing_authority": self._weighted_choice([
                    ("Panama Maritime Authority", 0.20), ("Liberia Maritime Authority", 0.15),
                    ("Marshall Islands Maritime", 0.15), ("Other", 0.50)
                ]),
            },
            "audit_history": {
                "total_audits_3yr": num_audits,
                "total_findings": total_findings,
                "major_nonconformities": major_nc,
                "audits": sorted(audits, key=lambda x: x["audit_date"], reverse=True),
            },
            "sms_status": {
                "documented": True,
                "last_review_date": self._random_date(365, 0),
                "drills_conducted_12mo": self._rng.randint(6, 24),
                "near_miss_reports_12mo": self._rng.randint(0, 15),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "doc_status": doc_status,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class FlagStatePerformanceExtractor(DataExtractor):
    """
    Flag State Performance - Paris/Tokyo MoU white/grey/black lists.
    
    Signals: flag_state, flag_state_quality
    
    Alternative Sources:
    - Paris MoU: performance/flags
    - Tokyo MoU: performance/flags
    - US Coast Guard: qualship21
    """
    source_name = "flag_state_performance"
    coverage = "marine"
    signals = ["flag_state", "flag_state_quality"]
    ttl_config = TTLConfig.semi_static("Flag state lists updated periodically")
    
    alternative_sources = [
        DataSource("api", "paris_mou", "performance/flags", priority=1),
        DataSource("api", "tokyo_mou", "performance/flags", priority=2),
        DataSource("api", "uscg", "qualship21", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        flag_state = self.kwargs.get("flag_state", self._weighted_choice([
            ("Panama", 0.18), ("Liberia", 0.15), ("Marshall Islands", 0.14),
            ("Singapore", 0.10), ("Hong Kong", 0.10), ("Malta", 0.08),
            ("Bahamas", 0.07), ("Cyprus", 0.05), ("Other", 0.13)
        ]))
        
        # Determine list color based on flag state
        white_list_flags = ["Singapore", "Hong Kong", "Denmark", "Norway", "Japan", "UK", "Germany", "Netherlands"]
        black_list_flags = ["Comoros", "Palau", "Togo", "Moldova", "Sierra Leone"]
        
        if flag_state in white_list_flags:
            list_color = "WHITE"
            detention_rate = round(self._rng.uniform(0.5, 2.5), 2)
        elif flag_state in black_list_flags:
            list_color = "BLACK"
            detention_rate = round(self._rng.uniform(8.0, 20.0), 2)
        else:
            list_color = self._weighted_choice([("WHITE", 0.50), ("GREY", 0.40), ("BLACK", 0.10)])
            detention_rate = round(self._rng.uniform(1.0, 8.0), 2)
        
        raw_data = {
            "flag_state": flag_state,
            "flag_code": flag_state[:3].upper(),
            "paris_mou_status": {
                "list_color": list_color,
                "detention_rate_pct": detention_rate,
                "deficiency_ratio": round(detention_rate * 1.5, 2),
                "inspection_count_3yr": self._rng.randint(100, 5000),
            },
            "tokyo_mou_status": {
                "list_color": list_color,
                "detention_rate_pct": detention_rate * self._rng.uniform(0.8, 1.2),
            },
            "qualship_21": {
                "eligible": list_color == "WHITE" and self._rng.random() > 0.3,
            },
            "imo_audit_status": {
                "audited": True,
                "last_audit_date": self._random_date(1825, 365),
                "significant_findings": self._rng.randint(0, 5),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "flag_state": flag_state,
                "list_color": list_color,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class PIClubExtractor(DataExtractor):
    """
    P&I Club Data - Club membership, claims history, coverage.
    
    Signals: pi_club, insurance_history
    
    Alternative Sources:
    - International Group: members/search
    - Individual P&I Club APIs
    """
    source_name = "pi_club"
    coverage = "marine"
    signals = ["pi_club", "insurance_history"]
    ttl_config = TTLConfig.semi_static("P&I membership updated weekly")
    
    alternative_sources = [
        DataSource("api", "ig_clubs", "members/search", priority=1),
        DataSource("scrape", "pi_club_websites", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        ig_clubs = [
            "Gard", "Britannia", "North P&I", "Standard Club", "UK P&I Club",
            "West of England", "Skuld", "American Club", "Japan P&I", "London P&I Club",
            "Swedish Club", "Steamship Mutual", "Shipowners' Club"
        ]
        
        is_ig_member = self._rng.random() > 0.15
        club_name = self._rng.choice(ig_clubs) if is_ig_member else f"Fixed Premium Insurer {self._random_id()}"
        club_type = "International Group" if is_ig_member else "Fixed Premium"
        
        # Claims history
        num_claims = self._weighted_choice([(0, 0.50), (self._rng.randint(1, 3), 0.35), (self._rng.randint(4, 10), 0.15)])
        total_incurred = 0
        claims = []
        
        for _ in range(num_claims):
            claim_amount = self._weighted_choice([
                (self._rng.randint(10000, 100000), 0.60),
                (self._rng.randint(100000, 500000), 0.25),
                (self._rng.randint(500000, 2000000), 0.10),
                (self._rng.randint(2000000, 10000000), 0.05),
            ])
            total_incurred += claim_amount
            claims.append({
                "claim_type": self._weighted_choice([
                    ("Cargo", 0.30), ("Personal Injury", 0.25), ("Collision", 0.15),
                    ("Pollution", 0.10), ("Wreck Removal", 0.08), ("Other", 0.12)
                ]),
                "claim_date": self._random_date(1825, 0),
                "incurred_amount_usd": claim_amount,
                "status": self._weighted_choice([("Open", 0.30), ("Closed", 0.70)]),
            })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("IMO", 7)),
            "membership": {
                "club_name": club_name,
                "club_type": club_type,
                "is_ig_member": is_ig_member,
                "member_since": self._random_date(7300, 365),
                "tonnage_entered": self._rng.randint(100000, 5000000),
            },
            "claims_history": {
                "total_claims_5yr": num_claims,
                "total_incurred_usd": total_incurred,
                "claims": sorted(claims, key=lambda x: x["claim_date"], reverse=True)[:10],
                "loss_ratio": round(total_incurred / max(self._rng.randint(500000, 5000000), 1), 3),
            },
            "coverage": {
                "p_and_i_limit_usd": 3_000_000_000 if is_ig_member else self._rng.randint(100_000_000, 500_000_000),
                "fdp_limit_usd": self._rng.randint(50_000_000, 500_000_000),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "is_ig_member": is_ig_member,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class MarineFinancialExtractor(DataExtractor):
    """
    Marine Financial Data - Revenue, leverage, credit metrics.
    
    Signals: credit_rating, leverage, financial_stability
    
    Alternative Sources:
    - SEC Edgar (if public)
    - Bloomberg
    - D&B
    - Marine Money
    """
    source_name = "marine_financial"
    coverage = "marine"
    signals = ["credit_rating", "leverage", "financial_stability"]
    ttl_config = TTLConfig.semi_static("Financial data updated weekly")
    
    alternative_sources = [
        DataSource("filing", "sec_edgar", "10-K", priority=1),
        DataSource("api", "bloomberg", "financials", priority=2),
        DataSource("api", "dnb", "company/financials", priority=3),
        DataSource("api", "marine_money", "transactions", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        revenue = self._weighted_choice([
            (self._rng.randint(10, 100) * 1_000_000, 0.40),
            (self._rng.randint(100, 500) * 1_000_000, 0.35),
            (self._rng.randint(500, 2000) * 1_000_000, 0.20),
            (self._rng.randint(2000, 10000) * 1_000_000, 0.05),
        ])
        
        ebitda_margin = self._rng.uniform(0.15, 0.45)
        ebitda = revenue * ebitda_margin
        
        debt_to_ebitda = self._weighted_choice([
            (self._rng.uniform(1.0, 3.0), 0.40),
            (self._rng.uniform(3.0, 5.0), 0.35),
            (self._rng.uniform(5.0, 8.0), 0.20),
            (self._rng.uniform(8.0, 12.0), 0.05),
        ])
        
        total_debt = ebitda * debt_to_ebitda
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 8)),
            "financials": {
                "revenue_usd": revenue,
                "ebitda_usd": ebitda,
                "ebitda_margin_pct": round(ebitda_margin * 100, 1),
                "net_income_usd": ebitda * self._rng.uniform(0.3, 0.7),
                "total_assets_usd": revenue * self._rng.uniform(2, 5),
                "fiscal_year_end": "2024-12-31",
            },
            "leverage": {
                "total_debt_usd": total_debt,
                "cash_usd": revenue * self._rng.uniform(0.05, 0.20),
                "net_debt_usd": total_debt - (revenue * self._rng.uniform(0.05, 0.20)),
            },
            "ratios": {
                "debt_to_ebitda": round(debt_to_ebitda, 2),
                "interest_coverage": round(self._rng.uniform(1.5, 8.0), 2),
                "current_ratio": round(self._rng.uniform(0.8, 2.5), 2),
            },
            "credit_profile": {
                "is_public": self._rng.random() > 0.70,
                "has_rating": self._rng.random() > 0.50,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class VesselValuationExtractor(DataExtractor):
    """
    Vessel Valuation Data - Market values, LTV ratios.
    
    Signals: fleet_value, ltv_ratio
    
    Alternative Sources:
    - VesselsValue
    - Clarksons: valuations
    - Baltic Exchange
    """
    source_name = "vessel_valuation"
    coverage = "marine"
    signals = ["fleet_value", "ltv_ratio"]
    ttl_config = TTLConfig.semi_static("Valuations updated weekly")
    
    alternative_sources = [
        DataSource("api", "vesselsvalue", "valuations/fleet", priority=1),
        DataSource("api", "clarksons", "valuations", priority=2),
        DataSource("api", "baltic_exchange", "indices", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        num_vessels = self._rng.randint(1, 50)
        vessels = []
        total_value = 0
        total_debt = 0
        
        for _ in range(num_vessels):
            vessel_type = self._weighted_choice([
                ("Container Ship", 0.25), ("Oil Tanker", 0.20), ("Bulk Carrier", 0.20),
                ("Chemical Tanker", 0.15), ("LNG Carrier", 0.10), ("Other", 0.10)
            ])
            
            # Value based on vessel type and age
            base_values = {
                "Container Ship": (30, 150), "Oil Tanker": (25, 120),
                "Bulk Carrier": (15, 60), "Chemical Tanker": (20, 80),
                "LNG Carrier": (150, 300), "Other": (10, 50)
            }
            low, high = base_values.get(vessel_type, (20, 80))
            market_value = self._rng.randint(low, high) * 1_000_000
            
            debt_pct = self._rng.uniform(0.40, 0.85)
            vessel_debt = market_value * debt_pct
            
            total_value += market_value
            total_debt += vessel_debt
            
            vessels.append({
                "vessel_type": vessel_type,
                "market_value_usd": market_value,
                "debt_usd": vessel_debt,
                "ltv_ratio": round(debt_pct, 3),
                "last_valuation_date": self._random_date(90, 0),
            })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 8)),
            "fleet_valuation": {
                "total_vessels": num_vessels,
                "total_fleet_value_usd": total_value,
                "average_vessel_value_usd": total_value // num_vessels,
                "valuation_date": self._random_date(30, 0),
            },
            "leverage": {
                "total_fleet_debt_usd": total_debt,
                "ltv_ratio": round(total_debt / total_value, 3) if total_value > 0 else 0,
            },
            "vessels": vessels[:20],
            "market_outlook": {
                "market_trend": self._weighted_choice([("Improving", 0.30), ("Stable", 0.45), ("Declining", 0.25)]),
                "value_change_12mo_pct": round(self._rng.uniform(-20, 30), 1),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "num_vessels": num_vessels,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class TradingPatternExtractor(DataExtractor):
    """
    Trading Pattern Analysis - Routes, regions, cargo types.
    
    Signals: trading_pattern, route_risk, geographic_exposure
    
    Alternative Sources:
    - MarineTraffic: routes/analysis
    - Spire: vessels/routes
    - ExactEarth: patterns/analysis
    """
    source_name = "trading_pattern"
    coverage = "marine"
    signals = ["trading_pattern", "route_risk", "geographic_exposure"]
    ttl_config = TTLConfig.dynamic("Trading patterns analyzed daily")
    
    alternative_sources = [
        DataSource("api", "marinetraffic", "routes/analysis", priority=1),
        DataSource("api", "spire", "vessels/routes", priority=2),
        DataSource("api", "exactearth", "patterns/analysis", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        trading_regions = ["Asia-Pacific", "Europe", "Americas", "Middle East", "Africa", "Global"]
        primary_region = self._weighted_choice([
            ("Asia-Pacific", 0.30), ("Europe", 0.20), ("Global", 0.20),
            ("Americas", 0.15), ("Middle East", 0.10), ("Africa", 0.05)
        ])
        
        route_types = ["Liner", "Tramp", "Industrial", "Mixed"]
        primary_route = self._weighted_choice([
            ("Liner", 0.25), ("Tramp", 0.40), ("Industrial", 0.20), ("Mixed", 0.15)
        ])
        
        # High risk area exposure
        high_risk_areas = ["Gulf of Aden", "Gulf of Guinea", "Strait of Malacca", "South China Sea"]
        exposed_areas = self._rng.sample(high_risk_areas, self._rng.randint(0, 3))
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 8)),
            "trading_pattern": {
                "primary_region": primary_region,
                "secondary_regions": self._rng.sample([r for r in trading_regions if r != primary_region], 2),
                "route_type": primary_route,
                "seasonal_pattern": self._weighted_choice([("Consistent", 0.60), ("Seasonal", 0.30), ("Opportunistic", 0.10)]),
            },
            "geographic_exposure": {
                "high_risk_areas": exposed_areas,
                "sanctioned_country_exposure": self._rng.random() < 0.05,
                "piracy_zone_transits_12mo": self._rng.randint(0, 20) if exposed_areas else 0,
            },
            "cargo_profile": {
                "primary_cargo": self._weighted_choice([
                    ("Containers", 0.25), ("Crude Oil", 0.15), ("Dry Bulk", 0.20),
                    ("Chemicals", 0.15), ("LNG", 0.10), ("General Cargo", 0.15)
                ]),
                "cargo_diversity": self._weighted_choice([("Single", 0.30), ("Diverse", 0.50), ("Specialized", 0.20)]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "primary_region": primary_region,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor  
class MarineVettingExtractor(DataExtractor):
    """
    Third-Party Vetting Data - RightShip, SIRE, CDI.
    
    Signals: vetting_score, inspection_quality
    
    Alternative Sources:
    - RightShip: vessels/score
    - OCIMF SIRE: reports/search
    - CDI: vessel_inspection/search
    """
    source_name = "vetting_scores"
    coverage = "marine"
    signals = ["vetting_score", "inspection_quality"]
    ttl_config = TTLConfig.semi_static("Vetting scores updated weekly")
    
    alternative_sources = [
        DataSource("api", "rightship", "vessels/score", priority=1),
        DataSource("api", "ocimf_sire", "reports/search", priority=2),
        DataSource("api", "cdp", "vessel_inspection/search", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        # RightShip score (0.5 to 5.0 stars)
        rightship_score = round(self._weighted_choice([
            (self._rng.uniform(4.0, 5.0), 0.30), (self._rng.uniform(3.0, 4.0), 0.40),
            (self._rng.uniform(2.0, 3.0), 0.20), (self._rng.uniform(0.5, 2.0), 0.10)
        ]), 1)
        
        # SIRE inspection
        sire_inspected = self._rng.random() > 0.30
        sire_observations = self._rng.randint(0, 25) if sire_inspected else None
        
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "rightship": {
                "score": rightship_score,
                "star_rating": int(rightship_score),
                "last_update": self._random_date(90, 0),
                "ghg_rating": self._weighted_choice([("A", 0.15), ("B", 0.25), ("C", 0.35), ("D", 0.20), ("E", 0.05)]),
            },
            "sire": {
                "inspected": sire_inspected,
                "last_inspection_date": self._random_date(365, 0) if sire_inspected else None,
                "total_observations": sire_observations,
                "negative_observations": self._rng.randint(0, min(10, sire_observations or 0)) if sire_observations else None,
            },
            "cdi": {
                "inspected": self._rng.random() > 0.50,
                "last_inspection_date": self._random_date(365, 0),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "rightship_score": rightship_score,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class MarineEnvironmentalExtractor(DataExtractor):
    """
    Environmental Compliance Data - CII, BWM, IMO 2020.
    
    Signals: cii_rating, bwm_compliance, imo2020_compliance, environmental_incident
    
    Alternative Sources:
    - IMO DCS: emissions/cii
    - Class Societies: vessels/cii
    - PSC databases
    """
    source_name = "marine_environmental"
    coverage = "marine"
    signals = ["cii_rating", "bwm_compliance", "imo2020_compliance", "environmental_incident"]
    ttl_config = TTLConfig.semi_static("Environmental data updated weekly")
    
    alternative_sources = [
        DataSource("api", "imo_dcs", "emissions/cii", priority=1),
        DataSource("api", "class_societies", "vessels/cii", priority=2),
        DataSource("api", "psc_databases", "deficiencies/marpol", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        cii_rating = self._weighted_choice([("A", 0.15), ("B", 0.25), ("C", 0.35), ("D", 0.20), ("E", 0.05)])
        
        bwm_compliant = self._rng.random() > 0.15
        imo2020_compliant = self._rng.random() > 0.05
        
        num_incidents = self._weighted_choice([(0, 0.85), (1, 0.10), (2, 0.04), (3, 0.01)])
        incidents = []
        for _ in range(num_incidents):
            incidents.append({
                "incident_date": self._random_date(1825, 0),
                "type": self._weighted_choice([
                    ("Oil Spill", 0.40), ("Chemical Discharge", 0.20),
                    ("Garbage Violation", 0.25), ("Air Emission", 0.15)
                ]),
                "severity": self._weighted_choice([("Minor", 0.60), ("Moderate", 0.30), ("Major", 0.10)]),
                "fine_usd": self._rng.randint(0, 500000) if self._rng.random() > 0.50 else 0,
            })
        
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "cii": {
                "rating": cii_rating,
                "attained_cii": round(self._rng.uniform(3, 15), 2),
                "required_cii": round(self._rng.uniform(5, 12), 2),
                "year": 2024,
                "trajectory": self._weighted_choice([("Improving", 0.40), ("Stable", 0.40), ("Declining", 0.20)]),
            },
            "bwm_compliance": {
                "compliant": bwm_compliant,
                "system_type": self._weighted_choice([("UV", 0.40), ("Electrochlorination", 0.35), ("Filtration", 0.25)]) if bwm_compliant else None,
                "compliance_date": self._random_date(1825, 365) if bwm_compliant else None,
            },
            "imo2020_compliance": {
                "compliant": imo2020_compliant,
                "method": self._weighted_choice([("LSFO", 0.70), ("Scrubber", 0.20), ("LNG", 0.10)]) if imo2020_compliant else "Non-compliant",
            },
            "environmental_incidents": {
                "total_5yr": num_incidents,
                "total_fines_usd": sum(i["fine_usd"] for i in incidents),
                "incidents": incidents,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "cii_rating": cii_rating,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class IndustryAssociationExtractor(DataExtractor):
    """
    Industry Association Membership - BIMCO, Intertanko, Intercargo.
    
    Signals: industry_association, charterer_quality
    
    Alternative Sources:
    - BIMCO: members
    - Intertanko: members
    - Intercargo: members
    """
    source_name = "industry_associations"
    coverage = "marine"
    signals = ["industry_association", "charterer_quality"]
    ttl_config = TTLConfig.static("Association membership changes rarely")
    
    alternative_sources = [
        DataSource("api", "bimco", "members", priority=1),
        DataSource("api", "intertanko", "members", priority=2),
        DataSource("api", "intercargo", "members", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        associations = ["BIMCO", "Intertanko", "Intercargo", "IMCA", "ICS"]
        member_of = [a for a in associations if self._rng.random() > 0.60]
        
        # Charterer relationships
        oil_majors = ["Shell", "BP", "ExxonMobil", "Chevron", "TotalEnergies", "Equinor"]
        commodity_traders = ["Trafigura", "Vitol", "Glencore", "Cargill", "Louis Dreyfus"]
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 8)),
            "memberships": {
                "associations": member_of,
                "total_memberships": len(member_of),
                "years_member": {a: self._rng.randint(1, 30) for a in member_of},
            },
            "charterer_relationships": {
                "oil_major_approved": self._rng.random() > 0.40,
                "approved_by": self._rng.sample(oil_majors, self._rng.randint(0, 3)),
                "commodity_trader_contracts": self._rng.sample(commodity_traders, self._rng.randint(0, 2)),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "memberships": len(member_of),
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CasualtyHistoryExtractor(DataExtractor):
    """
    Casualty and Incident History - Total losses, major incidents.
    
    Signals: casualty_history, total_loss
    
    Alternative Sources:
    - IHS Markit: casualties/search
    - Lloyd's List: casualties/search
    - IMO GISIS: casualties/search
    """
    source_name = "casualty_history"
    coverage = "marine"
    signals = ["casualty_history", "total_loss"]
    ttl_config = TTLConfig.dynamic("Casualty data updated daily")
    
    alternative_sources = [
        DataSource("api", "ihs_markit", "casualties/search", priority=1),
        DataSource("api", "lloyd_list", "casualties/search", priority=2),
        DataSource("api", "imo_gisis", "casualties/search", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        num_casualties = self._weighted_choice([(0, 0.75), (1, 0.15), (2, 0.07), (3, 0.03)])
        casualties = []
        
        casualty_types = [
            "Collision", "Grounding", "Fire/Explosion", "Machinery Failure",
            "Hull Failure", "Contact", "Flooding", "Foundering"
        ]
        
        for _ in range(num_casualties):
            severity = self._weighted_choice([("Minor", 0.50), ("Serious", 0.35), ("Very Serious", 0.12), ("Total Loss", 0.03)])
            casualties.append({
                "date": self._random_date(3650, 0),
                "type": self._rng.choice(casualty_types),
                "severity": severity,
                "location": f"{self._rng.uniform(-60, 60):.2f}, {self._rng.uniform(-180, 180):.2f}",
                "fatalities": self._rng.randint(0, 5) if severity in ("Very Serious", "Total Loss") else 0,
                "flag_state_investigation": severity != "Minor",
            })
        
        total_losses = sum(1 for c in casualties if c["severity"] == "Total Loss")
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 8)),
            "casualty_summary": {
                "total_casualties_10yr": num_casualties,
                "total_losses": total_losses,
                "fatalities": sum(c["fatalities"] for c in casualties),
                "by_severity": {s: sum(1 for c in casualties if c["severity"] == s) 
                              for s in ["Minor", "Serious", "Very Serious", "Total Loss"]},
            },
            "casualties": sorted(casualties, key=lambda x: x["date"], reverse=True),
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "casualties": num_casualties,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )

