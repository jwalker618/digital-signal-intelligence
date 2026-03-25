"""
DSI Synthetic Data Generator
==============================
Generates high-volume synthetic submission data for realistic UX analytics,
portfolio views, and commercial terms demonstration.

Complements the hand-curated seed_dsi_bench.py (61 companies) with ~1000+
synthetic companies that flow through the same production pipeline: scoring,
pricing, premium assembly, commercial terms, and risk terms.

Design:
    - Company names are combinatorial (prefix + descriptor + suffix)
    - Coverage/config routing uses config constraints (size bands, etc.)
    - Signal scores are drawn from normal distributions centered on target tier
    - Entity assignment covers all distribution types (BUNDLED, SUBSCRIPTION,
      TOWER, DIRECT, FRONTED)
    - Temporal spread over 12 months for realistic earned/written analytics

Usage:
    python -m synthetic_generator              # default 1000 companies
    python -m synthetic_generator --count 500  # custom count
    python -m synthetic_generator --dry-run    # print without DB writes

Can also be called from seed_dsi_bench.py:
    from synthetic_generator import generate_synthetic_companies
    companies = generate_synthetic_companies(count=1000)
"""

import math
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# COMPANY NAME GENERATION
# =============================================================================

_PREFIXES = [
    "Apex", "Atlas", "Aurora", "Beacon", "Blue", "Cascade", "Coastal",
    "Continental", "Crest", "Crown", "Delta", "Eagle", "Eclipse", "Ember",
    "Frontier", "Glacier", "Global", "Golden", "Granite", "Harbour",
    "Horizon", "Iron", "Keystone", "Lakeshore", "Landmark", "Liberty",
    "Meridian", "Monument", "Nordic", "Northstar", "Oakridge", "Omega",
    "Pacific", "Patriot", "Peak", "Phoenix", "Pinnacle", "Prime",
    "Quantum", "Red", "Ridge", "River", "Sage", "Sentinel", "Sierra",
    "Silver", "Sovereign", "Sterling", "Summit", "Titan", "Trident",
    "Vanguard", "Vertex", "Vista", "Zenith",
]

_DESCRIPTORS_BY_INDUSTRY = {
    "TECHNOLOGY": [
        "Digital", "Cloud", "Data", "Cyber", "Neural", "Logic", "Byte",
        "Nexus", "Code", "Signal", "Compute", "Vector", "Photon", "Lattice",
    ],
    "HEALTHCARE": [
        "Health", "Medical", "Bio", "Life", "Pharma", "Care", "Clinical",
        "Genomic", "Therapeutic", "Diagnostic", "Wellness", "Vital",
    ],
    "FINANCIAL_SERVICES": [
        "Capital", "Financial", "Equity", "Asset", "Trust", "Credit",
        "Investment", "Wealth", "Fiduciary", "Reserve", "Treasury",
    ],
    "ENERGY": [
        "Energy", "Power", "Fuel", "Grid", "Solar", "Wind", "Petrol",
        "Gas", "Nuclear", "Thermal", "Hydro", "Electric", "Resource",
    ],
    "MANUFACTURING": [
        "Industrial", "Steel", "Precision", "Forge", "Assembly", "Machine",
        "Fabrication", "Component", "Materials", "Alloy", "Dynamic",
    ],
    "RETAIL": [
        "Commerce", "Market", "Trade", "Supply", "Retail", "Consumer",
        "Brand", "Store", "Chain", "Outlet", "Wholesale",
    ],
    "PROFESSIONAL_SERVICES": [
        "Advisory", "Consulting", "Strategy", "Partners", "Associates",
        "Professional", "Insight", "Solutions", "Practice", "Counsel",
    ],
    "MARINE": [
        "Maritime", "Shipping", "Fleet", "Cargo", "Naval", "Ocean",
        "Port", "Vessel", "Navigation", "Harbour", "Seafarer",
    ],
    "AEROSPACE": [
        "Aviation", "Aero", "Flight", "Sky", "Jet", "Wing", "Orbital",
        "Propulsion", "Avionics", "Airborne", "Stratosphere",
    ],
}

_SUFFIXES = [
    "Inc", "Corp", "Group", "Holdings", "LLC", "Ltd", "Partners",
    "Solutions", "Technologies", "Systems", "International", "Global",
    "Industries", "Enterprises", "Co", "Services", "Networks", "Dynamics",
]


def _generate_company_name(industry: str, _used: set = set()) -> str:
    """Generate a unique company name for the given industry."""
    descriptors = _DESCRIPTORS_BY_INDUSTRY.get(
        industry, _DESCRIPTORS_BY_INDUSTRY["TECHNOLOGY"]
    )
    for _ in range(100):
        name = f"{random.choice(_PREFIXES)} {random.choice(descriptors)} {random.choice(_SUFFIXES)}"
        if name not in _used:
            _used.add(name)
            return name
    # Fallback with UUID fragment
    return f"{random.choice(_PREFIXES)} {random.choice(descriptors)} {uuid.uuid4().hex[:4].upper()}"


def _generate_domain(name: str) -> str:
    """Generate a plausible domain from a company name."""
    clean = name.lower().replace(" ", "").replace(",", "").replace(".", "")
    # Truncate to reasonable domain length
    if len(clean) > 20:
        clean = clean[:20]
    tld = random.choice([".com", ".io", ".co", ".net", ".com"])
    return clean + tld


# =============================================================================
# COVERAGE / CONFIGURATION ROUTING
# =============================================================================

# Coverage → list of (configuration, weight, constraints)
# Weight controls relative frequency. Constraints filter by size_band/industry.
COVERAGE_CONFIG_ROUTES = {
    "cyber": [
        ("cyber_general", 6, {"size_band": ["MEDIUM", "LARGE", "ENTERPRISE"]}),
        ("cyber_sme", 4, {"size_band": ["MICRO", "SMALL"]}),
    ],
    "directors_officers": [
        ("do_general", 6, {"size_band": ["MEDIUM", "LARGE", "ENTERPRISE"]}),
        ("do_sme", 4, {"size_band": ["MICRO", "SMALL"]}),
    ],
    "financial_institutions": [
        ("fi_general", 7, {"size_band": ["MEDIUM", "LARGE", "ENTERPRISE"]}),
        ("fi_sme", 3, {"size_band": ["MICRO", "SMALL"]}),
    ],
    "professional_indemnity": [
        ("pi_general", 6, {"size_band": ["MEDIUM", "LARGE", "ENTERPRISE"]}),
        ("pi_sme", 4, {"size_band": ["MICRO", "SMALL"]}),
    ],
    "energy": [
        ("energy_general", 3, {}),
        ("energy_upstream_deepwater", 1, {"size_band": ["LARGE", "ENTERPRISE"]}),
        ("energy_upstream_onshore", 2, {}),
        ("energy_upstream_unconventional", 1, {}),
        ("energy_midstream", 2, {}),
        ("energy_downstream", 2, {}),
        ("energy_offshore_wind", 2, {}),
        ("energy_onshore_renewable", 2, {}),
        ("energy_storage", 1, {}),
        ("energy_sme", 2, {"size_band": ["MICRO", "SMALL"]}),
    ],
    "marine": [
        ("marine_general", 1, {}),
    ],
    "aerospace": [
        ("aerospace_general", 1, {}),
    ],
}

# Portfolio mix — coverage weights for random selection
COVERAGE_WEIGHTS = {
    "cyber": 25,
    "directors_officers": 20,
    "financial_institutions": 10,
    "professional_indemnity": 10,
    "energy": 20,
    "marine": 8,
    "aerospace": 7,
}

# Industry distribution per coverage
INDUSTRY_BY_COVERAGE = {
    "cyber": ["TECHNOLOGY", "HEALTHCARE", "FINANCIAL_SERVICES", "MANUFACTURING", "RETAIL", "PROFESSIONAL_SERVICES"],
    "directors_officers": ["TECHNOLOGY", "HEALTHCARE", "FINANCIAL_SERVICES", "MANUFACTURING", "RETAIL", "PROFESSIONAL_SERVICES"],
    "financial_institutions": ["FINANCIAL_SERVICES"],
    "professional_indemnity": ["PROFESSIONAL_SERVICES", "TECHNOLOGY", "HEALTHCARE"],
    "energy": ["ENERGY"],
    "marine": ["MARINE"],
    "aerospace": ["AEROSPACE"],
}

# Size band distribution weights (realistic: many small, few enterprise)
SIZE_BAND_WEIGHTS = {
    "MICRO": 15,
    "SMALL": 25,
    "MEDIUM": 30,
    "LARGE": 20,
    "ENTERPRISE": 10,
}

# Revenue ranges per size band (USD)
REVENUE_RANGES = {
    "MICRO": (500_000, 5_000_000),
    "SMALL": (5_000_000, 50_000_000),
    "MEDIUM": (50_000_000, 500_000_000),
    "LARGE": (500_000_000, 5_000_000_000),
    "ENTERPRISE": (5_000_000_000, 500_000_000_000),
}

# Limit ranges per size band (USD)
LIMIT_RANGES = {
    "MICRO": (100_000, 1_000_000),
    "SMALL": (250_000, 5_000_000),
    "MEDIUM": (1_000_000, 25_000_000),
    "LARGE": (5_000_000, 100_000_000),
    "ENTERPRISE": (10_000_000, 500_000_000),
}

# Deductible ranges per size band (USD)
DEDUCTIBLE_RANGES = {
    "MICRO": (1_000, 10_000),
    "SMALL": (2_500, 50_000),
    "MEDIUM": (10_000, 250_000),
    "LARGE": (50_000, 1_000_000),
    "ENTERPRISE": (100_000, 5_000_000),
}

GEOGRAPHIES = ["US", "US", "US", "UK", "DE", "FR", "SG", "AU", "CA", "JP"]

# Product types per coverage
PRODUCT_TYPES = {
    "cyber": ["cyber_liability", "network_security", "privacy_liability", "cyber_extortion"],
    "directors_officers": ["side_a", "side_b", "side_c", "directors_officers"],
    "financial_institutions": ["financial_institution_bond", "fiduciary", "errors_omissions"],
    "professional_indemnity": ["professional_liability", "errors_omissions"],
    "energy": ["property_damage", "business_interruption", "control_of_well",
               "third_party_liability", "delay_in_start_up", "combined_property_liability"],
    "marine": ["hull_machinery", "third_party_liability"],
    "aerospace": ["aviation_hull_liability_combined", "third_party_liability"],
}


# =============================================================================
# ENTITY ASSIGNMENT — maps (coverage, size, geography) to commercial entity
# =============================================================================

def _assign_entity(coverage: str, size_band: str, geography: str) -> str:
    """Assign a commercial entity ID based on coverage, size, and geography."""
    # EU geographies use the fronted entity for cyber/D&O/PI
    if geography in ("DE", "FR") and coverage in ("cyber", "directors_officers", "professional_indemnity"):
        return "eu_fronted"

    if coverage in ("cyber", "directors_officers"):
        return "mga_us_cyber"

    if coverage in ("financial_institutions", "professional_indemnity"):
        return "direct_fi_pi"

    if coverage == "energy":
        # Large energy risks go through tower program, smaller through syndicate
        if size_band in ("LARGE", "ENTERPRISE"):
            return random.choice(["tower_us_energy", "syndicate_lead", "syndicate_example"])
        return random.choice(["syndicate_example", "syndicate_lead"])

    if coverage in ("marine", "aerospace"):
        return random.choice(["syndicate_example", "syndicate_lead"])

    return "mga_us_cyber"


# =============================================================================
# SIGNAL SCORE GENERATION — continuous variation from normal distribution
# =============================================================================

# Tier → target composite score band (mid-point, std dev)
TIER_SCORE_PARAMS = {
    1: (850, 60),   # Preferred: high scores
    2: (650, 70),   # Standard: good scores
    3: (450, 70),   # Elevated: moderate scores
    4: (300, 50),   # High risk: low scores
    5: (150, 50),   # Decline territory
}


def _generate_signal_scores(tier: int) -> Dict[str, float]:
    """Generate a flat dict of signal_id → score for the given target tier.

    Returns scores as a dict keyed by signal_id (no group nesting).
    Scores are drawn from a normal distribution centered on the tier's
    target band, with per-signal jitter for natural variation.
    """
    mid, std = TIER_SCORE_PARAMS.get(tier, (450, 70))

    # Generate a base composite target for this company
    base = random.gauss(mid, std)
    base = max(50, min(950, base))

    # Convert 0-1000 composite to 0-100 per-signal scores
    # Composite ≈ weighted average of signal scores × 10
    target_signal_score = base / 10.0  # 0-100 scale

    scores = {}
    # We don't know which signals exist until config is loaded,
    # so we store just the target and let the seed script's
    # build_synthetic_signal_outputs handle per-signal generation
    scores["_target_score"] = target_signal_score
    scores["_tier"] = tier

    return scores


# =============================================================================
# COMPANY GENERATION
# =============================================================================

def _select_configuration(coverage: str, size_band: str) -> str:
    """Select a configuration for the given coverage and size band."""
    routes = COVERAGE_CONFIG_ROUTES.get(coverage, [])
    eligible = []
    weights = []

    for config_name, weight, constraints in routes:
        if constraints:
            sb_constraint = constraints.get("size_band")
            if sb_constraint and size_band not in sb_constraint:
                continue
        eligible.append(config_name)
        weights.append(weight)

    if not eligible:
        # Fallback: use first route
        return routes[0][0] if routes else f"{coverage}_general"

    return random.choices(eligible, weights=weights, k=1)[0]


def _select_tier(size_band: str) -> int:
    """Select a risk tier with realistic distribution.

    Larger companies tend to have better risk profiles (more resources),
    but there's significant variation.
    """
    # Base distribution: most companies are tier 2-3
    tier_weights_by_size = {
        "MICRO":      [5, 15, 35, 30, 15],   # Skew worse
        "SMALL":      [10, 20, 35, 25, 10],
        "MEDIUM":     [15, 30, 30, 20, 5],
        "LARGE":      [20, 35, 25, 15, 5],
        "ENTERPRISE": [30, 35, 20, 10, 5],   # Skew better
    }
    weights = tier_weights_by_size.get(size_band, [15, 25, 30, 20, 10])
    return random.choices([1, 2, 3, 4, 5], weights=weights, k=1)[0]


def generate_synthetic_company(
    company_index: int,
    base_time: datetime,
) -> Dict[str, Any]:
    """Generate a single synthetic company dict compatible with seed_dsi_bench.

    Returns a dict with the same keys as entries in COMPANIES.
    """
    # Pick coverage weighted by portfolio mix
    coverages = list(COVERAGE_WEIGHTS.keys())
    weights = [COVERAGE_WEIGHTS[c] for c in coverages]
    coverage = random.choices(coverages, weights=weights, k=1)[0]

    # Industry for this coverage
    industries = INDUSTRY_BY_COVERAGE[coverage]
    industry = random.choice(industries)

    # Size band (weighted distribution)
    bands = list(SIZE_BAND_WEIGHTS.keys())
    band_weights = [SIZE_BAND_WEIGHTS[b] for b in bands]
    size_band = random.choices(bands, weights=band_weights, k=1)[0]

    # Configuration routing
    configuration = _select_configuration(coverage, size_band)

    # Risk tier
    tier = _select_tier(size_band)

    # Revenue
    rev_lo, rev_hi = REVENUE_RANGES[size_band]
    revenue = round(random.uniform(rev_lo, rev_hi), -3)  # Round to nearest 1000

    # Limit and deductible
    lim_lo, lim_hi = LIMIT_RANGES[size_band]
    limit = _round_to_nice(random.uniform(lim_lo, lim_hi))
    ded_lo, ded_hi = DEDUCTIBLE_RANGES[size_band]
    deductible = _round_to_nice(random.uniform(ded_lo, ded_hi))

    # Geography
    geography = random.choice(GEOGRAPHIES)

    # Company name and domain
    entity_name = _generate_company_name(industry)
    domain = _generate_domain(entity_name)

    # Product type
    product_types = PRODUCT_TYPES.get(coverage, ["standard"])
    product_type = random.choice(product_types)

    # Entity assignment
    entity_id = _assign_entity(coverage, size_band, geography)

    # Signal score target for this tier
    signal_meta = _generate_signal_scores(tier)

    # Temporal spread — submission created over the last 12 months
    days_ago = random.randint(0, 365)
    created_at = base_time - timedelta(days=days_ago)

    co = {
        "entity_name": entity_name,
        "domain": domain,
        "ticker": None,  # Synthetic companies don't have tickers
        "coverage": coverage,
        "configuration": configuration,
        "tier": tier,
        "decision": "",  # Determined by production pipeline
        "premium": 0,  # Determined by production pipeline
        "revenue": int(revenue),
        "industry": industry,
        "size_band": size_band,
        "geography": geography,
        "description": f"Synthetic {industry.lower().replace('_', ' ')} company, {size_band.lower()} segment.",
        "signal_profile": "",  # No named profile — uses _target_score
        "product_type": product_type,
        "limit": limit,
        "deductible": deductible,
        # Synthetic-specific metadata
        "_synthetic": True,
        "_target_signal_score": signal_meta["_target_score"],
        "_entity_id": entity_id,
        "_created_at": created_at,
        "_index": company_index,
    }

    # Coverage-specific fields
    if coverage == "energy":
        co["tiv"] = int(revenue * random.uniform(2, 10))
    if coverage == "marine":
        co["hull_value"] = int(random.uniform(5_000_000, 2_000_000_000))
    if coverage == "aerospace":
        co["hull_value"] = int(random.uniform(20_000_000, 5_000_000_000))
    if coverage == "financial_institutions":
        co["total_assets"] = int(revenue * random.uniform(5, 50))
    if coverage == "directors_officers":
        co["company_type"] = random.choice([
            "PUBLIC_LARGE_CAP", "PUBLIC_SMALL_CAP", "PRIVATE", "PRIVATE", "PRIVATE",
        ])

    return co


def _round_to_nice(value: float) -> int:
    """Round a value to a 'nice' number (1, 2, 2.5, 5 × 10^n)."""
    if value <= 0:
        return 1000
    magnitude = 10 ** int(math.log10(value))
    nice_multiples = [1, 2, 2.5, 5, 10]
    ratio = value / magnitude
    closest = min(nice_multiples, key=lambda m: abs(m - ratio))
    return int(closest * magnitude)


def generate_synthetic_companies(
    count: int = 1000,
    base_time: Optional[datetime] = None,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Generate a list of synthetic company dicts.

    Args:
        count: Number of companies to generate.
        base_time: Reference time for temporal spread (default: now).
        seed: Random seed for reproducibility.

    Returns:
        List of company dicts compatible with seed_dsi_bench.COMPANIES format.
    """
    if seed is not None:
        random.seed(seed)
    if base_time is None:
        base_time = datetime.now(timezone.utc)

    # Reset name uniqueness tracker
    _generate_company_name.__defaults__[0].clear()

    companies = []
    for i in range(count):
        co = generate_synthetic_company(i, base_time)
        companies.append(co)

    return companies


# =============================================================================
# STANDALONE EXECUTION (dry-run / preview)
# =============================================================================

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Generate synthetic DSI seed data")
    parser.add_argument("--count", type=int, default=1000, help="Number of companies")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without DB writes")
    args = parser.parse_args()

    companies = generate_synthetic_companies(count=args.count, seed=args.seed)

    # Summary statistics
    coverage_counts = {}
    config_counts = {}
    entity_counts = {}
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    size_counts = {}
    geo_counts = {}

    for co in companies:
        cov = co["coverage"]
        cfg = co["configuration"]
        ent = co["_entity_id"]
        tier = co["tier"]
        size = co["size_band"]
        geo = co["geography"]

        coverage_counts[cov] = coverage_counts.get(cov, 0) + 1
        config_counts[cfg] = config_counts.get(cfg, 0) + 1
        entity_counts[ent] = entity_counts.get(ent, 0) + 1
        tier_counts[tier] += 1
        size_counts[size] = size_counts.get(size, 0) + 1
        geo_counts[geo] = geo_counts.get(geo, 0) + 1

    print("=" * 70)
    print(f"  SYNTHETIC DATA GENERATOR — {args.count} companies (seed={args.seed})")
    print("=" * 70)

    print(f"\n  Coverage distribution:")
    for cov, n in sorted(coverage_counts.items(), key=lambda x: -x[1]):
        print(f"    {cov:<30s} {n:>5d}  ({100*n/len(companies):.1f}%)")

    print(f"\n  Configuration distribution:")
    for cfg, n in sorted(config_counts.items(), key=lambda x: -x[1]):
        print(f"    {cfg:<40s} {n:>5d}")

    print(f"\n  Entity distribution:")
    for ent, n in sorted(entity_counts.items(), key=lambda x: -x[1]):
        print(f"    {ent:<30s} {n:>5d}  ({100*n/len(companies):.1f}%)")

    print(f"\n  Tier distribution:")
    for tier in sorted(tier_counts):
        n = tier_counts[tier]
        bar = "#" * (n // 5)
        print(f"    Tier {tier}: {n:>5d}  {bar}")

    print(f"\n  Size band distribution:")
    for size, n in sorted(size_counts.items(), key=lambda x: -x[1]):
        print(f"    {size:<15s} {n:>5d}")

    print(f"\n  Geography distribution:")
    for geo, n in sorted(geo_counts.items(), key=lambda x: -x[1]):
        print(f"    {geo:<5s} {n:>5d}")

    # Sample companies
    print(f"\n  Sample companies:")
    for co in companies[:10]:
        print(f"    {co['entity_name']:<40s} {co['coverage']:<25s} "
              f"{co['configuration']:<35s} T{co['tier']} {co['size_band']:<12s} "
              f"${co['limit']:>13,d}  → {co['_entity_id']}")

    if args.dry_run:
        print(f"\n  DRY RUN — no database writes.")
        sys.exit(0)

    print(f"\n  To seed these into the database, run:")
    print(f"    python seed_dsi_bench.py --synthetic --count {args.count} --seed {args.seed}")
