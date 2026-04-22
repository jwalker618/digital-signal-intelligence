// A-3g: Notification toast host.
//
// Renders a stack of transient toasts in the top-right. Drops into the
// app shell once; any code can raise toasts via `pushNotification()`.
// The hub also auto-subscribes to the WebSocket: server-side audit
// events turn into notifications when they concern another user.

"use client";

import { useEffect, useState, useCallback } from "react";
import { X } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { getDsiWebSocket, type WSEvent } from "@/lib/websocket";

export interface Notification {
  id: string;
  title: string;
  body?: string;
  tone: "info" | "warn" | "error";
  createdAt: number;
}

type Subscriber = (n: Notification) => void;
const subscribers = new Set<Subscriber>();
let idCounter = 0;

export function pushNotification(n: Omit<Notification, "id" | "createdAt">) {
  const full: Notification = {
    id: `n-${Date.now()}-${idCounter++}`,
    createdAt: Date.now(),
    ...n,
  };
  for (const s of subscribers) s(full);
}

function eventToNotification(
  evt: WSEvent,
  currentUserId: string | null,
): Notification | null {
  const actorId =
    (evt.actor_id as string | undefined) ??
    (evt.user_id as string | undefined) ??
    null;
  if (actorId && currentUserId && actorId === currentUserId) return null;
  const action = (evt.action_type as string | undefined) ?? evt.type;
  if (!action) return null;
  const resource = (evt.resource_type as string | undefined) ?? "resource";
  const who = actorId ? `another user` : "the system";
  return {
    id: `n-${Date.now()}-${idCounter++}`,
    title: `${action.replace(/_/g, " ")}`,
    body: `${who} updated a ${resource}`,
    tone: "info",
    createdAt: Date.now(),
  };
}

export function NotificationToastHost() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const userId = useAuthStore((s) => s.user?.user_id ?? null);
  const [items, setItems] = useState<Notification[]>([]);

  // Subscribe to manual pushes
  useEffect(() => {
    const sub: Subscriber = (n) => {
      setItems((prev) => [...prev, n]);
      setTimeout(
        () => setItems((prev) => prev.filter((x) => x.id !== n.id)),
        6_000,
      );
    };
    subscribers.add(sub);
    return () => {
      subscribers.delete(sub);
    };
  }, []);

  // Connect the shared WebSocket to the toast feed
  useEffect(() => {
    if (!accessToken) return;
    const ws = getDsiWebSocket();
    ws.connect(accessToken);
    const off = ws.onEvent((evt) => {
      const n = eventToNotification(evt, userId);
      if (n) {
        for (const s of subscribers) s(n);
      }
    });
    return () => {
      off();
    };
  }, [accessToken, userId]);

  const dismiss = useCallback((id: string) => {
    setItems((prev) => prev.filter((x) => x.id !== id));
  }, []);

  if (items.length === 0) return null;

  return (
    <div className="fixed top-2 right-2 z-50 flex flex-col gap-2 max-w-sm">
      {items.map((n) => (
        <div
          key={n.id}
          role="status"
          className={`border-2 rounded p-3 shadow text-sm bg-dsi-background
            ${n.tone === "error" ? "border-dsi-negative" : ""}
            ${n.tone === "warn" ? "border-dsi-refer" : ""}
            ${n.tone === "info" ? "border-dsi-outline" : ""}`}
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="font-semibold">{n.title}</div>
              {n.body && <div className="opacity-80 text-xs mt-1">{n.body}</div>}
            </div>
            <button
              onClick={() => dismiss(n.id)}
              className="opacity-60 hover:opacity-100"
              aria-label="Dismiss notification"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
