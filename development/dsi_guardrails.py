from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class GuardrailConfig:
    max_premium_pct_limit: Optional[float] = 0.25      # e.g. 25% of limit
    max_premium_pct_revenue: Optional[float] = 0.01    # e.g. 1% of revenue
    min_modifier: float = 0.6                          # floor for total modifier
    max_modifier: float = 1.8                          # cap for total modifier
    min_deductible_by_segment: Optional[Dict[str, float]] = None  # {"enterprise": 250000}
    segment_rules: Optional[Dict[str, Dict[str, Any]]] = None     # routing / extra rules


def clamp_modifier(total_modifier: float, cfg: GuardrailConfig) -> float:
    """
    Clamp the combined modifier into an allowed band.
    """
    return max(cfg.min_modifier, min(cfg.max_modifier, total_modifier))


def check_premium_vs_limit(premium: float, limit: float, cfg: GuardrailConfig) -> Optional[str]:
    """
    Return a warning code if premium breaches premium/limit guardrail.
    """
    if cfg.max_premium_pct_limit is None or limit <= 0:
        return None
    if premium > cfg.max_premium_pct_limit * limit:
        return "PREMIUM_EXCEEDS_LIMIT_CAP"
    return None


def check_premium_vs_revenue(premium: float, revenue: float, cfg: GuardrailConfig) -> Optional[str]:
    """
    Return a warning code if premium breaches premium/revenue guardrail.
    """
    if cfg.max_premium_pct_revenue is None or revenue <= 0:
        return None
    if premium > cfg.max_premium_pct_revenue * revenue:
        return "PREMIUM_EXCEEDS_REVENUE_CAP"
    return None


def enforce_min_deductible(segment: str, deductible: float, cfg: GuardrailConfig) -> float:
    """
    Enforce a minimum deductible by segment (e.g. enterprise must have >= 250k).
    Returns the (possibly adjusted) deductible.
    """
    if not cfg.min_deductible_by_segment:
        return deductible
    min_ded = cfg.min_deductible_by_segment.get(segment)
    if min_ded is None:
        return deductible
    return max(deductible, min_ded)


def evaluate_guardrails(
    premium: float,
    limit: float,
    revenue: float,
    cfg: GuardrailConfig,
) -> Dict[str, Any]:
    """
    Evaluate all guardrails and return a structured result.
    """
    issues = []

    code1 = check_premium_vs_limit(premium, limit, cfg)
    if code1:
        issues.append(code1)

    code2 = check_premium_vs_revenue(premium, revenue, cfg)
    if code2:
        issues.append(code2)

    return {
        "premium": premium,
        "limit": limit,
        "revenue": revenue,
        "issues": issues,
        "ok": len(issues) == 0,
    }
