"""V7 Phase 10 — per-fact-class canonicalisation for root-cause clustering.

`canonical_entity_name` and `canonical_docket` normalise the surface text
so two reports of the SAME underlying event collapse to the same
`canonical_entity_ref` (and therefore the same deterministic cluster key
when no authoritative ID is available).

Deliberately conservative: these strip noise (legal-form suffixes,
punctuation, casing) but never reorder words or apply fuzzy matching —
fuzzy adjudication is the LLM second-pass's job, gated behind a 0.85
similarity floor.
"""
from __future__ import annotations

import re

# Legal-form suffixes stripped from company names. Lower-cased, no dots.
_LEGAL_SUFFIXES = {
    "ltd", "limited", "llc", "inc", "incorporated", "plc", "corp",
    "corporation", "co", "company", "gmbh", "ag", "sa", "sas", "spa",
    "srl", "bv", "nv", "pty", "llp", "lp", "llp", "pllc", " pc",
    "kk", "oyj", "ab", "as", "kft", "sp", "zoo", "ulc",
}

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")


def canonical_entity_name(name: str) -> str:
    """Normalise a company/person name for cluster-key purposes.

    lower-case -> drop punctuation -> collapse whitespace -> strip a
    single trailing legal-form suffix. Empty input -> "".
    """
    if not name:
        return ""
    s = _PUNCT_RE.sub(" ", name.lower())
    s = _WS_RE.sub(" ", s).strip()
    if not s:
        return ""
    tokens = s.split(" ")
    # Strip ONE trailing legal-form suffix token if present.
    if len(tokens) > 1 and tokens[-1] in _LEGAL_SUFFIXES:
        tokens = tokens[:-1]
    return " ".join(tokens)


_DOCKET_PREFIX_RE = re.compile(r"^(case|docket|no\.?|number)\s*[:#]?\s*", re.IGNORECASE)


def canonical_docket(docket: str) -> str:
    """Normalise a court docket / case number.

    Strips leading label tokens ('Case', 'Docket', 'No.', 'Number') —
    repeatedly, so a compound prefix like 'Case No.' is fully consumed —
    then lower-cases, removes punctuation noise, and collapses whitespace.
    Keeps the alphanumeric core intact so two references to the same case
    match.
    """
    if not docket:
        return ""
    s = docket.strip()
    # Strip prefix tokens repeatedly: "Case No. 1:21-cv-..." -> "1:21-cv-...".
    while True:
        stripped = _DOCKET_PREFIX_RE.sub("", s)
        if stripped == s:
            break
        s = stripped
    s = _PUNCT_RE.sub(" ", s.lower())
    s = _WS_RE.sub("", s)  # dockets have no meaningful internal whitespace
    return s


def canonical_identifier(identifier: str) -> str:
    """Normalise an authoritative ID (LEI, registration number, list ID).

    These are already canonical-ish; we just lower-case and strip
    punctuation/whitespace so trivial formatting differences don't split a
    cluster.
    """
    if not identifier:
        return ""
    s = _PUNCT_RE.sub("", identifier.lower())
    return _WS_RE.sub("", s)
