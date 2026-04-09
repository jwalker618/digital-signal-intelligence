# Phase B-3: User & Permission Management

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | A-1 (user/role schema) |

---

## Overview

Admin UI for managing users, roles, and permissions within a tenant. Includes user invitation flow, custom role creation, and permission enforcement.

## Current State

- A-1 creates `users`, `tenants`, `roles` tables and the `Permission` enum with default roles.
- No admin UI for user/role management. User creation is CLI/seed-script only.

## Target State

Admin pages for CRUD on users and roles, invitation flow with email, and live permission enforcement.

---

## Implementation Plan

### B-3a: User Management API

**New file**: `infrastructure/api/admin/user_routes.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/users` | GET | List users (filterable by role, status, search) |
| `/admin/users` | POST | Create user / send invitation |
| `/admin/users/{id}` | GET | User detail |
| `/admin/users/{id}` | PUT | Update user (name, role, active status) |
| `/admin/users/{id}/deactivate` | POST | Deactivate (soft delete) |
| `/admin/users/invite` | POST | Send email invitation with registration link |

### B-3b: Role Management API

**New file**: `infrastructure/api/admin/role_routes.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/roles` | GET | List roles with permission summary |
| `/admin/roles` | POST | Create custom role |
| `/admin/roles/{id}` | PUT | Update role permissions |
| `/admin/roles/{id}` | DELETE | Delete role (fails if users assigned) |
| `/admin/permissions` | GET | List all available permissions |

### B-3c: Invitation Service

**New file**: `infrastructure/admin/invitation_service.py`

```python
class InvitationService:
    """Handles user invitation flow."""

    def send_invitation(self, email: str, role_id: str, tenant_id: str, inviter_id: str) -> str:
        """Generate token, store pending invitation, send email with registration link."""

    def complete_registration(self, token: str, name: str, password: str) -> User:
        """Validate token, create user, assign role, mark invitation as used."""
```

### B-3d: Frontend -- User Management

**New file**: `frontend/src/app/admin/users/page.tsx`
- Table: name, email, role, status, last login
- Create/invite button, edit inline, deactivate with confirmation

**New file**: `frontend/src/app/admin/roles/page.tsx`
- Table: role name, user count, permission summary
- Create/edit with permission checkboxes grouped by domain (assessment, config, admin, etc.)

---

## Constraints

1. System roles (DEFAULT_ROLES from A-1) can have permissions viewed but not deleted
2. Cannot deactivate the last admin user in a tenant
3. All user/role changes are audit-logged via A-2

## Success Criteria

1. Admin can create, edit, and deactivate users
2. Admin can create custom roles with specific permissions
3. Permission enforcement works -- users without `config:write` cannot edit configs
4. User invitation flow works end-to-end
5. Audit log captures all user/role changes
