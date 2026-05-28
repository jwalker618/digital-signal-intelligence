import type { ReactNode } from "react";
import { PersonaSidebar, SIDEBAR_NAV } from "@/components/chrome/persona-sidebar";

/**
 * Wraps a top-level carrier page in the persona sidebar + main column.
 * The Submission Workbench uses WorkbenchShell instead — see
 * /carrier/submissions/[code]/layout.tsx.
 */
export function CarrierShell({ children }: { children: ReactNode }) {
  return (
    <>
      <PersonaSidebar nav={SIDEBAR_NAV.carrier} />
      <main className="flex h-full flex-1 flex-col overflow-hidden bg-canvas">
        {children}
      </main>
    </>
  );
}
