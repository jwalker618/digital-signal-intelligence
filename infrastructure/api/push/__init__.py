"""A-4: Push notification infrastructure.

- categories: NotificationCategory enum + defaults
- service: PushService (Web Push via pywebpush)
- routes: /api/v1/push/* endpoints

Mounted from infrastructure/api/main.py.
"""

from infrastructure.api.push.categories import (
    DEFAULT_PREFERENCES,
    NotificationCategory,
    category_for_action,
)
from infrastructure.api.push.service import PushPayload, PushService
from infrastructure.api.push.routes import router

__all__ = [
    "NotificationCategory",
    "DEFAULT_PREFERENCES",
    "category_for_action",
    "PushService",
    "PushPayload",
    "router",
]
