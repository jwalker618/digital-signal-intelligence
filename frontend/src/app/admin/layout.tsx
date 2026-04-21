// FE: Admin shell layout.
//
// Navigation into /admin/* now lives in the main sidebar's Admin group
// (see navConfig ADMIN_CHILDREN + components/layout/sidebar.tsx). This
// layout only has to guard direct/deep-link access: if the user has no
// admin permissions at all, show a friendly fallback.

"use client";

import { ShieldCheck } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { ADMIN_CHILDREN } from "@/components/layout/navConfig";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const anyAccess = ADMIN_CHILDREN.some((n) => hasPermission(n.permission));

  if (!anyAccess) {
    return (
      <main className="p-6">
        <div className="border-2 border-dsi-outline rounded p-4 text-sm opacity-80">
          <ShieldCheck className="icon inline mr-2" />
          You do not have access to any admin section.
        </div>
      </main>
    );
  }

  return <>{children}</>;
}
