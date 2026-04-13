// A-3a: Auth types
//
// Mirrors the response schemas from /api/v1/auth/* (see
// infrastructure/api/auth/routes.py). Kept intentionally narrow --
// we only model what the frontend consumes.

export interface AuthUser {
  user_id: string;
  email: string | null;
  tenant_id: string;
  role: string | null;
  permissions: string[];
  mfa_enabled: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  expires_in_seconds: number;
}

export interface LoginResponse extends TokenPair {
  token_type?: string;
  mfa_required: boolean;
  mfa_setup_required?: boolean;
}

export interface MFASetupResponse {
  secret: string;
  otpauth_uri: string;
}

export interface SSOStartResponse {
  redirect_url: string;
}

// Permission strings are snake:case:verb, matching A-1's
// infrastructure/api/auth/permissions.py::Permission enum.
export type Permission =
  | "assessment:read"
  | "assessment:write"
  | "assessment:refer"
  | "entity:read"
  | "entity:write"
  | "config:read"
  | "config:write"
  | "config:deploy"
  | "recalibration:view"
  | "recalibration:approve"
  | "portfolio:view"
  | "portfolio:simulate"
  | "world_engine:view"
  | "admin:system"
  | "admin:users"
  | "admin:audit";

export type Role =
  | "ADMIN"
  | "ACTUARIAL"
  | "SENIOR_UNDERWRITER"
  | "UNDERWRITER"
  | "READ_ONLY";
