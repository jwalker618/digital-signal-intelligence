# Phase A-3: Auth Frontend & Login Experience

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | A-1, A-2 |

---

## Overview

The complete authentication UI: login screen, MFA flow, role-based navigation, session management, user profile, real-time notification integration, and PWA installability. This phase is the single modification point for `layout.tsx` and `next.config.ts` -- all frontend shell changes land here.

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
- Built with a modular section layout so A-4 (Push Notifications) can add a notification preferences section without restructuring

### A-3i: PWA -- Installability & Asset Caching

Convert the frontend into an installable Progressive Web App with service worker asset caching. This is scoped to installability and static asset caching only -- no offline data access, no push notifications (those are A-4).

**Package**: Add `@ducanh2912/next-pwa` (maintained fork of `next-pwa`, wraps Workbox)

**File to modify**: `frontend/next.config.ts`

```typescript
import withPWA from "@ducanh2912/next-pwa";

const nextConfig: NextConfig = {
  // ... existing config
};

export default withPWA({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
  runtimeCaching: [
    // Static assets: cache-first (JS, CSS, fonts, images)
    {
      urlPattern: /\/_next\/static\/.*/i,
      handler: "CacheFirst",
      options: { cacheName: "static-assets", expiration: { maxEntries: 200, maxAgeSeconds: 30 * 24 * 60 * 60 } },
    },
    // API calls: network-first (never serve stale data)
    {
      urlPattern: /\/api\/v1\/.*/i,
      handler: "NetworkFirst",
      options: { cacheName: "api-responses", expiration: { maxEntries: 50, maxAgeSeconds: 5 * 60 }, networkTimeoutSeconds: 10 },
    },
    // Fonts: cache-first
    {
      urlPattern: /\.(?:woff|woff2|ttf|otf)$/i,
      handler: "CacheFirst",
      options: { cacheName: "fonts", expiration: { maxEntries: 20, maxAgeSeconds: 365 * 24 * 60 * 60 } },
    },
  ],
})(nextConfig);
```

**New file**: `frontend/public/manifest.json`

```json
{
  "name": "Digital Signal Intelligence",
  "short_name": "DSI",
  "description": "Insurance intelligence platform",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#000000",
  "theme_color": "#000000",
  "orientation": "landscape-primary",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

**New directory**: `frontend/public/icons/` -- Generate from DSI logo: 192x192, 512x512, maskable variants.

**File to modify**: `frontend/src/app/layout.tsx` (same pass as A-3e)

Add to `<head>`:
```html
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#000000" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black" />
<link rel="apple-touch-icon" href="/icons/icon-192.png" />
```

**Caching strategy rationale**:
- Static assets (JS/CSS/fonts): cache-first. These are content-hashed by Next.js, so cache invalidation is automatic on deploy.
- API responses: network-first with 10s timeout fallback. DSI is a live-data app; stale API data is worse than a loading spinner. The cache only serves as a timeout fallback, not a primary source.
- No offline page needed. If the network is down, the app shell loads (cached) and API calls show appropriate error states.

---

## Constraints

1. Login page must render without any authenticated API calls
2. SSO flow must handle redirect back correctly across browser sessions
3. MFA backup codes shown exactly once, then never retrievable
4. No client-side storage of passwords or MFA secrets
5. Service worker must not cache authenticated API responses across users -- cache keyed to session
6. PWA `display: standalone` -- no browser chrome in installed mode

## Success Criteria

1. Login flow works for username/password and SSO
2. MFA enrollment and verification works end-to-end
3. Navigation adapts correctly to user role
4. Session timeout and re-authentication work gracefully
5. WebSocket notifications display when another user changes shared data
6. Password reset flow works end-to-end
7. App is installable from Chrome/Edge/Safari "Install" prompt
8. Subsequent loads serve app shell from service worker cache (instant paint)
9. API calls always hit network first (no stale data served)
