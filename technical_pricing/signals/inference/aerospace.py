"""
Aerospace Coverage Inference Functions

Inference functions for aerospace insurance signal features and categorical groups.
Total: 5 categorical groups + 41 signal features = 46 inference functions
"""

from .base import (
    register_inference,
    register_categorical_inference,
    InferenceResult,
    CategoricalResult,
    InferenceContext,
    simulate_score,
    simulate_choice,
    simulate_count,
    simulate_boolean,
    simulate_tier,
    simulate_rate,
    simulate_percentage,
    map_tier_to_score,
    map_count_to_score,
    map_boolean_to_score,
)

# =============================================================================
# CATEGORICAL GROUP INFERENCE
# =============================================================================

@register_categorical_inference("aerospace_operator_type_inference")
def aerospace_operator_type_inference(ctx: InferenceContext) -> CategoricalResult:
    """Infer operator type from regulatory filings and operational data."""
    categories = [
        "MAJOR_AIRLINE", "REGIONAL_AIRLINE", "LOW_COST_CARRIER", "CARGO_AIRLINE",
        "CHARTER_OPERATOR", "CORPORATE_FLIGHT", "HELICOPTER_OPERATOR", 
        "FLIGHT_SCHOOL", "PRIVATE_OWNER"
    ]
    weights = [0.15, 0.20, 0.15, 0.10, 0.12, 0.10, 0.08, 0.05, 0.05]
    
    category = simulate_choice(ctx.entity_id, "operator_type", categories, weights)
    
    return CategoricalResult(
        feature_id="operator_type",
        category=category,
        confidence=0.9,
        evidence=[f"Operator classified as {category} from FAA/EASA registry"],
        metadata={"source": "regulatory_registry"}
    )


@register_categorical_inference("aerospace_fleet_category_inference")
def aerospace_fleet_category_inference(ctx: InferenceContext) -> CategoricalResult:
    """Infer primary aircraft category in fleet."""
    categories = ["WIDEBODY", "NARROWBODY", "REGIONAL_JET", "TURBOPROP", 
                  "BUSINESS_JET", "HELICOPTER", "PISTON"]
    weights = [0.10, 0.35, 0.15, 0.12, 0.12, 0.10, 0.06]
    
    category = simulate_choice(ctx.entity_id, "fleet_category", categories, weights)
    
    return CategoricalResult(
        feature_id="fleet_category",
        category=category,
        confidence=0.95,
        evidence=[f"Fleet predominantly {category} aircraft"],
        metadata={"source": "fleet_database"}
    )


@register_categorical_inference("aerospace_fleet_size_inference")
def aerospace_fleet_size_inference(ctx: InferenceContext) -> CategoricalResult:
    """Infer fleet size classification."""
    categories = ["SINGLE", "MICRO", "SMALL", "MEDIUM", "LARGE", "MAJOR"]
    weights = [0.10, 0.15, 0.25, 0.25, 0.15, 0.10]
    
    category = simulate_choice(ctx.entity_id, "fleet_size", categories, weights)
    
    return CategoricalResult(
        feature_id="fleet_size",
        category=category,
        confidence=0.95,
        evidence=[f"Fleet size: {category}"],
        metadata={"source": "fleet_database"}
    )


@register_categorical_inference("aerospace_regulatory_framework_inference")
def aerospace_regulatory_framework_inference(ctx: InferenceContext) -> CategoricalResult:
    """Infer primary regulatory authority."""
    categories = ["FAA", "EASA", "CAA_UK", "TCCA", "CASA", "CAAC", "DGCA_INDIA", "OTHER_ICAO", "NON_ICAO"]
    weights = [0.30, 0.25, 0.08, 0.05, 0.05, 0.08, 0.05, 0.10, 0.04]
    
    category = simulate_choice(ctx.entity_id, "regulatory_framework", categories, weights)
    
    return CategoricalResult(
        feature_id="regulatory_framework",
        category=category,
        confidence=0.98,
        evidence=[f"Primary regulator: {category}"],
        metadata={"source": "regulatory_registry"}
    )


@register_categorical_inference("aerospace_iosa_status_inference")
def aerospace_iosa_status_inference(ctx: InferenceContext) -> CategoricalResult:
    """Infer IOSA registration status."""
    categories = ["REGISTERED", "EXPIRED", "NEVER_REGISTERED", "NOT_APPLICABLE"]
    weights = [0.50, 0.10, 0.25, 0.15]
    
    category = simulate_choice(ctx.entity_id, "iosa_status_cat", categories, weights)
    
    return CategoricalResult(
        feature_id="iosa_status",
        category=category,
        confidence=0.99,
        evidence=[f"IOSA status: {category}"],
        metadata={"source": "iata_registry"}
    )


# =============================================================================
# NETWORK AUTHORITY SIGNALS
# =============================================================================

@register_inference("aerospace_alliance_membership_inference")
def aerospace_alliance_membership_inference(ctx: InferenceContext) -> InferenceResult:
    """Infer airline alliance membership."""
    alliances = ["STAR_ALLIANCE", "ONEWORLD", "SKYTEAM", "VALUE_ALLIANCE", "NONE"]
    weights = [0.20, 0.15, 0.15, 0.10, 0.40]
    
    alliance = simulate_choice(ctx.entity_id, "alliance_membership", alliances, weights)
    
    scores = {"STAR_ALLIANCE": 92, "ONEWORLD": 90, "SKYTEAM": 88, "VALUE_ALLIANCE": 72, "NONE": 50}
    score = scores[alliance]
    
    return InferenceResult(
        signal_id="alliance_membership",
        score=score,
        category=alliance,
        evidence=[f"Alliance: {alliance}"],
        confidence=0.95,
        source="iata_registry"
    )


@register_inference("aerospace_codeshare_quality_inference")
def aerospace_codeshare_quality_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess quality of codeshare partners."""
    partner_count = simulate_count(ctx.entity_id, "codeshare_count", max_count=15, zero_weight=0.2)
    avg_safety = simulate_score(ctx.entity_id, "codeshare_quality", base_score=75, variance=15)
    
    if partner_count == 0:
        score = 50
        category = "NO_PARTNERS"
    elif avg_safety >= 85:
        score = 90
        category = "HIGH_QUALITY"
    elif avg_safety >= 70:
        score = 75
        category = "GOOD_QUALITY"
    else:
        score = 55
        category = "MIXED_QUALITY"
    
    return InferenceResult(
        signal_id="codeshare_quality",
        score=score,
        category=category,
        raw_value={"partner_count": partner_count, "avg_safety": avg_safety},
        evidence=[f"{partner_count} codeshare partners, avg safety: {avg_safety:.0f}"],
        confidence=0.85
    )


@register_inference("aerospace_lessor_quality_inference")
def aerospace_lessor_quality_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess aircraft lessor quality tier."""
    tiers = ["TIER_1", "TIER_2", "TIER_3", "OWNER"]
    tier = simulate_tier(ctx.entity_id, "lessor_quality", tiers)
    
    tier_scores = {"TIER_1": 92, "TIER_2": 80, "TIER_3": 65, "OWNER": 70}
    score = tier_scores[tier]
    
    lessors = {
        "TIER_1": ["AerCap", "GECAS", "Avolon", "SMBC"],
        "TIER_2": ["BBAM", "NAC", "ACG", "BOC Aviation"],
        "TIER_3": ["Regional Lessor"],
        "OWNER": ["Self-owned"]
    }
    
    return InferenceResult(
        signal_id="lessor_quality",
        score=score,
        category=tier,
        evidence=[f"Primary lessor tier: {tier}"],
        confidence=0.85,
        metadata={"example_lessors": lessors[tier]}
    )


@register_inference("aerospace_oem_relationship_inference")
def aerospace_oem_relationship_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess OEM relationships."""
    direct_customer = simulate_boolean(ctx.entity_id, "oem_direct", true_probability=0.6)
    has_backlog = simulate_boolean(ctx.entity_id, "oem_backlog", true_probability=0.5)
    
    if direct_customer:
        score = 90
        category = "DIRECT"
    elif has_backlog:
        score = 82
        category = "ACTIVE_ORDERS"
    else:
        score = 60
        category = "INDIRECT"
    
    return InferenceResult(
        signal_id="oem_relationship",
        score=score,
        category=category,
        evidence=[f"OEM relationship: {category}"],
        confidence=0.85
    )


@register_inference("aerospace_mro_quality_inference")
def aerospace_mro_quality_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess MRO provider quality."""
    tiers = ["OEM_NETWORK", "MAJOR_INDEPENDENT", "REGIONAL", "BASIC"]
    tier = simulate_tier(ctx.entity_id, "mro_quality", tiers)
    
    tier_scores = {"OEM_NETWORK": 92, "MAJOR_INDEPENDENT": 85, "REGIONAL": 72, "BASIC": 58}
    score = tier_scores[tier]
    
    return InferenceResult(
        signal_id="mro_quality",
        score=score,
        category=tier,
        evidence=[f"MRO tier: {tier}"],
        confidence=0.85
    )


# =============================================================================
# SAFETY RECORD SIGNALS
# =============================================================================

@register_inference("aerospace_accident_history_inference")
def aerospace_accident_history_inference(ctx: InferenceContext) -> InferenceResult:
    """Analyze accident history (10-year lookback)."""
    hull_losses = simulate_count(ctx.entity_id, "hull_losses", max_count=3, zero_weight=0.7)
    major_accidents = simulate_count(ctx.entity_id, "major_accidents", max_count=5, zero_weight=0.5)
    
    if hull_losses == 0 and major_accidents == 0:
        score, category = 100, "CLEAN"
    elif hull_losses == 0 and major_accidents <= 2:
        score, category = 85, "MINOR_INCIDENTS"
    elif hull_losses <= 1:
        score, category = 55, "HULL_LOSS"
    else:
        score, category = 25, "MULTIPLE_LOSSES"
    
    return InferenceResult(
        signal_id="accident_history",
        score=score,
        category=category,
        raw_value={"hull_losses": hull_losses, "major_accidents": major_accidents},
        evidence=[f"Hull losses: {hull_losses}, Major accidents: {major_accidents}"],
        confidence=0.95,
        source="asn_database"
    )


@register_inference("aerospace_incident_history_inference")
def aerospace_incident_history_inference(ctx: InferenceContext) -> InferenceResult:
    """Analyze serious incident history."""
    rate = simulate_rate(ctx.entity_id, "incident_rate", mean=1.2, std=0.8)
    
    if rate < 0.5:
        score, category = 95, "EXCELLENT"
    elif rate < 1.0:
        score, category = 82, "GOOD"
    elif rate < 2.0:
        score, category = 68, "AVERAGE"
    elif rate < 3.5:
        score, category = 50, "ELEVATED"
    else:
        score, category = 30, "HIGH"
    
    return InferenceResult(
        signal_id="incident_history",
        score=score,
        category=category,
        raw_value=rate,
        evidence=[f"Incident rate: {rate:.2f} per 1000 flights"],
        confidence=0.90
    )


@register_inference("aerospace_accident_rate_inference")
def aerospace_accident_rate_inference(ctx: InferenceContext) -> InferenceResult:
    """Calculate accident rate vs industry average."""
    operator_rate = simulate_rate(ctx.entity_id, "accident_rate_op", mean=0.8, std=0.6)
    industry_avg = 1.0
    ratio = operator_rate / industry_avg if industry_avg > 0 else 1.0
    
    if ratio < 0.5:
        score, category = 98, "EXCELLENT"
    elif ratio < 0.8:
        score, category = 88, "GOOD"
    elif ratio < 1.2:
        score, category = 75, "AVERAGE"
    elif ratio < 2.0:
        score, category = 55, "ELEVATED"
    else:
        score, category = 30, "HIGH_RISK"
    
    return InferenceResult(
        signal_id="accident_rate",
        score=score,
        category=category,
        raw_value={"operator_rate": operator_rate, "industry_avg": industry_avg},
        evidence=[f"Accident rate: {ratio:.2f}x industry average"],
        confidence=0.90
    )


@register_inference("aerospace_fatality_history_inference")
def aerospace_fatality_history_inference(ctx: InferenceContext) -> InferenceResult:
    """Analyze fatal accident history."""
    fatal_accidents = simulate_count(ctx.entity_id, "fatal_accidents", max_count=2, zero_weight=0.85)
    
    if fatal_accidents == 0:
        score, category = 100, "CLEAN"
    elif fatal_accidents == 1:
        score, category = 45, "SINGLE_FATAL"
    else:
        score, category = 15, "MULTIPLE_FATAL"
    
    return InferenceResult(
        signal_id="fatality_history",
        score=score,
        category=category,
        raw_value=fatal_accidents,
        evidence=[f"Fatal accidents (10yr): {fatal_accidents}"],
        confidence=0.98
    )


@register_inference("aerospace_investigation_findings_inference")
def aerospace_investigation_findings_inference(ctx: InferenceContext) -> InferenceResult:
    """Analyze investigation findings where operator was cited."""
    cited_as_cause = simulate_count(ctx.entity_id, "cited_cause", max_count=3, zero_weight=0.75)
    contributing = simulate_count(ctx.entity_id, "contributing", max_count=5, zero_weight=0.6)
    
    if cited_as_cause == 0 and contributing == 0:
        score, category = 95, "CLEAN"
    elif cited_as_cause == 0:
        score, category = 78, "CONTRIBUTING_ONLY"
    elif cited_as_cause <= 1:
        score, category = 55, "SINGLE_CITATION"
    else:
        score, category = 30, "MULTIPLE_CITATIONS"
    
    return InferenceResult(
        signal_id="investigation_findings",
        score=score,
        category=category,
        raw_value={"cited_as_cause": cited_as_cause, "contributing": contributing},
        evidence=[f"Cited as cause: {cited_as_cause}, Contributing: {contributing}"],
        confidence=0.90
    )


# =============================================================================
# REGULATORY COMPLIANCE SIGNALS
# =============================================================================

@register_inference("aerospace_certificate_status_inference")
def aerospace_certificate_status_inference(ctx: InferenceContext) -> InferenceResult:
    """Check operating certificate status."""
    statuses = ["ACTIVE", "ACTIVE_WITH_RESTRICTIONS", "PROVISIONAL", "SUSPENDED", "REVOKED"]
    weights = [0.70, 0.12, 0.08, 0.07, 0.03]
    status = simulate_choice(ctx.entity_id, "certificate_status", statuses, weights)
    
    scores = {"ACTIVE": 100, "ACTIVE_WITH_RESTRICTIONS": 70, "PROVISIONAL": 60, "SUSPENDED": 20, "REVOKED": 5}
    score = scores[status]
    
    return InferenceResult(
        signal_id="certificate_status",
        score=score,
        category=status,
        evidence=[f"Certificate status: {status}"],
        confidence=0.98,
        source="regulatory_registry"
    )


@register_inference("aerospace_enforcement_actions_inference")
def aerospace_enforcement_actions_inference(ctx: InferenceContext) -> InferenceResult:
    """Check regulatory enforcement actions."""
    actions = simulate_count(ctx.entity_id, "enforcement_count", max_count=8, zero_weight=0.6)
    fines = actions * simulate_score(ctx.entity_id, "fine_amount", base_score=50000, variance=30000)
    
    if actions == 0:
        score, category = 98, "CLEAN"
    elif actions <= 2 and fines < 100000:
        score, category = 80, "MINOR"
    elif actions <= 5:
        score, category = 55, "MODERATE"
    else:
        score, category = 30, "SIGNIFICANT"
    
    return InferenceResult(
        signal_id="enforcement_actions",
        score=score,
        category=category,
        raw_value={"actions": actions, "total_fines": fines},
        evidence=[f"Enforcement actions (5yr): {actions}, Fines: ${fines:,.0f}"],
        confidence=0.90
    )


@register_inference("aerospace_iosa_audit_status_inference")
def aerospace_iosa_audit_status_inference(ctx: InferenceContext) -> InferenceResult:
    """Check IOSA audit status."""
    statuses = ["REGISTERED", "EXPIRED_RECENT", "EXPIRED_OLD", "NEVER_REGISTERED", "WITHDRAWN"]
    weights = [0.55, 0.10, 0.08, 0.22, 0.05]
    status = simulate_choice(ctx.entity_id, "iosa_audit", statuses, weights)
    
    scores = {"REGISTERED": 95, "EXPIRED_RECENT": 72, "EXPIRED_OLD": 55, "NEVER_REGISTERED": 45, "WITHDRAWN": 35}
    score = scores[status]
    
    return InferenceResult(
        signal_id="iosa_audit_status",
        score=score,
        category=status,
        evidence=[f"IOSA status: {status}"],
        confidence=0.98,
        source="iata_registry"
    )


@register_inference("aerospace_ramp_inspection_inference")
def aerospace_ramp_inspection_inference(ctx: InferenceContext) -> InferenceResult:
    """Analyze SAFA/SACA ramp inspection results."""
    finding_rate = simulate_rate(ctx.entity_id, "ramp_finding_rate", mean=1.2, std=0.8)
    
    if finding_rate < 0.5:
        score, category = 95, "EXCELLENT"
    elif finding_rate < 1.0:
        score, category = 85, "GOOD"
    elif finding_rate < 2.0:
        score, category = 70, "AVERAGE"
    elif finding_rate < 3.0:
        score, category = 50, "ELEVATED"
    else:
        score, category = 30, "HIGH"
    
    return InferenceResult(
        signal_id="ramp_inspection",
        score=score,
        category=category,
        raw_value=finding_rate,
        evidence=[f"Ramp finding rate: {finding_rate:.2f}"],
        confidence=0.85
    )


@register_inference("aerospace_eu_safety_list_inference")
def aerospace_eu_safety_list_inference(ctx: InferenceContext) -> InferenceResult:
    """Check EU Air Safety List status."""
    statuses = ["NOT_LISTED", "PARTIAL_BAN", "FULL_BAN"]
    weights = [0.92, 0.05, 0.03]
    status = simulate_choice(ctx.entity_id, "eu_safety_list", statuses, weights)
    
    scores = {"NOT_LISTED": 100, "PARTIAL_BAN": 35, "FULL_BAN": 5}
    score = scores[status]
    
    return InferenceResult(
        signal_id="eu_safety_list",
        score=score,
        category=status,
        evidence=[f"EU Air Safety List: {status}"],
        confidence=0.99
    )


@register_inference("aerospace_state_safety_rating_inference")
def aerospace_state_safety_rating_inference(ctx: InferenceContext) -> InferenceResult:
    """Check ICAO USOAP audit results for state."""
    categories = ["CAT_1", "CAT_2", "NOT_ASSESSED"]
    weights = [0.70, 0.15, 0.15]
    category = simulate_choice(ctx.entity_id, "state_safety", categories, weights)
    
    scores = {"CAT_1": 95, "CAT_2": 50, "NOT_ASSESSED": 70}
    score = scores[category]
    
    return InferenceResult(
        signal_id="state_safety_rating",
        score=score,
        category=category,
        evidence=[f"State safety category: {category}"],
        confidence=0.95
    )


# =============================================================================
# OPERATIONAL QUALITY SIGNALS
# =============================================================================

@register_inference("aerospace_otp_score_inference")
def aerospace_otp_score_inference(ctx: InferenceContext) -> InferenceResult:
    """Analyze on-time performance."""
    otp = simulate_percentage(ctx.entity_id, "otp_score", mean=78, std=12)
    
    if otp >= 85:
        score, category = 92, "EXCELLENT"
    elif otp >= 75:
        score, category = 80, "GOOD"
    elif otp >= 65:
        score, category = 65, "AVERAGE"
    else:
        score, category = 45, "POOR"
    
    return InferenceResult(
        signal_id="otp_score",
        score=score,
        category=category,
        raw_value=otp,
        evidence=[f"On-time performance: {otp:.1f}%"],
        confidence=0.85
    )


@register_inference("aerospace_dispatch_reliability_inference")
def aerospace_dispatch_reliability_inference(ctx: InferenceContext) -> InferenceResult:
    """Analyze dispatch reliability."""
    reliability = simulate_percentage(ctx.entity_id, "dispatch_reliability", mean=97, std=3)
    
    if reliability >= 99:
        score, category = 95, "EXCELLENT"
    elif reliability >= 97:
        score, category = 85, "GOOD"
    elif reliability >= 95:
        score, category = 72, "AVERAGE"
    else:
        score, category = 55, "BELOW_AVERAGE"
    
    return InferenceResult(
        signal_id="dispatch_reliability",
        score=score,
        category=category,
        raw_value=reliability,
        evidence=[f"Dispatch reliability: {reliability:.1f}%"],
        confidence=0.85
    )


@register_inference("aerospace_crew_experience_inference")
def aerospace_crew_experience_inference(ctx: InferenceContext) -> InferenceResult:
    """Infer average crew experience."""
    avg_hours = simulate_score(ctx.entity_id, "crew_hours", base_score=8000, variance=4000)
    
    if avg_hours >= 10000:
        score, category = 92, "HIGHLY_EXPERIENCED"
    elif avg_hours >= 6000:
        score, category = 80, "EXPERIENCED"
    elif avg_hours >= 3000:
        score, category = 65, "MODERATE"
    else:
        score, category = 45, "LIMITED"
    
    return InferenceResult(
        signal_id="crew_experience",
        score=score,
        category=category,
        raw_value=avg_hours,
        evidence=[f"Average crew flight hours: {avg_hours:,.0f}"],
        confidence=0.70
    )


@register_inference("aerospace_training_indicators_inference")
def aerospace_training_indicators_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess training investment signals."""
    has_sim = simulate_boolean(ctx.entity_id, "has_simulator", true_probability=0.6)
    training_center = simulate_boolean(ctx.entity_id, "training_center", true_probability=0.4)
    
    if has_sim and training_center:
        score, category = 92, "ADVANCED"
    elif has_sim:
        score, category = 80, "GOOD"
    else:
        score, category = 62, "BASIC"
    
    return InferenceResult(
        signal_id="training_indicators",
        score=score,
        category=category,
        evidence=[f"Training: {category}"],
        confidence=0.75
    )


@register_inference("aerospace_operational_complexity_inference")
def aerospace_operational_complexity_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess fleet and route complexity."""
    complexity = simulate_choice(ctx.entity_id, "op_complexity", 
                                 ["LOW", "MODERATE", "HIGH", "VERY_HIGH"],
                                 [0.25, 0.40, 0.25, 0.10])
    
    scores = {"LOW": 88, "MODERATE": 78, "HIGH": 65, "VERY_HIGH": 52}
    score = scores[complexity]
    
    return InferenceResult(
        signal_id="operational_complexity",
        score=score,
        category=complexity,
        evidence=[f"Operational complexity: {complexity}"],
        confidence=0.80
    )


@register_inference("aerospace_growth_rate_inference")
def aerospace_growth_rate_inference(ctx: InferenceContext) -> InferenceResult:
    """Analyze fleet/capacity growth rate."""
    growth = simulate_percentage(ctx.entity_id, "growth_rate", mean=5, std=10)
    
    if growth < 0:
        score, category = 70, "CONTRACTING"
    elif growth <= 5:
        score, category = 90, "STABLE"
    elif growth <= 15:
        score, category = 78, "MODERATE_GROWTH"
    elif growth <= 25:
        score, category = 60, "RAPID_GROWTH"
    else:
        score, category = 45, "AGGRESSIVE_GROWTH"
    
    return InferenceResult(
        signal_id="growth_rate",
        score=score,
        category=category,
        raw_value=growth,
        evidence=[f"YoY growth: {growth:.1f}%"],
        confidence=0.85
    )


# =============================================================================
# FLEET QUALITY SIGNALS
# =============================================================================

@register_inference("aerospace_fleet_age_inference")
def aerospace_fleet_age_inference(ctx: InferenceContext) -> InferenceResult:
    """Analyze fleet average age."""
    age = simulate_score(ctx.entity_id, "fleet_age", base_score=12, variance=8)
    
    if age <= 5:
        score, category = 95, "NEW"
    elif age <= 10:
        score, category = 85, "MODERN"
    elif age <= 15:
        score, category = 72, "MATURE"
    elif age <= 20:
        score, category = 55, "AGING"
    else:
        score, category = 35, "OLD"
    
    return InferenceResult(
        signal_id="fleet_age",
        score=score,
        category=category,
        raw_value=age,
        evidence=[f"Average fleet age: {age:.1f} years"],
        confidence=0.95
    )


@register_inference("aerospace_fleet_homogeneity_inference")
def aerospace_fleet_homogeneity_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess fleet type standardization."""
    homogeneity = simulate_percentage(ctx.entity_id, "fleet_homogeneity", mean=70, std=20)
    
    if homogeneity >= 90:
        score, category = 95, "SINGLE_TYPE"
    elif homogeneity >= 70:
        score, category = 85, "STANDARDIZED"
    elif homogeneity >= 50:
        score, category = 70, "MIXED"
    else:
        score, category = 55, "DIVERSE"
    
    return InferenceResult(
        signal_id="fleet_homogeneity",
        score=score,
        category=category,
        raw_value=homogeneity,
        evidence=[f"Fleet homogeneity: {homogeneity:.0f}%"],
        confidence=0.90
    )


@register_inference("aerospace_aircraft_generation_inference")
def aerospace_aircraft_generation_inference(ctx: InferenceContext) -> InferenceResult:
    """Analyze percentage of current-generation aircraft."""
    current_gen_pct = simulate_percentage(ctx.entity_id, "aircraft_gen", mean=55, std=25)
    
    if current_gen_pct >= 80:
        score, category = 95, "LATEST_GEN"
    elif current_gen_pct >= 60:
        score, category = 85, "CURRENT_GEN"
    elif current_gen_pct >= 40:
        score, category = 70, "MIXED_GEN"
    else:
        score, category = 50, "LEGACY"
    
    return InferenceResult(
        signal_id="aircraft_generation",
        score=score,
        category=category,
        raw_value=current_gen_pct,
        evidence=[f"Current generation: {current_gen_pct:.0f}%"],
        confidence=0.90
    )


@register_inference("aerospace_order_backlog_inference")
def aerospace_order_backlog_inference(ctx: InferenceContext) -> InferenceResult:
    """Analyze fleet renewal pipeline."""
    has_backlog = simulate_boolean(ctx.entity_id, "order_backlog", true_probability=0.5)
    backlog_size = simulate_count(ctx.entity_id, "backlog_size", max_count=50, zero_weight=0.3) if has_backlog else 0
    
    if backlog_size >= 20:
        score, category = 92, "STRONG"
    elif backlog_size >= 5:
        score, category = 80, "MODERATE"
    elif backlog_size > 0:
        score, category = 68, "LIMITED"
    else:
        score, category = 55, "NONE"
    
    return InferenceResult(
        signal_id="order_backlog",
        score=score,
        category=category,
        raw_value=backlog_size,
        evidence=[f"Order backlog: {backlog_size} aircraft"],
        confidence=0.85
    )


@register_inference("aerospace_maintenance_indicators_inference")
def aerospace_maintenance_indicators_inference(ctx: InferenceContext) -> InferenceResult:
    """Infer maintenance quality."""
    quality = simulate_choice(ctx.entity_id, "maintenance_quality",
                              ["EXCELLENT", "GOOD", "AVERAGE", "BELOW_AVERAGE", "POOR"],
                              [0.20, 0.35, 0.30, 0.10, 0.05])
    
    scores = {"EXCELLENT": 95, "GOOD": 85, "AVERAGE": 72, "BELOW_AVERAGE": 55, "POOR": 35}
    score = scores[quality]
    
    return InferenceResult(
        signal_id="maintenance_indicators",
        score=score,
        category=quality,
        evidence=[f"Maintenance quality: {quality}"],
        confidence=0.75
    )


# =============================================================================
# FINANCIAL STABILITY SIGNALS
# =============================================================================

@register_inference("aerospace_credit_rating_inference")
def aerospace_credit_rating_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess credit rating."""
    ratings = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "NOT_RATED"]
    weights = [0.02, 0.08, 0.15, 0.25, 0.20, 0.15, 0.05, 0.10]
    rating = simulate_choice(ctx.entity_id, "credit_rating", ratings, weights)
    
    scores = {"AAA": 100, "AA": 95, "A": 88, "BBB": 78, "BB": 62, "B": 45, "CCC": 25, "NOT_RATED": 55}
    score = scores[rating]
    
    return InferenceResult(
        signal_id="credit_rating",
        score=score,
        category=rating,
        evidence=[f"Credit rating: {rating}"],
        confidence=0.95
    )


@register_inference("aerospace_public_financials_inference")
def aerospace_public_financials_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess public financial health."""
    score = simulate_score(ctx.entity_id, "public_financials", base_score=68, variance=20)
    
    if score >= 85:
        category = "STRONG"
    elif score >= 70:
        category = "STABLE"
    elif score >= 55:
        category = "ADEQUATE"
    else:
        category = "WEAK"
    
    return InferenceResult(
        signal_id="public_financials",
        score=score,
        category=category,
        evidence=[f"Financial health: {category}"],
        confidence=0.80
    )


@register_inference("aerospace_market_position_inference")
def aerospace_market_position_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess market share and competitive position."""
    positions = ["LEADER", "MAJOR", "ESTABLISHED", "NICHE", "EMERGING"]
    weights = [0.10, 0.20, 0.35, 0.25, 0.10]
    position = simulate_choice(ctx.entity_id, "market_position", positions, weights)
    
    scores = {"LEADER": 95, "MAJOR": 85, "ESTABLISHED": 75, "NICHE": 65, "EMERGING": 55}
    score = scores[position]
    
    return InferenceResult(
        signal_id="market_position",
        score=score,
        category=position,
        evidence=[f"Market position: {position}"],
        confidence=0.85
    )


@register_inference("aerospace_government_support_inference")
def aerospace_government_support_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess state ownership or support."""
    support_level = simulate_choice(ctx.entity_id, "govt_support",
                                    ["FULL_STATE", "MAJORITY_STATE", "MINORITY_STATE", "IMPLICIT", "NONE"],
                                    [0.05, 0.10, 0.15, 0.20, 0.50])
    
    scores = {"FULL_STATE": 85, "MAJORITY_STATE": 80, "MINORITY_STATE": 75, "IMPLICIT": 70, "NONE": 65}
    score = scores[support_level]
    
    return InferenceResult(
        signal_id="government_support",
        score=score,
        category=support_level,
        evidence=[f"Government support: {support_level}"],
        confidence=0.90
    )


# =============================================================================
# ROUTE RISK SIGNALS
# =============================================================================

@register_inference("aerospace_conflict_zone_exposure_inference")
def aerospace_conflict_zone_exposure_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess exposure to conflict zones."""
    exposure = simulate_choice(ctx.entity_id, "conflict_exposure",
                               ["NONE", "MINIMAL", "MODERATE", "SIGNIFICANT", "HIGH"],
                               [0.50, 0.25, 0.15, 0.07, 0.03])
    
    scores = {"NONE": 100, "MINIMAL": 88, "MODERATE": 70, "SIGNIFICANT": 45, "HIGH": 20}
    score = scores[exposure]
    
    return InferenceResult(
        signal_id="conflict_zone_exposure",
        score=score,
        category=exposure,
        evidence=[f"Conflict zone exposure: {exposure}"],
        confidence=0.90
    )


@register_inference("aerospace_challenging_airports_inference")
def aerospace_challenging_airports_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess operations to challenging airports."""
    pct_challenging = simulate_percentage(ctx.entity_id, "challenging_airports", mean=15, std=12)
    
    if pct_challenging <= 5:
        score, category = 92, "LOW"
    elif pct_challenging <= 15:
        score, category = 80, "MODERATE"
    elif pct_challenging <= 30:
        score, category = 65, "ELEVATED"
    else:
        score, category = 48, "HIGH"
    
    return InferenceResult(
        signal_id="challenging_airports",
        score=score,
        category=category,
        raw_value=pct_challenging,
        evidence=[f"Challenging airports: {pct_challenging:.0f}% of destinations"],
        confidence=0.85
    )


@register_inference("aerospace_high_risk_destinations_inference")
def aerospace_high_risk_destinations_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess operations to high-risk countries."""
    pct_high_risk = simulate_percentage(ctx.entity_id, "high_risk_dest", mean=10, std=10)
    
    if pct_high_risk <= 5:
        score, category = 95, "LOW"
    elif pct_high_risk <= 15:
        score, category = 82, "MODERATE"
    elif pct_high_risk <= 30:
        score, category = 62, "ELEVATED"
    else:
        score, category = 40, "HIGH"
    
    return InferenceResult(
        signal_id="high_risk_destinations",
        score=score,
        category=category,
        raw_value=pct_high_risk,
        evidence=[f"High-risk destinations: {pct_high_risk:.0f}%"],
        confidence=0.88
    )


@register_inference("aerospace_weather_exposure_inference")
def aerospace_weather_exposure_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess route exposure to severe weather."""
    exposure = simulate_choice(ctx.entity_id, "weather_exposure",
                               ["LOW", "MODERATE", "HIGH", "EXTREME"],
                               [0.35, 0.40, 0.20, 0.05])
    
    scores = {"LOW": 90, "MODERATE": 78, "HIGH": 62, "EXTREME": 45}
    score = scores[exposure]
    
    return InferenceResult(
        signal_id="weather_exposure",
        score=score,
        category=exposure,
        evidence=[f"Weather exposure: {exposure}"],
        confidence=0.82
    )


@register_inference("aerospace_terrain_exposure_inference")
def aerospace_terrain_exposure_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess operations in mountainous terrain."""
    exposure = simulate_choice(ctx.entity_id, "terrain_exposure",
                               ["STANDARD", "CHALLENGING", "MOUNTAINOUS", "EXTREME"],
                               [0.45, 0.30, 0.20, 0.05])
    
    scores = {"STANDARD": 90, "CHALLENGING": 75, "MOUNTAINOUS": 58, "EXTREME": 42}
    score = scores[exposure]
    
    return InferenceResult(
        signal_id="terrain_exposure",
        score=score,
        category=exposure,
        evidence=[f"Terrain exposure: {exposure}"],
        confidence=0.85
    )


# =============================================================================
# CORPORATE GOVERNANCE SIGNALS
# =============================================================================

@register_inference("aerospace_management_stability_inference")
def aerospace_management_stability_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess CEO/COO tenure and turnover."""
    avg_tenure = simulate_score(ctx.entity_id, "mgmt_tenure", base_score=5, variance=3)
    
    if avg_tenure >= 7:
        score, category = 92, "STABLE"
    elif avg_tenure >= 4:
        score, category = 80, "ESTABLISHED"
    elif avg_tenure >= 2:
        score, category = 65, "MODERATE"
    else:
        score, category = 45, "HIGH_TURNOVER"
    
    return InferenceResult(
        signal_id="management_stability",
        score=score,
        category=category,
        raw_value=avg_tenure,
        evidence=[f"Average executive tenure: {avg_tenure:.1f} years"],
        confidence=0.85
    )


@register_inference("aerospace_safety_leadership_inference")
def aerospace_safety_leadership_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess dedicated safety leadership presence."""
    has_cso = simulate_boolean(ctx.entity_id, "has_cso", true_probability=0.7)
    visible = simulate_boolean(ctx.entity_id, "safety_visible", true_probability=0.6)
    
    if has_cso and visible:
        score, category = 95, "STRONG"
    elif has_cso:
        score, category = 80, "PRESENT"
    else:
        score, category = 55, "LIMITED"
    
    return InferenceResult(
        signal_id="safety_leadership",
        score=score,
        category=category,
        evidence=[f"Safety leadership: {category}"],
        confidence=0.80
    )


@register_inference("aerospace_safety_reporting_inference")
def aerospace_safety_reporting_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess public safety reporting and disclosure."""
    quality = simulate_choice(ctx.entity_id, "safety_reporting",
                              ["COMPREHENSIVE", "STANDARD", "LIMITED", "MINIMAL"],
                              [0.25, 0.40, 0.25, 0.10])
    
    scores = {"COMPREHENSIVE": 92, "STANDARD": 78, "LIMITED": 60, "MINIMAL": 40}
    score = scores[quality]
    
    return InferenceResult(
        signal_id="safety_reporting",
        score=score,
        category=quality,
        evidence=[f"Safety reporting: {quality}"],
        confidence=0.78
    )


@register_inference("aerospace_corporate_structure_inference")
def aerospace_corporate_structure_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess transparency of corporate structure."""
    transparency = simulate_choice(ctx.entity_id, "corp_structure",
                                   ["FULLY_TRANSPARENT", "MOSTLY_CLEAR", "PARTIAL", "OPAQUE"],
                                   [0.35, 0.40, 0.18, 0.07])
    
    scores = {"FULLY_TRANSPARENT": 95, "MOSTLY_CLEAR": 82, "PARTIAL": 62, "OPAQUE": 38}
    score = scores[transparency]
    
    return InferenceResult(
        signal_id="corporate_structure",
        score=score,
        category=transparency,
        evidence=[f"Corporate structure transparency: {transparency}"],
        confidence=0.85
    )


@register_inference("aerospace_industry_engagement_inference")
def aerospace_industry_engagement_inference(ctx: InferenceContext) -> InferenceResult:
    """Assess participation in industry safety groups."""
    engagement = simulate_choice(ctx.entity_id, "industry_engagement",
                                 ["ACTIVE_LEADER", "ACTIVE_MEMBER", "PASSIVE", "NONE"],
                                 [0.15, 0.40, 0.30, 0.15])
    
    scores = {"ACTIVE_LEADER": 95, "ACTIVE_MEMBER": 82, "PASSIVE": 65, "NONE": 48}
    score = scores[engagement]
    
    return InferenceResult(
        signal_id="industry_engagement",
        score=score,
        category=engagement,
        evidence=[f"Industry engagement: {engagement}"],
        confidence=0.80
    )
