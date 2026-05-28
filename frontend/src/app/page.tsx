"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

/**
 * Root entry. Dispatches the user to the right persona surface (or to
 * /login if not authenticated). Real auth gating lives in SessionGuard;
 * this is just the initial routing hint.
 */
export default function RootPage() {
  const router = useRouter();
  useEffect(() => {
    const state = useAuthStore.getState();
    if (!state.isAuthenticated()) {
      router.replace("/login");
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
