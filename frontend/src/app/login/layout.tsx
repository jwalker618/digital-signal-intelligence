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
      {/* Form column — top-aligned (form sits ~200px down), left-aligned,
          max 420 wide. Matches reim_auth.jsx AuthShell. */}
      <div className="flex flex-1 flex-col items-start overflow-y-auto bg-canvas px-10 pb-10 pt-[200px]">
        <div className="w-full max-w-[420px]">{children}</div>
      </div>
    </div>
  );
}
