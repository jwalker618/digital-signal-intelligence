"""A-4c: PushService decision helpers (with a mocked DB + connection manager)."""

from unittest.mock import MagicMock

import pytest

from infrastructure.api.push.categories import NotificationCategory
from infrastructure.api.push.service import PushPayload, PushService


class _FakeDB:
    """Minimal SQLAlchemy Session stub -- just records calls to execute()."""

    def __init__(self, rows=None, rowcount=0):
        self._rows = rows or []
        self._rowcount = rowcount
        self.calls = []

    def execute(self, statement, params=None):
        self.calls.append((str(statement), params or {}))
        result = MagicMock()
        mapping_iter = MagicMock()
        mapping_iter.first.return_value = self._rows[0] if self._rows else None
        mapping_iter.all.return_value = self._rows
        result.mappings.return_value = mapping_iter
        result.rowcount = self._rowcount
        return result


class TestPayload:
    def test_to_json_round_trip(self):
        payload = PushPayload(
            category=NotificationCategory.DRIFT_ALERT,
            title="Drift detected",
            body="IV stat drop > 30%",
            url="/world-engine",
        )
        import json

        parsed = json.loads(payload.to_json())
        assert parsed["category"] == "drift_alert"
        assert parsed["title"] == "Drift detected"
        assert parsed["url"] == "/world-engine"


class TestShouldPush:
    def _svc(self, *, rows=None, connected_users=()):
        db = _FakeDB(rows=rows or [])
        manager = MagicMock()
        manager.get_active_users.return_value = [
            {"user_id": u} for u in connected_users
        ]
        return PushService(db, connection_manager=manager), db, manager

    def test_online_user_skipped(self):
        svc, _, _ = self._svc(connected_users=["u1"])
        assert not svc.should_push(
            tenant_id="t", user_id="u1", category=NotificationCategory.DRIFT_ALERT
        )

    def test_offline_default_enabled(self):
        svc, _, _ = self._svc(rows=[], connected_users=[])
        assert svc.should_push(
            tenant_id="t", user_id="u1", category=NotificationCategory.DRIFT_ALERT
        )

    def test_offline_disabled_preference(self):
        # get_preference returns row with push_enabled=False
        svc, _, _ = self._svc(
            rows=[{"push_enabled": False, "in_app_enabled": True, "email_enabled": False}],
            connected_users=[],
        )
        assert not svc.should_push(
            tenant_id="t",
            user_id="u1",
            category=NotificationCategory.DRIFT_ALERT,
        )

    def test_force_bypasses_preference(self):
        svc, _, _ = self._svc(
            rows=[{"push_enabled": False, "in_app_enabled": True, "email_enabled": False}],
            connected_users=[],
        )
        assert svc.should_push(
            tenant_id="t",
            user_id="u1",
            category=NotificationCategory.DRIFT_ALERT,
            force=True,
        )

    def test_force_still_skips_online_user(self):
        # Critical alerts shouldn't push to already-connected users
        svc, _, _ = self._svc(connected_users=["u1"])
        assert not svc.should_push(
            tenant_id="t",
            user_id="u1",
            category=NotificationCategory.DRIFT_ALERT,
            force=True,
        )


class TestSendWithoutPywebpush:
    """Without VAPID keys / pywebpush, send() returns 0 without raising."""

    def test_no_subscriptions_returns_zero(self):
        db = _FakeDB(rows=[])
        svc = PushService(db, connection_manager=None)
        payload = PushPayload(
            category=NotificationCategory.DRIFT_ALERT,
            title="x",
            body="y",
        )
        assert svc.send(user_id="u1", payload=payload) == 0

    def test_vapid_missing_returns_zero_with_subs(self, monkeypatch):
        db = _FakeDB(
            rows=[
                {
                    "id": "sub-1",
                    "endpoint": "https://push.example/abc",
                    "p256dh_key": "AAA",
                    "auth_key": "BBB",
                }
            ]
        )
        # No VAPID env set
        monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
        monkeypatch.delenv("VAPID_CLAIMS_EMAIL", raising=False)
        svc = PushService(db)
        payload = PushPayload(
            category=NotificationCategory.DRIFT_ALERT, title="x", body="y"
        )
        assert svc.send(user_id="u1", payload=payload) == 0


class TestNotifyEventFilters:
    def test_unknown_action_returns_zero(self):
        svc = PushService(_FakeDB(), connection_manager=None)
        sent = svc.notify_event(
            action_type="LOGIN",
            tenant_id="t",
            actor_id="u1",
            recipient_ids=["u1", "u2"],
            title="x",
            body="y",
        )
        assert sent == 0

    def test_actor_is_excluded(self):
        # Actor should never receive their own push. Everyone else offline
        # with no subscriptions -> send returns 0, but we verify the actor
        # was filtered by inspecting calls.
        db = _FakeDB(rows=[])  # no subscriptions for anyone
        manager = MagicMock()
        manager.get_active_users.return_value = []
        svc = PushService(db, connection_manager=manager)
        sent = svc.notify_event(
            action_type="RECALIBRATION_APPROVE",
            tenant_id="t",
            actor_id="u1",
            recipient_ids=["u1", "u2", "u3"],
            title="x",
            body="y",
        )
        assert sent == 0
        # Ensure get_active_users was checked for u2 + u3 (2 calls), not u1.
        assert manager.get_active_users.call_count == 2
