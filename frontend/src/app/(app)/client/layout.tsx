import type { ReactNode } from "react";
import { PersonaSidebar, SIDEBAR_NAV } from "@/components/chrome/persona-sidebar";

/**
 * Client persona shell. Owns the sidebar; each leaf page owns its own
 * topbar (so per-page actions and the entity badge can flow from data).
 */
export default function ClientShell({ children }: { children: ReactNode }) {
  return (
    <>
      <PersonaSidebar nav={SIDEBAR_NAV.client} />
      <main className="flex h-full flex-1 flex-col overflow-hidden bg-canvas">
        {children}
      </main>
    </>
  );
}
