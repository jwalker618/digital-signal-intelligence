"""A-1d: JWT auth primitives (pure-functional tests, no DB required)."""

from datetime import datetime, timedelta, timezone

import pytest

from infrastructure.api.auth.jwt_auth import (
    DEFAULT_ACCESS_TOKEN_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        h = hash_password("MyS3curePW!")
        assert h != "MyS3curePW!"
        assert verify_password("MyS3curePW!", h)

    def test_wrong_password(self):
        h = hash_password("correct")
        assert not verify_password("wrong", h)

    def test_different_hashes_for_same_password(self):
        """Salts ensure each hash is unique."""
        assert hash_password("same") != hash_password("same")

    def test_empty_hash_rejected(self):
        assert not verify_password("anything", "")

    def test_long_password_truncated_not_raises(self):
        """bcrypt has 72-byte limit; our wrapper truncates gracefully."""
        long_pw = "a" * 200
        h = hash_password(long_pw)
        assert verify_password(long_pw, h)


class TestAccessToken:
    def test_create_and_decode(self):
        token = create_access_token(
            user_id="u1",
            tenant_id="t1",
            role="ADMIN",
            permissions=["admin:system"],
            email="u@example.com",
        )
        payload = decode_token(token, expected_type="access")
        assert payload is not None
        assert payload.sub == "u1"
        assert payload.tenant_id == "t1"
        assert payload.role == "ADMIN"
        assert "admin:system" in payload.permissions
        assert payload.type == "access"
        assert payload.email == "u@example.com"

    def test_invalid_token_returns_none(self):
        assert decode_token("not-a-jwt") is None
        assert decode_token("a.b.c") is None

    def test_wrong_type_rejected(self):
        token = create_access_token("u1", "t1")
        assert decode_token(token, expected_type="refresh") is None

    def test_unique_jti(self):
        t1 = create_access_token("u1", "t1")
        t2 = create_access_token("u1", "t1")
        assert t1 != t2

    def test_expiry_set(self):
        token = create_access_token("u1", "t1", expires_minutes=30)
        payload = decode_token(token)
        assert payload is not None
        # Expiry should be ~30 min in the future
        exp_dt = datetime.fromtimestamp(payload.exp, tz=timezone.utc)
        expected = datetime.now(timezone.utc) + timedelta(minutes=30)
        assert abs((exp_dt - expected).total_seconds()) < 5


class TestRefreshToken:
    def test_create_returns_token_and_hash(self):
        token, token_hash = create_refresh_token("u1", "t1")
        assert token
        assert token_hash
        assert hash_token(token) == token_hash

    def test_hash_deterministic(self):
        t, h1 = create_refresh_token("u1", "t1")
        h2 = hash_token(t)
        assert h1 == h2

    def test_refresh_type(self):
        token, _ = create_refresh_token("u1", "t1")
        payload = decode_token(token, expected_type="refresh")
        assert payload is not None
        assert payload.type == "refresh"

    def test_access_type_rejected_as_refresh(self):
        token, _ = create_refresh_token("u1", "t1")
        assert decode_token(token, expected_type="access") is None
