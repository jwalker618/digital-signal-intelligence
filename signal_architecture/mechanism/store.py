"""V7 Phase 12 — append-only JSONL mechanism store + archival.

Path convention: ``<base>/<tenant_id>/mechanisms.jsonl`` where `base`
defaults to ``~/.dsi``. Tests pass an explicit tmp `base` to avoid
touching real home dirs.

Operations:
    load_all(tenant_id)               — read every mechanism (sorted-by-file order)
    append(tenant_id, m)              — insert unless canonical_signature already present
    update_recall(tenant_id, m_id)    — stamp last_recalled_at + increment recall_count
    prune_old(tenant_id, ...)         — move low-recall stale rows to mechanisms_archive.jsonl
    existing_signatures(tenant_id)    — set of canonical_signatures already stored

V8 may swap to SQLite; the current JSONL works because:
  - per-tenant volume is expected in the low thousands
  - append is the dominant op
  - update_recall is rare relative to append/recall
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from .types import Mechanism

DEFAULT_BASE = Path.home() / ".dsi"


def _store_path(tenant_id: str, base: Optional[Path] = None) -> Path:
    p = (base or DEFAULT_BASE) / tenant_id / "mechanisms.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _archive_path(tenant_id: str, base: Optional[Path] = None) -> Path:
    p = (base or DEFAULT_BASE) / tenant_id / "mechanisms_archive.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_all(tenant_id: str, base: Optional[Path] = None) -> list[Mechanism]:
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
            # Skip a corrupt row rather than poisoning the whole file.
            continue
    return out


def existing_signatures(tenant_id: str, base: Optional[Path] = None) -> set[str]:
    return {m.canonical_signature for m in load_all(tenant_id, base)}


def append(
    tenant_id: str,
    mechanism: Mechanism,
    base: Optional[Path] = None,
) -> bool:
    """Append unless `canonical_signature` already exists. Returns True on insert."""
    if mechanism.canonical_signature in existing_signatures(tenant_id, base):
        return False
    p = _store_path(tenant_id, base)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(mechanism.to_dict(), sort_keys=True) + "\n")
    return True


def update_recall(
    tenant_id: str,
    mechanism_id: str,
    base: Optional[Path] = None,
    *,
    now: Optional[float] = None,
) -> bool:
    """Stamp last_recalled_at + increment recall_count for one mechanism.

    Rewrites the file (acceptable at expected tenant volumes). Returns True
    when the row was found + updated; False otherwise.
    """
    p = _store_path(tenant_id, base)
    if not p.exists():
        return False
    rows = load_all(tenant_id, base)
    stamp = now if now is not None else time.time()
    changed = False
    for m in rows:
        if m.id == mechanism_id:
            m.last_recalled_at = stamp
            m.recall_count += 1
            changed = True
            break
    if not changed:
        return False
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for m in rows:
            f.write(json.dumps(m.to_dict(), sort_keys=True) + "\n")
    tmp.replace(p)
    return True


def prune_old(
    tenant_id: str,
    *,
    base: Optional[Path] = None,
    older_than_days: int = 365,
    min_recall_count: int = 3,
    now: Optional[float] = None,
) -> int:
    """Move stale low-recall rows to the archive file.

    A mechanism is archived only if BOTH:
      - recall_count < min_recall_count
      - last_recalled_at older than `older_than_days` (or never recalled)

    Returns the number archived.
    """
    rows = load_all(tenant_id, base)
    stamp = now if now is not None else time.time()
    cutoff = stamp - older_than_days * 86400
    keep: list[Mechanism] = []
    archive: list[Mechanism] = []
    for m in rows:
        # Never-recalled rows treated as "stale" only if they're older than
        # the cutoff via first_seen.
        last = m.last_recalled_at or m.first_seen
        if m.recall_count < min_recall_count and last < cutoff:
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
