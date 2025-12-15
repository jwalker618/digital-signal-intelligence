"""
DSI Technical Pricing Data Extraction Framework

This module provides stub extractors for ALL signals across all 7 coverage lines.
Each extractor simulates realistic API/data source outputs with seeded randomisation.

Coverage Lines & Signal Groups:
- Marine: 8 signal groups → 10+ extractors
- Aerospace: 7 signal groups → 9+ extractors  
- Cyber: 5 signal groups → 8+ extractors
- D&O: 6 signal groups → 8+ extractors
- Financial Institutions: 7 signal groups → 10+ extractors
- Energy: 7 signal groups → 9+ extractors
- Professional Indemnity: 7 signal groups → 9+ extractors
"""

from __future__ import annotations

import hashlib
import random
import string
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type, Tuple

# =============================================================================
# REGISTRY & BASE CLASSES
# =============================================================================

EXTRACTOR_REGISTRY: Dict[str, Type["DataExtractor"]] = {}


def register_extractor(cls: Type["DataExtractor"]) -> Type["DataExtractor"]:
    EXTRACTOR_REGISTRY[cls.__name__] = cls
    return cls


@dataclass
class ExtractionResult:
    source: str
    source_type: str
    timestamp: str
    raw_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class DataExtractor(ABC):
    def __init__(self, seed: Optional[str] = None, **kwargs: Any):
        self.seed = seed
        self.kwargs = kwargs
        self._rng = self._create_rng(seed)
    
    def _create_rng(self, seed: Optional[str]) -> random.Random:
        rng = random.Random()
        if seed:
            rng.seed(int(hashlib.md5(seed.encode()).hexdigest(), 16))
        return rng
    
    def _random_date(self, start_days_ago: int = 365, end_days_ago: int = 0) -> str:
        days_ago = self._rng.randint(min(end_days_ago, start_days_ago), max(end_days_ago, start_days_ago))
        return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    def _weighted_choice(self, choices: List[Tuple[Any, float]]) -> Any:
        items, weights = zip(*choices)
        return self._rng.choices(items, weights=weights, k=1)[0]
    
    def _random_id(self, prefix: str = "", length: int = 8) -> str:
        chars = string.ascii_uppercase + string.digits
        return f"{prefix}{''.join(self._rng.choices(chars, k=length))}"

    @abstractmethod
    def extract(self) -> ExtractionResult:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def coverage(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def signals(self) -> List[str]:
        raise NotImplementedError


# =============================================================================
# MARINE EXTRACTORS (10 extractors for 8 signal groups)
# =============================================================================

@register_extractor
class EquasisOperatorExtractor(DataExtractor):
    """Equasis API - fleet composition, ISM, company details. Signals: fleet_quality, management_quality"""
    source_name = "equasis"
    coverage = "marine"
    signals = ["fleet_quality", "management_quality"]

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
                "vessel_type": self._weighted_choice([("Container Ship", 0.25), ("Oil Tanker", 0.20), ("Bulk Carrier", 0.20), ("Chemical Tanker", 0.12), ("LNG Carrier", 0.08), ("General Cargo", 0.10), ("Other", 0.05)]),
                "gross_tonnage": self._rng.randint(5000, 180000),
                "build_year": build_year,
                "age_years": 2024 - build_year,
                "flag_state": self._weighted_choice([("Panama", 0.18), ("Liberia", 0.15), ("Marshall Islands", 0.14), ("Singapore", 0.10), ("Hong Kong", 0.10), ("Malta", 0.08), ("Bahamas", 0.07), ("Other", 0.18)]),
                "classification_society": self._weighted_choice([("DNV", 0.22), ("Lloyd's Register", 0.20), ("Bureau Veritas", 0.15), ("ABS", 0.15), ("ClassNK", 0.12), ("Other", 0.16)]),
            })
        raw_data = {
            "company": {
                "imo_company_number": self.kwargs.get("company_id", self._random_id("IMO", 7)),
                "company_name": self.kwargs.get("company_name", f"Maritime Operator {self._random_id()}"),
                "company_status": self._weighted_choice([("Active", 0.95), ("Inactive", 0.05)]),
                "role": self._weighted_choice([("Owner", 0.40), ("Operator", 0.35), ("Manager", 0.25)]),
            },
            "fleet": {"total_vessels": fleet_size, "vessels": vessels[:30], "average_age": round(sum(v["age_years"] for v in vessels) / len(vessels), 1) if vessels else 0},
            "ism_compliance": {
                "doc_status": self._weighted_choice([("Valid", 0.94), ("Expired", 0.03), ("Suspended", 0.02), ("Withdrawn", 0.01)]),
                "last_audit_date": self._random_date(365, 30),
                "audit_findings": self._rng.randint(0, 5) if self._rng.random() < 0.20 else 0,
            },
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"fleet_size": fleet_size})


@register_extractor
class PSCInspectionExtractor(DataExtractor):
    """Port State Control database - inspections, deficiencies, detentions. Signals: safety_compliance"""
    source_name = "psc_database"
    coverage = "marine"
    signals = ["safety_compliance"]

    def extract(self) -> ExtractionResult:
        num_inspections = self._rng.randint(3, 15)
        inspections = []
        total_deficiencies = 0
        total_detentions = 0
        for _ in range(num_inspections):
            deficiency_count = self._weighted_choice([(0, 0.35), (self._rng.randint(1, 3), 0.35), (self._rng.randint(4, 8), 0.20), (self._rng.randint(9, 15), 0.10)])
            detained = deficiency_count > 5 and self._rng.random() < 0.15
            total_deficiencies += deficiency_count
            total_detentions += 1 if detained else 0
            inspections.append({
                "inspection_date": self._random_date(1095, 0),
                "port": self._weighted_choice([("Rotterdam", 0.08), ("Singapore", 0.10), ("Shanghai", 0.08), ("Houston", 0.07), ("Other", 0.67)]),
                "psc_regime": self._weighted_choice([("Paris MoU", 0.30), ("Tokyo MoU", 0.25), ("US Coast Guard", 0.20), ("Other", 0.25)]),
                "deficiency_count": deficiency_count,
                "detained": detained,
                "detention_days": self._rng.randint(1, 10) if detained else 0,
            })
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "inspection_summary": {"total_inspections_3yr": num_inspections, "total_deficiencies_3yr": total_deficiencies, "total_detentions_3yr": total_detentions, "deficiency_ratio": round(total_deficiencies / num_inspections, 2)},
            "inspections": sorted(inspections, key=lambda x: x["inspection_date"], reverse=True),
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"inspections": num_inspections, "detentions": total_detentions})


@register_extractor
class AISTrackingExtractor(DataExtractor):
    """AIS tracking - position history, port calls, dark activity, STS events. Signals: operational_telemetry, sanctions_compliance"""
    source_name = "ais_tracking"
    coverage = "marine"
    signals = ["operational_telemetry", "sanctions_compliance"]

    def extract(self) -> ExtractionResult:
        num_port_calls = self._rng.randint(10, 40)
        port_calls = [{"port": f"Port_{self._random_id('', 4)}", "country": self._weighted_choice([("China", 0.15), ("Singapore", 0.10), ("USA", 0.10), ("Netherlands", 0.08), ("Other", 0.57)]), "arrival_date": self._random_date(365, 0)} for _ in range(num_port_calls)]
        
        ais_gaps = []
        num_gaps = self._weighted_choice([(0, 0.70), (1, 0.15), (2, 0.10), (self._rng.randint(3, 5), 0.05)])
        for _ in range(num_gaps):
            ais_gaps.append({"duration_hours": self._rng.randint(6, 168), "location_type": self._weighted_choice([("Coastal", 0.50), ("Open Ocean", 0.35), ("Anchorage", 0.15)]), "risk_level": self._weighted_choice([("Low", 0.60), ("Medium", 0.25), ("High", 0.12), ("Critical", 0.03)])})
        
        sts_events = []
        num_sts = self._weighted_choice([(0, 0.85), (1, 0.10), (2, 0.05)])
        for _ in range(num_sts):
            sts_events.append({"event_date": self._random_date(365, 0), "location_risk": self._weighted_choice([("Low", 0.70), ("Medium", 0.20), ("High", 0.10)])})
        
        sanctioned_exposure = self._rng.random() < 0.03
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "port_calls": {"total_12mo": num_port_calls, "unique_countries": len(set(p["country"] for p in port_calls)), "calls": port_calls[:20]},
            "ais_gaps": {"total_gaps_12mo": num_gaps, "high_risk_gaps": sum(1 for g in ais_gaps if g["risk_level"] in ("High", "Critical")), "gaps": ais_gaps},
            "sts_events": {"total_12mo": num_sts, "events": sts_events},
            "sanctions_exposure": {"sanctioned_area_visit": sanctioned_exposure, "high_risk_area_transits": self._rng.randint(0, 5)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"gaps": num_gaps, "sts": num_sts})


@register_extractor
class SanctionsScreeningExtractor(DataExtractor):
    """Sanctions screening - OFAC, EU, UN lists. Signals: sanctions_compliance"""
    source_name = "sanctions_screening"
    coverage = "marine"
    signals = ["sanctions_compliance"]

    def extract(self) -> ExtractionResult:
        has_hits = self._rng.random() < 0.08
        hits = []
        if has_hits:
            for _ in range(self._rng.randint(1, 3)):
                hits.append({"list_name": self._weighted_choice([("OFAC SDN", 0.30), ("EU Consolidated", 0.25), ("UN Security Council", 0.20), ("UK Sanctions", 0.15), ("Other", 0.10)]), "match_score": self._rng.randint(60, 100), "status": self._weighted_choice([("Active", 0.80), ("Cleared", 0.15), ("Under Review", 0.05)])})
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 8)),
            "screening_result": {"status": "HIT" if hits else "CLEAR", "total_hits": len(hits), "hits": hits},
            "ownership_flags": {"high_risk_jurisdiction": self._rng.random() < 0.05, "complex_structure": self._rng.random() < 0.10},
            "risk_score": round(100 - len(hits) * 25 - (10 if self._rng.random() < 0.05 else 0), 1),
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"hits": len(hits)})


@register_extractor
class ClassificationSocietyExtractor(DataExtractor):
    """Classification society - class status, surveys, conditions. Signals: classification_quality, safety_compliance"""
    source_name = "classification_society"
    coverage = "marine"
    signals = ["classification_quality", "safety_compliance"]

    def extract(self) -> ExtractionResult:
        class_status = self._weighted_choice([("In Class", 0.92), ("Suspended", 0.03), ("Withdrawn", 0.02), ("Laid Up", 0.03)])
        num_conditions = self._weighted_choice([(0, 0.70), (1, 0.15), (2, 0.08), (self._rng.randint(3, 6), 0.07)])
        conditions = [{"category": self._weighted_choice([("Hull", 0.30), ("Machinery", 0.30), ("Safety", 0.20), ("Other", 0.20)]), "severity": self._weighted_choice([("Minor", 0.50), ("Moderate", 0.35), ("Major", 0.15)]), "status": self._weighted_choice([("Outstanding", 0.40), ("Completed", 0.50), ("Overdue", 0.10)])} for _ in range(num_conditions)]
        
        surveys = [{"survey_type": self._weighted_choice([("Annual", 0.40), ("Intermediate", 0.25), ("Special", 0.20), ("Bottom", 0.15)]), "date": self._random_date(1095, 0), "result": self._weighted_choice([("Satisfactory", 0.85), ("Conditional", 0.12), ("Unsatisfactory", 0.03)])} for _ in range(self._rng.randint(3, 10))]
        
        raw_data = {
            "vessel_imo": self.kwargs.get("vessel_imo", str(self._rng.randint(9000000, 9999999))),
            "classification": {"society_name": self._weighted_choice([("DNV", 0.22), ("Lloyd's Register", 0.20), ("Bureau Veritas", 0.15), ("ABS", 0.15), ("ClassNK", 0.12), ("Other", 0.16)]), "class_status": class_status, "entry_date": self._random_date(7300, 365)},
            "conditions_of_class": {"total": num_conditions, "outstanding": sum(1 for c in conditions if c["status"] == "Outstanding"), "overdue": sum(1 for c in conditions if c["status"] == "Overdue"), "conditions": conditions},
            "survey_history": {"compliance_rate": round(sum(1 for s in surveys if s["result"] == "Satisfactory") / len(surveys), 3) if surveys else 1.0, "surveys": surveys},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"class_status": class_status, "conditions": num_conditions})


@register_extractor
class PIClubExtractor(DataExtractor):
    """P&I Club data - membership, claims, coverage. Signals: p_and_i_quality"""
    source_name = "pi_club"
    coverage = "marine"
    signals = ["p_and_i_quality"]

    def extract(self) -> ExtractionResult:
        is_ig = self._rng.random() < 0.85
        club_name = self._weighted_choice([("Gard", 0.15), ("Britannia", 0.12), ("UK Club", 0.11), ("North", 0.10), ("Standard", 0.10), ("West of England", 0.09), ("Skuld", 0.08), ("Other IG", 0.10), ("Fixed Premium", 0.15)])
        
        num_claims = self._weighted_choice([(0, 0.40), (self._rng.randint(1, 3), 0.35), (self._rng.randint(4, 8), 0.18), (self._rng.randint(9, 15), 0.07)])
        claims = [{"claim_type": self._weighted_choice([("Cargo", 0.25), ("Personal Injury", 0.20), ("Pollution", 0.10), ("Collision", 0.10), ("Crew", 0.15), ("Other", 0.20)]), "incurred_usd": self._rng.randint(10000, 5000000), "status": self._weighted_choice([("Closed", 0.60), ("Open", 0.30), ("Reserved", 0.10)])} for _ in range(num_claims)]
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("IMO", 7)),
            "membership": {"club_name": club_name, "club_type": "International Group" if is_ig else "Fixed Premium", "status": self._weighted_choice([("Active", 0.95), ("Suspended", 0.03), ("Terminated", 0.02)]), "member_since": self._random_date(7300, 365)},
            "claims_history": {"total_claims_5yr": num_claims, "total_incurred_usd": sum(c["incurred_usd"] for c in claims), "claims": claims},
            "coverage": {"limit_usd": self._weighted_choice([(500000000, 0.30), (1000000000, 0.40), (3000000000, 0.20), (float("inf"), 0.10)]), "deductible_usd": self._weighted_choice([(25000, 0.30), (50000, 0.35), (100000, 0.25), (250000, 0.10)])},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"club": club_name, "claims": num_claims})


@register_extractor
class MarineFinancialExtractor(DataExtractor):
    """Marine operator financials. Signals: financial_stability"""
    source_name = "marine_financial"
    coverage = "marine"
    signals = ["financial_stability"]

    def extract(self) -> ExtractionResult:
        revenue = self._weighted_choice([(self._rng.randint(10_000_000, 100_000_000), 0.35), (self._rng.randint(100_000_001, 500_000_000), 0.30), (self._rng.randint(500_000_001, 2_000_000_000), 0.25), (self._rng.randint(2_000_000_001, 10_000_000_000), 0.10)])
        ebitda_margin = self._rng.uniform(0.08, 0.30)
        debt_to_ebitda = self._rng.uniform(2.0, 7.0)
        
        has_rating = self._rng.random() < 0.30
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("IMO", 7)),
            "financials": {"revenue_usd": revenue, "ebitda_usd": int(revenue * ebitda_margin), "ebitda_margin_pct": round(ebitda_margin * 100, 1), "total_debt_usd": int(revenue * ebitda_margin * debt_to_ebitda)},
            "ratios": {"debt_to_ebitda": round(debt_to_ebitda, 2), "interest_coverage": round(self._rng.uniform(1.5, 5.0), 2), "current_ratio": round(self._rng.uniform(0.9, 2.2), 2)},
            "credit": {"has_rating": has_rating, "rating": self._weighted_choice([("BBB", 0.25), ("BB+", 0.25), ("BB", 0.25), ("B+", 0.15), ("B", 0.10)]) if has_rating else None},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"revenue": revenue})


@register_extractor
class ISMComplianceExtractor(DataExtractor):
    """ISM Code compliance - DOC, audits, findings. Signals: management_quality, safety_compliance"""
    source_name = "ism_compliance"
    coverage = "marine"
    signals = ["management_quality", "safety_compliance"]

    def extract(self) -> ExtractionResult:
        doc_status = self._weighted_choice([("Valid", 0.92), ("Expired", 0.04), ("Suspended", 0.02), ("Withdrawn", 0.02)])
        num_audits = self._rng.randint(2, 6)
        audits = [{"audit_date": self._random_date(1095, 0), "audit_type": self._weighted_choice([("Initial", 0.15), ("Annual", 0.50), ("Intermediate", 0.25), ("Renewal", 0.10)]), "findings": self._weighted_choice([(0, 0.50), (self._rng.randint(1, 3), 0.35), (self._rng.randint(4, 8), 0.15)]), "major_nonconformities": self._weighted_choice([(0, 0.85), (1, 0.12), (2, 0.03)])} for _ in range(num_audits)]
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("IMO", 7)),
            "doc_status": {"status": doc_status, "issuing_authority": self._weighted_choice([("Panama", 0.20), ("Liberia", 0.18), ("Marshall Islands", 0.15), ("Singapore", 0.12), ("Other", 0.35)]), "expiry_date": self._random_date(-30, -730)},
            "audit_history": {"total_audits_3yr": num_audits, "total_findings": sum(a["findings"] for a in audits), "major_nonconformities": sum(a["major_nonconformities"] for a in audits), "audits": audits},
            "sms_status": {"documented": True, "last_review_date": self._random_date(365, 0), "drills_conducted_12mo": self._rng.randint(6, 24)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"doc_status": doc_status})


@register_extractor
class VesselValuationExtractor(DataExtractor):
    """Vessel/fleet valuation - market values, LTV. Signals: fleet_quality, financial_stability"""
    source_name = "vessel_valuation"
    coverage = "marine"
    signals = ["fleet_quality", "financial_stability"]

    def extract(self) -> ExtractionResult:
        fleet_size = self._rng.randint(1, 50)
        avg_value = self._rng.randint(15_000_000, 120_000_000)
        total_value = fleet_size * avg_value
        total_debt = int(total_value * self._rng.uniform(0.40, 0.75))
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("IMO", 7)),
            "fleet_valuation": {"vessel_count": fleet_size, "total_value_usd": total_value, "average_value_usd": avg_value, "valuation_date": self._random_date(90, 0), "source": self._weighted_choice([("VesselsValue", 0.40), ("Clarksons", 0.35), ("Baltic Exchange", 0.15), ("Internal", 0.10)])},
            "leverage": {"total_debt_usd": total_debt, "ltv_ratio": round(total_debt / total_value, 3), "unencumbered_vessels": self._rng.randint(0, fleet_size // 3)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"fleet_value": total_value})


@register_extractor
class FlagStatePerformanceExtractor(DataExtractor):
    """Flag state quality metrics - Paris MoU performance. Signals: fleet_quality"""
    source_name = "flag_state_performance"
    coverage = "marine"
    signals = ["fleet_quality"]

    def extract(self) -> ExtractionResult:
        flag_state = self.kwargs.get("flag_state", self._weighted_choice([("Panama", 0.18), ("Liberia", 0.15), ("Marshall Islands", 0.14), ("Singapore", 0.10), ("Hong Kong", 0.10), ("Malta", 0.08), ("Bahamas", 0.07), ("Other", 0.18)]))
        
        # Simplified flag state categorization
        white_flags = ["Singapore", "Hong Kong", "United Kingdom", "Norway", "Denmark", "Netherlands", "Japan"]
        grey_flags = ["Panama", "Liberia", "Marshall Islands", "Malta", "Bahamas", "Cyprus"]
        
        if flag_state in white_flags:
            list_color = "WHITE"
            detention_rate = self._rng.uniform(0.5, 2.0)
        elif flag_state in grey_flags:
            list_color = "GREY"
            detention_rate = self._rng.uniform(2.0, 4.0)
        else:
            list_color = self._weighted_choice([("WHITE", 0.30), ("GREY", 0.50), ("BLACK", 0.20)])
            detention_rate = self._rng.uniform(1.0, 6.0)
        
        raw_data = {
            "flag_state": flag_state,
            "paris_mou_status": {"list_color": list_color, "detention_rate_pct": round(detention_rate, 2), "deficiency_rate": round(self._rng.uniform(1.0, 5.0), 2)},
            "iacs_member_class_required": list_color != "BLACK",
            "recognized_organizations": self._rng.randint(5, 15),
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"flag": flag_state, "list": list_color})


# =============================================================================
# AEROSPACE EXTRACTORS (9 extractors for 7 signal groups)
# =============================================================================

@register_extractor
class IATAOperatorExtractor(DataExtractor):
    """IATA registry - IOSA status, operator profile. Signals: safety_record, regulatory_compliance"""
    source_name = "iata_registry"
    coverage = "aerospace"
    signals = ["safety_record", "regulatory_compliance"]

    def extract(self) -> ExtractionResult:
        iosa_registered = self._rng.random() < 0.75
        fleet_size = self._weighted_choice([(self._rng.randint(1, 10), 0.30), (self._rng.randint(11, 50), 0.35), (self._rng.randint(51, 200), 0.25), (self._rng.randint(201, 500), 0.10)])
        
        raw_data = {
            "operator": {"operator_id": self.kwargs.get("operator_id", self._random_id("AOC", 6)), "legal_name": self.kwargs.get("operator_name", f"Airways {self._random_id()}"), "iata_code": self._random_id("", 2).upper(), "icao_code": self._random_id("", 3).upper(), "country": self._weighted_choice([("United States", 0.20), ("China", 0.12), ("India", 0.08), ("United Kingdom", 0.06), ("UAE", 0.05), ("Other", 0.49)])},
            "iosa": {"registered": iosa_registered, "status": self._weighted_choice([("Registered", 0.90), ("Renewal Pending", 0.05), ("Expired", 0.05)]) if iosa_registered else "Not Registered", "last_audit_date": self._random_date(730, 30) if iosa_registered else None, "findings_count": self._rng.randint(0, 15) if iosa_registered else None},
            "regulatory": {"aoc_status": self._weighted_choice([("Valid", 0.95), ("Suspended", 0.02), ("Revoked", 0.01), ("Pending", 0.02)]), "primary_regulator": self._weighted_choice([("FAA", 0.30), ("EASA", 0.25), ("CAAC", 0.12), ("DGCA", 0.08), ("Other", 0.25)])},
            "fleet": {"total_aircraft": fleet_size, "average_age": round(self._rng.uniform(5, 18), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"iosa": iosa_registered})


@register_extractor
class AviationSafetyExtractor(DataExtractor):
    """Aviation safety databases - accidents, incidents, fatalities. Signals: safety_record"""
    source_name = "aviation_safety"
    coverage = "aerospace"
    signals = ["safety_record"]

    def extract(self) -> ExtractionResult:
        accidents_5yr = self._weighted_choice([(0, 0.82), (1, 0.12), (2, 0.04), (self._rng.randint(3, 5), 0.02)])
        incidents_5yr = self._weighted_choice([(0, 0.45), (self._rng.randint(1, 3), 0.35), (self._rng.randint(4, 8), 0.15), (self._rng.randint(9, 15), 0.05)])
        fatalities = self._rng.randint(0, accidents_5yr * 80) if accidents_5yr > 0 else 0
        hull_losses = min(accidents_5yr, self._rng.randint(0, accidents_5yr + 1))
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("AOC", 6)),
            "safety_record_5yr": {"accidents": accidents_5yr, "incidents": incidents_5yr, "fatalities": fatalities, "hull_losses": hull_losses, "serious_incidents": self._rng.randint(0, incidents_5yr)},
            "rates": {"accident_rate_per_million_flights": round(accidents_5yr / max(1, self._rng.randint(100, 1000)) * 1000000, 4), "incident_rate_per_million_flights": round(incidents_5yr / max(1, self._rng.randint(100, 1000)) * 1000000, 4)},
            "last_event": {"date": self._random_date(1825, 0) if accidents_5yr > 0 else None, "type": self._weighted_choice([("Ground Damage", 0.30), ("Runway Excursion", 0.20), ("Bird Strike", 0.15), ("Turbulence Injury", 0.15), ("Other", 0.20)]) if accidents_5yr > 0 else None},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"accidents": accidents_5yr, "fatalities": fatalities})


@register_extractor
class FAARegistryExtractor(DataExtractor):
    """FAA registry - aircraft registration, AD compliance, enforcement. Signals: regulatory_compliance, fleet_quality"""
    source_name = "faa_registry"
    coverage = "aerospace"
    signals = ["regulatory_compliance", "fleet_quality"]

    def extract(self) -> ExtractionResult:
        num_aircraft = self._rng.randint(1, 150)
        enforcement_actions = self._weighted_choice([(0, 0.75), (1, 0.15), (self._rng.randint(2, 5), 0.08), (self._rng.randint(6, 10), 0.02)])
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 8)),
            "registrations": {"total_aircraft": num_aircraft, "average_age": round(self._rng.uniform(5, 20), 1)},
            "airworthiness_directives": {"total_applicable": self._rng.randint(50, 300), "complied": self._rng.randint(48, 298), "overdue": self._weighted_choice([(0, 0.85), (self._rng.randint(1, 3), 0.12), (self._rng.randint(4, 8), 0.03)])},
            "enforcement": {"total_actions_5yr": enforcement_actions, "total_penalties_usd": enforcement_actions * self._rng.randint(5000, 75000), "certificate_actions": self._rng.randint(0, enforcement_actions // 2 + 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"aircraft": num_aircraft, "enforcement": enforcement_actions})


@register_extractor
class AircraftFleetExtractor(DataExtractor):
    """Aircraft fleet data - types, ages, engines, ownership. Signals: fleet_quality"""
    source_name = "aircraft_fleet"
    coverage = "aerospace"
    signals = ["fleet_quality"]

    def extract(self) -> ExtractionResult:
        fleet_size = self._weighted_choice([(self._rng.randint(1, 10), 0.30), (self._rng.randint(11, 50), 0.35), (self._rng.randint(51, 150), 0.25), (self._rng.randint(151, 400), 0.10)])
        aircraft = []
        for _ in range(min(fleet_size, 30)):
            build_year = self._rng.randint(2000, 2024)
            aircraft.append({
                "type": self._weighted_choice([("Boeing 737", 0.25), ("Airbus A320", 0.25), ("Boeing 777", 0.10), ("Airbus A330", 0.08), ("Boeing 787", 0.07), ("Embraer E-Jet", 0.08), ("Other", 0.17)]),
                "build_year": build_year,
                "age": 2024 - build_year,
                "engine_type": self._weighted_choice([("CFM56", 0.25), ("CFM LEAP", 0.20), ("PW1000G", 0.15), ("GE90", 0.10), ("Trent", 0.10), ("Other", 0.20)]),
                "ownership": self._weighted_choice([("Owned", 0.35), ("Operating Lease", 0.45), ("Finance Lease", 0.15), ("Wet Lease", 0.05)]),
            })
        avg_age = round(sum(a["age"] for a in aircraft) / len(aircraft), 1) if aircraft else 0
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "fleet_summary": {"total_aircraft": fleet_size, "active": int(fleet_size * 0.92), "average_age": avg_age, "owned_pct": round(sum(1 for a in aircraft if a["ownership"] == "Owned") / len(aircraft) * 100, 1) if aircraft else 0},
            "aircraft": aircraft,
            "fleet_composition": {"narrowbody_pct": round(sum(1 for a in aircraft if "737" in a["type"] or "A320" in a["type"]) / len(aircraft) * 100, 1) if aircraft else 0},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"fleet_size": fleet_size, "avg_age": avg_age})


@register_extractor
class MROProviderExtractor(DataExtractor):
    """MRO provider data - maintenance quality, findings. Signals: maintenance_quality"""
    source_name = "mro_provider"
    coverage = "aerospace"
    signals = ["maintenance_quality"]

    def extract(self) -> ExtractionResult:
        mro_relationships = []
        for _ in range(self._rng.randint(1, 4)):
            mro_relationships.append({
                "mro_name": self._weighted_choice([("Lufthansa Technik", 0.15), ("ST Aerospace", 0.12), ("HAECO", 0.10), ("AAR Corp", 0.10), ("AFI KLM E&M", 0.08), ("In-House", 0.20), ("Other", 0.25)]),
                "tier": self._weighted_choice([("OEM Affiliated", 0.20), ("Major Independent", 0.35), ("Regional", 0.30), ("In-House", 0.15)]),
                "contract_type": self._weighted_choice([("Flight Hour Agreement", 0.30), ("Time & Material", 0.35), ("Power by Hour", 0.20), ("Fixed Price", 0.15)]),
                "audit_result": self._weighted_choice([("Satisfactory", 0.85), ("Satisfactory with Findings", 0.12), ("Unsatisfactory", 0.03)]),
            })
        
        num_events = self._rng.randint(20, 150)
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "mro_relationships": mro_relationships,
            "maintenance_summary": {"events_12mo": num_events, "on_time_rate": round(self._rng.uniform(0.82, 0.98), 3), "avg_findings_per_event": round(self._rng.uniform(0.5, 3.5), 2), "unscheduled_events_pct": round(self._rng.uniform(5, 20), 1)},
            "quality_metrics": {"aog_events_12mo": self._rng.randint(0, 15), "repeat_discrepancies_pct": round(self._rng.uniform(1, 8), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"mro_count": len(mro_relationships)})


@register_extractor
class CrewTrainingExtractor(DataExtractor):
    """Crew training and qualifications. Signals: crew_quality"""
    source_name = "crew_training"
    coverage = "aerospace"
    signals = ["crew_quality"]

    def extract(self) -> ExtractionResult:
        num_pilots = self._weighted_choice([(self._rng.randint(20, 100), 0.40), (self._rng.randint(101, 500), 0.35), (self._rng.randint(501, 2000), 0.20), (self._rng.randint(2001, 10000), 0.05)])
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "pilot_roster": {"total_pilots": num_pilots, "captains": int(num_pilots * self._rng.uniform(0.38, 0.48)), "average_total_hours": self._rng.randint(6000, 14000), "average_type_hours": self._rng.randint(1500, 7000), "pilots_under_1500_hrs": int(num_pilots * self._rng.uniform(0.02, 0.12))},
            "training_compliance": {"recurrent_current_pct": round(self._rng.uniform(96, 100), 1), "line_checks_current_pct": round(self._rng.uniform(95, 100), 1), "medical_current_pct": round(self._rng.uniform(98, 100), 1)},
            "training_metrics": {"pass_rate_pct": round(self._rng.uniform(92, 99), 1), "additional_training_rate_pct": round(self._rng.uniform(2, 8), 1), "check_airmen_ratio": round(self._rng.uniform(0.05, 0.12), 3)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"pilots": num_pilots})


@register_extractor
class OperationalPerformanceExtractor(DataExtractor):
    """Operational performance - OTP, dispatch reliability. Signals: operational_quality"""
    source_name = "operational_performance"
    coverage = "aerospace"
    signals = ["operational_quality"]

    def extract(self) -> ExtractionResult:
        otp = round(self._rng.uniform(70, 92), 1)
        dispatch_reliability = round(self._rng.uniform(97, 99.8), 2)
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "performance_12mo": {"on_time_performance_pct": otp, "dispatch_reliability_pct": dispatch_reliability, "completion_factor_pct": round(self._rng.uniform(98, 99.9), 2), "cancellation_rate_pct": round(self._rng.uniform(0.5, 3.0), 2)},
            "operational_metrics": {"daily_utilization_hours": round(self._rng.uniform(8, 14), 1), "turnaround_time_avg_min": self._rng.randint(25, 55), "flights_per_day": self._rng.randint(50, 1500)},
            "delays": {"avg_delay_min": self._rng.randint(10, 45), "controllable_delays_pct": round(self._rng.uniform(20, 50), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"otp": otp})


@register_extractor
class AviationFinancialExtractor(DataExtractor):
    """Aviation operator financials. Signals: financial_stability"""
    source_name = "aviation_financial"
    coverage = "aerospace"
    signals = ["financial_stability"]

    def extract(self) -> ExtractionResult:
        fleet_size = self._rng.randint(5, 200)
        revenue = fleet_size * self._rng.randint(8_000_000, 25_000_000)
        ebitdar_margin = self._rng.uniform(0.12, 0.28)
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "financials": {"revenue_usd": revenue, "ebitdar_usd": int(revenue * ebitdar_margin), "ebitdar_margin_pct": round(ebitdar_margin * 100, 1)},
            "leverage": {"total_debt_usd": int(revenue * self._rng.uniform(0.5, 1.5)), "lease_adjusted_debt_usd": int(revenue * self._rng.uniform(1.0, 3.0)), "cash_usd": int(revenue * self._rng.uniform(0.05, 0.20))},
            "credit": {"has_rating": self._rng.random() < 0.35, "rating": self._weighted_choice([("BB+", 0.20), ("BB", 0.25), ("BB-", 0.20), ("B+", 0.20), ("B", 0.15)]) if self._rng.random() < 0.35 else None},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"revenue": revenue})


# =============================================================================
# CYBER EXTRACTORS (8 extractors for 5 signal groups)
# =============================================================================

@register_extractor
class SecurityScorecardExtractor(DataExtractor):
    """External security ratings - overall score, factor scores. Signals: technical_infrastructure"""
    source_name = "security_scorecard"
    coverage = "cyber"
    signals = ["technical_infrastructure"]

    def extract(self) -> ExtractionResult:
        overall_score = self._weighted_choice([(self._rng.randint(85, 100), 0.15), (self._rng.randint(70, 84), 0.30), (self._rng.randint(55, 69), 0.30), (self._rng.randint(40, 54), 0.18), (self._rng.randint(20, 39), 0.07)])
        grade = "A" if overall_score >= 85 else "B" if overall_score >= 70 else "C" if overall_score >= 55 else "D" if overall_score >= 40 else "F"
        
        factors = [{"factor": f, "score": max(0, min(100, overall_score + self._rng.randint(-15, 15))), "issues": self._rng.randint(0, 20)} for f in ["Network Security", "DNS Health", "Patching Cadence", "Endpoint Security", "IP Reputation", "Web App Security", "Leaked Credentials", "Hacker Chatter"]]
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("SSC", 8)),
            "company_name": self.kwargs.get("company_name", f"Company {self._random_id()}"),
            "overall_rating": {"score": overall_score, "grade": grade, "percentile": self._rng.randint(max(1, overall_score - 15), min(99, overall_score + 10))},
            "factor_scores": factors,
            "trend": self._weighted_choice([("Improving", 0.30), ("Stable", 0.50), ("Declining", 0.20)]),
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"score": overall_score, "grade": grade})


@register_extractor
class CVEExposureExtractor(DataExtractor):
    """CVE vulnerability scanning. Signals: technical_infrastructure"""
    source_name = "cve_scanner"
    coverage = "cyber"
    signals = ["technical_infrastructure"]

    def extract(self) -> ExtractionResult:
        num_vulns = self._weighted_choice([(self._rng.randint(0, 20), 0.35), (self._rng.randint(21, 80), 0.35), (self._rng.randint(81, 200), 0.20), (self._rng.randint(201, 500), 0.10)])
        critical = int(num_vulns * self._rng.uniform(0.02, 0.10))
        high = int(num_vulns * self._rng.uniform(0.10, 0.25))
        
        raw_data = {
            "target_id": self.kwargs.get("target_id", self._random_id("TGT", 8)),
            "scan_date": self._random_date(14, 0),
            "vulnerability_summary": {"total": num_vulns, "critical": critical, "high": high, "medium": int(num_vulns * 0.35), "low": num_vulns - critical - high - int(num_vulns * 0.35)},
            "exploitability": {"exploitable_count": int(num_vulns * self._rng.uniform(0.15, 0.35)), "actively_exploited": self._rng.randint(0, critical)},
            "remediation": {"mttr_critical_days": self._rng.randint(5, 45), "mttr_high_days": self._rng.randint(15, 60), "patch_compliance_pct": round(self._rng.uniform(65, 98), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"vulns": num_vulns, "critical": critical})


@register_extractor
class BreachDatabaseExtractor(DataExtractor):
    """Breach history database. Signals: public_record"""
    source_name = "breach_database"
    coverage = "cyber"
    signals = ["public_record"]

    def extract(self) -> ExtractionResult:
        num_breaches = self._weighted_choice([(0, 0.65), (1, 0.20), (2, 0.10), (self._rng.randint(3, 6), 0.05)])
        breaches = []
        for _ in range(num_breaches):
            records = self._weighted_choice([(self._rng.randint(100, 10000), 0.45), (self._rng.randint(10001, 100000), 0.30), (self._rng.randint(100001, 1000000), 0.18), (self._rng.randint(1000001, 50000000), 0.07)])
            breaches.append({"breach_type": self._weighted_choice([("Hacking", 0.35), ("Ransomware", 0.25), ("Credential Leak", 0.20), ("Insider", 0.10), ("Other", 0.10)]), "records_affected": records, "date": self._random_date(1825, 30), "regulatory_fine_usd": self._weighted_choice([(0, 0.60), (self._rng.randint(10000, 500000), 0.25), (self._rng.randint(500001, 5000000), 0.12), (self._rng.randint(5000001, 50000000), 0.03)])})
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CMP", 8)),
            "breach_history": {"total_breaches_5yr": num_breaches, "total_records_exposed": sum(b["records_affected"] for b in breaches), "total_fines_usd": sum(b["regulatory_fine_usd"] for b in breaches), "breaches": breaches},
            "litigation": {"class_actions": sum(1 for b in breaches if b["records_affected"] > 100000 and self._rng.random() < 0.30), "regulatory_investigations": sum(1 for b in breaches if b["regulatory_fine_usd"] > 0)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"breaches": num_breaches})


@register_extractor
class CyberGovernanceExtractor(DataExtractor):
    """Cyber governance assessment - CISO, certifications, policies. Signals: governance"""
    source_name = "cyber_governance"
    coverage = "cyber"
    signals = ["governance"]

    def extract(self) -> ExtractionResult:
        has_ciso = self._rng.random() < 0.72
        certifications = []
        for cert in ["SOC 2 Type II", "ISO 27001", "PCI DSS", "HITRUST", "FedRAMP"]:
            if self._rng.random() < 0.35:
                certifications.append({"certification": cert, "status": self._weighted_choice([("Current", 0.85), ("Expired", 0.08), ("In Progress", 0.07)]), "scope": self._weighted_choice([("Enterprise-wide", 0.55), ("Specific Systems", 0.35), ("Business Unit", 0.10)])})
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CMP", 8)),
            "leadership": {"has_ciso": has_ciso, "ciso_reports_to": self._weighted_choice([("CEO", 0.30), ("CIO", 0.35), ("CTO", 0.15), ("CFO", 0.10), ("Board", 0.10)]) if has_ciso else None, "security_team_size": self._weighted_choice([(self._rng.randint(1, 5), 0.40), (self._rng.randint(6, 20), 0.35), (self._rng.randint(21, 50), 0.18), (self._rng.randint(51, 200), 0.07)]), "board_cyber_oversight": self._rng.random() < 0.58},
            "certifications": certifications,
            "policies": {"incident_response_plan": self._rng.random() < 0.82, "business_continuity_plan": self._rng.random() < 0.78, "security_awareness_training": self._rng.random() < 0.88, "pen_test_frequency": self._weighted_choice([("Annual", 0.35), ("Semi-Annual", 0.30), ("Quarterly", 0.20), ("Continuous", 0.08), ("None", 0.07)])},
            "maturity": {"level": self._weighted_choice([(1, 0.10), (2, 0.25), (3, 0.40), (4, 0.20), (5, 0.05)]), "framework": self._weighted_choice([("NIST CSF", 0.45), ("ISO 27001", 0.25), ("CIS Controls", 0.15), ("Internal", 0.15)])},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"has_ciso": has_ciso, "certs": len(certifications)})


@register_extractor
class VendorSecurityExtractor(DataExtractor):
    """Third-party vendor risk management. Signals: vendor_management"""
    source_name = "vendor_security"
    coverage = "cyber"
    signals = ["vendor_management"]

    def extract(self) -> ExtractionResult:
        num_vendors = self._weighted_choice([(self._rng.randint(20, 100), 0.35), (self._rng.randint(101, 300), 0.35), (self._rng.randint(301, 800), 0.20), (self._rng.randint(801, 2000), 0.10)])
        critical = int(num_vendors * self._rng.uniform(0.05, 0.12))
        high_risk = int(num_vendors * self._rng.uniform(0.10, 0.22))
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CMP", 8)),
            "vendor_inventory": {"total": num_vendors, "critical": critical, "high_risk": high_risk, "medium_risk": int(num_vendors * 0.35), "low_risk": num_vendors - critical - high_risk - int(num_vendors * 0.35)},
            "assessment_coverage": {"assessed_12mo_pct": round(self._rng.uniform(55, 95), 1), "critical_assessed_pct": round(self._rng.uniform(85, 100), 1), "average_score": self._rng.randint(60, 90)},
            "risk_metrics": {"vendors_below_threshold": self._rng.randint(0, int(num_vendors * 0.12)), "fourth_party_risk_assessed": self._rng.random() < 0.45, "contractual_security_requirements": self._rng.random() < 0.82},
            "program_maturity": {"vrm_program_exists": self._rng.random() < 0.78, "automated_monitoring": self._rng.random() < 0.45},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"vendors": num_vendors, "critical": critical})


@register_extractor
class IncidentResponseExtractor(DataExtractor):
    """Incident response capabilities. Signals: incident_response"""
    source_name = "incident_response"
    coverage = "cyber"
    signals = ["incident_response"]

    def extract(self) -> ExtractionResult:
        has_ir_plan = self._rng.random() < 0.82
        has_retainer = self._rng.random() < 0.55
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CMP", 8)),
            "ir_capabilities": {"ir_plan_documented": has_ir_plan, "ir_plan_tested_12mo": has_ir_plan and self._rng.random() < 0.65, "tabletop_exercises_12mo": self._rng.randint(0, 4) if has_ir_plan else 0, "ir_retainer": has_retainer, "retainer_provider": self._weighted_choice([("CrowdStrike", 0.20), ("Mandiant", 0.18), ("Secureworks", 0.12), ("Kroll", 0.10), ("Other", 0.40)]) if has_retainer else None},
            "response_metrics": {"mttd_hours": self._rng.randint(2, 72), "mttr_hours": self._rng.randint(12, 168), "incidents_12mo": self._weighted_choice([(0, 0.40), (self._rng.randint(1, 5), 0.35), (self._rng.randint(6, 15), 0.20), (self._rng.randint(16, 50), 0.05)])},
            "soc_capabilities": {"has_soc": self._rng.random() < 0.60, "soc_type": self._weighted_choice([("In-House", 0.30), ("Outsourced", 0.45), ("Hybrid", 0.25)]) if self._rng.random() < 0.60 else None, "24x7_coverage": self._rng.random() < 0.45},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"ir_plan": has_ir_plan, "retainer": has_retainer})


@register_extractor
class ThreatIntelligenceExtractor(DataExtractor):
    """Threat intelligence feeds - dark web, hacker chatter. Signals: public_record, technical_infrastructure"""
    source_name = "threat_intelligence"
    coverage = "cyber"
    signals = ["public_record", "technical_infrastructure"]

    def extract(self) -> ExtractionResult:
        dark_web_mentions = self._weighted_choice([(0, 0.60), (self._rng.randint(1, 10), 0.25), (self._rng.randint(11, 50), 0.12), (self._rng.randint(51, 200), 0.03)])
        credential_leaks = self._weighted_choice([(0, 0.45), (self._rng.randint(1, 100), 0.35), (self._rng.randint(101, 1000), 0.15), (self._rng.randint(1001, 10000), 0.05)])
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CMP", 8)),
            "dark_web_monitoring": {"mentions_90d": dark_web_mentions, "threat_actors_targeting": self._rng.randint(0, 5), "data_for_sale": dark_web_mentions > 20 and self._rng.random() < 0.25},
            "credential_exposure": {"leaked_credentials_detected": credential_leaks, "unique_accounts": int(credential_leaks * self._rng.uniform(0.3, 0.8)), "sources": self._rng.randint(1, 10) if credential_leaks > 0 else 0},
            "threat_level": {"current": self._weighted_choice([("Low", 0.50), ("Moderate", 0.35), ("Elevated", 0.12), ("High", 0.03)]), "trend": self._weighted_choice([("Stable", 0.55), ("Increasing", 0.30), ("Decreasing", 0.15)])},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"dark_web": dark_web_mentions, "creds": credential_leaks})


@register_extractor
class CyberInsuranceHistoryExtractor(DataExtractor):
    """Cyber insurance claims and coverage history. Signals: public_record"""
    source_name = "cyber_insurance_history"
    coverage = "cyber"
    signals = ["public_record"]

    def extract(self) -> ExtractionResult:
        has_coverage = self._rng.random() < 0.72
        num_claims = self._weighted_choice([(0, 0.70), (1, 0.18), (2, 0.08), (self._rng.randint(3, 5), 0.04)]) if has_coverage else 0
        
        claims = []
        for _ in range(num_claims):
            claims.append({"claim_type": self._weighted_choice([("Ransomware", 0.35), ("Data Breach", 0.30), ("Business Interruption", 0.15), ("Social Engineering", 0.12), ("Other", 0.08)]), "amount_usd": self._weighted_choice([(self._rng.randint(25000, 250000), 0.50), (self._rng.randint(250001, 1000000), 0.30), (self._rng.randint(1000001, 5000000), 0.15), (self._rng.randint(5000001, 20000000), 0.05)]), "year": 2024 - self._rng.randint(0, 4)})
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CMP", 8)),
            "current_coverage": {"has_cyber_insurance": has_coverage, "limit_usd": self._weighted_choice([(1000000, 0.20), (5000000, 0.30), (10000000, 0.25), (25000000, 0.15), (50000000, 0.10)]) if has_coverage else None, "retention_usd": self._weighted_choice([(25000, 0.25), (50000, 0.30), (100000, 0.25), (250000, 0.15), (500000, 0.05)]) if has_coverage else None},
            "claims_history": {"total_claims_5yr": num_claims, "total_paid_usd": sum(c["amount_usd"] for c in claims), "claims": claims},
            "underwriting": {"prior_declinations": self._rng.randint(0, 2), "premium_trend": self._weighted_choice([("Stable", 0.35), ("Increasing", 0.50), ("Decreasing", 0.15)])},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"has_coverage": has_coverage, "claims": num_claims})


# =============================================================================
# FINANCIAL INSTITUTIONS EXTRACTORS (10 extractors for 7 signal groups)
# =============================================================================

@register_extractor
class FFIECCallReportExtractor(DataExtractor):
    """FFIEC Call Report - capital ratios, asset quality. Signals: financial_condition, credit_quality"""
    source_name = "ffiec_call_report"
    coverage = "financial_institutions"
    signals = ["financial_condition", "credit_quality"]

    def extract(self) -> ExtractionResult:
        total_assets = self._weighted_choice([(self._rng.randint(100_000_000, 500_000_000), 0.35), (self._rng.randint(500_000_001, 5_000_000_000), 0.30), (self._rng.randint(5_000_000_001, 50_000_000_000), 0.20), (self._rng.randint(50_000_000_001, 500_000_000_000), 0.12), (self._rng.randint(500_000_000_001, 3_000_000_000_000), 0.03)])
        
        tier1_ratio = round(self._rng.uniform(9.0, 17.0), 2)
        npa_ratio = round(self._rng.uniform(0.25, 3.50), 2)
        
        raw_data = {
            "institution": {"rssd_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)), "name": self.kwargs.get("institution_name", f"Bank {self._random_id()}"), "charter_type": self._weighted_choice([("National Bank", 0.25), ("State Member", 0.20), ("State Nonmember", 0.30), ("Savings Assoc", 0.15), ("Credit Union", 0.10)]), "primary_regulator": self._weighted_choice([("OCC", 0.25), ("Federal Reserve", 0.20), ("FDIC", 0.35), ("NCUA", 0.10), ("State", 0.10)])},
            "balance_sheet": {"total_assets_usd": total_assets, "total_loans_usd": int(total_assets * self._rng.uniform(0.55, 0.75)), "total_deposits_usd": int(total_assets * self._rng.uniform(0.75, 0.90)), "total_equity_usd": int(total_assets * self._rng.uniform(0.08, 0.14))},
            "capital_ratios": {"tier1_ratio_pct": tier1_ratio, "total_capital_ratio_pct": round(tier1_ratio + self._rng.uniform(1.0, 3.0), 2), "leverage_ratio_pct": round(self._rng.uniform(7.0, 12.0), 2), "cet1_ratio_pct": round(tier1_ratio - self._rng.uniform(0.5, 1.5), 2), "capital_category": "Well Capitalized" if tier1_ratio >= 8.0 else "Adequately Capitalized" if tier1_ratio >= 6.0 else "Undercapitalized"},
            "asset_quality": {"npa_ratio_pct": npa_ratio, "npl_ratio_pct": round(npa_ratio * self._rng.uniform(0.7, 0.9), 2), "charge_off_ratio_pct": round(self._rng.uniform(0.05, 1.20), 2), "allowance_ratio_pct": round(self._rng.uniform(0.90, 2.20), 2)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"assets": total_assets, "tier1": tier1_ratio})


@register_extractor
class CAMELSRatingExtractor(DataExtractor):
    """CAMELS examination ratings. Signals: regulatory_compliance"""
    source_name = "camels_rating"
    coverage = "financial_institutions"
    signals = ["regulatory_compliance"]

    def extract(self) -> ExtractionResult:
        composite = self._weighted_choice([(1, 0.20), (2, 0.55), (3, 0.18), (4, 0.05), (5, 0.02)])
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "camels_rating": {"composite": composite, "capital": self._weighted_choice([(1, 0.25), (2, 0.50), (3, 0.18), (4, 0.05), (5, 0.02)]), "asset_quality": self._weighted_choice([(1, 0.22), (2, 0.52), (3, 0.18), (4, 0.06), (5, 0.02)]), "management": self._weighted_choice([(1, 0.20), (2, 0.55), (3, 0.18), (4, 0.05), (5, 0.02)]), "earnings": self._weighted_choice([(1, 0.25), (2, 0.50), (3, 0.18), (4, 0.05), (5, 0.02)]), "liquidity": self._weighted_choice([(1, 0.28), (2, 0.52), (3, 0.15), (4, 0.04), (5, 0.01)]), "sensitivity": self._weighted_choice([(1, 0.22), (2, 0.55), (3, 0.18), (4, 0.04), (5, 0.01)])},
            "exam_info": {"last_exam_date": self._random_date(730, 90), "next_exam_expected": self._random_date(-30, -365)},
            "mras": {"total_mras": self._rng.randint(0, 8) if composite >= 2 else 0, "mrias": self._rng.randint(0, 3) if composite >= 3 else 0},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"camels": composite})


@register_extractor
class BankEnforcementExtractor(DataExtractor):
    """Bank regulatory enforcement actions. Signals: regulatory_compliance"""
    source_name = "bank_enforcement"
    coverage = "financial_institutions"
    signals = ["regulatory_compliance"]

    def extract(self) -> ExtractionResult:
        num_actions = self._weighted_choice([(0, 0.82), (1, 0.12), (2, 0.04), (self._rng.randint(3, 5), 0.02)])
        actions = []
        for _ in range(num_actions):
            actions.append({"action_type": self._weighted_choice([("Consent Order", 0.30), ("Cease and Desist", 0.25), ("Civil Money Penalty", 0.20), ("Formal Agreement", 0.15), ("Removal/Prohibition", 0.10)]), "regulator": self._weighted_choice([("OCC", 0.25), ("Federal Reserve", 0.20), ("FDIC", 0.30), ("CFPB", 0.15), ("State", 0.10)]), "issue": self._weighted_choice([("BSA/AML", 0.30), ("Fair Lending", 0.15), ("Consumer Compliance", 0.20), ("Safety & Soundness", 0.20), ("Other", 0.15)]), "penalty_usd": self._weighted_choice([(0, 0.40), (self._rng.randint(50000, 500000), 0.30), (self._rng.randint(500001, 5000000), 0.20), (self._rng.randint(5000001, 50000000), 0.10)]), "date": self._random_date(1825, 0), "status": self._weighted_choice([("Active", 0.40), ("Terminated", 0.50), ("Modified", 0.10)])})
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "enforcement_history": {"total_actions_5yr": num_actions, "active_actions": sum(1 for a in actions if a["status"] == "Active"), "total_penalties_usd": sum(a["penalty_usd"] for a in actions)},
            "actions": actions,
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"actions": num_actions})


@register_extractor
class FIOperationalRiskExtractor(DataExtractor):
    """Operational risk metrics for FIs. Signals: operational_risk"""
    source_name = "fi_operational_risk"
    coverage = "financial_institutions"
    signals = ["operational_risk"]

    def extract(self) -> ExtractionResult:
        op_losses_12mo = self._weighted_choice([(0, 0.40), (self._rng.randint(1, 5), 0.35), (self._rng.randint(6, 15), 0.18), (self._rng.randint(16, 50), 0.07)])
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "operational_losses": {"events_12mo": op_losses_12mo, "total_loss_usd": op_losses_12mo * self._rng.randint(50000, 2000000), "categories": {"internal_fraud": self._rng.randint(0, op_losses_12mo // 3 + 1), "external_fraud": self._rng.randint(0, op_losses_12mo // 3 + 1), "systems": self._rng.randint(0, op_losses_12mo // 3 + 1), "process": self._rng.randint(0, op_losses_12mo // 3 + 1)}},
            "risk_management": {"orm_framework": self._rng.random() < 0.85, "rcsa_frequency": self._weighted_choice([("Annual", 0.40), ("Semi-Annual", 0.35), ("Quarterly", 0.25)]), "key_risk_indicators": self._rng.randint(10, 50)},
            "internal_audit": {"audit_rating": self._weighted_choice([("Satisfactory", 0.75), ("Needs Improvement", 0.20), ("Unsatisfactory", 0.05)]), "open_findings": self._rng.randint(0, 25), "overdue_findings": self._rng.randint(0, 5)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"op_losses": op_losses_12mo})


@register_extractor
class FICyberSecurityExtractor(DataExtractor):
    """Cyber security for financial institutions. Signals: cybersecurity"""
    source_name = "fi_cybersecurity"
    coverage = "financial_institutions"
    signals = ["cybersecurity"]

    def extract(self) -> ExtractionResult:
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "cyber_program": {"maturity_level": self._weighted_choice([(1, 0.08), (2, 0.22), (3, 0.42), (4, 0.22), (5, 0.06)]), "ffiec_cat_completed": self._rng.random() < 0.85, "has_ciso": self._rng.random() < 0.78},
            "incidents": {"cyber_incidents_12mo": self._weighted_choice([(0, 0.50), (self._rng.randint(1, 5), 0.35), (self._rng.randint(6, 15), 0.12), (self._rng.randint(16, 30), 0.03)]), "regulatory_reportable": self._weighted_choice([(0, 0.80), (1, 0.15), (2, 0.05)])},
            "third_party": {"critical_vendors": self._rng.randint(5, 30), "vendors_assessed_pct": round(self._rng.uniform(70, 100), 1)},
            "controls": {"pen_test_frequency": self._weighted_choice([("Annual", 0.35), ("Semi-Annual", 0.35), ("Quarterly", 0.25), ("Continuous", 0.05)]), "vulnerability_scan_frequency": self._weighted_choice([("Monthly", 0.40), ("Weekly", 0.35), ("Daily", 0.20), ("Continuous", 0.05)])},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={})


@register_extractor
class FIGovernanceExtractor(DataExtractor):
    """Corporate governance for financial institutions. Signals: governance"""
    source_name = "fi_governance"
    coverage = "financial_institutions"
    signals = ["governance"]

    def extract(self) -> ExtractionResult:
        board_size = self._rng.randint(7, 15)
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "board": {"size": board_size, "independent_pct": round(self._rng.uniform(60, 90), 1), "financial_experts": self._rng.randint(2, board_size // 2), "avg_tenure_years": round(self._rng.uniform(4, 12), 1)},
            "committees": {"audit_committee": True, "risk_committee": self._rng.random() < 0.85, "compliance_committee": self._rng.random() < 0.70, "technology_committee": self._rng.random() < 0.45},
            "risk_management": {"cro_exists": self._rng.random() < 0.80, "cro_reports_to": self._weighted_choice([("CEO", 0.35), ("Board", 0.40), ("Risk Committee", 0.25)]) if self._rng.random() < 0.80 else None, "risk_appetite_statement": self._rng.random() < 0.85, "stress_testing_program": self._rng.random() < 0.75},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"board_size": board_size})


@register_extractor
class FILitigationExtractor(DataExtractor):
    """Litigation for financial institutions. Signals: litigation"""
    source_name = "fi_litigation"
    coverage = "financial_institutions"
    signals = ["litigation"]

    def extract(self) -> ExtractionResult:
        consumer_complaints = self._rng.randint(10, 500)
        num_cases = self._weighted_choice([(0, 0.50), (1, 0.25), (self._rng.randint(2, 5), 0.18), (self._rng.randint(6, 15), 0.07)])
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "consumer_complaints": {"cfpb_complaints_12mo": consumer_complaints, "complaint_rate_vs_peers": round(self._rng.uniform(0.5, 2.0), 2), "resolution_rate_pct": round(self._rng.uniform(85, 99), 1)},
            "litigation": {"active_cases": num_cases, "class_actions": self._rng.randint(0, max(1, num_cases // 3)), "total_exposure_usd": num_cases * self._rng.randint(500000, 10000000), "settlements_3yr_usd": self._rng.randint(0, num_cases * 2000000)},
            "regulatory_fines": {"total_fines_5yr_usd": self._weighted_choice([(0, 0.60), (self._rng.randint(50000, 500000), 0.25), (self._rng.randint(500001, 5000000), 0.12), (self._rng.randint(5000001, 50000000), 0.03)])},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"complaints": consumer_complaints, "cases": num_cases})


@register_extractor
class FIEarningsExtractor(DataExtractor):
    """Earnings and profitability for FIs. Signals: financial_condition"""
    source_name = "fi_earnings"
    coverage = "financial_institutions"
    signals = ["financial_condition"]

    def extract(self) -> ExtractionResult:
        nim = round(self._rng.uniform(2.50, 4.50), 2)
        roa = round(self._rng.uniform(0.50, 1.80), 2)
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "earnings": {"net_interest_margin_pct": nim, "roa_pct": roa, "roe_pct": round(self._rng.uniform(6.0, 18.0), 2), "efficiency_ratio_pct": round(self._rng.uniform(50, 80), 1), "pre_provision_net_revenue_usd": self._rng.randint(10_000_000, 500_000_000)},
            "revenue_mix": {"net_interest_income_pct": round(self._rng.uniform(60, 85), 1), "fee_income_pct": round(self._rng.uniform(15, 40), 1)},
            "trends": {"nim_yoy_change_bps": self._rng.randint(-30, 30), "roa_yoy_change_bps": self._rng.randint(-20, 20), "efficiency_trend": self._weighted_choice([("Improving", 0.35), ("Stable", 0.45), ("Declining", 0.20)])},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"nim": nim, "roa": roa})


@register_extractor
class AMLBSAExtractor(DataExtractor):
    """BSA/AML compliance for FIs. Signals: regulatory_compliance"""
    source_name = "aml_bsa"
    coverage = "financial_institutions"
    signals = ["regulatory_compliance"]

    def extract(self) -> ExtractionResult:
        sars_filed = self._rng.randint(50, 2000)
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "bsa_program": {"bsa_officer": True, "independent_testing": self._rng.random() < 0.95, "training_program": self._rng.random() < 0.98},
            "filing_activity": {"sars_filed_12mo": sars_filed, "ctrs_filed_12mo": self._rng.randint(100, 5000), "sar_filing_trend": self._weighted_choice([("Increasing", 0.40), ("Stable", 0.45), ("Decreasing", 0.15)])},
            "examination_results": {"last_bsa_exam_date": self._random_date(730, 90), "exam_rating": self._weighted_choice([("Satisfactory", 0.78), ("Needs Improvement", 0.18), ("Unsatisfactory", 0.04)]), "open_findings": self._rng.randint(0, 10)},
            "enforcement": {"bsa_enforcement_actions": self._weighted_choice([(0, 0.90), (1, 0.08), (2, 0.02)]), "lookback_required": self._rng.random() < 0.05},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"sars": sars_filed})


# =============================================================================
# ENERGY EXTRACTORS (9 extractors for 7 signal groups)
# =============================================================================

@register_extractor
class OSHASafetyExtractor(DataExtractor):
    """OSHA safety records - inspections, violations, TRIR. Signals: safety_performance"""
    source_name = "osha_safety"
    coverage = "energy"
    signals = ["safety_performance"]

    def extract(self) -> ExtractionResult:
        trir = round(self._rng.uniform(0.4, 5.5), 2)
        num_inspections = self._weighted_choice([(0, 0.30), (self._rng.randint(1, 3), 0.40), (self._rng.randint(4, 8), 0.20), (self._rng.randint(9, 20), 0.10)])
        total_violations = 0
        inspections = []
        for _ in range(num_inspections):
            violations = self._weighted_choice([(0, 0.35), (self._rng.randint(1, 3), 0.35), (self._rng.randint(4, 10), 0.20), (self._rng.randint(11, 25), 0.10)])
            total_violations += violations
            inspections.append({"date": self._random_date(1095, 0), "type": self._weighted_choice([("Planned", 0.30), ("Complaint", 0.25), ("Accident", 0.15), ("Referral", 0.15), ("Follow-up", 0.15)]), "violations": violations, "serious_violations": int(violations * self._rng.uniform(0.2, 0.5)), "penalty_usd": violations * self._rng.randint(1000, 15000)})
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("EST", 10)),
            "injury_rates": {"trir": trir, "dart_rate": round(trir * self._rng.uniform(0.4, 0.7), 2), "fatalities_5yr": self._weighted_choice([(0, 0.90), (1, 0.07), (2, 0.03)]), "industry_benchmark_trir": 2.0, "vs_benchmark": round(trir / 2.0, 2)},
            "inspection_history": {"total_3yr": num_inspections, "total_violations": total_violations, "total_penalties_usd": sum(i["penalty_usd"] for i in inspections), "inspections": inspections},
            "safety_program": {"vpp_participant": self._rng.random() < 0.12, "iso_45001": self._rng.random() < 0.28, "safety_training_hours": self._rng.randint(20, 80)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"trir": trir, "inspections": num_inspections})


@register_extractor
class EPAComplianceExtractor(DataExtractor):
    """EPA environmental compliance - permits, violations, spills. Signals: environmental_compliance"""
    source_name = "epa_compliance"
    coverage = "energy"
    signals = ["environmental_compliance"]

    def extract(self) -> ExtractionResult:
        num_violations = self._weighted_choice([(0, 0.45), (self._rng.randint(1, 3), 0.30), (self._rng.randint(4, 8), 0.18), (self._rng.randint(9, 20), 0.07)])
        num_spills = self._weighted_choice([(0, 0.55), (self._rng.randint(1, 3), 0.30), (self._rng.randint(4, 8), 0.12), (self._rng.randint(9, 15), 0.03)])
        
        violations = [{"program": self._weighted_choice([("Clean Air Act", 0.30), ("Clean Water Act", 0.25), ("RCRA", 0.20), ("SPCC", 0.15), ("Other", 0.10)]), "severity": self._weighted_choice([("Minor", 0.55), ("Significant", 0.30), ("High Priority", 0.15)]), "penalty_usd": self._rng.randint(5000, 500000), "status": self._weighted_choice([("Resolved", 0.60), ("Open", 0.25), ("Enforcement", 0.15)])} for _ in range(num_violations)]
        
        spills = [{"material": self._weighted_choice([("Crude Oil", 0.35), ("Produced Water", 0.25), ("NGL", 0.15), ("Diesel", 0.10), ("Chemicals", 0.15)]), "volume_barrels": self._weighted_choice([(self._rng.randint(1, 50), 0.50), (self._rng.randint(51, 500), 0.30), (self._rng.randint(501, 5000), 0.15), (self._rng.randint(5001, 50000), 0.05)]), "media_affected": self._weighted_choice([("Soil", 0.40), ("Water", 0.30), ("Both", 0.20), ("Contained", 0.10)]), "cleanup_complete": self._rng.random() < 0.75} for _ in range(num_spills)]
        
        raw_data = {
            "facility_id": self.kwargs.get("facility_id", self._random_id("EPA", 12)),
            "compliance_status": {"overall": "In Compliance" if num_violations == 0 else "Minor Violations" if num_violations < 4 else "Significant Noncompliance", "quarters_in_compliance_12mo": 4 - min(num_violations, 3)},
            "violations": {"total_3yr": num_violations, "high_priority": sum(1 for v in violations if v["severity"] == "High Priority"), "total_penalties_usd": sum(v["penalty_usd"] for v in violations), "violations": violations},
            "spill_history": {"total_5yr": num_spills, "reportable_spills": sum(1 for s in spills if s["volume_barrels"] > 10), "total_volume_barrels": sum(s["volume_barrels"] for s in spills), "spills": spills},
            "programs": {"iso_14001": self._rng.random() < 0.38, "environmental_management_system": self._rng.random() < 0.72, "ghg_reporting": self._rng.random() < 0.82},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"violations": num_violations, "spills": num_spills})


@register_extractor
class StateRegulatoryExtractor(DataExtractor):
    """State regulatory standing - permits, enforcement. Signals: regulatory_standing"""
    source_name = "state_regulatory"
    coverage = "energy"
    signals = ["regulatory_standing"]

    def extract(self) -> ExtractionResult:
        num_permits = self._rng.randint(5, 50)
        num_violations = self._weighted_choice([(0, 0.50), (self._rng.randint(1, 5), 0.30), (self._rng.randint(6, 15), 0.15), (self._rng.randint(16, 30), 0.05)])
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OPR", 8)),
            "permits": {"total_active": num_permits, "pending_applications": self._rng.randint(0, 10), "expired": self._rng.randint(0, 3), "states_operating": self._rng.randint(1, 8)},
            "violations": {"total_3yr": num_violations, "per_permit": round(num_violations / num_permits, 2) if num_permits > 0 else 0, "penalties_usd": num_violations * self._rng.randint(2000, 25000)},
            "bonding": {"bonds_posted_usd": num_permits * self._rng.randint(25000, 100000), "bond_claims": self._weighted_choice([(0, 0.90), (1, 0.08), (2, 0.02)])},
            "orphan_wells": {"operated_orphan_wells": self._rng.randint(0, 5), "plugging_obligations": self._rng.randint(0, 20)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"permits": num_permits, "violations": num_violations})


@register_extractor
class ProductionDataExtractor(DataExtractor):
    """Production data - volumes, wells, operations. Signals: operational_quality"""
    source_name = "production_data"
    coverage = "energy"
    signals = ["operational_quality"]

    def extract(self) -> ExtractionResult:
        production_boed = self._weighted_choice([(self._rng.randint(500, 5000), 0.35), (self._rng.randint(5001, 25000), 0.30), (self._rng.randint(25001, 100000), 0.20), (self._rng.randint(100001, 500000), 0.12), (self._rng.randint(500001, 2000000), 0.03)])
        oil_pct = self._rng.uniform(0.20, 0.80)
        active_wells = self._weighted_choice([(self._rng.randint(10, 100), 0.40), (self._rng.randint(101, 500), 0.30), (self._rng.randint(501, 2000), 0.20), (self._rng.randint(2001, 10000), 0.10)])
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OPR", 8)),
            "production": {"total_boed": production_boed, "oil_bopd": int(production_boed * oil_pct), "gas_mcfd": int(production_boed * (1 - oil_pct) * 6), "oil_pct": round(oil_pct * 100, 1), "yoy_change_pct": round(self._rng.uniform(-15, 25), 1)},
            "wells": {"total_active": active_wells, "producing": int(active_wells * 0.85), "injection": int(active_wells * 0.08), "shut_in": int(active_wells * 0.07), "drilled_ytd": self._rng.randint(0, int(active_wells * 0.15))},
            "operations": {"loe_per_boe_usd": round(self._rng.uniform(5, 18), 2), "downtime_pct": round(self._rng.uniform(1, 8), 1), "water_cut_pct": round(self._rng.uniform(30, 85), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"production": production_boed, "wells": active_wells})


@register_extractor
class EnergyFinancialExtractor(DataExtractor):
    """Energy operator financials. Signals: financial_stability"""
    source_name = "energy_financial"
    coverage = "energy"
    signals = ["financial_stability"]

    def extract(self) -> ExtractionResult:
        production_boed = self._rng.randint(5000, 200000)
        revenue = production_boed * 365 * self._rng.randint(30, 60)
        ebitdax_margin = self._rng.uniform(0.35, 0.65)
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OPR", 8)),
            "financials": {"revenue_usd": revenue, "ebitdax_usd": int(revenue * ebitdax_margin), "ebitdax_margin_pct": round(ebitdax_margin * 100, 1)},
            "leverage": {"total_debt_usd": int(revenue * self._rng.uniform(0.3, 1.2)), "debt_to_ebitdax": round(self._rng.uniform(1.5, 4.5), 2), "interest_coverage": round(self._rng.uniform(2.0, 8.0), 2)},
            "hedging": {"oil_hedged_pct_12mo": round(self._rng.uniform(30, 80), 1), "gas_hedged_pct_12mo": round(self._rng.uniform(20, 70), 1), "hedge_floor_price_oil_usd": self._rng.randint(50, 75)},
            "credit": {"has_rating": self._rng.random() < 0.35, "credit_facility_usd": int(revenue * self._rng.uniform(0.3, 0.8)), "availability_usd": int(revenue * self._rng.uniform(0.1, 0.4))},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"revenue": revenue})


@register_extractor
class ReserveDataExtractor(DataExtractor):
    """Reserve and asset data. Signals: asset_quality"""
    source_name = "reserve_data"
    coverage = "energy"
    signals = ["asset_quality"]

    def extract(self) -> ExtractionResult:
        proved_reserves = self._rng.randint(10, 500)  # MMBoe
        production_boed = self._rng.randint(5000, 100000)
        reserve_life = round(proved_reserves * 1000000 / (production_boed * 365), 1)
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OPR", 8)),
            "reserves": {"proved_reserves_mmboe": proved_reserves, "proved_developed_pct": round(self._rng.uniform(55, 80), 1), "pud_pct": round(self._rng.uniform(20, 45), 1), "reserve_life_years": reserve_life},
            "asset_profile": {"acreage_total": self._rng.randint(50000, 500000), "acreage_undeveloped_pct": round(self._rng.uniform(30, 70), 1), "primary_basins": self._rng.randint(1, 5)},
            "reserve_replacement": {"replacement_ratio_3yr": round(self._rng.uniform(0.8, 2.0), 2), "finding_cost_per_boe_usd": round(self._rng.uniform(8, 25), 2), "organic_growth_pct": round(self._rng.uniform(60, 100), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"reserves": proved_reserves, "reserve_life": reserve_life})


@register_extractor
class ESGDataExtractor(DataExtractor):
    """ESG metrics for energy operators. Signals: esg_factors"""
    source_name = "esg_data"
    coverage = "energy"
    signals = ["esg_factors"]

    def extract(self) -> ExtractionResult:
        ghg_intensity = round(self._rng.uniform(15, 45), 1)  # kg CO2e/boe
        methane_intensity = round(self._rng.uniform(0.1, 1.5), 2)  # %
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OPR", 8)),
            "emissions": {"ghg_intensity_kg_co2e_boe": ghg_intensity, "methane_intensity_pct": methane_intensity, "flaring_intensity_mcf_boe": round(self._rng.uniform(0.5, 5.0), 2), "scope_1_tonnes_co2e": self._rng.randint(50000, 2000000)},
            "environmental": {"water_recycling_pct": round(self._rng.uniform(20, 90), 1), "spill_intensity_bbls_mmboe": round(self._rng.uniform(5, 50), 1), "land_disturbance_acres": self._rng.randint(100, 5000)},
            "social": {"community_investment_usd": self._rng.randint(100000, 5000000), "local_employment_pct": round(self._rng.uniform(40, 90), 1), "safety_trir": round(self._rng.uniform(0.5, 4.0), 2)},
            "governance": {"board_independence_pct": round(self._rng.uniform(60, 90), 1), "esg_committee": self._rng.random() < 0.55, "sustainability_report": self._rng.random() < 0.65},
            "ratings": {"msci_esg_rating": self._weighted_choice([("AAA", 0.05), ("AA", 0.10), ("A", 0.20), ("BBB", 0.30), ("BB", 0.20), ("B", 0.10), ("CCC", 0.05)]) if self._rng.random() < 0.60 else None},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"ghg_intensity": ghg_intensity})


@register_extractor
class WellIntegrityExtractor(DataExtractor):
    """Well integrity and asset condition. Signals: asset_quality, safety_performance"""
    source_name = "well_integrity"
    coverage = "energy"
    signals = ["asset_quality", "safety_performance"]

    def extract(self) -> ExtractionResult:
        total_wells = self._rng.randint(50, 2000)
        integrity_failures = self._weighted_choice([(0, 0.55), (self._rng.randint(1, 5), 0.30), (self._rng.randint(6, 15), 0.12), (self._rng.randint(16, 30), 0.03)])
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OPR", 8)),
            "well_inventory": {"total_wells": total_wells, "average_age_years": round(self._rng.uniform(8, 25), 1), "wells_over_20_years": int(total_wells * self._rng.uniform(0.15, 0.45))},
            "integrity_status": {"failures_3yr": integrity_failures, "failure_rate_pct": round(integrity_failures / total_wells * 100, 3), "mits_performed_12mo": self._rng.randint(total_wells // 10, total_wells // 3), "casing_failures": self._rng.randint(0, integrity_failures), "cement_failures": self._rng.randint(0, integrity_failures)},
            "plugging": {"wells_plugged_12mo": self._rng.randint(0, 20), "plugging_backlog": self._rng.randint(0, 50), "estimated_plugging_liability_usd": self._rng.randint(500000, 10000000)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"wells": total_wells, "failures": integrity_failures})


@register_extractor
class ProcessSafetyExtractor(DataExtractor):
    """Process safety metrics for energy. Signals: safety_performance"""
    source_name = "process_safety"
    coverage = "energy"
    signals = ["safety_performance"]

    def extract(self) -> ExtractionResult:
        tier1_events = self._weighted_choice([(0, 0.60), (1, 0.25), (2, 0.10), (self._rng.randint(3, 6), 0.05)])
        tier2_events = self._weighted_choice([(0, 0.40), (self._rng.randint(1, 3), 0.35), (self._rng.randint(4, 8), 0.18), (self._rng.randint(9, 15), 0.07)])
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OPR", 8)),
            "process_safety_events": {"tier1_events_12mo": tier1_events, "tier2_events_12mo": tier2_events, "tier1_rate_per_mmboe": round(tier1_events / max(1, self._rng.randint(1, 50)), 3), "tier2_rate_per_mmboe": round(tier2_events / max(1, self._rng.randint(1, 50)), 3)},
            "hazard_management": {"process_hazard_analyses_current_pct": round(self._rng.uniform(85, 100), 1), "moc_backlog": self._rng.randint(0, 20), "psi_audits_12mo": self._rng.randint(2, 12)},
            "emergency_response": {"drills_12mo": self._rng.randint(4, 24), "response_time_target_met_pct": round(self._rng.uniform(85, 100), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"tier1": tier1_events, "tier2": tier2_events})


# =============================================================================
# PROFESSIONAL INDEMNITY EXTRACTORS (9 extractors for 7 signal groups)
# =============================================================================

@register_extractor
class StateBarExtractor(DataExtractor):
    """State bar/licensing board data - license status, disciplinary. Signals: regulatory_standing"""
    source_name = "state_bar"
    coverage = "professional_indemnity"
    signals = ["regulatory_standing"]

    def extract(self) -> ExtractionResult:
        entity_type = self.kwargs.get("entity_type", "firm")
        num_professionals = self._weighted_choice([(self._rng.randint(1, 10), 0.40), (self._rng.randint(11, 50), 0.30), (self._rng.randint(51, 200), 0.20), (self._rng.randint(201, 1000), 0.10)]) if entity_type == "firm" else 1
        
        num_disciplinary = self._weighted_choice([(0, 0.82), (1, 0.12), (2, 0.04), (self._rng.randint(3, 5), 0.02)])
        disciplinary_actions = [{"action_type": self._weighted_choice([("Private Reprimand", 0.40), ("Public Reprimand", 0.25), ("Probation", 0.15), ("Suspension", 0.12), ("Disbarment/Revocation", 0.05), ("Resignation", 0.03)]), "date": self._random_date(3650, 0), "basis": self._weighted_choice([("Negligence", 0.30), ("Trust Account", 0.15), ("Conflict of Interest", 0.12), ("Failure to Communicate", 0.10), ("Criminal Conviction", 0.08), ("Fee Dispute", 0.10), ("Other", 0.15)])} for _ in range(num_disciplinary)]
        
        raw_data = {
            "entity": {"entity_id": self.kwargs.get("entity_id", self._random_id("LIC", 10)), "entity_type": entity_type, "name": self.kwargs.get("firm_name", f"Professional Firm {self._random_id()}"), "profession": self._weighted_choice([("Attorney", 0.30), ("CPA", 0.25), ("Architect", 0.15), ("Engineer", 0.15), ("Medical", 0.10), ("Other", 0.05)]), "num_professionals": num_professionals, "states_licensed": self._rng.randint(1, 8)},
            "license_status": {"status": self._weighted_choice([("Active", 0.92), ("Inactive", 0.04), ("Suspended", 0.02), ("Revoked", 0.01), ("Retired", 0.01)]) if entity_type == "individual" else "Active", "years_licensed": self._rng.randint(2, 40)},
            "disciplinary_history": {"total_actions": num_disciplinary, "serious_actions": sum(1 for a in disciplinary_actions if a["action_type"] in ("Suspension", "Disbarment/Revocation")), "actions": disciplinary_actions},
            "standing": {"good_standing": num_disciplinary == 0 or all(a["action_type"] == "Private Reprimand" for a in disciplinary_actions)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"professionals": num_professionals, "disciplinary": num_disciplinary})


@register_extractor
class MalpracticeClaimsExtractor(DataExtractor):
    """Malpractice claims history. Signals: claims_history"""
    source_name = "malpractice_claims"
    coverage = "professional_indemnity"
    signals = ["claims_history"]

    def extract(self) -> ExtractionResult:
        num_claims = self._weighted_choice([(0, 0.60), (1, 0.22), (2, 0.10), (self._rng.randint(3, 6), 0.06), (self._rng.randint(7, 12), 0.02)])
        claims = []
        for _ in range(num_claims):
            claimed = self._weighted_choice([(self._rng.randint(50000, 250000), 0.45), (self._rng.randint(250001, 1000000), 0.35), (self._rng.randint(1000001, 5000000), 0.15), (self._rng.randint(5000001, 25000000), 0.05)])
            status = self._weighted_choice([("Closed - No Payment", 0.35), ("Closed - Settled", 0.30), ("Closed - Judgment", 0.10), ("Open", 0.20), ("Reserved", 0.05)])
            paid = int(claimed * self._rng.uniform(0, 0.60)) if "Settled" in status or "Judgment" in status else 0
            claims.append({"claim_type": self._weighted_choice([("Malpractice", 0.50), ("Breach of Fiduciary Duty", 0.15), ("Breach of Contract", 0.12), ("Fraud", 0.08), ("Negligent Misrepresentation", 0.10), ("Other", 0.05)]), "date": self._random_date(1825, 0), "claimed_usd": claimed, "paid_usd": paid, "status": status})
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("LIC", 10)),
            "claims_history": {"total_claims_5yr": num_claims, "total_claimed_usd": sum(c["claimed_usd"] for c in claims), "total_paid_usd": sum(c["paid_usd"] for c in claims), "open_claims": sum(1 for c in claims if c["status"] == "Open"), "claims": claims},
            "loss_ratios": {"frequency_per_professional": round(num_claims / max(1, self._rng.randint(1, 50)), 3), "severity_average_usd": round(sum(c["paid_usd"] for c in claims) / max(1, num_claims), 0)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"claims": num_claims})


@register_extractor
class PeerReviewExtractor(DataExtractor):
    """Peer review results and quality assurance. Signals: peer_review"""
    source_name = "peer_review"
    coverage = "professional_indemnity"
    signals = ["peer_review"]

    def extract(self) -> ExtractionResult:
        rating = self._weighted_choice([("Pass", 0.70), ("Pass with Deficiencies", 0.20), ("Fail", 0.07), ("No Opinion", 0.03)])
        num_reviews = self._rng.randint(1, 5)
        reviews = [{"date": self._random_date(365 * (i + 1), 365 * i), "type": self._weighted_choice([("System Review", 0.50), ("Engagement Review", 0.35), ("Quality Review", 0.15)]), "rating": self._weighted_choice([("Pass", 0.70), ("Pass with Deficiencies", 0.20), ("Fail", 0.10)]) if i > 0 else rating, "findings": self._rng.randint(0, 8) if rating != "Pass" else 0} for i in range(num_reviews)]
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FRM", 8)),
            "current_status": {"most_recent_rating": rating, "most_recent_date": reviews[0]["date"], "next_review_due": self._random_date(-30, -730), "in_good_standing": rating in ("Pass", "Pass with Deficiencies")},
            "review_history": {"total_reviews": num_reviews, "consecutive_pass": sum(1 for r in reviews if r["rating"] == "Pass"), "reviews": reviews},
            "quality_metrics": {"findings_last_review": reviews[0]["findings"], "significant_findings": self._rng.randint(0, reviews[0]["findings"] // 2 + 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"rating": rating})


@register_extractor
class QualityManagementExtractor(DataExtractor):
    """Quality management systems and certifications. Signals: quality_management"""
    source_name = "quality_management"
    coverage = "professional_indemnity"
    signals = ["quality_management"]

    def extract(self) -> ExtractionResult:
        has_qms = self._rng.random() < 0.72
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FRM", 8)),
            "quality_program": {"has_qms": has_qms, "qms_documented": has_qms, "last_review_date": self._random_date(365, 0) if has_qms else None, "responsible_partner": has_qms},
            "certifications": {"iso_9001": self._rng.random() < 0.25, "industry_specific": self._rng.random() < 0.40, "certifications": [c for c in ["ISO 9001", "ISO 17025", "AICPA QC", "State Board QC"] if self._rng.random() < 0.30]},
            "procedures": {"engagement_acceptance": self._rng.random() < 0.85, "conflict_checking": self._rng.random() < 0.92, "file_review": self._rng.random() < 0.78, "continuing_education_tracking": self._rng.random() < 0.88},
            "internal_inspections": {"inspections_12mo": self._rng.randint(0, 10), "findings_per_inspection": round(self._rng.uniform(0.5, 4.0), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"has_qms": has_qms})


@register_extractor
class NetworkAuthorityExtractor(DataExtractor):
    """Network and panel membership data. Signals: network_authority"""
    source_name = "network_authority"
    coverage = "professional_indemnity"
    signals = ["network_authority"]

    def extract(self) -> ExtractionResult:
        num_panels = self._weighted_choice([(0, 0.30), (self._rng.randint(1, 3), 0.35), (self._rng.randint(4, 8), 0.25), (self._rng.randint(9, 20), 0.10)])
        
        panels = [{"panel_type": self._weighted_choice([("Insurance Carrier", 0.35), ("Corporate", 0.25), ("Government", 0.15), ("Trade Association", 0.15), ("Court Appointed", 0.10)]), "status": self._weighted_choice([("Active", 0.90), ("Probation", 0.05), ("Suspended", 0.03), ("Terminated", 0.02)]), "years_on_panel": self._rng.randint(1, 15)} for _ in range(num_panels)]
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FRM", 8)),
            "panel_memberships": {"total_panels": num_panels, "active_panels": sum(1 for p in panels if p["status"] == "Active"), "panels": panels},
            "referral_network": {"referral_sources": self._rng.randint(5, 50), "referral_revenue_pct": round(self._rng.uniform(10, 60), 1)},
            "certifications": {"specialist_certifications": self._rng.randint(0, 5), "approved_vendor_listings": self._rng.randint(0, 10)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"panels": num_panels})


@register_extractor
class ClientQualityExtractor(DataExtractor):
    """Client quality and concentration data. Signals: client_quality"""
    source_name = "client_quality"
    coverage = "professional_indemnity"
    signals = ["client_quality"]

    def extract(self) -> ExtractionResult:
        total_clients = self._weighted_choice([(self._rng.randint(20, 100), 0.35), (self._rng.randint(101, 500), 0.35), (self._rng.randint(501, 2000), 0.20), (self._rng.randint(2001, 10000), 0.10)])
        top_client_pct = round(self._rng.uniform(5, 35), 1)
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FRM", 8)),
            "client_base": {"total_clients": total_clients, "new_clients_12mo": int(total_clients * self._rng.uniform(0.10, 0.30)), "client_retention_pct": round(self._rng.uniform(75, 95), 1)},
            "concentration": {"top_client_revenue_pct": top_client_pct, "top_5_clients_pct": round(top_client_pct + self._rng.uniform(10, 25), 1), "top_10_clients_pct": round(top_client_pct + self._rng.uniform(20, 40), 1)},
            "client_profile": {"high_risk_clients_pct": round(self._rng.uniform(5, 25), 1), "litigation_clients_pct": round(self._rng.uniform(10, 40), 1), "international_clients_pct": round(self._rng.uniform(0, 30), 1)},
            "billing": {"average_matter_value_usd": self._rng.randint(5000, 100000), "realization_rate_pct": round(self._rng.uniform(85, 98), 1), "collection_rate_pct": round(self._rng.uniform(90, 99), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"clients": total_clients, "top_concentration": top_client_pct})


@register_extractor
class ProfessionalDevelopmentExtractor(DataExtractor):
    """CPE and professional development tracking. Signals: professional_development"""
    source_name = "professional_development"
    coverage = "professional_indemnity"
    signals = ["professional_development"]

    def extract(self) -> ExtractionResult:
        num_professionals = self._rng.randint(5, 200)
        cpe_compliance = round(self._rng.uniform(90, 100), 1)
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FRM", 8)),
            "cpe_compliance": {"total_professionals": num_professionals, "compliance_pct": cpe_compliance, "average_hours_per_professional": self._rng.randint(30, 60), "ethics_hours_avg": self._rng.randint(2, 8)},
            "specializations": {"specialized_credentials": self._rng.randint(0, num_professionals // 3), "board_certifications": self._rng.randint(0, num_professionals // 5), "advanced_degrees": int(num_professionals * self._rng.uniform(0.20, 0.60))},
            "training_investment": {"training_budget_per_professional_usd": self._rng.randint(500, 5000), "internal_training_hours_avg": self._rng.randint(10, 40), "external_conferences_avg": round(self._rng.uniform(1, 4), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"professionals": num_professionals, "cpe_compliance": cpe_compliance})


@register_extractor
class PIFinancialExtractor(DataExtractor):
    """PI-specific financial metrics. Signals: claims_history, quality_management"""
    source_name = "pi_financial"
    coverage = "professional_indemnity"
    signals = ["claims_history", "quality_management"]

    def extract(self) -> ExtractionResult:
        num_professionals = self._rng.randint(5, 200)
        revenue_per_prof = self._rng.randint(150000, 800000)
        revenue = num_professionals * revenue_per_prof
        
        raw_data = {
            "firm_id": self.kwargs.get("firm_id", self._random_id("FRM", 8)),
            "financials": {"revenue_usd": revenue, "revenue_per_professional_usd": revenue_per_prof, "profit_margin_pct": round(self._rng.uniform(15, 45), 1), "revenue_growth_pct": round(self._rng.uniform(-10, 25), 1)},
            "expenses": {"compensation_pct_revenue": round(self._rng.uniform(45, 65), 1), "insurance_pct_revenue": round(self._rng.uniform(2, 8), 1), "overhead_pct_revenue": round(self._rng.uniform(15, 30), 1)},
            "insurance": {"pi_coverage_limit_usd": self._weighted_choice([(1000000, 0.25), (2000000, 0.30), (5000000, 0.25), (10000000, 0.15), (25000000, 0.05)]), "retention_usd": self._weighted_choice([(10000, 0.25), (25000, 0.35), (50000, 0.25), (100000, 0.15)]), "premium_usd": int(revenue * self._rng.uniform(0.015, 0.050))},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"revenue": revenue, "professionals": num_professionals})


# =============================================================================
# COMMON/SHARED EXTRACTORS (used across multiple coverages)
# =============================================================================

@register_extractor
class CreditRatingExtractor(DataExtractor):
    """Credit rating agency data. Signals: financial_stability (all coverages)"""
    source_name = "credit_rating"
    coverage = "common"
    signals = ["financial_stability"]

    def extract(self) -> ExtractionResult:
        is_rated = self._rng.random() < 0.38
        ratings = []
        if is_rated:
            for _ in range(self._rng.randint(1, 3)):
                agency = self._weighted_choice([("Moody's", 0.35), ("S&P", 0.35), ("Fitch", 0.30)])
                rating_idx = self._weighted_choice([(self._rng.randint(0, 5), 0.20), (self._rng.randint(6, 9), 0.35), (self._rng.randint(10, 14), 0.30), (self._rng.randint(15, 20), 0.15)])
                ratings_list = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C"]
                ratings.append({"agency": agency, "rating": ratings_list[min(rating_idx, len(ratings_list) - 1)], "outlook": self._weighted_choice([("Stable", 0.60), ("Positive", 0.15), ("Negative", 0.20), ("Watch", 0.05)]), "investment_grade": rating_idx <= 9})
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "rating_status": {"is_rated": is_rated, "investment_grade": any(r["investment_grade"] for r in ratings) if ratings else None},
            "ratings": ratings,
            "history": {"upgrades_3yr": self._rng.randint(0, 2) if is_rated else 0, "downgrades_3yr": self._rng.randint(0, 3) if is_rated else 0},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"is_rated": is_rated})


@register_extractor
class NewsMediaExtractor(DataExtractor):
    """News and media monitoring. Signals: public_record (all coverages)"""
    source_name = "news_media"
    coverage = "common"
    signals = ["public_record"]

    def extract(self) -> ExtractionResult:
        num_articles = self._weighted_choice([(self._rng.randint(0, 20), 0.35), (self._rng.randint(21, 100), 0.35), (self._rng.randint(101, 500), 0.20), (self._rng.randint(501, 2000), 0.10)])
        sentiments = [self._weighted_choice([("Positive", 0.30), ("Neutral", 0.45), ("Negative", 0.25)]) for _ in range(num_articles)]
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "coverage_summary": {"total_articles_12mo": num_articles, "by_sentiment": {"positive": sum(1 for s in sentiments if s == "Positive"), "neutral": sum(1 for s in sentiments if s == "Neutral"), "negative": sum(1 for s in sentiments if s == "Negative")}, "average_sentiment_score": round(sum(0.8 if s == "Positive" else 0.5 if s == "Neutral" else 0.2 for s in sentiments) / max(1, len(sentiments)), 3)},
            "adverse_media": {"adverse_count": sum(1 for s in sentiments if s == "Negative"), "significant_adverse": num_articles > 50 and sum(1 for s in sentiments if s == "Negative") > num_articles * 0.25},
            "categories": {"regulatory": self._rng.randint(0, num_articles // 10 + 1), "legal": self._rng.randint(0, num_articles // 10 + 1), "financial": self._rng.randint(0, num_articles // 5 + 1), "operational": self._rng.randint(0, num_articles // 5 + 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"articles": num_articles})


@register_extractor
class CompanyProfileExtractor(DataExtractor):
    """General company profile data. Signals: multiple"""
    source_name = "company_profile"
    coverage = "common"
    signals = ["financial_stability", "governance"]

    def extract(self) -> ExtractionResult:
        employees = self._weighted_choice([(self._rng.randint(10, 100), 0.30), (self._rng.randint(101, 500), 0.30), (self._rng.randint(501, 2000), 0.25), (self._rng.randint(2001, 50000), 0.15)])
        revenue = employees * self._rng.randint(100000, 500000)
        years_in_business = self._rng.randint(2, 100)
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CMP", 10)),
            "profile": {"name": self.kwargs.get("company_name", f"Company {self._random_id()}"), "years_in_business": years_in_business, "employees": employees, "locations": self._rng.randint(1, 50), "countries_operating": self._rng.randint(1, 30)},
            "financials": {"revenue_usd": revenue, "revenue_growth_3yr_cagr": round(self._rng.uniform(-5, 25), 1)},
            "ownership": {"type": self._weighted_choice([("Private", 0.55), ("Public", 0.25), ("PE-Backed", 0.10), ("Family", 0.08), ("Government", 0.02)]), "majority_shareholder": self._weighted_choice([("Founders", 0.30), ("PE Fund", 0.20), ("Public Float", 0.25), ("Family", 0.15), ("Other", 0.10)])},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"employees": employees, "revenue": revenue})


# =============================================================================
# FACTORY FUNCTIONS AND UTILITIES
# =============================================================================

def get_extractor(extractor_type: str, seed: Optional[str] = None, **kwargs) -> DataExtractor:
    """Factory function to instantiate extractors by type name or shorthand."""
    shorthand_map = {
        # Marine
        "equasis_operator": "EquasisOperatorExtractor",
        "psc_inspection": "PSCInspectionExtractor",
        "ais_tracking": "AISTrackingExtractor",
        "sanctions_screening": "SanctionsScreeningExtractor",
        "classification_society": "ClassificationSocietyExtractor",
        "pi_club": "PIClubExtractor",
        "marine_financial": "MarineFinancialExtractor",
        "ism_compliance": "ISMComplianceExtractor",
        "vessel_valuation": "VesselValuationExtractor",
        "flag_state_performance": "FlagStatePerformanceExtractor",
        # Aerospace
        "iata_operator": "IATAOperatorExtractor",
        "aviation_safety": "AviationSafetyExtractor",
        "faa_registry": "FAARegistryExtractor",
        "aircraft_fleet": "AircraftFleetExtractor",
        "mro_provider": "MROProviderExtractor",
        "crew_training": "CrewTrainingExtractor",
        "operational_performance": "OperationalPerformanceExtractor",
        "aviation_financial": "AviationFinancialExtractor",
        # Cyber
        "security_scorecard": "SecurityScorecardExtractor",
        "cve_exposure": "CVEExposureExtractor",
        "breach_database": "BreachDatabaseExtractor",
        "cyber_governance": "CyberGovernanceExtractor",
        "vendor_security": "VendorSecurityExtractor",
        "incident_response": "IncidentResponseExtractor",
        "threat_intelligence": "ThreatIntelligenceExtractor",
        "cyber_insurance_history": "CyberInsuranceHistoryExtractor",
        # D&O
        "sec_edgar": "SECEdgarExtractor",
        "litigation_database": "LitigationDatabaseExtractor",
        "proxy_statement": "ProxyStatementExtractor",
        "insider_activity": "InsiderActivityExtractor",
        "sec_enforcement": "SECEnforcementExtractor",
        "industry_comparison": "IndustryComparisonExtractor",
        "do_financial": "DOFinancialExtractor",
        # Financial Institutions
        "ffiec_call_report": "FFIECCallReportExtractor",
        "camels_rating": "CAMELSRatingExtractor",
        "bank_enforcement": "BankEnforcementExtractor",
        "fi_operational_risk": "FIOperationalRiskExtractor",
        "fi_cybersecurity": "FICyberSecurityExtractor",
        "fi_governance": "FIGovernanceExtractor",
        "fi_litigation": "FILitigationExtractor",
        "fi_earnings": "FIEarningsExtractor",
        "aml_bsa": "AMLBSAExtractor",
        # Energy
        "osha_safety": "OSHASafetyExtractor",
        "epa_compliance": "EPAComplianceExtractor",
        "state_regulatory": "StateRegulatoryExtractor",
        "production_data": "ProductionDataExtractor",
        "energy_financial": "EnergyFinancialExtractor",
        "reserve_data": "ReserveDataExtractor",
        "esg_data": "ESGDataExtractor",
        "well_integrity": "WellIntegrityExtractor",
        "process_safety": "ProcessSafetyExtractor",
        # Professional Indemnity
        "state_bar": "StateBarExtractor",
        "malpractice_claims": "MalpracticeClaimsExtractor",
        "peer_review": "PeerReviewExtractor",
        "quality_management": "QualityManagementExtractor",
        "network_authority": "NetworkAuthorityExtractor",
        "client_quality": "ClientQualityExtractor",
        "professional_development": "ProfessionalDevelopmentExtractor",
        "pi_financial": "PIFinancialExtractor",
        # Common
        "credit_rating": "CreditRatingExtractor",
        "news_media": "NewsMediaExtractor",
        "company_profile": "CompanyProfileExtractor",
    }
    
    class_name = shorthand_map.get(extractor_type.lower(), extractor_type)
    extractor_class = EXTRACTOR_REGISTRY.get(class_name)
    
    if not extractor_class:
        raise ValueError(f"Unknown extractor type '{extractor_type}'. Available: {list(shorthand_map.keys())}")
    
    return extractor_class(seed=seed, **kwargs)


def list_extractors_by_coverage() -> Dict[str, List[str]]:
    """List all extractors organized by coverage line."""
    coverage_map: Dict[str, List[str]] = {}
    for name, cls in EXTRACTOR_REGISTRY.items():
        coverage = getattr(cls, "coverage", "unknown")
        if coverage not in coverage_map:
            coverage_map[coverage] = []
        coverage_map[coverage].append(name)
    return coverage_map


def list_extractors_by_signal() -> Dict[str, List[str]]:
    """List all extractors organized by signal they contribute to."""
    signal_map: Dict[str, List[str]] = {}
    for name, cls in EXTRACTOR_REGISTRY.items():
        signals = getattr(cls, "signals", [])
        for signal in signals:
            if signal not in signal_map:
                signal_map[signal] = []
            signal_map[signal].append(name)
    return signal_map


def get_signal_coverage_matrix() -> Dict[str, Dict[str, List[str]]]:
    """Get a matrix of coverage -> signal -> extractors."""
    matrix: Dict[str, Dict[str, List[str]]] = {}
    for name, cls in EXTRACTOR_REGISTRY.items():
        coverage = getattr(cls, "coverage", "unknown")
        signals = getattr(cls, "signals", [])
        if coverage not in matrix:
            matrix[coverage] = {}
        for signal in signals:
            if signal not in matrix[coverage]:
                matrix[coverage][signal] = []
            matrix[coverage][signal].append(name)
    return matrix


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("EXTRACTORS MODULE - COMPREHENSIVE DEMONSTRATION")
    print("=" * 80)
    
    # Summary by coverage
    print("\n--- EXTRACTORS BY COVERAGE ---")
    coverage_map = list_extractors_by_coverage()
    for coverage in sorted(coverage_map.keys()):
        extractors = coverage_map[coverage]
        print(f"\n{coverage.upper()}: {len(extractors)} extractors")
        for ext in extractors:
            cls = EXTRACTOR_REGISTRY[ext]
            signals = getattr(cls, "signals", [])
            print(f"  - {ext}: {signals}")
    
    total_extractors = sum(len(e) for e in coverage_map.values())
    print(f"\n>>> TOTAL EXTRACTORS: {total_extractors}")
    
    # Signal coverage matrix
    print("\n" + "=" * 80)
    print("SIGNAL COVERAGE MATRIX")
    print("=" * 80)
    matrix = get_signal_coverage_matrix()
    for coverage in sorted(matrix.keys()):
        if coverage == "common":
            continue
        print(f"\n{coverage.upper()}:")
        for signal, extractors in sorted(matrix[coverage].items()):
            print(f"  {signal}: {len(extractors)} extractor(s) - {extractors}")
    
    # Sample extractions
    print("\n" + "=" * 80)
    print("SAMPLE EXTRACTIONS")
    print("=" * 80)
    
    samples = [
        ("equasis_operator", {"company_name": "Atlas Shipping"}),
        ("iata_operator", {"operator_name": "Sky Airways"}),
        ("security_scorecard", {"company_name": "TechCorp"}),
        ("sec_edgar", {"company_name": "MegaCorp"}),
        ("ffiec_call_report", {"institution_name": "First Bank"}),
        ("osha_safety", {"company_name": "Energy LLC"}),
        ("state_bar", {"firm_name": "Smith & Associates"}),
    ]
    
    for ext_type, kwargs in samples:
        print(f"\n--- {ext_type} ---")
        ext = get_extractor(ext_type, seed="demo", **kwargs)
        result = ext.extract()
        print(f"Coverage: {ext.coverage}, Signals: {ext.signals}")
        print(f"Data keys: {list(result.raw_data.keys())}")


# =============================================================================
# FINANCIAL INSTITUTIONS EXTRACTORS (10 extractors for 7 signal groups)
# =============================================================================

@register_extractor
class FFIECCallReportExtractor(DataExtractor):
    """FFIEC Call Report - capital ratios, asset quality, earnings. Signals: financial_condition, credit_quality"""
    source_name = "ffiec_call_report"
    coverage = "financial_institutions"
    signals = ["financial_condition", "credit_quality"]

    def extract(self) -> ExtractionResult:
        total_assets = self._weighted_choice([(self._rng.randint(100_000_000, 500_000_000), 0.35), (self._rng.randint(500_000_001, 5_000_000_000), 0.30), (self._rng.randint(5_000_000_001, 50_000_000_000), 0.20), (self._rng.randint(50_000_000_001, 500_000_000_000), 0.12), (self._rng.randint(500_000_000_001, 3_000_000_000_000), 0.03)])
        
        tier1_ratio = round(self._rng.uniform(9.0, 16.0), 2)
        cet1_ratio = round(tier1_ratio - self._rng.uniform(0.5, 2.0), 2)
        total_capital_ratio = round(tier1_ratio + self._rng.uniform(1.0, 3.0), 2)
        
        npa_ratio = round(self._rng.uniform(0.20, 3.50), 2)
        npl_ratio = round(npa_ratio * self._rng.uniform(0.60, 0.90), 2)
        
        raw_data = {
            "institution": {"rssd_id": self.kwargs.get("institution_id", self._random_id("", 10)), "name": self.kwargs.get("institution_name", f"Bank {self._random_id()}"), "charter_type": self._weighted_choice([("National Bank", 0.35), ("State Member", 0.20), ("State Non-Member", 0.25), ("Savings Association", 0.15), ("Credit Union", 0.05)])},
            "balance_sheet": {"total_assets_usd": total_assets, "total_loans_usd": int(total_assets * self._rng.uniform(0.55, 0.75)), "total_deposits_usd": int(total_assets * self._rng.uniform(0.70, 0.88))},
            "capital_ratios": {"cet1_ratio_pct": cet1_ratio, "tier1_ratio_pct": tier1_ratio, "total_capital_ratio_pct": total_capital_ratio, "leverage_ratio_pct": round(self._rng.uniform(7.0, 12.0), 2), "capital_category": "Well Capitalized" if tier1_ratio >= 8.0 else "Adequately Capitalized" if tier1_ratio >= 6.0 else "Undercapitalized"},
            "asset_quality": {"npa_ratio_pct": npa_ratio, "npl_ratio_pct": npl_ratio, "charge_off_ratio_pct": round(self._rng.uniform(0.10, 1.50), 2), "allowance_coverage_pct": round(self._rng.uniform(100, 250), 1)},
            "earnings": {"roa_pct": round(self._rng.uniform(0.60, 1.40), 2), "roe_pct": round(self._rng.uniform(8.0, 15.0), 2), "nim_pct": round(self._rng.uniform(2.5, 4.2), 2), "efficiency_ratio_pct": round(self._rng.uniform(52, 72), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"assets": total_assets, "tier1": tier1_ratio})


@register_extractor
class BankRegulatoryExtractor(DataExtractor):
    """Regulatory status - CAMELS, MRAs, enforcement. Signals: regulatory_compliance"""
    source_name = "bank_regulatory"
    coverage = "financial_institutions"
    signals = ["regulatory_compliance"]

    def extract(self) -> ExtractionResult:
        camels = self._weighted_choice([(1, 0.18), (2, 0.55), (3, 0.18), (4, 0.06), (5, 0.03)])
        num_mras = self._weighted_choice([(0, 0.40), (self._rng.randint(1, 5), 0.35), (self._rng.randint(6, 15), 0.18), (self._rng.randint(16, 30), 0.07)])
        enforcement = self._weighted_choice([(0, 0.85), (1, 0.10), (2, 0.04), (3, 0.01)])
        
        mras = [{"category": self._weighted_choice([("Credit Risk", 0.25), ("BSA/AML", 0.20), ("IT/Cyber", 0.18), ("Liquidity", 0.12), ("Compliance", 0.15), ("Operational", 0.10)]), "severity": self._weighted_choice([("MRA", 0.70), ("MRIA", 0.30)]), "status": self._weighted_choice([("Open", 0.55), ("Closed", 0.35), ("Past Due", 0.10)])} for _ in range(num_mras)]
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "regulatory_status": {"camels_composite": camels, "camels_components": {"capital": self._rng.randint(max(1, camels - 1), min(5, camels + 1)), "asset_quality": self._rng.randint(max(1, camels - 1), min(5, camels + 1)), "management": self._rng.randint(max(1, camels - 1), min(5, camels + 1)), "earnings": self._rng.randint(max(1, camels - 1), min(5, camels + 1)), "liquidity": self._rng.randint(max(1, camels - 1), min(5, camels + 1)), "sensitivity": self._rng.randint(max(1, camels - 1), min(5, camels + 1))}, "last_exam_date": self._random_date(548, 30)},
            "mras_mriaas": {"total_open": sum(1 for m in mras if m["status"] == "Open"), "total_mrias": sum(1 for m in mras if m["severity"] == "MRIA"), "past_due": sum(1 for m in mras if m["status"] == "Past Due"), "details": mras[:15]},
            "enforcement_actions": {"active_actions": enforcement, "action_types": [self._weighted_choice([("Consent Order", 0.35), ("Cease and Desist", 0.25), ("Civil Money Penalty", 0.20), ("Memorandum of Understanding", 0.20)]) for _ in range(enforcement)]},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"camels": camels, "mras": num_mras})


@register_extractor
class FILitigationExtractor(DataExtractor):
    """Financial institution litigation - consumer, class actions, regulatory fines. Signals: litigation"""
    source_name = "fi_litigation"
    coverage = "financial_institutions"
    signals = ["litigation"]

    def extract(self) -> ExtractionResult:
        num_cases = self._weighted_choice([(0, 0.45), (self._rng.randint(1, 5), 0.30), (self._rng.randint(6, 15), 0.18), (self._rng.randint(16, 40), 0.07)])
        cases = []
        for _ in range(num_cases):
            cases.append({"case_type": self._weighted_choice([("Consumer Class Action", 0.25), ("CFPB Enforcement", 0.15), ("Fair Lending", 0.12), ("BSA/AML", 0.12), ("Securities", 0.10), ("Employment", 0.10), ("Other", 0.16)]), "amount_usd": self._weighted_choice([(self._rng.randint(100000, 1000000), 0.40), (self._rng.randint(1000001, 10000000), 0.30), (self._rng.randint(10000001, 100000000), 0.20), (self._rng.randint(100000001, 1000000000), 0.10)]), "status": self._weighted_choice([("Active", 0.40), ("Settled", 0.35), ("Dismissed", 0.25)])})
        
        cfpb_complaints = self._weighted_choice([(self._rng.randint(10, 100), 0.35), (self._rng.randint(101, 500), 0.35), (self._rng.randint(501, 2000), 0.20), (self._rng.randint(2001, 10000), 0.10)])
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "litigation": {"total_cases_5yr": num_cases, "active_cases": sum(1 for c in cases if c["status"] == "Active"), "total_exposure_usd": sum(c["amount_usd"] for c in cases if c["status"] == "Active"), "cases": cases[:15]},
            "consumer_complaints": {"cfpb_complaints_12mo": cfpb_complaints, "complaint_ratio_per_bn_deposits": round(cfpb_complaints / max(1, self._rng.randint(1, 100)), 2), "top_categories": ["Deposits", "Credit Cards", "Mortgages"][:self._rng.randint(1, 3)]},
            "regulatory_fines": {"total_fines_5yr_usd": sum(c["amount_usd"] for c in cases if "CFPB" in c["case_type"] or "BSA" in c["case_type"])},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"cases": num_cases, "complaints": cfpb_complaints})


@register_extractor
class FIGovernanceExtractor(DataExtractor):
    """FI governance - board, audit committee, risk management. Signals: governance"""
    source_name = "fi_governance"
    coverage = "financial_institutions"
    signals = ["governance"]

    def extract(self) -> ExtractionResult:
        board_size = self._rng.randint(7, 15)
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "board": {"size": board_size, "independent_pct": round(self._rng.uniform(60, 90), 1), "financial_expertise_pct": round(self._rng.uniform(40, 70), 1), "avg_tenure_years": round(self._rng.uniform(4, 12), 1), "meetings_per_year": self._rng.randint(8, 15)},
            "committees": {"audit_meetings": self._rng.randint(6, 12), "risk_committee_exists": self._rng.random() < 0.85, "risk_meetings": self._rng.randint(6, 12) if self._rng.random() < 0.85 else 0, "compliance_committee": self._rng.random() < 0.75},
            "risk_management": {"cro_exists": self._rng.random() < 0.80, "cro_reports_to_board": self._rng.random() < 0.60, "erm_framework": self._weighted_choice([("COSO", 0.40), ("ISO 31000", 0.20), ("Custom", 0.30), ("None", 0.10)]), "stress_testing_program": self._rng.random() < 0.75},
            "audit": {"internal_audit_function": True, "external_auditor": self._weighted_choice([("Deloitte", 0.22), ("PwC", 0.20), ("EY", 0.18), ("KPMG", 0.15), ("BDO", 0.10), ("Other", 0.15)]), "audit_findings_open": self._rng.randint(0, 15)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"board_size": board_size})


@register_extractor
class FICyberExtractor(DataExtractor):
    """FI cybersecurity assessment. Signals: cybersecurity"""
    source_name = "fi_cyber"
    coverage = "financial_institutions"
    signals = ["cybersecurity"]

    def extract(self) -> ExtractionResult:
        maturity = self._weighted_choice([(1, 0.08), (2, 0.22), (3, 0.42), (4, 0.22), (5, 0.06)])
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "cyber_maturity": {"ffiec_cat_level": maturity, "assessment_date": self._random_date(365, 0), "inherent_risk_profile": self._weighted_choice([("Least", 0.15), ("Minimal", 0.25), ("Moderate", 0.35), ("Significant", 0.18), ("Most", 0.07)])},
            "security_program": {"ciso_exists": self._rng.random() < 0.78, "security_awareness_training": self._rng.random() < 0.92, "pen_test_frequency": self._weighted_choice([("Annual", 0.40), ("Semi-Annual", 0.30), ("Quarterly", 0.20), ("None", 0.10)]), "vulnerability_scanning": self._weighted_choice([("Continuous", 0.25), ("Weekly", 0.30), ("Monthly", 0.30), ("Quarterly", 0.15)])},
            "incidents": {"cyber_incidents_12mo": self._weighted_choice([(0, 0.50), (self._rng.randint(1, 5), 0.35), (self._rng.randint(6, 15), 0.12), (self._rng.randint(16, 30), 0.03)]), "breaches_requiring_notification": self._weighted_choice([(0, 0.85), (1, 0.12), (2, 0.03)])},
            "vendor_risk": {"critical_vendors": self._rng.randint(5, 30), "vendors_assessed_12mo_pct": round(self._rng.uniform(60, 95), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"maturity": maturity})


@register_extractor
class FIOperationalRiskExtractor(DataExtractor):
    """FI operational risk - systems, controls, incidents. Signals: operational_risk"""
    source_name = "fi_operational"
    coverage = "financial_institutions"
    signals = ["operational_risk"]

    def extract(self) -> ExtractionResult:
        num_incidents = self._weighted_choice([(0, 0.35), (self._rng.randint(1, 10), 0.40), (self._rng.randint(11, 30), 0.18), (self._rng.randint(31, 100), 0.07)])
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "operational_incidents": {"total_12mo": num_incidents, "by_category": {"technology": int(num_incidents * 0.35), "process": int(num_incidents * 0.25), "people": int(num_incidents * 0.20), "external": int(num_incidents * 0.20)}, "losses_usd": self._rng.randint(10000, 5000000) if num_incidents > 0 else 0},
            "systems": {"core_system_age_years": self._rng.randint(3, 20), "system_uptime_pct": round(self._rng.uniform(99.0, 99.99), 3), "disaster_recovery_tested": self._rng.random() < 0.85, "rpo_hours": self._weighted_choice([(1, 0.30), (4, 0.35), (24, 0.25), (72, 0.10)]), "rto_hours": self._weighted_choice([(4, 0.25), (8, 0.35), (24, 0.25), (72, 0.15)])},
            "controls": {"sox_compliant": self._rng.random() < 0.92, "internal_audit_coverage_pct": round(self._rng.uniform(70, 100), 1), "control_deficiencies_open": self._rng.randint(0, 20)},
            "bcp": {"business_continuity_plan": True, "last_test_date": self._random_date(365, 0), "test_result": self._weighted_choice([("Successful", 0.75), ("Partial Success", 0.20), ("Failed", 0.05)])},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"incidents": num_incidents})


@register_extractor
class BSAAMLExtractor(DataExtractor):
    """BSA/AML compliance program. Signals: regulatory_compliance"""
    source_name = "bsa_aml"
    coverage = "financial_institutions"
    signals = ["regulatory_compliance"]

    def extract(self) -> ExtractionResult:
        sars_filed = self._weighted_choice([(self._rng.randint(10, 100), 0.40), (self._rng.randint(101, 500), 0.30), (self._rng.randint(501, 2000), 0.20), (self._rng.randint(2001, 10000), 0.10)])
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "bsa_program": {"bsa_officer": True, "independent_testing": self._rng.random() < 0.92, "training_completion_pct": round(self._rng.uniform(90, 100), 1), "kyc_program": self._weighted_choice([("Enhanced", 0.35), ("Standard", 0.55), ("Basic", 0.10)])},
            "activity": {"sars_filed_12mo": sars_filed, "ctrs_filed_12mo": self._rng.randint(sars_filed // 2, sars_filed * 3), "high_risk_customers": self._rng.randint(50, 2000), "peps_count": self._rng.randint(0, 100)},
            "exam_findings": {"bsa_exam_rating": self._weighted_choice([(1, 0.25), (2, 0.50), (3, 0.18), (4, 0.05), (5, 0.02)]), "open_findings": self._rng.randint(0, 10), "enforcement_history": self._weighted_choice([(0, 0.88), (1, 0.10), (2, 0.02)])},
            "technology": {"transaction_monitoring_system": self._weighted_choice([("Actimize", 0.25), ("Mantas", 0.20), ("SAS", 0.15), ("FICO", 0.15), ("Other", 0.25)]), "automation_level": self._weighted_choice([("High", 0.30), ("Medium", 0.45), ("Low", 0.25)])},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"sars": sars_filed})


@register_extractor
class LiquidityExtractor(DataExtractor):
    """Liquidity management and stress testing. Signals: financial_condition"""
    source_name = "liquidity"
    coverage = "financial_institutions"
    signals = ["financial_condition"]

    def extract(self) -> ExtractionResult:
        lcr = round(self._rng.uniform(100, 180), 1)
        nsfr = round(self._rng.uniform(100, 150), 1)
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "liquidity_ratios": {"lcr_pct": lcr, "nsfr_pct": nsfr, "loan_to_deposit_ratio_pct": round(self._rng.uniform(70, 95), 1), "liquid_assets_to_total_assets_pct": round(self._rng.uniform(15, 35), 1)},
            "funding": {"core_deposits_pct": round(self._rng.uniform(60, 90), 1), "wholesale_funding_pct": round(self._rng.uniform(5, 25), 1), "brokered_deposits_pct": round(self._rng.uniform(0, 15), 1), "fhlb_capacity_usd": self._rng.randint(100_000_000, 10_000_000_000)},
            "stress_testing": {"liquidity_stress_test": self._rng.random() < 0.80, "30_day_survival_days": self._rng.randint(30, 180), "contingency_funding_plan": self._rng.random() < 0.90},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"lcr": lcr})


@register_extractor
class CreditPortfolioExtractor(DataExtractor):
    """Credit portfolio composition and quality. Signals: credit_quality"""
    source_name = "credit_portfolio"
    coverage = "financial_institutions"
    signals = ["credit_quality"]

    def extract(self) -> ExtractionResult:
        total_loans = self._rng.randint(500_000_000, 100_000_000_000)
        
        raw_data = {
            "institution_id": self.kwargs.get("institution_id", self._random_id("RSSD", 10)),
            "portfolio_composition": {"total_loans_usd": total_loans, "cre_pct": round(self._rng.uniform(15, 45), 1), "c_and_i_pct": round(self._rng.uniform(15, 35), 1), "residential_pct": round(self._rng.uniform(10, 35), 1), "consumer_pct": round(self._rng.uniform(5, 20), 1)},
            "concentration": {"top_10_borrowers_pct": round(self._rng.uniform(8, 25), 1), "cre_to_capital_pct": round(self._rng.uniform(100, 400), 1), "construction_to_capital_pct": round(self._rng.uniform(20, 150), 1)},
            "risk_grades": {"pass_pct": round(self._rng.uniform(85, 96), 1), "special_mention_pct": round(self._rng.uniform(1, 6), 1), "substandard_pct": round(self._rng.uniform(1, 5), 1), "doubtful_pct": round(self._rng.uniform(0, 1), 2)},
            "underwriting": {"avg_ltv_cre_pct": round(self._rng.uniform(60, 80), 1), "avg_dscr_cre": round(self._rng.uniform(1.15, 1.50), 2), "exception_rate_pct": round(self._rng.uniform(5, 20), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"total_loans": total_loans})


# =============================================================================
# ENERGY EXTRACTORS (9 extractors for 7 signal groups)
# =============================================================================

@register_extractor
class OSHASafetyExtractor(DataExtractor):
    """OSHA safety records - inspections, violations, injury rates. Signals: safety_performance"""
    source_name = "osha_safety"
    coverage = "energy"
    signals = ["safety_performance"]

    def extract(self) -> ExtractionResult:
        trir = round(self._rng.uniform(0.3, 4.5), 2)
        dart = round(trir * self._rng.uniform(0.4, 0.7), 2)
        fatalities = self._weighted_choice([(0, 0.90), (1, 0.07), (2, 0.02), (self._rng.randint(3, 5), 0.01)])
        
        num_inspections = self._rng.randint(0, 12)
        num_violations = self._weighted_choice([(0, 0.40), (self._rng.randint(1, 10), 0.35), (self._rng.randint(11, 30), 0.18), (self._rng.randint(31, 80), 0.07)])
        
        violations = [{"type": self._weighted_choice([("Serious", 0.45), ("Other-Than-Serious", 0.35), ("Willful", 0.05), ("Repeat", 0.08), ("Failure to Abate", 0.07)]), "category": self._weighted_choice([("Fall Protection", 0.15), ("Hazard Communication", 0.12), ("Scaffolding", 0.10), ("Lockout/Tagout", 0.12), ("Respiratory", 0.10), ("Machine Guarding", 0.08), ("Other", 0.33)]), "penalty_usd": self._weighted_choice([(0, 0.30), (self._rng.randint(1000, 15000), 0.45), (self._rng.randint(15001, 75000), 0.20), (self._rng.randint(75001, 150000), 0.05)])} for _ in range(num_violations)]
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("EST", 10)),
            "injury_rates": {"trir": trir, "dart": dart, "fatalities_3yr": fatalities, "industry_avg_trir": round(self._rng.uniform(1.5, 2.5), 2)},
            "inspections": {"total_3yr": num_inspections, "resulting_in_citation": int(num_inspections * self._rng.uniform(0.3, 0.7))},
            "violations": {"total_3yr": num_violations, "serious": sum(1 for v in violations if v["type"] == "Serious"), "willful_repeat": sum(1 for v in violations if v["type"] in ("Willful", "Repeat")), "total_penalties_usd": sum(v["penalty_usd"] for v in violations), "details": violations[:15]},
            "safety_program": {"written_program": self._rng.random() < 0.92, "jsa_program": self._rng.random() < 0.85, "behavior_based_safety": self._rng.random() < 0.65, "vpp_participant": self._rng.random() < 0.15},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"trir": trir, "violations": num_violations})


@register_extractor
class EPAComplianceExtractor(DataExtractor):
    """EPA environmental compliance - permits, violations, spills. Signals: environmental_compliance"""
    source_name = "epa_compliance"
    coverage = "energy"
    signals = ["environmental_compliance"]

    def extract(self) -> ExtractionResult:
        num_permits = self._rng.randint(3, 25)
        num_violations = self._weighted_choice([(0, 0.45), (self._rng.randint(1, 8), 0.35), (self._rng.randint(9, 25), 0.15), (self._rng.randint(26, 60), 0.05)])
        num_spills = self._weighted_choice([(0, 0.60), (self._rng.randint(1, 5), 0.30), (self._rng.randint(6, 15), 0.08), (self._rng.randint(16, 30), 0.02)])
        
        violations = [{"program": self._weighted_choice([("Clean Air Act", 0.30), ("Clean Water Act", 0.25), ("RCRA", 0.20), ("CERCLA", 0.08), ("TSCA", 0.07), ("EPCRA", 0.10)]), "severity": self._weighted_choice([("Minor", 0.50), ("Moderate", 0.35), ("Major", 0.15)]), "penalty_usd": self._weighted_choice([(0, 0.40), (self._rng.randint(5000, 50000), 0.35), (self._rng.randint(50001, 500000), 0.18), (self._rng.randint(500001, 5000000), 0.07)])} for _ in range(num_violations)]
        
        spills = [{"type": self._weighted_choice([("Oil", 0.45), ("Produced Water", 0.25), ("Chemical", 0.15), ("Other", 0.15)]), "volume_bbls": self._weighted_choice([(self._rng.randint(1, 50), 0.50), (self._rng.randint(51, 500), 0.35), (self._rng.randint(501, 5000), 0.12), (self._rng.randint(5001, 50000), 0.03)]), "reportable": self._rng.random() < 0.70} for _ in range(num_spills)]
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("EPA", 10)),
            "permits": {"total_active": num_permits, "types": {"air": self._rng.randint(1, 10), "npdes": self._rng.randint(0, 5), "rcra": self._rng.randint(0, 3), "uic": self._rng.randint(0, 8)}},
            "violations": {"total_3yr": num_violations, "by_severity": {"major": sum(1 for v in violations if v["severity"] == "Major"), "moderate": sum(1 for v in violations if v["severity"] == "Moderate"), "minor": sum(1 for v in violations if v["severity"] == "Minor")}, "total_penalties_usd": sum(v["penalty_usd"] for v in violations), "details": violations[:15]},
            "spills": {"total_5yr": num_spills, "reportable_spills": sum(1 for s in spills if s["reportable"]), "total_volume_bbls": sum(s["volume_bbls"] for s in spills), "details": spills[:10]},
            "compliance_status": {"overall": "In Compliance" if num_violations < 3 else "Minor Violations" if num_violations < 10 else "Significant Violations", "consent_decrees_active": self._rng.random() < 0.08, "supplemental_environmental_projects": self._rng.random() < 0.12},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"violations": num_violations, "spills": num_spills})


@register_extractor
class StateRegulatoryExtractor(DataExtractor):
    """State regulatory status - permits, enforcement, bonds. Signals: regulatory_standing"""
    source_name = "state_regulatory"
    coverage = "energy"
    signals = ["regulatory_standing"]

    def extract(self) -> ExtractionResult:
        num_states = self._rng.randint(1, 12)
        states = []
        for _ in range(num_states):
            states.append({"state": self._weighted_choice([("Texas", 0.25), ("Oklahoma", 0.12), ("New Mexico", 0.10), ("North Dakota", 0.08), ("Colorado", 0.08), ("Louisiana", 0.07), ("Wyoming", 0.06), ("Other", 0.24)]), "permit_status": self._weighted_choice([("Good Standing", 0.85), ("Conditional", 0.10), ("Probation", 0.04), ("Revoked", 0.01)]), "violations_12mo": self._weighted_choice([(0, 0.55), (self._rng.randint(1, 5), 0.30), (self._rng.randint(6, 15), 0.12), (self._rng.randint(16, 30), 0.03)]), "bond_amount_usd": self._rng.randint(50000, 5000000)})
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("OP", 8)),
            "operating_states": {"count": num_states, "details": states},
            "aggregate_status": {"states_good_standing": sum(1 for s in states if s["permit_status"] == "Good Standing"), "total_violations": sum(s["violations_12mo"] for s in states), "total_bonds_usd": sum(s["bond_amount_usd"] for s in states)},
            "enforcement": {"notices_of_violation_12mo": self._weighted_choice([(0, 0.55), (self._rng.randint(1, 5), 0.30), (self._rng.randint(6, 15), 0.12), (self._rng.randint(16, 30), 0.03)]), "administrative_orders": self._weighted_choice([(0, 0.85), (1, 0.10), (2, 0.04), (3, 0.01)])},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"states": num_states})


@register_extractor
class ProductionDataExtractor(DataExtractor):
    """Oil & gas production data - volumes, wells, basins. Signals: operational_quality, asset_quality"""
    source_name = "production_data"
    coverage = "energy"
    signals = ["operational_quality", "asset_quality"]

    def extract(self) -> ExtractionResult:
        production_boed = self._weighted_choice([(self._rng.randint(500, 10000), 0.35), (self._rng.randint(10001, 50000), 0.30), (self._rng.randint(50001, 200000), 0.20), (self._rng.randint(200001, 1000000), 0.12), (self._rng.randint(1000001, 5000000), 0.03)])
        oil_pct = self._rng.uniform(0.20, 0.80)
        
        active_wells = self._weighted_choice([(self._rng.randint(10, 100), 0.35), (self._rng.randint(101, 500), 0.30), (self._rng.randint(501, 2000), 0.20), (self._rng.randint(2001, 10000), 0.12), (self._rng.randint(10001, 50000), 0.03)])
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("OP", 8)),
            "production": {"total_boed": production_boed, "oil_bopd": int(production_boed * oil_pct), "gas_mcfd": int(production_boed * (1 - oil_pct) * 6), "ngl_boed": int(production_boed * self._rng.uniform(0.05, 0.15)), "pct_oil": round(oil_pct * 100, 1)},
            "wells": {"total_active": active_wells, "producing": int(active_wells * 0.85), "injection": int(active_wells * 0.10), "shut_in": int(active_wells * 0.05), "average_age_years": round(self._rng.uniform(3, 15), 1)},
            "basins": {"primary": self._weighted_choice([("Permian", 0.30), ("Eagle Ford", 0.12), ("Bakken", 0.10), ("DJ Basin", 0.08), ("Marcellus", 0.08), ("SCOOP/STACK", 0.07), ("Other", 0.25)]), "diversification_score": self._rng.randint(1, 5)},
            "operational_metrics": {"production_per_well_boed": round(production_boed / max(1, active_wells), 1), "decline_rate_pct": round(self._rng.uniform(15, 45), 1), "uptime_pct": round(self._rng.uniform(92, 99), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"production": production_boed, "wells": active_wells})


@register_extractor
class ReserveDataExtractor(DataExtractor):
    """Reserves and resources data. Signals: asset_quality"""
    source_name = "reserve_data"
    coverage = "energy"
    signals = ["asset_quality"]

    def extract(self) -> ExtractionResult:
        proved_reserves = self._weighted_choice([(self._rng.randint(1_000_000, 10_000_000), 0.35), (self._rng.randint(10_000_001, 100_000_000), 0.30), (self._rng.randint(100_000_001, 500_000_000), 0.20), (self._rng.randint(500_000_001, 2_000_000_000), 0.12), (self._rng.randint(2_000_000_001, 10_000_000_000), 0.03)])
        
        production = proved_reserves / self._rng.uniform(6, 15)  # Reserve life calculation
        reserve_life = proved_reserves / max(1, production)
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("OP", 8)),
            "reserves": {"proved_reserves_boe": proved_reserves, "proved_developed_pct": round(self._rng.uniform(50, 85), 1), "proved_undeveloped_pct": round(self._rng.uniform(15, 50), 1), "pv10_usd": int(proved_reserves * self._rng.uniform(8, 18))},
            "reserve_metrics": {"reserve_life_years": round(reserve_life, 1), "reserve_replacement_ratio": round(self._rng.uniform(0.60, 1.50), 2), "finding_cost_per_boe_usd": round(self._rng.uniform(5, 20), 2)},
            "resource_potential": {"probable_reserves_boe": int(proved_reserves * self._rng.uniform(0.30, 0.80)), "contingent_resources_boe": int(proved_reserves * self._rng.uniform(0.50, 2.00))},
            "third_party_audit": {"auditor": self._weighted_choice([("Ryder Scott", 0.25), ("Netherland Sewell", 0.25), ("DeGolyer MacNaughton", 0.20), ("NSAI", 0.15), ("Other", 0.15)]), "audit_date": self._random_date(365, 0)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"reserves": proved_reserves, "reserve_life": round(reserve_life, 1)})


@register_extractor
class EnergyFinancialExtractor(DataExtractor):
    """Energy company financials. Signals: financial_stability"""
    source_name = "energy_financial"
    coverage = "energy"
    signals = ["financial_stability"]

    def extract(self) -> ExtractionResult:
        production = self._rng.randint(10000, 500000)
        price_per_boe = self._rng.uniform(35, 65)
        revenue = int(production * 365 * price_per_boe)
        ebitdax_margin = self._rng.uniform(0.35, 0.65)
        
        has_hedges = self._rng.random() < 0.80
        hedge_pct = self._rng.uniform(0.30, 0.80) if has_hedges else 0
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("OP", 8)),
            "financials": {"revenue_usd": revenue, "ebitdax_usd": int(revenue * ebitdax_margin), "ebitdax_margin_pct": round(ebitdax_margin * 100, 1), "capex_usd": int(revenue * self._rng.uniform(0.30, 0.70))},
            "leverage": {"total_debt_usd": int(revenue * self._rng.uniform(0.50, 2.00)), "debt_to_ebitdax": round(self._rng.uniform(1.0, 4.0), 2), "interest_coverage": round(self._rng.uniform(2.0, 8.0), 2), "borrowing_base_usd": int(revenue * self._rng.uniform(0.60, 1.20))},
            "hedging": {"hedged": has_hedges, "next_12mo_hedged_pct": round(hedge_pct * 100, 1), "avg_hedge_price_oil_usd": round(self._rng.uniform(55, 80), 2) if has_hedges else None, "hedge_value_usd": int(production * 365 * hedge_pct * self._rng.uniform(-5, 10)) if has_hedges else 0},
            "credit": {"has_rating": self._rng.random() < 0.35, "rating": self._weighted_choice([("BB+", 0.15), ("BB", 0.25), ("BB-", 0.25), ("B+", 0.20), ("B", 0.15)]) if self._rng.random() < 0.35 else None, "rbl_availability_pct": round(self._rng.uniform(30, 80), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"revenue": revenue})


@register_extractor
class ESGMetricsExtractor(DataExtractor):
    """ESG metrics - emissions, sustainability, community. Signals: esg_factors"""
    source_name = "esg_metrics"
    coverage = "energy"
    signals = ["esg_factors"]

    def extract(self) -> ExtractionResult:
        ghg_intensity = round(self._rng.uniform(15, 45), 1)  # kg CO2e per BOE
        methane_intensity = round(self._rng.uniform(0.10, 0.80), 2)  # %
        flaring_intensity = round(self._rng.uniform(0.5, 5.0), 2)  # mcf per bbl
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("OP", 8)),
            "emissions": {"ghg_intensity_kg_co2e_boe": ghg_intensity, "methane_intensity_pct": methane_intensity, "flaring_intensity_mcf_bbl": flaring_intensity, "scope_1_emissions_mtco2e": self._rng.randint(10000, 5000000), "scope_2_emissions_mtco2e": self._rng.randint(1000, 500000)},
            "environmental": {"freshwater_intensity_bbl_boe": round(self._rng.uniform(0.5, 3.0), 2), "recycled_water_pct": round(self._rng.uniform(20, 80), 1), "spill_rate_per_1000_wells": round(self._rng.uniform(0.5, 5.0), 2)},
            "social": {"employee_safety_trir": round(self._rng.uniform(0.3, 2.5), 2), "diversity_pct": round(self._rng.uniform(15, 45), 1), "community_investment_usd": self._rng.randint(100000, 10000000)},
            "governance": {"esg_committee": self._rng.random() < 0.65, "sustainability_report": self._rng.random() < 0.70, "climate_disclosure": self._weighted_choice([("TCFD", 0.35), ("CDP", 0.25), ("Both", 0.15), ("None", 0.25)])},
            "targets": {"net_zero_commitment": self._rng.random() < 0.45, "emissions_reduction_target_pct": self._rng.randint(15, 50) if self._rng.random() < 0.55 else None, "methane_reduction_target": self._rng.random() < 0.60},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"ghg_intensity": ghg_intensity})


@register_extractor
class OperationsMetricsExtractor(DataExtractor):
    """Operational efficiency metrics. Signals: operational_quality"""
    source_name = "operations_metrics"
    coverage = "energy"
    signals = ["operational_quality"]

    def extract(self) -> ExtractionResult:
        loe = round(self._rng.uniform(5, 18), 2)  # $/BOE
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("OP", 8)),
            "costs": {"loe_per_boe_usd": loe, "gathering_transport_per_boe_usd": round(self._rng.uniform(1, 5), 2), "production_tax_per_boe_usd": round(self._rng.uniform(2, 8), 2), "total_cash_cost_per_boe_usd": round(loe + self._rng.uniform(5, 15), 2)},
            "efficiency": {"drilling_days_avg": self._rng.randint(8, 25), "completion_stages_per_day": round(self._rng.uniform(3, 8), 1), "ip_30_boed_avg": self._rng.randint(500, 2500), "well_cost_usd": self._rng.randint(4000000, 12000000)},
            "reliability": {"uptime_pct": round(self._rng.uniform(92, 99), 1), "unplanned_downtime_pct": round(self._rng.uniform(1, 6), 1), "artificial_lift_pct": round(self._rng.uniform(40, 85), 1)},
            "capital_efficiency": {"capex_per_flowing_boe_usd": self._rng.randint(15000, 50000), "recycle_ratio": round(self._rng.uniform(1.2, 3.5), 2)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"loe": loe})


@register_extractor
class WellIntegrityExtractor(DataExtractor):
    """Well integrity and abandonment status. Signals: asset_quality, environmental_compliance"""
    source_name = "well_integrity"
    coverage = "energy"
    signals = ["asset_quality", "environmental_compliance"]

    def extract(self) -> ExtractionResult:
        total_wells = self._rng.randint(50, 5000)
        orphan_wells = int(total_wells * self._rng.uniform(0.01, 0.08))
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("OP", 8)),
            "well_inventory": {"total_wells": total_wells, "active": int(total_wells * 0.75), "temporarily_abandoned": int(total_wells * 0.15), "permanently_abandoned": int(total_wells * 0.10)},
            "integrity": {"integrity_tests_passed_pct": round(self._rng.uniform(92, 99.5), 1), "sustained_casing_pressure_wells": self._rng.randint(0, int(total_wells * 0.05)), "remediation_required": self._rng.randint(0, int(total_wells * 0.03))},
            "abandonment": {"aro_liability_usd": total_wells * self._rng.randint(30000, 150000), "plugging_backlog": self._rng.randint(0, int(total_wells * 0.05)), "orphan_wells": orphan_wells, "aro_funding_pct": round(self._rng.uniform(50, 100), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"wells": total_wells, "orphan": orphan_wells})


# =============================================================================
# PROFESSIONAL INDEMNITY EXTRACTORS (9 extractors for 7 signal groups)
# =============================================================================

@register_extractor
class StateBarExtractor(DataExtractor):
    """State bar/licensing board - license status, disciplinary history. Signals: regulatory_standing"""
    source_name = "state_bar"
    coverage = "professional_indemnity"
    signals = ["regulatory_standing"]

    def extract(self) -> ExtractionResult:
        entity_type = self.kwargs.get("entity_type", "firm")
        profession = self._weighted_choice([("Attorney", 0.45), ("CPA", 0.25), ("Architect", 0.12), ("Engineer", 0.10), ("Other", 0.08)])
        
        if entity_type == "firm":
            num_professionals = self._weighted_choice([(self._rng.randint(1, 5), 0.35), (self._rng.randint(6, 25), 0.30), (self._rng.randint(26, 100), 0.20), (self._rng.randint(101, 500), 0.12), (self._rng.randint(501, 2000), 0.03)])
            disciplinary_actions = self._weighted_choice([(0, 0.75), (1, 0.15), (self._rng.randint(2, 5), 0.08), (self._rng.randint(6, 12), 0.02)])
        else:
            num_professionals = 1
            disciplinary_actions = self._weighted_choice([(0, 0.88), (1, 0.08), (2, 0.03), (3, 0.01)])
        
        actions = [{"action_type": self._weighted_choice([("Private Reprimand", 0.35), ("Public Reprimand", 0.25), ("Suspension", 0.20), ("Probation", 0.12), ("Disbarment/Revocation", 0.08)]), "date": self._random_date(1825, 30), "basis": self._weighted_choice([("Negligence", 0.30), ("Trust Account", 0.15), ("Conflict of Interest", 0.12), ("Failure to Communicate", 0.12), ("Criminal Conviction", 0.08), ("Other", 0.23)])} for _ in range(disciplinary_actions)]
        
        raw_data = {
            "entity": {"entity_type": entity_type, "firm_name": self.kwargs.get("firm_name", f"Professional Firm {self._random_id()}"), "profession_type": profession, "num_professionals": num_professionals, "states_licensed": self._rng.randint(1, 12) if entity_type == "firm" else self._rng.randint(1, 4)},
            "license_status": {"status": self._weighted_choice([("Active", 0.94), ("Inactive", 0.03), ("Suspended", 0.02), ("Revoked", 0.01)]), "years_licensed": self._rng.randint(3, 40)},
            "disciplinary_history": {"total_actions": disciplinary_actions, "serious_actions": sum(1 for a in actions if a["action_type"] in ("Suspension", "Disbarment/Revocation")), "actions": actions},
            "standing": {"good_standing": disciplinary_actions == 0 or all(a["action_type"] == "Private Reprimand" for a in actions)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"profession": profession, "disciplinary": disciplinary_actions})


@register_extractor
class MalpracticeClaimsExtractor(DataExtractor):
    """Malpractice claims history. Signals: claims_history"""
    source_name = "malpractice_claims"
    coverage = "professional_indemnity"
    signals = ["claims_history"]

    def extract(self) -> ExtractionResult:
        num_claims = self._weighted_choice([(0, 0.55), (1, 0.22), (2, 0.12), (self._rng.randint(3, 6), 0.08), (self._rng.randint(7, 15), 0.03)])
        
        claims = []
        for _ in range(num_claims):
            claimed = self._weighted_choice([(self._rng.randint(25000, 250000), 0.45), (self._rng.randint(250001, 1000000), 0.30), (self._rng.randint(1000001, 5000000), 0.18), (self._rng.randint(5000001, 25000000), 0.07)])
            status = self._weighted_choice([("Closed - No Payment", 0.35), ("Closed - Settled", 0.30), ("Closed - Judgment", 0.08), ("Open", 0.22), ("Reserved", 0.05)])
            paid = int(claimed * self._rng.uniform(0.15, 0.60)) if "Settled" in status or "Judgment" in status else 0
            claims.append({"claim_type": self._weighted_choice([("Malpractice", 0.50), ("Breach of Fiduciary Duty", 0.15), ("Breach of Contract", 0.12), ("Negligent Misrepresentation", 0.10), ("Fraud", 0.05), ("Other", 0.08)]), "claim_date": self._random_date(1825, 30), "claimed_usd": claimed, "paid_usd": paid, "status": status, "allocated_expense_usd": self._rng.randint(10000, 200000)})
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "claims_summary": {"total_claims_5yr": num_claims, "open_claims": sum(1 for c in claims if c["status"] == "Open"), "claims_with_payment": sum(1 for c in claims if c["paid_usd"] > 0), "total_incurred_usd": sum(c["claimed_usd"] for c in claims), "total_paid_usd": sum(c["paid_usd"] for c in claims), "total_expense_usd": sum(c["allocated_expense_usd"] for c in claims)},
            "claims": claims,
            "frequency_metrics": {"claims_per_professional": round(num_claims / max(1, self.kwargs.get("num_professionals", 10)), 3), "avg_claim_size_usd": round(sum(c["claimed_usd"] for c in claims) / max(1, num_claims), 0)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"claims": num_claims})


@register_extractor
class NetworkAuthorityExtractor(DataExtractor):
    """Panel memberships and network authority. Signals: network_authority"""
    source_name = "network_authority"
    coverage = "professional_indemnity"
    signals = ["network_authority"]

    def extract(self) -> ExtractionResult:
        profession = self.kwargs.get("profession", "Attorney")
        
        # Panel memberships vary by profession
        if profession == "Attorney":
            panels = [{"panel_name": self._weighted_choice([("Insurance Defense", 0.25), ("Corporate Counsel", 0.20), ("Litigation", 0.15), ("Real Estate", 0.12), ("Employment", 0.10), ("IP", 0.08), ("Other", 0.10)]), "tier": self._weighted_choice([("Primary", 0.40), ("Secondary", 0.35), ("Approved", 0.25)]), "years_on_panel": self._rng.randint(1, 15)} for _ in range(self._rng.randint(0, 8))]
        elif profession == "CPA":
            panels = [{"panel_name": self._weighted_choice([("SEC Audit", 0.20), ("Tax Advisory", 0.25), ("Forensic Accounting", 0.15), ("M&A Due Diligence", 0.15), ("SOX Compliance", 0.15), ("Other", 0.10)]), "tier": self._weighted_choice([("Approved", 0.50), ("Preferred", 0.35), ("Exclusive", 0.15)]), "years_on_panel": self._rng.randint(1, 12)} for _ in range(self._rng.randint(0, 6))]
        else:
            panels = [{"panel_name": self._weighted_choice([("Government Contracts", 0.30), ("Commercial", 0.35), ("Industrial", 0.20), ("Other", 0.15)]), "tier": self._weighted_choice([("Approved", 0.55), ("Preferred", 0.30), ("Primary", 0.15)]), "years_on_panel": self._rng.randint(1, 10)} for _ in range(self._rng.randint(0, 5))]
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "panel_memberships": {"total_panels": len(panels), "primary_panels": sum(1 for p in panels if p["tier"] == "Primary"), "panels": panels},
            "referral_network": {"referral_sources": self._rng.randint(5, 50), "repeat_client_pct": round(self._rng.uniform(30, 75), 1), "client_tenure_avg_years": round(self._rng.uniform(2, 10), 1)},
            "authority_indicators": {"ranking": self._weighted_choice([("Am Law 100", 0.08), ("Am Law 200", 0.12), ("Regional Leader", 0.25), ("Recognized", 0.30), ("Emerging", 0.25)]) if profession == "Attorney" else self._weighted_choice([("Big 4", 0.05), ("National", 0.15), ("Regional", 0.35), ("Local", 0.45)]), "chambers_ranking": self._rng.random() < 0.25, "industry_awards": self._rng.randint(0, 8)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"panels": len(panels)})


@register_extractor
class PeerReviewExtractor(DataExtractor):
    """Peer review and quality assurance. Signals: peer_review"""
    source_name = "peer_review"
    coverage = "professional_indemnity"
    signals = ["peer_review"]

    def extract(self) -> ExtractionResult:
        num_reviews = self._rng.randint(1, 5)
        reviews = []
        for i in range(num_reviews):
            rating = self._weighted_choice([("Pass", 0.70), ("Pass with Deficiencies", 0.20), ("Fail", 0.07), ("Modified", 0.03)])
            findings = self._rng.randint(0, 8) if rating != "Pass" else 0
            reviews.append({"review_date": self._random_date(365 * (i + 1), 365 * i), "review_type": self._weighted_choice([("System Review", 0.45), ("Engagement Review", 0.35), ("Quality Review", 0.20)]), "rating": rating, "findings": findings, "significant_findings": self._rng.randint(0, min(2, findings))})
        
        most_recent = max(reviews, key=lambda x: x["review_date"])
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("FRM", 8)),
            "current_status": {"most_recent_rating": most_recent["rating"], "most_recent_date": most_recent["review_date"], "in_good_standing": most_recent["rating"] in ("Pass", "Pass with Deficiencies")},
            "review_history": {"total_reviews": num_reviews, "consecutive_pass": sum(1 for r in sorted(reviews, key=lambda x: x["review_date"], reverse=True) if r["rating"] == "Pass"), "reviews": reviews},
            "quality_indicators": {"findings_last_review": most_recent["findings"], "trend": "Improving" if len(reviews) > 1 and reviews[-1]["findings"] < reviews[-2]["findings"] else "Stable" if len(reviews) > 1 else "N/A"},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"rating": most_recent["rating"]})


@register_extractor
class QualityManagementExtractor(DataExtractor):
    """Quality management systems and certifications. Signals: quality_management"""
    source_name = "quality_management"
    coverage = "professional_indemnity"
    signals = ["quality_management"]

    def extract(self) -> ExtractionResult:
        has_qms = self._rng.random() < 0.72
        
        certifications = []
        for cert in ["ISO 9001", "ISO 17025", "AICPA QC Standards", "Professional Standards"]:
            if self._rng.random() < 0.30:
                certifications.append({"certification": cert, "status": self._weighted_choice([("Current", 0.88), ("Expired", 0.07), ("In Progress", 0.05)]), "scope": self._weighted_choice([("Firm-wide", 0.65), ("Practice Area", 0.25), ("Office", 0.10)])})
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "qms": {"has_documented_qms": has_qms, "qms_type": self._weighted_choice([("ISO-based", 0.30), ("Professional Standard", 0.35), ("Custom", 0.25), ("None", 0.10)]) if has_qms else "None", "last_internal_audit": self._random_date(365, 0) if has_qms else None},
            "certifications": certifications,
            "quality_metrics": {"engagement_quality_reviews_pct": round(self._rng.uniform(5, 25), 1), "quality_issues_12mo": self._rng.randint(0, 10), "client_complaints_12mo": self._rng.randint(0, 8)},
            "procedures": {"engagement_acceptance": self._rng.random() < 0.85, "conflict_check": self._rng.random() < 0.95, "supervision_protocols": self._rng.random() < 0.82, "file_review_policy": self._rng.random() < 0.78},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"has_qms": has_qms, "certs": len(certifications)})


@register_extractor
class ClientQualityExtractor(DataExtractor):
    """Client quality and concentration. Signals: client_quality"""
    source_name = "client_quality"
    coverage = "professional_indemnity"
    signals = ["client_quality"]

    def extract(self) -> ExtractionResult:
        num_clients = self._weighted_choice([(self._rng.randint(10, 50), 0.35), (self._rng.randint(51, 200), 0.30), (self._rng.randint(201, 500), 0.20), (self._rng.randint(501, 2000), 0.12), (self._rng.randint(2001, 10000), 0.03)])
        top_client_pct = self._rng.uniform(5, 35)
        top_10_pct = self._rng.uniform(max(15, top_client_pct), min(80, top_client_pct + 40))
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "client_base": {"total_active_clients": num_clients, "new_clients_12mo": int(num_clients * self._rng.uniform(0.10, 0.30)), "client_retention_pct": round(self._rng.uniform(75, 95), 1)},
            "concentration": {"top_client_revenue_pct": round(top_client_pct, 1), "top_10_clients_revenue_pct": round(top_10_pct, 1), "single_industry_exposure_pct": round(self._rng.uniform(10, 50), 1)},
            "client_profile": {"public_company_clients": self._rng.randint(0, int(num_clients * 0.15)), "regulated_industry_pct": round(self._rng.uniform(10, 60), 1), "high_risk_clients_pct": round(self._rng.uniform(2, 15), 1)},
            "billing": {"realization_rate_pct": round(self._rng.uniform(85, 98), 1), "collection_rate_pct": round(self._rng.uniform(90, 99), 1), "avg_matter_size_usd": self._rng.randint(5000, 500000)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"clients": num_clients, "concentration": round(top_client_pct, 1)})


@register_extractor
class ProfessionalDevelopmentExtractor(DataExtractor):
    """CPE and professional development. Signals: professional_development"""
    source_name = "professional_development"
    coverage = "professional_indemnity"
    signals = ["professional_development"]

    def extract(self) -> ExtractionResult:
        num_professionals = self.kwargs.get("num_professionals", self._rng.randint(5, 100))
        cpe_compliance_pct = round(self._rng.uniform(92, 100), 1)
        
        specializations = []
        for spec in ["Tax", "Audit", "Litigation", "Corporate", "Real Estate", "IP", "Employment", "Healthcare"]:
            if self._rng.random() < 0.35:
                specializations.append({"area": spec, "certified_professionals": self._rng.randint(1, max(1, num_professionals // 4)), "credentials": self._weighted_choice([("Board Certified", 0.20), ("Specialized Training", 0.40), ("Experience-based", 0.40)])})
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "cpe_status": {"compliance_pct": cpe_compliance_pct, "avg_cpe_hours_per_professional": self._rng.randint(30, 60), "ethics_hours_avg": round(self._rng.uniform(2, 6), 1)},
            "specializations": {"areas": specializations, "board_certified_count": sum(s["certified_professionals"] for s in specializations if s["credentials"] == "Board Certified")},
            "training": {"internal_training_hours_avg": self._rng.randint(15, 60), "external_conferences_per_year": self._rng.randint(1, 6), "mentorship_program": self._rng.random() < 0.55},
            "credentials": {"advanced_degrees_pct": round(self._rng.uniform(10, 50), 1), "dual_licensed_pct": round(self._rng.uniform(5, 25), 1)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"cpe_compliance": cpe_compliance_pct})


@register_extractor
class PIFinancialExtractor(DataExtractor):
    """Professional firm financials. Signals: claims_history (exposure context)"""
    source_name = "pi_financial"
    coverage = "professional_indemnity"
    signals = ["claims_history"]

    def extract(self) -> ExtractionResult:
        num_professionals = self.kwargs.get("num_professionals", self._rng.randint(5, 100))
        revenue_per_professional = self._rng.randint(150000, 800000)
        revenue = num_professionals * revenue_per_professional
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "financials": {"revenue_usd": revenue, "revenue_per_professional_usd": revenue_per_professional, "profit_margin_pct": round(self._rng.uniform(15, 45), 1), "billable_hours_avg": self._rng.randint(1600, 2200)},
            "staff": {"num_professionals": num_professionals, "leverage_ratio": round(self._rng.uniform(1.0, 3.5), 2), "turnover_pct": round(self._rng.uniform(8, 25), 1)},
            "insurance": {"current_pi_limit_usd": self._weighted_choice([(1000000, 0.25), (2000000, 0.30), (5000000, 0.25), (10000000, 0.15), (25000000, 0.05)]), "retention_usd": self._weighted_choice([(10000, 0.25), (25000, 0.30), (50000, 0.25), (100000, 0.15), (250000, 0.05)]), "prior_coverage_years": self._rng.randint(5, 30)},
        }
        return ExtractionResult(source=self.source_name, source_type="database", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"revenue": revenue})


# =============================================================================
# COMMON/SHARED EXTRACTORS (applicable across coverage lines)
# =============================================================================

@register_extractor
class CreditRatingExtractor(DataExtractor):
    """Credit rating agency data. Signals: financial_stability (all coverages)"""
    source_name = "credit_rating"
    coverage = "common"
    signals = ["financial_stability"]

    def extract(self) -> ExtractionResult:
        is_rated = self._rng.random() < 0.40
        ratings = []
        if is_rated:
            for agency in self._rng.sample(["Moody's", "S&P", "Fitch"], k=self._rng.randint(1, 3)):
                rating_idx = self._weighted_choice([(self._rng.randint(0, 5), 0.20), (self._rng.randint(6, 9), 0.35), (self._rng.randint(10, 14), 0.30), (self._rng.randint(15, 20), 0.15)])
                ratings_scale = {"Moody's": ["Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3", "Baa1", "Baa2", "Baa3", "Ba1", "Ba2", "Ba3", "B1", "B2", "B3", "Caa1", "Caa2", "Caa3", "Ca", "C"], "S&P": ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "D"], "Fitch": ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "D"]}
                rating = ratings_scale[agency][min(rating_idx, len(ratings_scale[agency]) - 1)]
                ratings.append({"agency": agency, "rating": rating, "outlook": self._weighted_choice([("Stable", 0.60), ("Positive", 0.15), ("Negative", 0.20), ("Watch", 0.05)]), "investment_grade": rating_idx <= 9})
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "rating_status": {"is_rated": is_rated, "investment_grade": any(r["investment_grade"] for r in ratings) if ratings else None},
            "ratings": ratings,
            "rating_history": {"upgrades_3yr": self._rng.randint(0, 2) if is_rated else 0, "downgrades_3yr": self._rng.randint(0, 3) if is_rated else 0},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"is_rated": is_rated})


@register_extractor
class NewsMediaExtractor(DataExtractor):
    """News and media monitoring. Signals: public_record (all coverages)"""
    source_name = "news_media"
    coverage = "common"
    signals = ["public_record"]

    def extract(self) -> ExtractionResult:
        num_articles = self._weighted_choice([(self._rng.randint(0, 20), 0.40), (self._rng.randint(21, 100), 0.35), (self._rng.randint(101, 500), 0.18), (self._rng.randint(501, 2000), 0.07)])
        
        sentiment_scores = [self._weighted_choice([(self._rng.uniform(0.7, 1.0), 0.30), (self._rng.uniform(0.4, 0.7), 0.45), (self._rng.uniform(0.0, 0.4), 0.25)]) for _ in range(min(num_articles, 50))]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
        
        adverse_count = sum(1 for s in sentiment_scores if s < 0.4)
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "coverage_summary": {"total_articles_12mo": num_articles, "avg_sentiment_score": round(avg_sentiment, 3), "positive_pct": round(sum(1 for s in sentiment_scores if s >= 0.7) / max(1, len(sentiment_scores)) * 100, 1), "negative_pct": round(adverse_count / max(1, len(sentiment_scores)) * 100, 1)},
            "adverse_media": {"adverse_article_count": adverse_count, "significant_adverse_news": adverse_count > num_articles * 0.15 and num_articles > 10, "regulatory_mentions": self._rng.randint(0, num_articles // 10), "litigation_mentions": self._rng.randint(0, num_articles // 15)},
            "media_risk": {"risk_score": round((1 - avg_sentiment) * 100, 1), "trend": self._weighted_choice([("Improving", 0.25), ("Stable", 0.55), ("Worsening", 0.20)])},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"articles": num_articles, "sentiment": round(avg_sentiment, 3)})


@register_extractor
class CorporateRegistryExtractor(DataExtractor):
    """Corporate registry data - formation, officers, registered agent. Signals: governance (multiple coverages)"""
    source_name = "corporate_registry"
    coverage = "common"
    signals = ["governance"]

    def extract(self) -> ExtractionResult:
        formation_year = self._rng.randint(1950, 2023)
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "entity_details": {"legal_name": self.kwargs.get("company_name", f"Entity {self._random_id()}"), "entity_type": self._weighted_choice([("Corporation", 0.45), ("LLC", 0.35), ("Partnership", 0.10), ("Other", 0.10)]), "state_of_formation": self._weighted_choice([("Delaware", 0.35), ("Nevada", 0.10), ("Wyoming", 0.05), ("Texas", 0.08), ("California", 0.10), ("New York", 0.08), ("Other", 0.24)]), "formation_date": f"{formation_year}-{self._rng.randint(1, 12):02d}-{self._rng.randint(1, 28):02d}"},
            "status": {"good_standing": self._rng.random() < 0.95, "status": self._weighted_choice([("Active", 0.94), ("Inactive", 0.03), ("Dissolved", 0.02), ("Suspended", 0.01)]), "annual_report_current": self._rng.random() < 0.92},
            "officers": {"registered_agent": f"Agent Services {self._random_id('', 4)}", "officers_count": self._rng.randint(2, 10), "directors_count": self._rng.randint(3, 12)},
            "filings": {"recent_amendments": self._rng.randint(0, 5), "ucc_filings": self._rng.randint(0, 10)},
        }
        return ExtractionResult(source=self.source_name, source_type="api", timestamp=datetime.now().isoformat(), raw_data=raw_data, metadata={"years_in_business": 2024 - formation_year})


# =============================================================================
# FACTORY FUNCTIONS AND UTILITIES
# =============================================================================

def get_extractor(extractor_type: str, seed: Optional[str] = None, **kwargs) -> DataExtractor:
    """Factory function to instantiate extractors by name or shorthand."""
    shorthand_map = {
        # Marine
        "equasis_operator": "EquasisOperatorExtractor", "psc_inspection": "PSCInspectionExtractor",
        "ais_tracking": "AISTrackingExtractor", "sanctions_screening": "SanctionsScreeningExtractor",
        "classification_society": "ClassificationSocietyExtractor", "pi_club": "PIClubExtractor",
        "marine_financial": "MarineFinancialExtractor", "ism_compliance": "ISMComplianceExtractor",
        "vessel_valuation": "VesselValuationExtractor", "flag_state_performance": "FlagStatePerformanceExtractor",
        # Aerospace
        "iata_operator": "IATAOperatorExtractor", "aviation_safety": "AviationSafetyExtractor",
        "faa_registry": "FAARegistryExtractor", "aircraft_fleet": "AircraftFleetExtractor",
        "mro_provider": "MROProviderExtractor", "crew_training": "CrewTrainingExtractor",
        "operational_performance": "OperationalPerformanceExtractor", "aviation_financial": "AviationFinancialExtractor",
        # Cyber
        "security_scorecard": "SecurityScorecardExtractor", "cve_exposure": "CVEExposureExtractor",
        "breach_database": "BreachDatabaseExtractor", "cyber_governance": "CyberGovernanceExtractor",
        "vendor_security": "VendorSecurityExtractor", "incident_response": "IncidentResponseExtractor",
        "threat_intelligence": "ThreatIntelligenceExtractor", "cyber_insurance_history": "CyberInsuranceHistoryExtractor",
        # D&O
        "sec_edgar": "SECEdgarExtractor", "litigation_database": "LitigationDatabaseExtractor",
        "proxy_statement": "ProxyStatementExtractor", "insider_activity": "InsiderActivityExtractor",
        "sec_enforcement": "SECEnforcementExtractor", "industry_comparison": "IndustryComparisonExtractor",
        "do_financial": "DOFinancialExtractor",
        # Financial Institutions
        "ffiec_call_report": "FFIECCallReportExtractor", "bank_regulatory": "BankRegulatoryExtractor",
        "fi_litigation": "FILitigationExtractor", "fi_governance": "FIGovernanceExtractor",
        "fi_cyber": "FICyberExtractor", "fi_operational": "FIOperationalRiskExtractor",
        "bsa_aml": "BSAAMLExtractor", "liquidity": "LiquidityExtractor", "credit_portfolio": "CreditPortfolioExtractor",
        # Energy
        "osha_safety": "OSHASafetyExtractor", "epa_compliance": "EPAComplianceExtractor",
        "state_regulatory": "StateRegulatoryExtractor", "production_data": "ProductionDataExtractor",
        "reserve_data": "ReserveDataExtractor", "energy_financial": "EnergyFinancialExtractor",
        "esg_metrics": "ESGMetricsExtractor", "operations_metrics": "OperationsMetricsExtractor",
        "well_integrity": "WellIntegrityExtractor",
        # Professional Indemnity
        "state_bar": "StateBarExtractor", "malpractice_claims": "MalpracticeClaimsExtractor",
        "network_authority": "NetworkAuthorityExtractor", "peer_review": "PeerReviewExtractor",
        "quality_management": "QualityManagementExtractor", "client_quality": "ClientQualityExtractor",
        "professional_development": "ProfessionalDevelopmentExtractor", "pi_financial": "PIFinancialExtractor",
        # Common
        "credit_rating": "CreditRatingExtractor", "news_media": "NewsMediaExtractor",
        "corporate_registry": "CorporateRegistryExtractor",
    }
    
    class_name = shorthand_map.get(extractor_type.lower(), extractor_type)
    extractor_class = EXTRACTOR_REGISTRY.get(class_name)
    
    if not extractor_class:
        raise ValueError(f"Unknown extractor '{extractor_type}'. Available: {sorted(shorthand_map.keys())}")
    
    return extractor_class(seed=seed, **kwargs)


def list_extractors_by_coverage() -> Dict[str, List[str]]:
    """List all extractors organized by coverage line."""
    coverage_map: Dict[str, List[str]] = {}
    for name, cls in EXTRACTOR_REGISTRY.items():
        coverage = getattr(cls, "coverage", "unknown")
        if coverage not in coverage_map:
            coverage_map[coverage] = []
        coverage_map[coverage].append(name)
    return coverage_map


def list_extractors_by_signal() -> Dict[str, List[str]]:
    """List all extractors organized by signal they contribute to."""
    signal_map: Dict[str, List[str]] = {}
    for name, cls in EXTRACTOR_REGISTRY.items():
        signals = getattr(cls, "signals", [])
        for signal in signals:
            if signal not in signal_map:
                signal_map[signal] = []
            signal_map[signal].append(name)
    return signal_map


def get_extractors_for_coverage(coverage: str) -> List[str]:
    """Get all extractor names for a specific coverage line."""
    return [name for name, cls in EXTRACTOR_REGISTRY.items() if getattr(cls, "coverage", "") == coverage]


def get_extractors_for_signal(signal: str) -> List[str]:
    """Get all extractor names that contribute to a specific signal."""
    return [name for name, cls in EXTRACTOR_REGISTRY.items() if signal in getattr(cls, "signals", [])]


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("EXTRACTORS MODULE - COMPREHENSIVE DEMONSTRATION")
    print("=" * 80)
    
    # Count extractors by coverage
    print("\n--- Extractors by Coverage ---")
    coverage_counts = {}
    for coverage, extractors in sorted(list_extractors_by_coverage().items()):
        coverage_counts[coverage] = len(extractors)
        print(f"\n{coverage.upper()}: {len(extractors)} extractors")
        for ext in extractors:
            signals = getattr(EXTRACTOR_REGISTRY[ext], "signals", [])
            print(f"  - {ext}: {signals}")
    
    total_extractors = sum(coverage_counts.values())
    print(f"\n{'='*80}")
    print(f"TOTAL: {total_extractors} extractors across {len(coverage_counts)} coverage lines")
    print(f"{'='*80}")
    
    # Signal coverage matrix
    print("\n--- Signal Coverage Matrix ---")
    signal_map = list_extractors_by_signal()
    for signal, extractors in sorted(signal_map.items()):
        print(f"\n{signal} ({len(extractors)} extractors):")
        for ext in extractors:
            coverage = getattr(EXTRACTOR_REGISTRY[ext], "coverage", "unknown")
            print(f"  [{coverage}] {ext}")
    
    # Sample extractions
    print(f"\n{'='*80}")
    print("SAMPLE EXTRACTIONS")
    print(f"{'='*80}")
    
    demos = [
        ("equasis_operator", {"company_name": "Atlas Container Lines"}),
        ("iata_operator", {"operator_name": "Sky Airways International"}),
        ("security_scorecard", {"company_name": "TechCorp Solutions"}),
        ("sec_edgar", {"company_name": "MegaCorp Industries"}),
        ("ffiec_call_report", {"institution_name": "First National Bank"}),
        ("osha_safety", {"company_name": "Gulf Energy LLC"}),
        ("state_bar", {"firm_name": "Smith & Partners LLP", "entity_type": "firm"}),
    ]
    
    for ext_type, kwargs in demos:
        print(f"\n--- {ext_type} ---")
        ext = get_extractor(ext_type, seed="demo_seed_2024", **kwargs)
        result = ext.extract()
        print(f"Coverage: {ext.coverage}, Signals: {ext.signals}")
        print(f"Data keys: {list(result.raw_data.keys())}")
        print(f"Metadata: {result.metadata}")
