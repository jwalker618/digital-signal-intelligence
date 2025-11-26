"""
Digital Signal Intelligence - Directors & Officers (D&O) Insurance Pricing Model
=================================================================================

This module implements DSI-based pricing for D&O insurance, covering:
- Side A (Personal liability when company cannot indemnify)
- Side B (Company reimbursement for indemnifying D&Os)
- Side C (Entity securities coverage)
- Employment Practices Liability (EPL) 
- Fiduciary Liability

D&O insurance is uniquely suited to DSI because corporate governance generates
extensive digital footprints through SEC filings, proxy statements, news coverage,
litigation databases, executive backgrounds, and ESG ratings.

Signal Categories:
1. Corporate Governance (board composition, independence, committees)
2. Financial Health (accounting quality, audit opinions, debt metrics)
3. Litigation History (securities suits, derivative actions, regulatory)
4. Executive Signals (turnover, compensation, background issues)
5. ESG & Reputation (controversies, stakeholder sentiment, ESG scores)
6. Regulatory Environment (industry scrutiny, enforcement trends)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from datetime import datetime, timedelta
import json


class CompanyType(Enum):
    """Company classification for D&O"""
    PUBLIC_LARGE_CAP = "public_large_cap"      # >$10B market cap
    PUBLIC_MID_CAP = "public_mid_cap"          # $2B-$10B
    PUBLIC_SMALL_CAP = "public_small_cap"      # $300M-$2B
    PUBLIC_MICRO_CAP = "public_micro_cap"      # <$300M
    PRE_IPO = "pre_ipo"
    SPAC = "spac"
    PRIVATE_PE_BACKED = "private_pe_backed"
    PRIVATE_VC_BACKED = "private_vc_backed"
    PRIVATE_FAMILY = "private_family"
    NONPROFIT = "nonprofit"


class IndustryRisk(Enum):
    """Industry risk classification for D&O"""
    FINANCIAL_SERVICES = "financial_services"   # Banks, insurance, asset management
    HEALTHCARE_PHARMA = "healthcare_pharma"     # Biotech, pharma, medical devices
    TECHNOLOGY = "technology"                    # Software, hardware, internet
    ENERGY = "energy"                           # Oil & gas, utilities, renewables
    RETAIL_CONSUMER = "retail_consumer"
    MANUFACTURING = "manufacturing"
    REAL_ESTATE = "real_estate"
    CRYPTO_DIGITAL = "crypto_digital_assets"    # Highest risk category
    CANNABIS = "cannabis"
    OTHER = "other"


class CoverageType(Enum):
    """D&O coverage types"""
    SIDE_A = "side_a"                    # Personal D&O liability
    SIDE_B = "side_b"                    # Corporate reimbursement
    SIDE_C = "side_c"                    # Entity securities coverage
    ABC_COMBINED = "abc_combined"         # Full D&O package
    EPL = "employment_practices"          # Employment practices liability
    FIDUCIARY = "fiduciary"              # ERISA fiduciary
    CRIME = "crime"                       # Fidelity/crime


@dataclass
class DOSignal:
    """Individual D&O risk signal"""
    signal_name: str
    raw_value: any
    normalized_score: float  # 0-100
    weight: float
    evidence: str
    data_source: str
    observation_date: datetime
    confidence: float = 1.0


@dataclass
class CompanyProfile:
    """Company information for D&O underwriting"""
    company_name: str
    ticker: Optional[str]
    company_type: CompanyType
    industry: IndustryRisk
    market_cap: Optional[float]          # For public companies
    revenue: float
    total_assets: float
    employees: int
    headquarters_country: str
    stock_exchange: Optional[str]
    fiscal_year_end: str
    year_founded: int
    

@dataclass
class BoardProfile:
    """Board of directors composition"""
    board_size: int
    independent_directors: int
    female_directors: int
    minority_directors: int
    avg_tenure_years: float
    avg_age: float
    directors_over_75: int
    interlocking_directorships: int      # Directors serving on multiple boards
    audit_committee_financial_experts: int
    ceo_is_chairman: bool
    founder_controlled: bool


@dataclass
class DOSubmission:
    """Complete D&O insurance submission"""
    submission_id: str
    company: CompanyProfile
    board: BoardProfile
    coverage_types: List[CoverageType]
    policy_period_start: datetime
    policy_period_end: datetime
    limit_requested: float
    retention: float
    broker: str
    expiring_premium: Optional[float] = None
    expiring_insurer: Optional[str] = None
    claims_history: List[Dict] = field(default_factory=list)


class DOSignalScorer:
    """
    Scores D&O-specific digital signals from various data sources.
    
    Data Sources:
    - SEC EDGAR (10-K, 10-Q, 8-K, DEF 14A proxy statements)
    - PACER (federal litigation database)
    - State court records
    - Glassdoor/Indeed (employee sentiment)
    - News APIs (controversy detection)
    - ESG rating providers (MSCI, Sustainalytics)
    - Executive background databases
    - Short interest data
    - Social media sentiment
    """
    
    # Signal weights for D&O insurance
    SIGNAL_WEIGHTS = {
        # Corporate Governance (25%)
        "board_independence": 0.08,
        "board_diversity": 0.05,
        "committee_quality": 0.06,
        "governance_structure": 0.06,
        
        # Financial Health (25%)
        "accounting_quality": 0.10,
        "audit_opinion": 0.06,
        "financial_distress": 0.05,
        "related_party_transactions": 0.04,
        
        # Litigation & Regulatory (20%)
        "securities_litigation_history": 0.08,
        "regulatory_enforcement": 0.06,
        "derivative_litigation": 0.03,
        "class_action_risk": 0.03,
        
        # Executive Signals (15%)
        "executive_turnover": 0.05,
        "compensation_controversy": 0.04,
        "insider_trading_patterns": 0.03,
        "executive_background": 0.03,
        
        # ESG & Reputation (15%)
        "esg_score": 0.05,
        "controversy_score": 0.05,
        "employee_sentiment": 0.03,
        "short_interest": 0.02,
    }
    
    # Industry base risk factors
    INDUSTRY_RISK_FACTORS = {
        IndustryRisk.CRYPTO_DIGITAL: 2.5,
        IndustryRisk.CANNABIS: 2.0,
        IndustryRisk.HEALTHCARE_PHARMA: 1.6,
        IndustryRisk.FINANCIAL_SERVICES: 1.4,
        IndustryRisk.TECHNOLOGY: 1.3,
        IndustryRisk.ENERGY: 1.2,
        IndustryRisk.REAL_ESTATE: 1.1,
        IndustryRisk.RETAIL_CONSUMER: 1.0,
        IndustryRisk.MANUFACTURING: 0.95,
        IndustryRisk.OTHER: 1.0,
    }
    
    def __init__(self):
        self.signals: Dict[str, DOSignal] = {}
    
    def score_board_independence(self, board: BoardProfile) -> DOSignal:
        """
        Score board independence and structure.
        
        Independent boards provide better oversight and reduce litigation risk.
        NYSE/NASDAQ require majority independence, but best practice is higher.
        
        Scoring:
        - 90-100: >75% independent, diverse committees, no CEO/Chair duality
        - 75-89: >66% independent, meets listing standards
        - 60-74: 50-66% independent, some concerns
        - 40-59: <50% independent, significant governance gaps
        - 0-39: Controlled board, major independence issues
        """
        independence_ratio = board.independent_directors / board.board_size if board.board_size > 0 else 0
        
        # Base score from independence ratio
        if independence_ratio >= 0.80:
            base_score = 95
        elif independence_ratio >= 0.70:
            base_score = 85
        elif independence_ratio >= 0.60:
            base_score = 72
        elif independence_ratio >= 0.50:
            base_score = 58
        else:
            base_score = 35
        
        # Adjustments
        adjustments = 0
        evidence_parts = [f"{independence_ratio:.0%} independent directors"]
        
        if board.ceo_is_chairman:
            adjustments -= 10
            evidence_parts.append("CEO/Chair duality")
        
        if board.founder_controlled:
            adjustments -= 8
            evidence_parts.append("founder-controlled")
        
        if board.interlocking_directorships > 3:
            adjustments -= 5
            evidence_parts.append(f"{board.interlocking_directorships} interlocks")
        
        if board.directors_over_75 > 2:
            adjustments -= 5
            evidence_parts.append(f"{board.directors_over_75} directors over 75")
        
        if board.avg_tenure_years > 12:
            adjustments -= 5
            evidence_parts.append(f"high avg tenure ({board.avg_tenure_years:.1f}yr)")
        
        score = max(min(base_score + adjustments, 100), 10)
        
        return DOSignal(
            signal_name="board_independence",
            raw_value={"independence_ratio": independence_ratio, "adjustments": adjustments},
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["board_independence"],
            evidence="; ".join(evidence_parts),
            data_source="SEC_DEF14A_PROXY",
            observation_date=datetime.now()
        )
    
    def score_board_diversity(self, board: BoardProfile) -> DOSignal:
        """
        Score board diversity.
        
        Diverse boards correlate with better governance outcomes and
        reduced litigation risk. Increasingly important for institutional
        investors and regulatory scrutiny.
        """
        female_ratio = board.female_directors / board.board_size if board.board_size > 0 else 0
        minority_ratio = board.minority_directors / board.board_size if board.board_size > 0 else 0
        
        # Score based on diversity metrics
        if female_ratio >= 0.40 and minority_ratio >= 0.20:
            score = 95
            evidence = f"Excellent diversity: {female_ratio:.0%} female, {minority_ratio:.0%} minority"
        elif female_ratio >= 0.30 and minority_ratio >= 0.15:
            score = 85
            evidence = f"Good diversity: {female_ratio:.0%} female, {minority_ratio:.0%} minority"
        elif female_ratio >= 0.20:
            score = 70
            evidence = f"Adequate diversity: {female_ratio:.0%} female"
        elif female_ratio >= 0.10:
            score = 55
            evidence = f"Below average diversity: {female_ratio:.0%} female"
        else:
            score = 35
            evidence = f"Poor diversity: {female_ratio:.0%} female, {minority_ratio:.0%} minority"
        
        return DOSignal(
            signal_name="board_diversity",
            raw_value={"female_ratio": female_ratio, "minority_ratio": minority_ratio},
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["board_diversity"],
            evidence=evidence,
            data_source="SEC_DEF14A_PROXY",
            observation_date=datetime.now()
        )
    
    def score_accounting_quality(self, financial_data: Dict) -> DOSignal:
        """
        Score accounting quality and financial reporting.
        
        Key indicators:
        - Material weaknesses in internal controls
        - Restatements
        - Non-GAAP adjustments magnitude
        - Revenue recognition complexity
        - Audit fees relative to peers
        - CFO turnover
        """
        material_weaknesses = financial_data.get("material_weaknesses", 0)
        significant_deficiencies = financial_data.get("significant_deficiencies", 0)
        restatements_3yr = financial_data.get("restatements_3_years", 0)
        late_filings = financial_data.get("late_filings_3_years", 0)
        non_gaap_gap = financial_data.get("non_gaap_vs_gaap_eps_gap_pct", 0)
        cfo_changes_3yr = financial_data.get("cfo_changes_3_years", 0)
        auditor_changes_3yr = financial_data.get("auditor_changes_3_years", 0)
        
        # Critical failures
        if material_weaknesses > 0 and restatements_3yr > 0:
            score = 15
            evidence = f"CRITICAL: {material_weaknesses} material weaknesses + {restatements_3yr} restatements"
        elif material_weaknesses > 0:
            score = 30
            evidence = f"Material weakness in internal controls"
        elif restatements_3yr > 1:
            score = 35
            evidence = f"Multiple restatements: {restatements_3yr} in 3 years"
        elif restatements_3yr > 0:
            score = 50
            evidence = f"Financial restatement in past 3 years"
        elif late_filings > 1:
            score = 45
            evidence = f"Multiple late filings: {late_filings} in 3 years"
        elif significant_deficiencies > 1:
            score = 55
            evidence = f"Significant deficiencies: {significant_deficiencies}"
        elif non_gaap_gap > 50:
            score = 55
            evidence = f"Large non-GAAP adjustments: {non_gaap_gap:.0f}% gap"
        elif cfo_changes_3yr > 1 or auditor_changes_3yr > 0:
            score = 65
            evidence = f"CFO/auditor turnover: {cfo_changes_3yr} CFO, {auditor_changes_3yr} auditor changes"
        elif non_gaap_gap > 25:
            score = 75
            evidence = f"Moderate non-GAAP adjustments: {non_gaap_gap:.0f}% gap"
        else:
            score = 90
            evidence = "Clean accounting record, no material issues"
        
        return DOSignal(
            signal_name="accounting_quality",
            raw_value=financial_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["accounting_quality"],
            evidence=evidence,
            data_source="SEC_10K_10Q",
            observation_date=datetime.now()
        )
    
    def score_audit_opinion(self, audit_data: Dict) -> DOSignal:
        """
        Score audit opinion and going concern.
        
        Audit opinions are binary for coverage purposes (qualified = serious issue)
        but DSI looks at subtler signals:
        - Going concern language
        - Critical audit matters (CAMs)
        - Audit fee trends
        - Auditor tenure
        """
        opinion_type = audit_data.get("opinion_type", "unqualified")
        going_concern = audit_data.get("going_concern", False)
        going_concern_resolved = audit_data.get("going_concern_resolved", False)
        cams_count = audit_data.get("critical_audit_matters", 0)
        auditor_tenure = audit_data.get("auditor_tenure_years", 5)
        big4_auditor = audit_data.get("big4_auditor", True)
        
        if opinion_type in ["adverse", "disclaimer"]:
            score = 5
            evidence = f"CRITICAL: {opinion_type} audit opinion"
        elif opinion_type == "qualified":
            score = 20
            evidence = "Qualified audit opinion"
        elif going_concern and not going_concern_resolved:
            score = 25
            evidence = "Going concern warning - unresolved"
        elif going_concern and going_concern_resolved:
            score = 55
            evidence = "Going concern warning - subsequently resolved"
        elif not big4_auditor:
            score = 60
            evidence = f"Non-Big 4 auditor"
        elif cams_count > 3:
            score = 65
            evidence = f"Elevated critical audit matters: {cams_count}"
        elif auditor_tenure > 20:
            score = 70
            evidence = f"Long auditor tenure: {auditor_tenure} years (independence concern)"
        elif cams_count > 1:
            score = 80
            evidence = f"Standard audit, {cams_count} critical audit matters"
        else:
            score = 95
            evidence = "Clean unqualified opinion, Big 4 auditor"
        
        return DOSignal(
            signal_name="audit_opinion",
            raw_value=audit_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["audit_opinion"],
            evidence=evidence,
            data_source="SEC_10K_AUDIT_REPORT",
            observation_date=datetime.now()
        )
    
    def score_securities_litigation(self, litigation_data: Dict) -> DOSignal:
        """
        Score securities litigation history.
        
        Prior securities class actions are the strongest predictor of future
        claims. DSI tracks:
        - Securities class actions (10b-5)
        - Derivative suits
        - SEC enforcement
        - Settlement amounts
        """
        class_actions_5yr = litigation_data.get("securities_class_actions_5yr", 0)
        pending_class_actions = litigation_data.get("pending_class_actions", 0)
        sec_enforcement_5yr = litigation_data.get("sec_enforcement_5yr", 0)
        derivative_suits_5yr = litigation_data.get("derivative_suits_5yr", 0)
        total_settlements = litigation_data.get("total_settlement_amount_5yr", 0)
        
        if pending_class_actions > 0 and sec_enforcement_5yr > 0:
            score = 10
            evidence = f"CRITICAL: {pending_class_actions} pending class actions + SEC enforcement"
        elif pending_class_actions > 1:
            score = 20
            evidence = f"Multiple pending class actions: {pending_class_actions}"
        elif pending_class_actions > 0:
            score = 35
            evidence = f"Pending securities class action"
        elif sec_enforcement_5yr > 0:
            score = 40
            evidence = f"SEC enforcement action in past 5 years"
        elif class_actions_5yr > 1:
            score = 45
            evidence = f"Multiple prior class actions: {class_actions_5yr} in 5 years"
        elif class_actions_5yr > 0:
            score = 55
            evidence = f"Prior securities class action (settled)"
        elif derivative_suits_5yr > 1:
            score = 60
            evidence = f"Derivative suits: {derivative_suits_5yr} in 5 years"
        elif derivative_suits_5yr > 0:
            score = 75
            evidence = f"Single derivative suit in 5 years"
        else:
            score = 95
            evidence = "No securities litigation history"
        
        return DOSignal(
            signal_name="securities_litigation_history",
            raw_value=litigation_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["securities_litigation_history"],
            evidence=evidence,
            data_source="PACER_SCAC_DATABASE",
            observation_date=datetime.now()
        )
    
    def score_executive_turnover(self, executive_data: Dict) -> DOSignal:
        """
        Score executive turnover patterns.
        
        High C-suite turnover, especially sudden departures, correlates
        with underlying problems that lead to D&O claims.
        """
        ceo_changes_3yr = executive_data.get("ceo_changes_3_years", 0)
        cfo_changes_3yr = executive_data.get("cfo_changes_3_years", 0)
        coo_changes_3yr = executive_data.get("coo_changes_3_years", 0)
        sudden_departures = executive_data.get("sudden_departures_3_years", 0)
        departures_under_investigation = executive_data.get("departures_under_investigation", 0)
        avg_c_suite_tenure = executive_data.get("avg_c_suite_tenure_years", 5)
        
        total_c_suite_changes = ceo_changes_3yr + cfo_changes_3yr + coo_changes_3yr
        
        if departures_under_investigation > 0:
            score = 15
            evidence = f"CRITICAL: Executive departures under investigation"
        elif sudden_departures > 2:
            score = 30
            evidence = f"Multiple sudden executive departures: {sudden_departures}"
        elif ceo_changes_3yr > 1 or cfo_changes_3yr > 1:
            score = 40
            evidence = f"High C-suite turnover: {ceo_changes_3yr} CEO, {cfo_changes_3yr} CFO changes"
        elif sudden_departures > 0:
            score = 50
            evidence = f"Sudden executive departure in past 3 years"
        elif total_c_suite_changes > 3:
            score = 55
            evidence = f"Elevated C-suite turnover: {total_c_suite_changes} changes in 3 years"
        elif avg_c_suite_tenure < 2:
            score = 60
            evidence = f"Short C-suite tenure: {avg_c_suite_tenure:.1f} years average"
        elif total_c_suite_changes > 1:
            score = 75
            evidence = f"Some C-suite turnover: {total_c_suite_changes} changes"
        else:
            score = 92
            evidence = f"Stable executive team, {avg_c_suite_tenure:.1f} years avg tenure"
        
        return DOSignal(
            signal_name="executive_turnover",
            raw_value=executive_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["executive_turnover"],
            evidence=evidence,
            data_source="SEC_8K_PROXY",
            observation_date=datetime.now()
        )
    
    def score_insider_trading_patterns(self, insider_data: Dict) -> DOSignal:
        """
        Score insider trading patterns.
        
        Unusual insider selling, especially clustered selling before
        negative news, is a litigation red flag.
        """
        insider_sell_ratio = insider_data.get("sell_buy_ratio_12m", 1.0)
        clustered_selling = insider_data.get("clustered_selling_events", 0)
        selling_before_decline = insider_data.get("selling_before_price_decline", False)
        rule_10b5_1_plans = insider_data.get("10b5_1_plan_coverage_pct", 0)
        
        if selling_before_decline and clustered_selling > 0:
            score = 15
            evidence = "CRITICAL: Clustered insider selling before price decline"
        elif selling_before_decline:
            score = 30
            evidence = "Insider selling preceded significant stock decline"
        elif clustered_selling > 2:
            score = 45
            evidence = f"Multiple clustered selling events: {clustered_selling}"
        elif insider_sell_ratio > 5 and rule_10b5_1_plans < 50:
            score = 50
            evidence = f"Heavy insider selling ({insider_sell_ratio:.1f}x) outside 10b5-1 plans"
        elif insider_sell_ratio > 3:
            score = 60
            evidence = f"Elevated insider selling: {insider_sell_ratio:.1f}x sell/buy ratio"
        elif rule_10b5_1_plans < 30:
            score = 70
            evidence = f"Low 10b5-1 plan coverage: {rule_10b5_1_plans:.0f}%"
        elif insider_sell_ratio > 1.5:
            score = 80
            evidence = f"Moderate insider selling: {insider_sell_ratio:.1f}x ratio"
        else:
            score = 92
            evidence = f"Normal insider trading patterns, {rule_10b5_1_plans:.0f}% 10b5-1 coverage"
        
        return DOSignal(
            signal_name="insider_trading_patterns",
            raw_value=insider_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["insider_trading_patterns"],
            evidence=evidence,
            data_source="SEC_FORM4_EDGAR",
            observation_date=datetime.now()
        )
    
    def score_esg(self, esg_data: Dict) -> DOSignal:
        """
        Score ESG profile.
        
        ESG issues increasingly drive D&O claims through:
        - Climate disclosure litigation
        - Greenwashing claims
        - Human capital management suits
        - Board diversity demands
        """
        esg_rating = esg_data.get("overall_rating", "BBB")  # MSCI scale
        environmental_score = esg_data.get("environmental_score", 50)
        social_score = esg_data.get("social_score", 50)
        governance_score = esg_data.get("governance_score", 50)
        controversies = esg_data.get("active_controversies", 0)
        severe_controversies = esg_data.get("severe_controversies", 0)
        
        # Map MSCI ratings to scores
        rating_scores = {
            "AAA": 95, "AA": 88, "A": 78, "BBB": 65,
            "BB": 52, "B": 40, "CCC": 25
        }
        base_score = rating_scores.get(esg_rating, 50)
        
        # Adjust for controversies
        if severe_controversies > 0:
            score = min(base_score, 35)
            evidence = f"Severe ESG controversy active, rating: {esg_rating}"
        elif controversies > 2:
            score = min(base_score - 15, 55)
            evidence = f"Multiple ESG controversies ({controversies}), rating: {esg_rating}"
        elif controversies > 0:
            score = min(base_score - 8, 70)
            evidence = f"ESG controversy present, rating: {esg_rating}"
        elif governance_score < 40:
            score = min(base_score, 55)
            evidence = f"Weak governance pillar ({governance_score}), overall: {esg_rating}"
        else:
            score = base_score
            evidence = f"ESG rating: {esg_rating}, G score: {governance_score}"
        
        return DOSignal(
            signal_name="esg_score",
            raw_value=esg_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["esg_score"],
            evidence=evidence,
            data_source="MSCI_SUSTAINALYTICS",
            observation_date=datetime.now()
        )
    
    def score_employee_sentiment(self, sentiment_data: Dict) -> DOSignal:
        """
        Score employee sentiment from Glassdoor/Indeed.
        
        Poor employee sentiment correlates with EPL claims and can
        indicate cultural issues that lead to broader D&O exposure.
        """
        glassdoor_rating = sentiment_data.get("glassdoor_overall", 3.5)
        ceo_approval = sentiment_data.get("ceo_approval_pct", 70)
        recommend_pct = sentiment_data.get("recommend_to_friend_pct", 60)
        culture_rating = sentiment_data.get("culture_rating", 3.5)
        recent_trend = sentiment_data.get("rating_trend_12m", 0)  # Positive = improving
        review_count = sentiment_data.get("review_count", 100)
        
        # Low review count = low confidence
        confidence = min(review_count / 200, 1.0)
        
        if glassdoor_rating < 2.5 or ceo_approval < 40:
            score = 25
            evidence = f"Poor sentiment: {glassdoor_rating}/5 Glassdoor, {ceo_approval}% CEO approval"
        elif glassdoor_rating < 3.0:
            score = 40
            evidence = f"Below average: {glassdoor_rating}/5 Glassdoor"
        elif glassdoor_rating < 3.5 or recommend_pct < 50:
            score = 55
            evidence = f"Mixed sentiment: {glassdoor_rating}/5, {recommend_pct}% recommend"
        elif glassdoor_rating < 4.0:
            score = 72
            evidence = f"Acceptable sentiment: {glassdoor_rating}/5, {ceo_approval}% CEO approval"
        elif recent_trend < -0.3:
            score = 65
            evidence = f"Good rating ({glassdoor_rating}/5) but declining trend"
        else:
            score = 88
            evidence = f"Strong sentiment: {glassdoor_rating}/5, {recommend_pct}% recommend"
        
        return DOSignal(
            signal_name="employee_sentiment",
            raw_value=sentiment_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["employee_sentiment"],
            evidence=evidence,
            data_source="GLASSDOOR_INDEED",
            observation_date=datetime.now(),
            confidence=confidence
        )
    
    def score_short_interest(self, market_data: Dict) -> DOSignal:
        """
        Score short interest as litigation predictor.
        
        High short interest indicates market skepticism and often
        precedes securities class actions when shorts are proven right.
        """
        short_interest_pct = market_data.get("short_interest_pct_float", 0)
        short_interest_ratio = market_data.get("days_to_cover", 1)
        short_interest_change_30d = market_data.get("short_interest_change_30d_pct", 0)
        on_short_squeeze_lists = market_data.get("on_short_squeeze_watch", False)
        
        if short_interest_pct > 25:
            score = 20
            evidence = f"CRITICAL: Extreme short interest {short_interest_pct:.1f}% of float"
        elif short_interest_pct > 15:
            score = 35
            evidence = f"Very high short interest: {short_interest_pct:.1f}% of float"
        elif short_interest_pct > 10:
            score = 50
            evidence = f"Elevated short interest: {short_interest_pct:.1f}% of float"
        elif short_interest_change_30d > 50:
            score = 55
            evidence = f"Rapidly increasing short interest: +{short_interest_change_30d:.0f}% in 30d"
        elif short_interest_pct > 5:
            score = 70
            evidence = f"Moderate short interest: {short_interest_pct:.1f}% of float"
        elif on_short_squeeze_lists:
            score = 60
            evidence = f"On short squeeze watchlists"
        else:
            score = 90
            evidence = f"Low short interest: {short_interest_pct:.1f}% of float"
        
        return DOSignal(
            signal_name="short_interest",
            raw_value=market_data,
            normalized_score=score,
            weight=self.SIGNAL_WEIGHTS["short_interest"],
            evidence=evidence,
            data_source="FINRA_SHORT_INTEREST",
            observation_date=datetime.now()
        )


class DOPricingModel:
    """
    DSI-based D&O insurance pricing model.
    
    Combines digital signals with traditional D&O underwriting factors
    to produce risk-adjusted pricing.
    """
    
    # Base rates per $1M of coverage by company type
    BASE_RATES_PER_MILLION = {
        CompanyType.PUBLIC_LARGE_CAP: 3500,
        CompanyType.PUBLIC_MID_CAP: 5500,
        CompanyType.PUBLIC_SMALL_CAP: 8500,
        CompanyType.PUBLIC_MICRO_CAP: 15000,
        CompanyType.PRE_IPO: 25000,
        CompanyType.SPAC: 45000,
        CompanyType.PRIVATE_PE_BACKED: 4000,
        CompanyType.PRIVATE_VC_BACKED: 6000,
        CompanyType.PRIVATE_FAMILY: 2500,
        CompanyType.NONPROFIT: 2000,
    }
    
    # DSI tier pricing adjustments
    TIER_ADJUSTMENTS = {
        1: 0.70,   # Preferred: 30% discount
        2: 1.00,   # Standard: no adjustment
        3: 1.50,   # Elevated: 50% surcharge
        4: 2.50,   # High Risk: 150% surcharge (if bound at all)
    }
    
    def __init__(self):
        self.signal_scorer = DOSignalScorer()
    
    def calculate_composite_score(self, signals: Dict[str, DOSignal]) -> Tuple[float, float]:
        """Calculate weighted composite DSI score."""
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
        submission: DOSubmission,
        signals: Dict[str, DOSignal],
        composite_score: float
    ) -> Dict:
        """Calculate risk-adjusted premium."""
        company = submission.company
        
        # Base premium
        base_rate = self.BASE_RATES_PER_MILLION.get(company.company_type, 5000)
        limit_millions = submission.limit_requested / 1_000_000
        base_premium = base_rate * limit_millions
        
        # Industry adjustment
        industry_mult = self.signal_scorer.INDUSTRY_RISK_FACTORS.get(company.industry, 1.0)
        
        # DSI tier adjustment
        tier = self.determine_tier(composite_score)
        dsi_mult = self.TIER_ADJUSTMENTS[tier]
        
        # Size adjustment (larger companies = more exposure)
        if company.market_cap and company.market_cap > 50_000_000_000:
            size_mult = 1.25
        elif company.market_cap and company.market_cap > 10_000_000_000:
            size_mult = 1.10
        elif company.revenue > 5_000_000_000:
            size_mult = 1.05
        else:
            size_mult = 1.00
        
        # ILF (Increased Limit Factor) - premium doesn't scale linearly with limit
        if limit_millions <= 5:
            ilf = 1.0
        elif limit_millions <= 10:
            ilf = 0.90
        elif limit_millions <= 25:
            ilf = 0.80
        else:
            ilf = 0.70
        
        # Calculate final premium
        adjusted_premium = base_premium * industry_mult * dsi_mult * size_mult * ilf
        
        # Minimum premium
        minimum_premium = 15000
        final_premium = max(adjusted_premium, minimum_premium)
        
        return {
            "base_premium": base_premium,
            "industry_adjustment": industry_mult,
            "dsi_adjustment": dsi_mult,
            "size_adjustment": size_mult,
            "ilf": ilf,
            "adjusted_premium": adjusted_premium,
            "final_premium": final_premium,
            "dsi_tier": tier,
            "dsi_score": composite_score,
            "rate_per_million": final_premium / limit_millions,
        }
    
    def generate_underwriting_decision(
        self,
        submission: DOSubmission,
        signals: Dict[str, DOSignal],
        composite_score: float
    ) -> Dict:
        """Generate complete underwriting decision."""
        tier = self.determine_tier(composite_score)
        pricing = self.calculate_premium(submission, signals, composite_score)
        
        # Identify critical signals
        critical_signals = [s for s in signals.values() if s.normalized_score < 40]
        warning_signals = [s for s in signals.values() if 40 <= s.normalized_score < 60]
        
        # Check for automatic declinations
        auto_decline_triggers = [
            signals.get("securities_litigation_history", DOSignal("", "", 100, 0, "", "", datetime.now())).normalized_score < 20,
            signals.get("audit_opinion", DOSignal("", "", 100, 0, "", "", datetime.now())).normalized_score < 15,
            signals.get("accounting_quality", DOSignal("", "", 100, 0, "", "", datetime.now())).normalized_score < 20,
        ]
        
        # Decision logic
        if any(auto_decline_triggers):
            decision = "DECLINE"
            action = "Automatic decline - critical issue identified"
            conditions = [f"Unacceptable: {s.signal_name} - {s.evidence}" for s in critical_signals]
        elif tier == 1:
            decision = "APPROVE"
            action = "Auto-bind at preferred terms"
            conditions = []
        elif tier == 2:
            decision = "APPROVE"
            action = "Auto-bind at standard terms"
            conditions = []
        elif tier == 3:
            decision = "REFER"
            action = "Senior underwriter review required"
            conditions = [f"Review: {s.signal_name} - {s.evidence}" for s in critical_signals + warning_signals]
        else:
            decision = "REFER"
            action = "Management approval required - high risk submission"
            conditions = [f"Concern: {s.signal_name} - {s.evidence}" for s in critical_signals]
        
        return {
            "submission_id": submission.submission_id,
            "company": {
                "name": submission.company.company_name,
                "ticker": submission.company.ticker,
                "type": submission.company.company_type.value,
                "industry": submission.company.industry.value,
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
    print("DSI D&O Insurance Pricing Model - Test Run")
    print("=" * 70)
    
    # Create sample company
    company = CompanyProfile(
        company_name="TechCorp Industries Inc.",
        ticker="TECH",
        company_type=CompanyType.PUBLIC_MID_CAP,
        industry=IndustryRisk.TECHNOLOGY,
        market_cap=5_500_000_000,
        revenue=2_200_000_000,
        total_assets=3_800_000_000,
        employees=8500,
        headquarters_country="US",
        stock_exchange="NASDAQ",
        fiscal_year_end="December",
        year_founded=2005
    )
    
    board = BoardProfile(
        board_size=9,
        independent_directors=7,
        female_directors=3,
        minority_directors=2,
        avg_tenure_years=6.5,
        avg_age=58,
        directors_over_75=1,
        interlocking_directorships=2,
        audit_committee_financial_experts=2,
        ceo_is_chairman=False,
        founder_controlled=False
    )
    
    submission = DOSubmission(
        submission_id="DO-2025-005678",
        company=company,
        board=board,
        coverage_types=[CoverageType.ABC_COMBINED],
        policy_period_start=datetime.now(),
        policy_period_end=datetime.now() + timedelta(days=365),
        limit_requested=15_000_000,
        retention=500_000,
        broker="Aon",
        expiring_premium=175000,
        expiring_insurer="AIG"
    )
    
    # Score signals
    scorer = DOSignalScorer()
    signals = {}
    
    # Board signals
    signals["board_independence"] = scorer.score_board_independence(board)
    signals["board_diversity"] = scorer.score_board_diversity(board)
    
    # Financial signals
    financial_data = {
        "material_weaknesses": 0,
        "significant_deficiencies": 1,
        "restatements_3_years": 0,
        "late_filings_3_years": 0,
        "non_gaap_vs_gaap_eps_gap_pct": 18,
        "cfo_changes_3_years": 0,
        "auditor_changes_3_years": 0
    }
    signals["accounting_quality"] = scorer.score_accounting_quality(financial_data)
    
    audit_data = {
        "opinion_type": "unqualified",
        "going_concern": False,
        "critical_audit_matters": 2,
        "auditor_tenure_years": 8,
        "big4_auditor": True
    }
    signals["audit_opinion"] = scorer.score_audit_opinion(audit_data)
    
    # Litigation signals
    litigation_data = {
        "securities_class_actions_5yr": 0,
        "pending_class_actions": 0,
        "sec_enforcement_5yr": 0,
        "derivative_suits_5yr": 1,
        "total_settlement_amount_5yr": 0
    }
    signals["securities_litigation_history"] = scorer.score_securities_litigation(litigation_data)
    
    # Executive signals
    executive_data = {
        "ceo_changes_3_years": 0,
        "cfo_changes_3_years": 1,
        "coo_changes_3_years": 0,
        "sudden_departures_3_years": 0,
        "departures_under_investigation": 0,
        "avg_c_suite_tenure_years": 4.5
    }
    signals["executive_turnover"] = scorer.score_executive_turnover(executive_data)
    
    insider_data = {
        "sell_buy_ratio_12m": 2.1,
        "clustered_selling_events": 0,
        "selling_before_price_decline": False,
        "10b5_1_plan_coverage_pct": 65
    }
    signals["insider_trading_patterns"] = scorer.score_insider_trading_patterns(insider_data)
    
    # ESG signals
    esg_data = {
        "overall_rating": "A",
        "environmental_score": 62,
        "social_score": 58,
        "governance_score": 72,
        "active_controversies": 0,
        "severe_controversies": 0
    }
    signals["esg_score"] = scorer.score_esg(esg_data)
    
    sentiment_data = {
        "glassdoor_overall": 3.8,
        "ceo_approval_pct": 78,
        "recommend_to_friend_pct": 72,
        "culture_rating": 3.6,
        "rating_trend_12m": 0.1,
        "review_count": 450
    }
    signals["employee_sentiment"] = scorer.score_employee_sentiment(sentiment_data)
    
    market_data = {
        "short_interest_pct_float": 4.2,
        "days_to_cover": 2.8,
        "short_interest_change_30d_pct": 5,
        "on_short_squeeze_watch": False
    }
    signals["short_interest"] = scorer.score_short_interest(market_data)
    
    # Calculate composite and generate decision
    model = DOPricingModel()
    composite, confidence = model.calculate_composite_score(signals)
    decision = model.generate_underwriting_decision(submission, signals, composite)
    
    print(f"\nCompany: {company.company_name} ({company.ticker})")
    print(f"Type: {company.company_type.value}")
    print(f"Industry: {company.industry.value}")
    print(f"Market Cap: ${company.market_cap:,.0f}")
    print(f"Limit Requested: ${submission.limit_requested:,.0f}")
    print()
    print("Signal Scores:")
    print("-" * 60)
    for name, signal in signals.items():
        evidence_short = signal.evidence[:45] + "..." if len(signal.evidence) > 45 else signal.evidence
        print(f"  {name:32} {signal.normalized_score:5.0f}/100  ({evidence_short})")
    print()
    print(f"DSI Composite Score: {composite:.0f}/1000")
    print(f"Risk Tier: {decision['tier']}")
    print(f"Decision: {decision['decision']}")
    print(f"Action: {decision['action']}")
    print()
    print("Pricing:")
    print(f"  Base Premium: ${decision['pricing']['base_premium']:,.0f}")
    print(f"  Industry Adjustment: {decision['pricing']['industry_adjustment']:.2f}x")
    print(f"  DSI Adjustment: {decision['pricing']['dsi_adjustment']:.2f}x")
    print(f"  Final Premium: ${decision['pricing']['final_premium']:,.0f}")
    print(f"  Rate per $1M: ${decision['pricing']['rate_per_million']:,.0f}")
    print(f"  vs Expiring: {((decision['pricing']['final_premium'] / submission.expiring_premium) - 1) * 100:+.1f}%")
