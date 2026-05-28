import { ReactNode } from "react";
import { AuthBrandPanel } from "@/components/chrome/auth-brand-panel";

/**
 * Pre-auth route group. Split-screen: brand panel on the left, form on the
 * right. The form column is scrollable so longer flows (e.g. MFA setup
 * with backup codes) stay reachable.
 */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <AuthBrandPanel />
      <div className="flex flex-1 items-center justify-center overflow-y-auto bg-canvas p-10">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
