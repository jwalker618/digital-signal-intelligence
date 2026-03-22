import math
from dataclasses import dataclass
from typing import Callable, Dict, Any


# -------------------------
# Raw Curve Implementations
# -------------------------
# Each function returns raw(L) — the un-normalised curve value.
# Anchor normalisation (ILF = raw(L) / raw(anchor)) is applied
# uniformly by ILFEngine.get_ilf(), so adding a new curve type
# only requires defining its raw(L) shape.


def bounded_exponential(L, anchor, max_ilf, k):
    """
    raw(L) = 1 + (max_ilf - 1) * (1 - exp(-k * L/anchor))
    Saturating curve, good for financial lines.
    """
    return 1 + (max_ilf - 1) * (1 - math.exp(-k * (L / anchor)))


def power_curve(L, anchor, alpha):
    """
    raw(L) = (L/anchor)^alpha
    Clean power-law scaling, already normalised at anchor.
    """
    return (L / anchor) ** alpha


def logarithmic_curve(L, anchor, a, b):
    """
    raw(L) = a + b * log(L/anchor + 1)
    """
    return a + b * math.log((L / anchor) + 1)


def pareto_curve(L, anchor, alpha):
    """
    raw(L) = (L/anchor)^alpha
    Single-Pareto severity scaling.
    """
    return (L / anchor) ** alpha


def iso_pareto_curve(L, anchor, q, b):
    """
    ISO Pareto ILF — based on the truncated Pareto severity distribution.

    raw(L) = 1 - (b / (b + L))^(q - 1)

    where q is the Pareto shape parameter (typically 1.5-3.0) and b is the
    loss elimination ratio threshold.

    The ISO increased limits table is a discretised version of this curve.
    """
    return 1 - (b / (b + L)) ** (q - 1)


# -------------------------
# ILF Engine
# -------------------------

CURVE_MAP: Dict[str, Callable] = {
    "bounded_exponential": bounded_exponential,
    "power": power_curve,
    "logarithmic": logarithmic_curve,
    "pareto": pareto_curve,
    "iso_pareto": iso_pareto_curve,
}


@dataclass
class ILFConfig:
    curve: str
    anchor_limit: float
    params: Dict[str, Any]


class ILFEngine:
    def __init__(self, config: Dict[str, Any]):
        self.coverage_cfg = config["ilf"]["coverages"]
        self.default_curve = config["ilf"].get("default_curve", "bounded_exponential")

    def get_ilf(self, coverage: str, limit: float) -> float:
        cfg = self.coverage_cfg.get(coverage)

        if cfg is None:
            raise ValueError(f"No ILF config for coverage '{coverage}'")

        curve_name = cfg.get("curve", self.default_curve)
        curve_fn = CURVE_MAP[curve_name]

        anchor = cfg["anchor_limit"]
        params = dict(cfg["params"])

        # Extract cap (not passed to raw function)
        cap = params.pop("cap", None)

        # Uniform anchor normalisation: ILF = raw(L) / raw(anchor)
        raw_at_limit = curve_fn(limit, anchor, **params)
        raw_at_anchor = curve_fn(anchor, anchor, **params)

        if raw_at_anchor == 0:
            ilf = 1.0
        else:
            ilf = raw_at_limit / raw_at_anchor

        # Apply cap if specified
        if cap is not None:
            ilf = min(ilf, cap)

        # Ensure ILF never drops below 1
        return max(ilf, 1.0)
