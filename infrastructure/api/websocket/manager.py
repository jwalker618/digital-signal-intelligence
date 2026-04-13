"""
A-2d: WebSocket Connection Manager

Tenant-scoped broadcast to all connected clients. Connections are tracked
in an in-memory dict keyed by tenant_id. Each connection carries the
user_id for filtering and the connection timestamp.

Broadcasts happen via both sync and async paths:
- sync path (broadcast_to_tenant_sync): used by AuditService inside a
  synchronous DB callback. Messages are enqueued; the event loop drains
  the queue on the next tick.
- async path (broadcast_to_tenant): used when the caller is already in
  an async context.

In production, replace the in-memory store with Redis pub/sub to scale
across multiple API replicas. The interface here is stable so that
replacement is a single-class swap.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("dsi.api.websocket")


@dataclass(eq=False)  # Identity-based equality/hashing (we never compare by fields)
class _Connection:
    websocket: WebSocket
    user_id: str
    tenant_id: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectionManager:
    """In-memory registry of active WebSocket connections keyed by tenant.

    Design notes:
    - The manager tracks connections per tenant for broadcasting.
    - The sync -> async bridge (broadcast_to_tenant_sync) uses
      `asyncio.run_coroutine_threadsafe` with the event loop captured at
      connect time. This avoids pinning a queue to a specific loop, which
      would break across test clients.
    """

    def __init__(self) -> None:
        self._connections: dict[str, set[_Connection]] = defaultdict(set)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self, websocket: WebSocket, tenant_id: str, user_id: str) -> _Connection:
        await websocket.accept()
        conn = _Connection(websocket=websocket, user_id=user_id, tenant_id=tenant_id)
        self._connections[tenant_id].add(conn)
        # Capture the running loop for sync -> async bridging.
        self._loop = asyncio.get_running_loop()
        logger.debug("WS connect: tenant=%s user=%s (%d total for tenant)",
                     tenant_id, user_id, len(self._connections[tenant_id]))
        return conn

    async def disconnect(self, conn: _Connection) -> None:
        self._connections[conn.tenant_id].discard(conn)
        if not self._connections[conn.tenant_id]:
            del self._connections[conn.tenant_id]
        # If no more connections anywhere, drop the loop reference so a
        # fresh one is captured on the next connect.
        if not any(self._connections.values()):
            self._loop = None
        logger.debug("WS disconnect: tenant=%s user=%s", conn.tenant_id, conn.user_id)

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------

    async def broadcast_to_tenant(self, tenant_id: str, message: dict) -> int:
        """Send a message to all connected clients in a tenant."""
        conns = list(self._connections.get(tenant_id, set()))
        if not conns:
            return 0

        message_json = json.dumps(message, default=str)
        sent = 0
        dead: list[_Connection] = []
        for conn in conns:
            try:
                await conn.websocket.send_text(message_json)
                sent += 1
            except Exception as exc:  # noqa: BLE001
                logger.debug("WS send failed for %s: %s", conn.user_id, exc)
                dead.append(conn)

        for conn in dead:
            await self.disconnect(conn)

        return sent

    def broadcast_to_tenant_sync(self, tenant_id: str, message: dict) -> None:
        """Broadcast from synchronous code.

        Dispatches the coroutine onto the captured event loop via
        run_coroutine_threadsafe. If no loop is available (no active
        connections), the broadcast is silently dropped -- there is
        nobody to receive it anyway.
        """
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self.broadcast_to_tenant(tenant_id, message), loop
            )
        except RuntimeError as exc:
            logger.debug("WS broadcast_sync dropped: %s", exc)

    # ------------------------------------------------------------------
    # Introspection (used by /admin/health endpoints later)
    # ------------------------------------------------------------------

    def get_active_users(self, tenant_id: str) -> list[dict]:
        conns = self._connections.get(tenant_id, set())
        return [
            {"user_id": c.user_id, "connected_at": c.connected_at.isoformat()}
            for c in conns
        ]

    def stats(self) -> dict:
        """Return summary stats for monitoring."""
        total = sum(len(s) for s in self._connections.values())
        return {
            "total_connections": total,
            "tenants_with_connections": len(self._connections),
            "loop_attached": self._loop is not None and not self._loop.is_closed(),
        }


# Module-level singleton -- one manager per API process.
_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
