"""
A-1c: SSO Integration (SAML 2.0 and OIDC)

Provides:
- SAMLProvider: generates the auth redirect, processes SAML assertions.
- OIDCProvider: generates the auth URL, exchanges the authorisation code.
- UserClaims: normalised output used by the login flow to locate or provision
  a user account.

SAML is implemented via python3-saml. OIDC via authlib. Both are optional
dependencies -- if the tenant's sso_provider is NONE, these modules are not
imported. The module imports defer optional deps lazily inside methods so
tenants not using SSO never require them to be installed.

Tenant.sso_metadata structure:
  SAML:
    {"idp_entity_id": "...", "idp_sso_url": "...", "idp_x509_cert": "...",
     "sp_entity_id": "...", "attribute_mapping": {"email": "...", "groups": "..."}}
  OIDC:
    {"issuer": "...", "client_id": "...", "client_secret": "...",
     "redirect_uri": "...", "scopes": ["openid", "email", "profile", "groups"]}
"""

from __future__ import annotations

import logging
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger("dsi.api.auth.sso")


class UserClaims(BaseModel):
    """Normalised claims extracted from a successful SSO login.

    The login flow uses these to find or provision a user in the tenant.
    """

    email: str
    name: Optional[str] = None
    groups: list[str] = []
    external_id: Optional[str] = None  # IdP's stable user identifier
    raw: dict = {}


class SSOError(Exception):
    """Raised when SSO validation or processing fails."""


# ---------------------------------------------------------------------------
# SAML 2.0
# ---------------------------------------------------------------------------


class SAMLProvider:
    """SAML 2.0 SSO integration.

    Requires: python3-saml (not imported at module scope).

    Usage:
        provider = SAMLProvider(tenant)
        redirect_url = provider.get_auth_redirect(relay_state="...")
        # ... user authenticates at IdP, POSTs SAML response back to /auth/sso/callback ...
        claims = provider.process_assertion(saml_response_base64)
    """

    def __init__(self, tenant):
        self.tenant = tenant
        if tenant.sso_provider != "SAML":
            raise SSOError(f"Tenant {tenant.slug} is not configured for SAML")
        self.metadata = tenant.sso_metadata or {}

    def _settings(self) -> dict:
        """Build the python3-saml settings dict from the tenant metadata."""
        md = self.metadata
        required = ["idp_entity_id", "idp_sso_url", "idp_x509_cert", "sp_entity_id", "sp_acs_url"]
        missing = [k for k in required if not md.get(k)]
        if missing:
            raise SSOError(f"SAML tenant metadata missing keys: {missing}")

        return {
            "strict": True,
            "debug": False,
            "sp": {
                "entityId": md["sp_entity_id"],
                "assertionConsumerService": {
                    "url": md["sp_acs_url"],
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                "x509cert": md.get("sp_x509_cert", ""),
                "privateKey": md.get("sp_private_key", ""),
            },
            "idp": {
                "entityId": md["idp_entity_id"],
                "singleSignOnService": {
                    "url": md["idp_sso_url"],
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": md["idp_x509_cert"],
            },
        }

    def get_auth_redirect(self, relay_state: str = "") -> str:
        """Return the URL the browser should be redirected to for IdP auth."""
        from onelogin.saml2.auth import OneLogin_Saml2_Auth  # type: ignore

        request_data = {
            "https": "on",
            "http_host": self.metadata.get("sp_host", ""),
            "server_port": "443",
            "script_name": "/",
            "get_data": {},
            "post_data": {},
        }
        auth = OneLogin_Saml2_Auth(request_data, self._settings())
        return auth.login(return_to=relay_state)

    def process_assertion(self, saml_response_b64: str, host: str) -> UserClaims:
        """Validate a SAML assertion and extract user claims."""
        from onelogin.saml2.auth import OneLogin_Saml2_Auth  # type: ignore

        request_data = {
            "https": "on",
            "http_host": host,
            "server_port": "443",
            "script_name": "/",
            "get_data": {},
            "post_data": {"SAMLResponse": saml_response_b64},
        }
        auth = OneLogin_Saml2_Auth(request_data, self._settings())
        auth.process_response()
        errors = auth.get_errors()
        if errors:
            raise SSOError(f"SAML validation failed: {errors}; last_error={auth.get_last_error_reason()}")
        if not auth.is_authenticated():
            raise SSOError("SAML response did not authenticate")

        attrs = auth.get_attributes()
        mapping = self.metadata.get("attribute_mapping", {})
        email_attr = mapping.get("email", "email")
        groups_attr = mapping.get("groups", "groups")
        name_attr = mapping.get("name", "name")

        email_values = attrs.get(email_attr) or [auth.get_nameid()]
        email = email_values[0] if email_values else None
        if not email:
            raise SSOError("SAML response missing email attribute")

        return UserClaims(
            email=email,
            name=(attrs.get(name_attr) or [None])[0],
            groups=attrs.get(groups_attr) or [],
            external_id=auth.get_nameid(),
            raw=attrs,
        )


# ---------------------------------------------------------------------------
# OIDC
# ---------------------------------------------------------------------------


class OIDCProvider:
    """OIDC SSO integration (Auth0, Okta, Azure AD, etc.).

    Requires: authlib (not imported at module scope).
    """

    def __init__(self, tenant):
        self.tenant = tenant
        if tenant.sso_provider != "OIDC":
            raise SSOError(f"Tenant {tenant.slug} is not configured for OIDC")
        self.metadata = tenant.sso_metadata or {}
        required = ["issuer", "client_id", "client_secret", "redirect_uri"]
        missing = [k for k in required if not self.metadata.get(k)]
        if missing:
            raise SSOError(f"OIDC tenant metadata missing keys: {missing}")

    def get_auth_url(self, state: str) -> str:
        """Return the OIDC authorisation URL to redirect the browser to."""
        from urllib.parse import urlencode

        scopes = " ".join(self.metadata.get("scopes") or ["openid", "email", "profile"])
        params = {
            "response_type": "code",
            "client_id": self.metadata["client_id"],
            "redirect_uri": self.metadata["redirect_uri"],
            "scope": scopes,
            "state": state,
        }
        return f"{self.metadata['issuer'].rstrip('/')}/authorize?{urlencode(params)}"

    def exchange_code(self, code: str) -> UserClaims:
        """Exchange an authorisation code for tokens + extract claims."""
        import httpx

        token_url = f"{self.metadata['issuer'].rstrip('/')}/oauth/token"
        userinfo_url = f"{self.metadata['issuer'].rstrip('/')}/userinfo"

        with httpx.Client(timeout=10.0) as client:
            token_resp = client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.metadata["redirect_uri"],
                    "client_id": self.metadata["client_id"],
                    "client_secret": self.metadata["client_secret"],
                },
            )
            if token_resp.status_code >= 400:
                raise SSOError(f"OIDC token exchange failed: {token_resp.status_code} {token_resp.text}")
            tokens = token_resp.json()

            access_token = tokens.get("access_token")
            if not access_token:
                raise SSOError("OIDC response missing access_token")

            userinfo_resp = client.get(
                userinfo_url, headers={"Authorization": f"Bearer {access_token}"}
            )
            if userinfo_resp.status_code >= 400:
                raise SSOError(f"OIDC userinfo failed: {userinfo_resp.status_code}")
            info = userinfo_resp.json()

        email = info.get("email")
        if not email:
            raise SSOError("OIDC userinfo missing email")

        return UserClaims(
            email=email,
            name=info.get("name"),
            groups=info.get("groups") or info.get("roles") or [],
            external_id=info.get("sub"),
            raw=info,
        )


def provider_for(tenant):
    """Factory: returns the appropriate provider for the tenant, or None if NONE."""
    if tenant.sso_provider == "SAML":
        return SAMLProvider(tenant)
    if tenant.sso_provider == "OIDC":
        return OIDCProvider(tenant)
    return None
