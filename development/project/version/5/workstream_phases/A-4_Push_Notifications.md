# Phase A-4: Push Notifications

| Item | Value |
|------|-------|
| Version | 1.0 |
| Depends on | A-1 (user model), A-2 (WebSocket + audit events), A-3 (profile page, PWA service worker) |

---

## Overview

Extends the real-time sync infrastructure (A-2 WebSocket) with push notifications that reach users when DSI is not in the foreground. When the app is open, events arrive via WebSocket. When it is closed or backgrounded, the same events trigger push notifications via the service worker installed in A-3. Users control which notification categories they receive.

## Current State (after A-2 and A-3)

- A-2 provides `ConnectionManager` for WebSocket broadcasting within tenant
- A-2 provides `AuditService` that records events and broadcasts via WebSocket
- A-3 installs a service worker via `next-pwa` (for asset caching)
- A-3 creates the profile page with modular section layout
- No push notification infrastructure. No subscription management. No notification preferences.

## Target State

- Backend push service that routes events to Web Push API when user is offline
- User-configurable notification preferences (which event types, per-channel)
- Service worker push event handler (extends A-3's PWA service worker)
- Notification preferences section on the profile page

---

## Implementation Plan

### A-4a: Push Subscription Schema

**Migration**: `alembic/versions/018_push_notifications.py`

| Table | Key Columns |
|-------|-------------|
| `push_subscriptions` | `id` (UUID), `user_id` FK, `tenant_id` FK, `endpoint` (TEXT -- Web Push endpoint URL), `p256dh_key` (TEXT), `auth_key` (TEXT), `user_agent`, `created_at`, `last_used_at` |
| `notification_preferences` | `id`, `user_id` FK, `tenant_id` FK, `category` (enum), `push_enabled` (bool), `in_app_enabled` (bool), `email_enabled` (bool -- future) |

**Indexes**: `push_subscriptions` on (`user_id`). `notification_preferences` on (`user_id`, `category`) unique.

### A-4b: Notification Categories

**New file**: `infrastructure/api/push/categories.py`

```python
class NotificationCategory(str, Enum):
    REFERRAL_PENDING = "referral_pending"           # Referral awaiting your decision
    REFERRAL_DECIDED = "referral_decided"            # Referral you submitted was decided
    ASSESSMENT_COMPLETE = "assessment_complete"       # Assessment finished processing
    CONFIG_DEPLOYED = "config_deployed"               # Config version deployed
    RECALIBRATION_PROPOSED = "recalibration_proposed" # New recalibration proposal
    RECALIBRATION_DECIDED = "recalibration_decided"   # Proposal you reviewed was decided
    DRIFT_ALERT = "drift_alert"                       # World Engine drift alert (CRITICAL only)
    CONCENTRATION_ALERT = "concentration_alert"       # Portfolio concentration alert

# Default preferences: all enabled for push + in-app
DEFAULT_PREFERENCES = {cat: {"push": True, "in_app": True} for cat in NotificationCategory}
```

### A-4c: Push Service

**New file**: `infrastructure/api/push/service.py`

```python
class PushService:
    """Routes events to push notifications for offline users."""

    def __init__(self, vapid_private_key: str, vapid_claims: dict):
        """Uses pywebpush for Web Push API compliance."""

    def should_push(self, user_id: str, category: NotificationCategory) -> bool:
        """
        Push if:
        1. User has an active push subscription
        2. User's preference for this category has push_enabled=True
        3. User does NOT have an active WebSocket connection (avoid duplicate)
        """

    def send(self, user_id: str, category: NotificationCategory,
             title: str, body: str, url: str | None = None) -> bool:
        """
        Send push notification via Web Push API (pywebpush).
        Returns True if delivered, False if subscription expired.
        Cleans up expired subscriptions automatically.
        """

    def notify_event(self, event: AuditEvent) -> None:
        """
        Maps an AuditEvent to a NotificationCategory.
        Determines which users should receive the notification.
        For each: check should_push(), if yes send().
        Called by AuditMiddleware after recording the event.
        """
```

**Package**: `pywebpush` for VAPID-authenticated Web Push.

**VAPID keys**: Generated once, stored as environment variables (`VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_CLAIMS_EMAIL`). Not in code or config files.

### A-4d: Push API Routes

**New file**: `infrastructure/api/push/routes.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/push/vapid-public-key` | GET | Returns VAPID public key for client subscription |
| `/push/subscribe` | POST | Register push subscription (endpoint + keys) |
| `/push/unsubscribe` | POST | Remove push subscription |
| `/push/preferences` | GET | Get user's notification preferences |
| `/push/preferences` | PUT | Update notification preferences |
| `/push/test` | POST | Send a test notification to self (development/verification) |

**File to modify**: `infrastructure/api/main.py` -- Mount push router at `/api/v1/push/`.

### A-4e: Audit Middleware Extension

**File to modify**: `infrastructure/api/audit/middleware.py`

After recording an audit event and broadcasting via WebSocket, also call `PushService.notify_event()`:

```python
# In AuditMiddleware, after WebSocket broadcast:
push_service.notify_event(audit_event)
```

This is the single integration point. The push service internally determines who should receive pushes and whether they're online (skip if WebSocket connected).

### A-4f: Service Worker Push Handler

**New file**: `frontend/public/custom-sw.js`

```javascript
// Extends the next-pwa generated service worker
// next-pwa supports custom worker via the customWorkerSrc option

self.addEventListener('push', (event) => {
  const data = event.data?.json() ?? {};
  event.waitUntil(
    self.registration.showNotification(data.title || 'DSI', {
      body: data.body,
      icon: '/icons/icon-192.png',
      badge: '/icons/icon-badge-72.png',
      data: { url: data.url },
      tag: data.category,        // Collapse same-category notifications
      renotify: true,
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(clients.openWindow(url));
});
```

**File to modify**: `frontend/next.config.ts` -- Add `customWorkerSrc: "custom-sw.js"` to the PWA config (already configured in A-3i).

### A-4g: Frontend -- Subscription & Preferences

**New file**: `frontend/src/lib/push.ts`

```typescript
export class PushManager {
  async requestPermission(): Promise<boolean> { /* Notification.requestPermission() */ }
  async subscribe(vapidPublicKey: string): Promise<PushSubscription> { /* registration.pushManager.subscribe() */ }
  async unsubscribe(): Promise<void> { ... }
  async syncSubscription(): Promise<void> { /* POST /push/subscribe with subscription keys */ }
}
```

**New file**: `frontend/src/components/profile/NotificationPreferences.tsx`

- Toggle grid: rows = notification categories, columns = push / in-app
- "Enable push notifications" button (triggers browser permission prompt + subscription)
- "Send test notification" button
- Unsubscribe option

**File to modify**: `frontend/src/app/profile/page.tsx` -- Add `<NotificationPreferences />` section. This is the only file touched by both A-3 and A-4; A-3 creates it with modular layout, A-4 adds a section.

---

## Constraints

1. Push notifications must not duplicate WebSocket in-app notifications -- check connection state before sending
2. VAPID keys are environment variables, never committed to source
3. Expired/invalid subscriptions cleaned up automatically on failed delivery
4. User must explicitly opt-in via browser permission prompt -- no auto-subscribe
5. Push payload must not contain sensitive data (no signal scores, no premiums) -- only category, title, and a link
6. Critical drift alerts (`DriftSeverity.CRITICAL`) bypass per-category preferences -- always delivered if push is enabled at all

## Success Criteria

1. Users can enable push notifications from profile page
2. When DSI is backgrounded, push notifications arrive for enabled categories
3. Clicking a push notification opens DSI at the relevant resource
4. Users with active WebSocket connection do NOT receive duplicate pushes
5. Notification preferences are respected per-category
6. Test notification delivers successfully
7. Expired subscriptions are cleaned up without errors
