"""
Digital Signal Intelligence - Marine Insurance Pricing Model
=============================================================

This module implements DSI-based pricing for Marine insurance, covering:
- Hull & Machinery (H&M)
- Cargo
- Protection & Indemnity (P&I)
- Marine Liability

Marine insurance presents unique DSI opportunities because vessel operations
generate extensive digital footprints through AIS tracking, port state control
databases, classification society records, and regulatory filings.

Signal Categories:
1. Vessel Operations (AIS patterns, port calls, trading routes)
2. Safety & Compliance (PSC detentions, class status, ISM compliance)
3. Fleet Management (operator reputation, technical management)
4. Financial Stability (owner/operator financials, sanctions exposure)
5. Environmental (emissions compliance, environmental incidents)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import json


class VesselType(Enum):
    """Marine vessel classifications"""
    CONTAINER = "container"
    BULK_CARRIER = "bulk_carrier"
    TANKER_CRUDE = "tanker_crude"
    TANKER_PRODUCT = "tanker_product"
    TANKER_CHEMICAL = "tanker_chemical"
    LNG_CARRIER = "lng_carrier"
    LPG_CARRIER = "lpg_carrier"
    RORO = "roro"
    GENERAL_CARGO = "general_cargo"
    OFFSHORE = "offshore"
    PASSENGER = "passenger"
    FISHING = "fishing"


class CoverageType(Enum):
    """Marine coverage types"""
    HULL_MACHINERY = "hull_machinery"
    CARGO = "cargo"
    PI = "protection_indemnity"
    MARINE_LIABILITY = "marine_liability"
    WAR_RISKS = "war_risks"
    LOSS_OF_HIRE = "loss_of_hire"


class TradingArea(Enum):
    """Geographic trading areas with risk profiles"""
    WORLDWIDE = "worldwide"
    WORLDWIDE_EXC_WAR = "worldwide_excluding_war_zones"
    NORTH_ATLANTIC = "north_atlantic"
    MEDITERRANEAN = "mediterranean"
    ASIA_PACIFIC = "asia_pacific"
    MIDDLE_EAST_GULF = "middle_east_gulf"
    WEST_AFRICA = "west_africa"
    CARIBBEAN = "caribbean"
    INLAND_WATERS = "inland_waters"


@dataclass
class MarineSignal:
    """Individual marine risk signal"""
    signal_name: str
    raw_value: any
    normalized_score: float  # 0-100
    weight: float
    evidence: str
    data_source: str
    observation_date: datetime
    confidence: float = 1.0


@dataclass 
class VesselProfile:
    """Vessel information for underwriting"""
    imo_number: str
    vessel_name: str
    vessel_type: VesselType
    flag_state: str
    gross_tonnage: int
    deadweight: int
    year_built: int
    classification_society: str
    owner: str
    operator: str
    technical_manager: str
    insured_value: float
    trading_area: TradingArea


@dataclass
class MarineSubmission:
    """Complete marine insurance submission"""
    submission_id: str
    vessel: VesselProfile
    coverage_types: List[CoverageType]
    policy_period_start: datetime
    policy_period_end: datetime
    deductible: float
    limit: float
    broker: str
    previous_insurer: Optional[str] = None
    claims_history: List[Dict] = field(default_factory=list)


class MarineSignalScorer:
    """
    Scores marine-specific digital signals from various data sources.
    
    Data Sources:
    - AIS (Automatic Identification System) tracking data
    - Equasis (vessel/company database)
    - Paris MoU / Tokyo MoU (Port State Control)
    - Classification society records
    - IMO GISIS (Global Integrated Shipping Information System)
    - Sanctions screening databases
    - Maritime news and incident databases
    """
    
    # Signal weights for marine insurance
    SIGNAL_WEIGHTS = {
        # Vessel Operations (25%)
        "ais_compliance": 0.08,
        "trading_pattern_risk": 0.08,
        "port_call_risk": 0.05,
        "dark_activity": 0.04,
        
        # Safety & Compliance (30%)
        "psc_performance": 0.10,
        "class_status": 0.08,
        "ism_compliance": 0.06,
        "vessel_age_condition": 0.06,
        
        # Fleet/Operator (20%)
        "operator_reputation": 0.08,
        "technical_manager_quality": 0.06,
        "fleet_performance": 0.06,
        
        # Financial & Sanctions (15%)
        "owner_financial_stability": 0.06,
        "sanctions_exposure": 0.05,
        "beneficial_owner_transparency": 0.04,
        
        # Environmental (10%)
        "environmental_compliance": 0.05,
        "emissions_performance": 0.03,
        "environmental_incidents": 0.02,
    }
    
    # Flag state risk tiers
    FLAG_STATE_TIERS = {
        "tier_1": ["GB", "NO", "DK", "NL", "DE", "FR", "SG", "JP", "HK", "AU"],  # White list
        "tier_2": ["MT", "CY", "GR", "IT", "US", "CA", "KR", "TW"],  # Generally acceptable
        "tier_3": ["LR", "MH", "PA", "BS"],  # Open registries - scrutiny needed
        "tier_4": ["KH", "TZ", "TG", "CM"],  # High risk flags
    }
    
    # Classification society tiers
    CLASS_SOCIETY_TIERS = {
        "iacs": ["LR", "DNV", "BV", "ABS", "NK", "KR", "CCS", "RINA", "RS", "CRS", "IRS", "PRS"],
        "recognized": ["IRCLASS", "VR", "HR"],
        "other": []  # Anything else requires scrutiny
    }
    
    def __init__(self):
        self.signals: Dict[str, MarineSignal] = {}
    
    def score_ais_compliance(self, ais_data: Dict) -> MarineSignal:
        """
        Score AIS transmission compliance and patterns.
        
        Vessels are required to transmit AIS continuously. Gaps or manipulation
        indicate potential regulatory evasion or illicit activity.
        
        Scoring:
        - 95-100: Continuous transmission, no gaps > 1 hour
        - 80-94: Minor gaps (1-4 hours), explainable
        - 60-79: Moderate gaps (4-24 hours)
        - 40-59: Significant gaps (24-72 hours)
        - 0-39: Extended dark periods or manipulation detected
        """
        gaps = ais_data.get("transmission_gaps", [])
        max_gap_hours = max([g.get("duration_hours", 0) for g in gaps]) if gaps else 0
        total_gap_hours = sum([g.get("duration_hours", 0) for g in gaps])
        manipulation_detected = ais_data.get("manipulation_indicators", False)
        
        if manipulation_detected:
            score = 15
            evidence = "AIS manipulation indicators detected"
        elif max_gap_hours > 72:
            score = 25
            evidence = f"Extended AIS dark period: {max_gap_hours:.0f} hours"
        elif max_gap_hours > 24:
            score = 45
            evidence = f"Significant AIS gaps detected: max {max_gap_hours:.0f} hours"
        elif max_gap_hours > 4:
            score = 65
            evidence = f"Moderate AIS gaps: {total_gap_hours:.1f} total hours"
        elif max_gap_hours > 1:
            score = 85
            evidence = f"Minor AIS gaps: {total_gap_hours:.1f} total hours"
        else:
            score = 98
            evidence = "Continuous AIS transmission, fully compliant"
        
        return MarineSignal(
            signal_name="ais_compliance",
            raw_value={"max_gap": max_gap_hours, "total_gaps": total_gap_hours},
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["ais_compliance"],
            evidence=evidence,
            data_source="AIS_TRACKING",
            observation_date=datetime.now()
        )
    
    def score_dark_activity(self, ais_data: Dict, vessel: VesselProfile) -> MarineSignal:
        """
        Score vessel dark activity patterns.
        
        "Going dark" (disabling AIS) near certain locations or during
        ship-to-ship transfers is a major red flag for sanctions evasion,
        illegal fishing, or smuggling.
        
        High-risk dark zones:
        - Near sanctioned country waters (NK, Iran, Syria, Russia)
        - Known STS transfer areas
        - Unregulated fishing zones
        """
        dark_events = ais_data.get("dark_events", [])
        high_risk_dark = 0
        moderate_risk_dark = 0
        
        high_risk_zones = ["NK_EEZ", "IRAN_WATERS", "SYRIA_WATERS", "CRIMEA", "STS_HOTSPOT"]
        
        for event in dark_events:
            if event.get("last_known_zone") in high_risk_zones:
                high_risk_dark += 1
            elif event.get("duration_hours", 0) > 12:
                moderate_risk_dark += 1
        
        if high_risk_dark > 0:
            score = 10
            evidence = f"CRITICAL: {high_risk_dark} dark events near high-risk zones"
        elif moderate_risk_dark > 2:
            score = 35
            evidence = f"Multiple extended dark periods: {moderate_risk_dark} events"
        elif moderate_risk_dark > 0:
            score = 55
            evidence = f"Some extended dark periods detected"
        elif len(dark_events) > 0:
            score = 75
            evidence = f"Minor dark events: {len(dark_events)} total"
        else:
            score = 95
            evidence = "No suspicious dark activity detected"
        
        return MarineSignal(
            signal_name="dark_activity",
            raw_value={"high_risk": high_risk_dark, "moderate_risk": moderate_risk_dark},
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["dark_activity"],
            evidence=evidence,
            data_source="AIS_TRACKING",
            observation_date=datetime.now()
        )
    
    def score_psc_performance(self, psc_data: Dict) -> MarineSignal:
        """
        Score Port State Control inspection performance.
        
        PSC inspections are conducted by port authorities worldwide.
        Detentions and deficiencies are strong predictors of vessel condition.
        
        Key metrics:
        - Detention ratio (detentions / inspections)
        - Deficiency rate (deficiencies per inspection)
        - Deficiency types (safety-critical vs administrative)
        - Trend (improving or deteriorating)
        """
        inspections = psc_data.get("inspections_36_months", 0)
        detentions = psc_data.get("detentions_36_months", 0)
        deficiencies = psc_data.get("deficiencies_36_months", 0)
        safety_critical = psc_data.get("safety_critical_deficiencies", 0)
        
        if inspections == 0:
            # No inspection record - could be new vessel or limited trading
            return MarineSignal(
                signal_name="psc_performance",
                raw_value=psc_data,
                normalized_score=60,
                weight=self.SIGNAL_WEIGHTS["psc_performance"],
                evidence="No PSC inspection history available",
                data_source="PARIS_MOU_TOKYO_MOU",
                observation_date=datetime.now(),
                confidence=0.5
            )
        
        detention_ratio = detentions / inspections
        deficiency_rate = deficiencies / inspections
        
        # Scoring matrix
        if detention_ratio > 0.3 or safety_critical > 2:
            score = 15
            evidence = f"CRITICAL: {detentions} detentions in {inspections} inspections, {safety_critical} safety-critical"
        elif detention_ratio > 0.15:
            score = 35
            evidence = f"Poor PSC record: {detention_ratio:.0%} detention rate"
        elif detention_ratio > 0.05:
            score = 55
            evidence = f"Below average PSC: {detention_ratio:.0%} detention rate, {deficiency_rate:.1f} deficiencies/inspection"
        elif deficiency_rate > 3:
            score = 65
            evidence = f"Elevated deficiencies: {deficiency_rate:.1f} per inspection"
        elif deficiency_rate > 1.5:
            score = 78
            evidence = f"Acceptable PSC record: {deficiency_rate:.1f} deficiencies/inspection"
        elif detentions == 0 and deficiency_rate < 1:
            score = 95
            evidence = f"Excellent PSC record: No detentions, {deficiency_rate:.1f} deficiencies/inspection"
        else:
            score = 85
            evidence = f"Good PSC record: {detentions} detentions, {deficiency_rate:.1f} deficiencies/inspection"
        
        return MarineSignal(
            signal_name="psc_performance",
            raw_value=psc_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["psc_performance"],
            evidence=evidence,
            data_source="PARIS_MOU_TOKYO_MOU",
            observation_date=datetime.now()
        )
    
    def score_class_status(self, class_data: Dict, vessel: VesselProfile) -> MarineSignal:
        """
        Score classification society status.
        
        Classification societies survey vessels and certify seaworthiness.
        Key signals:
        - IACS member vs non-IACS
        - Class status (in class, suspended, withdrawn)
        - Outstanding recommendations
        - Survey status (overdue, completed)
        - Class changes (flag of convenience indicator)
        """
        society = class_data.get("society", "")
        status = class_data.get("status", "unknown")
        outstanding_recs = class_data.get("outstanding_recommendations", 0)
        conditions_of_class = class_data.get("conditions_of_class", 0)
        survey_overdue = class_data.get("survey_overdue", False)
        class_changes_5yr = class_data.get("class_changes_5_years", 0)
        
        # Determine society tier
        if society in self.CLASS_SOCIETY_TIERS["iacs"]:
            society_score = 100
        elif society in self.CLASS_SOCIETY_TIERS["recognized"]:
            society_score = 75
        else:
            society_score = 40
        
        # Status scoring
        if status == "withdrawn" or status == "suspended":
            score = 5
            evidence = f"CRITICAL: Class {status} - vessel not classed"
        elif survey_overdue:
            score = 25
            evidence = f"Class survey overdue - potential unseaworthiness"
        elif conditions_of_class > 2:
            score = 40
            evidence = f"Multiple conditions of class: {conditions_of_class} outstanding"
        elif outstanding_recs > 5:
            score = 50
            evidence = f"Elevated recommendations: {outstanding_recs} outstanding"
        elif class_changes_5yr > 2:
            score = 55
            evidence = f"Frequent class changes: {class_changes_5yr} in 5 years (flag shopping indicator)"
        elif outstanding_recs > 2:
            score = 70
            evidence = f"Some recommendations outstanding: {outstanding_recs}"
        elif society_score < 75:
            score = 60
            evidence = f"Non-IACS classification society: {society}"
        else:
            base_score = society_score - (outstanding_recs * 3) - (conditions_of_class * 10)
            score = max(base_score, 50)
            evidence = f"In class with {society}, {outstanding_recs} recommendations"
        
        return MarineSignal(
            signal_name="class_status",
            raw_value=class_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["class_status"],
            evidence=evidence,
            data_source="CLASSIFICATION_SOCIETY",
            observation_date=datetime.now()
        )
    
    def score_vessel_age_condition(self, vessel: VesselProfile, condition_data: Dict) -> MarineSignal:
        """
        Score vessel age and condition indicators.
        
        Age alone is not determinative - a well-maintained 20-year vessel
        may be better than a neglected 5-year vessel. DSI combines age with
        maintenance signals.
        """
        current_year = datetime.now().year
        age = current_year - vessel.year_built
        
        # Condition indicators
        dry_dock_overdue = condition_data.get("dry_dock_overdue", False)
        major_repairs_pending = condition_data.get("major_repairs_pending", 0)
        machinery_issues = condition_data.get("machinery_failures_12m", 0)
        
        # Age-based baseline
        if age <= 5:
            age_score = 95
        elif age <= 10:
            age_score = 85
        elif age <= 15:
            age_score = 72
        elif age <= 20:
            age_score = 58
        elif age <= 25:
            age_score = 42
        else:
            age_score = 25
        
        # Condition adjustments
        condition_penalty = 0
        if dry_dock_overdue:
            condition_penalty += 25
        condition_penalty += major_repairs_pending * 10
        condition_penalty += machinery_issues * 8
        
        score = max(age_score - condition_penalty, 10)
        
        evidence_parts = [f"Vessel age: {age} years"]
        if dry_dock_overdue:
            evidence_parts.append("dry dock overdue")
        if major_repairs_pending:
            evidence_parts.append(f"{major_repairs_pending} major repairs pending")
        if machinery_issues:
            evidence_parts.append(f"{machinery_issues} machinery failures in 12m")
        
        return MarineSignal(
            signal_name="vessel_age_condition",
            raw_value={"age": age, "condition": condition_data},
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["vessel_age_condition"],
            evidence="; ".join(evidence_parts),
            data_source="EQUASIS_CLASS_RECORDS",
            observation_date=datetime.now()
        )
    
    def score_operator_reputation(self, operator_data: Dict) -> MarineSignal:
        """
        Score ship operator/manager reputation.
        
        The DOC (Document of Compliance) holder is often more important
        than the vessel itself. DSI tracks operator performance across
        their entire fleet.
        """
        fleet_size = operator_data.get("fleet_size", 1)
        fleet_detention_rate = operator_data.get("fleet_detention_rate_36m", 0)
        total_losses = operator_data.get("total_losses_5yr", 0)
        major_incidents = operator_data.get("major_incidents_5yr", 0)
        years_operating = operator_data.get("years_in_operation", 0)
        
        # Small fleet penalty (less data, higher uncertainty)
        if fleet_size < 3:
            size_factor = 0.85
        elif fleet_size < 10:
            size_factor = 0.95
        else:
            size_factor = 1.0
        
        # Experience factor
        if years_operating < 3:
            experience_factor = 0.80
        elif years_operating < 10:
            experience_factor = 0.95
        else:
            experience_factor = 1.0
        
        # Performance scoring
        if total_losses > 0:
            score = 20
            evidence = f"CRITICAL: {total_losses} total losses in 5 years"
        elif major_incidents > 2:
            score = 35
            evidence = f"Multiple major incidents: {major_incidents} in 5 years"
        elif fleet_detention_rate > 0.15:
            score = 40
            evidence = f"Poor fleet performance: {fleet_detention_rate:.0%} detention rate"
        elif fleet_detention_rate > 0.08:
            score = 55
            evidence = f"Below average fleet: {fleet_detention_rate:.0%} detention rate"
        elif major_incidents > 0:
            score = 65
            evidence = f"Some incidents: {major_incidents} major in 5 years"
        elif fleet_detention_rate > 0.03:
            score = 78
            evidence = f"Acceptable fleet performance: {fleet_detention_rate:.0%} detention rate"
        else:
            score = 92
            evidence = f"Excellent operator: {fleet_size} vessels, {fleet_detention_rate:.1%} detention rate"
        
        score = score * size_factor * experience_factor
        
        return MarineSignal(
            signal_name="operator_reputation",
            raw_value=operator_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["operator_reputation"],
            evidence=evidence,
            data_source="EQUASIS_FLEET_DATA",
            observation_date=datetime.now()
        )
    
    def score_sanctions_exposure(self, sanctions_data: Dict, vessel: VesselProfile) -> MarineSignal:
        """
        Score sanctions and compliance risk.
        
        Sanctions exposure is binary in terms of coverage (sanctioned = no cover)
        but DSI identifies elevated risk indicators:
        - Trading patterns near sanctioned regions
        - Ownership opacity
        - Historical sanctions connections
        - STS transfers with flagged vessels
        """
        direct_sanctions = sanctions_data.get("direct_sanctions", False)
        owner_sanctions = sanctions_data.get("owner_sanctioned", False)
        sts_with_sanctioned = sanctions_data.get("sts_with_sanctioned_vessels", 0)
        high_risk_port_calls = sanctions_data.get("high_risk_port_calls_12m", 0)
        ownership_opacity = sanctions_data.get("ownership_layers", 0)
        
        if direct_sanctions or owner_sanctions:
            score = 0
            evidence = "SANCTIONED - Coverage not available"
        elif sts_with_sanctioned > 0:
            score = 10
            evidence = f"CRITICAL: {sts_with_sanctioned} STS transfers with sanctioned vessels"
        elif high_risk_port_calls > 3:
            score = 25
            evidence = f"Elevated sanctions risk: {high_risk_port_calls} high-risk port calls"
        elif ownership_opacity > 4:
            score = 40
            evidence = f"Opaque ownership: {ownership_opacity} layers - sanctions evasion risk"
        elif high_risk_port_calls > 0:
            score = 60
            evidence = f"Some high-risk exposure: {high_risk_port_calls} port calls"
        elif ownership_opacity > 2:
            score = 75
            evidence = f"Complex ownership: {ownership_opacity} layers"
        else:
            score = 95
            evidence = "Clean sanctions profile, transparent ownership"
        
        return MarineSignal(
            signal_name="sanctions_exposure",
            raw_value=sanctions_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["sanctions_exposure"],
            evidence=evidence,
            data_source="SANCTIONS_SCREENING",
            observation_date=datetime.now()
        )
    
    def score_environmental_compliance(self, environmental_data: Dict, vessel: VesselProfile) -> MarineSignal:
        """
        Score environmental compliance and incidents.
        
        Environmental signals include:
        - IMO 2020 sulphur compliance
        - Ballast water management
        - Environmental incidents/fines
        - EEDI/CII ratings
        """
        imo2020_compliant = environmental_data.get("imo2020_compliant", True)
        bwm_compliant = environmental_data.get("ballast_water_compliant", True)
        environmental_fines = environmental_data.get("environmental_fines_5yr", 0)
        oil_spills = environmental_data.get("oil_spills_5yr", 0)
        cii_rating = environmental_data.get("cii_rating", "C")
        
        if oil_spills > 0:
            score = 20
            evidence = f"CRITICAL: {oil_spills} oil spill incidents in 5 years"
        elif not imo2020_compliant:
            score = 30
            evidence = "Non-compliant with IMO 2020 sulphur regulations"
        elif environmental_fines > 2:
            score = 40
            evidence = f"Multiple environmental fines: {environmental_fines} in 5 years"
        elif not bwm_compliant:
            score = 50
            evidence = "Ballast water management non-compliant"
        elif cii_rating in ["D", "E"]:
            score = 55
            evidence = f"Poor CII rating: {cii_rating}"
        elif environmental_fines > 0:
            score = 65
            evidence = f"Some environmental issues: {environmental_fines} fines"
        elif cii_rating == "C":
            score = 78
            evidence = f"Acceptable environmental profile, CII: {cii_rating}"
        else:
            score = 92
            evidence = f"Strong environmental compliance, CII: {cii_rating}"
        
        return MarineSignal(
            signal_name="environmental_compliance",
            raw_value=environmental_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["environmental_compliance"],
            evidence=evidence,
            data_source="IMO_GISIS_ENVIRONMENTAL",
            observation_date=datetime.now()
        )


class MarinePricingModel:
    """
    DSI-based marine insurance pricing model.
    
    Combines digital signals with traditional marine underwriting factors
    to produce risk-adjusted pricing.
    """
    
    # Base rates by vessel type (per $100 of insured value, annual)
    BASE_RATES = {
        VesselType.CONTAINER: 0.18,
        VesselType.BULK_CARRIER: 0.20,
        VesselType.TANKER_CRUDE: 0.25,
        VesselType.TANKER_PRODUCT: 0.22,
        VesselType.TANKER_CHEMICAL: 0.28,
        VesselType.LNG_CARRIER: 0.15,
        VesselType.LPG_CARRIER: 0.18,
        VesselType.RORO: 0.30,
        VesselType.GENERAL_CARGO: 0.22,
        VesselType.OFFSHORE: 0.35,
        VesselType.PASSENGER: 0.40,
        VesselType.FISHING: 0.45,
    }
    
    # Trading area multipliers
    TRADING_MULTIPLIERS = {
        TradingArea.WORLDWIDE: 1.20,
        TradingArea.WORLDWIDE_EXC_WAR: 1.00,
        TradingArea.NORTH_ATLANTIC: 0.95,
        TradingArea.MEDITERRANEAN: 0.90,
        TradingArea.ASIA_PACIFIC: 1.00,
        TradingArea.MIDDLE_EAST_GULF: 1.15,
        TradingArea.WEST_AFRICA: 1.25,
        TradingArea.CARIBBEAN: 1.10,
        TradingArea.INLAND_WATERS: 0.85,
    }
    
    # DSI tier pricing adjustments
    TIER_ADJUSTMENTS = {
        1: 0.75,   # Preferred: 25% discount
        2: 1.00,   # Standard: no adjustment
        3: 1.35,   # Elevated: 35% surcharge
        4: 2.00,   # High Risk: 100% surcharge (if bound at all)
    }
    
    def __init__(self):
        self.signal_scorer = MarineSignalScorer()
    
    def calculate_composite_score(self, signals: Dict[str, MarineSignal]) -> Tuple[float, float]:
        """
        Calculate weighted composite DSI score.
        
        Returns:
            Tuple of (composite_score 0-1000, confidence 0-1)
        """
        weighted_sum = 0
        weight_sum = 0
        confidence_sum = 0
        
        for signal_name, signal in signals.items():
            weighted_sum += signal.normalized_score * signal.weight * signal.confidence
            weight_sum += signal.weight
            confidence_sum += signal.confidence * signal.weight
        
        if weight_sum > 0:
            raw_score = weighted_sum / weight_sum
            composite = raw_score * 10  # Scale to 0-1000
            confidence = confidence_sum / weight_sum
        else:
            composite = 500
            confidence = 0.5
        
        return composite, confidence
    
    def determine_tier(self, composite_score: float) -> int:
        """Determine risk tier from composite score"""
        if composite_score >= 750:
            return 1
        elif composite_score >= 600:
            return 2
        elif composite_score >= 450:
            return 3
        else:
            return 4
    
    def calculate_premium(
        self,
        submission: MarineSubmission,
        signals: Dict[str, MarineSignal],
        composite_score: float
    ) -> Dict:
        """
        Calculate risk-adjusted premium.
        
        Returns complete pricing breakdown.
        """
        vessel = submission.vessel
        
        # Base premium
        base_rate = self.BASE_RATES.get(vessel.vessel_type, 0.25)
        base_premium = (vessel.insured_value / 100) * base_rate
        
        # Trading area adjustment
        trading_mult = self.TRADING_MULTIPLIERS.get(vessel.trading_area, 1.0)
        
        # DSI tier adjustment
        tier = self.determine_tier(composite_score)
        dsi_mult = self.TIER_ADJUSTMENTS[tier]
        
        # Age loading
        age = datetime.now().year - vessel.year_built
        if age > 20:
            age_mult = 1.40
        elif age > 15:
            age_mult = 1.20
        elif age > 10:
            age_mult = 1.10
        else:
            age_mult = 1.00
        
        # Calculate final premium
        adjusted_premium = base_premium * trading_mult * dsi_mult * age_mult
        
        # Minimum premium
        minimum_premium = 25000
        final_premium = max(adjusted_premium, minimum_premium)
        
        return {
            "base_premium": base_premium,
            "trading_area_adjustment": trading_mult,
            "dsi_adjustment": dsi_mult,
            "age_adjustment": age_mult,
            "adjusted_premium": adjusted_premium,
            "final_premium": final_premium,
            "dsi_tier": tier,
            "dsi_score": composite_score,
            "rate_per_100": (final_premium / vessel.insured_value) * 100,
        }
    
    def generate_underwriting_decision(
        self,
        submission: MarineSubmission,
        signals: Dict[str, MarineSignal],
        composite_score: float
    ) -> Dict:
        """
        Generate complete underwriting decision with recommendations.
        """
        tier = self.determine_tier(composite_score)
        pricing = self.calculate_premium(submission, signals, composite_score)
        
        # Identify critical signals
        critical_signals = [
            s for s in signals.values() 
            if s.normalized_score < 40
        ]
        
        warning_signals = [
            s for s in signals.values()
            if 40 <= s.normalized_score < 60
        ]
        
        # Decision logic
        if tier == 1:
            decision = "APPROVE"
            action = "Auto-bind at preferred terms"
            conditions = []
        elif tier == 2:
            decision = "APPROVE"
            action = "Auto-bind at standard terms"
            conditions = []
        elif tier == 3:
            decision = "REFER"
            action = "Manual underwriter review required"
            conditions = [
                f"Review {s.signal_name}: {s.evidence}" 
                for s in critical_signals + warning_signals
            ]
        else:  # tier == 4
            if any(s.normalized_score < 20 for s in signals.values()):
                decision = "DECLINE"
                action = "Risk outside appetite"
                conditions = [
                    f"Unacceptable: {s.signal_name} - {s.evidence}"
                    for s in signals.values() if s.normalized_score < 20
                ]
            else:
                decision = "REFER"
                action = "Senior underwriter approval required"
                conditions = [
                    f"Require improvement: {s.signal_name}"
                    for s in critical_signals
                ]
        
        return {
            "submission_id": submission.submission_id,
            "vessel": {
                "imo": submission.vessel.imo_number,
                "name": submission.vessel.vessel_name,
                "type": submission.vessel.vessel_type.value,
            },
            "dsi_score": composite_score,
            "tier": tier,
            "decision": decision,
            "action": action,
            "conditions": conditions,
            "pricing": pricing,
            "critical_signals": [
                {"name": s.signal_name, "score": s.normalized_score, "evidence": s.evidence}
                for s in critical_signals
            ],
            "warning_signals": [
                {"name": s.signal_name, "score": s.normalized_score, "evidence": s.evidence}
                for s in warning_signals
            ],
            "timestamp": datetime.now().isoformat(),
        }


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("DSI Marine Insurance Pricing Model - Test Run")
    print("=" * 70)
    
    # Create sample vessel
    vessel = VesselProfile(
        imo_number="9876543",
        vessel_name="ATLANTIC PIONEER",
        vessel_type=VesselType.BULK_CARRIER,
        flag_state="MH",  # Marshall Islands
        gross_tonnage=45000,
        deadweight=82000,
        year_built=2015,
        classification_society="DNV",
        owner="Oceanic Shipping Ltd",
        operator="Global Bulk Carriers",
        technical_manager="Maritime Technical Services",
        insured_value=35000000,
        trading_area=TradingArea.WORLDWIDE_EXC_WAR
    )
    
    submission = MarineSubmission(
        submission_id="MAR-2025-001234",
        vessel=vessel,
        coverage_types=[CoverageType.HULL_MACHINERY],
        policy_period_start=datetime.now(),
        policy_period_end=datetime.now() + timedelta(days=365),
        deductible=150000,
        limit=35000000,
        broker="Marsh Marine"
    )
    
    # Score signals
    scorer = MarineSignalScorer()
    
    signals = {}
    
    # AIS data
    ais_data = {
        "transmission_gaps": [
            {"duration_hours": 2.5, "location": "SINGAPORE_STRAIT"},
        ],
        "manipulation_indicators": False,
        "dark_events": []
    }
    signals["ais_compliance"] = scorer.score_ais_compliance(ais_data)
    signals["dark_activity"] = scorer.score_dark_activity(ais_data, vessel)
    
    # PSC data
    psc_data = {
        "inspections_36_months": 8,
        "detentions_36_months": 0,
        "deficiencies_36_months": 12,
        "safety_critical_deficiencies": 0
    }
    signals["psc_performance"] = scorer.score_psc_performance(psc_data)
    
    # Class data
    class_data = {
        "society": "DNV",
        "status": "in_class",
        "outstanding_recommendations": 2,
        "conditions_of_class": 0,
        "survey_overdue": False,
        "class_changes_5_years": 0
    }
    signals["class_status"] = scorer.score_class_status(class_data, vessel)
    
    # Vessel condition
    condition_data = {
        "dry_dock_overdue": False,
        "major_repairs_pending": 0,
        "machinery_failures_12m": 1
    }
    signals["vessel_age_condition"] = scorer.score_vessel_age_condition(vessel, condition_data)
    
    # Operator data
    operator_data = {
        "fleet_size": 12,
        "fleet_detention_rate_36m": 0.04,
        "total_losses_5yr": 0,
        "major_incidents_5yr": 1,
        "years_in_operation": 15
    }
    signals["operator_reputation"] = scorer.score_operator_reputation(operator_data)
    
    # Sanctions
    sanctions_data = {
        "direct_sanctions": False,
        "owner_sanctioned": False,
        "sts_with_sanctioned_vessels": 0,
        "high_risk_port_calls_12m": 0,
        "ownership_layers": 2
    }
    signals["sanctions_exposure"] = scorer.score_sanctions_exposure(sanctions_data, vessel)
    
    # Environmental
    environmental_data = {
        "imo2020_compliant": True,
        "ballast_water_compliant": True,
        "environmental_fines_5yr": 0,
        "oil_spills_5yr": 0,
        "cii_rating": "B"
    }
    signals["environmental_compliance"] = scorer.score_environmental_compliance(environmental_data, vessel)
    
    # Calculate composite and generate decision
    model = MarinePricingModel()
    composite, confidence = model.calculate_composite_score(signals)
    decision = model.generate_underwriting_decision(submission, signals, composite)
    
    print(f"\nVessel: {vessel.vessel_name} (IMO: {vessel.imo_number})")
    print(f"Type: {vessel.vessel_type.value}")
    print(f"Insured Value: ${vessel.insured_value:,.0f}")
    print()
    print("Signal Scores:")
    print("-" * 50)
    for name, signal in signals.items():
        print(f"  {name:30} {signal.normalized_score:5.0f}/100  ({signal.evidence[:40]}...)")
    print()
    print(f"DSI Composite Score: {composite:.0f}/1000")
    print(f"Risk Tier: {decision['tier']}")
    print(f"Decision: {decision['decision']}")
    print(f"Action: {decision['action']}")
    print()
    print("Pricing:")
    print(f"  Base Premium: ${decision['pricing']['base_premium']:,.0f}")
    print(f"  DSI Adjustment: {decision['pricing']['dsi_adjustment']:.2f}x")
    print(f"  Final Premium: ${decision['pricing']['final_premium']:,.0f}")
    print(f"  Rate per $100: ${decision['pricing']['rate_per_100']:.3f}")
