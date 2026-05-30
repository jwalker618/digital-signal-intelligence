import { ReactNode } from "react";
import { SessionGuard } from "@/components/auth/SessionGuard";
import { MobileRedirect } from "@/components/auth/MobileRedirect";

/**
 * Authenticated app shell. Wraps every page in (app) with SessionGuard so
 * unauthenticated visitors are bounced to /login, role-vs-persona URL
 * mismatches self-correct, and token refresh runs in the background.
 * MobileRedirect bounces phone-viewport users to /m unless they've
 * opted into the desktop layout.
 */
export default function AppGroupLayout({ children }: { children: ReactNode }) {
  return (
    <SessionGuard>
      <MobileRedirect />
      <div className="flex h-screen w-screen overflow-hidden">{children}</div>
    </SessionGuard>
  );
}
