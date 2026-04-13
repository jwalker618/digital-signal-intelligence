// FE: PermissionGate -- renders children only when the current user has
// the required permission. Optional `fallback` renders otherwise
// (default: nothing).

"use client";

import { ReactNode } from "react";

import { useAuthStore } from "@/store/authStore";

export function PermissionGate({
  permission,
  anyOf,
  fallback = null,
  children,
}: {
  permission?: string;
  anyOf?: string[];
  fallback?: ReactNode;
  children: ReactNode;
}) {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  let ok = true;
  if (permission) ok = hasPermission(permission);
  if (anyOf && anyOf.length > 0) {
    ok = ok && anyOf.some((p) => hasPermission(p));
  }
  if (!ok) return <>{fallback}</>;
  return <>{children}</>;
}
