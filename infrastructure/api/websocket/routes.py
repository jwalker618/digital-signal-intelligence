"""
A-2d: WebSocket endpoint.

Mounted at /ws. Authenticates via token query parameter (browsers can't
set Authorization headers on WebSocket connections). Joins the client to
its tenant's broadcast channel.

Client protocol:
- Connect: ws://host/ws?token=<access_token>
- Server sends JSON messages: {event_type, action_type, resource_type,
  resource_id, user_id, timestamp, summary, audit_id}
- Client can send heartbeat pings (text "ping"); server responds "pong"
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from infrastructure.api.auth.jwt_auth import decode_token
from infrastructure.api.websocket.manager import get_connection_manager

logger = logging.getLogger("dsi.api.websocket.routes")
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """Authenticated WebSocket endpoint for real-time audit events."""
    # Authenticate via token query param (WebSocket can't carry Authorization header)
    payload = decode_token(token, expected_type="access")
    if payload is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    manager = get_connection_manager()
    conn = await manager.connect(
        websocket=websocket,
        tenant_id=payload.tenant_id,
        user_id=payload.sub,
    )

    try:
        # Send initial hello
        await websocket.send_json(
            {
                "event_type": "hello",
                "user_id": payload.sub,
                "tenant_id": payload.tenant_id,
                "role": payload.role,
            }
        )

        # Listen for client messages (heartbeats, subscription updates)
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_text("pong")
            # Additional client-side commands (e.g. subscribe to a specific
            # resource) can be handled here when the frontend needs them.

    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected: user=%s", payload.sub)
    except Exception as exc:  # noqa: BLE001
        logger.warning("WebSocket error for user=%s: %s", payload.sub, exc)
    finally:
        await manager.disconnect(conn)
