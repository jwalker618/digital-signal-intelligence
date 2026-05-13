# V7 Phase 12: Mechanism Memory — Cross-Cycle Learning

## Depends on
- Phase 6 (validator-confirmed signals).
- Phase 8 (reproducibility class — only `stable` signals are eligible as mechanism sources).
- Phase 9 (primitive_type — mechanisms are keyed by primitive).
- Phase 10 (cluster + symptoms — mechanism source is a cluster, not a single hit).

## Blocks
- Phase 14 (frontend exposes mechanism panels alongside grade).

## Scope

Lifted from Clearwing's `mechanism_memory.py:57-99, 105-133`. After a high-confidence audit-grade signal is confirmed (graded `structured_attested`+, validator advanced, reproducibility `stable`, clustered with ≥1 deterministic contributor), extract its **abstract risk-pattern** via LLM and persist it in an append-only JSONL store. On subsequent cycles for any entity, recall top-K relevant mechanisms by primitive + sector + keyword similarity, inject them as priors into validator and (Phase 6) prompts to sharpen counter-argument generation.

Mechanisms are **abstract** — they strip entity names, specific dates, file paths. They keep the pattern. Example mechanism extracted from a confirmed director-litigation cluster: "Director with >3 securities-class actions on prior listed companies AND board overlap ≥2 with sanctioned counterparty → governance signal corroborated by both Companies House and CourtListener."

Three recall backends with automatic fallback (Clearwing pattern):

- `keyword` — primitive + sector + tag overlap. Cheapest. Always available.
- `tfidf` — pure-python TF-IDF over the mechanism summary. Default in V7.
- `chromadb` — embeddings recall when `CHROMADB_URL` env var set. Best quality, optional dependency.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Storage | `~/.dsi/mechanisms.jsonl` (append-only). DB-backed alternative deferred to V8 |
| D2 | Eligibility | `evidence_grade >= structured_attested` AND validator `advance=True` AND reproducibility `stable` AND cluster `deterministic=True` |
| D3 | Extraction | One LLM call per eligible signal; ~150 tokens output JSON |
| D4 | Abstract | Mechanism MUST strip entity names, addresses, dates, file paths, jurisdiction names. Generic keywords only |
| D5 | Recall backends | `keyword` always, `tfidf` default, `chromadb` opt-in via env var. Auto-fallback on runtime error in higher backend |
| D6 | Top-K | Recall returns top 3 mechanisms per (primitive, sector) at cycle start. Injected into validator prompts and disclosure packets |
| D7 | Pruning | Mechanisms with `last_recalled_at` older than 365 days AND `recall_count < 3` are archived (moved to `mechanisms_archive.jsonl`) |
| D8 | Idempotency | A mechanism with the same `canonical_signature` (hash of `summary` + `primitive_type`) is not re-stored. Existing record's `recall_count` not affected by extraction; only by recall |
| D9 | Privacy | Mechanisms are tenant-scoped: store path is `~/.dsi/<tenant_id>/mechanisms.jsonl`. Cross-tenant recall forbidden |
| D10 | LLM-extraction failure | Returns `None`; no row stored. Audit-logged `mechanism_extraction_failed` |

## Files

### Create
- `signal_architecture/mechanism/__init__.py`
- `signal_architecture/mechanism/types.py`
- `signal_architecture/mechanism/store.py`
- `signal_architecture/mechanism/extractor.py`
- `signal_architecture/mechanism/recall.py`
- `signal_architecture/mechanism/prompts.py`
- `tests/unit/test_mechanism_extractor.py`
- `tests/unit/test_mechanism_store.py`
- `tests/unit/test_mechanism_recall.py`

### Modify
- `layers/risk/workflow.py` — extract eligible mechanisms at cycle-commit-after-Phase-6; inject recall at cycle-start
- `signal_architecture/validation/validator.py` — accept `priors: list[Mechanism]` in `ValidatorInput`; prompt receives them as context
- `infrastructure/models/config_schema.py` — add `MechanismMemoryPolicy`

## Types

`signal_architecture/mechanism/types.py`:

```python
"""V7 Phase 12 — mechanism-memory types."""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=False)
class Mechanism:
    """Abstract risk pattern extracted from a verified signal."""
    id: str
    summary: str                  # one-sentence abstract mechanism, no entity/date/path
    primitive_type: str           # e.g. "governance"
    sector_tags: list[str]        # ["fi", "do"] — coverages where this could recur
    tags: list[str]               # mechanism-level tags
    keywords: list[str]           # bag for recall
    what_made_it_high_grade: str  # brief explanation of why it earned structured_attested
    source_cluster_id: str        # cluster_id of the originating signal
    source_signal_id: str
    source_cycle_id: str          # model_version_id of the origin cycle
    first_seen: float = field(default_factory=time.time)
    last_recalled_at: float = 0.0
    recall_count: int = 0

    @property
    def canonical_signature(self) -> str:
        key = f"{self.primitive_type}::{self.summary.strip().lower()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "primitive_type": self.primitive_type,
            "sector_tags": self.sector_tags,
            "tags": self.tags,
            "keywords": self.keywords,
            "what_made_it_high_grade": self.what_made_it_high_grade,
            "source_cluster_id": self.source_cluster_id,
            "source_signal_id": self.source_signal_id,
            "source_cycle_id": self.source_cycle_id,
            "first_seen": self.first_seen,
            "last_recalled_at": self.last_recalled_at,
            "recall_count": self.recall_count,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Mechanism":
        return cls(
            id=d["id"],
            summary=d["summary"],
            primitive_type=d["primitive_type"],
            sector_tags=list(d.get("sector_tags", [])),
            tags=list(d.get("tags", [])),
            keywords=list(d.get("keywords", [])),
            what_made_it_high_grade=d.get("what_made_it_high_grade", ""),
            source_cluster_id=d.get("source_cluster_id", ""),
            source_signal_id=d.get("source_signal_id", ""),
            source_cycle_id=d.get("source_cycle_id", ""),
            first_seen=float(d.get("first_seen", time.time())),
            last_recalled_at=float(d.get("last_recalled_at", 0.0)),
            recall_count=int(d.get("recall_count", 0)),
        )
```

## Prompts

`signal_architecture/mechanism/prompts.py`:

```python
"""V7 Phase 12 — extraction + abstraction prompts.

Extraction MUST strip entity names, addresses, dates, file paths, and
jurisdiction names. The system prompt forbids them.
"""

EXTRACTION_SYSTEM = """\
You are extracting an ABSTRACT risk mechanism from a verified insurance signal.

Goal: produce a pattern that might apply to OTHER entities.

CRITICAL RULES:
- DO NOT name the entity, its officers, addresses, jurisdictions, or any case numbers.
- DO NOT include specific dates.
- DO use generic role nouns: "director", "subsidiary", "regulator".
- DO use generic source types: "structured register", "court index", "regulator filing".

Return ONLY this JSON:
{
  "summary": "one sentence, abstract, entity-anonymous",
  "tags": ["snake_case", "tags"],
  "keywords": ["words", "useful", "for", "recall"],
  "what_made_it_high_grade": "brief — why this earned structured_attested or higher"
}

Examples:

Input: cluster of OFAC SDN listing + UK FCA enforcement + press confirmation
       (sanctions_screening_result, structured_attested, validator advanced).
Output:
{
  "summary": "Entity carries an SDN listing corroborated by a separate regulator enforcement action and contemporaneous press coverage",
  "tags": ["sdn", "regulator_corroboration", "press_corroboration"],
  "keywords": ["sdn", "sanctions", "regulator", "enforcement", "press"],
  "what_made_it_high_grade": "Two independent authoritative registers plus an independent reputational signal agreed on the same listing window"
}
"""


def build_extraction_user(payload_json: str) -> str:
    return f"Extract mechanism from this verified signal cluster:\n\n{payload_json}\n"
```

## Store

`signal_architecture/mechanism/store.py`:

```python
"""V7 Phase 12 — append-only JSONL store + archival.

Path convention: ~/.dsi/<tenant_id>/mechanisms.jsonl
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Iterable

from .types import Mechanism

DEFAULT_BASE = Path.home() / ".dsi"


def _store_path(tenant_id: str, base: Path | None = None) -> Path:
    base = base or DEFAULT_BASE
    p = base / tenant_id / "mechanisms.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _archive_path(tenant_id: str, base: Path | None = None) -> Path:
    base = base or DEFAULT_BASE
    p = base / tenant_id / "mechanisms_archive.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_all(tenant_id: str, base: Path | None = None) -> list[Mechanism]:
    p = _store_path(tenant_id, base)
    if not p.exists():
        return []
    out: list[Mechanism] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(Mechanism.from_dict(json.loads(line)))
        except (json.JSONDecodeError, KeyError):
            continue
    return out


def existing_signatures(tenant_id: str, base: Path | None = None) -> set[str]:
    return {m.canonical_signature for m in load_all(tenant_id, base)}


def append(tenant_id: str, mechanism: Mechanism, base: Path | None = None) -> bool:
    """Append unless canonical_signature already present. Returns True on insert."""
    if mechanism.canonical_signature in existing_signatures(tenant_id, base):
        return False
    p = _store_path(tenant_id, base)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(mechanism.to_dict(), sort_keys=True) + "\n")
    return True


def update_recall(tenant_id: str, mechanism_id: str, base: Path | None = None) -> None:
    """Increment recall_count and stamp last_recalled_at by rewriting the JSONL.

    JSONL is small (<10k rows expected per tenant for years). Full rewrite is fine.
    For high-volume tenants we move to SQLite in V8.
    """
    p = _store_path(tenant_id, base)
    if not p.exists():
        return
    rows = load_all(tenant_id, base)
    now = time.time()
    changed = False
    for m in rows:
        if m.id == mechanism_id:
            m.last_recalled_at = now
            m.recall_count += 1
            changed = True
            break
    if not changed:
        return
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for m in rows:
            f.write(json.dumps(m.to_dict(), sort_keys=True) + "\n")
    tmp.replace(p)


def prune_old(
    tenant_id: str,
    *,
    base: Path | None = None,
    older_than_days: int = 365,
    min_recall_count: int = 3,
) -> int:
    rows = load_all(tenant_id, base)
    now = time.time()
    cutoff = now - older_than_days * 86400
    keep, archive = [], []
    for m in rows:
        if m.recall_count < min_recall_count and m.last_recalled_at and m.last_recalled_at < cutoff:
            archive.append(m)
        else:
            keep.append(m)
    if not archive:
        return 0
    p = _store_path(tenant_id, base)
    a = _archive_path(tenant_id, base)
    with a.open("a", encoding="utf-8") as f:
        for m in archive:
            f.write(json.dumps(m.to_dict(), sort_keys=True) + "\n")
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for m in keep:
            f.write(json.dumps(m.to_dict(), sort_keys=True) + "\n")
    tmp.replace(p)
    return len(archive)
```

## Extraction

`signal_architecture/mechanism/extractor.py`:

```python
from __future__ import annotations

import json
import re
import uuid
from typing import Optional

from signal_architecture.signals.types import SignalResult
from .prompts import EXTRACTION_SYSTEM, build_extraction_user
from .types import Mechanism


def is_eligible(sig: SignalResult, *, validator_advanced: bool) -> bool:
    if not validator_advanced:
        return False
    if sig.evidence_grade not in ("structured_attested", "behaviourally_validated"):
        return False
    if sig.reproducibility != "stable":
        return False
    if not sig.metadata or not sig.metadata.get("cluster_id"):
        return False
    if sig.metadata.get("deterministic") is False:
        return False
    return True


def _strip_disallowed(text: str) -> str:
    """Best-effort scrubbing. The prompt instructs the LLM, but we belt-and-brace."""
    # 4-digit year
    text = re.sub(r"\b(19|20)\d{2}\b", "<YEAR>", text)
    # Title-cased multi-word proper nouns (rough): "Jane Smith", "Acme Plc"
    text = re.sub(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b", "<NAME>", text)
    return text


def extract_mechanism(
    llm,
    sig: SignalResult,
    *,
    sector_tags: list[str],
    cycle_id: str,
) -> Optional[Mechanism]:
    payload = {
        "primitive_type": sig.primitive_type,
        "fact_class": sig.metadata.get("fact_class"),
        "cluster_size": len(sig.metadata.get("symptoms") or []),
        "evidence_grade": sig.evidence_grade,
        "evidence_basis": _strip_disallowed(sig.evidence_basis or ""),
        "reproducibility": sig.reproducibility,
    }
    try:
        resp = llm.aask_text(system=EXTRACTION_SYSTEM, user=build_extraction_user(json.dumps(payload))).first_text() or ""
    except Exception:
        return None
    match = re.search(r"\{[\s\S]*\}", resp)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    summary = _strip_disallowed((data.get("summary") or "").strip())
    if not summary:
        return None
    return Mechanism(
        id=f"mech-{uuid.uuid4().hex[:10]}",
        summary=summary,
        primitive_type=sig.primitive_type or "unknown",
        sector_tags=sector_tags,
        tags=[t for t in (data.get("tags") or []) if isinstance(t, str)],
        keywords=[k for k in (data.get("keywords") or []) if isinstance(k, str)],
        what_made_it_high_grade=_strip_disallowed(data.get("what_made_it_high_grade") or ""),
        source_cluster_id=sig.metadata.get("cluster_id", ""),
        source_signal_id=sig.signal_id,
        source_cycle_id=cycle_id,
    )
```

## Recall

`signal_architecture/mechanism/recall.py`:

```python
"""V7 Phase 12 — three recall backends with automatic fallback.

Public API:
    recall(tenant_id, *, primitive_type, coverage, query_text, top_k=3) -> list[Mechanism]
"""
from __future__ import annotations

import math
import os
import re
from collections import Counter
from typing import Optional

from .store import load_all, update_recall
from .types import Mechanism


_TOKEN_RE = re.compile(r"\b[a-z][a-z0-9_]+\b")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


# ---------------------------------------------------------------------------
# Keyword backend
# ---------------------------------------------------------------------------

def _keyword_score(m: Mechanism, *, primitive_type: str, coverage: str, q_tokens: set[str]) -> float:
    score = 0.0
    if m.primitive_type == primitive_type:
        score += 2.0
    if coverage in m.sector_tags:
        score += 1.0
    overlap = len(q_tokens & set(m.keywords) | (q_tokens & set(m.tags)))
    score += overlap * 0.5
    return score


# ---------------------------------------------------------------------------
# TF-IDF backend
# ---------------------------------------------------------------------------

def _build_tfidf(mechanisms: list[Mechanism]) -> tuple[dict, dict, list[Counter]]:
    """Precompute IDF + per-doc term frequencies."""
    docs = [_tokens(" ".join([m.summary, " ".join(m.tags), " ".join(m.keywords)])) for m in mechanisms]
    tfs = [Counter(d) for d in docs]
    n = len(mechanisms)
    df: Counter[str] = Counter()
    for d in docs:
        for t in set(d):
            df[t] += 1
    idf = {t: math.log((1 + n) / (1 + dfv)) + 1.0 for t, dfv in df.items()}
    return idf, df, tfs


def _tfidf_score(q_tokens: list[str], idf: dict, tf: Counter) -> float:
    score = 0.0
    for t in q_tokens:
        if t in tf:
            score += tf[t] * idf.get(t, 0.0)
    return score


# ---------------------------------------------------------------------------
# Chromadb backend (opt-in)
# ---------------------------------------------------------------------------

def _chromadb_available() -> bool:
    try:
        import chromadb  # noqa: F401
        return bool(os.environ.get("CHROMADB_URL"))
    except ImportError:
        return False


def _chromadb_score(query_text: str, mechanisms: list[Mechanism]) -> list[tuple[Mechanism, float]]:
    import chromadb  # type: ignore
    # Implementation: connect, embed query, embed mechanism corpus, cosine.
    # Out-of-scope detail. Returns sorted [(m, score)].
    raise NotImplementedError("chromadb backend stub")


# ---------------------------------------------------------------------------
# Public recall
# ---------------------------------------------------------------------------

def recall(
    tenant_id: str,
    *,
    primitive_type: str,
    coverage: str,
    query_text: str,
    top_k: int = 3,
) -> list[Mechanism]:
    """Top-K mechanisms by (primitive_type + coverage + query) similarity.

    Backend selection:
        1. chromadb if CHROMADB_URL set AND chromadb installed
        2. tfidf (default)
        3. keyword (fallback if tfidf raises)

    Each recalled mechanism has its recall_count incremented.
    """
    mechanisms = load_all(tenant_id)
    if not mechanisms:
        return []
    if _chromadb_available():
        try:
            scored = _chromadb_score(query_text, mechanisms)
            top = [m for m, _ in scored[:top_k]]
            for m in top:
                update_recall(tenant_id, m.id)
            return top
        except Exception:
            pass
    # tfidf
    try:
        idf, _df, tfs = _build_tfidf(mechanisms)
        q = _tokens(query_text)
        scored = sorted(
            zip(mechanisms, tfs),
            key=lambda mt: _tfidf_score(q, idf, mt[1]) + _keyword_score(
                mt[0], primitive_type=primitive_type, coverage=coverage, q_tokens=set(q),
            ),
            reverse=True,
        )
        top = [m for m, _ in scored[:top_k]]
        for m in top:
            update_recall(tenant_id, m.id)
        return top
    except Exception:
        pass
    # keyword fallback
    q = set(_tokens(query_text))
    scored = sorted(
        mechanisms,
        key=lambda m: _keyword_score(m, primitive_type=primitive_type, coverage=coverage, q_tokens=q),
        reverse=True,
    )
    top = scored[:top_k]
    for m in top:
        update_recall(tenant_id, m.id)
    return top
```

## Workflow integration

`layers/risk/workflow.py`:

```python
from signal_architecture.mechanism.extractor import extract_mechanism, is_eligible
from signal_architecture.mechanism.recall import recall
from signal_architecture.mechanism.store import append, prune_old


def _at_cycle_start_inject_priors(self, ctx, signals_planned, *, tenant_id):
    """Called BEFORE the validator runs. Sets ctx.priors for each primitive."""
    by_primitive: dict[str, list[Mechanism]] = {}
    for prim in set(self._predict_primitives(signals_planned)):
        by_primitive[prim] = recall(
            tenant_id=tenant_id,
            primitive_type=prim,
            coverage=ctx.coverage,
            query_text=ctx.entity_profile_text,
            top_k=3,
        )
    ctx.priors_by_primitive = by_primitive


def _at_cycle_commit_extract_mechanisms(self, ctx, committed_signals, validator_verdicts, *, tenant_id, cycle_id):
    """Called AFTER commit. Extracts mechanisms from eligible signals."""
    sector_tags = [ctx.coverage]
    for sig in committed_signals:
        v = validator_verdicts.get(sig.signal_id)
        if not is_eligible(sig, validator_advanced=bool(v and v.advance)):
            continue
        m = extract_mechanism(ctx.llm, sig, sector_tags=sector_tags, cycle_id=cycle_id)
        if m is None:
            self._audit("mechanism_extraction_failed", signal_id=sig.signal_id, payload={})
            continue
        if append(tenant_id, m):
            self._audit("mechanism_stored", signal_id=sig.signal_id, payload={"mechanism_id": m.id})
        else:
            self._audit("mechanism_duplicate_skipped", signal_id=sig.signal_id, payload={"signature": m.canonical_signature})
    # Background prune
    if random.random() < 0.05:  # 1-in-20 cycles
        prune_old(tenant_id)
```

The validator (Phase 6) accepts `priors_by_primitive[sig.primitive_type]` and pre-prompts:

```text
Known patterns for this risk primitive (anonymous, abstract):
  - <mechanism.summary>
  - <mechanism.summary>
  - <mechanism.summary>
Use these to sharpen your counter-argument: ask whether the current signal
fits the pattern or breaks it.
```

## Steps

### 12.1 — Module skeleton
**Files**: `signal_architecture/mechanism/{__init__.py,types.py,prompts.py,store.py,extractor.py,recall.py}`.
**Action**: Drop in code.

### 12.2 — Unit tests
**Files**:
- `tests/unit/test_mechanism_store.py` — append + dedup by signature, update_recall increments, prune moves to archive.
- `tests/unit/test_mechanism_extractor.py` — eligibility gating, stripping of years and proper nouns, JSON parse failures yield None.
- `tests/unit/test_mechanism_recall.py` — keyword backend deterministic; tfidf gives sensible ranking on a synthetic corpus; backend fallback when tfidf raises.

### 12.3 — Workflow integration
**File**: `layers/risk/workflow.py`.
**Action**:
- Add `_at_cycle_start_inject_priors` and `_at_cycle_commit_extract_mechanisms`.
- Tenant id resolution: from submission ctx.

### 12.4 — Validator integration
**File**: `signal_architecture/validation/validator.py`.
**Action**:
- Accept optional `priors: list[Mechanism]` argument.
- Prepend the priors block to the user message when present.
- Add `priors_used` field to `ValidatorVerdict.raw_response` metadata so audit trail records the priors that were in scope.

### 12.5 — Policy
**File**: `infrastructure/models/config_schema.py`.
**Action**:
```python
class MechanismMemoryPolicy(StrictModel):
    enabled: bool = True
    top_k: int = Field(default=3, ge=0, le=10)


class EvidenceGradePolicy(StrictModel):
    # ... existing ...
    mechanism_memory: MechanismMemoryPolicy = Field(default_factory=MechanismMemoryPolicy)
```

### 12.6 — Privacy gate
**Action**: Tenant id is required. Store path includes tenant id; no global mechanism store. Test asserts that calling `recall(tenant_a)` returns no rows from tenant_b.

## Test gates

```bash
pytest tests/unit/test_mechanism_store.py \
        tests/unit/test_mechanism_extractor.py \
        tests/unit/test_mechanism_recall.py -v

# End-to-end: seed bench across two cycles for the same entity. Cycle 1
# extracts mechanisms; Cycle 2 recall returns them.
python -m seed bench

# Calibration unchanged: priors only influence the validator's prompt;
# they do not modify scores.
python -m layers.risk.calibration_harness fi cyber casualty
```

## Done when

- [ ] Eligibility correctly gates on grade + validator + reproducibility + cluster.
- [ ] Mechanisms are abstract (no entity names, addresses, dates, jurisdictions) — `_strip_disallowed` plus prompt enforce.
- [ ] Append dedups by canonical signature.
- [ ] Recall ranking deterministic for the same store + same query.
- [ ] Backend fallback works: with `CHROMADB_URL` unset, tfidf runs; if tfidf raises (mock), keyword runs.
- [ ] Cross-tenant isolation: no mechanism from tenant A reachable from tenant B.
- [ ] Calibration unchanged.
- [ ] Full pytest green.

## Out of scope

- SQL-backed mechanism store. → V8.
- Mechanism-driven *generation* of new signals (Phase 11 does within-cycle amplification; this phase is cross-cycle priors only).
- Frontend mechanism inspector. → Phase 14.

## Invariants

1. Mechanisms are entity-anonymous post-extraction (best-effort: prompt rules + scrubber).
2. Recall increments `recall_count` and updates `last_recalled_at`.
3. Pruning never deletes mechanisms with `recall_count >= 3`.
4. Cross-tenant recall is impossible: store path is tenant-scoped.
5. No pricing impact.
