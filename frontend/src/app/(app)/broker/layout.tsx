import type { ReactNode } from "react";
import { PersonaSidebar, SIDEBAR_NAV } from "@/components/chrome/persona-sidebar";

/**
 * Broker persona shell. Sidebar uses PORTAL_BROKER_CHILDREN; each leaf
 * page owns its own topbar so per-page actions can flow from data.
 */
export default function BrokerShell({ children }: { children: ReactNode }) {
  return (
    <>
      <PersonaSidebar nav={SIDEBAR_NAV.broker} />
      <main className="flex h-full flex-1 flex-col overflow-hidden bg-canvas">
        {children}
      </main>
    </>
  );
}
