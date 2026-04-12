// A-4g: Push subscription helper.
//
// Wraps the browser Notification + PushManager APIs and syncs state
// with the /api/v1/push/* backend. The auth store supplies the bearer
// token via authorizedFetch().

import { useAuthStore } from "@/store/authStore";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

async function req<T = unknown>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const fetcher = useAuthStore.getState().authorizedFetch;
  const res = await fetcher(apiUrl(path), {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  const parsed = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const msg =
      (parsed && (parsed.error || parsed.detail)) || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return parsed as T;
}

export interface CategoryPreference {
  push: boolean;
  in_app: boolean;
  email: boolean;
}

export type PreferencesMap = Record<string, CategoryPreference>;

// =============================================================================
// Helpers
// =============================================================================

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const base64Safe = (base64 + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64Safe);
  const output = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) output[i] = raw.charCodeAt(i);
  return output;
}

function arrayBufferToBase64(buffer: ArrayBuffer | null): string {
  if (!buffer) return "";
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

// =============================================================================
// PushManager
// =============================================================================

export class DSIPushManager {
  async isSupported(): Promise<boolean> {
    return (
      typeof window !== "undefined" &&
      "serviceWorker" in navigator &&
      "PushManager" in window &&
      "Notification" in window
    );
  }

  async requestPermission(): Promise<NotificationPermission> {
    if (typeof Notification === "undefined") return "denied";
    return Notification.requestPermission();
  }

  private async getRegistration(): Promise<ServiceWorkerRegistration | null> {
    if (!("serviceWorker" in navigator)) return null;
    return (await navigator.serviceWorker.getRegistration()) ?? null;
  }

  async getVapidKey(): Promise<string> {
    const resp = await req<{ public_key: string }>(
      "GET",
      "/api/v1/push/vapid-public-key",
    );
    return resp.public_key;
  }

  async subscribe(vapidPublicKey: string): Promise<PushSubscription | null> {
    const reg = await this.getRegistration();
    if (!reg) return null;
    const existing = await reg.pushManager.getSubscription();
    if (existing) return existing;
    return reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
    });
  }

  async unsubscribe(): Promise<void> {
    const reg = await this.getRegistration();
    const sub = reg ? await reg.pushManager.getSubscription() : null;
    if (!sub) return;
    const endpoint = sub.endpoint;
    try {
      await sub.unsubscribe();
    } finally {
      await req("POST", "/api/v1/push/unsubscribe", { endpoint });
    }
  }

  async syncSubscription(): Promise<void> {
    const permission = await this.requestPermission();
    if (permission !== "granted") {
      throw new Error("Notification permission not granted");
    }
    const vapid = await this.getVapidKey();
    if (!vapid) {
      throw new Error("Server has no VAPID public key configured");
    }
    const sub = await this.subscribe(vapid);
    if (!sub) throw new Error("Subscription failed");
    const json = sub.toJSON();
    await req("POST", "/api/v1/push/subscribe", {
      endpoint: json.endpoint,
      p256dh_key:
        json.keys?.p256dh ?? arrayBufferToBase64(sub.getKey("p256dh")),
      auth_key: json.keys?.auth ?? arrayBufferToBase64(sub.getKey("auth")),
      user_agent:
        typeof navigator !== "undefined" ? navigator.userAgent : undefined,
    });
  }

  async getPreferences(): Promise<PreferencesMap> {
    const resp = await req<{ preferences: PreferencesMap }>(
      "GET",
      "/api/v1/push/preferences",
    );
    return resp.preferences;
  }

  async setPreferences(
    updates: Record<string, Partial<CategoryPreference>>,
  ): Promise<PreferencesMap> {
    const resp = await req<{ preferences: PreferencesMap }>(
      "PUT",
      "/api/v1/push/preferences",
      { updates },
    );
    return resp.preferences;
  }

  async sendTest(): Promise<{ delivered: number }> {
    return req("POST", "/api/v1/push/test", {});
  }
}

let singleton: DSIPushManager | null = null;

export function getPushManager(): DSIPushManager {
  if (!singleton) singleton = new DSIPushManager();
  return singleton;
}
