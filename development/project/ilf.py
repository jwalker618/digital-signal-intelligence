import math
from dataclasses import dataclass
from typing import Callable, Dict, Any


# -------------------------
# Curve Implementations
# -------------------------

def bounded_exponential(L, anchor, max_ilf, k):
    """
    ILF(L) = 1 + (max_ilf - 1) * (1 - exp(-k * L/anchor))
    Normalised so ILF(anchor) = 1.0
    """
    raw_anchor = 1 + (max_ilf - 1) * (1 - math.exp(-k))
    raw = 1 + (max_ilf - 1) * (1 - math.exp(-k * (L / anchor)))
    return raw / raw_anchor


def power_curve(L, anchor, alpha, cap):
    """
    ILF(L) = (L/anchor)^alpha, capped.
    """
    ilf = (L / anchor) ** alpha
    return min(ilf, cap)


def logarithmic_curve(L, anchor, a, b, cap):
    """
    ILF(L) = a + b * log(L/anchor + 1)
    """
    ilf = a + b * math.log((L / anchor) + 1)
    return min(ilf, cap)


def pareto_curve(L, anchor, alpha, cap):
    """
    Pareto severity ILF: (L/anchor)^alpha, capped. Returns 1.0 at/below anchor.
    """
    if L <= anchor:
        return 1.0
    ilf = (L / anchor) ** alpha
    return min(ilf, cap)


# -------------------------
# ILF Engine
# -------------------------

CURVE_MAP: Dict[str, Callable] = {
    "bounded_exponential": bounded_exponential,
    "power": power_curve,
    "logarithmic": logarithmic_curve,
    "pareto": pareto_curve,
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
        params = cfg["params"]

        ilf = curve_fn(limit, anchor, **params)

        # Ensure ILF never drops below 1
        return max(ilf, 1.0)
