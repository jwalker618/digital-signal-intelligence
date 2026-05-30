import type { AuthUser } from "@/types/auth";

export interface UserDisplay {
  initials: string;
  name: string;
  email: string;
  roleLabel: string;
  tenantLabel: string;
}

/**
 * Derive a human-friendly identity from the auth user. We only persist
 * email server-side, so the display name + initials are inferred from the
 * email local-part (e.g. `sasha.alvarez@marsh.com` → "Sasha Alvarez" / "SA").
 *
 * Single home for this so the profile page, the persona sidebar account
 * block, and anywhere else that surfaces the signed-in user agree.
 */
export function deriveUserDisplay(user: AuthUser): UserDisplay {
  const email = user.email ?? "—";
  const local = user.email?.split("@")[0] ?? "";
  const parts = local.split(/[._-]/).filter(Boolean);
  const name = parts.length
    ? parts
        .slice(0, 2)
        .map((p) => p[0].toUpperCase() + p.slice(1))
        .join(" ")
    : email;
  const initials =
    (parts
      .map((p) => p[0] ?? "")
      .join("")
      .slice(0, 2)
      .toUpperCase() ||
      user.email?.slice(0, 2).toUpperCase()) ??
    "—";
  const roleLabel = user.role
    ? user.role
        .replace(/_/g, " ")
        .toLowerCase()
        .replace(/\b\w/g, (c) => c.toUpperCase())
    : "";
  return { initials, name, email, roleLabel, tenantLabel: user.tenant_id };
}
