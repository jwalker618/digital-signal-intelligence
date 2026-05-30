import type { ReactNode } from "react";
import { SessionGuard } from "@/components/auth/SessionGuard";
import "./mobile.css";

/**
 * Mobile companion shell. The mobile surface lives outside the (app)
 * layout group so it can render edge-to-edge without inheriting the
 * desktop chrome (sidebar + topbar). SessionGuard still gates entry.
 */
export default function MobileLayout({ children }: { children: ReactNode }) {
  return (
    <SessionGuard>
      <div className="h-screen w-screen overflow-hidden">{children}</div>
    </SessionGuard>
  );
}
