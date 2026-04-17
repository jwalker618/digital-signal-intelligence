"""V6/E9 — canonical 7-category taxonomy.

Enforced at:
- `development/project/assessments/scripts/assess_config_compliance.py`
  (currently emits warnings; after the one-time migration script runs
  the check becomes a hard error).
- `infrastructure.builder.signal_library.SignalLibrary.validate_signal`
  (added via this module).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Tuple


@dataclass(frozen=True)
class CanonicalCategory:
    """One of the seven canonical DSI signal categories."""
    id: str
    name: str
    description: str


CANONICAL_CATEGORIES: Tuple[CanonicalCategory, ...] = (
    CanonicalCategory(
        id="network_authority",
        name="Network Authority",
        description=(
            "DNS, WHOIS, BGP and registrar observations — the legal + "
            "operational identity of the domain/ASN envelope."
        ),
    ),
    CanonicalCategory(
        id="technical_infrastructure",
        name="Technical Infrastructure",
        description=(
            "Observable technical posture: TLS, headers, ports, CVEs, "
            "CDN, cloud-hosting, email-auth, patch cadence."
        ),
    ),
    CanonicalCategory(
        id="corporate_footprint",
        name="Corporate Digital Footprint",
        description=(
            "Web presence, social, content, hiring, brand signals that "
            "describe the entity's operating posture."
        ),
    ),
    CanonicalCategory(
        id="behavioural",
        name="Behavioural",
        description=(
            "Derived behaviours over time: drift, velocity, incident "
            "response cadence, patch-window consistency."
        ),
    ),
    CanonicalCategory(
        id="public_record",
        name="Public Record",
        description=(
            "Regulatory, litigation, sanctions, and corporate-registry "
            "data. Single most reliable evidence channel."
        ),
    ),
    CanonicalCategory(
        id="structured_data",
        name="Structured Data",
        description=(
            "Bureau, rating-agency, filings, loss-run, audited financial, "
            "and industry-structured data — paid or regulated sources."
        ),
    ),
    CanonicalCategory(
        id="direct_inquiry",
        name="Direct Inquiry",
        description=(
            "Broker / applicant attested disclosures. Lowest natural "
            "confidence but highest explainability."
        ),
    ),
)

CANONICAL_IDS: FrozenSet[str] = frozenset(c.id for c in CANONICAL_CATEGORIES)

CANONICAL_ID_TO_NAME: Dict[str, str] = {c.id: c.name for c in CANONICAL_CATEGORIES}


def is_canonical(category_id: str) -> bool:
    return category_id in CANONICAL_IDS


def require_canonical(category_id: str) -> None:
    """Raise ``ValueError`` unless ``category_id`` is canonical (E9)."""
    if not is_canonical(category_id):
        raise ValueError(
            f"'{category_id}' is not a canonical V6 category. "
            f"Must be one of {sorted(CANONICAL_IDS)}."
        )
