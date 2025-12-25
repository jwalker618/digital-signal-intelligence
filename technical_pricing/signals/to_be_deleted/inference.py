"""
inference_functions.py - DSI Signal Inference Orchestration

Inference functions orchestrate the data flow for each signal feature:
    Extractor(s) → Aggregator → Score

Key Design Principles:
1. One inference function per signal feature (referenced by name in config)
2. Inference functions return scores (0-100), NOT modifiers or tier decisions
3. Modifiers, weights, and tier logic are applied by utility functions
4. Inference functions are stateless - they receive entity_id and return score

Example Config Reference:
```yaml
signal_features:
  network_authority:
    - id: "alliance_membership"
      name: "Airline Alliance Membership"
      weight: 0.25  # Weight applied by CompositeScorer, not here
      inference_function: "alliance_membership_inference"
```
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

# =============================================================================
# REGISTRY
# =============================================================================

INFERENCE_REGISTRY: Dict[str, Callable] = {}


def register_inference(name: str):
    """Decorator to register inference functions by name."""
    def decorator(func: Callable) -> Callable:
        INFERENCE_REGISTRY[name] = func
        return func
    return decorator


def get_inference_function(name: str) -> Optional[Callable]:
    """Retrieve an inference function by name."""
    return INFERENCE_REGISTRY.get(name)


def list_inference_functions() -> List[str]:
    """List all registered inference function names."""
    return list(INFERENCE_REGISTRY.keys())


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class InferenceResult:
    """
    Standardized result from an inference function.
    
    Note: Does NOT include modifiers or weights - those come from config
    and are applied by utility functions.
    """
    signal_id: str
    score: float                      # 0-100 scale
    category: Optional[str] = None    # e.g., "STAR_ALLIANCE"
    evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0
    source_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "score": self.score,
            "category": self.category,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "metadata": self.metadata,
        }


@dataclass
class InferenceContext:
    """
    Context passed to inference functions.
    
    Contains entity identification and any pre-fetched data that can be
    shared across multiple inference functions.
    """
    entity_id: str                    # Primary identifier (e.g., ICAO code, company name)
    entity_name: Optional[str] = None
    domain: Optional[str] = None
    coverage: str = ""
    cov_configuration: str = ""
    cached_data: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# AEROSPACE INFERENCE FUNCTIONS
# =============================================================================

# -----------------------------------------------------------------------------
# Network Authority Signals
# -----------------------------------------------------------------------------

@register_inference("alliance_membership_inference")
def alliance_membership_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Infer airline alliance membership from IATA registry and public sources.
    
    Score mapping:
        Star Alliance, oneworld, SkyTeam member: 85-95
        Value Alliance, affiliate: 65-75
        No alliance membership: 40-55
        Unknown: 50
    """
    # In production: IATARegistryExtractor().extract(ctx.entity_id)
    # For stub: simulate based on entity
    
    alliance_data = _simulate_alliance_lookup(ctx.entity_id)
    
    if alliance_data["alliance"] in ["STAR_ALLIANCE", "ONEWORLD", "SKYTEAM"]:
        score = 90
        category = alliance_data["alliance"]
        evidence = [f"Member of {alliance_data['alliance']} since {alliance_data.get('since', 'unknown')}"]
    elif alliance_data["alliance"] in ["VALUE_ALLIANCE", "U-FLY_ALLIANCE"]:
        score = 70
        category = alliance_data["alliance"]
        evidence = [f"Member of {alliance_data['alliance']}"]
    elif alliance_data["alliance"] == "NONE":
        score = 50
        category = "UNAFFILIATED"
        evidence = ["No alliance membership identified"]
    else:
        score = 50
        category = "UNKNOWN"
        evidence = ["Alliance status could not be determined"]

    return InferenceResult(
        signal_id="alliance_membership",
        score=score,
        category=category,
        evidence=evidence,
        confidence=alliance_data.get("confidence", 0.9),
        metadata=alliance_data
    )


@register_inference("codeshare_quality_inference")
def codeshare_quality_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Assess quality of codeshare partners based on their safety ratings.
    
    Aggregates safety scores of all codeshare partners.
    """
    # Simulate codeshare partner lookup
    partners = _simulate_codeshare_partners(ctx.entity_id)
    
    if not partners:
        return InferenceResult(
            signal_id="codeshare_quality",
            score=50,
            category="NO_PARTNERS",
            evidence=["No codeshare partners identified"],
            confidence=0.7
        )
    
    # Average safety rating of partners
    avg_rating = sum(p["safety_score"] for p in partners) / len(partners)
    score = min(100, max(0, avg_rating))
    
    return InferenceResult(
        signal_id="codeshare_quality",
        score=round(score, 1),
        category="HIGH" if score >= 80 else "MEDIUM" if score >= 60 else "LOW",
        evidence=[f"{len(partners)} codeshare partners, avg safety: {score:.0f}"],
        confidence=0.85,
        metadata={"partner_count": len(partners), "partners": partners}
    )


@register_inference("lessor_quality_inference")
def lessor_quality_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Assess quality tier of aircraft lessors.
    
    Tier 1 (AerCap, GECAS, Avolon): 90-95
    Tier 2 (BBAM, NAC, ACG): 75-85
    Tier 3 (Others): 60-70
    Owner-operated: 70
    """
    lessor_data = _simulate_lessor_lookup(ctx.entity_id)
    
    tier_scores = {"TIER_1": 92, "TIER_2": 80, "TIER_3": 65, "OWNER": 70, "UNKNOWN": 55}
    score = tier_scores.get(lessor_data.get("tier", "UNKNOWN"), 55)
    
    return InferenceResult(
        signal_id="lessor_quality",
        score=score,
        category=lessor_data.get("tier", "UNKNOWN"),
        evidence=[f"Primary lessor: {lessor_data.get('lessor', 'unknown')}"],
        confidence=lessor_data.get("confidence", 0.8),
        metadata=lessor_data
    )


@register_inference("oem_relationship_inference")
def oem_relationship_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Assess direct relationships with OEMs (Boeing, Airbus, Embraer).
    """
    oem_data = _simulate_oem_relationship(ctx.entity_id)
    
    if oem_data.get("direct_customer"):
        score = 90
        category = "DIRECT"
        evidence = [f"Direct customer of {', '.join(oem_data.get('oems', []))}"]
    elif oem_data.get("order_backlog"):
        score = 85
        category = "ACTIVE_ORDERS"
        evidence = ["Active order backlog with OEMs"]
    else:
        score = 60
        category = "INDIRECT"
        evidence = ["No direct OEM relationship identified"]
    
    return InferenceResult(
        signal_id="oem_relationship",
        score=score,
        category=category,
        evidence=evidence,
        confidence=0.85,
        metadata=oem_data
    )


@register_inference("mro_quality_inference")
def mro_quality_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Assess quality of MRO providers.
    
    OEM-approved/major independent: 85-95
    Regional certified: 70-80
    Basic/unknown: 50-65
    """
    mro_data = _simulate_mro_lookup(ctx.entity_id)
    
    tier_scores = {"OEM_NETWORK": 92, "MAJOR_INDEPENDENT": 85, "REGIONAL": 72, "BASIC": 58}
    score = tier_scores.get(mro_data.get("tier", "BASIC"), 58)
    
    return InferenceResult(
        signal_id="mro_quality",
        score=score,
        category=mro_data.get("tier", "UNKNOWN"),
        evidence=[f"MRO provider: {mro_data.get('provider', 'unknown')}"],
        confidence=0.8,
        metadata=mro_data
    )


# -----------------------------------------------------------------------------
# Safety Record Signals
# -----------------------------------------------------------------------------

@register_inference("accident_history_inference")
def accident_history_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Analyze accident history from ASN, NTSB, and ICAO databases.
    
    10-year lookback for hull losses and major accidents.
    """
    accident_data = _simulate_accident_lookup(ctx.entity_id)
    
    hull_losses = accident_data.get("hull_losses", 0)
    major_accidents = accident_data.get("major_accidents", 0)
    
    # Scoring: 100 for clean record, decreasing with incidents
    if hull_losses == 0 and major_accidents == 0:
        score = 100
        category = "CLEAN"
    elif hull_losses == 0 and major_accidents <= 2:
        score = 85
        category = "MINOR_INCIDENTS"
    elif hull_losses <= 1:
        score = 60
        category = "HULL_LOSS"
    else:
        score = 30
        category = "MULTIPLE_LOSSES"
    
    return InferenceResult(
        signal_id="accident_history",
        score=score,
        category=category,
        evidence=[
            f"Hull losses (10yr): {hull_losses}",
            f"Major accidents: {major_accidents}"
        ],
        confidence=0.95,
        metadata=accident_data
    )


@register_inference("incident_history_inference")
def incident_history_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Analyze incident history - runway excursions, near-misses, serious incidents.
    """
    incident_data = _simulate_incident_lookup(ctx.entity_id)
    
    incidents = incident_data.get("serious_incidents", 0)
    normalized_rate = incident_data.get("rate_per_1000_flights", 0)
    
    if normalized_rate < 0.5:
        score = 95
        category = "EXCELLENT"
    elif normalized_rate < 1.0:
        score = 82
        category = "GOOD"
    elif normalized_rate < 2.0:
        score = 68
        category = "AVERAGE"
    elif normalized_rate < 3.5:
        score = 50
        category = "ELEVATED"
    else:
        score = 30
        category = "HIGH"
    
    return InferenceResult(
        signal_id="incident_history",
        score=score,
        category=category,
        evidence=[f"Incident rate: {normalized_rate:.2f} per 1000 flights"],
        confidence=0.9,
        metadata=incident_data
    )


@register_inference("accident_rate_inference")
def accident_rate_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Calculate accident rate vs industry average.
    """
    rate_data = _simulate_accident_rate(ctx.entity_id)
    
    operator_rate = rate_data.get("operator_rate", 0)
    industry_avg = rate_data.get("industry_avg", 1.0)
    
    if industry_avg > 0:
        ratio = operator_rate / industry_avg
    else:
        ratio = 1.0
    
    if ratio < 0.5:
        score = 98
        category = "EXCELLENT"
    elif ratio < 0.8:
        score = 88
        category = "GOOD"
    elif ratio < 1.2:
        score = 75
        category = "AVERAGE"
    elif ratio < 2.0:
        score = 55
        category = "ELEVATED"
    else:
        score = 30
        category = "HIGH_RISK"
    
    return InferenceResult(
        signal_id="accident_rate",
        score=score,
        category=category,
        evidence=[f"Accident rate {ratio:.2f}x industry average"],
        confidence=0.9,
        metadata=rate_data
    )


@register_inference("fatality_history_inference")
def fatality_history_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Analyze fatal accident history (10-year lookback).
    """
    fatality_data = _simulate_fatality_lookup(ctx.entity_id)
    
    fatal_accidents = fatality_data.get("fatal_accidents", 0)
    
    if fatal_accidents == 0:
        score = 100
        category = "CLEAN"
    elif fatal_accidents == 1:
        score = 50
        category = "SINGLE_FATAL"
    else:
        score = 20
        category = "MULTIPLE_FATAL"
    
    return InferenceResult(
        signal_id="fatality_history",
        score=score,
        category=category,
        evidence=[f"Fatal accidents (10yr): {fatal_accidents}"],
        confidence=0.98,
        metadata=fatality_data
    )


@register_inference("investigation_findings_inference")
def investigation_findings_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Analyze whether operator was cited as causal factor in investigations.
    """
    investigation_data = _simulate_investigation_lookup(ctx.entity_id)
    
    cited_as_cause = investigation_data.get("cited_as_cause", 0)
    contributing_factors = investigation_data.get("contributing_factors", 0)
    
    if cited_as_cause == 0 and contributing_factors == 0:
        score = 95
        category = "CLEAN"
    elif cited_as_cause == 0:
        score = 78
        category = "CONTRIBUTING_ONLY"
    elif cited_as_cause <= 1:
        score = 55
        category = "SINGLE_CITATION"
    else:
        score = 30
        category = "MULTIPLE_CITATIONS"
    
    return InferenceResult(
        signal_id="investigation_findings",
        score=score,
        category=category,
        evidence=[
            f"Cited as cause: {cited_as_cause}",
            f"Contributing factors: {contributing_factors}"
        ],
        confidence=0.9,
        metadata=investigation_data
    )


# -----------------------------------------------------------------------------
# Regulatory Compliance Signals
# -----------------------------------------------------------------------------

@register_inference("certificate_status_inference")
def certificate_status_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Check operating certificate status (AOC/Part 121/135).
    """
    cert_data = _simulate_certificate_lookup(ctx.entity_id)
    
    status = cert_data.get("status", "UNKNOWN")
    
    status_scores = {
        "ACTIVE": 100,
        "ACTIVE_WITH_RESTRICTIONS": 70,
        "PROVISIONAL": 60,
        "SUSPENDED": 20,
        "REVOKED": 5,
        "UNKNOWN": 50
    }
    
    score = status_scores.get(status, 50)
    
    return InferenceResult(
        signal_id="certificate_status",
        score=score,
        category=status,
        evidence=[f"Certificate status: {status}"],
        confidence=0.95,
        metadata=cert_data
    )


@register_inference("enforcement_actions_inference")
def enforcement_actions_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Check regulatory enforcement actions (5-year lookback).
    """
    enforcement_data = _simulate_enforcement_lookup(ctx.entity_id)
    
    actions = enforcement_data.get("enforcement_count", 0)
    total_fines = enforcement_data.get("total_fines_usd", 0)
    
    if actions == 0:
        score = 98
        category = "CLEAN"
    elif actions <= 2 and total_fines < 100000:
        score = 80
        category = "MINOR"
    elif actions <= 5:
        score = 55
        category = "MODERATE"
    else:
        score = 30
        category = "SIGNIFICANT"
    
    return InferenceResult(
        signal_id="enforcement_actions",
        score=score,
        category=category,
        evidence=[
            f"Enforcement actions (5yr): {actions}",
            f"Total fines: ${total_fines:,.0f}"
        ],
        confidence=0.9,
        metadata=enforcement_data
    )


@register_inference("iosa_audit_status_inference")
def iosa_audit_status_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Check IOSA registration and audit status.
    """
    iosa_data = _simulate_iosa_lookup(ctx.entity_id)
    
    status = iosa_data.get("status", "UNKNOWN")
    
    if status == "REGISTERED":
        score = 95
        category = "REGISTERED"
        evidence = [f"IOSA registered, expires {iosa_data.get('expiry', 'unknown')}"]
    elif status == "EXPIRED_RECENT":
        score = 72
        category = "EXPIRED_RECENT"
        evidence = ["IOSA registration recently expired"]
    elif status == "EXPIRED_OLD":
        score = 55
        category = "EXPIRED_OLD"
        evidence = ["IOSA registration expired >1 year"]
    elif status == "NEVER_REGISTERED":
        score = 45
        category = "NEVER_REGISTERED"
        evidence = ["Never registered with IOSA"]
    else:
        score = 50
        category = "UNKNOWN"
        evidence = ["IOSA status unknown"]
    
    return InferenceResult(
        signal_id="iosa_audit_status",
        score=score,
        category=category,
        evidence=evidence,
        confidence=0.95,
        metadata=iosa_data
    )


@register_inference("ramp_inspection_inference")
def ramp_inspection_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Analyze SAFA/SACA ramp inspection results.
    """
    ramp_data = _simulate_ramp_inspection(ctx.entity_id)
    
    finding_rate = ramp_data.get("finding_rate", 0)
    
    if finding_rate < 0.5:
        score = 95
        category = "EXCELLENT"
    elif finding_rate < 1.0:
        score = 85
        category = "GOOD"
    elif finding_rate < 2.0:
        score = 70
        category = "AVERAGE"
    elif finding_rate < 3.0:
        score = 50
        category = "ELEVATED"
    else:
        score = 30
        category = "HIGH"
    
    return InferenceResult(
        signal_id="ramp_inspection",
        score=score,
        category=category,
        evidence=[f"Ramp finding rate: {finding_rate:.2f}"],
        confidence=0.85,
        metadata=ramp_data
    )


@register_inference("eu_safety_list_inference")
def eu_safety_list_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Check EU Air Safety List status.
    """
    eu_data = _simulate_eu_list_lookup(ctx.entity_id)
    
    status = eu_data.get("status", "NOT_LISTED")
    
    if status == "NOT_LISTED":
        score = 100
        category = "NOT_LISTED"
    elif status == "PARTIAL_BAN":
        score = 35
        category = "PARTIAL_BAN"
    elif status == "FULL_BAN":
        score = 5
        category = "FULL_BAN"
    else:
        score = 50
        category = "UNKNOWN"
    
    return InferenceResult(
        signal_id="eu_safety_list",
        score=score,
        category=category,
        evidence=[f"EU Air Safety List: {status}"],
        confidence=0.99,
        metadata=eu_data
    )


@register_inference("state_safety_rating_inference")
def state_safety_rating_inference(ctx: InferenceContext) -> InferenceResult:
    """
    Check ICAO USOAP audit results for state of registry.
    """
    state_data = _simulate_state_safety(ctx.entity_id)
    
    category = state_data.get("category", "UNKNOWN")
    score_map = {"CAT_1": 95, "CAT_2": 50, "NOT_ASSESSED": 70, "UNKNOWN": 60}
    score = score_map.get(category, 60)
    
    return InferenceResult(
        signal_id="state_safety_rating",
        score=score,
        category=category,
        evidence=[f"State safety category: {category}"],
        confidence=0.9,
        metadata=state_data
    )


# =============================================================================
# SIMULATION HELPERS (Replace with actual extractors in production)
# =============================================================================

def _simulate_alliance_lookup(entity_id: str) -> Dict[str, Any]:
    """Simulated alliance membership lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    alliances = ["STAR_ALLIANCE", "ONEWORLD", "SKYTEAM", "VALUE_ALLIANCE", "NONE", "NONE"]
    return {
        "alliance": alliances[seed % len(alliances)],
        "since": f"20{10 + (seed % 14)}",
        "confidence": 0.9
    }


def _simulate_codeshare_partners(entity_id: str) -> List[Dict[str, Any]]:
    """Simulated codeshare partner lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    count = (seed % 8) + 2
    return [
        {"name": f"Partner_{i}", "safety_score": 65 + ((seed + i) % 30)}
        for i in range(count)
    ]


def _simulate_lessor_lookup(entity_id: str) -> Dict[str, Any]:
    """Simulated lessor quality lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    tiers = ["TIER_1", "TIER_1", "TIER_2", "TIER_2", "TIER_3", "OWNER"]
    lessors = {"TIER_1": "AerCap", "TIER_2": "BBAM", "TIER_3": "Regional Lessor", "OWNER": "Self-owned"}
    tier = tiers[seed % len(tiers)]
    return {"tier": tier, "lessor": lessors[tier], "confidence": 0.85}


def _simulate_oem_relationship(entity_id: str) -> Dict[str, Any]:
    """Simulated OEM relationship lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    return {
        "direct_customer": seed % 3 != 0,
        "oems": ["Boeing", "Airbus"][:1 + (seed % 2)],
        "order_backlog": seed % 2 == 0
    }


def _simulate_mro_lookup(entity_id: str) -> Dict[str, Any]:
    """Simulated MRO provider lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    tiers = ["OEM_NETWORK", "MAJOR_INDEPENDENT", "MAJOR_INDEPENDENT", "REGIONAL", "BASIC"]
    providers = {"OEM_NETWORK": "Lufthansa Technik", "MAJOR_INDEPENDENT": "AAR", 
                 "REGIONAL": "Regional MRO", "BASIC": "Local Provider"}
    tier = tiers[seed % len(tiers)]
    return {"tier": tier, "provider": providers[tier]}


def _simulate_accident_lookup(entity_id: str) -> Dict[str, Any]:
    """Simulated accident history lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    return {
        "hull_losses": 0 if seed % 10 < 7 else (1 if seed % 10 < 9 else 2),
        "major_accidents": seed % 4
    }


def _simulate_incident_lookup(entity_id: str) -> Dict[str, Any]:
    """Simulated incident history lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    return {
        "serious_incidents": seed % 6,
        "rate_per_1000_flights": 0.3 + (seed % 30) / 10
    }


def _simulate_accident_rate(entity_id: str) -> Dict[str, Any]:
    """Simulated accident rate calculation."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    return {
        "operator_rate": 0.5 + (seed % 20) / 10,
        "industry_avg": 1.0
    }


def _simulate_fatality_lookup(entity_id: str) -> Dict[str, Any]:
    """Simulated fatality history lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    return {"fatal_accidents": 0 if seed % 10 < 8 else (1 if seed % 10 < 9 else 2)}


def _simulate_investigation_lookup(entity_id: str) -> Dict[str, Any]:
    """Simulated investigation findings lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    return {
        "cited_as_cause": 0 if seed % 8 < 6 else seed % 3,
        "contributing_factors": seed % 4
    }


def _simulate_certificate_lookup(entity_id: str) -> Dict[str, Any]:
    """Simulated certificate status lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    statuses = ["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE_WITH_RESTRICTIONS", "PROVISIONAL"]
    return {"status": statuses[seed % len(statuses)], "certificate_type": "AOC"}


def _simulate_enforcement_lookup(entity_id: str) -> Dict[str, Any]:
    """Simulated enforcement actions lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    return {
        "enforcement_count": seed % 5,
        "total_fines_usd": (seed % 10) * 25000
    }


def _simulate_iosa_lookup(entity_id: str) -> Dict[str, Any]:
    """Simulated IOSA lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    statuses = ["REGISTERED", "REGISTERED", "REGISTERED", "EXPIRED_RECENT", "NEVER_REGISTERED"]
    return {"status": statuses[seed % len(statuses)], "expiry": "2025-06-30"}


def _simulate_ramp_inspection(entity_id: str) -> Dict[str, Any]:
    """Simulated ramp inspection lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    return {"finding_rate": 0.5 + (seed % 25) / 10, "inspections": 20 + seed % 30}


def _simulate_eu_list_lookup(entity_id: str) -> Dict[str, Any]:
    """Simulated EU Air Safety List lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    return {"status": "NOT_LISTED" if seed % 20 < 18 else "PARTIAL_BAN"}


def _simulate_state_safety(entity_id: str) -> Dict[str, Any]:
    """Simulated state safety rating lookup."""
    import hashlib
    seed = int(hashlib.md5(entity_id.encode()).hexdigest()[:8], 16)
    categories = ["CAT_1", "CAT_1", "CAT_1", "CAT_2", "NOT_ASSESSED"]
    return {"category": categories[seed % len(categories)]}


# =============================================================================
# BATCH INFERENCE
# =============================================================================

def run_signal_inference(
    ctx: InferenceContext,
    signal_features: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, InferenceResult]:
    """
    Run inference for all signal features defined in configuration.
    
    Args:
        ctx: InferenceContext with entity information
        signal_features: Signal features from configuration
    
    Returns:
        Dict mapping signal_id to InferenceResult
    """
    results = {}
    
    for group_id, features in signal_features.items():
        for feature in features:
            signal_id = feature.get("id")
            inference_func_name = feature.get("inference_function")
            
            if not signal_id or not inference_func_name:
                continue
            
            inference_func = get_inference_function(inference_func_name)
            
            if inference_func:
                try:
                    result = inference_func(ctx)
                    results[signal_id] = result
                except Exception as e:
                    # Return default result on error
                    results[signal_id] = InferenceResult(
                        signal_id=signal_id,
                        score=50,
                        category="ERROR",
                        evidence=[f"Inference error: {str(e)}"],
                        confidence=0.0
                    )
            else:
                # No inference function registered
                results[signal_id] = InferenceResult(
                    signal_id=signal_id,
                    score=50,
                    category="NOT_IMPLEMENTED",
                    evidence=[f"No inference function: {inference_func_name}"],
                    confidence=0.0
                )
    
    return results


def extract_scores(inference_results: Dict[str, InferenceResult]) -> Dict[str, float]:
    """
    Extract just the scores from inference results for utility functions.
    """
    return {signal_id: result.score for signal_id, result in inference_results.items()}


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("DSI INFERENCE FUNCTIONS - DEMO")
    print("=" * 70)

    print(f"\nRegistered inference functions: {len(INFERENCE_REGISTRY)}")
    for name in sorted(INFERENCE_REGISTRY.keys()):
        print(f"  - {name}")

    print("\n" + "-" * 70)
    print("Running inference for 'Delta Air Lines'")
    print("-" * 70)

    ctx = InferenceContext(
        entity_id="DAL",
        entity_name="Delta Air Lines",
        coverage="aerospace",
        cov_configuration="aerospace_general"
    )

    # Run individual inferences
    for func_name in [
        "alliance_membership_inference",
        "accident_history_inference",
        "certificate_status_inference",
        "iosa_audit_status_inference",
        "eu_safety_list_inference"
    ]:
        func = get_inference_function(func_name)
        if func:
            result = func(ctx)
            print(f"\n{result.signal_id}:")
            print(f"  Score: {result.score}")
            print(f"  Category: {result.category}")
            print(f"  Evidence: {result.evidence}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
