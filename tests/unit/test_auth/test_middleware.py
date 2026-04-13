"""A-1e: Tenant middleware path classification tests."""

from infrastructure.api.auth.tenant_middleware import _is_public_path


class TestPublicPaths:
    def test_root(self):
        assert _is_public_path("/") is True

    def test_api_v1_root(self):
        assert _is_public_path("/api/v1") is True

    def test_health(self):
        assert _is_public_path("/api/v1/health/live") is True
        assert _is_public_path("/api/v1/health/ready") is True

    def test_login_and_refresh(self):
        assert _is_public_path("/api/v1/auth/login") is True
        assert _is_public_path("/api/v1/auth/refresh") is True
        assert _is_public_path("/api/v1/auth/logout") is True

    def test_sso(self):
        assert _is_public_path("/api/v1/auth/sso/some-tenant") is True
        assert _is_public_path("/api/v1/auth/sso/callback") is True

    def test_password_reset(self):
        assert _is_public_path("/api/v1/auth/password/reset-request") is True
        assert _is_public_path("/api/v1/auth/password/reset-confirm") is True

    def test_docs(self):
        assert _is_public_path("/api/docs") is True
        assert _is_public_path("/openapi.json") is True

    def test_metrics(self):
        assert _is_public_path("/metrics") is True
        assert _is_public_path("/api/v1/metrics") is True


class TestProtectedPaths:
    def test_me_endpoint_not_public(self):
        assert _is_public_path("/api/v1/auth/me") is False

    def test_mfa_endpoints_not_public(self):
        assert _is_public_path("/api/v1/auth/mfa/setup") is False
        assert _is_public_path("/api/v1/auth/mfa/verify") is False

    def test_business_endpoints_not_public(self):
        assert _is_public_path("/api/v1/submissions") is False
        assert _is_public_path("/api/v1/quotes") is False
        assert _is_public_path("/api/v1/world-engine/maturity") is False

    def test_api_v1_sub_paths_not_public(self):
        assert _is_public_path("/api/v1/anything/else") is False
