"""
aggregators.py - DSI Technical Pricing Data Aggregation Framework

This module transforms raw extractor output into structured input suitable for categorizers.
Each aggregator maps to one or more extractors and produces typed output dictionaries
that match categorizer input specifications.

Architecture:
- Aggregators receive ExtractionResult objects from extractors
- Transform raw_data into structured signal inputs
- Each signal produces a dict matching categorizer expectations:
  - ThresholdBucket: {"value": <numeric>}
  - ScoringLogic: {"state": "<STATE_NAME>"}
  - Enumeration: {"category": "<CATEGORY>"} or evaluation criteria
  - QualityTier: {"entity": "<entity_name>"}
  - Composite: {"<signal_name>": <score>, ...}
  - Boolean: {"flag": <bool>}

Coverage Lines:
- Marine: 8 signal groups
- Aerospace: 7 signal groups
- Cyber: 5 signal groups
- D&O: 6 signal groups
- Financial Institutions: 7 signal groups
- Energy: 7 signal groups
- Professional Indemnity: 7 signal groups
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# REGISTRY & BASE CLASSES
# =============================================================================

AGGREGATOR_REGISTRY: Dict[str, Type["DataAggregator"]] = {}


def register_aggregator(cls: Type["DataAggregator"]) -> Type["DataAggregator"]:
    """Decorator to register aggregator classes."""
    AGGREGATOR_REGISTRY[cls.__name__] = cls
    return cls


@dataclass
class SignalOutput:
    """Structured output for a single signal, ready for categorization."""
    signal_name: str
    categorizer_type: str
    configuration: str
    data: Dict[str, Any]
    confidence: float = 1.0
    source_extractors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class AggregationResult:
    """Complete aggregation output for a coverage/entity."""
    coverage: str
    entity_id: str
    timestamp: str
    signals: Dict[str, SignalOutput]
    composite_input: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class DataAggregator(ABC):
    """Abstract base class for all aggregators."""

    def __init__(self, coverage: str, **kwargs: Any):
        self.coverage = coverage
        self.kwargs = kwargs

    @abstractmethod
    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        """
        Transform raw extraction data into structured signal outputs.
        
        Args:
            extractions: Dict mapping extractor names to their raw_data outputs
            
        Returns:
            AggregationResult with all signals for this coverage
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def required_extractors(self) -> List[str]:
        """List of extractor names this aggregator requires."""
        raise NotImplementedError

    @property
    @abstractmethod
    def optional_extractors(self) -> List[str]:
        """List of extractor names this aggregator can use if available."""
        raise NotImplementedError

    def _safe_get(self, data: Dict, *keys: str, default: Any = None) -> Any:
        """Safely navigate nested dictionary structures."""
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, default)
            else:
                return default
        return current if current is not None else default

    def _safe_divide(self, numerator: float, denominator: float, default: float = 0.0) -> float:
        """Safe division with default for zero denominator."""
        return numerator / denominator if denominator != 0 else default

    def _clamp(self, value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
        """Clamp value to range."""
        return max(min_val, min(max_val, value))

    def _weighted_average(self, values_weights: List[tuple]) -> float:
        """Calculate weighted average from list of (value, weight) tuples."""
        total_weight = sum(w for _, w in values_weights if w > 0)
        if total_weight == 0:
            return 0.0
        return sum(v * w for v, w in values_weights if w > 0) / total_weight

    def _map_to_state(self, value: Any, mapping: Dict[Any, str], default: str = "UNKNOWN") -> str:
        """Map a value to a state string using provided mapping."""
        return mapping.get(value, default)

    def _count_to_state(self, count: int, thresholds: List[tuple]) -> str:
        """
        Map a count to a state based on thresholds.
        thresholds: List of (max_count, state) in ascending order
        """
        for max_count, state in thresholds:
            if count <= max_count:
                return state
        return thresholds[-1][1] if thresholds else "UNKNOWN"


# =============================================================================
# MARINE AGGREGATORS
# =============================================================================

@register_aggregator
class MarineSafetyComplianceAggregator(DataAggregator):
    """
    Aggregates safety compliance signals for marine coverage.
    
    Input Extractors:
    - PSCInspectionExtractor: detention history, deficiency rates
    - ClassificationSocietyExtractor: class status, conditions of class
    - ISMComplianceExtractor: DOC status, audit findings
    
    Output Signals:
    - psc_detention_status (ScoringLogic)
    - class_status (ScoringLogic)
    - ism_doc_status (Boolean + ScoringLogic)
    - safety_compliance (Composite)
    """
    
    required_extractors = ["psc_inspection", "classification_society", "ism_compliance"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        errors = []
        
        entity_id = self._safe_get(extractions, "psc_inspection", "vessel_imo", default="UNKNOWN")
        
        # --- PSC Detention Status ---
        psc_data = extractions.get("psc_inspection", {})
        detentions_3yr = self._safe_get(psc_data, "inspection_summary", "total_detentions_3yr", default=0)
        
        detention_state = self._count_to_state(detentions_3yr, [
            (0, "NONE_3YR"),
            (1, "DETAINED_1_3YR"),
            (2, "DETAINED_2_3YR"),
        ])
        if detentions_3yr >= 3:
            detention_state = "DETAINED_3_PLUS_3YR"
        
        # Check for bans (would come from flag state or sanctions data)
        if self._safe_get(psc_data, "banned", default=False):
            detention_state = "BANNED"
        
        psc_score = {"NONE_3YR": 100, "DETAINED_1_3YR": 75, "DETAINED_2_3YR": 55, 
                     "DETAINED_3_PLUS_3YR": 30, "BANNED": 5}.get(detention_state, 50)
        
        signals["psc_detention_status"] = SignalOutput(
            signal_name="psc_detention_status",
            categorizer_type="scoring_logic",
            configuration="psc_detention_status",
            data={"state": detention_state},
            source_extractors=["psc_inspection"],
            metadata={
                "detentions_3yr": detentions_3yr,
                "deficiency_ratio": self._safe_get(psc_data, "inspection_summary", "deficiency_ratio", default=0)
            }
        )
        composite_scores["psc_detention_status"] = psc_score
        
        # --- Classification Status ---
        class_data = extractions.get("classification_society", {})
        class_status_raw = self._safe_get(class_data, "classification", "class_status", default="Unknown")
        conditions = self._safe_get(class_data, "conditions_of_class", default={})
        outstanding = conditions.get("outstanding", 0)
        overdue = conditions.get("overdue", 0)
        
        # Map to scoring logic states
        if class_status_raw == "In Class":
            if overdue > 0:
                class_state = "IN_CLASS_MAJOR_CONDITIONS"
            elif outstanding > 2:
                class_state = "IN_CLASS_MAJOR_CONDITIONS"
            elif outstanding > 0:
                class_state = "IN_CLASS_MINOR_CONDITIONS"
            else:
                class_state = "IN_CLASS_NO_CONDITIONS"
        elif class_status_raw == "Suspended":
            class_state = "SUSPENDED"
        elif class_status_raw == "Withdrawn":
            class_state = "WITHDRAWN"
        else:
            class_state = "NO_CLASS"
        
        class_score = {"IN_CLASS_NO_CONDITIONS": 100, "IN_CLASS_MINOR_CONDITIONS": 85,
                       "IN_CLASS_MAJOR_CONDITIONS": 60, "SUSPENDED": 25, 
                       "WITHDRAWN": 10, "NO_CLASS": 5}.get(class_state, 50)
        
        signals["class_status"] = SignalOutput(
            signal_name="class_status",
            categorizer_type="scoring_logic",
            configuration="class_status",
            data={"state": class_state},
            source_extractors=["classification_society"],
            metadata={
                "society": self._safe_get(class_data, "classification", "society_name"),
                "outstanding_conditions": outstanding,
                "overdue_conditions": overdue
            }
        )
        composite_scores["class_status"] = class_score
        
        # --- ISM Compliance ---
        ism_data = extractions.get("ism_compliance", {})
        doc_status_raw = self._safe_get(ism_data, "doc_status", "status", default="Unknown")
        major_nc = self._safe_get(ism_data, "audit_history", "major_nonconformities", default=0)
        
        doc_valid = doc_status_raw == "Valid"
        
        # Map to scoring state
        if doc_status_raw == "Valid" and major_nc == 0:
            ism_state = "VALID_NO_NC"
            ism_score = 100
        elif doc_status_raw == "Valid" and major_nc > 0:
            ism_state = "VALID_WITH_NC"
            ism_score = 75
        elif doc_status_raw == "Expired":
            ism_state = "EXPIRED"
            ism_score = 40
        elif doc_status_raw == "Suspended":
            ism_state = "SUSPENDED"
            ism_score = 20
        elif doc_status_raw == "Withdrawn":
            ism_state = "WITHDRAWN"
            ism_score = 5
        else:
            ism_state = "UNKNOWN"
            ism_score = 30
        
        signals["ism_doc_status"] = SignalOutput(
            signal_name="ism_doc_status",
            categorizer_type="scoring_logic",
            configuration="ism_doc_status",
            data={"state": ism_state, "flag": doc_valid},
            source_extractors=["ism_compliance"],
            metadata={
                "major_nonconformities": major_nc,
                "total_findings": self._safe_get(ism_data, "audit_history", "total_findings", default=0)
            }
        )
        composite_scores["ism_doc_status"] = ism_score
        
        # --- Safety Compliance Composite ---
        safety_composite = self._weighted_average([
            (psc_score, 0.35),
            (class_score, 0.35),
            (ism_score, 0.30)
        ])
        
        signals["safety_compliance"] = SignalOutput(
            signal_name="safety_compliance",
            categorizer_type="composite_score",
            configuration="safety_compliance",
            data={
                "psc_detention_status": psc_score,
                "class_status": class_score,
                "ism_doc_status": ism_score
            },
            confidence=1.0,
            source_extractors=["psc_inspection", "classification_society", "ism_compliance"],
            metadata={"composite_score": safety_composite}
        )
        composite_scores["safety_compliance"] = safety_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores,
            errors=errors
        )


@register_aggregator
class MarineOperationalTelemetryAggregator(DataAggregator):
    """
    Aggregates operational telemetry signals for marine coverage.
    
    Input Extractors:
    - AISTrackingExtractor: AIS gaps, port calls, voyage patterns
    
    Output Signals:
    - dark_activity_status (ScoringLogic)
    - operational_telemetry (Composite)
    """
    
    required_extractors = ["ais_tracking"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        ais_data = extractions.get("ais_tracking", {})
        entity_id = self._safe_get(ais_data, "vessel_imo", default="UNKNOWN")
        
        # --- Dark Activity Status ---
        gaps = self._safe_get(ais_data, "ais_gaps", default={})
        total_gaps = gaps.get("total_gaps_12mo", 0)
        high_risk_gaps = gaps.get("high_risk_gaps", 0)
        
        gap_details = gaps.get("gaps", [])
        has_open_water_gap = any(g.get("location_type") == "Open Ocean" for g in gap_details)
        
        # Map to dark activity states
        if total_gaps == 0:
            dark_state = "NONE"
            dark_score = 100
        elif high_risk_gaps == 0 and not has_open_water_gap:
            if total_gaps <= 2:
                dark_state = "BRIEF_COASTAL"
                dark_score = 90
            else:
                dark_state = "EXTENDED_COASTAL"
                dark_score = 75
        elif has_open_water_gap and high_risk_gaps == 0:
            dark_state = "OPEN_WATER_MINOR"
            dark_score = 55
        elif high_risk_gaps > 0:
            dark_state = "OPEN_WATER_MAJOR"
            dark_score = 25
        else:
            dark_state = "EXTENDED_COASTAL"
            dark_score = 75
        
        # Check for STS events
        sts_events = self._safe_get(ais_data, "sts_events", "total_12mo", default=0)
        if sts_events > 0:
            dark_state = "STS_SUSPECTED"
            dark_score = 15
        
        signals["dark_activity_status"] = SignalOutput(
            signal_name="dark_activity_status",
            categorizer_type="scoring_logic",
            configuration="dark_activity_status",
            data={"state": dark_state},
            source_extractors=["ais_tracking"],
            metadata={
                "total_gaps": total_gaps,
                "high_risk_gaps": high_risk_gaps,
                "sts_events": sts_events
            }
        )
        composite_scores["dark_activity_status"] = dark_score
        
        # --- Port Call Metrics ---
        port_calls = self._safe_get(ais_data, "port_calls", default={})
        port_call_count = port_calls.get("total_12mo", 0)
        unique_countries = port_calls.get("unique_countries", 0)
        
        # Operational activity score based on utilization
        if port_call_count >= 20:
            activity_score = 90
        elif port_call_count >= 10:
            activity_score = 80
        elif port_call_count >= 5:
            activity_score = 70
        else:
            activity_score = 60
        
        composite_scores["port_activity"] = activity_score
        
        # --- Operational Telemetry Composite ---
        telemetry_composite = self._weighted_average([
            (dark_score, 0.60),
            (activity_score, 0.40)
        ])
        
        signals["operational_telemetry"] = SignalOutput(
            signal_name="operational_telemetry",
            categorizer_type="composite_score",
            configuration="operational_telemetry",
            data={
                "dark_activity_status": dark_score,
                "port_activity": activity_score
            },
            source_extractors=["ais_tracking"],
            metadata={
                "composite_score": telemetry_composite,
                "port_calls_12mo": port_call_count,
                "unique_countries": unique_countries
            }
        )
        composite_scores["operational_telemetry"] = telemetry_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class MarineSanctionsComplianceAggregator(DataAggregator):
    """
    Aggregates sanctions compliance signals for marine coverage.
    
    Input Extractors:
    - SanctionsScreeningExtractor: OFAC/EU/UN screening results
    - AISTrackingExtractor: High-risk area transits, STS events
    
    Output Signals:
    - sanctions_screening_result (Boolean + ScoringLogic)
    - sanctions_compliance (Composite)
    """
    
    required_extractors = ["sanctions_screening"]
    optional_extractors = ["ais_tracking"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        sanctions_data = extractions.get("sanctions_screening", {})
        entity_id = self._safe_get(sanctions_data, "entity_id", default="UNKNOWN")
        
        # --- Sanctions Screening ---
        screening = self._safe_get(sanctions_data, "screening_result", default={})
        status = screening.get("status", "UNKNOWN")
        total_hits = screening.get("total_hits", 0)
        
        # Check for active hits vs cleared
        hits = screening.get("hits", [])
        active_hits = sum(1 for h in hits if h.get("status") == "Active")
        
        if status == "CLEAR" and total_hits == 0:
            sanctions_state = "CLEAR"
            sanctions_score = 100
        elif active_hits == 0 and total_hits > 0:
            sanctions_state = "CLEARED_HISTORICAL"
            sanctions_score = 85
        elif active_hits == 1:
            sanctions_state = "HIT_SINGLE"
            sanctions_score = 25
        elif active_hits > 1:
            sanctions_state = "HIT_MULTIPLE"
            sanctions_score = 5
        else:
            sanctions_state = "PENDING_REVIEW"
            sanctions_score = 50
        
        # Check ownership flags
        ownership = self._safe_get(sanctions_data, "ownership_flags", default={})
        high_risk_jurisdiction = ownership.get("high_risk_jurisdiction", False)
        complex_structure = ownership.get("complex_structure", False)
        
        if high_risk_jurisdiction:
            sanctions_score = max(10, sanctions_score - 25)
        if complex_structure:
            sanctions_score = max(10, sanctions_score - 10)
        
        signals["sanctions_screening_result"] = SignalOutput(
            signal_name="sanctions_screening_result",
            categorizer_type="scoring_logic",
            configuration="sanctions_screening",
            data={"state": sanctions_state, "flag": status == "CLEAR"},
            source_extractors=["sanctions_screening"],
            metadata={
                "total_hits": total_hits,
                "active_hits": active_hits,
                "high_risk_jurisdiction": high_risk_jurisdiction
            }
        )
        composite_scores["sanctions_screening"] = sanctions_score
        
        # --- High Risk Area Exposure (from AIS if available) ---
        ais_data = extractions.get("ais_tracking", {})
        high_risk_transits = self._safe_get(ais_data, "sanctions_exposure", "high_risk_area_transits", default=0)
        sanctioned_visit = self._safe_get(ais_data, "sanctions_exposure", "sanctioned_area_visit", default=False)
        
        if sanctioned_visit:
            exposure_score = 10
        elif high_risk_transits > 5:
            exposure_score = 40
        elif high_risk_transits > 2:
            exposure_score = 60
        elif high_risk_transits > 0:
            exposure_score = 80
        else:
            exposure_score = 100
        
        composite_scores["high_risk_exposure"] = exposure_score
        
        # --- Sanctions Compliance Composite ---
        sanctions_composite = self._weighted_average([
            (sanctions_score, 0.70),
            (exposure_score, 0.30)
        ])
        
        signals["sanctions_compliance"] = SignalOutput(
            signal_name="sanctions_compliance",
            categorizer_type="composite_score",
            configuration="sanctions_compliance",
            data={
                "sanctions_screening": sanctions_score,
                "high_risk_exposure": exposure_score
            },
            source_extractors=["sanctions_screening", "ais_tracking"],
            metadata={"composite_score": sanctions_composite}
        )
        composite_scores["sanctions_compliance"] = sanctions_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class MarineFleetQualityAggregator(DataAggregator):
    """
    Aggregates fleet quality signals for marine coverage.
    
    Input Extractors:
    - EquasisOperatorExtractor: Fleet composition, vessel ages
    - VesselValuationExtractor: Fleet values, LTV
    - FlagStatePerformanceExtractor: Flag state quality
    
    Output Signals:
    - fleet_size (ThresholdBucket)
    - fleet_age (ThresholdBucket)
    - flag_state_quality (Enumeration)
    - fleet_quality (Composite)
    """
    
    required_extractors = ["equasis_operator"]
    optional_extractors = ["vessel_valuation", "flag_state_performance"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        equasis_data = extractions.get("equasis_operator", {})
        entity_id = self._safe_get(equasis_data, "company", "imo_company_number", default="UNKNOWN")
        
        # --- Fleet Size ---
        fleet = self._safe_get(equasis_data, "fleet", default={})
        fleet_size = fleet.get("total_vessels", 0)
        
        signals["fleet_size"] = SignalOutput(
            signal_name="fleet_size",
            categorizer_type="threshold_bucket",
            configuration="fleet_size",
            data={"value": fleet_size},
            source_extractors=["equasis_operator"],
            metadata={"coverage": "marine"}
        )
        
        # Score based on threshold profile
        if fleet_size <= 5:
            size_score = 60
        elif fleet_size <= 20:
            size_score = 70
        elif fleet_size <= 50:
            size_score = 80
        elif fleet_size <= 100:
            size_score = 85
        elif fleet_size <= 250:
            size_score = 90
        else:
            size_score = 95
        composite_scores["fleet_size"] = size_score
        
        # --- Fleet Age ---
        avg_age = fleet.get("average_age", 15)
        
        signals["fleet_age"] = SignalOutput(
            signal_name="fleet_age",
            categorizer_type="threshold_bucket",
            configuration="fleet_age",
            data={"value": avg_age},
            source_extractors=["equasis_operator"],
            metadata={"coverage": "marine"}
        )
        
        # Score based on age thresholds
        if avg_age <= 5:
            age_score = 95
        elif avg_age <= 10:
            age_score = 88
        elif avg_age <= 15:
            age_score = 78
        elif avg_age <= 20:
            age_score = 65
        elif avg_age <= 25:
            age_score = 50
        else:
            age_score = 35
        composite_scores["fleet_age"] = age_score
        
        # --- Flag State Quality ---
        flag_data = extractions.get("flag_state_performance", {})
        flag_list = self._safe_get(flag_data, "paris_mou_status", "list_color", default="GREY")
        
        flag_state_map = {"WHITE": 95, "GREY": 75, "BLACK": 40}
        flag_score = flag_state_map.get(flag_list, 70)
        
        signals["flag_state_quality"] = SignalOutput(
            signal_name="flag_state_quality",
            categorizer_type="enumeration",
            configuration="flag_state_quality",
            data={"category": flag_list},
            source_extractors=["flag_state_performance"],
            metadata={
                "flag_state": self._safe_get(flag_data, "flag_state"),
                "detention_rate": self._safe_get(flag_data, "paris_mou_status", "detention_rate_pct")
            }
        )
        composite_scores["flag_state_quality"] = flag_score
        
        # --- Vessel Categories (majority analysis) ---
        vessels = fleet.get("vessels", [])
        if vessels:
            category_counts = {}
            for v in vessels:
                cat = v.get("vessel_type", "Other")
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            majority_cat = max(category_counts, key=category_counts.get) if category_counts else "Mixed"
            majority_pct = category_counts.get(majority_cat, 0) / len(vessels) * 100
        else:
            majority_cat = "Unknown"
            majority_pct = 0
        
        signals["vessel_category"] = SignalOutput(
            signal_name="vessel_category",
            categorizer_type="enumeration",
            configuration="vessel_category",
            data={
                "category": majority_cat.lower().replace(" ", "_"),
                "vessel_majority": majority_cat.lower().replace(" ", "_"),
                "fleet_size": fleet_size
            },
            source_extractors=["equasis_operator"],
            metadata={"majority_percentage": majority_pct}
        )
        
        # --- Fleet Quality Composite ---
        fleet_composite = self._weighted_average([
            (size_score, 0.25),
            (age_score, 0.40),
            (flag_score, 0.35)
        ])
        
        signals["fleet_quality"] = SignalOutput(
            signal_name="fleet_quality",
            categorizer_type="composite_score",
            configuration="fleet_quality",
            data={
                "fleet_size": size_score,
                "fleet_age": age_score,
                "flag_state_quality": flag_score
            },
            source_extractors=["equasis_operator", "flag_state_performance"],
            metadata={"composite_score": fleet_composite}
        )
        composite_scores["fleet_quality"] = fleet_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class MarineFinancialStabilityAggregator(DataAggregator):
    """
    Aggregates financial stability signals for marine coverage.
    
    Input Extractors:
    - MarineFinancialExtractor: Revenue, EBITDA, leverage ratios
    - VesselValuationExtractor: Asset values, LTV
    - CreditRatingExtractor: Credit ratings (common)
    
    Output Signals:
    - credit_rating (QualityTier)
    - leverage_ratio (ThresholdBucket)
    - financial_stability (Composite)
    """
    
    required_extractors = ["marine_financial"]
    optional_extractors = ["vessel_valuation", "credit_rating"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        fin_data = extractions.get("marine_financial", {})
        entity_id = self._safe_get(fin_data, "company_id", default="UNKNOWN")
        
        # --- Credit Rating ---
        credit_data = extractions.get("credit_rating", {})
        ratings = self._safe_get(credit_data, "ratings", default=[])
        
        if ratings:
            # Take highest (best) rating
            rating_order = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", 
                          "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
                          "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D"]
            best_rating = None
            for r in ratings:
                rating_str = r.get("rating", "").upper()
                if rating_str in rating_order:
                    if best_rating is None or rating_order.index(rating_str) < rating_order.index(best_rating):
                        best_rating = rating_str
            
            if best_rating:
                rating_idx = rating_order.index(best_rating)
                if rating_idx <= 3:
                    rating_score = 95
                elif rating_idx <= 6:
                    rating_score = 88
                elif rating_idx <= 9:
                    rating_score = 78
                elif rating_idx <= 12:
                    rating_score = 65
                else:
                    rating_score = 35
            else:
                best_rating = "NR"
                rating_score = 60
        else:
            best_rating = "NR"
            rating_score = 60
        
        signals["credit_rating"] = SignalOutput(
            signal_name="credit_rating",
            categorizer_type="quality_tier",
            configuration="credit_rating",
            data={"entity": best_rating.lower()},
            source_extractors=["credit_rating"],
            metadata={"all_ratings": ratings}
        )
        composite_scores["credit_rating"] = rating_score
        
        # --- Leverage Metrics ---
        ratios = self._safe_get(fin_data, "ratios", default={})
        debt_to_ebitda = ratios.get("debt_to_ebitda", 5.0)
        interest_coverage = ratios.get("interest_coverage", 2.0)
        
        # Debt/EBITDA scoring
        if debt_to_ebitda <= 2.0:
            leverage_score = 95
        elif debt_to_ebitda <= 3.5:
            leverage_score = 85
        elif debt_to_ebitda <= 5.0:
            leverage_score = 70
        elif debt_to_ebitda <= 7.0:
            leverage_score = 50
        else:
            leverage_score = 30
        
        signals["leverage_ratio"] = SignalOutput(
            signal_name="leverage_ratio",
            categorizer_type="threshold_bucket",
            configuration="debt_to_ebitda",
            data={"value": debt_to_ebitda},
            source_extractors=["marine_financial"],
            metadata={"interest_coverage": interest_coverage}
        )
        composite_scores["leverage_ratio"] = leverage_score
        
        # --- LTV from Vessel Valuation ---
        valuation_data = extractions.get("vessel_valuation", {})
        ltv = self._safe_get(valuation_data, "leverage", "ltv_ratio", default=0.6)
        
        if ltv <= 0.50:
            ltv_score = 95
        elif ltv <= 0.65:
            ltv_score = 85
        elif ltv <= 0.75:
            ltv_score = 70
        elif ltv <= 0.85:
            ltv_score = 50
        else:
            ltv_score = 30
        
        composite_scores["ltv_ratio"] = ltv_score
        
        # --- Financial Stability Composite ---
        financial_composite = self._weighted_average([
            (rating_score, 0.35),
            (leverage_score, 0.35),
            (ltv_score, 0.30)
        ])
        
        signals["financial_stability"] = SignalOutput(
            signal_name="financial_stability",
            categorizer_type="composite_score",
            configuration="financial_stability",
            data={
                "credit_rating": rating_score,
                "leverage_ratio": leverage_score,
                "ltv_ratio": ltv_score
            },
            source_extractors=["marine_financial", "vessel_valuation", "credit_rating"],
            metadata={"composite_score": financial_composite}
        )
        composite_scores["financial_stability"] = financial_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class MarineClassificationQualityAggregator(DataAggregator):
    """
    Aggregates classification quality signals for marine coverage.
    
    Input Extractors:
    - ClassificationSocietyExtractor: Class society tier, survey compliance
    
    Output Signals:
    - classification_society (QualityTier)
    - survey_compliance (ThresholdBucket)
    - classification_quality (Composite)
    """
    
    required_extractors = ["classification_society"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        class_data = extractions.get("classification_society", {})
        entity_id = self._safe_get(class_data, "vessel_imo", default="UNKNOWN")
        
        # --- Classification Society Tier ---
        society_name = self._safe_get(class_data, "classification", "society_name", default="Unknown")
        
        # Map to quality tiers
        top_iacs = ["dnv", "lloyd's register", "bureau veritas", "abs", "american bureau of shipping"]
        iacs_member = ["class nk", "rina", "ccs", "korean register", "indian register"]
        
        society_lower = society_name.lower()
        if any(s in society_lower for s in top_iacs):
            society_tier = "TOP_IACS"
            society_score = 95
        elif any(s in society_lower for s in iacs_member):
            society_tier = "IACS_MEMBER"
            society_score = 88
        elif society_name != "Unknown":
            society_tier = "RECOGNIZED"
            society_score = 75
        else:
            society_tier = "OTHER"
            society_score = 60
        
        signals["classification_society"] = SignalOutput(
            signal_name="classification_society",
            categorizer_type="quality_tier",
            configuration="classification_society",
            data={"entity": society_lower},
            source_extractors=["classification_society"],
            metadata={"tier": society_tier}
        )
        composite_scores["classification_society"] = society_score
        
        # --- Survey Compliance ---
        survey_history = self._safe_get(class_data, "survey_history", default={})
        compliance_rate = survey_history.get("compliance_rate", 0.90)
        
        compliance_pct = compliance_rate * 100
        if compliance_pct >= 98:
            survey_score = 100
        elif compliance_pct >= 95:
            survey_score = 90
        elif compliance_pct >= 90:
            survey_score = 80
        elif compliance_pct >= 85:
            survey_score = 65
        else:
            survey_score = 45
        
        signals["survey_compliance"] = SignalOutput(
            signal_name="survey_compliance",
            categorizer_type="threshold_bucket",
            configuration="survey_compliance",
            data={"value": compliance_pct},
            source_extractors=["classification_society"],
            metadata={"surveys": survey_history.get("surveys", [])}
        )
        composite_scores["survey_compliance"] = survey_score
        
        # --- Classification Quality Composite ---
        class_composite = self._weighted_average([
            (society_score, 0.50),
            (survey_score, 0.50)
        ])
        
        signals["classification_quality"] = SignalOutput(
            signal_name="classification_quality",
            categorizer_type="composite_score",
            configuration="classification_quality",
            data={
                "classification_society": society_score,
                "survey_compliance": survey_score
            },
            source_extractors=["classification_society"],
            metadata={"composite_score": class_composite}
        )
        composite_scores["classification_quality"] = class_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class MarinePIQualityAggregator(DataAggregator):
    """
    Aggregates P&I quality signals for marine coverage.
    
    Input Extractors:
    - PIClubExtractor: Club membership, claims history
    
    Output Signals:
    - pi_club_tier (QualityTier)
    - claims_history (ScoringLogic)
    - p_and_i_quality (Composite)
    """
    
    required_extractors = ["pi_club"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        pi_data = extractions.get("pi_club", {})
        entity_id = self._safe_get(pi_data, "company_id", default="UNKNOWN")
        
        # --- P&I Club Tier ---
        membership = self._safe_get(pi_data, "membership", default={})
        club_name = membership.get("club_name", "Unknown")
        club_type = membership.get("club_type", "Unknown")
        
        ig_top = ["gard", "britannia", "uk club", "north", "standard", "west of england", "skuld"]
        ig_member = ["american club", "japan club", "london club", "swedish club"]
        
        club_lower = club_name.lower()
        if any(c in club_lower for c in ig_top):
            club_tier = "IG_TOP"
            club_score = 95
        elif any(c in club_lower for c in ig_member) or "other ig" in club_lower:
            club_tier = "IG_MEMBER"
            club_score = 88
        elif club_type == "Fixed Premium":
            club_tier = "QUALITY_FIXED"
            club_score = 78
        else:
            club_tier = "STANDARD"
            club_score = 68
        
        signals["pi_club_tier"] = SignalOutput(
            signal_name="pi_club_tier",
            categorizer_type="quality_tier",
            configuration="p_and_i_club",
            data={"entity": club_lower},
            source_extractors=["pi_club"],
            metadata={"tier": club_tier, "club_type": club_type}
        )
        composite_scores["pi_club_tier"] = club_score
        
        # --- Claims History ---
        claims = self._safe_get(pi_data, "claims_history", default={})
        total_claims = claims.get("total_claims_5yr", 0)
        total_incurred = claims.get("total_incurred_usd", 0)
        
        # Map claims to state
        if total_claims == 0:
            claims_state = "NONE"
            claims_score = 100
        elif total_claims <= 2 and total_incurred < 500000:
            claims_state = "LOW"
            claims_score = 85
        elif total_claims <= 5 and total_incurred < 2000000:
            claims_state = "MODERATE"
            claims_score = 70
        elif total_claims <= 10:
            claims_state = "ELEVATED"
            claims_score = 50
        else:
            claims_state = "HIGH"
            claims_score = 30
        
        signals["pi_claims_history"] = SignalOutput(
            signal_name="pi_claims_history",
            categorizer_type="scoring_logic",
            configuration="pi_claims_history",
            data={"state": claims_state},
            source_extractors=["pi_club"],
            metadata={
                "total_claims": total_claims,
                "total_incurred_usd": total_incurred
            }
        )
        composite_scores["pi_claims_history"] = claims_score
        
        # --- P&I Quality Composite ---
        pi_composite = self._weighted_average([
            (club_score, 0.60),
            (claims_score, 0.40)
        ])
        
        signals["p_and_i_quality"] = SignalOutput(
            signal_name="p_and_i_quality",
            categorizer_type="composite_score",
            configuration="p_and_i_quality",
            data={
                "pi_club_tier": club_score,
                "pi_claims_history": claims_score
            },
            source_extractors=["pi_club"],
            metadata={"composite_score": pi_composite}
        )
        composite_scores["p_and_i_quality"] = pi_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class MarineManagementQualityAggregator(DataAggregator):
    """
    Aggregates management quality signals for marine coverage.
    
    Input Extractors:
    - EquasisOperatorExtractor: Company profile, DOC holder
    - ISMComplianceExtractor: Management system, audit history
    
    Output Signals:
    - operator_type (Enumeration)
    - management_quality (Composite)
    """
    
    required_extractors = ["equasis_operator", "ism_compliance"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        equasis_data = extractions.get("equasis_operator", {})
        ism_data = extractions.get("ism_compliance", {})
        entity_id = self._safe_get(equasis_data, "company", "imo_company_number", default="UNKNOWN")
        
        # --- Operator Type Classification ---
        company = self._safe_get(equasis_data, "company", default={})
        fleet = self._safe_get(equasis_data, "fleet", default={})
        
        fleet_size = fleet.get("total_vessels", 0)
        vessels = fleet.get("vessels", [])
        company_role = company.get("role", "Unknown")
        
        # Determine majority vessel type
        if vessels:
            category_counts = {}
            for v in vessels:
                cat = v.get("vessel_type", "Other").lower()
                if "container" in cat:
                    cat = "container"
                elif "tanker" in cat:
                    cat = "tanker"
                elif "bulk" in cat:
                    cat = "bulk"
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            majority = max(category_counts, key=category_counts.get) if category_counts else "mixed"
        else:
            majority = "unknown"
        
        # Determine operator type (simplified - would come from more sources in production)
        offers_liner = self._safe_get(equasis_data, "company", "offers_liner_service", default=False)
        
        if majority == "container" and fleet_size >= 50 and offers_liner:
            operator_type = "MAJOR_LINER"
            operator_score = 90
        elif majority == "container" and fleet_size >= 10:
            operator_type = "REGIONAL_LINER"
            operator_score = 82
        elif majority == "tanker" and fleet_size >= 30:
            operator_type = "MAJOR_TANKER"
            operator_score = 88
        elif majority == "tanker":
            operator_type = "INDEPENDENT_TANKER"
            operator_score = 75
        elif majority == "bulk" and fleet_size >= 40:
            operator_type = "MAJOR_BULK"
            operator_score = 85
        elif fleet_size < 10:
            operator_type = "TRAMP_OPERATOR"
            operator_score = 65
        else:
            operator_type = "UNCATEGORIZED"
            operator_score = 70
        
        signals["operator_type"] = SignalOutput(
            signal_name="operator_type",
            categorizer_type="enumeration",
            configuration="operator_type",
            data={
                "category": operator_type,
                "vessel_majority": majority,
                "fleet_size": fleet_size,
                "offers_liner_service": offers_liner
            },
            source_extractors=["equasis_operator"],
            metadata={"company_role": company_role}
        )
        composite_scores["operator_type"] = operator_score
        
        # --- SMS Quality (from ISM) ---
        sms = self._safe_get(ism_data, "sms_status", default={})
        drills = sms.get("drills_conducted_12mo", 0)
        documented = sms.get("documented", False)
        
        if documented and drills >= 12:
            sms_score = 95
        elif documented and drills >= 6:
            sms_score = 85
        elif documented:
            sms_score = 70
        else:
            sms_score = 50
        
        composite_scores["sms_quality"] = sms_score
        
        # --- Management Quality Composite ---
        mgmt_composite = self._weighted_average([
            (operator_score, 0.50),
            (sms_score, 0.50)
        ])
        
        signals["management_quality"] = SignalOutput(
            signal_name="management_quality",
            categorizer_type="composite_score",
            configuration="management_quality",
            data={
                "operator_type": operator_score,
                "sms_quality": sms_score
            },
            source_extractors=["equasis_operator", "ism_compliance"],
            metadata={"composite_score": mgmt_composite}
        )
        composite_scores["management_quality"] = mgmt_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


# =============================================================================
# AEROSPACE AGGREGATORS
# =============================================================================

@register_aggregator
class AerospaceSafetyRecordAggregator(DataAggregator):
    """
    Aggregates safety record signals for aerospace coverage.
    
    Input Extractors:
    - IATAOperatorExtractor: IOSA status, basic safety info
    - AviationSafetyExtractor: Accidents, incidents, fatalities
    
    Output Signals:
    - accident_history_5yr (ScoringLogic)
    - iosa_status (ScoringLogic)
    - safety_record (Composite)
    """
    
    required_extractors = ["aviation_safety"]
    optional_extractors = ["iata_operator"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        safety_data = extractions.get("aviation_safety", {})
        iata_data = extractions.get("iata_operator", {})
        entity_id = self._safe_get(safety_data, "operator_id", default="UNKNOWN")
        
        # --- Accident History ---
        record = self._safe_get(safety_data, "safety_record_5yr", default={})
        accidents = record.get("accidents", 0)
        fatalities = record.get("fatalities", 0)
        hull_losses = record.get("hull_losses", 0)
        
        # Map to scoring states
        if accidents == 0:
            accident_state = "NONE"
            accident_score = 100
        elif accidents == 1 and fatalities == 0:
            accident_state = "MINOR_1"
            accident_score = 85
        elif accidents >= 2 and fatalities == 0:
            accident_state = "MINOR_2_PLUS"
            accident_score = 70
        elif accidents == 1 and fatalities > 0:
            accident_state = "MAJOR_1"
            accident_score = 50
        elif accidents >= 2 and fatalities > 0 and fatalities < 50:
            accident_state = "MAJOR_2_PLUS"
            accident_score = 25
        else:
            accident_state = "FATAL"
            accident_score = 10
        
        signals["accident_history_5yr"] = SignalOutput(
            signal_name="accident_history_5yr",
            categorizer_type="scoring_logic",
            configuration="accident_history_5yr",
            data={"state": accident_state},
            source_extractors=["aviation_safety"],
            metadata={
                "accidents": accidents,
                "fatalities": fatalities,
                "hull_losses": hull_losses
            }
        )
        composite_scores["accident_history"] = accident_score
        
        # --- IOSA Status ---
        iosa = self._safe_get(iata_data, "iosa", default={})
        iosa_registered = iosa.get("registered", False)
        iosa_status_raw = iosa.get("status", "Not Registered")
        
        if iosa_status_raw == "Registered":
            iosa_state = "REGISTERED_CURRENT"
            iosa_score = 100
        elif iosa_status_raw == "Renewal Pending":
            iosa_state = "REGISTERED_RENEWAL_PENDING"
            iosa_score = 90
        elif iosa_status_raw == "Expired":
            iosa_state = "EXPIRED_LESS_6MO"
            iosa_score = 70
        elif not iosa_registered:
            # Check if IOSA is applicable (scheduled airlines should have it)
            operator_type = self._safe_get(iata_data, "regulatory", "aoc_status", default="Unknown")
            if operator_type == "Valid":
                iosa_state = "NEVER_REGISTERED_APPLICABLE"
                iosa_score = 30
            else:
                iosa_state = "NOT_APPLICABLE"
                iosa_score = 75
        else:
            iosa_state = "UNKNOWN"
            iosa_score = 50
        
        signals["iosa_status"] = SignalOutput(
            signal_name="iosa_status",
            categorizer_type="scoring_logic",
            configuration="iosa_status",
            data={"state": iosa_state, "flag": iosa_registered},
            source_extractors=["iata_operator"],
            metadata={"findings_count": iosa.get("findings_count")}
        )
        composite_scores["iosa_status"] = iosa_score
        
        # --- Safety Record Composite ---
        safety_composite = self._weighted_average([
            (accident_score, 0.60),
            (iosa_score, 0.40)
        ])
        
        signals["safety_record"] = SignalOutput(
            signal_name="safety_record",
            categorizer_type="composite_score",
            configuration="safety_record",
            data={
                "accident_history": accident_score,
                "iosa_status": iosa_score
            },
            source_extractors=["aviation_safety", "iata_operator"],
            metadata={"composite_score": safety_composite}
        )
        composite_scores["safety_record"] = safety_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class AerospaceRegulatoryComplianceAggregator(DataAggregator):
    """
    Aggregates regulatory compliance signals for aerospace coverage.
    
    Input Extractors:
    - IATAOperatorExtractor: AOC status, primary regulator
    - FAARegistryExtractor: Enforcement actions, AD compliance
    
    Output Signals:
    - aoc_status (Boolean)
    - enforcement_actions_3yr (ScoringLogic)
    - ad_compliance (ThresholdBucket)
    - regulatory_compliance (Composite)
    """
    
    required_extractors = ["faa_registry"]
    optional_extractors = ["iata_operator"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        faa_data = extractions.get("faa_registry", {})
        iata_data = extractions.get("iata_operator", {})
        entity_id = self._safe_get(faa_data, "operator_id", default="UNKNOWN")
        
        # --- AOC Status ---
        aoc_status = self._safe_get(iata_data, "regulatory", "aoc_status", default="Unknown")
        aoc_valid = aoc_status == "Valid"
        
        if aoc_valid:
            aoc_score = 100
        elif aoc_status == "Pending":
            aoc_score = 70
        elif aoc_status == "Suspended":
            aoc_score = 25
        elif aoc_status == "Revoked":
            aoc_score = 5
        else:
            aoc_score = 50
        
        signals["aoc_status"] = SignalOutput(
            signal_name="aoc_status",
            categorizer_type="boolean_flag",
            configuration="aoc_valid",
            data={"flag": aoc_valid, "state": aoc_status.upper()},
            source_extractors=["iata_operator"],
            metadata={"regulator": self._safe_get(iata_data, "regulatory", "primary_regulator")}
        )
        composite_scores["aoc_status"] = aoc_score
        
        # --- Enforcement Actions ---
        enforcement = self._safe_get(faa_data, "enforcement", default={})
        total_actions = enforcement.get("total_actions_5yr", 0)
        certificate_actions = enforcement.get("certificate_actions", 0)
        
        if total_actions == 0:
            enforcement_state = "NONE"
            enforcement_score = 100
        elif total_actions == 1 and certificate_actions == 0:
            enforcement_state = "MINOR_1"
            enforcement_score = 85
        elif total_actions >= 2 and certificate_actions == 0:
            enforcement_state = "MINOR_2_PLUS"
            enforcement_score = 70
        elif certificate_actions == 1:
            enforcement_state = "MAJOR_1"
            enforcement_score = 45
        elif certificate_actions >= 2:
            enforcement_state = "MAJOR_2_PLUS"
            enforcement_score = 20
        else:
            enforcement_state = "MINOR_1"
            enforcement_score = 85
        
        signals["enforcement_actions_3yr"] = SignalOutput(
            signal_name="enforcement_actions_3yr",
            categorizer_type="scoring_logic",
            configuration="enforcement_actions_3yr",
            data={"state": enforcement_state},
            source_extractors=["faa_registry"],
            metadata={
                "total_actions": total_actions,
                "certificate_actions": certificate_actions,
                "penalties_usd": enforcement.get("total_penalties_usd", 0)
            }
        )
        composite_scores["enforcement_actions"] = enforcement_score
        
        # --- AD Compliance ---
        ad_data = self._safe_get(faa_data, "airworthiness_directives", default={})
        total_ad = ad_data.get("total_applicable", 100)
        complied = ad_data.get("complied", 100)
        overdue = ad_data.get("overdue", 0)
        
        compliance_rate = self._safe_divide(complied, total_ad, 1.0) * 100
        
        if compliance_rate >= 99 and overdue == 0:
            ad_score = 100
        elif compliance_rate >= 97:
            ad_score = 90
        elif compliance_rate >= 95:
            ad_score = 75
        elif compliance_rate >= 90:
            ad_score = 55
        else:
            ad_score = 30
        
        signals["ad_compliance"] = SignalOutput(
            signal_name="ad_compliance",
            categorizer_type="threshold_bucket",
            configuration="ad_compliance",
            data={"value": compliance_rate},
            source_extractors=["faa_registry"],
            metadata={"overdue_ads": overdue}
        )
        composite_scores["ad_compliance"] = ad_score
        
        # --- Regulatory Compliance Composite ---
        regulatory_composite = self._weighted_average([
            (aoc_score, 0.35),
            (enforcement_score, 0.35),
            (ad_score, 0.30)
        ])
        
        signals["regulatory_compliance"] = SignalOutput(
            signal_name="regulatory_compliance",
            categorizer_type="composite_score",
            configuration="regulatory_compliance",
            data={
                "aoc_status": aoc_score,
                "enforcement_actions": enforcement_score,
                "ad_compliance": ad_score
            },
            source_extractors=["faa_registry", "iata_operator"],
            metadata={"composite_score": regulatory_composite}
        )
        composite_scores["regulatory_compliance"] = regulatory_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class AerospaceFleetQualityAggregator(DataAggregator):
    """
    Aggregates fleet quality signals for aerospace coverage.
    
    Input Extractors:
    - AircraftFleetExtractor: Fleet composition, ages, types
    - FAARegistryExtractor: Registration data
    
    Output Signals:
    - fleet_size (ThresholdBucket)
    - fleet_age (ThresholdBucket)
    - fleet_quality (Composite)
    """
    
    required_extractors = ["aircraft_fleet"]
    optional_extractors = ["faa_registry"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        fleet_data = extractions.get("aircraft_fleet", {})
        entity_id = self._safe_get(fleet_data, "operator_id", default="UNKNOWN")
        
        # --- Fleet Size ---
        summary = self._safe_get(fleet_data, "fleet_summary", default={})
        fleet_size = summary.get("total_aircraft", 0)
        
        signals["fleet_size"] = SignalOutput(
            signal_name="fleet_size",
            categorizer_type="threshold_bucket",
            configuration="fleet_size",
            data={"value": fleet_size},
            source_extractors=["aircraft_fleet"],
            metadata={"coverage": "aerospace", "active": summary.get("active", 0)}
        )
        
        # Aerospace-specific size scoring
        if fleet_size <= 3:
            size_score = 55
        elif fleet_size <= 10:
            size_score = 65
        elif fleet_size <= 25:
            size_score = 75
        elif fleet_size <= 75:
            size_score = 85
        elif fleet_size <= 200:
            size_score = 90
        else:
            size_score = 95
        composite_scores["fleet_size"] = size_score
        
        # --- Fleet Age ---
        avg_age = summary.get("average_age", 12)
        
        signals["fleet_age"] = SignalOutput(
            signal_name="fleet_age",
            categorizer_type="threshold_bucket",
            configuration="fleet_age",
            data={"value": avg_age},
            source_extractors=["aircraft_fleet"],
            metadata={"coverage": "aerospace"}
        )
        
        # Aerospace-specific age scoring
        if avg_age <= 3:
            age_score = 95
        elif avg_age <= 8:
            age_score = 88
        elif avg_age <= 15:
            age_score = 78
        elif avg_age <= 20:
            age_score = 65
        else:
            age_score = 50
        composite_scores["fleet_age"] = age_score
        
        # --- Fleet Composition ---
        aircraft = self._safe_get(fleet_data, "aircraft", default=[])
        owned_pct = summary.get("owned_pct", 35)
        
        # Ownership stability scoring
        if owned_pct >= 60:
            ownership_score = 90
        elif owned_pct >= 40:
            ownership_score = 80
        elif owned_pct >= 20:
            ownership_score = 70
        else:
            ownership_score = 60
        composite_scores["ownership_stability"] = ownership_score
        
        # --- Fleet Quality Composite ---
        fleet_composite = self._weighted_average([
            (size_score, 0.25),
            (age_score, 0.45),
            (ownership_score, 0.30)
        ])
        
        signals["fleet_quality"] = SignalOutput(
            signal_name="fleet_quality",
            categorizer_type="composite_score",
            configuration="fleet_quality",
            data={
                "fleet_size": size_score,
                "fleet_age": age_score,
                "ownership_stability": ownership_score
            },
            source_extractors=["aircraft_fleet"],
            metadata={"composite_score": fleet_composite}
        )
        composite_scores["fleet_quality"] = fleet_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class AerospaceOperationalQualityAggregator(DataAggregator):
    """
    Aggregates operational quality signals for aerospace coverage.
    
    Input Extractors:
    - OperationalPerformanceExtractor: OTP, dispatch reliability, utilization
    
    Output Signals:
    - on_time_performance (ThresholdBucket)
    - dispatch_reliability (ThresholdBucket)
    - operational_quality (Composite)
    """
    
    required_extractors = ["operational_performance"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        ops_data = extractions.get("operational_performance", {})
        entity_id = self._safe_get(ops_data, "operator_id", default="UNKNOWN")
        
        performance = self._safe_get(ops_data, "performance_12mo", default={})
        
        # --- On-Time Performance ---
        otp = performance.get("on_time_performance_pct", 75)
        
        signals["on_time_performance"] = SignalOutput(
            signal_name="on_time_performance",
            categorizer_type="threshold_bucket",
            configuration="on_time_performance",
            data={"value": otp},
            source_extractors=["operational_performance"]
        )
        
        if otp >= 90:
            otp_score = 95
        elif otp >= 85:
            otp_score = 88
        elif otp >= 80:
            otp_score = 78
        elif otp >= 75:
            otp_score = 68
        elif otp >= 70:
            otp_score = 55
        else:
            otp_score = 40
        composite_scores["on_time_performance"] = otp_score
        
        # --- Dispatch Reliability ---
        dispatch = performance.get("dispatch_reliability_pct", 98)
        
        signals["dispatch_reliability"] = SignalOutput(
            signal_name="dispatch_reliability",
            categorizer_type="threshold_bucket",
            configuration="dispatch_reliability",
            data={"value": dispatch},
            source_extractors=["operational_performance"]
        )
        
        if dispatch >= 99.5:
            dispatch_score = 100
        elif dispatch >= 99.0:
            dispatch_score = 92
        elif dispatch >= 98.0:
            dispatch_score = 82
        elif dispatch >= 97.0:
            dispatch_score = 70
        else:
            dispatch_score = 55
        composite_scores["dispatch_reliability"] = dispatch_score
        
        # --- Operational Quality Composite ---
        ops_composite = self._weighted_average([
            (otp_score, 0.40),
            (dispatch_score, 0.60)
        ])
        
        signals["operational_quality"] = SignalOutput(
            signal_name="operational_quality",
            categorizer_type="composite_score",
            configuration="operational_quality",
            data={
                "on_time_performance": otp_score,
                "dispatch_reliability": dispatch_score
            },
            source_extractors=["operational_performance"],
            metadata={"composite_score": ops_composite}
        )
        composite_scores["operational_quality"] = ops_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class AerospaceMaintenanceQualityAggregator(DataAggregator):
    """
    Aggregates maintenance quality signals for aerospace coverage.
    
    Input Extractors:
    - MROProviderExtractor: MRO relationships, quality metrics
    
    Output Signals:
    - mro_tier (QualityTier)
    - maintenance_findings (ThresholdBucket)
    - maintenance_quality (Composite)
    """
    
    required_extractors = ["mro_provider"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        mro_data = extractions.get("mro_provider", {})
        entity_id = self._safe_get(mro_data, "operator_id", default="UNKNOWN")
        
        # --- MRO Tier ---
        relationships = self._safe_get(mro_data, "mro_relationships", default=[])
        
        # Find highest tier MRO
        tier_scores = {"OEM Affiliated": 95, "Major Independent": 85, "Regional": 70, "In-House": 75}
        best_tier_score = 60
        best_tier = "Unknown"
        
        for rel in relationships:
            tier = rel.get("tier", "Unknown")
            audit_result = rel.get("audit_result", "Unknown")
            tier_score = tier_scores.get(tier, 60)
            
            # Adjust for audit results
            if audit_result == "Unsatisfactory":
                tier_score -= 20
            elif audit_result == "Satisfactory with Findings":
                tier_score -= 5
            
            if tier_score > best_tier_score:
                best_tier_score = tier_score
                best_tier = tier
        
        signals["mro_tier"] = SignalOutput(
            signal_name="mro_tier",
            categorizer_type="quality_tier",
            configuration="mro_provider",
            data={"entity": best_tier.lower().replace(" ", "_")},
            source_extractors=["mro_provider"],
            metadata={"mro_count": len(relationships)}
        )
        composite_scores["mro_tier"] = best_tier_score
        
        # --- Maintenance Metrics ---
        summary = self._safe_get(mro_data, "maintenance_summary", default={})
        on_time_rate = summary.get("on_time_rate", 0.90) * 100
        avg_findings = summary.get("avg_findings_per_event", 2.0)
        
        # Findings score
        if avg_findings <= 1.0:
            findings_score = 95
        elif avg_findings <= 2.0:
            findings_score = 85
        elif avg_findings <= 3.0:
            findings_score = 70
        else:
            findings_score = 55
        
        signals["maintenance_findings"] = SignalOutput(
            signal_name="maintenance_findings",
            categorizer_type="threshold_bucket",
            configuration="maintenance_findings",
            data={"value": avg_findings},
            source_extractors=["mro_provider"],
            metadata={"on_time_rate_pct": on_time_rate}
        )
        composite_scores["maintenance_findings"] = findings_score
        
        # --- Maintenance Quality Composite ---
        maint_composite = self._weighted_average([
            (best_tier_score, 0.50),
            (findings_score, 0.50)
        ])
        
        signals["maintenance_quality"] = SignalOutput(
            signal_name="maintenance_quality",
            categorizer_type="composite_score",
            configuration="maintenance_quality",
            data={
                "mro_tier": best_tier_score,
                "maintenance_findings": findings_score
            },
            source_extractors=["mro_provider"],
            metadata={"composite_score": maint_composite}
        )
        composite_scores["maintenance_quality"] = maint_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class AerospaceCrewQualityAggregator(DataAggregator):
    """
    Aggregates crew quality signals for aerospace coverage.
    
    Input Extractors:
    - CrewTrainingExtractor: Pilot qualifications, training metrics
    
    Output Signals:
    - training_compliance (ThresholdBucket)
    - crew_experience (ThresholdBucket)
    - crew_quality (Composite)
    """
    
    required_extractors = ["crew_training"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        crew_data = extractions.get("crew_training", {})
        entity_id = self._safe_get(crew_data, "operator_id", default="UNKNOWN")
        
        # --- Training Compliance ---
        compliance = self._safe_get(crew_data, "training_compliance", default={})
        recurrent_pct = compliance.get("recurrent_current_pct", 95)
        
        signals["training_compliance"] = SignalOutput(
            signal_name="training_compliance",
            categorizer_type="threshold_bucket",
            configuration="training_compliance",
            data={"value": recurrent_pct},
            source_extractors=["crew_training"]
        )
        
        if recurrent_pct >= 99:
            training_score = 100
        elif recurrent_pct >= 97:
            training_score = 90
        elif recurrent_pct >= 95:
            training_score = 80
        elif recurrent_pct >= 90:
            training_score = 65
        else:
            training_score = 45
        composite_scores["training_compliance"] = training_score
        
        # --- Crew Experience ---
        roster = self._safe_get(crew_data, "pilot_roster", default={})
        avg_hours = roster.get("average_total_hours", 8000)
        low_time_pct = self._safe_divide(
            roster.get("pilots_under_1500_hrs", 0),
            roster.get("total_pilots", 1),
            0
        ) * 100
        
        # Experience scoring
        if avg_hours >= 12000 and low_time_pct < 5:
            experience_score = 95
        elif avg_hours >= 8000:
            experience_score = 85
        elif avg_hours >= 5000:
            experience_score = 75
        else:
            experience_score = 60
        
        # Penalty for high percentage of low-time pilots
        if low_time_pct > 10:
            experience_score -= 15
        elif low_time_pct > 5:
            experience_score -= 5
        
        experience_score = max(30, experience_score)
        
        signals["crew_experience"] = SignalOutput(
            signal_name="crew_experience",
            categorizer_type="threshold_bucket",
            configuration="crew_experience",
            data={"value": avg_hours},
            source_extractors=["crew_training"],
            metadata={"low_time_pilot_pct": low_time_pct}
        )
        composite_scores["crew_experience"] = experience_score
        
        # --- Pass Rates ---
        metrics = self._safe_get(crew_data, "training_metrics", default={})
        pass_rate = metrics.get("pass_rate_pct", 95)
        
        if pass_rate >= 98:
            pass_score = 95
        elif pass_rate >= 95:
            pass_score = 85
        elif pass_rate >= 92:
            pass_score = 72
        else:
            pass_score = 55
        composite_scores["pass_rate"] = pass_score
        
        # --- Crew Quality Composite ---
        crew_composite = self._weighted_average([
            (training_score, 0.35),
            (experience_score, 0.40),
            (pass_score, 0.25)
        ])
        
        signals["crew_quality"] = SignalOutput(
            signal_name="crew_quality",
            categorizer_type="composite_score",
            configuration="crew_quality",
            data={
                "training_compliance": training_score,
                "crew_experience": experience_score,
                "pass_rate": pass_score
            },
            source_extractors=["crew_training"],
            metadata={"composite_score": crew_composite}
        )
        composite_scores["crew_quality"] = crew_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class AerospaceFinancialStabilityAggregator(DataAggregator):
    """
    Aggregates financial stability signals for aerospace coverage.
    
    Input Extractors:
    - AviationFinancialExtractor: Revenue, leverage, cash
    - CreditRatingExtractor: Credit ratings (common)
    
    Output Signals:
    - credit_rating (QualityTier)
    - leverage_metrics (ThresholdBucket)
    - financial_stability (Composite)
    """
    
    required_extractors = ["aviation_financial"]
    optional_extractors = ["credit_rating"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        fin_data = extractions.get("aviation_financial", {})
        entity_id = self._safe_get(fin_data, "operator_id", default="UNKNOWN")
        
        # --- Credit Rating (similar to marine) ---
        credit_data = extractions.get("credit_rating", {})
        ratings = self._safe_get(credit_data, "ratings", default=[])
        
        if ratings:
            best_rating = ratings[0].get("rating", "NR")
            is_investment_grade = any(r.get("investment_grade", False) for r in ratings)
            
            if is_investment_grade:
                rating_score = 88
            else:
                rating_score = 60
        else:
            best_rating = "NR"
            rating_score = 55
        
        signals["credit_rating"] = SignalOutput(
            signal_name="credit_rating",
            categorizer_type="quality_tier",
            configuration="credit_rating",
            data={"entity": best_rating.lower()},
            source_extractors=["credit_rating"]
        )
        composite_scores["credit_rating"] = rating_score
        
        # --- Leverage ---
        leverage = self._safe_get(fin_data, "leverage", default={})
        financials = self._safe_get(fin_data, "financials", default={})
        
        ebitdar = financials.get("ebitdar_usd", 1)
        lease_adjusted_debt = leverage.get("lease_adjusted_debt_usd", 0)
        
        debt_to_ebitdar = self._safe_divide(lease_adjusted_debt, ebitdar, 5.0)
        
        signals["leverage_metrics"] = SignalOutput(
            signal_name="leverage_metrics",
            categorizer_type="threshold_bucket",
            configuration="debt_to_ebitdar",
            data={"value": debt_to_ebitdar},
            source_extractors=["aviation_financial"]
        )
        
        if debt_to_ebitdar <= 2.0:
            leverage_score = 95
        elif debt_to_ebitdar <= 3.5:
            leverage_score = 85
        elif debt_to_ebitdar <= 5.0:
            leverage_score = 70
        elif debt_to_ebitdar <= 7.0:
            leverage_score = 50
        else:
            leverage_score = 30
        composite_scores["leverage_metrics"] = leverage_score
        
        # --- Liquidity ---
        cash = leverage.get("cash_usd", 0)
        revenue = financials.get("revenue_usd", 1)
        cash_pct = self._safe_divide(cash, revenue, 0) * 100
        
        if cash_pct >= 15:
            liquidity_score = 90
        elif cash_pct >= 10:
            liquidity_score = 80
        elif cash_pct >= 5:
            liquidity_score = 65
        else:
            liquidity_score = 45
        composite_scores["liquidity"] = liquidity_score
        
        # --- Financial Stability Composite ---
        financial_composite = self._weighted_average([
            (rating_score, 0.30),
            (leverage_score, 0.40),
            (liquidity_score, 0.30)
        ])
        
        signals["financial_stability"] = SignalOutput(
            signal_name="financial_stability",
            categorizer_type="composite_score",
            configuration="financial_stability",
            data={
                "credit_rating": rating_score,
                "leverage_metrics": leverage_score,
                "liquidity": liquidity_score
            },
            source_extractors=["aviation_financial", "credit_rating"],
            metadata={"composite_score": financial_composite}
        )
        composite_scores["financial_stability"] = financial_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )
        
        if total_claims == 0:
            claims_score = 100
        elif total_claims == 1:
            claims_score = 80
        elif total_claims <= 3:
            claims_score = 60
        else:
            claims_score = 40
        composite_scores["claims_history"] = claims_score
        
        # --- Dark Web Exposure ---
        threat_data = extractions.get("threat_intelligence", {})
        dark_web = self._safe_get(threat_data, "dark_web_monitoring", default={})
        mentions = dark_web.get("mentions_90d", 0)
        data_for_sale = dark_web.get("data_for_sale", False)
        
        if mentions == 0 and not data_for_sale:
            dark_web_score = 100
        elif mentions <= 10:
            dark_web_score = 85
        elif mentions <= 50:
            dark_web_score = 65
        elif data_for_sale:
            dark_web_score = 30
        else:
            dark_web_score = 50
        composite_scores["dark_web_exposure"] = dark_web_score
        
        # --- Public Record Composite ---
        public_composite = self._weighted_average([
            (breach_score, 0.50),
            (claims_score, 0.25),
            (dark_web_score, 0.25)
        ])
        
        signals["public_record"] = SignalOutput(
            signal_name="public_record",
            categorizer_type="composite_score",
            configuration="public_record",
            data={
                "breach_history": breach_score,
                "claims_history": claims_score,
                "dark_web_exposure": dark_web_score
            },
            source_extractors=["breach_database", "cyber_insurance_history", "threat_intelligence"],
            metadata={"composite_score": public_composite}
        )
        composite_scores["public_record"] = public_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


# =============================================================================
# CYBER AGGREGATORS
# =============================================================================

@register_aggregator
class CyberTechnicalInfrastructureAggregator(DataAggregator):
    """Aggregates technical infrastructure signals for cyber coverage."""
    
    required_extractors = ["security_scorecard"]
    optional_extractors = ["cve_exposure", "threat_intelligence"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        ssc_data = extractions.get("security_scorecard", {})
        entity_id = self._safe_get(ssc_data, "company_id", default="UNKNOWN")
        
        # Security Rating
        overall = self._safe_get(ssc_data, "overall_rating", default={})
        score = overall.get("score", 70)
        
        signals["security_rating"] = SignalOutput(
            signal_name="security_rating",
            categorizer_type="threshold_bucket",
            configuration="security_score",
            data={"value": score},
            source_extractors=["security_scorecard"]
        )
        
        if score >= 85:
            rating_score = 95
        elif score >= 70:
            rating_score = 80
        elif score >= 55:
            rating_score = 65
        else:
            rating_score = 45
        composite_scores["security_rating"] = rating_score
        
        # Vulnerability Exposure
        cve_data = extractions.get("cve_exposure", {})
        vuln_summary = self._safe_get(cve_data, "vulnerability_summary", default={})
        critical = vuln_summary.get("critical", 0)
        
        if critical == 0:
            vuln_score = 95
        elif critical <= 2:
            vuln_score = 75
        elif critical <= 5:
            vuln_score = 55
        else:
            vuln_score = 35
        composite_scores["vulnerability_exposure"] = vuln_score
        
        # Composite
        tech_composite = self._weighted_average([
            (rating_score, 0.50),
            (vuln_score, 0.50)
        ])
        
        signals["technical_infrastructure"] = SignalOutput(
            signal_name="technical_infrastructure",
            categorizer_type="composite_score",
            configuration="technical_infrastructure",
            data={"security_rating": rating_score, "vulnerability_exposure": vuln_score},
            source_extractors=["security_scorecard", "cve_exposure"],
            metadata={"composite_score": tech_composite}
        )
        composite_scores["technical_infrastructure"] = tech_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class CyberPublicRecordAggregator(DataAggregator):
    """Aggregates public record signals for cyber coverage."""
    
    required_extractors = ["breach_database"]
    optional_extractors = ["cyber_insurance_history", "threat_intelligence"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        breach_data = extractions.get("breach_database", {})
        entity_id = self._safe_get(breach_data, "company_id", default="UNKNOWN")
        
        # Breach History
        history = self._safe_get(breach_data, "breach_history", default={})
        total_breaches = history.get("total_breaches_5yr", 0)
        total_records = history.get("total_records_exposed", 0)
        
        if total_breaches == 0:
            breach_state = "NONE"
            breach_score = 100
        elif total_breaches == 1 and total_records < 100000:
            breach_state = "MINOR_1"
            breach_score = 85
        elif total_breaches <= 2:
            breach_state = "MINOR_2_PLUS"
            breach_score = 70
        else:
            breach_state = "MAJOR"
            breach_score = 40
        
        signals["breach_history_3yr"] = SignalOutput(
            signal_name="breach_history_3yr",
            categorizer_type="scoring_logic",
            configuration="breach_history_3yr",
            data={"state": breach_state},
            source_extractors=["breach_database"],
            metadata={"total_breaches": total_breaches}
        )
        composite_scores["breach_history"] = breach_score
        
        signals["public_record"] = SignalOutput(
            signal_name="public_record",
            categorizer_type="composite_score",
            configuration="public_record",
            data={"breach_history": breach_score},
            source_extractors=["breach_database"],
            metadata={"composite_score": breach_score}
        )
        composite_scores["public_record"] = breach_score
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class CyberGovernanceAggregator(DataAggregator):
    """
    Aggregates governance signals for cyber coverage.
    
    Input Extractors:
    - CyberGovernanceExtractor: CISO, certifications, policies
    
    Output Signals:
    - ciso_present (Boolean)
    - certifications (ScoringLogic)
    - governance (Composite)
    """
    
    required_extractors = ["cyber_governance"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        gov_data = extractions.get("cyber_governance", {})
        entity_id = self._safe_get(gov_data, "company_id", default="UNKNOWN")
        
        # --- CISO Presence ---
        leadership = self._safe_get(gov_data, "leadership", default={})
        has_ciso = leadership.get("has_ciso", False)
        board_oversight = leadership.get("board_cyber_oversight", False)
        
        signals["ciso_present"] = SignalOutput(
            signal_name="ciso_present",
            categorizer_type="boolean_flag",
            configuration="ciso_present",
            data={"flag": has_ciso},
            source_extractors=["cyber_governance"],
            metadata={"reports_to": leadership.get("ciso_reports_to")}
        )
        
        ciso_score = 95 if has_ciso else 50
        if has_ciso and leadership.get("ciso_reports_to") in ["CEO", "Board"]:
            ciso_score = 100
        composite_scores["ciso_present"] = ciso_score
        
        # --- Certifications ---
        certs = self._safe_get(gov_data, "certifications", default=[])
        current_certs = [c for c in certs if c.get("status") == "Current"]
        enterprise_certs = [c for c in current_certs if c.get("scope") == "Enterprise-wide"]
        
        key_certs = ["SOC 2 Type II", "ISO 27001"]
        has_key_cert = any(c["certification"] in key_certs for c in current_certs)
        
        if len(enterprise_certs) >= 2 and has_key_cert:
            cert_state = "COMPREHENSIVE"
            cert_score = 95
        elif has_key_cert:
            cert_state = "STANDARD"
            cert_score = 80
        elif len(current_certs) > 0:
            cert_state = "PARTIAL"
            cert_score = 65
        else:
            cert_state = "NONE"
            cert_score = 40
        
        signals["certifications"] = SignalOutput(
            signal_name="certifications",
            categorizer_type="scoring_logic",
            configuration="security_certifications",
            data={"state": cert_state},
            source_extractors=["cyber_governance"],
            metadata={"certifications": [c["certification"] for c in current_certs]}
        )
        composite_scores["certifications"] = cert_score
        
        # --- Maturity Level ---
        maturity = self._safe_get(gov_data, "maturity", default={})
        maturity_level = maturity.get("level", 2)
        
        maturity_scores = {1: 40, 2: 55, 3: 75, 4: 88, 5: 98}
        maturity_score = maturity_scores.get(maturity_level, 55)
        composite_scores["maturity_level"] = maturity_score
        
        # --- Policies ---
        policies = self._safe_get(gov_data, "policies", default={})
        ir_plan = policies.get("incident_response_plan", False)
        bcp = policies.get("business_continuity_plan", False)
        training = policies.get("security_awareness_training", False)
        
        policy_count = sum([ir_plan, bcp, training])
        policy_score = 40 + (policy_count * 20)
        composite_scores["policies"] = policy_score
        
        # --- Governance Composite ---
        gov_composite = self._weighted_average([
            (ciso_score, 0.30),
            (cert_score, 0.25),
            (maturity_score, 0.25),
            (policy_score, 0.20)
        ])
        
        signals["governance"] = SignalOutput(
            signal_name="governance",
            categorizer_type="composite_score",
            configuration="governance",
            data={
                "ciso_present": ciso_score,
                "certifications": cert_score,
                "maturity_level": maturity_score,
                "policies": policy_score
            },
            source_extractors=["cyber_governance"],
            metadata={"composite_score": gov_composite}
        )
        composite_scores["governance"] = gov_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class CyberVendorManagementAggregator(DataAggregator):
    """
    Aggregates vendor management signals for cyber coverage.
    
    Input Extractors:
    - VendorSecurityExtractor: Third-party risk management
    
    Output Signals:
    - vendor_risk_program (ScoringLogic)
    - vendor_management (Composite)
    """
    
    required_extractors = ["vendor_security"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        vendor_data = extractions.get("vendor_security", {})
        entity_id = self._safe_get(vendor_data, "company_id", default="UNKNOWN")
        
        # --- Vendor Risk Program ---
        program = self._safe_get(vendor_data, "program_maturity", default={})
        vrm_exists = program.get("vrm_program_exists", False)
        automated = program.get("automated_monitoring", False)
        
        assessment = self._safe_get(vendor_data, "assessment_coverage", default={})
        assessed_pct = assessment.get("assessed_12mo_pct", 0)
        critical_assessed = assessment.get("critical_assessed_pct", 0)
        
        if vrm_exists and critical_assessed >= 95 and automated:
            program_state = "MATURE"
            program_score = 95
        elif vrm_exists and critical_assessed >= 85:
            program_state = "ESTABLISHED"
            program_score = 80
        elif vrm_exists and assessed_pct >= 50:
            program_state = "DEVELOPING"
            program_score = 65
        elif vrm_exists:
            program_state = "BASIC"
            program_score = 50
        else:
            program_state = "NONE"
            program_score = 30
        
        signals["vendor_risk_program"] = SignalOutput(
            signal_name="vendor_risk_program",
            categorizer_type="scoring_logic",
            configuration="vendor_risk_program",
            data={"state": program_state},
            source_extractors=["vendor_security"],
            metadata={
                "assessed_pct": assessed_pct,
                "critical_assessed_pct": critical_assessed
            }
        )
        composite_scores["vendor_risk_program"] = program_score
        
        # --- Vendor Inventory Risk ---
        inventory = self._safe_get(vendor_data, "vendor_inventory", default={})
        total_vendors = inventory.get("total", 100)
        critical_vendors = inventory.get("critical", 10)
        high_risk = inventory.get("high_risk", 15)
        
        risk_pct = self._safe_divide(high_risk + critical_vendors, total_vendors, 0.15) * 100
        
        if risk_pct <= 10:
            risk_score = 90
        elif risk_pct <= 20:
            risk_score = 75
        elif risk_pct <= 35:
            risk_score = 60
        else:
            risk_score = 40
        composite_scores["vendor_risk_concentration"] = risk_score
        
        # --- Vendor Management Composite ---
        vendor_composite = self._weighted_average([
            (program_score, 0.60),
            (risk_score, 0.40)
        ])
        
        signals["vendor_management"] = SignalOutput(
            signal_name="vendor_management",
            categorizer_type="composite_score",
            configuration="vendor_management",
            data={
                "vendor_risk_program": program_score,
                "vendor_risk_concentration": risk_score
            },
            source_extractors=["vendor_security"],
            metadata={"composite_score": vendor_composite}
        )
        composite_scores["vendor_management"] = vendor_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class CyberIncidentResponseAggregator(DataAggregator):
    """
    Aggregates incident response signals for cyber coverage.
    
    Input Extractors:
    - IncidentResponseExtractor: IR capabilities, SOC, retainers
    
    Output Signals:
    - ir_capabilities (ScoringLogic)
    - incident_response (Composite)
    """
    
    required_extractors = ["incident_response"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        ir_data = extractions.get("incident_response", {})
        entity_id = self._safe_get(ir_data, "company_id", default="UNKNOWN")
        
        # --- IR Capabilities ---
        capabilities = self._safe_get(ir_data, "ir_capabilities", default={})
        ir_plan = capabilities.get("ir_plan_documented", False)
        ir_tested = capabilities.get("ir_plan_tested_12mo", False)
        tabletops = capabilities.get("tabletop_exercises_12mo", 0)
        has_retainer = capabilities.get("ir_retainer", False)
        
        if ir_plan and ir_tested and tabletops >= 2 and has_retainer:
            ir_state = "COMPREHENSIVE"
            ir_score = 95
        elif ir_plan and ir_tested and has_retainer:
            ir_state = "STRONG"
            ir_score = 85
        elif ir_plan and ir_tested:
            ir_state = "ADEQUATE"
            ir_score = 70
        elif ir_plan:
            ir_state = "BASIC"
            ir_score = 55
        else:
            ir_state = "MINIMAL"
            ir_score = 30
        
        signals["ir_capabilities"] = SignalOutput(
            signal_name="ir_capabilities",
            categorizer_type="scoring_logic",
            configuration="ir_capabilities",
            data={"state": ir_state},
            source_extractors=["incident_response"],
            metadata={
                "has_plan": ir_plan,
                "tested": ir_tested,
                "tabletops": tabletops,
                "retainer": has_retainer
            }
        )
        composite_scores["ir_capabilities"] = ir_score
        
        # --- Response Metrics ---
        metrics = self._safe_get(ir_data, "response_metrics", default={})
        mttd = metrics.get("mttd_hours", 48)
        mttr = metrics.get("mttr_hours", 96)
        
        if mttd <= 6 and mttr <= 24:
            response_score = 95
        elif mttd <= 24 and mttr <= 48:
            response_score = 80
        elif mttd <= 48 and mttr <= 96:
            response_score = 65
        else:
            response_score = 45
        composite_scores["response_metrics"] = response_score
        
        # --- SOC Capabilities ---
        soc = self._safe_get(ir_data, "soc_capabilities", default={})
        has_soc = soc.get("has_soc", False)
        is_24x7 = soc.get("24x7_coverage", False)
        
        if has_soc and is_24x7:
            soc_score = 95
        elif has_soc:
            soc_score = 75
        else:
            soc_score = 50
        composite_scores["soc_capabilities"] = soc_score
        
        # --- Incident Response Composite ---
        incident_composite = self._weighted_average([
            (ir_score, 0.45),
            (response_score, 0.30),
            (soc_score, 0.25)
        ])
        
        signals["incident_response"] = SignalOutput(
            signal_name="incident_response",
            categorizer_type="composite_score",
            configuration="incident_response",
            data={
                "ir_capabilities": ir_score,
                "response_metrics": response_score,
                "soc_capabilities": soc_score
            },
            source_extractors=["incident_response"],
            metadata={"composite_score": incident_composite}
        )
        composite_scores["incident_response"] = incident_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


# =============================================================================
# D&O AGGREGATORS
# =============================================================================

@register_aggregator
class DOGovernanceAggregator(DataAggregator):
    """
    Aggregates governance signals for D&O coverage.
    
    Input Extractors:
    - ProxyStatementExtractor: Board composition, committees
    
    Output Signals:
    - board_independence (ThresholdBucket)
    - governance (Composite)
    """
    
    required_extractors = ["proxy_statement"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        proxy_data = extractions.get("proxy_statement", {})
        entity_id = self._safe_get(proxy_data, "company_id", default="UNKNOWN")
        
        # --- Board Independence ---
        board = self._safe_get(proxy_data, "board_composition", default={})
        independence_pct = board.get("independence_pct", 70)
        
        signals["board_independence"] = SignalOutput(
            signal_name="board_independence",
            categorizer_type="threshold_bucket",
            configuration="board_independence",
            data={"value": independence_pct},
            source_extractors=["proxy_statement"]
        )
        
        if independence_pct >= 80:
            independence_score = 95
        elif independence_pct >= 70:
            independence_score = 85
        elif independence_pct >= 60:
            independence_score = 70
        elif independence_pct >= 50:
            independence_score = 55
        else:
            independence_score = 40
        composite_scores["board_independence"] = independence_score
        
        # --- Board Quality Factors ---
        ceo_chair_separated = board.get("ceo_chair_separated", False)
        lead_independent = board.get("lead_independent_director", False)
        diversity_pct = board.get("diversity_pct", 20)
        
        structure_score = 50
        if ceo_chair_separated:
            structure_score += 25
        if lead_independent:
            structure_score += 15
        if diversity_pct >= 30:
            structure_score += 10
        composite_scores["board_structure"] = min(100, structure_score)
        
        # --- Committee Quality ---
        committees = self._safe_get(proxy_data, "committees", default={})
        audit_ind = committees.get("audit_independent", True)
        comp_ind = committees.get("comp_independent", True)
        
        committee_score = 70
        if audit_ind:
            committee_score += 15
        if comp_ind:
            committee_score += 15
        composite_scores["committee_quality"] = min(100, committee_score)
        
        # --- Governance Provisions ---
        provisions = self._safe_get(proxy_data, "governance_provisions", default={})
        classified = provisions.get("classified_board", False)
        poison_pill = provisions.get("poison_pill", False)
        majority_voting = provisions.get("majority_voting", True)
        
        provisions_score = 80
        if classified:
            provisions_score -= 15
        if poison_pill:
            provisions_score -= 10
        if not majority_voting:
            provisions_score -= 10
        composite_scores["governance_provisions"] = max(40, provisions_score)
        
        # --- Governance Composite ---
        gov_composite = self._weighted_average([
            (independence_score, 0.30),
            (composite_scores["board_structure"], 0.25),
            (composite_scores["committee_quality"], 0.25),
            (composite_scores["governance_provisions"], 0.20)
        ])
        
        signals["governance"] = SignalOutput(
            signal_name="governance",
            categorizer_type="composite_score",
            configuration="governance",
            data={
                "board_independence": independence_score,
                "board_structure": composite_scores["board_structure"],
                "committee_quality": composite_scores["committee_quality"],
                "governance_provisions": composite_scores["governance_provisions"]
            },
            source_extractors=["proxy_statement"],
            metadata={"composite_score": gov_composite}
        )
        composite_scores["governance"] = gov_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class DOLitigationAggregator(DataAggregator):
    """
    Aggregates litigation signals for D&O coverage.
    
    Input Extractors:
    - LitigationDatabaseExtractor: Case history, settlements
    
    Output Signals:
    - securities_litigation (ScoringLogic)
    - litigation (Composite)
    """
    
    required_extractors = ["litigation_database"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        lit_data = extractions.get("litigation_database", {})
        entity_id = self._safe_get(lit_data, "company_id", default="UNKNOWN")
        
        # --- Securities Litigation ---
        summary = self._safe_get(lit_data, "litigation_summary", default={})
        total_cases = summary.get("total_cases_5yr", 0)
        sca = summary.get("securities_class_actions", 0)
        regulatory = summary.get("regulatory_matters", 0)
        active = summary.get("active_cases", 0)
        
        if sca == 0 and regulatory == 0:
            lit_state = "CLEAN"
            lit_score = 100
        elif sca <= 1 and regulatory == 0:
            lit_state = "MINOR"
            lit_score = 75
        elif sca <= 2 or regulatory <= 1:
            lit_state = "MODERATE"
            lit_score = 55
        elif sca <= 3 or regulatory <= 2:
            lit_state = "ELEVATED"
            lit_score = 35
        else:
            lit_state = "SEVERE"
            lit_score = 15
        
        signals["securities_litigation"] = SignalOutput(
            signal_name="securities_litigation",
            categorizer_type="scoring_logic",
            configuration="securities_litigation",
            data={"state": lit_state},
            source_extractors=["litigation_database"],
            metadata={
                "total_cases": total_cases,
                "securities_class_actions": sca,
                "regulatory_matters": regulatory
            }
        )
        composite_scores["securities_litigation"] = lit_score
        
        # --- Financial Exposure ---
        exposure = self._safe_get(lit_data, "financial_exposure", default={})
        pending = exposure.get("total_pending_usd", 0)
        settlements = exposure.get("total_settlements_usd", 0)
        
        total_exposure = pending + settlements
        if total_exposure == 0:
            exposure_score = 100
        elif total_exposure < 5_000_000:
            exposure_score = 85
        elif total_exposure < 25_000_000:
            exposure_score = 65
        elif total_exposure < 100_000_000:
            exposure_score = 45
        else:
            exposure_score = 25
        composite_scores["financial_exposure"] = exposure_score
        
        # --- Litigation Composite ---
        lit_composite = self._weighted_average([
            (lit_score, 0.60),
            (exposure_score, 0.40)
        ])
        
        signals["litigation"] = SignalOutput(
            signal_name="litigation",
            categorizer_type="composite_score",
            configuration="litigation",
            data={
                "securities_litigation": lit_score,
                "financial_exposure": exposure_score
            },
            source_extractors=["litigation_database"],
            metadata={"composite_score": lit_composite}
        )
        composite_scores["litigation"] = lit_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class DOFinancialAggregator(DataAggregator):
    """
    Aggregates financial signals for D&O coverage.
    
    Input Extractors:
    - SECEdgarExtractor: Financials, accounting quality
    - DOFinancialExtractor: Detailed metrics
    
    Output Signals:
    - market_cap (ThresholdBucket)
    - accounting_quality (ScoringLogic)
    - financial (Composite)
    """
    
    required_extractors = ["sec_edgar"]
    optional_extractors = ["do_financial"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        edgar_data = extractions.get("sec_edgar", {})
        entity_id = self._safe_get(edgar_data, "company", "cik", default="UNKNOWN")
        
        # --- Market Cap ---
        market_data = self._safe_get(edgar_data, "market_data", default={})
        market_cap = market_data.get("market_cap_usd") or 0
        is_public = market_data.get("is_public", False)
        
        signals["market_cap"] = SignalOutput(
            signal_name="market_cap",
            categorizer_type="threshold_bucket",
            configuration="market_cap",
            data={"value": market_cap},
            source_extractors=["sec_edgar"],
            metadata={"is_public": is_public, "category": market_data.get("market_cap_category")}
        )
        
        # Market cap scoring (larger = more stable but more exposure)
        if market_cap >= 200_000_000_000:
            cap_score = 88
        elif market_cap >= 10_000_000_000:
            cap_score = 83
        elif market_cap >= 2_000_000_000:
            cap_score = 78
        elif market_cap >= 300_000_000:
            cap_score = 72
        elif market_cap > 0:
            cap_score = 65
        else:
            cap_score = 70  # Private company baseline
        composite_scores["market_cap"] = cap_score
        
        # --- Accounting Quality ---
        accounting = self._safe_get(edgar_data, "accounting_quality", default={})
        restatements = accounting.get("restatements_3yr", 0)
        material_weaknesses = accounting.get("material_weaknesses", 0)
        going_concern = accounting.get("going_concern", False)
        
        if going_concern:
            acct_state = "GOING_CONCERN"
            acct_score = 15
        elif material_weaknesses > 0:
            acct_state = "MATERIAL_WEAKNESS"
            acct_score = 40
        elif restatements >= 2:
            acct_state = "MULTIPLE_RESTATEMENTS"
            acct_score = 55
        elif restatements == 1:
            acct_state = "SINGLE_RESTATEMENT"
            acct_score = 75
        else:
            acct_state = "CLEAN"
            acct_score = 100
        
        signals["accounting_quality"] = SignalOutput(
            signal_name="accounting_quality",
            categorizer_type="scoring_logic",
            configuration="accounting_quality",
            data={"state": acct_state},
            source_extractors=["sec_edgar"],
            metadata={
                "restatements": restatements,
                "material_weaknesses": material_weaknesses,
                "going_concern": going_concern
            }
        )
        composite_scores["accounting_quality"] = acct_score
        
        # --- Auditor Quality ---
        auditor = accounting.get("auditor", "Unknown")
        big_4 = ["deloitte", "pwc", "ey", "kpmg"]
        
        if auditor.lower() in big_4:
            auditor_score = 95
        elif auditor.lower() in ["bdo", "grant thornton", "rsm"]:
            auditor_score = 85
        else:
            auditor_score = 70
        composite_scores["auditor_quality"] = auditor_score
        
        # --- Financial Composite ---
        fin_composite = self._weighted_average([
            (cap_score, 0.30),
            (acct_score, 0.45),
            (auditor_score, 0.25)
        ])
        
        signals["financial"] = SignalOutput(
            signal_name="financial",
            categorizer_type="composite_score",
            configuration="financial",
            data={
                "market_cap": cap_score,
                "accounting_quality": acct_score,
                "auditor_quality": auditor_score
            },
            source_extractors=["sec_edgar"],
            metadata={"composite_score": fin_composite}
        )
        composite_scores["financial"] = fin_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class DORegulatoryAggregator(DataAggregator):
    """
    Aggregates regulatory signals for D&O coverage.
    
    Input Extractors:
    - SECEnforcementExtractor: SEC actions
    - SECEdgarExtractor: Filing compliance
    
    Output Signals:
    - enforcement_history (ScoringLogic)
    - regulatory (Composite)
    """
    
    required_extractors = ["sec_enforcement"]
    optional_extractors = ["sec_edgar"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        enf_data = extractions.get("sec_enforcement", {})
        entity_id = self._safe_get(enf_data, "company_id", default="UNKNOWN")
        
        # --- Enforcement History ---
        history = self._safe_get(enf_data, "enforcement_history", default={})
        total_actions = history.get("total_actions_5yr", 0)
        total_penalties = history.get("total_penalties_usd", 0)
        pending = history.get("pending_investigations", 0)
        
        if total_actions == 0 and pending == 0:
            enf_state = "CLEAN"
            enf_score = 100
        elif total_actions == 1 and total_penalties < 1_000_000:
            enf_state = "MINOR"
            enf_score = 75
        elif total_actions <= 2:
            enf_state = "MODERATE"
            enf_score = 55
        elif pending > 0:
            enf_state = "PENDING_INVESTIGATION"
            enf_score = 35
        else:
            enf_state = "SIGNIFICANT"
            enf_score = 25
        
        signals["enforcement_history"] = SignalOutput(
            signal_name="enforcement_history",
            categorizer_type="scoring_logic",
            configuration="enforcement_history",
            data={"state": enf_state},
            source_extractors=["sec_enforcement"],
            metadata={
                "total_actions": total_actions,
                "total_penalties_usd": total_penalties,
                "pending_investigations": pending
            }
        )
        composite_scores["enforcement_history"] = enf_score
        
        # --- Individual Actions ---
        individual = self._safe_get(enf_data, "individual_actions", default={})
        officers_named = individual.get("officers_named", 0)
        bar_orders = individual.get("bar_orders", 0)
        
        if bar_orders > 0:
            individual_score = 20
        elif officers_named > 2:
            individual_score = 40
        elif officers_named > 0:
            individual_score = 60
        else:
            individual_score = 100
        composite_scores["individual_actions"] = individual_score
        
        # --- Regulatory Composite ---
        reg_composite = self._weighted_average([
            (enf_score, 0.65),
            (individual_score, 0.35)
        ])
        
        signals["regulatory"] = SignalOutput(
            signal_name="regulatory",
            categorizer_type="composite_score",
            configuration="regulatory",
            data={
                "enforcement_history": enf_score,
                "individual_actions": individual_score
            },
            source_extractors=["sec_enforcement"],
            metadata={"composite_score": reg_composite}
        )
        composite_scores["regulatory"] = reg_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class DOPublicCompanyFactorsAggregator(DataAggregator):
    """
    Aggregates public company factors for D&O coverage.
    
    Input Extractors:
    - InsiderActivityExtractor: Insider trading patterns
    - SECEdgarExtractor: Exchange, float
    
    Output Signals:
    - insider_sentiment (ScoringLogic)
    - public_company_factors (Composite)
    """
    
    required_extractors = ["insider_activity"]
    optional_extractors = ["sec_edgar"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        insider_data = extractions.get("insider_activity", {})
        entity_id = self._safe_get(insider_data, "company_id", default="UNKNOWN")
        
        # --- Insider Sentiment ---
        activity = self._safe_get(insider_data, "insider_activity_12mo", default={})
        sentiment = activity.get("net_sentiment", "Neutral")
        purchases = activity.get("purchases", 0)
        sales = activity.get("sales", 0)
        
        if sentiment == "Buying" and purchases > sales * 2:
            sentiment_state = "STRONG_BUYING"
            sentiment_score = 90
        elif sentiment == "Buying":
            sentiment_state = "NET_BUYING"
            sentiment_score = 80
        elif sentiment == "Selling" and sales > purchases * 3:
            sentiment_state = "HEAVY_SELLING"
            sentiment_score = 50
        elif sentiment == "Selling":
            sentiment_state = "NET_SELLING"
            sentiment_score = 65
        else:
            sentiment_state = "NEUTRAL"
            sentiment_score = 75
        
        signals["insider_sentiment"] = SignalOutput(
            signal_name="insider_sentiment",
            categorizer_type="scoring_logic",
            configuration="insider_sentiment",
            data={"state": sentiment_state},
            source_extractors=["insider_activity"],
            metadata={"purchases": purchases, "sales": sales}
        )
        composite_scores["insider_sentiment"] = sentiment_score
        
        # --- Exchange Quality ---
        edgar_data = extractions.get("sec_edgar", {})
        market_data = self._safe_get(edgar_data, "market_data", default={})
        
        company = self._safe_get(edgar_data, "company", default={})
        exchange = company.get("exchange", "Unknown")
        
        exchange_scores = {"NYSE": 90, "NASDAQ": 88, "NYSE American": 75, "OTC": 55}
        exchange_score = exchange_scores.get(exchange, 70)
        composite_scores["exchange_quality"] = exchange_score
        
        # --- Public Company Factors Composite ---
        public_composite = self._weighted_average([
            (sentiment_score, 0.50),
            (exchange_score, 0.50)
        ])
        
        signals["public_company_factors"] = SignalOutput(
            signal_name="public_company_factors",
            categorizer_type="composite_score",
            configuration="public_company_factors",
            data={
                "insider_sentiment": sentiment_score,
                "exchange_quality": exchange_score
            },
            source_extractors=["insider_activity", "sec_edgar"],
            metadata={"composite_score": public_composite}
        )
        composite_scores["public_company_factors"] = public_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class DOIndustryFactorsAggregator(DataAggregator):
    """
    Aggregates industry factors for D&O coverage.
    
    Input Extractors:
    - IndustryComparisonExtractor: Industry classification, risk factors
    
    Output Signals:
    - industry_classification (Enumeration)
    - industry_factors (Composite)
    """
    
    required_extractors = ["industry_comparison"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        industry_data = extractions.get("industry_comparison", {})
        entity_id = self._safe_get(industry_data, "company_id", default="UNKNOWN")
        
        # --- Industry Classification ---
        classification = self._safe_get(industry_data, "classification", default={})
        industry = classification.get("industry", "Other")
        
        # Industry risk factors for D&O
        industry_risk_scores = {
            "Technology": 75,
            "Healthcare/Pharma": 65,
            "Financial Services": 70,
            "Energy": 78,
            "Consumer Discretionary": 82,
            "Consumer Staples": 88,
            "Industrials": 85,
            "Utilities": 90,
            "Real Estate": 82,
            "Materials": 85,
            "Communication": 78
        }
        
        industry_score = industry_risk_scores.get(industry, 80)
        
        signals["industry_classification"] = SignalOutput(
            signal_name="industry_classification",
            categorizer_type="enumeration",
            configuration="industry_classification",
            data={"category": industry.upper().replace("/", "_").replace(" ", "_")},
            source_extractors=["industry_comparison"],
            metadata={"sic_code": classification.get("sic_code")}
        )
        composite_scores["industry_classification"] = industry_score
        
        # --- Industry Risk Factors ---
        risk = self._safe_get(industry_data, "industry_risk", default={})
        lit_frequency = risk.get("litigation_frequency_vs_avg", 1.0)
        reg_scrutiny = risk.get("regulatory_scrutiny", "Medium")
        
        if lit_frequency <= 0.7:
            lit_risk_score = 90
        elif lit_frequency <= 1.0:
            lit_risk_score = 80
        elif lit_frequency <= 1.3:
            lit_risk_score = 65
        else:
            lit_risk_score = 50
        
        scrutiny_scores = {"Low": 90, "Medium": 75, "High": 55}
        scrutiny_score = scrutiny_scores.get(reg_scrutiny, 75)
        
        composite_scores["litigation_risk"] = lit_risk_score
        composite_scores["regulatory_scrutiny"] = scrutiny_score
        
        # --- Industry Factors Composite ---
        industry_composite = self._weighted_average([
            (industry_score, 0.40),
            (lit_risk_score, 0.35),
            (scrutiny_score, 0.25)
        ])
        
        signals["industry_factors"] = SignalOutput(
            signal_name="industry_factors",
            categorizer_type="composite_score",
            configuration="industry_factors",
            data={
                "industry_classification": industry_score,
                "litigation_risk": lit_risk_score,
                "regulatory_scrutiny": scrutiny_score
            },
            source_extractors=["industry_comparison"],
            metadata={"composite_score": industry_composite}
        )
        composite_scores["industry_factors"] = industry_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


# =============================================================================
# FINANCIAL INSTITUTIONS AGGREGATORS
# =============================================================================

@register_aggregator
class FIRegulatoryComplianceAggregator(DataAggregator):
    """
    Aggregates regulatory compliance signals for FI coverage.
    
    Input Extractors:
    - BankRegulatoryExtractor: CAMELS, MRAs, enforcement
    - BSAAMLExtractor: BSA/AML compliance
    
    Output Signals:
    - camels_rating (ScoringLogic)
    - mra_status (ScoringLogic)
    - regulatory_compliance (Composite)
    """
    
    required_extractors = ["bank_regulatory"]
    optional_extractors = ["bsa_aml"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        reg_data = extractions.get("bank_regulatory", {})
        entity_id = self._safe_get(reg_data, "institution_id", default="UNKNOWN")
        
        # --- CAMELS Rating ---
        status = self._safe_get(reg_data, "regulatory_status", default={})
        camels = status.get("camels_composite", 2)
        
        camels_scores = {1: 100, 2: 85, 3: 60, 4: 35, 5: 10}
        camels_score = camels_scores.get(camels, 60)
        
        signals["camels_rating"] = SignalOutput(
            signal_name="camels_rating",
            categorizer_type="scoring_logic",
            configuration="camels_rating",
            data={"state": f"CAMELS_{camels}"},
            source_extractors=["bank_regulatory"],
            metadata={"components": status.get("camels_components")}
        )
        composite_scores["camels_rating"] = camels_score
        
        # --- MRA Status ---
        mras = self._safe_get(reg_data, "mras_mriaas", default={})
        total_open = mras.get("total_open", 0)
        total_mrias = mras.get("total_mrias", 0)
        past_due = mras.get("past_due", 0)
        
        if total_open == 0:
            mra_state = "NONE"
            mra_score = 100
        elif total_mrias == 0 and past_due == 0:
            mra_state = "MRA_ONLY"
            mra_score = 80
        elif total_mrias > 0 and past_due == 0:
            mra_state = "HAS_MRIA"
            mra_score = 60
        elif past_due > 0:
            mra_state = "PAST_DUE"
            mra_score = 40
        else:
            mra_state = "MRA_ONLY"
            mra_score = 80
        
        signals["mra_status"] = SignalOutput(
            signal_name="mra_status",
            categorizer_type="scoring_logic",
            configuration="mra_status",
            data={"state": mra_state},
            source_extractors=["bank_regulatory"],
            metadata={"open_mras": total_open, "mrias": total_mrias, "past_due": past_due}
        )
        composite_scores["mra_status"] = mra_score
        
        # --- Enforcement Actions ---
        enforcement = self._safe_get(reg_data, "enforcement_actions", default={})
        active_actions = enforcement.get("active_actions", 0)
        
        if active_actions == 0:
            enforcement_score = 100
        elif active_actions == 1:
            enforcement_score = 50
        else:
            enforcement_score = 25
        composite_scores["enforcement_actions"] = enforcement_score
        
        # --- BSA/AML ---
        bsa_data = extractions.get("bsa_aml", {})
        bsa_rating = self._safe_get(bsa_data, "exam_findings", "bsa_exam_rating", default=2)
        bsa_score = {1: 100, 2: 85, 3: 60, 4: 35, 5: 10}.get(bsa_rating, 60)
        composite_scores["bsa_compliance"] = bsa_score
        
        # --- Regulatory Compliance Composite ---
        reg_composite = self._weighted_average([
            (camels_score, 0.35),
            (mra_score, 0.25),
            (enforcement_score, 0.20),
            (bsa_score, 0.20)
        ])
        
        signals["regulatory_compliance"] = SignalOutput(
            signal_name="regulatory_compliance",
            categorizer_type="composite_score",
            configuration="regulatory_compliance",
            data={
                "camels_rating": camels_score,
                "mra_status": mra_score,
                "enforcement_actions": enforcement_score,
                "bsa_compliance": bsa_score
            },
            source_extractors=["bank_regulatory", "bsa_aml"],
            metadata={"composite_score": reg_composite}
        )
        composite_scores["regulatory_compliance"] = reg_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class FIFinancialConditionAggregator(DataAggregator):
    """
    Aggregates financial condition signals for FI coverage.
    
    Input Extractors:
    - FFIECCallReportExtractor: Capital, earnings, liquidity
    - LiquidityExtractor: LCR, NSFR
    
    Output Signals:
    - capital_ratio_status (ScoringLogic)
    - asset_size (ThresholdBucket)
    - financial_condition (Composite)
    """
    
    required_extractors = ["ffiec_call_report"]
    optional_extractors = ["liquidity"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        call_data = extractions.get("ffiec_call_report", {})
        entity_id = self._safe_get(call_data, "institution", "rssd_id", default="UNKNOWN")
        
        # --- Capital Status ---
        capital = self._safe_get(call_data, "capital_ratios", default={})
        tier1 = capital.get("tier1_ratio_pct", 10)
        category = capital.get("capital_category", "Adequately Capitalized")
        
        capital_states = {
            "Well Capitalized": ("WELL_CAPITALIZED", 100),
            "Adequately Capitalized": ("ADEQUATELY_CAPITALIZED", 80),
            "Undercapitalized": ("UNDERCAPITALIZED", 50),
            "Significantly Undercapitalized": ("SIGNIFICANTLY_UNDERCAPITALIZED", 25),
            "Critically Undercapitalized": ("CRITICALLY_UNDERCAPITALIZED", 10)
        }
        
        cap_state, cap_score = capital_states.get(category, ("ADEQUATELY_CAPITALIZED", 80))
        
        signals["capital_ratio_status"] = SignalOutput(
            signal_name="capital_ratio_status",
            categorizer_type="scoring_logic",
            configuration="capital_ratio_status",
            data={"state": cap_state},
            source_extractors=["ffiec_call_report"],
            metadata={"tier1_ratio": tier1, "category": category}
        )
        composite_scores["capital_ratio_status"] = cap_score
        
        # --- Asset Size ---
        balance = self._safe_get(call_data, "balance_sheet", default={})
        total_assets = balance.get("total_assets_usd", 1_000_000_000)
        
        signals["asset_size"] = SignalOutput(
            signal_name="asset_size",
            categorizer_type="threshold_bucket",
            configuration="asset_size",
            data={"value": total_assets},
            source_extractors=["ffiec_call_report"],
            metadata={"coverage": "financial_institutions"}
        )
        
        # Asset size scoring (larger = more sophisticated risk management)
        if total_assets >= 250_000_000_000:
            asset_score = 92
        elif total_assets >= 50_000_000_000:
            asset_score = 88
        elif total_assets >= 5_000_000_000:
            asset_score = 85
        elif total_assets >= 500_000_000:
            asset_score = 78
        else:
            asset_score = 70
        composite_scores["asset_size"] = asset_score
        
        # --- Earnings ---
        earnings = self._safe_get(call_data, "earnings", default={})
        roa = earnings.get("roa_pct", 1.0)
        efficiency = earnings.get("efficiency_ratio_pct", 65)
        
        if roa >= 1.2 and efficiency <= 55:
            earnings_score = 95
        elif roa >= 0.9 and efficiency <= 65:
            earnings_score = 85
        elif roa >= 0.6:
            earnings_score = 70
        elif roa >= 0:
            earnings_score = 55
        else:
            earnings_score = 35
        composite_scores["earnings"] = earnings_score
        
        # --- Liquidity ---
        liq_data = extractions.get("liquidity", {})
        ratios = self._safe_get(liq_data, "liquidity_ratios", default={})
        lcr = ratios.get("lcr_pct", 120)
        
        if lcr >= 150:
            liquidity_score = 95
        elif lcr >= 120:
            liquidity_score = 85
        elif lcr >= 100:
            liquidity_score = 75
        else:
            liquidity_score = 50
        composite_scores["liquidity"] = liquidity_score
        
        # --- Financial Condition Composite ---
        fin_composite = self._weighted_average([
            (cap_score, 0.35),
            (asset_score, 0.15),
            (earnings_score, 0.25),
            (liquidity_score, 0.25)
        ])
        
        signals["financial_condition"] = SignalOutput(
            signal_name="financial_condition",
            categorizer_type="composite_score",
            configuration="financial_condition",
            data={
                "capital_ratio_status": cap_score,
                "asset_size": asset_score,
                "earnings": earnings_score,
                "liquidity": liquidity_score
            },
            source_extractors=["ffiec_call_report", "liquidity"],
            metadata={"composite_score": fin_composite}
        )
        composite_scores["financial_condition"] = fin_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class FICreditQualityAggregator(DataAggregator):
    """
    Aggregates credit quality signals for FI coverage.
    
    Input Extractors:
    - FFIECCallReportExtractor: Asset quality metrics
    - CreditPortfolioExtractor: Portfolio composition
    
    Output Signals:
    - npa_ratio (ThresholdBucket)
    - credit_quality (Composite)
    """
    
    required_extractors = ["ffiec_call_report"]
    optional_extractors = ["credit_portfolio"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        call_data = extractions.get("ffiec_call_report", {})
        entity_id = self._safe_get(call_data, "institution", "rssd_id", default="UNKNOWN")
        
        # --- NPA Ratio ---
        quality = self._safe_get(call_data, "asset_quality", default={})
        npa_ratio = quality.get("npa_ratio_pct", 1.5)
        
        signals["npa_ratio"] = SignalOutput(
            signal_name="npa_ratio",
            categorizer_type="threshold_bucket",
            configuration="npa_ratio",
            data={"value": npa_ratio},
            source_extractors=["ffiec_call_report"]
        )
        
        if npa_ratio <= 0.5:
            npa_score = 100
        elif npa_ratio <= 1.0:
            npa_score = 90
        elif npa_ratio <= 2.0:
            npa_score = 75
        elif npa_ratio <= 3.5:
            npa_score = 55
        else:
            npa_score = 35
        composite_scores["npa_ratio"] = npa_score
        
        # --- Charge-off Ratio ---
        charge_off = quality.get("charge_off_ratio_pct", 0.5)
        
        if charge_off <= 0.25:
            co_score = 100
        elif charge_off <= 0.5:
            co_score = 90
        elif charge_off <= 1.0:
            co_score = 75
        elif charge_off <= 2.0:
            co_score = 55
        else:
            co_score = 35
        composite_scores["charge_off_ratio"] = co_score
        
        # --- Allowance Coverage ---
        allowance = quality.get("allowance_coverage_pct", 150)
        
        if allowance >= 200:
            allowance_score = 95
        elif allowance >= 150:
            allowance_score = 85
        elif allowance >= 100:
            allowance_score = 70
        else:
            allowance_score = 50
        composite_scores["allowance_coverage"] = allowance_score
        
        # --- Concentration Risk ---
        portfolio_data = extractions.get("credit_portfolio", {})
        concentration = self._safe_get(portfolio_data, "concentration", default={})
        cre_to_capital = concentration.get("cre_to_capital_pct", 200)
        
        if cre_to_capital <= 200:
            conc_score = 90
        elif cre_to_capital <= 300:
            conc_score = 75
        elif cre_to_capital <= 400:
            conc_score = 55
        else:
            conc_score = 35
        composite_scores["concentration_risk"] = conc_score
        
        # --- Credit Quality Composite ---
        credit_composite = self._weighted_average([
            (npa_score, 0.35),
            (co_score, 0.25),
            (allowance_score, 0.20),
            (conc_score, 0.20)
        ])
        
        signals["credit_quality"] = SignalOutput(
            signal_name="credit_quality",
            categorizer_type="composite_score",
            configuration="credit_quality",
            data={
                "npa_ratio": npa_score,
                "charge_off_ratio": co_score,
                "allowance_coverage": allowance_score,
                "concentration_risk": conc_score
            },
            source_extractors=["ffiec_call_report", "credit_portfolio"],
            metadata={"composite_score": credit_composite}
        )
        composite_scores["credit_quality"] = credit_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator  
class FIOperationalRiskAggregator(DataAggregator):
    """
    Aggregates operational risk signals for FI coverage.
    
    Input Extractors:
    - FIOperationalRiskExtractor: Incidents, systems, controls
    
    Output Signals:
    - operational_incidents (ScoringLogic)
    - operational_risk (Composite)
    """
    
    required_extractors = ["fi_operational"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        ops_data = extractions.get("fi_operational", {})
        entity_id = self._safe_get(ops_data, "institution_id", default="UNKNOWN")
        
        # --- Operational Incidents ---
        incidents = self._safe_get(ops_data, "operational_incidents", default={})
        total = incidents.get("total_12mo", 0)
        losses = incidents.get("losses_usd", 0)
        
        if total == 0:
            incident_state = "MINIMAL"
            incident_score = 100
        elif total <= 10 and losses < 100000:
            incident_state = "LOW"
            incident_score = 85
        elif total <= 30:
            incident_state = "MODERATE"
            incident_score = 70
        elif total <= 50:
            incident_state = "ELEVATED"
            incident_score = 50
        else:
            incident_state = "HIGH"
            incident_score = 35
        
        signals["operational_incidents"] = SignalOutput(
            signal_name="operational_incidents",
            categorizer_type="scoring_logic",
            configuration="operational_incidents",
            data={"state": incident_state},
            source_extractors=["fi_operational"],
            metadata={"total_incidents": total, "losses_usd": losses}
        )
        composite_scores["operational_incidents"] = incident_score
        
        # --- Systems Resilience ---
        systems = self._safe_get(ops_data, "systems", default={})
        uptime = systems.get("system_uptime_pct", 99.5)
        dr_tested = systems.get("disaster_recovery_tested", False)
        
        if uptime >= 99.9 and dr_tested:
            systems_score = 95
        elif uptime >= 99.5:
            systems_score = 85
        elif uptime >= 99.0:
            systems_score = 70
        else:
            systems_score = 50
        composite_scores["systems_resilience"] = systems_score
        
        # --- Controls ---
        controls = self._safe_get(ops_data, "controls", default={})
        sox_compliant = controls.get("sox_compliant", True)
        deficiencies = controls.get("control_deficiencies_open", 0)
        
        if sox_compliant and deficiencies == 0:
            controls_score = 95
        elif sox_compliant and deficiencies <= 5:
            controls_score = 80
        elif sox_compliant:
            controls_score = 65
        else:
            controls_score = 45
        composite_scores["internal_controls"] = controls_score
        
        # --- Operational Risk Composite ---
        ops_composite = self._weighted_average([
            (incident_score, 0.40),
            (systems_score, 0.30),
            (controls_score, 0.30)
        ])
        
        signals["operational_risk"] = SignalOutput(
            signal_name="operational_risk",
            categorizer_type="composite_score",
            configuration="operational_risk",
            data={
                "operational_incidents": incident_score,
                "systems_resilience": systems_score,
                "internal_controls": controls_score
            },
            source_extractors=["fi_operational"],
            metadata={"composite_score": ops_composite}
        )
        composite_scores["operational_risk"] = ops_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class FICybersecurityAggregator(DataAggregator):
    """
    Aggregates cybersecurity signals for FI coverage.
    
    Input Extractors:
    - FICyberExtractor: FFIEC CAT, security program
    
    Output Signals:
    - cyber_maturity (ScoringLogic)
    - cybersecurity (Composite)
    """
    
    required_extractors = ["fi_cyber"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        cyber_data = extractions.get("fi_cyber", {})
        entity_id = self._safe_get(cyber_data, "institution_id", default="UNKNOWN")
        
        # --- Cyber Maturity ---
        maturity = self._safe_get(cyber_data, "cyber_maturity", default={})
        level = maturity.get("ffiec_cat_level", 2)
        
        maturity_scores = {1: 40, 2: 55, 3: 75, 4: 88, 5: 98}
        mat_score = maturity_scores.get(level, 55)
        
        signals["cyber_maturity"] = SignalOutput(
            signal_name="cyber_maturity",
            categorizer_type="scoring_logic",
            configuration="ffiec_cat_maturity",
            data={"state": f"LEVEL_{level}"},
            source_extractors=["fi_cyber"],
            metadata={"inherent_risk": maturity.get("inherent_risk_profile")}
        )
        composite_scores["cyber_maturity"] = mat_score
        
        # --- Security Program ---
        program = self._safe_get(cyber_data, "security_program", default={})
        has_ciso = program.get("ciso_exists", False)
        training = program.get("security_awareness_training", False)
        pen_test = program.get("pen_test_frequency", "None")
        
        program_score = 50
        if has_ciso:
            program_score += 20
        if training:
            program_score += 15
        if pen_test in ["Continuous", "Quarterly"]:
            program_score += 15
        elif pen_test in ["Semi-Annual", "Annual"]:
            program_score += 10
        composite_scores["security_program"] = min(100, program_score)
        
        # --- Incidents ---
        incidents = self._safe_get(cyber_data, "incidents", default={})
        breaches = incidents.get("breaches_requiring_notification", 0)
        
        if breaches == 0:
            incident_score = 100
        elif breaches == 1:
            incident_score = 60
        else:
            incident_score = 30
        composite_scores["cyber_incidents"] = incident_score
        
        # --- Cybersecurity Composite ---
        cyber_composite = self._weighted_average([
            (mat_score, 0.40),
            (composite_scores["security_program"], 0.35),
            (incident_score, 0.25)
        ])
        
        signals["cybersecurity"] = SignalOutput(
            signal_name="cybersecurity",
            categorizer_type="composite_score",
            configuration="cybersecurity",
            data={
                "cyber_maturity": mat_score,
                "security_program": composite_scores["security_program"],
                "cyber_incidents": incident_score
            },
            source_extractors=["fi_cyber"],
            metadata={"composite_score": cyber_composite}
        )
        composite_scores["cybersecurity"] = cyber_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class FIGovernanceAggregator(DataAggregator):
    """
    Aggregates governance signals for FI coverage.
    
    Input Extractors:
    - FIGovernanceExtractor: Board, committees, risk management
    
    Output Signals:
    - board_oversight (ScoringLogic)
    - governance (Composite)
    """
    
    required_extractors = ["fi_governance"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        gov_data = extractions.get("fi_governance", {})
        entity_id = self._safe_get(gov_data, "institution_id", default="UNKNOWN")
        
        # --- Board Quality ---
        board = self._safe_get(gov_data, "board", default={})
        independence = board.get("independent_pct", 70)
        expertise = board.get("financial_expertise_pct", 50)
        
        if independence >= 75 and expertise >= 50:
            board_state = "STRONG"
            board_score = 95
        elif independence >= 60:
            board_state = "ADEQUATE"
            board_score = 80
        else:
            board_state = "NEEDS_IMPROVEMENT"
            board_score = 60
        
        signals["board_oversight"] = SignalOutput(
            signal_name="board_oversight",
            categorizer_type="scoring_logic",
            configuration="board_oversight",
            data={"state": board_state},
            source_extractors=["fi_governance"],
            metadata={"independence_pct": independence, "expertise_pct": expertise}
        )
        composite_scores["board_oversight"] = board_score
        
        # --- Risk Management ---
        risk_mgmt = self._safe_get(gov_data, "risk_management", default={})
        cro_exists = risk_mgmt.get("cro_exists", False)
        cro_to_board = risk_mgmt.get("cro_reports_to_board", False)
        erm = risk_mgmt.get("erm_framework", "None")
        
        risk_score = 50
        if cro_exists:
            risk_score += 20
        if cro_to_board:
            risk_score += 10
        if erm in ["COSO", "ISO 31000"]:
            risk_score += 20
        composite_scores["risk_management"] = min(100, risk_score)
        
        # --- Audit Function ---
        audit = self._safe_get(gov_data, "audit", default={})
        findings_open = audit.get("audit_findings_open", 0)
        
        if findings_open == 0:
            audit_score = 100
        elif findings_open <= 5:
            audit_score = 85
        elif findings_open <= 15:
            audit_score = 65
        else:
            audit_score = 45
        composite_scores["audit_function"] = audit_score
        
        # --- Governance Composite ---
        gov_composite = self._weighted_average([
            (board_score, 0.35),
            (composite_scores["risk_management"], 0.35),
            (audit_score, 0.30)
        ])
        
        signals["governance"] = SignalOutput(
            signal_name="governance",
            categorizer_type="composite_score",
            configuration="governance",
            data={
                "board_oversight": board_score,
                "risk_management": composite_scores["risk_management"],
                "audit_function": audit_score
            },
            source_extractors=["fi_governance"],
            metadata={"composite_score": gov_composite}
        )
        composite_scores["governance"] = gov_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class FILitigationAggregator(DataAggregator):
    """
    Aggregates litigation signals for FI coverage.
    
    Input Extractors:
    - FILitigationExtractor: Cases, complaints, fines
    
    Output Signals:
    - consumer_complaints (ThresholdBucket)
    - litigation (Composite)
    """
    
    required_extractors = ["fi_litigation"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        lit_data = extractions.get("fi_litigation", {})
        entity_id = self._safe_get(lit_data, "institution_id", default="UNKNOWN")
        
        # --- Consumer Complaints ---
        complaints = self._safe_get(lit_data, "consumer_complaints", default={})
        cfpb = complaints.get("cfpb_complaints_12mo", 100)
        ratio = complaints.get("complaint_ratio_per_bn_deposits", 10)
        
        signals["consumer_complaints"] = SignalOutput(
            signal_name="consumer_complaints",
            categorizer_type="threshold_bucket",
            configuration="consumer_complaints",
            data={"value": ratio},
            source_extractors=["fi_litigation"],
            metadata={"total_complaints": cfpb}
        )
        
        if ratio <= 5:
            complaint_score = 95
        elif ratio <= 15:
            complaint_score = 80
        elif ratio <= 30:
            complaint_score = 65
        else:
            complaint_score = 45
        composite_scores["consumer_complaints"] = complaint_score
        
        # --- Litigation Cases ---
        litigation = self._safe_get(lit_data, "litigation", default={})
        total_cases = litigation.get("total_cases_5yr", 0)
        active = litigation.get("active_cases", 0)
        
        if active == 0:
            case_score = 100
        elif active <= 3:
            case_score = 80
        elif active <= 8:
            case_score = 60
        else:
            case_score = 40
        composite_scores["litigation_cases"] = case_score
        
        # --- Regulatory Fines ---
        fines = self._safe_get(lit_data, "regulatory_fines", "total_fines_5yr_usd", default=0)
        
        if fines == 0:
            fines_score = 100
        elif fines < 1_000_000:
            fines_score = 85
        elif fines < 10_000_000:
            fines_score = 65
        elif fines < 50_000_000:
            fines_score = 45
        else:
            fines_score = 25
        composite_scores["regulatory_fines"] = fines_score
        
        # --- Litigation Composite ---
        lit_composite = self._weighted_average([
            (complaint_score, 0.35),
            (case_score, 0.35),
            (fines_score, 0.30)
        ])
        
        signals["litigation"] = SignalOutput(
            signal_name="litigation",
            categorizer_type="composite_score",
            configuration="litigation",
            data={
                "consumer_complaints": complaint_score,
                "litigation_cases": case_score,
                "regulatory_fines": fines_score
            },
            source_extractors=["fi_litigation"],
            metadata={"composite_score": lit_composite}
        )
        composite_scores["litigation"] = lit_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


# =============================================================================
# ENERGY AGGREGATORS
# =============================================================================

@register_aggregator
class EnergySafetyPerformanceAggregator(DataAggregator):
    """Aggregates safety performance signals for energy coverage."""
    
    required_extractors = ["osha_safety"]
    optional_extractors = ["well_integrity"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        osha_data = extractions.get("osha_safety", {})
        entity_id = self._safe_get(osha_data, "company_id", default="UNKNOWN")
        
        injury = self._safe_get(osha_data, "injury_rates", default={})
        trir = injury.get("trir", 2.0)
        
        signals["trir_benchmark"] = SignalOutput(
            signal_name="trir_benchmark",
            categorizer_type="threshold_bucket",
            configuration="trir",
            data={"value": trir},
            source_extractors=["osha_safety"]
        )
        
        if trir <= 0.5:
            trir_score = 100
        elif trir <= 1.0:
            trir_score = 90
        elif trir <= 2.0:
            trir_score = 75
        else:
            trir_score = 55
        composite_scores["trir"] = trir_score
        
        signals["safety_performance"] = SignalOutput(
            signal_name="safety_performance",
            categorizer_type="composite_score",
            configuration="safety_performance",
            data={"trir": trir_score},
            source_extractors=["osha_safety"],
            metadata={"composite_score": trir_score}
        )
        composite_scores["safety_performance"] = trir_score
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class EnergyEnvironmentalComplianceAggregator(DataAggregator):
    """Aggregates environmental compliance signals for energy coverage."""
    
    required_extractors = ["epa_compliance"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        epa_data = extractions.get("epa_compliance", {})
        entity_id = self._safe_get(epa_data, "company_id", default="UNKNOWN")
        
        violations = self._safe_get(epa_data, "violations", default={})
        total = violations.get("total_3yr", 0)
        
        if total == 0:
            violation_score = 100
        elif total <= 5:
            violation_score = 85
        elif total <= 15:
            violation_score = 65
        else:
            violation_score = 45
        composite_scores["environmental_violations"] = violation_score
        
        signals["environmental_compliance"] = SignalOutput(
            signal_name="environmental_compliance",
            categorizer_type="composite_score",
            configuration="environmental_compliance",
            data={"environmental_violations": violation_score},
            source_extractors=["epa_compliance"],
            metadata={"composite_score": violation_score}
        )
        composite_scores["environmental_compliance"] = violation_score
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class EnergyOperationalQualityAggregator(DataAggregator):
    """Aggregates operational quality signals for energy coverage."""
    
    required_extractors = ["production_data"]
    optional_extractors = ["operations_metrics"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        prod_data = extractions.get("production_data", {})
        entity_id = self._safe_get(prod_data, "company_id", default="UNKNOWN")
        
        production = self._safe_get(prod_data, "production", default={})
        total_boed = production.get("total_boed", 10000)
        
        signals["production_boed"] = SignalOutput(
            signal_name="production_boed",
            categorizer_type="threshold_bucket",
            configuration="production_boed",
            data={"value": total_boed},
            source_extractors=["production_data"]
        )
        
        if total_boed >= 200000:
            scale_score = 85
        elif total_boed >= 50000:
            scale_score = 78
        else:
            scale_score = 70
        composite_scores["production_scale"] = scale_score
        
        signals["operational_quality"] = SignalOutput(
            signal_name="operational_quality",
            categorizer_type="composite_score",
            configuration="operational_quality",
            data={"production_scale": scale_score},
            source_extractors=["production_data"],
            metadata={"composite_score": scale_score}
        )
        composite_scores["operational_quality"] = scale_score
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class EnergyAssetQualityAggregator(DataAggregator):
    """Aggregates asset quality signals for energy coverage."""
    
    required_extractors = ["reserve_data"]
    optional_extractors = ["well_integrity"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        reserve_data = extractions.get("reserve_data", {})
        entity_id = self._safe_get(reserve_data, "company_id", default="UNKNOWN")
        
        metrics = self._safe_get(reserve_data, "reserve_metrics", default={})
        reserve_life = metrics.get("reserve_life_years", 8)
        
        signals["reserve_life"] = SignalOutput(
            signal_name="reserve_life",
            categorizer_type="threshold_bucket",
            configuration="reserve_life",
            data={"value": reserve_life},
            source_extractors=["reserve_data"]
        )
        
        if reserve_life >= 15:
            life_score = 95
        elif reserve_life >= 10:
            life_score = 85
        elif reserve_life >= 7:
            life_score = 75
        else:
            life_score = 60
        composite_scores["reserve_life"] = life_score
        
        signals["asset_quality"] = SignalOutput(
            signal_name="asset_quality",
            categorizer_type="composite_score",
            configuration="asset_quality",
            data={"reserve_life": life_score},
            source_extractors=["reserve_data"],
            metadata={"composite_score": life_score}
        )
        composite_scores["asset_quality"] = life_score
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class EnergyFinancialStabilityAggregator(DataAggregator):
    """Aggregates financial stability signals for energy coverage."""
    
    required_extractors = ["energy_financial"]
    optional_extractors = ["credit_rating"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        fin_data = extractions.get("energy_financial", {})
        entity_id = self._safe_get(fin_data, "company_id", default="UNKNOWN")
        
        leverage = self._safe_get(fin_data, "leverage", default={})
        debt_to_ebitdax = leverage.get("debt_to_ebitdax", 3.0)
        
        if debt_to_ebitdax <= 2.0:
            leverage_score = 95
        elif debt_to_ebitdax <= 3.5:
            leverage_score = 80
        else:
            leverage_score = 60
        composite_scores["leverage"] = leverage_score
        
        signals["financial_stability"] = SignalOutput(
            signal_name="financial_stability",
            categorizer_type="composite_score",
            configuration="financial_stability",
            data={"leverage": leverage_score},
            source_extractors=["energy_financial"],
            metadata={"composite_score": leverage_score}
        )
        composite_scores["financial_stability"] = leverage_score
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class EnergyESGFactorsAggregator(DataAggregator):
    """
    Aggregates ESG factors for energy coverage.
    
    Input Extractors:
    - ESGMetricsExtractor: Emissions, sustainability
    """
    
    required_extractors = ["esg_metrics"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        esg_data = extractions.get("esg_metrics", {})
        entity_id = self._safe_get(esg_data, "company_id", default="UNKNOWN")
        
        # --- Emissions Intensity ---
        emissions = self._safe_get(esg_data, "emissions", default={})
        ghg_intensity = emissions.get("ghg_intensity_kg_co2e_boe", 30)
        methane = emissions.get("methane_intensity_pct", 0.4)
        
        if ghg_intensity <= 20:
            emissions_score = 95
        elif ghg_intensity <= 30:
            emissions_score = 80
        elif ghg_intensity <= 40:
            emissions_score = 65
        else:
            emissions_score = 45
        
        # Methane penalty
        if methane > 0.5:
            emissions_score -= 15
        composite_scores["emissions"] = max(20, emissions_score)
        
        # --- Governance & Disclosure ---
        governance = self._safe_get(esg_data, "governance", default={})
        esg_committee = governance.get("esg_committee", False)
        sustainability_report = governance.get("sustainability_report", False)
        climate_disclosure = governance.get("climate_disclosure", "None")
        
        gov_score = 40
        if esg_committee:
            gov_score += 20
        if sustainability_report:
            gov_score += 20
        if climate_disclosure in ["TCFD", "Both"]:
            gov_score += 20
        elif climate_disclosure == "CDP":
            gov_score += 15
        composite_scores["esg_governance"] = min(100, gov_score)
        
        # --- Targets ---
        targets = self._safe_get(esg_data, "targets", default={})
        net_zero = targets.get("net_zero_commitment", False)
        reduction_target = targets.get("emissions_reduction_target_pct")
        
        if net_zero and reduction_target and reduction_target >= 30:
            targets_score = 95
        elif net_zero:
            targets_score = 80
        elif reduction_target:
            targets_score = 70
        else:
            targets_score = 50
        composite_scores["esg_targets"] = targets_score
        
        # --- ESG Factors Composite ---
        esg_composite = self._weighted_average([
            (composite_scores["emissions"], 0.45),
            (composite_scores["esg_governance"], 0.30),
            (targets_score, 0.25)
        ])
        
        signals["esg_factors"] = SignalOutput(
            signal_name="esg_factors",
            categorizer_type="composite_score",
            configuration="esg_factors",
            data={
                "emissions": composite_scores["emissions"],
                "esg_governance": composite_scores["esg_governance"],
                "esg_targets": targets_score
            },
            source_extractors=["esg_metrics"],
            metadata={"composite_score": esg_composite}
        )
        composite_scores["esg_factors"] = esg_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class EnergyRegulatoryStandingAggregator(DataAggregator):
    """
    Aggregates regulatory standing signals for energy coverage.
    """
    
    required_extractors = ["state_regulatory"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        reg_data = extractions.get("state_regulatory", {})
        entity_id = self._safe_get(reg_data, "company_id", default="UNKNOWN")
        
        # --- State Permit Status ---
        aggregate = self._safe_get(reg_data, "aggregate_status", default={})
        good_standing = aggregate.get("states_good_standing", 0)
        total_states = self._safe_get(reg_data, "operating_states", "count", default=1)
        
        standing_pct = self._safe_divide(good_standing, total_states, 1.0) * 100
        
        if standing_pct >= 100:
            standing_score = 100
        elif standing_pct >= 90:
            standing_score = 85
        elif standing_pct >= 75:
            standing_score = 65
        else:
            standing_score = 45
        composite_scores["permit_status"] = standing_score
        
        # --- Enforcement ---
        enforcement = self._safe_get(reg_data, "enforcement", default={})
        nov = enforcement.get("notices_of_violation_12mo", 0)
        admin_orders = enforcement.get("administrative_orders", 0)
        
        if admin_orders > 0:
            enforcement_score = 35
        elif nov > 10:
            enforcement_score = 50
        elif nov > 5:
            enforcement_score = 70
        elif nov > 0:
            enforcement_score = 85
        else:
            enforcement_score = 100
        composite_scores["enforcement"] = enforcement_score
        
        # --- Regulatory Standing Composite ---
        reg_composite = self._weighted_average([
            (standing_score, 0.55),
            (enforcement_score, 0.45)
        ])
        
        signals["regulatory_standing"] = SignalOutput(
            signal_name="regulatory_standing",
            categorizer_type="composite_score",
            configuration="regulatory_standing",
            data={
                "permit_status": standing_score,
                "enforcement": enforcement_score
            },
            source_extractors=["state_regulatory"],
            metadata={"composite_score": reg_composite}
        )
        composite_scores["regulatory_standing"] = reg_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


# =============================================================================
# PROFESSIONAL INDEMNITY AGGREGATORS
# =============================================================================

@register_aggregator
class PIRegulatoryStandingAggregator(DataAggregator):
    """
    Aggregates regulatory standing signals for PI coverage.
    """
    
    required_extractors = ["state_bar"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        bar_data = extractions.get("state_bar", {})
        entity_id = self._safe_get(bar_data, "entity", "firm_name", default="UNKNOWN")
        
        # --- License Status ---
        status = self._safe_get(bar_data, "license_status", default={})
        license_status = status.get("status", "Unknown")
        
        status_scores = {
            "Active": 100,
            "Inactive": 60,
            "Suspended": 25,
            "Revoked": 5
        }
        license_score = status_scores.get(license_status, 50)
        
        signals["license_status"] = SignalOutput(
            signal_name="license_status",
            categorizer_type="scoring_logic",
            configuration="license_status",
            data={"state": license_status.upper()},
            source_extractors=["state_bar"]
        )
        composite_scores["license_status"] = license_score
        
        # --- Disciplinary History ---
        disciplinary = self._safe_get(bar_data, "disciplinary_history", default={})
        total_actions = disciplinary.get("total_actions", 0)
        serious = disciplinary.get("serious_actions", 0)
        
        if serious > 0:
            disc_score = 25
        elif total_actions > 3:
            disc_score = 50
        elif total_actions > 0:
            disc_score = 75
        else:
            disc_score = 100
        composite_scores["disciplinary_history"] = disc_score
        
        # --- Good Standing ---
        good_standing = self._safe_get(bar_data, "standing", "good_standing", default=True)
        standing_score = 100 if good_standing else 40
        composite_scores["good_standing"] = standing_score
        
        # --- Regulatory Standing Composite ---
        reg_composite = self._weighted_average([
            (license_score, 0.35),
            (disc_score, 0.40),
            (standing_score, 0.25)
        ])
        
        signals["regulatory_standing"] = SignalOutput(
            signal_name="regulatory_standing",
            categorizer_type="composite_score",
            configuration="regulatory_standing",
            data={
                "license_status": license_score,
                "disciplinary_history": disc_score,
                "good_standing": standing_score
            },
            source_extractors=["state_bar"],
            metadata={"composite_score": reg_composite}
        )
        composite_scores["regulatory_standing"] = reg_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class PIClaimsHistoryAggregator(DataAggregator):
    """
    Aggregates claims history signals for PI coverage.
    """
    
    required_extractors = ["malpractice_claims"]
    optional_extractors = ["pi_financial"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        claims_data = extractions.get("malpractice_claims", {})
        entity_id = self._safe_get(claims_data, "entity_id", default="UNKNOWN")
        
        # --- Malpractice Claims ---
        summary = self._safe_get(claims_data, "claims_summary", default={})
        total_claims = summary.get("total_claims_5yr", 0)
        with_payment = summary.get("claims_with_payment", 0)
        
        if total_claims == 0:
            claims_state = "NONE"
            claims_score = 100
        elif total_claims == 1 and with_payment == 0:
            claims_state = "CLAIM_1_NO_PAYMENT"
            claims_score = 90
        elif total_claims == 1:
            claims_state = "CLAIM_1_WITH_PAYMENT"
            claims_score = 75
        elif total_claims <= 3:
            claims_state = "CLAIMS_2_3"
            claims_score = 55
        else:
            claims_state = "CLAIMS_4_PLUS"
            claims_score = 30
        
        signals["malpractice_claims_5yr"] = SignalOutput(
            signal_name="malpractice_claims_5yr",
            categorizer_type="scoring_logic",
            configuration="malpractice_claims_5yr",
            data={"state": claims_state},
            source_extractors=["malpractice_claims"],
            metadata={
                "total_claims": total_claims,
                "claims_with_payment": with_payment,
                "total_paid_usd": summary.get("total_paid_usd", 0)
            }
        )
        composite_scores["malpractice_claims"] = claims_score
        
        # --- Frequency Metrics ---
        frequency = self._safe_get(claims_data, "frequency_metrics", default={})
        claims_per_prof = frequency.get("claims_per_professional", 0)
        
        if claims_per_prof <= 0.05:
            freq_score = 95
        elif claims_per_prof <= 0.10:
            freq_score = 80
        elif claims_per_prof <= 0.20:
            freq_score = 65
        else:
            freq_score = 45
        composite_scores["claims_frequency"] = freq_score
        
        # --- Claims History Composite ---
        claims_composite = self._weighted_average([
            (claims_score, 0.65),
            (freq_score, 0.35)
        ])
        
        signals["claims_history"] = SignalOutput(
            signal_name="claims_history",
            categorizer_type="composite_score",
            configuration="claims_history",
            data={
                "malpractice_claims": claims_score,
                "claims_frequency": freq_score
            },
            source_extractors=["malpractice_claims"],
            metadata={"composite_score": claims_composite}
        )
        composite_scores["claims_history"] = claims_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class PIQualityManagementAggregator(DataAggregator):
    """
    Aggregates quality management signals for PI coverage.
    """
    
    required_extractors = ["quality_management"]
    optional_extractors = ["peer_review"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        qm_data = extractions.get("quality_management", {})
        entity_id = self._safe_get(qm_data, "entity_id", default="UNKNOWN")
        
        # --- QMS Status ---
        qms = self._safe_get(qm_data, "qms", default={})
        has_qms = qms.get("has_documented_qms", False)
        qms_type = qms.get("qms_type", "None")
        
        if has_qms and qms_type in ["ISO-based", "Professional Standard"]:
            qms_score = 95
        elif has_qms:
            qms_score = 75
        else:
            qms_score = 50
        composite_scores["qms_status"] = qms_score
        
        # --- Certifications ---
        certs = self._safe_get(qm_data, "certifications", default=[])
        current_certs = len([c for c in certs if c.get("status") == "Current"])
        
        if current_certs >= 2:
            cert_score = 95
        elif current_certs == 1:
            cert_score = 80
        else:
            cert_score = 60
        composite_scores["certifications"] = cert_score
        
        # --- Peer Review ---
        peer_data = extractions.get("peer_review", {})
        current_status = self._safe_get(peer_data, "current_status", default={})
        rating = current_status.get("most_recent_rating", "Unknown")
        
        rating_scores = {
            "Pass": 100,
            "Pass with Deficiencies": 75,
            "Modified": 55,
            "Fail": 25
        }
        peer_score = rating_scores.get(rating, 60)
        composite_scores["peer_review"] = peer_score
        
        signals["peer_review"] = SignalOutput(
            signal_name="peer_review",
            categorizer_type="scoring_logic",
            configuration="peer_review",
            data={"state": rating.upper().replace(" ", "_")},
            source_extractors=["peer_review"]
        )
        
        # --- Quality Management Composite ---
        qm_composite = self._weighted_average([
            (qms_score, 0.35),
            (cert_score, 0.25),
            (peer_score, 0.40)
        ])
        
        signals["quality_management"] = SignalOutput(
            signal_name="quality_management",
            categorizer_type="composite_score",
            configuration="quality_management",
            data={
                "qms_status": qms_score,
                "certifications": cert_score,
                "peer_review": peer_score
            },
            source_extractors=["quality_management", "peer_review"],
            metadata={"composite_score": qm_composite}
        )
        composite_scores["quality_management"] = qm_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class PIClientQualityAggregator(DataAggregator):
    """
    Aggregates client quality signals for PI coverage.
    """
    
    required_extractors = ["client_quality"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        client_data = extractions.get("client_quality", {})
        entity_id = self._safe_get(client_data, "entity_id", default="UNKNOWN")
        
        # --- Client Concentration ---
        concentration = self._safe_get(client_data, "concentration", default={})
        top_client_pct = concentration.get("top_client_revenue_pct", 15)
        top_10_pct = concentration.get("top_10_clients_revenue_pct", 50)
        
        if top_client_pct <= 10 and top_10_pct <= 40:
            conc_score = 95
        elif top_client_pct <= 20:
            conc_score = 80
        elif top_client_pct <= 30:
            conc_score = 65
        else:
            conc_score = 45
        composite_scores["concentration"] = conc_score
        
        # --- Client Retention ---
        base = self._safe_get(client_data, "client_base", default={})
        retention = base.get("client_retention_pct", 80)
        
        if retention >= 90:
            retention_score = 95
        elif retention >= 80:
            retention_score = 80
        elif retention >= 70:
            retention_score = 65
        else:
            retention_score = 50
        composite_scores["retention"] = retention_score
        
        # --- Client Risk Profile ---
        profile = self._safe_get(client_data, "client_profile", default={})
        high_risk_pct = profile.get("high_risk_clients_pct", 5)
        
        if high_risk_pct <= 5:
            risk_score = 95
        elif high_risk_pct <= 10:
            risk_score = 80
        elif high_risk_pct <= 15:
            risk_score = 65
        else:
            risk_score = 45
        composite_scores["client_risk"] = risk_score
        
        # --- Client Quality Composite ---
        client_composite = self._weighted_average([
            (conc_score, 0.40),
            (retention_score, 0.30),
            (risk_score, 0.30)
        ])
        
        signals["client_quality"] = SignalOutput(
            signal_name="client_quality",
            categorizer_type="composite_score",
            configuration="client_quality",
            data={
                "concentration": conc_score,
                "retention": retention_score,
                "client_risk": risk_score
            },
            source_extractors=["client_quality"],
            metadata={"composite_score": client_composite}
        )
        composite_scores["client_quality"] = client_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class PINetworkAuthorityAggregator(DataAggregator):
    """
    Aggregates network authority signals for PI coverage.
    """
    
    required_extractors = ["network_authority"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        network_data = extractions.get("network_authority", {})
        entity_id = self._safe_get(network_data, "entity_id", default="UNKNOWN")
        
        # --- Panel Memberships ---
        panels = self._safe_get(network_data, "panel_memberships", default={})
        total_panels = panels.get("total_panels", 0)
        primary_panels = panels.get("primary_panels", 0)
        
        if primary_panels >= 3:
            panel_score = 95
        elif primary_panels >= 1:
            panel_score = 85
        elif total_panels >= 3:
            panel_score = 75
        elif total_panels > 0:
            panel_score = 65
        else:
            panel_score = 50
        composite_scores["panel_memberships"] = panel_score
        
        # --- Authority Indicators ---
        authority = self._safe_get(network_data, "authority_indicators", default={})
        ranking = authority.get("ranking", "Emerging")
        chambers = authority.get("chambers_ranking", False)
        
        ranking_scores = {
            "Am Law 100": 95,
            "Am Law 200": 90,
            "Big 4": 95,
            "National": 88,
            "Regional Leader": 82,
            "Regional": 75,
            "Recognized": 70,
            "Local": 65,
            "Emerging": 60
        }
        authority_score = ranking_scores.get(ranking, 65)
        if chambers:
            authority_score = min(100, authority_score + 5)
        composite_scores["authority"] = authority_score
        
        # --- Network Authority Composite ---
        network_composite = self._weighted_average([
            (panel_score, 0.45),
            (authority_score, 0.55)
        ])
        
        signals["network_authority"] = SignalOutput(
            signal_name="network_authority",
            categorizer_type="composite_score",
            configuration="network_authority",
            data={
                "panel_memberships": panel_score,
                "authority": authority_score
            },
            source_extractors=["network_authority"],
            metadata={"composite_score": network_composite}
        )
        composite_scores["network_authority"] = network_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


@register_aggregator
class PIProfessionalDevelopmentAggregator(DataAggregator):
    """
    Aggregates professional development signals for PI coverage.
    """
    
    required_extractors = ["professional_development"]
    optional_extractors = []

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        composite_scores = {}
        
        dev_data = extractions.get("professional_development", {})
        entity_id = self._safe_get(dev_data, "entity_id", default="UNKNOWN")
        
        # --- CPE Compliance ---
        cpe = self._safe_get(dev_data, "cpe_status", default={})
        compliance_pct = cpe.get("compliance_pct", 95)
        
        if compliance_pct >= 99:
            cpe_score = 100
        elif compliance_pct >= 95:
            cpe_score = 90
        elif compliance_pct >= 90:
            cpe_score = 75
        else:
            cpe_score = 55
        composite_scores["cpe_compliance"] = cpe_score
        
        # --- Specializations ---
        specializations = self._safe_get(dev_data, "specializations", default={})
        areas = specializations.get("areas", [])
        board_certified = specializations.get("board_certified_count", 0)
        
        if board_certified >= 3:
            spec_score = 95
        elif board_certified >= 1:
            spec_score = 85
        elif len(areas) >= 3:
            spec_score = 75
        elif len(areas) > 0:
            spec_score = 65
        else:
            spec_score = 55
        composite_scores["specializations"] = spec_score
        
        # --- Training Investment ---
        training = self._safe_get(dev_data, "training", default={})
        internal_hours = training.get("internal_training_hours_avg", 20)
        mentorship = training.get("mentorship_program", False)
        
        training_score = 50
        if internal_hours >= 40:
            training_score += 30
        elif internal_hours >= 20:
            training_score += 20
        if mentorship:
            training_score += 20
        composite_scores["training"] = min(100, training_score)
        
        # --- Professional Development Composite ---
        dev_composite = self._weighted_average([
            (cpe_score, 0.40),
            (spec_score, 0.35),
            (composite_scores["training"], 0.25)
        ])
        
        signals["professional_development"] = SignalOutput(
            signal_name="professional_development",
            categorizer_type="composite_score",
            configuration="professional_development",
            data={
                "cpe_compliance": cpe_score,
                "specializations": spec_score,
                "training": composite_scores["training"]
            },
            source_extractors=["professional_development"],
            metadata={"composite_score": dev_composite}
        )
        composite_scores["professional_development"] = dev_composite
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=entity_id,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            composite_input=composite_scores
        )


# =============================================================================
# ORCHESTRATOR AND FACTORY FUNCTIONS
# =============================================================================

# Coverage to aggregator mapping
COVERAGE_AGGREGATOR_MAP: Dict[str, List[str]] = {
    "marine": [
        "MarineSafetyComplianceAggregator",
        "MarineOperationalTelemetryAggregator",
        "MarineSanctionsComplianceAggregator",
        "MarineFleetQualityAggregator",
        "MarineFinancialStabilityAggregator",
        "MarineClassificationQualityAggregator",
        "MarinePIQualityAggregator",
        "MarineManagementQualityAggregator",
    ],
    "aerospace": [
        "AerospaceSafetyRecordAggregator",
        "AerospaceRegulatoryComplianceAggregator",
        "AerospaceFleetQualityAggregator",
        "AerospaceOperationalQualityAggregator",
        "AerospaceMaintenanceQualityAggregator",
        "AerospaceCrewQualityAggregator",
        "AerospaceFinancialStabilityAggregator",
    ],
    "cyber": [
        "CyberTechnicalInfrastructureAggregator",
        "CyberPublicRecordAggregator",
        "CyberGovernanceAggregator",
        "CyberVendorManagementAggregator",
        "CyberIncidentResponseAggregator",
    ],
    "d_and_o": [
        "DOGovernanceAggregator",
        "DOLitigationAggregator",
        "DOFinancialAggregator",
        "DORegulatoryAggregator",
        "DOPublicCompanyFactorsAggregator",
        "DOIndustryFactorsAggregator",
    ],
    "financial_institutions": [
        "FIRegulatoryComplianceAggregator",
        "FIFinancialConditionAggregator",
        "FICreditQualityAggregator",
        "FIOperationalRiskAggregator",
        "FICybersecurityAggregator",
        "FIGovernanceAggregator",
        "FILitigationAggregator",
    ],
    "energy": [
        "EnergySafetyPerformanceAggregator",
        "EnergyEnvironmentalComplianceAggregator",
        "EnergyOperationalQualityAggregator",
        "EnergyAssetQualityAggregator",
        "EnergyFinancialStabilityAggregator",
        "EnergyESGFactorsAggregator",
        "EnergyRegulatoryStandingAggregator",
    ],
    "professional_indemnity": [
        "PIRegulatoryStandingAggregator",
        "PIClaimsHistoryAggregator",
        "PIQualityManagementAggregator",
        "PIClientQualityAggregator",
        "PINetworkAuthorityAggregator",
        "PIProfessionalDevelopmentAggregator",
    ],
}


def get_aggregator(aggregator_name: str, coverage: str, **kwargs) -> DataAggregator:
    """
    Factory function to instantiate aggregators.
    
    Args:
        aggregator_name: Name of the aggregator class
        coverage: Coverage line (e.g., 'marine', 'cyber')
        **kwargs: Additional arguments passed to aggregator
        
    Returns:
        Instantiated DataAggregator
    """
    aggregator_class = AGGREGATOR_REGISTRY.get(aggregator_name)
    if not aggregator_class:
        available = list(AGGREGATOR_REGISTRY.keys())
        raise ValueError(f"Unknown aggregator '{aggregator_name}'. Available: {available}")
    
    return aggregator_class(coverage=coverage, **kwargs)


def get_aggregators_for_coverage(coverage: str) -> List[DataAggregator]:
    """
    Get all aggregators for a specific coverage line.
    
    Args:
        coverage: Coverage line name
        
    Returns:
        List of instantiated aggregators
    """
    aggregator_names = COVERAGE_AGGREGATOR_MAP.get(coverage, [])
    return [get_aggregator(name, coverage) for name in aggregator_names]


def list_aggregators_by_coverage() -> Dict[str, List[str]]:
    """List all aggregators organized by coverage line."""
    return COVERAGE_AGGREGATOR_MAP.copy()


def list_all_aggregators() -> List[str]:
    """List all registered aggregator names."""
    return list(AGGREGATOR_REGISTRY.keys())


class CoverageAggregationOrchestrator:
    """
    Orchestrates the complete aggregation process for a coverage line.
    
    This class coordinates multiple aggregators to transform raw extraction
    data into a complete set of categorizer-ready signal outputs.
    """
    
    def __init__(self, coverage: str):
        self.coverage = coverage
        self.aggregators = get_aggregators_for_coverage(coverage)
        
        if not self.aggregators:
            raise ValueError(f"No aggregators found for coverage '{coverage}'")
        
        logger.info(f"Initialized orchestrator for {coverage} with {len(self.aggregators)} aggregators")
    
    def aggregate_all(self, extractions: Dict[str, Dict[str, Any]], entity_id: Optional[str] = None) -> AggregationResult:
        """
        Run all aggregators and combine results.
        
        Args:
            extractions: Dict mapping extractor names to their raw_data outputs
            entity_id: Optional entity identifier (auto-detected if not provided)
            
        Returns:
            Combined AggregationResult with all signals
        """
        all_signals: Dict[str, SignalOutput] = {}
        all_composite: Dict[str, float] = {}
        all_errors: List[str] = []
        detected_entity_id = entity_id or "UNKNOWN"
        
        for aggregator in self.aggregators:
            try:
                # Check required extractors
                missing = [e for e in aggregator.required_extractors if e not in extractions]
                if missing:
                    logger.warning(f"{aggregator.__class__.__name__} missing required extractors: {missing}")
                    all_errors.append(f"{aggregator.__class__.__name__}: Missing {missing}")
                    continue
                
                # Run aggregation
                result = aggregator.aggregate(extractions)
                
                # Merge results
                all_signals.update(result.signals)
                all_composite.update(result.composite_input)
                all_errors.extend(result.errors)
                
                # Use first valid entity_id
                if detected_entity_id == "UNKNOWN" and result.entity_id != "UNKNOWN":
                    detected_entity_id = result.entity_id
                
                logger.debug(f"{aggregator.__class__.__name__} produced {len(result.signals)} signals")
                
            except Exception as e:
                logger.exception(f"Error in {aggregator.__class__.__name__}: {e}")
                all_errors.append(f"{aggregator.__class__.__name__}: {str(e)}")
        
        return AggregationResult(
            coverage=self.coverage,
            entity_id=detected_entity_id,
            timestamp=datetime.now().isoformat(),
            signals=all_signals,
            composite_input=all_composite,
            errors=all_errors,
            metadata={
                "aggregators_run": len(self.aggregators),
                "signals_produced": len(all_signals),
                "errors_count": len(all_errors)
            }
        )
    
    def get_required_extractors(self) -> List[str]:
        """Get list of all required extractors for this coverage."""
        required = set()
        for aggregator in self.aggregators:
            required.update(aggregator.required_extractors)
        return sorted(list(required))
    
    def get_optional_extractors(self) -> List[str]:
        """Get list of all optional extractors for this coverage."""
        optional = set()
        for aggregator in self.aggregators:
            optional.update(aggregator.optional_extractors)
        return sorted(list(optional))


# =============================================================================
# DEMO AND TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("AGGREGATORS MODULE - DEMONSTRATION")
    print("=" * 80)
    
    # List aggregators by coverage
    print("\n--- Aggregators by Coverage ---")
    for coverage, aggregators in COVERAGE_AGGREGATOR_MAP.items():
        print(f"\n{coverage.upper()}: {len(aggregators)} aggregators")
        for agg in aggregators:
            agg_instance = get_aggregator(agg, coverage)
            print(f"  - {agg}")
            print(f"      Required: {agg_instance.required_extractors}")
            if agg_instance.optional_extractors:
                print(f"      Optional: {agg_instance.optional_extractors}")
    
    # Total count
    total = sum(len(aggs) for aggs in COVERAGE_AGGREGATOR_MAP.values())
    print(f"\n{'='*80}")
    print(f"TOTAL: {total} aggregators across {len(COVERAGE_AGGREGATOR_MAP)} coverage lines")
    print(f"{'='*80}")
    
    # Demo with sample data
    print("\n--- Sample Aggregation (Marine) ---")
    
    # Simulate extraction data
    sample_extractions = {
        "psc_inspection": {
            "vessel_imo": "9876543",
            "inspection_summary": {
                "total_inspections_3yr": 8,
                "total_deficiencies_3yr": 12,
                "total_detentions_3yr": 0,
                "deficiency_ratio": 1.5
            }
        },
        "classification_society": {
            "vessel_imo": "9876543",
            "classification": {
                "society_name": "DNV",
                "class_status": "In Class"
            },
            "conditions_of_class": {
                "total": 1,
                "outstanding": 1,
                "overdue": 0
            },
            "survey_history": {
                "compliance_rate": 0.95
            }
        },
        "ism_compliance": {
            "company_id": "IMO1234567",
            "doc_status": {"status": "Valid"},
            "audit_history": {
                "total_audits_3yr": 3,
                "total_findings": 5,
                "major_nonconformities": 0
            },
            "sms_status": {
                "documented": True,
                "drills_conducted_12mo": 18
            }
        },
        "equasis_operator": {
            "company": {
                "imo_company_number": "IMO1234567",
                "company_name": "Demo Shipping Ltd"
            },
            "fleet": {
                "total_vessels": 25,
                "average_age": 12.5,
                "vessels": [
                    {"vessel_type": "Container Ship", "age": 10},
                    {"vessel_type": "Container Ship", "age": 12},
                    {"vessel_type": "Bulk Carrier", "age": 15},
                ]
            }
        },
        "ais_tracking": {
            "vessel_imo": "9876543",
            "port_calls": {"total_12mo": 28, "unique_countries": 12},
            "ais_gaps": {"total_gaps_12mo": 1, "high_risk_gaps": 0, "gaps": []},
            "sts_events": {"total_12mo": 0},
            "sanctions_exposure": {"sanctioned_area_visit": False, "high_risk_area_transits": 1}
        },
        "sanctions_screening": {
            "entity_id": "IMO1234567",
            "screening_result": {"status": "CLEAR", "total_hits": 0, "hits": []},
            "ownership_flags": {"high_risk_jurisdiction": False, "complex_structure": False}
        },
        "flag_state_performance": {
            "flag_state": "Singapore",
            "paris_mou_status": {"list_color": "WHITE", "detention_rate_pct": 1.2}
        },
        "marine_financial": {
            "company_id": "IMO1234567",
            "ratios": {"debt_to_ebitda": 3.2, "interest_coverage": 3.5}
        },
        "pi_club": {
            "company_id": "IMO1234567",
            "membership": {"club_name": "Gard", "club_type": "International Group"},
            "claims_history": {"total_claims_5yr": 2, "total_incurred_usd": 350000}
        }
    }
    
    # Run orchestrator
    orchestrator = CoverageAggregationOrchestrator("marine")
    print(f"\nRequired extractors: {orchestrator.get_required_extractors()}")
    
    result = orchestrator.aggregate_all(sample_extractions)
    
    print(f"\nAggregation Result:")
    print(f"  Entity ID: {result.entity_id}")
    print(f"  Signals produced: {len(result.signals)}")
    print(f"  Errors: {len(result.errors)}")
    
    print(f"\n--- Signal Outputs ---")
    for signal_name, signal in sorted(result.signals.items()):
        print(f"\n{signal_name}:")
        print(f"  Type: {signal.categorizer_type}")
        print(f"  Config: {signal.configuration}")
        print(f"  Data: {signal.data}")
        if signal.metadata:
            print(f"  Metadata: {signal.metadata}")
    
    print(f"\n--- Composite Scores ---")
    for name, score in sorted(result.composite_input.items()):
        print(f"  {name}: {score:.1f}")
