"""A-2d: ConnectionManager tests (no live WebSocket required)."""

import asyncio
from dataclasses import dataclass

import pytest

from infrastructure.api.websocket.manager import ConnectionManager


class _FakeWebSocket:
    """Minimal stand-in for the WebSocket type used by ConnectionManager."""

    def __init__(self):
        self.messages: list[str] = []
        self.accepted = False
        self.should_fail = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, message: str):
        if self.should_fail:
            raise ConnectionError("fake disconnect")
        self.messages.append(message)


@pytest.mark.asyncio
async def test_connect_tracks_connection():
    mgr = ConnectionManager()
    ws = _FakeWebSocket()
    conn = await mgr.connect(ws, tenant_id="t1", user_id="u1")
    assert ws.accepted
    assert mgr.stats()["total_connections"] == 1
    assert mgr.stats()["tenants_with_connections"] == 1
    assert conn.user_id == "u1"


@pytest.mark.asyncio
async def test_disconnect_removes_connection():
    mgr = ConnectionManager()
    ws = _FakeWebSocket()
    conn = await mgr.connect(ws, tenant_id="t1", user_id="u1")
    await mgr.disconnect(conn)
    assert mgr.stats()["total_connections"] == 0


@pytest.mark.asyncio
async def test_broadcast_to_tenant_reaches_all():
    mgr = ConnectionManager()
    ws1 = _FakeWebSocket()
    ws2 = _FakeWebSocket()
    await mgr.connect(ws1, tenant_id="t1", user_id="u1")
    await mgr.connect(ws2, tenant_id="t1", user_id="u2")

    sent = await mgr.broadcast_to_tenant("t1", {"event_type": "audit", "hello": "world"})
    assert sent == 2
    assert len(ws1.messages) == 1
    assert len(ws2.messages) == 1
    assert "hello" in ws1.messages[0]


@pytest.mark.asyncio
async def test_broadcast_tenant_isolation():
    mgr = ConnectionManager()
    ws_a = _FakeWebSocket()
    ws_b = _FakeWebSocket()
    await mgr.connect(ws_a, tenant_id="tenant_a", user_id="u1")
    await mgr.connect(ws_b, tenant_id="tenant_b", user_id="u2")

    await mgr.broadcast_to_tenant("tenant_a", {"for": "a"})
    assert len(ws_a.messages) == 1
    assert len(ws_b.messages) == 0  # other tenant not reached


@pytest.mark.asyncio
async def test_broadcast_removes_dead_connections():
    mgr = ConnectionManager()
    ws_good = _FakeWebSocket()
    ws_bad = _FakeWebSocket()
    ws_bad.should_fail = True
    await mgr.connect(ws_good, tenant_id="t1", user_id="u1")
    await mgr.connect(ws_bad, tenant_id="t1", user_id="u2")

    sent = await mgr.broadcast_to_tenant("t1", {"m": 1})
    assert sent == 1  # only one succeeded
    assert mgr.stats()["total_connections"] == 1  # dead one removed


def test_sync_broadcast_without_loop_is_safe():
    """When no WS connections exist, sync broadcast is a no-op."""
    mgr = ConnectionManager()
    mgr.broadcast_to_tenant_sync("t1", {"m": "dropped"})
    # No assertion -- the important thing is it doesn't raise


@pytest.mark.asyncio
async def test_active_users_returns_list():
    mgr = ConnectionManager()
    ws1 = _FakeWebSocket()
    ws2 = _FakeWebSocket()
    await mgr.connect(ws1, tenant_id="t1", user_id="alice")
    await mgr.connect(ws2, tenant_id="t1", user_id="bob")

    users = mgr.get_active_users("t1")
    user_ids = {u["user_id"] for u in users}
    assert user_ids == {"alice", "bob"}
