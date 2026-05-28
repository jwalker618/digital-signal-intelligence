import type { ReactNode } from "react";
import { PersonaSidebar } from "@/components/chrome/persona-sidebar";

/**
 * Client persona shell. Owns the sidebar; each leaf page owns its own
 * topbar (so per-page actions and the entity badge can flow from data).
 */
export default function ClientShell({ children }: { children: ReactNode }) {
  return (
    <>
      <PersonaSidebar persona="client" />
      <main className="flex h-full flex-1 flex-col overflow-hidden bg-canvas">
        {children}
      </main>
    </>
  );
}
