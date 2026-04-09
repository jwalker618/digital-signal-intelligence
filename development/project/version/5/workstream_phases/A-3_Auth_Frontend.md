# Phase A-3: Auth Frontend & Login Experience

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | A-1, A-2 |

---

## Overview

The complete authentication UI: login screen, MFA flow, role-based navigation, session management, user profile, and real-time notification integration.

## Current State

- `frontend/src/app/layout.tsx` -- App layout with sidebar navigation. No auth gating.
- `frontend/src/stores/dsiStore.ts` -- Zustand state management. No user/auth state.
- `frontend/src/types/dsi.ts` -- TypeScript types. No user/auth types.
- No login page, no MFA flow, no session management, no role-based navigation.

## Target State

Complete auth UI with login, MFA, SSO redirect, role-gated navigation, WebSocket-driven notifications, session management, and user profile.

---

## Implementation Plan

### A-3a: Auth Store & Types

**New file**: `frontend/src/stores/authStore.ts`

```typescript
interface AuthState {
  user: User | null;
  tenant: Tenant | null;
  permissions: string[];
  isAuthenticated: boolean;
  sessionExpiresAt: Date | null;
  login(email: string, password: string): Promise<void>;
  loginSSO(tenantSlug: string): void;
  verifyMFA(code: string): Promise<void>;
  refreshToken(): Promise<void>;
  logout(): void;
  hasPermission(perm: string): boolean;
}
```

**New file**: `frontend/src/types/auth.ts` -- User, Tenant, Role, Permission types.

### A-3b: Login Page

**New file**: `frontend/src/app/login/page.tsx`

- Email/password form with validation
- SSO redirect button (tenant-specific branding from slug)
- Error handling: invalid credentials, locked account, expired session
- "Remember me" checkbox (extends refresh token TTL)
- Link to password reset flow

### A-3c: MFA Flow

**New file**: `frontend/src/components/auth/MFASetup.tsx` -- QR code enrollment (TOTP), backup codes generation/download
**New file**: `frontend/src/components/auth/MFAVerify.tsx` -- 6-digit code entry on login

### A-3d: Password Management

**New file**: `frontend/src/app/reset-password/page.tsx` -- Email link reset flow
**New file**: `frontend/src/components/auth/ChangePassword.tsx` -- Current + new password form with strength meter

### A-3e: Role-Based Navigation

**File to modify**: `frontend/src/app/layout.tsx`

After login, the app shell adapts to the user's role:

| Role | Visible Sections |
|------|-----------------|
| UNDERWRITER | Submissions workbench |
| SENIOR_UNDERWRITER | Submissions + config viewer (read-only) |
| ACTUARIAL | Submissions + config + recalibration |
| ADMIN | All sections including `/admin` |
| READ_ONLY | Submissions (read-only), portfolio viewer |

Navigation items are permission-gated using `authStore.hasPermission()`.

### A-3f: Session Management

**New file**: `frontend/src/components/auth/SessionGuard.tsx`

- Wraps the app. Redirects to login if not authenticated.
- Session timeout warning (toast 5 min before expiry)
- Automatic logout on expiry
- Token refresh on activity

### A-3g: WebSocket Integration

**New file**: `frontend/src/lib/websocket.ts`

```typescript
class DSIWebSocket {
  connect(token: string): void;
  onEvent(handler: (event: WSEvent) => void): void;
  disconnect(): void;
}
```

**New file**: `frontend/src/components/shared/NotificationToast.tsx`

- Toast notifications when another user makes a relevant change
- Auto-refresh data when WebSocket event indicates current view's resource changed

**File to modify**: `frontend/src/stores/dsiStore.ts` -- Subscribe to WebSocket events, invalidate/refresh data on change.

### A-3h: User Profile

**New file**: `frontend/src/app/profile/page.tsx`

- View own profile, change password, manage MFA, view own audit log

---

## Constraints

1. Login page must render without any authenticated API calls
2. SSO flow must handle redirect back correctly across browser sessions
3. MFA backup codes shown exactly once, then never retrievable
4. No client-side storage of passwords or MFA secrets

## Success Criteria

1. Login flow works for username/password and SSO
2. MFA enrollment and verification works end-to-end
3. Navigation adapts correctly to user role
4. Session timeout and re-authentication work gracefully
5. WebSocket notifications display when another user changes shared data
6. Password reset flow works end-to-end
