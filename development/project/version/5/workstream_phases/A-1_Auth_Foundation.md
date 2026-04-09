# Phase A-1: Auth Foundation

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | None -- this is the first phase |

---

## Overview

Replace the lightweight JWT + API key auth (`infrastructure/api/auth/`) with enterprise-grade multi-tenant authentication supporting SSO/SAML, OIDC, MFA, and granular role-based permissions. This gates every subsequent phase in Workstreams A and B.

## Current State

- `infrastructure/api/auth/jwt_auth.py` -- JWT token authentication
- `infrastructure/api/auth/api_key.py` -- API key validation (prefix matching, hash verification)
- `infrastructure/db/models.py` -- `User` model (email, permissions JSONB, 2FA fields exist but not wired), `APIKey` model
- `infrastructure/api/main.py` -- CORS middleware, rate limiting, request logging. Auth middleware is minimal.
- No multi-tenant support. No SSO/SAML. No role model. No tenant-scoped queries.

## Target State

Full multi-tenant auth system with User/Tenant/Role models, SSO/SAML + OIDC support, MFA, JWT with tenant context, and middleware that automatically scopes all queries by tenant.

---

## Implementation Plan

### A-1a: Database Models & Migration

**New migration**: `alembic/versions/012_auth_foundation.py`

| Table | Key Columns |
|-------|-------------|
| `tenants` | `id` (UUID), `name`, `slug` (unique), `sso_provider` (enum: NONE/SAML/OIDC), `sso_metadata` (JSONB), `settings` (JSONB -- session duration, MFA policy), `created_at` |
| `roles` | `id` (UUID), `tenant_id` FK, `name`, `permissions` (JSONB array), `is_system_role` (bool), `created_at` |
| `users` (alter) | Add `tenant_id` FK, `role_id` FK, `mfa_secret` (encrypted), `mfa_backup_codes` (encrypted JSONB), `mfa_enabled`, `is_active`, `last_login`, `password_hash` |
| `user_sessions` | `id`, `user_id` FK, `tenant_id` FK, `token_hash`, `refresh_token_hash`, `expires_at`, `created_at`, `last_activity` |

Add `tenant_id` FK to all tenant-scoped existing tables: `submissions`, `quotes`, `model_version_records`, `referrals`. Backfill with a default system tenant.

**Indexes**: `users` on (`tenant_id`, `email`) unique. `roles` on (`tenant_id`, `name`) unique.

### A-1b: Permission System

**New file**: `infrastructure/api/auth/permissions.py`

```python
class Permission(str, Enum):
    ASSESSMENT_READ = "assessment:read"
    ASSESSMENT_WRITE = "assessment:write"
    ASSESSMENT_REFER = "assessment:refer"
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"
    CONFIG_DEPLOY = "config:deploy"
    ENTITY_READ = "entity:read"
    ENTITY_WRITE = "entity:write"
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_AUDIT = "admin:audit"
    RECALIBRATION_VIEW = "recalibration:view"
    RECALIBRATION_APPROVE = "recalibration:approve"
    PORTFOLIO_VIEW = "portfolio:view"
    PORTFOLIO_SIMULATE = "portfolio:simulate"
    WORLD_ENGINE_VIEW = "world_engine:view"

DEFAULT_ROLES = {
    "UNDERWRITER": [ASSESSMENT_READ, ASSESSMENT_WRITE, ASSESSMENT_REFER],
    "SENIOR_UNDERWRITER": [... + CONFIG_READ],
    "ACTUARIAL": [... + CONFIG_WRITE, RECALIBRATION_VIEW, RECALIBRATION_APPROVE],
    "ADMIN": [all],
    "READ_ONLY": [ASSESSMENT_READ, CONFIG_READ, ENTITY_READ, PORTFOLIO_VIEW],
}

def require_permission(*perms: Permission) -> Depends:
    """FastAPI dependency that checks the authenticated user has all listed permissions."""
```

### A-1c: SSO/SAML & OIDC Integration

**New file**: `infrastructure/api/auth/sso.py`

```python
class SAMLProvider:
    """SAML 2.0 integration via python3-saml."""
    def get_auth_redirect(self, tenant: Tenant) -> str: ...
    def process_assertion(self, saml_response: str, tenant: Tenant) -> UserClaims: ...

class OIDCProvider:
    """OIDC integration for Auth0/Okta/Azure AD."""
    def get_auth_url(self, tenant: Tenant) -> str: ...
    def exchange_code(self, code: str, tenant: Tenant) -> UserClaims: ...

class UserClaims(BaseModel):
    email: str
    name: str
    groups: list[str]  # Mapped to DSI roles via tenant config
```

### A-1d: Session Management

**File to modify**: `infrastructure/api/auth/jwt_auth.py`

Replace current JWT implementation with tenant-aware version:

```python
class TokenPayload(BaseModel):
    user_id: str
    tenant_id: str
    role: str
    permissions: list[str]
    exp: datetime

def create_token_pair(user: User) -> tuple[str, str]:
    """Returns (access_token, refresh_token). Access: 15min. Refresh: 7d (configurable per tenant)."""

def refresh_access_token(refresh_token: str) -> str:
    """Rotate refresh token on use. Invalidate old."""
```

### A-1e: Tenant-Scoped Middleware

**New file**: `infrastructure/api/auth/tenant_middleware.py`

```python
class TenantMiddleware:
    """Extracts tenant from JWT, injects into request state, scopes DB queries."""

    async def __call__(self, request: Request, call_next):
        """
        1. Extract tenant_id from JWT payload
        2. Set request.state.tenant_id
        3. Apply SQLAlchemy session event to add .filter(tenant_id=...) to all queries
        """
```

**File to modify**: `infrastructure/api/main.py` -- Replace current auth middleware, add TenantMiddleware.

### A-1f: Auth API Routes

**New file**: `infrastructure/api/auth/routes.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Email/password login, returns token pair |
| `/auth/sso/{tenant_slug}` | GET | SSO redirect for tenant |
| `/auth/sso/callback` | POST | SSO assertion processing |
| `/auth/refresh` | POST | Refresh token rotation |
| `/auth/logout` | POST | Invalidate session |
| `/auth/mfa/setup` | POST | Generate TOTP secret + QR URI |
| `/auth/mfa/verify` | POST | Verify 6-digit TOTP code |
| `/auth/mfa/backup-codes` | POST | Generate backup codes |

### A-1g: Seed Script

**File to modify**: `seed_dsi_bench.py`

Create default system tenant, admin user, and default roles. Assign all existing seeded data to system tenant.

---

## Constraints

1. Existing API key auth must continue to work during migration (backwards-compatible)
2. MFA secrets and backup codes must be encrypted at rest
3. Password hashing via `bcrypt` or `argon2`
4. No plaintext credentials in logs or error responses

## Success Criteria

1. Users can log in via username/password and via SAML SSO
2. MFA enrollment and verification works
3. API requests without valid auth return 401
4. Users in Tenant A cannot see data from Tenant B
5. Role-based permissions control API endpoint access
6. Default admin user can create new users and tenants
7. Existing API key auth still works (backwards-compatible)
