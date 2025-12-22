"""
signal_configs.py - Signal Configuration Mappings

Maps each signal to its categorizer type and configuration profile.
This provides the complete wiring between aggregator outputs and categorizers.
"""

from typing import Dict, Any, List

# =============================================================================
# SCORING LOGIC PROFILES - STATE -> SCORE MAPPINGS
# =============================================================================

SCORING_LOGIC_PROFILES: Dict[str, Dict[str, float]] = {
    # --- GENERIC PATTERNS (reusable) ---
    "clean_single_multiple_significant": {
        "CLEAN": 100, "SINGLE": 70, "MULTIPLE": 45, "SIGNIFICANT": 20, "UNKNOWN": 50
    },
    "clean_low_moderate_high": {
        "CLEAN": 100, "LOW": 80, "MODERATE": 55, "HIGH": 25, "UNKNOWN": 50
    },
    "compliant_partial_noncompliant": {
        "COMPLIANT": 100, "PARTIAL": 65, "EXPIRED": 40, "NON_COMPLIANT": 20, "UNKNOWN": 50
    },
    "stable_moderate_volatile": {
        "STABLE": 100, "MODERATE": 75, "VOLATILE": 45, "HIGHLY_VOLATILE": 20, "UNKNOWN": 50
    },
    "tier1_tier2_none": {
        "TIER_1": 100, "TIER_2": 70, "NONE": 40, "UNKNOWN": 50
    },
    "excellent_good_adequate_poor": {
        "EXCELLENT": 100, "GOOD": 85, "ADEQUATE": 65, "POOR": 35, "UNKNOWN": 50
    },
    "low_moderate_elevated_high": {
        "LOW": 100, "MODERATE": 75, "ELEVATED": 50, "HIGH": 25, "UNKNOWN": 50
    },
    "active_not_used": {
        "ACTIVE": 100, "NOT_USED": 60, "UNKNOWN": 50
    },
    "none_occasional_frequent_high": {
        "NONE": 100, "OCCASIONAL": 75, "FREQUENT": 45, "HIGH_FREQUENCY": 20, "UNKNOWN": 50
    },
    
    # --- MARINE SIGNALS ---
    "psc_detention": {
        "CLEAN": 100, "SINGLE": 70, "MULTIPLE": 40, "FREQUENT": 15, "UNKNOWN": 50
    },
    "class_status": {
        "IN_CLASS_CLEAN": 100, "IN_CLASS_CONDITIONS": 75, "SUSPENDED": 30, "WITHDRAWN": 10, "NO_CLASS": 5, "UNKNOWN": 50
    },
    "ism_compliance": {
        "COMPLIANT": 100, "PARTIAL": 60, "EXPIRED": 35, "NON_COMPLIANT": 15, "UNKNOWN": 50
    },
    "survey_compliance": {
        "CURRENT": 100, "MINOR_OVERDUE": 70, "MAJOR_OVERDUE": 35, "UNKNOWN": 50
    },
    "sanctions_status": {
        "CLEAR": 100, "POTENTIAL_MATCH": 50, "MATCH": 10, "BLOCKED": 0, "UNKNOWN": 50
    },
    "ownership_transparency": {
        "TRANSPARENT": 100, "PARTIAL": 65, "OPAQUE": 30, "UNKNOWN": 50
    },
    "jurisdiction_risk": {
        "LOW": 100, "MODERATE": 70, "ELEVATED": 45, "HIGH": 20, "SANCTIONED": 5, "UNKNOWN": 50
    },
    "dark_activity": {
        "CLEAN": 100, "MINOR": 80, "CONCERNING": 50, "HIGH_RISK": 20, "UNKNOWN": 50
    },
    "route_risk": {
        "LOW": 100, "MODERATE": 75, "ELEVATED": 50, "HIGH": 25, "VERY_HIGH": 10, "UNKNOWN": 50
    },
    "crew_certification": {
        "COMPLIANT": 100, "MINOR_GAPS": 75, "MAJOR_GAPS": 40, "NON_COMPLIANT": 15, "UNKNOWN": 50
    },
    "flag_state": {
        "WHITE_LIST": 100, "GREY_LIST": 60, "BLACK_LIST": 20, "UNKNOWN": 50
    },
    "environmental_compliance": {
        "COMPLIANT": 100, "MINOR_ISSUES": 75, "MAJOR_ISSUES": 40, "NON_COMPLIANT": 15, "UNKNOWN": 50
    },
    "cii_rating": {
        "A": 100, "B": 85, "C": 70, "D": 45, "E": 20, "UNKNOWN": 50
    },
    
    # --- AEROSPACE SIGNALS ---
    "accident_history": {
        "CLEAN": 100, "SINGLE": 65, "MULTIPLE": 35, "SIGNIFICANT": 15, "UNKNOWN": 50
    },
    "fatality_history": {
        "CLEAN": 100, "SINGLE": 40, "MULTIPLE": 15, "UNKNOWN": 50
    },
    "incident_history": {
        "CLEAN": 100, "LOW": 80, "MODERATE": 55, "HIGH": 25, "UNKNOWN": 50
    },
    "investigation_findings": {
        "CLEAN": 100, "MINOR": 80, "MODERATE": 55, "SIGNIFICANT": 25, "UNKNOWN": 50
    },
    "eu_safety_list": {
        "CLEAR": 100, "OPERATING_RESTRICTIONS": 50, "BANNED": 5, "UNKNOWN": 50
    },
    "state_safety_rating": {
        "CAT_1": 100, "CAT_2": 50, "UNRATED": 60, "UNKNOWN": 50
    },
    "iosa_status": {
        "REGISTERED": 100, "NOT_REGISTERED": 50, "UNKNOWN": 50
    },
    "iosa_audit_status": {
        "CLEAN": 100, "MINOR_FINDINGS": 80, "MODERATE_FINDINGS": 55, "SIGNIFICANT_FINDINGS": 25, "UNKNOWN": 50
    },
    "certificate_status": {
        "VALID": 100, "CONDITIONAL": 70, "SUSPENDED": 25, "REVOKED": 5, "UNKNOWN": 50
    },
    "aoc_status": {
        "VALID": 100, "CONDITIONAL": 70, "SUSPENDED": 25, "REVOKED": 5, "UNKNOWN": 50
    },
    "enforcement_actions": {
        "CLEAN": 100, "SINGLE": 70, "MULTIPLE": 40, "SIGNIFICANT": 15, "UNKNOWN": 50
    },
    "ramp_inspection": {
        "CLEAN": 100, "MINOR": 80, "MODERATE": 55, "SIGNIFICANT": 25, "UNKNOWN": 50
    },
    "fleet_homogeneity": {
        "HOMOGENEOUS": 100, "MODERATE": 75, "DIVERSE": 55, "UNKNOWN": 50
    },
    "aircraft_generation": {
        "CURRENT": 100, "PREVIOUS": 75, "LEGACY": 50, "VINTAGE": 30, "UNKNOWN": 50
    },
    "oem_relationship": {
        "STRATEGIC": 100, "PREFERRED": 80, "STANDARD": 60, "MINIMAL": 40, "UNKNOWN": 50
    },
    "operational_complexity": {
        "LOW": 100, "MODERATE": 75, "HIGH": 50, "VERY_HIGH": 30, "UNKNOWN": 50
    },
    "terrain_exposure": {
        "LOW": 100, "MODERATE": 75, "ELEVATED": 50, "HIGH": 30, "UNKNOWN": 50
    },
    "weather_exposure": {
        "LOW": 100, "MODERATE": 75, "ELEVATED": 50, "HIGH": 30, "UNKNOWN": 50
    },
    "conflict_zone_exposure": {
        "NONE": 100, "MINIMAL": 80, "MODERATE": 55, "SIGNIFICANT": 30, "UNKNOWN": 50
    },
    "maintenance_indicators": {
        "EXCELLENT": 100, "GOOD": 85, "ADEQUATE": 65, "POOR": 35, "UNKNOWN": 50
    },
    "ad_compliance": {
        "COMPLIANT": 100, "MINOR_OVERDUE": 70, "SIGNIFICANT_OVERDUE": 35, "UNKNOWN": 50
    },
    "crew_experience": {
        "VERY_HIGH": 100, "HIGH": 85, "MODERATE": 65, "LOW": 40, "UNKNOWN": 50
    },
    "training_indicators": {
        "EXCELLENT": 100, "GOOD": 85, "ADEQUATE": 65, "POOR": 35, "UNKNOWN": 50
    },
    "public_financials": {
        "STRONG": 100, "STABLE": 80, "MODERATE": 55, "WEAK": 30, "DISTRESSED": 10, "UNKNOWN": 50
    },
    "government_support": {
        "GUARANTEED": 100, "STRONG": 85, "MODERATE": 65, "MINIMAL": 45, "NONE": 50, "UNKNOWN": 50
    },
    "alliance_membership": {
        "STAR_ALLIANCE": 100, "ONEWORLD": 100, "SKYTEAM": 100, "REGIONAL": 70, "NONE": 50, "UNKNOWN": 50
    },
    "codeshare_quality": {
        "EXTENSIVE": 100, "MODERATE": 75, "LIMITED": 50, "NONE": 40, "UNKNOWN": 50
    },
    "market_position": {
        "DOMINANT": 100, "MAJOR": 85, "SIGNIFICANT": 70, "MINOR": 50, "NICHE": 40, "UNKNOWN": 50
    },
    "industry_engagement": {
        "LEADERSHIP": 100, "ACTIVE": 80, "MODERATE": 60, "MINIMAL": 40, "NONE": 30, "UNKNOWN": 50
    },
    "management_stability": {
        "STABLE": 100, "MINOR_CHANGES": 75, "FREQUENT_CHANGES": 40, "UNKNOWN": 50
    },
    "corporate_structure": {
        "SIMPLE": 100, "MODERATE": 75, "COMPLEX": 50, "OPAQUE": 25, "UNKNOWN": 50
    },
    "safety_leadership": {
        "EXEMPLARY": 100, "STRONG": 85, "ADEQUATE": 65, "WEAK": 35, "UNKNOWN": 50
    },
    "safety_reporting": {
        "PROACTIVE": 100, "ADEQUATE": 75, "REACTIVE": 50, "MINIMAL": 30, "UNKNOWN": 50
    },
    
    # --- CYBER SIGNALS ---
    "tls_score": {
        "A+": 100, "A": 95, "B": 80, "C": 60, "D": 40, "F": 15, "UNKNOWN": 50
    },
    "email_auth": {
        "FULL": 100, "PARTIAL": 65, "NONE": 30, "UNKNOWN": 50
    },
    "security_headers": {
        "COMPLETE": 100, "PARTIAL": 65, "MINIMAL": 35, "NONE": 15, "UNKNOWN": 50
    },
    "cloud_infrastructure": {
        "ENTERPRISE": 100, "MAJOR": 85, "STANDARD": 65, "UNKNOWN": 50
    },
    "software_currency": {
        "CURRENT": 100, "MINOR_LAG": 80, "SIGNIFICANT_LAG": 50, "OUTDATED": 25, "UNKNOWN": 50
    },
    "cve_exposure": {
        "CLEAN": 100, "LOW": 80, "MODERATE": 55, "HIGH": 25, "CRITICAL": 10, "UNKNOWN": 50
    },
    "credential_exposure": {
        "NONE": 100, "HISTORICAL": 70, "RECENT": 35, "ACTIVE": 10, "UNKNOWN": 50
    },
    "dark_web": {
        "CLEAN": 100, "MENTIONS": 70, "TARGETED": 40, "ACTIVE": 15, "UNKNOWN": 50
    },
    "security_leadership": {
        "MATURE": 100, "DEVELOPING": 70, "BASIC": 45, "MINIMAL": 25, "UNKNOWN": 50
    },
    "security_hiring": {
        "ACTIVE": 100, "MODERATE": 70, "MINIMAL": 45, "NONE": 30, "UNKNOWN": 50
    },
    "privacy_policy": {
        "COMPREHENSIVE": 100, "ADEQUATE": 75, "BASIC": 50, "MINIMAL": 30, "NONE": 15, "UNKNOWN": 50
    },
    "developer_resources": {
        "EXTENSIVE": 100, "GOOD": 75, "BASIC": 50, "MINIMAL": 30, "UNKNOWN": 50
    },
    "vendor_risk_program": {
        "MATURE": 100, "ESTABLISHED": 80, "DEVELOPING": 55, "BASIC": 35, "NONE": 20, "UNKNOWN": 50
    },
    "partner_quality": {
        "PREMIUM": 100, "GOOD": 80, "STANDARD": 60, "CONCERNING": 35, "UNKNOWN": 50
    },
    "customer_quality": {
        "ENTERPRISE": 100, "DIVERSIFIED": 85, "CONCENTRATED": 60, "SINGLE": 35, "UNKNOWN": 50
    },
    "ir_capabilities": {
        "MATURE": 100, "ESTABLISHED": 80, "DEVELOPING": 55, "BASIC": 35, "NONE": 15, "UNKNOWN": 50
    },
    "network_centrality": {
        "LOW": 100, "MODERATE": 75, "HIGH": 50, "CRITICAL": 30, "UNKNOWN": 50
    },
    "second_degree": {
        "LOW": 100, "MODERATE": 70, "ELEVATED": 45, "HIGH": 25, "UNKNOWN": 50
    },
    "industry_body": {
        "MEMBER": 100, "ASSOCIATE": 70, "NONE": 40, "UNKNOWN": 50
    },
    "esg_cyber": {
        "LEADER": 100, "STRONG": 85, "AVERAGE": 65, "LAGGARD": 40, "NOT_RATED": 50, "UNKNOWN": 50
    },
    "technical_content": {
        "EXTENSIVE": 100, "GOOD": 80, "BASIC": 55, "MINIMAL": 35, "NONE": 20, "UNKNOWN": 50
    },
    
    # --- D&O SIGNALS ---
    "board_diversity": {
        "EXEMPLARY": 100, "GOOD": 80, "ADEQUATE": 60, "LIMITED": 40, "POOR": 20, "UNKNOWN": 50
    },
    "board_refreshment": {
        "BALANCED": 100, "ADEQUATE": 75, "STALE": 45, "ENTRENCHED": 25, "UNKNOWN": 50
    },
    "committee_structure": {
        "ROBUST": 100, "ADEQUATE": 75, "BASIC": 50, "WEAK": 30, "UNKNOWN": 50
    },
    "board_network": {
        "STRONG": 100, "ADEQUATE": 75, "LIMITED": 50, "ISOLATED": 30, "UNKNOWN": 50
    },
    "compensation_structure": {
        "ALIGNED": 100, "MOSTLY_ALIGNED": 80, "CONCERNING": 50, "MISALIGNED": 25, "UNKNOWN": 50
    },
    "shareholder_rights": {
        "STRONG": 100, "ADEQUATE": 75, "LIMITED": 50, "RESTRICTED": 25, "UNKNOWN": 50
    },
    "governance_rating": {
        "LEADER": 100, "STRONG": 85, "AVERAGE": 65, "LAGGARD": 40, "NOT_RATED": 50, "UNKNOWN": 50
    },
    "iss_governance": {
        "LOW_CONCERN": 100, "MODERATE": 70, "ELEVATED": 45, "HIGH_CONCERN": 25, "UNKNOWN": 50
    },
    "audit_opinion": {
        "UNQUALIFIED": 100, "QUALIFIED": 60, "ADVERSE": 20, "DISCLAIMER": 10, "UNKNOWN": 50
    },
    "revenue_recognition": {
        "LOW": 100, "MODERATE": 70, "ELEVATED": 45, "HIGH": 25, "UNKNOWN": 50
    },
    "internal_controls": {
        "EFFECTIVE": 100, "MINOR_WEAKNESS": 75, "MATERIAL_WEAKNESS": 40, "SIGNIFICANT_DEFICIENCY": 25, "UNKNOWN": 50
    },
    "filing_timeliness": {
        "TIMELY": 100, "LATE_MINOR": 80, "LATE_SIGNIFICANT": 50, "NT_FILED": 30, "UNKNOWN": 50
    },
    "accounting_quality": {
        "HIGH": 100, "ADEQUATE": 75, "CONCERNING": 45, "POOR": 25, "UNKNOWN": 50
    },
    "debt_covenant": {
        "COMPLIANT": 100, "TIGHT": 70, "WAIVER": 45, "VIOLATION": 20, "UNKNOWN": 50
    },
    "securities_litigation": {
        "CLEAN": 100, "SINGLE": 65, "MULTIPLE": 35, "SIGNIFICANT": 15, "UNKNOWN": 50
    },
    "derivative_litigation": {
        "CLEAN": 100, "SINGLE": 70, "MULTIPLE": 45, "SIGNIFICANT": 20, "UNKNOWN": 50
    },
    "pending_litigation": {
        "NONE": 100, "MINOR": 80, "MODERATE": 55, "SIGNIFICANT": 30, "MATERIAL": 15, "UNKNOWN": 50
    },
    "sec_enforcement": {
        "CLEAN": 100, "INQUIRY": 70, "INVESTIGATION": 45, "ACTION": 20, "SETTLED": 40, "UNKNOWN": 50
    },
    "whistleblower": {
        "NONE": 100, "HISTORICAL": 70, "PENDING": 40, "ACTIVE": 20, "UNKNOWN": 50
    },
    "executive_stability": {
        "STABLE": 100, "MINOR_CHANGES": 75, "SIGNIFICANT_CHANGES": 40, "UNKNOWN": 50
    },
    "executive_background": {
        "EXEMPLARY": 100, "STRONG": 85, "ADEQUATE": 65, "CONCERNING": 35, "UNKNOWN": 50
    },
    "cfo_quality": {
        "EXEMPLARY": 100, "STRONG": 85, "ADEQUATE": 65, "CONCERNING": 35, "UNKNOWN": 50
    },
    "leadership_visibility": {
        "HIGH": 100, "MODERATE": 75, "LOW": 50, "MINIMAL": 30, "UNKNOWN": 50
    },
    "insider_trading": {
        "BALANCED": 100, "MODERATE_SELLING": 75, "HEAVY_SELLING": 45, "CLUSTER_SELLING": 25, "UNKNOWN": 50
    },
    "analyst_coverage": {
        "EXTENSIVE": 100, "ADEQUATE": 80, "LIMITED": 55, "NONE": 35, "UNKNOWN": 50
    },
    "index_inclusion": {
        "SP500": 100, "MIDCAP": 85, "SMALLCAP": 70, "NONE": 50, "UNKNOWN": 50
    },
    "investor_quality": {
        "BLUE_CHIP": 100, "QUALITY": 85, "MIXED": 65, "CONCERNING": 40, "UNKNOWN": 50
    },
    "investor_relations": {
        "EXEMPLARY": 100, "STRONG": 85, "ADEQUATE": 65, "WEAK": 40, "UNKNOWN": 50
    },
    "press_release": {
        "PROFESSIONAL": 100, "ADEQUATE": 75, "SPARSE": 50, "CONCERNING": 30, "UNKNOWN": 50
    },
    "related_party": {
        "NONE": 100, "MINOR": 80, "MODERATE": 55, "SIGNIFICANT": 30, "CONCERNING": 15, "UNKNOWN": 50
    },
    "esg_rating": {
        "LEADER": 100, "STRONG": 85, "AVERAGE": 65, "LAGGARD": 40, "NOT_RATED": 50, "UNKNOWN": 50
    },
    "esg_reporting": {
        "COMPREHENSIVE": 100, "GOOD": 80, "BASIC": 55, "MINIMAL": 35, "NONE": 20, "UNKNOWN": 50
    },
    "credit_rating": {
        "AAA": 100, "AA": 95, "A": 88, "BBB": 75, "BB": 55, "B": 40, "CCC": 25, "CC": 15, "C": 10, "D": 5, "NR": 50, "UNKNOWN": 50
    },
    
    # --- ENERGY SIGNALS ---
    "osha_violations": {
        "CLEAN": 100, "LOW": 80, "MODERATE": 55, "HIGH": 30, "SEVERE": 15, "UNKNOWN": 50
    },
    "fatality": {
        "CLEAN": 100, "SINGLE": 50, "MULTIPLE": 20, "UNKNOWN": 50
    },
    "near_miss": {
        "PROACTIVE": 100, "ADEQUATE": 75, "REACTIVE": 50, "MINIMAL": 30, "UNKNOWN": 50
    },
    "process_safety": {
        "EXCELLENT": 100, "GOOD": 85, "ADEQUATE": 65, "CONCERNING": 40, "POOR": 20, "UNKNOWN": 50
    },
    "major_incident": {
        "CLEAN": 100, "SINGLE": 55, "MULTIPLE": 30, "SIGNIFICANT": 15, "UNKNOWN": 50
    },
    "bsee_incident": {
        "CLEAN": 100, "LOW": 80, "MODERATE": 55, "HIGH": 30, "UNKNOWN": 50
    },
    "hse_leadership": {
        "EXEMPLARY": 100, "STRONG": 85, "ADEQUATE": 65, "WEAK": 40, "UNKNOWN": 50
    },
    "epa_violation": {
        "CLEAN": 100, "LOW": 80, "MODERATE": 55, "HIGH": 30, "SEVERE": 15, "UNKNOWN": 50
    },
    "spill_history": {
        "CLEAN": 100, "LOW": 80, "MODERATE": 55, "HIGH": 30, "SEVERE": 15, "UNKNOWN": 50
    },
    "emissions_compliance": {
        "COMPLIANT": 100, "MINOR_ISSUES": 75, "MAJOR_ISSUES": 40, "NON_COMPLIANT": 20, "UNKNOWN": 50
    },
    "flaring": {
        "MINIMAL": 100, "LOW": 80, "MODERATE": 55, "HIGH": 35, "EXCESSIVE": 20, "UNKNOWN": 50
    },
    "methane": {
        "EXCELLENT": 100, "GOOD": 80, "ADEQUATE": 60, "CONCERNING": 35, "POOR": 20, "UNKNOWN": 50
    },
    "remediation": {
        "COMPLETE": 100, "ONGOING_SCHEDULE": 80, "ONGOING_DELAYED": 55, "REQUIRED": 35, "UNKNOWN": 50
    },
    "permit_status": {
        "COMPLIANT": 100, "MINOR_ISSUES": 75, "MAJOR_ISSUES": 45, "NON_COMPLIANT": 20, "UNKNOWN": 50
    },
    "production_consistency": {
        "STABLE": 100, "MODERATE": 75, "VOLATILE": 50, "DECLINING": 35, "UNKNOWN": 50
    },
    "maintenance_pattern": {
        "PROACTIVE": 100, "SCHEDULED": 85, "REACTIVE": 55, "DEFERRED": 35, "UNKNOWN": 50
    },
    "well_integrity": {
        "EXCELLENT": 100, "GOOD": 85, "ADEQUATE": 65, "CONCERNING": 40, "POOR": 20, "UNKNOWN": 50
    },
    "facility_activity": {
        "GROWTH": 100, "STABLE": 85, "DECLINING": 55, "MINIMAL": 35, "UNKNOWN": 50
    },
    "contractor_quality": {
        "PREMIUM": 100, "QUALIFIED": 80, "STANDARD": 60, "CONCERNING": 35, "UNKNOWN": 50
    },
    "complexity": {
        "LOW": 100, "MODERATE": 75, "HIGH": 50, "EXTREME": 30, "UNKNOWN": 50
    },
    "concentration": {
        "DIVERSIFIED": 100, "MODERATE": 75, "CONCENTRATED": 50, "SINGLE_ASSET": 30, "UNKNOWN": 50
    },
    "decommissioning": {
        "FUNDED": 100, "PARTIALLY_FUNDED": 70, "UNDERFUNDED": 40, "UNFUNDED": 20, "UNKNOWN": 50
    },
    "benchmark": {
        "ABOVE": 100, "AT": 80, "BELOW": 55, "SIGNIFICANTLY_BELOW": 30, "UNKNOWN": 50
    },
    "aro_coverage": {
        "FULLY_COVERED": 100, "MOSTLY_COVERED": 75, "PARTIALLY_COVERED": 50, "UNDERCOVERED": 25, "UNKNOWN": 50
    },
    "capex_trend": {
        "GROWING": 100, "STABLE": 80, "DECLINING": 55, "MINIMAL": 35, "UNKNOWN": 50
    },
    "restructuring": {
        "NONE": 100, "MINOR": 75, "SIGNIFICANT": 45, "MAJOR": 25, "BANKRUPTCY": 10, "UNKNOWN": 50
    },
    "insurance_history": {
        "CLEAN": 100, "MINOR_CLAIMS": 80, "MODERATE_CLAIMS": 55, "SIGNIFICANT_CLAIMS": 30, "UNKNOWN": 50
    },
    "credit": {
        "STRONG": 100, "ADEQUATE": 80, "TIGHT": 55, "RESTRICTED": 30, "UNKNOWN": 50
    },
    "regulator_relationship": {
        "EXCELLENT": 100, "GOOD": 85, "ADEQUATE": 65, "STRAINED": 40, "ADVERSARIAL": 20, "UNKNOWN": 50
    },
    "industry_presence": {
        "LEADER": 100, "SIGNIFICANT": 85, "MODERATE": 65, "LIMITED": 45, "MINIMAL": 30, "UNKNOWN": 50
    },
    "technical_hiring": {
        "AGGRESSIVE": 100, "ACTIVE": 80, "MODERATE": 60, "MINIMAL": 40, "FROZEN": 25, "UNKNOWN": 50
    },
    "disclosure_quality": {
        "EXEMPLARY": 100, "STRONG": 85, "ADEQUATE": 65, "LIMITED": 40, "POOR": 20, "UNKNOWN": 50
    },
    "safety_communication": {
        "PROACTIVE": 100, "GOOD": 80, "ADEQUATE": 60, "REACTIVE": 40, "MINIMAL": 25, "UNKNOWN": 50
    },
    
    # --- FINANCIAL INSTITUTIONS SIGNALS ---
    "examination_rating": {
        "1": 100, "2": 85, "3": 60, "4": 35, "5": 15, "UNKNOWN": 50
    },
    "enforcement_action": {
        "CLEAN": 100, "MOU": 65, "CONSENT_ORDER": 40, "CEASE_DESIST": 20, "UNKNOWN": 50
    },
    "informal_action": {
        "CLEAN": 100, "BOARD_RESOLUTION": 75, "MOU": 55, "MULTIPLE": 35, "UNKNOWN": 50
    },
    "bsa_aml": {
        "SATISFACTORY": 100, "NEEDS_IMPROVEMENT": 65, "DEFICIENT": 35, "CRITICAL": 15, "UNKNOWN": 50
    },
    "consumer_compliance": {
        "SATISFACTORY": 100, "NEEDS_IMPROVEMENT": 65, "DEFICIENT": 35, "UNKNOWN": 50
    },
    "fair_lending": {
        "COMPLIANT": 100, "MONITORING": 70, "CONCERN": 40, "VIOLATION": 15, "UNKNOWN": 50
    },
    "cra_rating": {
        "OUTSTANDING": 100, "SATISFACTORY": 80, "NEEDS_IMPROVEMENT": 45, "SUBSTANTIAL_NONCOMPLIANCE": 15, "UNKNOWN": 50
    },
    "liquidity": {
        "STRONG": 100, "SATISFACTORY": 80, "ADEQUATE": 60, "STRAINED": 35, "CRITICAL": 15, "UNKNOWN": 50
    },
    "earnings": {
        "STRONG": 100, "SATISFACTORY": 80, "ADEQUATE": 60, "WEAK": 35, "CRITICAL": 15, "UNKNOWN": 50
    },
    "interest_rate_risk": {
        "LOW": 100, "MODERATE": 75, "ELEVATED": 50, "HIGH": 30, "UNKNOWN": 50
    },
    "peer_benchmark": {
        "OUTPERFORMING": 100, "AT_PEER": 80, "BELOW_PEER": 55, "SIGNIFICANTLY_BELOW": 30, "UNKNOWN": 50
    },
    "asset_quality": {
        "STRONG": 100, "SATISFACTORY": 80, "FAIR": 55, "MARGINAL": 35, "UNSATISFACTORY": 15, "UNKNOWN": 50
    },
    "operational_incident": {
        "CLEAN": 100, "LOW": 80, "MODERATE": 55, "HIGH": 30, "UNKNOWN": 50
    },
    "network_exposure": {
        "LOW": 100, "MODERATE": 75, "ELEVATED": 50, "HIGH": 30, "UNKNOWN": 50
    },
    "vulnerability": {
        "LOW": 100, "MODERATE": 75, "ELEVATED": 50, "HIGH": 30, "CRITICAL": 15, "UNKNOWN": 50
    },
    "audit_committee": {
        "STRONG": 100, "ADEQUATE": 75, "BASIC": 50, "WEAK": 30, "UNKNOWN": 50
    },
    "risk_committee": {
        "ROBUST": 100, "ADEQUATE": 75, "BASIC": 50, "WEAK": 30, "NONE": 20, "UNKNOWN": 50
    },
    "litigation": {
        "CLEAN": 100, "LOW": 80, "MODERATE": 55, "HIGH": 30, "UNKNOWN": 50
    },
    "cfpb_complaint": {
        "LOW": 100, "MODERATE": 75, "ELEVATED": 50, "HIGH": 30, "UNKNOWN": 50
    },
    "bbb_complaint": {
        "LOW": 100, "MODERATE": 75, "ELEVATED": 50, "HIGH": 30, "UNKNOWN": 50
    },
    "community_presence": {
        "STRONG": 100, "MODERATE": 75, "LIMITED": 50, "MINIMAL": 30, "UNKNOWN": 50
    },
    "hiring_signals": {
        "GROWTH": 100, "STABLE": 80, "CONTRACTION": 50, "SIGNIFICANT_CUTS": 30, "UNKNOWN": 50
    },
    
    # --- PROFESSIONAL INDEMNITY SIGNALS ---
    "license_status": {
        "ACTIVE_GOOD_STANDING": 100, "ACTIVE_CONDITIONS": 70, "PROBATION": 40, "SUSPENDED": 15, "REVOKED": 5, "UNKNOWN": 50
    },
    "disciplinary_history": {
        "CLEAN": 100, "SINGLE": 65, "MULTIPLE": 35, "SIGNIFICANT": 15, "UNKNOWN": 50
    },
    "malpractice_record": {
        "CLEAN": 100, "SINGLE": 65, "MULTIPLE": 35, "SIGNIFICANT": 15, "UNKNOWN": 50
    },
    "ce_compliance": {
        "CURRENT": 100, "MINOR_DEFICIENCY": 75, "MAJOR_DEFICIENCY": 45, "NON_COMPLIANT": 20, "UNKNOWN": 50
    },
    "specialty_certification": {
        "BOARD_CERTIFIED": 100, "SPECIALTY": 85, "GENERAL": 70, "NONE": 50, "UNKNOWN": 50
    },
    "peer_review": {
        "PASS": 100, "PASS_WITH_DEFICIENCIES": 70, "FAIL": 30, "NOT_APPLICABLE": 75, "UNKNOWN": 50
    },
    "pcaob_standing": {
        "GOOD_STANDING": 100, "REMEDIATION": 60, "CENSURED": 30, "REVOKED": 10, "NOT_APPLICABLE": 75, "UNKNOWN": 50
    },
    "malpractice_suits": {
        "CLEAN": 100, "SINGLE": 65, "MULTIPLE": 35, "SIGNIFICANT": 15, "UNKNOWN": 50
    },
    "complaint_history": {
        "CLEAN": 100, "LOW": 80, "MODERATE": 55, "HIGH": 30, "UNKNOWN": 50
    },
    "fee_dispute": {
        "CLEAN": 100, "LOW": 80, "MODERATE": 55, "HIGH": 30, "UNKNOWN": 50
    },
    "fee_disputes_litigation": {
        "CLEAN": 100, "SINGLE": 70, "MULTIPLE": 40, "SIGNIFICANT": 20, "UNKNOWN": 50
    },
    "civil_litigation": {
        "CLEAN": 100, "SINGLE": 70, "MULTIPLE": 45, "SIGNIFICANT": 20, "UNKNOWN": 50
    },
    "regulatory_enforcement": {
        "CLEAN": 100, "MINOR": 75, "MODERATE": 50, "SIGNIFICANT": 25, "UNKNOWN": 50
    },
    "partner_stability": {
        "STABLE": 100, "MODERATE": 75, "VOLATILE": 45, "HIGHLY_VOLATILE": 25, "UNKNOWN": 50
    },
    "staff_retention": {
        "EXCELLENT": 100, "GOOD": 85, "ADEQUATE": 65, "CONCERNING": 40, "POOR": 25, "UNKNOWN": 50
    },
    "office_stability": {
        "STABLE": 100, "GROWING": 90, "CONSOLIDATING": 70, "UNSTABLE": 40, "UNKNOWN": 50
    },
    "succession_planning": {
        "ROBUST": 100, "ADEQUATE": 75, "BASIC": 50, "MINIMAL": 30, "NONE": 20, "UNKNOWN": 50
    },
    "financial_stability": {
        "STRONG": 100, "STABLE": 80, "ADEQUATE": 60, "STRAINED": 35, "DISTRESSED": 15, "UNKNOWN": 50
    },
    "work_quality": {
        "EXEMPLARY": 100, "STRONG": 85, "ADEQUATE": 65, "INCONSISTENT": 40, "POOR": 20, "UNKNOWN": 50
    },
    "outcome_patterns": {
        "EXCELLENT": 100, "ABOVE_AVERAGE": 85, "AVERAGE": 70, "BELOW_AVERAGE": 45, "POOR": 25, "UNKNOWN": 50
    },
    "practice_clarity": {
        "FOCUSED": 100, "DEFINED": 80, "BROAD": 60, "UNFOCUSED": 40, "UNKNOWN": 50
    },
    "diversity": {
        "EXEMPLARY": 100, "STRONG": 80, "ADEQUATE": 60, "LIMITED": 40, "POOR": 25, "UNKNOWN": 50
    },
    "bio_completeness": {
        "COMPLETE": 100, "MOSTLY_COMPLETE": 80, "PARTIAL": 55, "MINIMAL": 35, "MISSING": 20, "UNKNOWN": 50
    },
    "client_quality": {
        "PREMIUM": 100, "QUALITY": 85, "STANDARD": 65, "CONCERNING": 40, "UNKNOWN": 50
    },
    "client_reviews": {
        "EXCELLENT": 100, "POSITIVE": 85, "MIXED": 60, "NEGATIVE": 35, "UNKNOWN": 50
    },
    "referral_network": {
        "STRONG": 100, "MODERATE": 75, "LIMITED": 50, "WEAK": 30, "UNKNOWN": 50
    },
    "peer_ranking": {
        "TOP_TIER": 100, "RECOGNIZED": 80, "LISTED": 60, "UNLISTED": 40, "UNKNOWN": 50
    },
    "association_leadership": {
        "NATIONAL": 100, "STATE": 80, "LOCAL": 60, "MEMBER": 50, "NONE": 35, "UNKNOWN": 50
    },
    "thought_leadership": {
        "NATIONAL": 100, "REGIONAL": 80, "LOCAL": 60, "EMERGING": 45, "NONE": 30, "UNKNOWN": 50
    },
    "publications": {
        "PROLIFIC": 100, "ACTIVE": 80, "OCCASIONAL": 60, "RARE": 40, "NONE": 25, "UNKNOWN": 50
    },
    "panel_membership": {
        "MAJOR": 100, "STANDARD": 75, "LIMITED": 50, "NONE": 35, "UNKNOWN": 50
    },
    "community_involvement": {
        "EXTENSIVE": 100, "ACTIVE": 80, "MODERATE": 60, "LIMITED": 40, "NONE": 25, "UNKNOWN": 50
    },
    "website_quality": {
        "EXCELLENT": 100, "GOOD": 80, "BASIC": 55, "POOR": 30, "UNKNOWN": 50
    },
    "portal_security": {
        "ROBUST": 100, "ADEQUATE": 75, "BASIC": 50, "WEAK": 30, "NONE": 15, "UNKNOWN": 50
    },
}

# =============================================================================
# SIGNAL TO PROFILE MAPPING
# =============================================================================

SIGNAL_CONFIG: Dict[str, Dict[str, str]] = {
    # Marine signals
    "psc_detention": {"categorizer": "scoring_logic", "profile": "psc_detention"},
    "psc_deficiency": {"categorizer": "threshold_bucket", "profile": "deficiency_rate"},
    "class_status": {"categorizer": "scoring_logic", "profile": "class_status"},
    "ism_compliance": {"categorizer": "scoring_logic", "profile": "ism_compliance"},
    "casualty_history": {"categorizer": "scoring_logic", "profile": "clean_single_multiple_significant"},
    "total_loss": {"categorizer": "scoring_logic", "profile": "clean_single_multiple_significant"},
    "survey_compliance": {"categorizer": "scoring_logic", "profile": "survey_compliance"},
    "sanctions_status": {"categorizer": "scoring_logic", "profile": "sanctions_status"},
    "ownership_transparency": {"categorizer": "scoring_logic", "profile": "ownership_transparency"},
    "jurisdiction_risk": {"categorizer": "scoring_logic", "profile": "jurisdiction_risk"},
    "sts_pattern": {"categorizer": "scoring_logic", "profile": "none_occasional_frequent_high"},
    "historical_sanctions": {"categorizer": "scoring_logic", "profile": "clean_single_multiple_significant"},
    "ais_compliance": {"categorizer": "threshold_bucket", "profile": "compliance_pct"},
    "dark_activity": {"categorizer": "scoring_logic", "profile": "dark_activity"},
    "route_risk": {"categorizer": "scoring_logic", "profile": "route_risk"},
    "psc_region_exposure": {"categorizer": "scoring_logic", "profile": "low_moderate_elevated_high"},
    "operational_efficiency": {"categorizer": "threshold_bucket", "profile": "efficiency_pct"},
    "weather_routing": {"categorizer": "scoring_logic", "profile": "active_not_used"},
    "trading_pattern": {"categorizer": "enumeration", "profile": "trading_pattern"},
    "fleet_age": {"categorizer": "threshold_bucket", "profile": "fleet_age"},
    "fleet_age_band": {"categorizer": "enumeration", "profile": "age_band"},
    "fleet_stability": {"categorizer": "scoring_logic", "profile": "stable_moderate_volatile"},
    "vessel_quality": {"categorizer": "threshold_bucket", "profile": "quality_score"},
    "vessel_category": {"categorizer": "enumeration", "profile": "vessel_category"},
    "crew_certification": {"categorizer": "scoring_logic", "profile": "crew_certification"},
    "management_consistency": {"categorizer": "scoring_logic", "profile": "management_stability"},
    "classification_society": {"categorizer": "quality_tier", "profile": "classification_society"},
    "flag_state": {"categorizer": "scoring_logic", "profile": "flag_state"},
    "flag_state_quality": {"categorizer": "quality_tier", "profile": "flag_state"},
    "pi_club": {"categorizer": "quality_tier", "profile": "p_and_i_club"},
    "pi_claims_history": {"categorizer": "scoring_logic", "profile": "clean_low_moderate_high"},
    "credit_rating": {"categorizer": "scoring_logic", "profile": "credit_rating"},
    "banking_relationship": {"categorizer": "quality_tier", "profile": "bank_tier"},
    "charterer_quality": {"categorizer": "quality_tier", "profile": "charterer"},
    "technical_manager": {"categorizer": "quality_tier", "profile": "ship_manager"},
    "industry_association": {"categorizer": "scoring_logic", "profile": "tier1_tier2_none"},
    "port_relationship": {"categorizer": "scoring_logic", "profile": "excellent_good_adequate_poor"},
    "operator_type": {"categorizer": "enumeration", "profile": "operator_type"},
    "imo2020_compliance": {"categorizer": "scoring_logic", "profile": "compliant_partial_noncompliant"},
    "bwm_compliance": {"categorizer": "scoring_logic", "profile": "compliant_partial_noncompliant"},
    "cii_rating": {"categorizer": "scoring_logic", "profile": "cii_rating"},
    "environmental_incident": {"categorizer": "scoring_logic", "profile": "clean_single_multiple_significant"},
    "website_quality": {"categorizer": "scoring_logic", "profile": "website_quality"},
    "fleet_disclosure": {"categorizer": "scoring_logic", "profile": "disclosure_quality"},
    "sustainability_reporting": {"categorizer": "scoring_logic", "profile": "esg_reporting"},
    "safety_communication": {"categorizer": "scoring_logic", "profile": "safety_communication"},
    "crew_welfare": {"categorizer": "scoring_logic", "profile": "excellent_good_adequate_poor"},
    "industry_presence": {"categorizer": "scoring_logic", "profile": "industry_presence"},
    "vetting": {"categorizer": "threshold_bucket", "profile": "vetting_score"},
    "esg_rating": {"categorizer": "scoring_logic", "profile": "esg_rating"},
    
    # Additional mappings would continue for all 329 signals...
    # Each signal maps to a categorizer type and profile name
}

print(f"Defined {len(SCORING_LOGIC_PROFILES)} scoring logic profiles")
print(f"Defined {len(SIGNAL_CONFIG)} signal configurations")
