import type { ReactNode } from "react";

/**
 * Carrier route group — passthrough. The persona sidebar is rendered by
 * individual pages via <CarrierShell>, and the Submission Workbench routes
 * (/carrier/submissions/[code]/*) substitute their own drill-down sidebar.
 */
export default function CarrierGroup({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
