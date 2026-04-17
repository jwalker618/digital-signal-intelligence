"""V6/E2 — provenance chain-of-custody tests."""
from __future__ import annotations

from datetime import datetime, timezone

from signal_architecture.signals.provenance import (
    build_provenance,
    compute_response_hash,
    verify_chain,
)


def test_response_hash_stable_across_dict_order():
    h1 = compute_response_hash({"a": 1, "b": 2, "c": 3})
    h2 = compute_response_hash({"c": 3, "b": 2, "a": 1})
    assert h1 == h2


def test_response_hash_sensitive_to_change():
    h1 = compute_response_hash({"k": 1})
    h2 = compute_response_hash({"k": 2})
    assert h1 != h2


def test_build_provenance_populates_hash_and_timestamp():
    ts = datetime(2026, 4, 17, tzinfo=timezone.utc)
    p = build_provenance(
        source_name="web.wayback",
        source_url="https://example.com",
        response_body={"first_seen": "1999-10-10"},
        extractor_version="1.0",
        request_timestamp=ts,
    )
    assert p.response_hash == compute_response_hash({"first_seen": "1999-10-10"})
    assert p.request_timestamp == ts
    assert p.cache_hit is False
    assert p.parent_hashes == []


def test_self_hash_changes_when_parent_changes():
    p_root = build_provenance(
        source_name="a", source_url="/a", response_body={"x": 1},
    )
    p_child_v1 = build_provenance(
        source_name="b", source_url="/b", response_body={"y": 2},
        parent_hashes=[p_root.self_hash()],
    )
    p_child_v2 = build_provenance(
        source_name="b", source_url="/b", response_body={"y": 2},
        parent_hashes=["some-other-parent-hash"],
    )
    assert p_child_v1.self_hash() != p_child_v2.self_hash()


def test_chain_of_trust_returns_parent_then_self():
    p_root = build_provenance(source_name="a", source_url="/a", response_body={})
    p_child = build_provenance(
        source_name="b", source_url="/b", response_body={},
        parent_hashes=[p_root.self_hash()],
    )
    chain = p_child.chain_of_trust()
    assert chain[0] == p_root.self_hash()
    assert chain[-1] == p_child.self_hash()


def test_verify_chain_valid():
    p1 = build_provenance(source_name="a", source_url="/a", response_body={})
    p2 = build_provenance(
        source_name="b", source_url="/b", response_body={},
        parent_hashes=[p1.self_hash()],
    )
    p3 = build_provenance(
        source_name="c", source_url="/c", response_body={},
        parent_hashes=[p2.self_hash()],
    )
    assert verify_chain([p1, p2, p3]) is True


def test_verify_chain_detects_tampering():
    p1 = build_provenance(source_name="a", source_url="/a", response_body={})
    p2 = build_provenance(
        source_name="b", source_url="/b", response_body={},
        parent_hashes=["evil-hash-not-linked-to-p1"],
    )
    assert verify_chain([p1, p2]) is False


def test_to_dict_includes_self_hash():
    p = build_provenance(source_name="a", source_url="/a", response_body={"x": 1})
    d = p.to_dict()
    assert d["self_hash"] == p.self_hash()
    assert isinstance(d["request_timestamp"], str)
