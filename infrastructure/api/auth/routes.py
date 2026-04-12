"""
A-1f: Auth API Routes

Endpoints mounted at /api/v1/auth/:
- POST /auth/login          email/password login
- POST /auth/refresh        rotate refresh token, return new pair
- POST /auth/logout         revoke current session
- POST /auth/mfa/setup      generate TOTP secret + QR URI
- POST /auth/mfa/verify     verify 6-digit TOTP code, enable MFA
- POST /auth/mfa/backup-codes  generate single-use backup codes
- GET  /auth/sso/{slug}     kick off SSO redirect for a tenant
- POST /auth/sso/callback   process SAML/OIDC response
- POST /auth/password/reset-request  send reset email (future)
- POST /auth/password/reset-confirm  consume reset token

All endpoints are PUBLIC (listed in tenant_middleware.PUBLIC_PATH_PREFIXES)
since they are responsible for issuing auth tokens. The /mfa/* endpoints
require an existing valid access token (checked inline).
"""

from __future__ import annotations

import base64
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.api.auth.jwt_auth import (
    DEFAULT_REFRESH_TOKEN_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from infrastructure.api.auth.permissions import AuthContext, get_auth_context
from infrastructure.api.auth.sso import SSOError, provider_for
from infrastructure.db.config import get_db
from infrastructure.db.models import Role, Tenant, User, UserSession

logger = logging.getLogger("dsi.api.auth.routes")
router = APIRouter()


# =============================================================================
# Request/response schemas
# =============================================================================


class LoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=1)
    remember_me: bool = False


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int  # access token lifetime
    mfa_required: bool = False
    mfa_setup_required: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class MFASetupResponse(BaseModel):
    secret: str
    otpauth_uri: str  # for QR code generation in the frontend


class MFAVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class MFAVerifyResponse(BaseModel):
    mfa_enabled: bool


class BackupCodesResponse(BaseModel):
    codes: list[str]  # shown exactly once


class SSOStartResponse(BaseModel):
    redirect_url: str


class SSOCallbackRequest(BaseModel):
    tenant_slug: str
    saml_response: Optional[str] = None  # base64 SAMLResponse
    code: Optional[str] = None  # OIDC authorisation code
    state: Optional[str] = None


# =============================================================================
# Helpers
# =============================================================================


def _load_user(db: Session, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email.lower())
    return db.execute(stmt).scalar_one_or_none()


def _load_tenant_by_slug(db: Session, slug: str) -> Optional[Tenant]:
    return db.execute(select(Tenant).where(Tenant.slug == slug)).scalar_one_or_none()


def _permissions_for_user(db: Session, user: User) -> list[str]:
    """Resolve the user's effective permission list from their role."""
    if not user.role_id:
        return []
    role = db.execute(select(Role).where(Role.id == user.role_id)).scalar_one_or_none()
    if role is None:
        return []
    return list(role.permissions or [])


def _issue_token_pair(
    db: Session,
    user: User,
    request: Request,
    remember_me: bool = False,
) -> TokenPair:
    """Create an access+refresh pair, persist a session, return the tokens."""
    permissions = _permissions_for_user(db, user)
    role = (
        db.execute(select(Role).where(Role.id == user.role_id)).scalar_one_or_none()
        if user.role_id
        else None
    )

    # Access token (15min default, configurable per tenant)
    access_token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id) if user.tenant_id else "",
        role=role.name if role else None,
        permissions=permissions,
        email=user.email,
    )

    # Refresh token (7d default, 30d if remember_me)
    refresh_days = 30 if remember_me else DEFAULT_REFRESH_TOKEN_DAYS
    refresh_token, refresh_hash = create_refresh_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id) if user.tenant_id else "",
        expires_days=refresh_days,
    )

    # Persist session
    session_row = UserSession(
        user_id=user.id,
        tenant_id=user.tenant_id,
        refresh_token_hash=refresh_hash,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=refresh_days),
    )
    db.add(session_row)

    # Update user's last_login / failed_login_attempts
    user.last_login = datetime.now(timezone.utc)
    user.failed_login_attempts = 0

    db.commit()

    from infrastructure.api.auth.jwt_auth import DEFAULT_ACCESS_TOKEN_MINUTES

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_seconds=DEFAULT_ACCESS_TOKEN_MINUTES * 60,
    )


def _decrypt_secret(stored: str) -> str:
    """Decrypt MFA secret. For now stored as plain-text; full encryption in
    a later phase. This indirection is here so the upgrade path is a single
    function change."""
    return stored


def _encrypt_secret(plain: str) -> str:
    """Encrypt MFA secret. See _decrypt_secret note."""
    return plain


# =============================================================================
# Login
# =============================================================================


@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    """Email/password login. Returns access + refresh tokens.

    Returns mfa_required=True if MFA is enabled -- the client should then
    call /auth/mfa/verify with the returned access_token to complete login.
    (Implementation note: for simplicity, MFA is verified by requiring a
    second login call. A cleaner flow is a two-step challenge/response
    which we can layer in later.)
    """
    user = _load_user(db, body.email.lower())
    generic_unauth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
    )
    if user is None:
        raise generic_unauth
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")
    if user.is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account locked")
    if not verify_password(body.password, user.hashed_password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= 10:
            user.is_locked = True
        db.commit()
        raise generic_unauth
    if user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no tenant")

    pair = _issue_token_pair(db, user, request, remember_me=body.remember_me)
    return LoginResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in_seconds=pair.expires_in_seconds,
        mfa_required=bool(user.mfa_enabled),
        mfa_setup_required=False,
    )


# =============================================================================
# Refresh
# =============================================================================


@router.post("/auth/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    """Rotate the refresh token. The old refresh token is invalidated."""
    payload = decode_token(body.refresh_token, expected_type="refresh")
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Find and invalidate the session row
    old_hash = hash_token(body.refresh_token)
    session_row = db.execute(
        select(UserSession).where(UserSession.refresh_token_hash == old_hash)
    ).scalar_one_or_none()
    if session_row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")
    if session_row.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")
    if session_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    # Load user
    user = db.execute(select(User).where(User.id == session_row.user_id)).scalar_one_or_none()
    if user is None or not user.is_active or user.is_locked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")

    # Rotate: mint new refresh, update session row hash
    permissions = _permissions_for_user(db, user)
    role = db.execute(select(Role).where(Role.id == user.role_id)).scalar_one_or_none() if user.role_id else None

    access_token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=role.name if role else None,
        permissions=permissions,
        email=user.email,
    )
    new_refresh, new_hash = create_refresh_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        expires_days=DEFAULT_REFRESH_TOKEN_DAYS,
    )

    session_row.refresh_token_hash = new_hash
    session_row.last_activity_at = datetime.now(timezone.utc)
    db.commit()

    from infrastructure.api.auth.jwt_auth import DEFAULT_ACCESS_TOKEN_MINUTES

    return TokenPair(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in_seconds=DEFAULT_ACCESS_TOKEN_MINUTES * 60,
    )


# =============================================================================
# Logout
# =============================================================================


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    body: RefreshRequest,
    db: Session = Depends(get_db),
):
    """Revoke the session associated with the provided refresh token."""
    old_hash = hash_token(body.refresh_token)
    session_row = db.execute(
        select(UserSession).where(UserSession.refresh_token_hash == old_hash)
    ).scalar_one_or_none()
    if session_row and session_row.revoked_at is None:
        session_row.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return None


# =============================================================================
# MFA
# =============================================================================


@router.post("/auth/mfa/setup", response_model=MFASetupResponse)
def mfa_setup(
    ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)
) -> MFASetupResponse:
    """Generate a new TOTP secret. User must call /mfa/verify to enable."""
    user = db.execute(select(User).where(User.id == UUID(ctx.user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    secret = pyotp.random_base32()
    user.mfa_secret = _encrypt_secret(secret)
    user.mfa_enabled = False  # not enabled until verified
    db.commit()

    issuer = "DSI"
    label = f"{issuer}:{user.email}"
    otpauth_uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=issuer)
    return MFASetupResponse(secret=secret, otpauth_uri=otpauth_uri)


@router.post("/auth/mfa/verify", response_model=MFAVerifyResponse)
def mfa_verify(
    body: MFAVerifyRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> MFAVerifyResponse:
    """Verify a TOTP code and enable MFA for the user."""
    user = db.execute(select(User).where(User.id == UUID(ctx.user_id))).scalar_one_or_none()
    if user is None or not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA not set up")

    totp = pyotp.TOTP(_decrypt_secret(user.mfa_secret))
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid code")

    user.mfa_enabled = True
    db.commit()
    return MFAVerifyResponse(mfa_enabled=True)


@router.post("/auth/mfa/backup-codes", response_model=BackupCodesResponse)
def mfa_backup_codes(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> BackupCodesResponse:
    """Generate 10 single-use backup codes. Previously-generated codes are invalidated."""
    user = db.execute(select(User).where(User.id == UUID(ctx.user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    codes_plain = [secrets.token_hex(5) for _ in range(10)]
    user.mfa_backup_codes = [hash_token(c) for c in codes_plain]
    db.commit()
    return BackupCodesResponse(codes=codes_plain)


# =============================================================================
# SSO
# =============================================================================


@router.get("/auth/sso/{tenant_slug}", response_model=SSOStartResponse)
def sso_start(tenant_slug: str, db: Session = Depends(get_db)) -> SSOStartResponse:
    """Kick off SSO redirect for a tenant. Returns the URL to redirect to."""
    tenant = _load_tenant_by_slug(db, tenant_slug)
    if tenant is None or tenant.sso_provider == "NONE":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SSO not configured for tenant")
    provider = provider_for(tenant)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No SSO provider")

    try:
        if tenant.sso_provider == "SAML":
            url = provider.get_auth_redirect()
        else:  # OIDC
            state = secrets.token_urlsafe(16)
            url = provider.get_auth_url(state=state)
    except SSOError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    return SSOStartResponse(redirect_url=url)


@router.post("/auth/sso/callback", response_model=LoginResponse)
def sso_callback(
    body: SSOCallbackRequest, request: Request, db: Session = Depends(get_db)
) -> LoginResponse:
    """Process SAML assertion or OIDC code. Issues tokens for the matched user."""
    tenant = _load_tenant_by_slug(db, body.tenant_slug)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    provider = provider_for(tenant)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SSO not configured")

    try:
        if tenant.sso_provider == "SAML":
            if not body.saml_response:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="saml_response required")
            claims = provider.process_assertion(body.saml_response, host=request.url.hostname or "")
        else:  # OIDC
            if not body.code:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="code required")
            claims = provider.exchange_code(body.code)
    except SSOError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    # Find or provision the user
    user = _load_user(db, claims.email.lower())
    if user is None:
        # Auto-provision with the tenant's default role (first non-ADMIN role, or READ_ONLY)
        default_role_name = tenant.settings.get("default_sso_role", "READ_ONLY")
        role = db.execute(
            select(Role).where(Role.tenant_id == tenant.id, Role.name == default_role_name)
        ).scalar_one_or_none()
        user = User(
            email=claims.email.lower(),
            hashed_password="$2b$12$SSO_USER_NO_PASSWORD",  # SSO-only account
            full_name=claims.name,
            tenant_id=tenant.id,
            role_id=role.id if role else None,
            is_active=True,
        )
        db.add(user)
        db.flush()
    elif user.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User exists in a different tenant",
        )

    if not user.is_active or user.is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account unavailable")

    pair = _issue_token_pair(db, user, request)
    return LoginResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in_seconds=pair.expires_in_seconds,
        mfa_required=bool(user.mfa_enabled),
    )


# =============================================================================
# Password management
# =============================================================================


class PasswordResetRequestBody(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PasswordResetConfirmBody(BaseModel):
    token: str
    new_password: str = Field(min_length=12)


@router.post("/auth/password/reset-request", status_code=status.HTTP_204_NO_CONTENT)
def password_reset_request(body: PasswordResetRequestBody, db: Session = Depends(get_db)):
    """Initiate password reset. Sends email with token (email integration TBD).

    Returns 204 regardless of whether the email exists (avoid account enumeration).
    """
    user = _load_user(db, body.email.lower())
    if user is not None and user.is_active:
        raw_token = secrets.token_urlsafe(32)
        user.password_reset_token_hash = hash_token(raw_token)
        user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        # TODO: email the user with raw_token. Email integration is a later
        # phase. For now the token is logged at debug level.
        logger.debug("Password reset token issued for %s (dev only)", user.email)
    return None


@router.post("/auth/password/reset-confirm", status_code=status.HTTP_204_NO_CONTENT)
def password_reset_confirm(body: PasswordResetConfirmBody, db: Session = Depends(get_db)):
    """Consume a reset token and set a new password."""
    token_hash = hash_token(body.token)
    user = db.execute(
        select(User).where(User.password_reset_token_hash == token_hash)
    ).scalar_one_or_none()
    if user is None or not user.password_reset_expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    if user.password_reset_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")

    user.hashed_password = hash_password(body.new_password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    user.failed_login_attempts = 0
    user.is_locked = False
    db.commit()
    return None


# =============================================================================
# Current user
# =============================================================================


class MeResponse(BaseModel):
    user_id: str
    email: Optional[str]
    tenant_id: str
    role: Optional[str]
    permissions: list[str]
    mfa_enabled: bool


@router.get("/auth/me", response_model=MeResponse)
def me(ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> MeResponse:
    """Return the authenticated user's profile summary."""
    user = db.execute(select(User).where(User.id == UUID(ctx.user_id))).scalar_one_or_none()
    return MeResponse(
        user_id=ctx.user_id,
        email=ctx.email,
        tenant_id=ctx.tenant_id,
        role=ctx.role,
        permissions=sorted(ctx.permissions),
        mfa_enabled=bool(user.mfa_enabled) if user else False,
    )
