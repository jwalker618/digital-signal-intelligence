import type { ReactNode } from "react";
import { PersonaSidebar } from "@/components/chrome/persona-sidebar";

/**
 * Admin console shell. Sidebar uses ADMIN_CHILDREN (which each carry a
 * permission); leaf pages render PermissionGate / SessionGuard already
 * handles the broader auth check.
 */
export default function AdminShell({ children }: { children: ReactNode }) {
  return (
    <>
      <PersonaSidebar persona="admin" />
      <main className="flex h-full flex-1 flex-col overflow-hidden bg-canvas">
        {children}
      </main>
    </>
  );
}
