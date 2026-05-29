"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

/**
 * Root entry. Dispatches the user to the right persona surface (or to
 * /login if not authenticated). Real auth gating lives in SessionGuard;
 * this is just the initial routing hint.
 *
 * On phone-sized viewports the user is routed to the dedicated mobile
 * companion at /m, unless they've opted into the desktop view via the
 * `prefersDesktop` flag.
 */
export default function RootPage() {
  const router = useRouter();
  useEffect(() => {
    const state = useAuthStore.getState();
    if (!state.isAuthenticated()) {
      router.replace("/login");
      return;
    }
    if (shouldUseMobile()) {
      router.replace("/m");
      return;
    }
    const role = state.user?.role;
    if (role === "BROKER") router.replace("/broker");
    else if (role === "CLIENT") router.replace("/client");
    else router.replace("/profile");
  }, [router]);

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-canvas text-ink-mute">
      <span className="text-sm">Loading…</span>
    </div>
  );
}

function shouldUseMobile(): boolean {
  if (typeof window === "undefined") return false;
  if (window.localStorage.getItem("dsi-prefers-desktop") === "1") return false;
  const sp = new URLSearchParams(window.location.search);
  if (sp.get("desktop") === "1") {
    window.localStorage.setItem("dsi-prefers-desktop", "1");
    return false;
  }
  return window.matchMedia("(max-width: 640px), (pointer: coarse)").matches;
}
