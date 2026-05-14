"""V7 Phase 9 — risk-primitive classification.

`primitive_type` is an axis orthogonal to source taxonomy, coverage, and
signal_id. It answers "which risk primitive does this signal contribute
to?" — letting the platform ask "what's this entity's grade distribution
by risk primitive?", a question DSI couldn't answer before V7.

Classification cascade (first level that resolves wins):
    1. YAML override   — signal_registry[<sig>].primitive_type
    2. signal_id prefix map (most specific prefix first)
    3. coverage default map
    4. LLM fallback    — lazy; only when 1-3 return 'unknown' AND the
                         signal has weight >= 0.05

`classify()` covers levels 1-3 and is pure/deterministic. `llm_fallback()`
is the level-4 escape hatch — callers gate it themselves.
"""
from __future__ import annotations

from typing import Literal, Optional

PrimitiveType = Literal[
    "counterparty",
    "regulatory",
    "operational",
    "financial",
    "reputational",
    "cyber",
    "climate",
    "governance",
    "crime",
    "physical_asset",
    "behavioural",
    "human_capital",
    "unknown",
]

PRIMITIVES: tuple[PrimitiveType, ...] = (
    "counterparty",
    "regulatory",
    "operational",
    "financial",
    "reputational",
    "cyber",
    "climate",
    "governance",
    "crime",
    "physical_asset",
    "behavioural",
    "human_capital",
    "unknown",
)

_VALID: frozenset[str] = frozenset(PRIMITIVES)


# Coverage-level defaults. Used only when the prefix map doesn't resolve.
COVERAGE_DEFAULTS: dict[str, PrimitiveType] = {
    "fi": "financial",
    "financial_institutions": "financial",
    "cyber": "cyber",
    "climate": "climate",
    "marine": "physical_asset",
    "property": "physical_asset",
    "commercial_property": "physical_asset",
    "casualty": "operational",
    "commercial_casualty": "operational",
    "do": "governance",
    "directors_officers": "governance",
    "pi": "operational",
    "professional_indemnity": "operational",
    "fpr": "counterparty",
    "financial_political_risk": "counterparty",
    "aerospace": "physical_asset",
    "energy": "physical_asset",
    "construction": "physical_asset",
    "medprof": "operational",
    "env_liab": "climate",
    "crop": "climate",
    "wc": "human_capital",
    "reinsurance": "counterparty",
    "specie": "physical_asset",
    "captive": "financial",
    "event": "operational",
    "prodlib": "operational",
    "pvt": "physical_asset",
    "teo": "operational",
}


# signal_id prefix -> primitive. First match wins; order matters — list
# more specific prefixes earlier.
SIGNAL_ID_PREFIX_MAP: list[tuple[str, PrimitiveType]] = [
    ("sanctions_",          "regulatory"),
    ("pep_",                "regulatory"),
    ("ofac_",               "regulatory"),
    ("regulatory_",         "regulatory"),
    ("license_",            "regulatory"),
    ("licence_",            "regulatory"),
    ("kyc_",                "regulatory"),
    ("director_litigation", "governance"),
    ("director_",           "governance"),
    ("officer_",            "governance"),
    ("board_",              "governance"),
    ("governance_",         "governance"),
    ("sec_filing",          "financial"),
    ("credit_rating",       "financial"),
    ("financial_",          "financial"),
    ("leverage_",           "financial"),
    ("liquidity_",          "financial"),
    ("solvency_",           "financial"),
    ("security_",           "cyber"),
    ("vuln_",               "cyber"),
    ("breach_",             "cyber"),
    ("tls_",                "cyber"),
    ("dns_",                "cyber"),
    ("patch_",              "behavioural"),
    ("cert_rotation",       "behavioural"),
    ("deployment_",         "behavioural"),
    ("hiring_",             "human_capital"),
    ("workforce_",          "human_capital"),
    ("headcount_",          "human_capital"),
    ("key_person",          "human_capital"),
    ("flood_",              "climate"),
    ("wind_",               "climate"),
    ("seismic_",            "climate"),
    ("wildfire_",           "climate"),
    ("hurricane_",          "climate"),
    ("esg_",                "reputational"),
    ("crime_",              "crime"),
    ("fraud_",              "crime"),
    ("aml_",                "crime"),
    ("money_laundering",    "crime"),
    ("tiv_",                "physical_asset"),
    ("asset_",              "physical_asset"),
    ("location_",           "physical_asset"),
    ("fleet_",              "physical_asset"),
    ("hull_",               "physical_asset"),
    ("alliance_",           "counterparty"),
    ("counterparty_",       "counterparty"),
    ("supply_chain",        "operational"),
    ("operational_",        "operational"),
    ("plant_",              "operational"),
    ("sentiment_",          "reputational"),
    ("sentiment",           "reputational"),
    ("reviews_",            "reputational"),
    ("media_",              "reputational"),
    ("reputation",          "reputational"),
]


def classify(
    *,
    signal_id: str,
    coverage: str,
    yaml_override: Optional[str] = None,
) -> PrimitiveType:
    """Deterministic cascade (levels 1-3). Returns 'unknown' when nothing
    resolves — caller may then invoke `llm_fallback`."""
    # Level 1: explicit YAML override.
    if yaml_override is not None and yaml_override in _VALID:
        return yaml_override  # type: ignore[return-value]
    # Level 2: signal_id prefix map.
    for prefix, prim in SIGNAL_ID_PREFIX_MAP:
        if signal_id.startswith(prefix):
            return prim
    # Level 3: coverage default.
    if coverage in COVERAGE_DEFAULTS:
        return COVERAGE_DEFAULTS[coverage]
    return "unknown"


# Level-4 LLM fallback. Kept tiny — the provider, retry, and JSON parsing
# are stamped in by the project's LLM client. Callers gate invocation
# (only when classify() returns 'unknown' AND signal_weight >= 0.05).

_LLM_SYSTEM = "You are a risk-classification expert."
_LLM_PROMPT = (
    "Classify this insurance pricing signal into exactly one risk primitive "
    "from this list: {primitives}.\n"
    "Return ONLY the primitive name, lowercase, nothing else.\n\n"
    "signal_id: {signal_id}\n"
    "coverage: {coverage}\n"
    "evidence_basis: {basis}\n"
)


def llm_fallback(
    llm_callable,
    *,
    signal_id: str,
    coverage: str,
    evidence_basis: str,
) -> PrimitiveType:
    """Level-4 fallback. `llm_callable` is (system, user) -> str.

    Returns 'unknown' if the LLM returns anything not in PRIMITIVES, so a
    bad model response can never inject a junk primitive.
    """
    user = _LLM_PROMPT.format(
        primitives=", ".join(p for p in PRIMITIVES if p != "unknown"),
        signal_id=signal_id,
        coverage=coverage,
        basis=evidence_basis or "",
    )
    try:
        raw = llm_callable(system=_LLM_SYSTEM, user=user) or ""
    except Exception:  # noqa: BLE001
        return "unknown"
    candidate = raw.strip().lower()
    return candidate if candidate in _VALID else "unknown"  # type: ignore[return-value]
