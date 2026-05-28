import { ReactNode } from "react";
import { SessionGuard } from "@/components/auth/SessionGuard";

/**
 * Authenticated app shell. Wraps every page in (app) with SessionGuard so
 * unauthenticated visitors are bounced to /login, role-vs-persona URL
 * mismatches self-correct, and token refresh runs in the background.
 */
export default function AppGroupLayout({ children }: { children: ReactNode }) {
  return (
    <SessionGuard>
      <div className="flex h-screen w-screen overflow-hidden">{children}</div>
    </SessionGuard>
  );
}
