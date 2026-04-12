"""A-4c: PushService.

Routes AuditEvents to Web Push notifications for offline users.

Responsibilities
----------------
- Decide whether to push (user online? preference enabled? subscription live?)
- Send the Web Push message (pywebpush)
- Clean up expired subscriptions (410 Gone / 404 responses)
- Bypass per-category preferences for CRITICAL drift alerts

The pywebpush dependency is imported lazily so the module can be
imported in environments where it isn't installed (e.g. unit tests that
don't exercise the send path).
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.api.push.categories import (
    DEFAULT_PREFERENCES,
    NotificationCategory,
    category_for_action,
)

logger = logging.getLogger("dsi.api.push.service")


@dataclass
class PushPayload:
    """Payload delivered to the service worker (kept small + non-sensitive)."""

    category: NotificationCategory
    title: str
    body: str
    url: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "category": self.category.value,
                "title": self.title,
                "body": self.body,
                "url": self.url,
            }
        )


class PushService:
    """
    Database-backed push dispatcher.

    Usage:
        svc = PushService(db, connection_manager=get_connection_manager())
        svc.notify_event(action_type="RECALIBRATION_APPROVE",
                         tenant_id=..., actor_id=..., recipient_ids=[...])
    """

    def __init__(
        self,
        db: Session,
        *,
        connection_manager: Any = None,
        vapid_private_key: Optional[str] = None,
        vapid_claims: Optional[dict] = None,
    ):
        self.db = db
        self.connection_manager = connection_manager
        self.vapid_private_key = vapid_private_key or os.getenv("VAPID_PRIVATE_KEY")
        claims_email = os.getenv("VAPID_CLAIMS_EMAIL")
        self.vapid_claims = vapid_claims or (
            {"sub": f"mailto:{claims_email}"} if claims_email else None
        )

    # ------------------------------------------------------------------
    # Preference resolution
    # ------------------------------------------------------------------

    def get_preference(
        self, user_id: str, category: NotificationCategory
    ) -> dict:
        """Return {push, in_app, email} for a user+category, with defaults."""
        row = self.db.execute(
            text(
                """
                SELECT push_enabled, in_app_enabled, email_enabled
                FROM notification_preferences
                WHERE user_id = :uid AND category = :cat
                """
            ),
            {"uid": user_id, "cat": category.value},
        ).mappings().first()
        if row:
            return {
                "push": bool(row["push_enabled"]),
                "in_app": bool(row["in_app_enabled"]),
                "email": bool(row["email_enabled"]),
            }
        return dict(DEFAULT_PREFERENCES[category])

    def set_preferences(
        self,
        user_id: str,
        tenant_id: str,
        updates: dict[NotificationCategory, dict[str, bool]],
    ) -> None:
        """Upsert preferences. `updates` maps category -> partial toggles."""
        for category, flags in updates.items():
            self.db.execute(
                text(
                    """
                    INSERT INTO notification_preferences
                      (user_id, tenant_id, category,
                       push_enabled, in_app_enabled, email_enabled)
                    VALUES (:uid, :tid, :cat, :push, :in_app, :email)
                    ON CONFLICT (user_id, category) DO UPDATE
                      SET push_enabled = EXCLUDED.push_enabled,
                          in_app_enabled = EXCLUDED.in_app_enabled,
                          email_enabled = EXCLUDED.email_enabled,
                          updated_at = now()
                    """
                ),
                {
                    "uid": user_id,
                    "tid": tenant_id,
                    "cat": category.value,
                    "push": flags.get("push", True),
                    "in_app": flags.get("in_app", True),
                    "email": flags.get("email", False),
                },
            )

    def list_preferences(self, user_id: str) -> dict[str, dict]:
        """Return all effective preferences keyed by category string."""
        result: dict[str, dict] = {}
        for cat in NotificationCategory:
            result[cat.value] = self.get_preference(user_id, cat)
        return result

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------

    def register_subscription(
        self,
        *,
        user_id: str,
        tenant_id: str,
        endpoint: str,
        p256dh_key: str,
        auth_key: str,
        user_agent: Optional[str] = None,
    ) -> None:
        """Upsert a push subscription (user_id + endpoint unique)."""
        self.db.execute(
            text(
                """
                INSERT INTO push_subscriptions
                  (user_id, tenant_id, endpoint, p256dh_key, auth_key, user_agent, last_used_at)
                VALUES (:uid, :tid, :endpoint, :p256dh, :auth, :ua, :now)
                ON CONFLICT (user_id, endpoint) DO UPDATE
                  SET p256dh_key = EXCLUDED.p256dh_key,
                      auth_key = EXCLUDED.auth_key,
                      user_agent = EXCLUDED.user_agent,
                      last_used_at = EXCLUDED.last_used_at
                """
            ),
            {
                "uid": user_id,
                "tid": tenant_id,
                "endpoint": endpoint,
                "p256dh": p256dh_key,
                "auth": auth_key,
                "ua": user_agent,
                "now": datetime.now(timezone.utc),
            },
        )

    def remove_subscription(self, *, user_id: str, endpoint: str) -> bool:
        result = self.db.execute(
            text(
                """
                DELETE FROM push_subscriptions
                WHERE user_id = :uid AND endpoint = :endpoint
                """
            ),
            {"uid": user_id, "endpoint": endpoint},
        )
        return bool(result.rowcount)

    def _list_subscriptions(self, user_id: str) -> list[dict]:
        rows = self.db.execute(
            text(
                """
                SELECT id::text, endpoint, p256dh_key, auth_key
                FROM push_subscriptions
                WHERE user_id = :uid
                """
            ),
            {"uid": user_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def _delete_subscription(self, subscription_id: str) -> None:
        self.db.execute(
            text("DELETE FROM push_subscriptions WHERE id = :id"),
            {"id": subscription_id},
        )

    # ------------------------------------------------------------------
    # Decision + delivery
    # ------------------------------------------------------------------

    def _user_is_online(self, tenant_id: str, user_id: str) -> bool:
        """True if the user has at least one live WebSocket connection."""
        if self.connection_manager is None:
            return False
        try:
            users = self.connection_manager.get_active_users(tenant_id)
        except Exception:  # pragma: no cover - defensive
            return False
        return any(u.get("user_id") == user_id for u in users)

    def should_push(
        self,
        *,
        tenant_id: str,
        user_id: str,
        category: NotificationCategory,
        force: bool = False,
    ) -> bool:
        """Decide if a push should be delivered.

        Rules:
        1. If the user is online (WS connected), skip -- they'll see it in-app.
        2. Unless `force=True` (CRITICAL alerts), respect the per-category
           preference.
        3. The subscription check is handled by send() -- if no subs, a no-op.
        """
        if self._user_is_online(tenant_id, user_id):
            return False
        if force:
            return True
        pref = self.get_preference(user_id, category)
        return bool(pref.get("push", True))

    def send(
        self,
        *,
        user_id: str,
        payload: PushPayload,
    ) -> int:
        """Send to all subscriptions for user_id. Returns delivered count.

        Expired subscriptions (410/404 from the push provider) are
        automatically cleaned up.
        """
        subs = self._list_subscriptions(user_id)
        if not subs:
            return 0

        try:
            from pywebpush import WebPushException, webpush  # type: ignore
        except Exception:
            logger.warning(
                "pywebpush not installed; skipping push for user=%s", user_id
            )
            return 0

        if not self.vapid_private_key or not self.vapid_claims:
            logger.warning(
                "VAPID keys not configured; skipping push for user=%s", user_id
            )
            return 0

        delivered = 0
        data = payload.to_json()
        for sub in subs:
            subscription_info = {
                "endpoint": sub["endpoint"],
                "keys": {"p256dh": sub["p256dh_key"], "auth": sub["auth_key"]},
            }
            try:
                webpush(
                    subscription_info=subscription_info,
                    data=data,
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims=dict(self.vapid_claims),
                )
                delivered += 1
            except WebPushException as exc:  # type: ignore
                status_code = getattr(
                    getattr(exc, "response", None), "status_code", None
                )
                if status_code in (404, 410):
                    logger.info(
                        "Push subscription expired (%s); removing id=%s",
                        status_code,
                        sub["id"],
                    )
                    self._delete_subscription(sub["id"])
                else:
                    logger.warning("Push delivery failed: %s", exc)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Unexpected push delivery error: %s", exc)
        return delivered

    # ------------------------------------------------------------------
    # High-level entry point
    # ------------------------------------------------------------------

    def notify_event(
        self,
        *,
        action_type: str,
        tenant_id: str,
        actor_id: Optional[str],
        recipient_ids: list[str],
        title: str,
        body: str,
        url: Optional[str] = None,
        force: bool = False,
    ) -> int:
        """Map an audit event -> category -> per-recipient push decision.

        Returns the number of push messages actually dispatched.
        Callers (AuditMiddleware) pre-compute recipient_ids -- this
        service does not load users or subscriptions for every event.
        """
        category = category_for_action(action_type)
        if category is None:
            return 0

        payload = PushPayload(category=category, title=title, body=body, url=url)
        sent = 0
        for rid in recipient_ids:
            if actor_id and rid == actor_id:
                continue  # don't notify the initiator
            if not self.should_push(
                tenant_id=tenant_id, user_id=rid, category=category, force=force
            ):
                continue
            sent += self.send(user_id=rid, payload=payload)
        return sent
