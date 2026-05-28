"""V6/E2 — /api/v1/quotes/{id}/provenance handler tests.

Exercises the route by hand-constructing AsyncSession-shaped stubs,
mirroring the existing quotes route unit test approach.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import pytest

from fastapi import HTTPException


class _StubScalarResult:
    def __init__(self, value):
        self._v = value

    def scalar_one_or_none(self):
        return self._v


class _StubFetchResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


@dataclass
class _FakeQuote:
    quote_code: str
    id: Any
    model_version_id: Any = None
    assessment_id: Any = None


class _StubAsyncDB:
    """Async-session-shaped stub that responds to the three queries the
    handler issues."""
    def __init__(self, quote, nodes, edges):
        self._quote = quote
        self._nodes = nodes
        self._edges = edges
        self._calls = 0

    async def execute(self, stmt, params=None):
        self._calls += 1
        if self._calls == 1:
            return _StubScalarResult(self._quote)
        if self._calls == 2:
            return _StubFetchResult(self._nodes)
        return _StubFetchResult(self._edges)


def _call(handler, *args, **kwargs):
    # Use asyncio.run() rather than asyncio.get_event_loop() -- the
    # latter returns a stale (sometimes closed) loop after other tests
    # in the same suite have created and torn down their own loops,
    # which made these tests flaky depending on suite ordering.
    return asyncio.run(handler(*args, **kwargs))


def test_returns_404_when_quote_missing():
    from infrastructure.api.routes.quotes import get_quote_provenance

    db = _StubAsyncDB(quote=None, nodes=[], edges=[])
    with pytest.raises(HTTPException) as exc:
        _call(get_quote_provenance, "q_missing", db=db)
    assert exc.value.status_code == 404


def test_returns_empty_chain_when_provenance_not_yet_captured():
    from infrastructure.api.routes.quotes import get_quote_provenance

    quote = _FakeQuote(quote_code="q_abc", id="quote-uuid-1", model_version_id="mv-1")
    db = _StubAsyncDB(quote=quote, nodes=[], edges=[])

    result = _call(get_quote_provenance, "q_abc", db=db)
    assert result["quote_code"] == "q_abc"
    assert result["nodes"] == []
    assert result["edges"] == []
    assert result["assessment_id"] == "quote-uuid-1"


def test_returns_nodes_and_edges_when_present():
    from infrastructure.api.routes.quotes import get_quote_provenance

    quote = _FakeQuote(quote_code="q_abc", id="quote-uuid-1")
    ts = datetime(2026, 4, 17, 12, 0, tzinfo=timezone.utc)
    nodes = [
        ("sig_a", "web.wayback", "resp-hash-a", "self-hash-a",
         "1.0", False, ts, {"source_url": "https://archive.org/"}),
        ("sig_b", "web.urlscan", "resp-hash-b", "self-hash-b",
         "1.0", True, ts, {"source_url": "https://urlscan.io/"}),
    ]
    edges = [("self-hash-a", "self-hash-b")]
    db = _StubAsyncDB(quote=quote, nodes=nodes, edges=edges)

    result = _call(get_quote_provenance, "q_abc", db=db)
    assert len(result["nodes"]) == 2
    first = result["nodes"][0]
    assert first["signal_id"] == "sig_a"
    assert first["self_hash"] == "self-hash-a"
    assert first["cache_hit"] is False
    assert first["request_timestamp"] == "2026-04-17T12:00:00+00:00"
    assert result["edges"] == [
        {"parent_hash": "self-hash-a", "child_hash": "self-hash-b"}
    ]
