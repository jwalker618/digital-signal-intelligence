"""v8.2 broker intelligence — synthetic data foundation.

Hand-crafted reference data the broker portal needs but the platform
doesn't have authoritative sources for in v8:

  - Carrier universe (12 real-name carriers with appetite, capacity,
    commission yield, pricing tightness, ESG stance)
  - Marsh practice verticals (industry lens used across every broker
    surface)
  - ESG signal taxonomy
  - Per-line market cycle position + recent loss events
  - Per-industry x peril CAT exposure factors

Everything is illustrative -- credible enough to support a sophisticated
pitch demo without pretending to be production data. v8.3 / production
would wire real carrier rosters, placement history, and market feeds.
"""
from __future__ import annotations

from typing import Optional


# ============================================================================
# Carrier universe
# ============================================================================
#
# Each carrier carries an appetite map (per-coverage stance), capacity
# band, typical commission %, pricing position vs market median, and
# ESG stance. The data is hand-tuned to feel real to a Marsh viewer --
# Beazley dominant in cyber, Munich Re heavy on treaty, Lloyd's
# syndicates open to specialty risks, etc.

AppetiteStance = str  # "leaning_in" | "neutral" | "selective" | "leaning_out"
PricingPosition = str  # "tight" | "median" | "light"
EsgStance = str        # "leader" | "progressive" | "neutral" | "restrictive"

CARRIER_UNIVERSE: list[dict] = [
    {
        "slug": "aig",
        "name": "AIG",
        "type": "Global",
        "headquarters": "United States",
        "capacity_band": "Large",
        "typical_commission_pct": 12.5,
        "pricing_position": "median",
        "esg_stance": "progressive",
        "win_rate": 0.41,
        "appetite": {
            "cyber": "leaning_in",
            "pi": "neutral",
            "do": "leaning_in",
            "property": "neutral",
            "casualty": "neutral",
            "prodlib": "selective",
            "medprof": "neutral",
            "energy": "selective",
        },
        "specialties": ["FinPro", "Cyber", "Multinational"],
        "movement_note": "Selectively re-expanding in mid-market cyber after 2023 pullback.",
        "esg_note": "Net-Zero Insurance Alliance signatory; coal underwriting wind-down by 2030.",
    },
    {
        "slug": "chubb",
        "name": "Chubb",
        "type": "Global",
        "headquarters": "Switzerland / United States",
        "capacity_band": "Large",
        "typical_commission_pct": 13.0,
        "pricing_position": "tight",
        "esg_stance": "progressive",
        "win_rate": 0.45,
        "appetite": {
            "cyber": "neutral",
            "pi": "leaning_in",
            "do": "leaning_in",
            "property": "leaning_in",
            "casualty": "leaning_in",
            "prodlib": "neutral",
            "medprof": "selective",
            "energy": "selective",
        },
        "specialties": ["High-net-worth", "Property", "Casualty"],
        "movement_note": "Disciplined underwriter; growing share in upper-middle market.",
        "esg_note": "Restrictive on new coal; growing renewable energy book.",
    },
    {
        "slug": "travelers",
        "name": "Travelers",
        "type": "Regional",
        "headquarters": "United States",
        "capacity_band": "Large",
        "typical_commission_pct": 11.5,
        "pricing_position": "median",
        "esg_stance": "neutral",
        "win_rate": 0.38,
        "appetite": {
            "cyber": "selective",
            "pi": "neutral",
            "do": "neutral",
            "property": "leaning_in",
            "casualty": "leaning_in",
            "prodlib": "leaning_in",
            "medprof": "leaning_out",
            "energy": "neutral",
        },
        "specialties": ["Property", "Workers Comp", "Construction"],
        "movement_note": "Strong middle-market property growth; trimming healthcare exposure.",
        "esg_note": "Climate transition disclosed; case-by-case fossil fuel approach.",
    },
    {
        "slug": "liberty-mutual",
        "name": "Liberty Mutual",
        "type": "Global",
        "headquarters": "United States",
        "capacity_band": "Large",
        "typical_commission_pct": 12.0,
        "pricing_position": "median",
        "esg_stance": "neutral",
        "win_rate": 0.36,
        "appetite": {
            "cyber": "neutral",
            "pi": "neutral",
            "do": "selective",
            "property": "leaning_in",
            "casualty": "leaning_in",
            "prodlib": "neutral",
            "medprof": "neutral",
            "energy": "selective",
        },
        "specialties": ["Casualty", "Property", "Programs"],
        "movement_note": "Growing in programs and global risk solutions.",
        "esg_note": "Coal underwriting restrictions in place since 2022.",
    },
    {
        "slug": "allianz",
        "name": "Allianz",
        "type": "Global",
        "headquarters": "Germany",
        "capacity_band": "Large",
        "typical_commission_pct": 13.5,
        "pricing_position": "tight",
        "esg_stance": "leader",
        "win_rate": 0.43,
        "appetite": {
            "cyber": "leaning_in",
            "pi": "leaning_in",
            "do": "leaning_in",
            "property": "leaning_in",
            "casualty": "neutral",
            "prodlib": "neutral",
            "medprof": "selective",
            "energy": "leaning_out",
        },
        "specialties": ["Corporate", "Climate", "Multinational"],
        "movement_note": "Aggressive ESG-led growth; exiting thermal coal completely.",
        "esg_note": "Net-Zero Asset Owner Alliance founding member; strong climate analytics.",
    },
    {
        "slug": "zurich",
        "name": "Zurich",
        "type": "Global",
        "headquarters": "Switzerland",
        "capacity_band": "Large",
        "typical_commission_pct": 12.5,
        "pricing_position": "median",
        "esg_stance": "leader",
        "win_rate": 0.40,
        "appetite": {
            "cyber": "neutral",
            "pi": "leaning_in",
            "do": "neutral",
            "property": "neutral",
            "casualty": "leaning_in",
            "prodlib": "selective",
            "medprof": "neutral",
            "energy": "leaning_out",
        },
        "specialties": ["Corporate", "Energy transition", "Construction"],
        "movement_note": "Doubling down on energy transition; building specialty climate practice.",
        "esg_note": "First major insurer to commit to oil & gas underwriting framework.",
    },
    {
        "slug": "axa-xl",
        "name": "AXA XL",
        "type": "Global",
        "headquarters": "France / Bermuda",
        "capacity_band": "Large",
        "typical_commission_pct": 13.0,
        "pricing_position": "median",
        "esg_stance": "leader",
        "win_rate": 0.39,
        "appetite": {
            "cyber": "leaning_in",
            "pi": "leaning_in",
            "do": "neutral",
            "property": "leaning_in",
            "casualty": "neutral",
            "prodlib": "neutral",
            "medprof": "selective",
            "energy": "selective",
        },
        "specialties": ["Cyber", "Specialty", "Reinsurance"],
        "movement_note": "Building cyber capacity post-Lloyd's; new climate risk product.",
        "esg_note": "Excluded coal since 2017; oil/gas tar sands restrictions tightening.",
    },
    {
        "slug": "beazley",
        "name": "Beazley",
        "type": "Specialty / Lloyd's",
        "headquarters": "United Kingdom",
        "capacity_band": "Mid",
        "typical_commission_pct": 15.0,
        "pricing_position": "tight",
        "esg_stance": "progressive",
        "win_rate": 0.52,
        "appetite": {
            "cyber": "leaning_in",
            "pi": "leaning_in",
            "do": "leaning_in",
            "property": "selective",
            "casualty": "selective",
            "prodlib": "selective",
            "medprof": "leaning_in",
            "energy": "neutral",
        },
        "specialties": ["Cyber", "PI / E&O", "Healthcare"],
        "movement_note": "Cyber market leader; growing healthcare professional book.",
        "esg_note": "Climate Smart product line for sustainability-led insureds.",
    },
    {
        "slug": "hiscox",
        "name": "Hiscox",
        "type": "Specialty / Lloyd's",
        "headquarters": "Bermuda / United Kingdom",
        "capacity_band": "Mid",
        "typical_commission_pct": 14.0,
        "pricing_position": "median",
        "esg_stance": "progressive",
        "win_rate": 0.46,
        "appetite": {
            "cyber": "leaning_in",
            "pi": "leaning_in",
            "do": "neutral",
            "property": "neutral",
            "casualty": "selective",
            "prodlib": "neutral",
            "medprof": "selective",
            "energy": "leaning_out",
        },
        "specialties": ["Specialty", "Small commercial", "Cyber"],
        "movement_note": "Steady cyber book; selective high-value property.",
        "esg_note": "Net-zero operations by 2030; restricted oil & gas underwriting.",
    },
    {
        "slug": "cfc",
        "name": "CFC Underwriting",
        "type": "MGA / Lloyd's",
        "headquarters": "United Kingdom",
        "capacity_band": "Mid",
        "typical_commission_pct": 17.5,
        "pricing_position": "tight",
        "esg_stance": "progressive",
        "win_rate": 0.55,
        "appetite": {
            "cyber": "leaning_in",
            "pi": "leaning_in",
            "do": "neutral",
            "property": "selective",
            "casualty": "leaning_out",
            "prodlib": "selective",
            "medprof": "neutral",
            "energy": "selective",
        },
        "specialties": ["Cyber MGA", "Emerging tech", "SME"],
        "movement_note": "Aggressive mid-market cyber growth via embedded distribution.",
        "esg_note": "ClimateNeutral certified; product transparency focus.",
    },
    {
        "slug": "tokio-marine-hcc",
        "name": "Tokio Marine HCC",
        "type": "Specialty",
        "headquarters": "United States / Japan",
        "capacity_band": "Mid",
        "typical_commission_pct": 14.5,
        "pricing_position": "median",
        "esg_stance": "progressive",
        "win_rate": 0.42,
        "appetite": {
            "cyber": "neutral",
            "pi": "leaning_in",
            "do": "leaning_in",
            "property": "neutral",
            "casualty": "neutral",
            "prodlib": "selective",
            "medprof": "leaning_in",
            "energy": "neutral",
        },
        "specialties": ["D&O / Mgmt liability", "Medical professional", "International"],
        "movement_note": "Selective expansion in management liability; healthcare growth.",
        "esg_note": "Sustainable infrastructure investment focus.",
    },
    {
        "slug": "brit-2987",
        "name": "Brit Syndicate 2987",
        "type": "Lloyd's syndicate",
        "headquarters": "Lloyd's of London",
        "capacity_band": "Mid",
        "typical_commission_pct": 16.0,
        "pricing_position": "median",
        "esg_stance": "neutral",
        "win_rate": 0.44,
        "appetite": {
            "cyber": "leaning_in",
            "pi": "leaning_in",
            "do": "neutral",
            "property": "leaning_in",
            "casualty": "selective",
            "prodlib": "neutral",
            "medprof": "selective",
            "energy": "leaning_in",
        },
        "specialties": ["Property cat", "Specialty", "Energy"],
        "movement_note": "Strong CAT property capacity; energy transition product launching.",
        "esg_note": "Lloyd's ESG framework alignment; case-by-case fossil fuel approach.",
    },
    {
        "slug": "apollo-1969",
        "name": "Apollo Syndicate 1969",
        "type": "Lloyd's syndicate",
        "headquarters": "Lloyd's of London",
        "capacity_band": "Mid",
        "typical_commission_pct": 16.5,
        "pricing_position": "tight",
        "esg_stance": "leader",
        "win_rate": 0.49,
        "appetite": {
            "cyber": "leaning_in",
            "pi": "neutral",
            "do": "selective",
            "property": "selective",
            "casualty": "selective",
            "prodlib": "selective",
            "medprof": "selective",
            "energy": "leaning_out",
        },
        "specialties": ["Cyber", "Climate parametric", "Specialty"],
        "movement_note": "Parametric climate product gaining traction; cyber leader.",
        "esg_note": "Parametric climate insurance; restricted thermal coal underwriting.",
    },
    {
        "slug": "munich-re",
        "name": "Munich Re",
        "type": "Reinsurer",
        "headquarters": "Germany",
        "capacity_band": "Large",
        "typical_commission_pct": 10.0,
        "pricing_position": "tight",
        "esg_stance": "leader",
        "win_rate": 0.35,
        "appetite": {
            "cyber": "leaning_in",
            "pi": "neutral",
            "do": "selective",
            "property": "leaning_in",
            "casualty": "neutral",
            "prodlib": "selective",
            "medprof": "selective",
            "energy": "leaning_out",
        },
        "specialties": ["Reinsurance", "Climate analytics", "Cyber treaty"],
        "movement_note": "Industry leader in climate modelling; cyber treaty market share growth.",
        "esg_note": "Net-Zero Insurance Alliance founder; coal exit by 2025 (direct), 2040 (treaty).",
    },
]


# ============================================================================
# Marsh practice verticals
# ============================================================================
#
# How Marsh organises internally. Every broker surface offers this as
# a filter. Each vertical maps to a set of NAICS sections so we can
# place demo clients into the right practice automatically.

MARSH_VERTICALS: list[dict] = [
    {
        "slug": "technology",
        "name": "Technology & MedTech",
        "icon": "Cpu",
        "naics_sections": ["51", "54"],
        "summary": "Software, SaaS, hardware, MedTech, fintech, telco.",
        "priority_lines": ["cyber", "pi", "do"],
    },
    {
        "slug": "healthcare",
        "name": "Healthcare Industries",
        "icon": "HeartPulse",
        "naics_sections": ["62"],
        "summary": "Hospitals, providers, life sciences, pharma, devices.",
        "priority_lines": ["medprof", "cyber", "pi", "property"],
    },
    {
        "slug": "manufacturing",
        "name": "Manufacturing & Automotive",
        "icon": "Factory",
        "naics_sections": ["31", "32", "33"],
        "summary": "Industrial, automotive, consumer goods, electronics.",
        "priority_lines": ["property", "casualty", "prodlib", "cyber"],
    },
    {
        "slug": "energy-power",
        "name": "Energy & Power",
        "icon": "Zap",
        "naics_sections": ["21", "22"],
        "summary": "Oil & gas, renewables, utilities, energy transition.",
        "priority_lines": ["property", "casualty", "energy", "do"],
    },
    {
        "slug": "financial-institutions",
        "name": "Financial Institutions",
        "icon": "Landmark",
        "naics_sections": ["52"],
        "summary": "Banks, asset managers, insurers, fintech, broker-dealers.",
        "priority_lines": ["fi", "do", "cyber", "pi"],
    },
    {
        "slug": "real-estate",
        "name": "Real Estate & Hospitality",
        "icon": "Building2",
        "naics_sections": ["53", "72"],
        "summary": "REITs, hospitality, leisure, lodging, retail real estate.",
        "priority_lines": ["property", "casualty", "do"],
    },
    {
        "slug": "construction",
        "name": "Construction",
        "icon": "HardHat",
        "naics_sections": ["23"],
        "summary": "Builders, contractors, infrastructure, surety.",
        "priority_lines": ["casualty", "property", "do"],
    },
    {
        "slug": "public-sector",
        "name": "Public Sector & Education",
        "icon": "Library",
        "naics_sections": ["61", "92"],
        "summary": "Municipalities, agencies, education, public utilities.",
        "priority_lines": ["casualty", "property", "do", "cyber"],
    },
]


def vertical_for_naics(naics_code: Optional[str]) -> Optional[str]:
    """Map a NAICS code (full or section) to a Marsh vertical slug."""
    if not naics_code:
        return None
    section = str(naics_code)[:2]
    for v in MARSH_VERTICALS:
        if section in v["naics_sections"]:
            return v["slug"]
    return None


# ============================================================================
# Market cycle position per coverage line
# ============================================================================

MARKET_LINES: list[dict] = [
    {
        "slug": "cyber",
        "name": "Cyber",
        "cycle_position": "Softening",
        "rate_change_yoy_pct": -3.5,
        "capacity_state": "Plentiful",
        "capacity_trend": "Expanding",
        "loss_trend": "Stable",
        "summary": (
            "First Q of softening after 2022-23 hardening. Capacity has "
            "returned via new MGA entrants and reinsurance opening up. "
            "Carriers competing again on terms; rate decreases for "
            "well-controlled risks."
        ),
        "key_drivers": [
            "Loss frequency stabilising as ransomware defences mature",
            "Reinsurance treaty Jan-1 renewals materially more orderly",
            "MGA / specialty capacity competing for mid-market",
        ],
        "esg_overlay": "Carriers increasingly evaluating supply-chain cyber dependence as ESG-adjacent governance risk.",
    },
    {
        "slug": "property",
        "name": "Property",
        "cycle_position": "Hardening",
        "rate_change_yoy_pct": 8.5,
        "capacity_state": "Tight",
        "capacity_trend": "Stable",
        "loss_trend": "Deteriorating",
        "summary": (
            "Continued hardening driven by named-storm activity, wildfire "
            "loss patterns, and reinsurance treaty pressure. CAT-exposed "
            "risks under particular pressure; non-CAT mid-market easier."
        ),
        "key_drivers": [
            "Atlantic hurricane season severity",
            "Wildfire frequency in California / Pacific Northwest",
            "Inflation-driven sum-insured increases",
        ],
        "esg_overlay": "Climate physical risk material; carriers increasingly pricing transition risk for fossil-fuel-adjacent insureds.",
    },
    {
        "slug": "casualty",
        "name": "Casualty (GL)",
        "cycle_position": "Flat",
        "rate_change_yoy_pct": 2.0,
        "capacity_state": "Adequate",
        "capacity_trend": "Stable",
        "loss_trend": "Worsening (social inflation)",
        "summary": (
            "Headline flat, but social-inflation pressure showing in "
            "umbrella / excess layers. Casualty carriers tightening on "
            "challenged classes (transport, hospitality)."
        ),
        "key_drivers": [
            "Nuclear verdicts in US courts",
            "Litigation funding growth",
            "Plaintiff-bar sophistication",
        ],
        "esg_overlay": "Workforce safety + supply-chain ESG flowing into casualty underwriting governance scores.",
    },
    {
        "slug": "do",
        "name": "D&O",
        "cycle_position": "Softening",
        "rate_change_yoy_pct": -8.0,
        "capacity_state": "Plentiful",
        "capacity_trend": "Expanding",
        "loss_trend": "Improving",
        "summary": (
            "Decisive softening after years of hardening. New entrants, "
            "easier capacity, and a quieter securities-class-action "
            "environment. Mid-market and public D&O competition fierce."
        ),
        "key_drivers": [
            "SCA filings down YoY",
            "Bermuda + Lloyd's capacity inflow",
            "IPO pipeline subdued",
        ],
        "esg_overlay": "ESG disclosure litigation rising — carriers asking about climate / DE&I governance practices.",
    },
    {
        "slug": "medprof",
        "name": "Medical Professional",
        "cycle_position": "Hardening",
        "rate_change_yoy_pct": 6.0,
        "capacity_state": "Tight",
        "capacity_trend": "Contracting",
        "loss_trend": "Deteriorating",
        "summary": (
            "Continued hardening driven by jury-verdict severity and "
            "long-tail claim development. Hospital and physician-group "
            "markets under particular pressure."
        ),
        "key_drivers": [
            "Severity inflation in malpractice claims",
            "Staffing shortages affecting risk profile",
            "Telehealth claim experience emerging",
        ],
        "esg_overlay": "Workforce wellbeing + clinical governance increasingly factored into ESG ratings.",
    },
    {
        "slug": "energy",
        "name": "Energy",
        "cycle_position": "Mixed",
        "rate_change_yoy_pct": 3.5,
        "capacity_state": "Bifurcated",
        "capacity_trend": "Shifting to renewables",
        "loss_trend": "Stable",
        "summary": (
            "Capacity flowing strongly to renewables and transition; "
            "fossil-fuel capacity narrowing as ESG-led insurers withdraw. "
            "Property+casualty packages remain on rate."
        ),
        "key_drivers": [
            "Major insurer fossil-fuel exits",
            "Renewable capacity competition",
            "ESG-driven divestment continuing",
        ],
        "esg_overlay": "Most acute ESG-led capacity shift in any line. Critical to broker placement strategy.",
    },
    {
        "slug": "fi",
        "name": "Financial Institutions",
        "cycle_position": "Softening",
        "rate_change_yoy_pct": -5.0,
        "capacity_state": "Plentiful",
        "capacity_trend": "Expanding",
        "loss_trend": "Stable",
        "summary": (
            "FI market following D&O downward. Plenty of capacity "
            "competing for clean financial-institution risks; complex "
            "challenged risks (crypto-adjacent, neobank) selectively "
            "underwritten."
        ),
        "key_drivers": [
            "Regulatory environment stabilising",
            "Crypto-adjacent risk appetite low",
            "Pension / asset-manager risk well understood",
        ],
        "esg_overlay": "Stewardship + investment-policy ESG factored into FI underwriting governance.",
    },
]


# ============================================================================
# Recent loss events affecting market direction
# ============================================================================

RECENT_LOSS_EVENTS: list[dict] = [
    {
        "headline": "Major US healthcare ransomware incident",
        "line": "cyber",
        "date": "Apr 2026",
        "estimated_industry_loss_usd_bn": 2.4,
        "implication": "Drives slight tightening on hospital cyber; broader market still softening.",
    },
    {
        "headline": "Atlantic hurricane season above average",
        "line": "property",
        "date": "Sep-Oct 2025",
        "estimated_industry_loss_usd_bn": 22.0,
        "implication": "Continued pressure on Gulf / South-East CAT property; tightening at 1/1 renewals.",
    },
    {
        "headline": "California wildfire complex",
        "line": "property",
        "date": "Aug 2025",
        "estimated_industry_loss_usd_bn": 8.5,
        "implication": "Wildland-urban interface property capacity contracting further.",
    },
    {
        "headline": "Mass securities-class-action filing — tech sector",
        "line": "do",
        "date": "Feb 2026",
        "estimated_industry_loss_usd_bn": 0.9,
        "implication": "Reminder that D&O softening is line-of-sight, not destination.",
    },
    {
        "headline": "Trial-bar verdict — $750M GL",
        "line": "casualty",
        "date": "Mar 2026",
        "estimated_industry_loss_usd_bn": 0.75,
        "implication": "Social-inflation tailwind continues; umbrella attachments rising.",
    },
    {
        "headline": "European energy ESG protest action",
        "line": "energy",
        "date": "Jun 2026",
        "estimated_industry_loss_usd_bn": 0.3,
        "implication": "Reputation / business interruption risk for fossil-fuel insureds; ESG capacity shift acceleration.",
    },
]


# ============================================================================
# ESG / Climate signals
# ============================================================================
#
# Per-vertical ESG positioning. Used in client-health and aggregation
# views to surface ESG-relevant signals consistently.

ESG_VERTICAL_PROFILE: dict[str, dict] = {
    "technology": {
        "carbon_intensity": "Low",
        "physical_climate_risk": "Low-to-moderate",
        "transition_risk": "Low",
        "governance_focus": ["Data ethics", "Workforce diversity", "AI accountability"],
        "esg_score_band": "Strong",
    },
    "healthcare": {
        "carbon_intensity": "Moderate",
        "physical_climate_risk": "Moderate",
        "transition_risk": "Low",
        "governance_focus": ["Patient safety", "Clinical governance", "Supply-chain integrity"],
        "esg_score_band": "Average",
    },
    "manufacturing": {
        "carbon_intensity": "High",
        "physical_climate_risk": "Moderate-to-high",
        "transition_risk": "Moderate",
        "governance_focus": ["Worker safety", "Supply-chain ESG", "Emissions reporting"],
        "esg_score_band": "Average",
    },
    "energy-power": {
        "carbon_intensity": "Very high (legacy) / Low (renewable)",
        "physical_climate_risk": "Moderate-to-high",
        "transition_risk": "High",
        "governance_focus": ["Energy transition", "Stranded asset risk", "Just transition"],
        "esg_score_band": "Mixed",
    },
    "financial-institutions": {
        "carbon_intensity": "Low (operations) / via portfolio",
        "physical_climate_risk": "Low",
        "transition_risk": "Moderate (financed emissions)",
        "governance_focus": ["Stewardship", "Climate disclosure", "Financed emissions"],
        "esg_score_band": "Strong",
    },
    "real-estate": {
        "carbon_intensity": "Moderate",
        "physical_climate_risk": "High",
        "transition_risk": "Moderate",
        "governance_focus": ["Building efficiency", "Climate resilience", "Tenant ESG"],
        "esg_score_band": "Average",
    },
    "construction": {
        "carbon_intensity": "High",
        "physical_climate_risk": "Moderate",
        "transition_risk": "Moderate",
        "governance_focus": ["Worker safety", "Embodied carbon", "Local community"],
        "esg_score_band": "Average",
    },
    "public-sector": {
        "carbon_intensity": "Moderate",
        "physical_climate_risk": "Moderate-to-high",
        "transition_risk": "Low",
        "governance_focus": ["Climate resilience", "Equity", "Procurement integrity"],
        "esg_score_band": "Average",
    },
}


# ============================================================================
# Per-industry x peril CAT exposure factors (used by risk aggregation)
# ============================================================================
#
# Each pair (industry vertical, peril) -> relative exposure factor
# 0.0-1.0. Used to compute book-level concentration in a CAT scenario.

CAT_PERILS: list[dict] = [
    {"slug": "atlantic-hurricane", "name": "Atlantic Hurricane", "icon": "Cloud"},
    {"slug": "wildfire", "name": "Wildfire (West Coast)", "icon": "Flame"},
    {"slug": "earthquake-cascadia", "name": "Cascadia Earthquake", "icon": "Activity"},
    {"slug": "cyber-ransomware-wave", "name": "Ransomware Wave", "icon": "ShieldAlert"},
    {"slug": "cloud-outage", "name": "Cloud Outage", "icon": "CloudOff"},
    {"slug": "supply-chain-disruption", "name": "Supply Chain Shock", "icon": "Network"},
]

CAT_EXPOSURE_FACTORS: dict[tuple[str, str], float] = {
    # technology
    ("technology", "atlantic-hurricane"): 0.10,
    ("technology", "wildfire"): 0.15,
    ("technology", "earthquake-cascadia"): 0.30,
    ("technology", "cyber-ransomware-wave"): 0.65,
    ("technology", "cloud-outage"): 0.85,
    ("technology", "supply-chain-disruption"): 0.40,
    # healthcare
    ("healthcare", "atlantic-hurricane"): 0.50,
    ("healthcare", "wildfire"): 0.30,
    ("healthcare", "earthquake-cascadia"): 0.40,
    ("healthcare", "cyber-ransomware-wave"): 0.80,
    ("healthcare", "cloud-outage"): 0.55,
    ("healthcare", "supply-chain-disruption"): 0.60,
    # manufacturing
    ("manufacturing", "atlantic-hurricane"): 0.75,
    ("manufacturing", "wildfire"): 0.55,
    ("manufacturing", "earthquake-cascadia"): 0.60,
    ("manufacturing", "cyber-ransomware-wave"): 0.45,
    ("manufacturing", "cloud-outage"): 0.30,
    ("manufacturing", "supply-chain-disruption"): 0.85,
    # energy-power
    ("energy-power", "atlantic-hurricane"): 0.85,
    ("energy-power", "wildfire"): 0.70,
    ("energy-power", "earthquake-cascadia"): 0.75,
    ("energy-power", "cyber-ransomware-wave"): 0.55,
    ("energy-power", "cloud-outage"): 0.40,
    ("energy-power", "supply-chain-disruption"): 0.70,
    # financial-institutions
    ("financial-institutions", "atlantic-hurricane"): 0.20,
    ("financial-institutions", "wildfire"): 0.15,
    ("financial-institutions", "earthquake-cascadia"): 0.25,
    ("financial-institutions", "cyber-ransomware-wave"): 0.75,
    ("financial-institutions", "cloud-outage"): 0.70,
    ("financial-institutions", "supply-chain-disruption"): 0.40,
    # real-estate
    ("real-estate", "atlantic-hurricane"): 0.85,
    ("real-estate", "wildfire"): 0.70,
    ("real-estate", "earthquake-cascadia"): 0.75,
    ("real-estate", "cyber-ransomware-wave"): 0.25,
    ("real-estate", "cloud-outage"): 0.20,
    ("real-estate", "supply-chain-disruption"): 0.30,
    # construction
    ("construction", "atlantic-hurricane"): 0.70,
    ("construction", "wildfire"): 0.60,
    ("construction", "earthquake-cascadia"): 0.65,
    ("construction", "cyber-ransomware-wave"): 0.20,
    ("construction", "cloud-outage"): 0.20,
    ("construction", "supply-chain-disruption"): 0.65,
    # public-sector
    ("public-sector", "atlantic-hurricane"): 0.65,
    ("public-sector", "wildfire"): 0.55,
    ("public-sector", "earthquake-cascadia"): 0.60,
    ("public-sector", "cyber-ransomware-wave"): 0.70,
    ("public-sector", "cloud-outage"): 0.45,
    ("public-sector", "supply-chain-disruption"): 0.50,
}


def cat_factor(vertical_slug: Optional[str], peril_slug: str) -> float:
    if not vertical_slug:
        return 0.4  # neutral default
    return CAT_EXPOSURE_FACTORS.get((vertical_slug, peril_slug), 0.3)


def get_carrier(slug: str) -> Optional[dict]:
    return next((c for c in CARRIER_UNIVERSE if c["slug"] == slug), None)


def get_vertical(slug: str) -> Optional[dict]:
    return next((v for v in MARSH_VERTICALS if v["slug"] == slug), None)


# ============================================================================
# Engagement scoring (synthesised from existing data)
# ============================================================================

def engagement_score_for(
    open_query_count: int,
    avg_response_hours: Optional[float],
    months_since_last_message: Optional[float],
    has_recent_signal_update: bool,
) -> tuple[int, str]:
    """Synthesise a 0-100 engagement score + descriptor.

    Inputs are derived from the existing communications + submissions
    data per client. Score is intentionally heuristic -- v8.3 would
    measure actual portal login / activity once that telemetry exists.
    """
    score = 60  # neutral baseline

    # Open queries are positive signal (active relationship) up to 3,
    # then negative (broker is behind)
    if 1 <= open_query_count <= 2:
        score += 15
    elif open_query_count >= 3:
        score -= 10

    # Fast response is positive
    if avg_response_hours is not None:
        if avg_response_hours < 24:
            score += 15
        elif avg_response_hours < 72:
            score += 5
        else:
            score -= 10

    # Recency
    if months_since_last_message is not None:
        if months_since_last_message < 1:
            score += 10
        elif months_since_last_message < 3:
            score += 0
        elif months_since_last_message < 6:
            score -= 10
        else:
            score -= 20

    if has_recent_signal_update:
        score += 5

    score = max(5, min(100, score))

    if score >= 80:
        descriptor = "Strong"
    elif score >= 60:
        descriptor = "Healthy"
    elif score >= 40:
        descriptor = "Moderate"
    elif score >= 20:
        descriptor = "Quiet"
    else:
        descriptor = "Dormant"

    return score, descriptor
