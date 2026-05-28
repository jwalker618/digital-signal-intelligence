"use client";

// / -- role-aware redirect.
//
// The root URL has no UI of its own. Once the user is authenticated,
// SessionGuard routes them to their persona home (/carrier, /broker,
// /client) via homePathForRole. This page is a thin fallback that
// runs the same redirect from the client side so a bookmark of / or
// a direct navigation here always lands somewhere sensible.

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { homePathForRole } from "@/lib/portalPaths";

export default function RootPage() {
  const router = useRouter();
  const isAuthed = useAuthStore((s) => s.isAuthenticated());
  const userRole = useAuthStore((s) => s.user?.role ?? null);

  useEffect(() => {
    if (isAuthed && userRole) {
      router.replace(homePathForRole(userRole));
    }
  }, [isAuthed, userRole, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-generate-light-background">
      <Loader2 className="icon animate-spin" />
    </div>
  );
}
