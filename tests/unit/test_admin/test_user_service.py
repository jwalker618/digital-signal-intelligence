"""B-3b/c: UserService + RoleService + InvitationService schema tests (no DB)."""

import pytest
from pydantic import ValidationError

from infrastructure.admin.user_service import (
    INVITATION_TTL_DAYS,
    RoleService,
)
from infrastructure.api.admin.user_routes import (
    AcceptInvitationRequest,
    InviteRequest,
    RoleCreateRequest,
    UserCreateRequest,
    UserUpdateRequest,
)


class TestUserCreateRequest:
    def test_valid(self):
        req = UserCreateRequest(
            email="bob@example.com",
            full_name="Bob",
            role_id="00000000-0000-0000-0000-000000000000",
            password="MinimumLength12",
        )
        assert req.email == "bob@example.com"

    def test_rejects_short_password(self):
        with pytest.raises(ValidationError):
            UserCreateRequest(
                email="bob@example.com",
                full_name="Bob",
                role_id="x",
                password="short",
            )

    def test_rejects_empty_name(self):
        with pytest.raises(ValidationError):
            UserCreateRequest(
                email="bob@example.com",
                full_name="",
                role_id="x",
                password="MinimumLength12",
            )

    def test_rejects_bad_email(self):
        with pytest.raises(ValidationError):
            UserCreateRequest(
                email="not-an-email",
                full_name="Bob",
                role_id="x",
                password="MinimumLength12",
            )


class TestUserUpdateRequest:
    def test_all_optional(self):
        req = UserUpdateRequest()
        assert req.model_dump(exclude_unset=True) == {}

    def test_partial_update(self):
        req = UserUpdateRequest(full_name="Jane", is_active=False)
        dumped = req.model_dump(exclude_unset=True)
        assert dumped == {"full_name": "Jane", "is_active": False}


class TestRoleCreateRequest:
    def test_name_uppercased(self):
        req = RoleCreateRequest(name="custom", description="x", permissions=[])
        assert req.name == "CUSTOM"

    def test_default_permissions_empty(self):
        req = RoleCreateRequest(name="x")
        assert req.permissions == []


class TestInviteRequest:
    def test_valid(self):
        req = InviteRequest(email="x@y.com", role_id="abc")
        assert req.email == "x@y.com"

    def test_rejects_invalid_email(self):
        with pytest.raises(ValidationError):
            InviteRequest(email="no-at-sign", role_id="abc")


class TestAcceptInvitationRequest:
    def test_requires_password_length(self):
        with pytest.raises(ValidationError):
            AcceptInvitationRequest(token="x", full_name="y", password="short")

    def test_requires_non_empty_fields(self):
        with pytest.raises(ValidationError):
            AcceptInvitationRequest(token="", full_name="y", password="MinimumLength12")
        with pytest.raises(ValidationError):
            AcceptInvitationRequest(token="x", full_name="", password="MinimumLength12")


class TestInvitationTtlConstant:
    def test_seven_days(self):
        assert INVITATION_TTL_DAYS == 7


class TestRolePermissionValidation:
    def test_unknown_permission_rejected(self):
        with pytest.raises(ValueError) as exc_info:
            RoleService._validate_permissions(["not:a:permission"])
        assert "Unknown permissions" in str(exc_info.value)

    def test_all_valid_permissions_accepted(self):
        from infrastructure.api.auth.permissions import Permission
        all_perms = [p.value for p in Permission]
        # Should not raise
        RoleService._validate_permissions(all_perms)

    def test_empty_permissions_accepted(self):
        # Empty list is valid (role with no permissions)
        RoleService._validate_permissions([])
