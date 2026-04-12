"""A-2d: WebSocket infrastructure for real-time sync.

Provides ConnectionManager (tenant-scoped broadcasting) and the WebSocket
endpoint mounted at /ws. Subscribers receive audit events from the audit
service in real-time.
"""

from infrastructure.api.websocket.manager import ConnectionManager, get_connection_manager

__all__ = ["ConnectionManager", "get_connection_manager"]
