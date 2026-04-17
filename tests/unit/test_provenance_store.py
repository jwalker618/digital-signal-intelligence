"""V6/E2 — provenance-store persistence helpers unit tests.

Uses a tiny SQLAlchemy-Session-shaped stub to avoid spinning up a
Postgres. Guarantees the INSERT shape + hash round-trip contract.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

from infrastructure.db.provenance_store import (
    persist_chain,
    persist_extractor_result,
    persist_provenance,
)
from signal_architecture.signals.provenance import build_provenance


@dataclass
class _RecordedExecute:
    stmt: str
    params: Dict[str, Any]


class _StubDB:
    def __init__(self) -> None:
        self.calls: List[_RecordedExecute] = []

    def execute(self, stmt, params=None) -> None:
        self.calls.append(_RecordedExecute(str(stmt), params or {}))


def test_persist_provenance_returns_self_hash_and_issues_single_insert():
    db = _StubDB()
    prov = build_provenance(
        source_name="web.wayback",
        source_url="https://example.com",
        response_body={"x": 1},
        extractor_version="1.0",
    )
    mvid = uuid.uuid4()
    returned = persist_provenance(
        db,
        signal_id="first_seen",
        model_version_id=mvid,
        assessment_id=None,
        provenance=prov,
    )
    assert returned == prov.self_hash()
    assert len(db.calls) == 1
    call = db.calls[0]
    assert "INSERT INTO signal_provenance" in call.stmt
    assert call.params["shash"] == prov.self_hash()
    assert call.params["source"] == "web.wayback"


def test_persist_chain_writes_every_edge():
    db = _StubDB()
    aid = uuid.uuid4()
    written = persist_chain(
        db,
        assessment_id=aid,
        edges=[("h1", "h2"), ("h2", "h3"), ("h1", "h3")],
    )
    assert written == 3
    for call in db.calls:
        assert "INSERT INTO provenance_chain" in call.stmt
        assert call.params["aid"] == aid


def test_persist_extractor_result_skips_when_no_provenance_attached():
    db = _StubDB()

    class _R:
        metadata = None

    out = persist_extractor_result(
        db, signal_id="x", model_version_id=uuid.uuid4(),
        assessment_id=None, extractor_result=_R(),
    )
    assert out is None
    assert db.calls == []


def test_persist_extractor_result_persists_when_provenance_present():
    prov = build_provenance(
        source_name="web.tranco",
        source_url="https://tranco-list.eu",
        response_body={"rank": 42},
    )

    class _R:
        metadata = {"provenance": prov.to_dict()}

    db = _StubDB()
    out = persist_extractor_result(
        db,
        signal_id="tranco_rank",
        model_version_id=uuid.uuid4(),
        assessment_id=uuid.uuid4(),
        extractor_result=_R(),
    )
    assert out is not None
    assert len(db.calls) == 1
    assert db.calls[0].params["source"] == "web.tranco"
    # The original response_hash is preserved so the chain stays stable
    assert db.calls[0].params["rhash"] == prov.response_hash
