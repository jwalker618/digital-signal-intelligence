from dataclasses import dataclass
from typing import Callable, Dict, List, Any, Iterable

from dsi_guardrails import GuardrailConfig, clamp_modifier, evaluate_guardrails


@dataclass
class PricingConfig:
    mode: str                      # "PREMIUM_BASE" or "MULTIPLIER"
    rate: float                    # e.g. 0.001 for 10 bps, or flat premium
    anchor_limit: float            # e.g. 1_000_000
    anchor_deductible: float       # e.g. 50_000
    ilf_curve: Callable[[float], float]
    ded_factor: Callable[[float], float]


@dataclass
class ModifierScenario:
    name: str
    m_risk: float
    m_loss: float
    m_exp: float


def compute_base(basis: float, cfg: PricingConfig) -> float:
    """
    Compute the base premium before ILF, deductible, and modifiers.
    """
    if cfg.mode == "PREMIUM_BASE":
        return cfg.rate
    elif cfg.mode == "MULTIPLIER":
        return basis * cfg.rate
    else:
        raise ValueError(f"Unknown pricing mode: {cfg.mode}")


def price_point(
    revenue: float,
    limit: float,
    deductible: float,
    mods: ModifierScenario,
    p_cfg: PricingConfig,
    g_cfg: GuardrailConfig,
) -> Dict[str, Any]:
    """
    Price a single point and evaluate guardrails.
    """
    base = compute_base(revenue, p_cfg)

    ilf_req = p_cfg.ilf_curve(limit)
    ilf_ref = p_cfg.ilf_curve(p_cfg.anchor_limit)
    d_fac = p_cfg.ded_factor(deductible)

    raw_modifier = mods.m_risk * mods.m_loss * mods.m_exp
    total_modifier = clamp_modifier(raw_modifier, g_cfg)

    premium = base * (ilf_req / ilf_ref) * d_fac * total_modifier

    guardrail_result = evaluate_guardrails(
        premium=premium,
        limit=limit,
        revenue=revenue,
        cfg=g_cfg,
    )

    return {
        "revenue": revenue,
        "limit": limit,
        "deductible": deductible,
        "modifier_scenario": mods.name,
        "base": base,
        "premium": premium,
        "raw_modifier": raw_modifier,
        "total_modifier": total_modifier,
        "guardrails": guardrail_result,
    }


def generate_grid(
    revenues: Iterable[float],
    limits: Iterable[float],
    deductibles: Iterable[float],
    modifier_scenarios: Iterable[ModifierScenario],
    p_cfg: PricingConfig,
    g_cfg: GuardrailConfig,
) -> List[Dict[str, Any]]:
    """
    Generate a full calibration grid across revenue, limit, deductible, and modifier scenarios.
    """
    results: List[Dict[str, Any]] = []
    for rev in revenues:
        for lim in limits:
            for ded in deductibles:
                for mods in modifier_scenarios:
                    result = price_point(
                        revenue=rev,
                        limit=lim,
                        deductible=ded,
                        mods=mods,
                        p_cfg=p_cfg,
                        g_cfg=g_cfg,
                    )
                    results.append(result)
    return results


def summarise_issues(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Summarise guardrail breaches across the grid.
    """
    total = len(results)
    breaches: List[Dict[str, Any]] = []

    for r in results:
        if not r["guardrails"]["ok"]:
            breaches.append(r)

    return {
        "total_points": total,
        "breach_count": len(breaches),
        "breach_ratio": len(breaches) / total if total > 0 else 0.0,
        "breaches": breaches,
    }
