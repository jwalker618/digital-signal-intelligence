"""V7 Phase 12 — three recall backends with auto-fallback.

Public API: recall(tenant_id, *, primitive_type, coverage, query_text, top_k=3).

Backend selection (highest-quality available wins):
    1. chromadb   — embeddings; opt-in via CHROMADB_URL env + chromadb installed
    2. tfidf      — pure-python TF-IDF + keyword bonus
    3. keyword    — primitive_type + coverage + keyword overlap

If a higher backend raises, the next one runs. Tests can force a
specific backend via `_force_backend`.

Each recalled mechanism has its `recall_count` incremented +
`last_recalled_at` stamped via store.update_recall.
"""
from __future__ import annotations

import math
import os
import re
from collections import Counter
from pathlib import Path
from typing import Optional

from .store import load_all, update_recall
from .types import Mechanism

_TOKEN_RE = re.compile(r"\b[a-z][a-z0-9_]+\b")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


# ---------------------------------------------------------------------------
# Keyword backend
# ---------------------------------------------------------------------------

def _keyword_score(
    m: Mechanism,
    *,
    primitive_type: str,
    coverage: str,
    q_tokens: set[str],
) -> float:
    """Higher = more relevant. Used as the fallback ranker AND as a tie-
    breaker bonus on top of TF-IDF."""
    score = 0.0
    if m.primitive_type == primitive_type:
        score += 2.0
    if coverage in m.sector_tags:
        score += 1.0
    overlap = len(q_tokens & (set(m.keywords) | set(m.tags)))
    score += overlap * 0.5
    return score


# ---------------------------------------------------------------------------
# TF-IDF backend
# ---------------------------------------------------------------------------

def _build_tfidf(mechanisms: list[Mechanism]) -> tuple[dict[str, float], list[Counter]]:
    """Per-doc term-frequency Counters + IDF lookup."""
    docs = [
        _tokens(" ".join([m.summary, " ".join(m.tags), " ".join(m.keywords)]))
        for m in mechanisms
    ]
    tfs = [Counter(d) for d in docs]
    n = len(mechanisms)
    df: Counter[str] = Counter()
    for d in docs:
        for t in set(d):
            df[t] += 1
    idf = {t: math.log((1 + n) / (1 + dfv)) + 1.0 for t, dfv in df.items()}
    return idf, tfs


def _tfidf_score(q_tokens: list[str], idf: dict[str, float], tf: Counter) -> float:
    score = 0.0
    for t in q_tokens:
        if t in tf:
            score += tf[t] * idf.get(t, 0.0)
    return score


# ---------------------------------------------------------------------------
# chromadb backend (opt-in)
# ---------------------------------------------------------------------------

def _chromadb_available() -> bool:
    if not os.environ.get("CHROMADB_URL"):
        return False
    try:
        import chromadb  # noqa: F401
        return True
    except ImportError:
        return False


def _chromadb_score(
    query_text: str,
    mechanisms: list[Mechanism],
) -> list[tuple[Mechanism, float]]:
    """Embedding-based ranking. Implementation deliberately a stub — the
    project wires the actual chromadb client at deploy time. Tests force
    this branch via `_force_backend='chromadb'` to assert the fallback
    behaviour when it raises."""
    raise NotImplementedError("chromadb backend not wired in this environment")


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
    base: Optional[Path] = None,
    _force_backend: Optional[str] = None,  # 'chromadb' | 'tfidf' | 'keyword'
) -> list[Mechanism]:
    """Top-K recall with auto-fallback. Updates recall_count + last_recalled_at."""
    mechanisms = load_all(tenant_id, base)
    if not mechanisms:
        return []

    backends_to_try: list[str]
    if _force_backend:
        backends_to_try = [_force_backend]
    else:
        backends_to_try = []
        if _chromadb_available():
            backends_to_try.append("chromadb")
        backends_to_try.extend(["tfidf", "keyword"])

    q = _tokens(query_text)
    q_set = set(q)
    selected: list[Mechanism] = []

    for backend in backends_to_try:
        try:
            if backend == "chromadb":
                scored = _chromadb_score(query_text, mechanisms)
                selected = [m for m, _ in scored[:top_k]]
            elif backend == "tfidf":
                idf, tfs = _build_tfidf(mechanisms)
                ranked = sorted(
                    zip(mechanisms, tfs),
                    key=lambda mt: (
                        _tfidf_score(q, idf, mt[1])
                        + _keyword_score(
                            mt[0],
                            primitive_type=primitive_type,
                            coverage=coverage,
                            q_tokens=q_set,
                        )
                    ),
                    reverse=True,
                )
                selected = [m for m, _ in ranked[:top_k]]
            else:  # keyword
                ranked = sorted(
                    mechanisms,
                    key=lambda m: _keyword_score(
                        m, primitive_type=primitive_type,
                        coverage=coverage, q_tokens=q_set,
                    ),
                    reverse=True,
                )
                selected = ranked[:top_k]
            # Successfully ranked — done.
            break
        except Exception:  # noqa: BLE001
            # Try the next backend.
            continue

    for m in selected:
        update_recall(tenant_id, m.id, base)
    return selected
