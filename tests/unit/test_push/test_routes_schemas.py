"""A-4d: Push route request schemas (pure validation, no DB)."""

import pytest
from pydantic import ValidationError

from infrastructure.api.push.routes import (
    CategoryToggle,
    PreferencesUpdateRequest,
    SubscribeRequest,
    SendTestPushRequest,
    UnsubscribeRequest,
)


class TestSubscribeRequest:
    def test_valid_minimal(self):
        s = SubscribeRequest(
            endpoint="https://push.example/abc",
            p256dh_key="AAAAA",
            auth_key="BBBBB",
        )
        assert s.user_agent is None

    def test_empty_endpoint_rejected(self):
        with pytest.raises(ValidationError):
            SubscribeRequest(endpoint="", p256dh_key="x", auth_key="y")


class TestUnsubscribeRequest:
    def test_requires_endpoint(self):
        with pytest.raises(ValidationError):
            UnsubscribeRequest(endpoint="")


class TestPreferencesUpdate:
    def test_partial_toggle(self):
        req = PreferencesUpdateRequest(
            updates={"drift_alert": CategoryToggle(push=False)}
        )
        assert req.updates["drift_alert"].push is False
        assert req.updates["drift_alert"].in_app is None

    def test_empty_updates_allowed(self):
        req = PreferencesUpdateRequest(updates={})
        assert req.updates == {}


class TestSendTestPushSchema:
    def test_optional_fields(self):
        t = SendTestPushRequest()
        assert t.title is None
        assert t.body is None
