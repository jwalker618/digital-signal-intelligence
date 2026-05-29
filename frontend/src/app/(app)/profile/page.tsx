"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Bell,
  Building2,
  Calendar,
  KeyRound,
  LogOut,
  Mail,
  ShieldCheck,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Body, Caption } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { BackButton } from "@/components/ui/back-button";
import { PageLoading } from "@/components/base/pageStates";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import type { AuthUser } from "@/types/auth";

const VISIBLE_PERMS = 14;

export default function ProfilePage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  if (!user) return <PageLoading />;

  const display = deriveDisplay(user);

  async function onSignOut() {
    await logout();
    router.replace("/login");
  }

  const shownPerms = user.permissions.slice(0, VISIBLE_PERMS);
  const remaining = Math.max(0, user.permissions.length - VISIBLE_PERMS);

  return (
    <div className="flex h-full flex-1 flex-col overflow-hidden">
      <Topbar crumbs={["Account", "Your Profile"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-5xl gap-4">
          <BackButton />

          <Card pad="lg" className="flex items-center gap-[18px]">
            <div className="flex h-[72px] w-[72px] shrink-0 items-center justify-center rounded-full bg-ink text-[28px] font-semibold text-canvas">
              {display.initials}
            </div>
            <div className="min-w-0 flex-1">
              <Eyebrow>Your account</Eyebrow>
              <h2 className="mt-1 font-display text-[24px] font-semibold leading-tight text-ink">
                {display.name}
              </h2>
              <Caption className="mt-1 block">
                {user.email ?? "—"}
                {display.roleLabel ? ` · ${display.roleLabel}` : ""}
              </Caption>
              <div className="mt-3 flex flex-wrap gap-2">
                <Chip>
                  <Building2 size={11} />
                  {display.tenantLabel}
                </Chip>
                <Chip variant={user.mfa_enabled ? "pos" : "warn"}>
                  <ShieldCheck size={11} />
                  {user.mfa_enabled ? "MFA enabled" : "MFA off"}
                </Chip>
                <Chip>
                  <Calendar size={11} />
                  Active session
                </Chip>
              </div>
            </div>
            <Button variant="ghost" onClick={onSignOut}>
              <LogOut size={14} />
              Sign out
            </Button>
          </Card>

          <div className="grid gap-4 lg:grid-cols-[1fr_1.2fr]">
            <Card pad="lg">
              <Eyebrow>Identity</Eyebrow>
              <h3 className="mt-1.5 mb-3.5 font-display text-[17px] font-semibold leading-[1.2] text-ink">
                Registered details
              </h3>
              <div className="flex flex-col">
                <DetailRow label="Full name" value={display.name} />
                <DetailRow label="Email" value={user.email ?? "—"} />
                <DetailRow label="User ID" value={user.user_id} mono />
                <DetailRow label="Tenant" value={user.tenant_id} mono />
                <DetailRow label="Role" value={user.role ?? "—"} mono />
                <DetailRow label="MFA" value={user.mfa_enabled ? "Enabled" : "Disabled"} last />
              </div>
            </Card>

            <Card pad="lg">
              <div className="flex items-baseline justify-between">
                <div>
                  <Eyebrow>Permissions</Eyebrow>
                  <h3 className="mt-1.5 font-display text-[17px] font-semibold leading-[1.2] text-ink">
                    What you can do
                  </h3>
                </div>
                <Chip>{user.permissions.length} permissions</Chip>
              </div>
              {user.permissions.length === 0 ? (
                <Body className="mt-3.5 italic">No permissions assigned.</Body>
              ) : (
                <div className="mt-3.5 flex flex-wrap gap-1.5">
                  {shownPerms.map((p) => (
                    <span
                      key={p}
                      className="inline-flex items-center rounded-chip bg-surface-sunken px-[9px] py-1 font-mono text-[10.5px] text-ink-soft"
                    >
                      {p}
                    </span>
                  ))}
                  {remaining > 0 && (
                    <span className="inline-flex items-center rounded-chip bg-surface-sunken px-2 py-1 text-[11px] text-ink-soft">
                      + {remaining} more
                    </span>
                  )}
                </div>
              )}
              <div className="mt-4 border-t border-rule pt-3.5">
                <Caption>
                  Granted via the{" "}
                  <strong className="text-ink">{user.role ?? "—"}</strong>{" "}
                  role. To change, contact your admin.
                </Caption>
              </div>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card
              pad="lg"
              variant={user.mfa_enabled ? "pos" : "warn"}
            >
              <div className="mb-3 flex items-center gap-2.5">
                <span
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-lg",
                    user.mfa_enabled
                      ? "bg-pos-soft text-pos"
                      : "bg-warn-soft text-warn",
                  )}
                >
                  <ShieldCheck size={18} />
                </span>
                <Eyebrow
                  className={user.mfa_enabled ? "text-pos" : "text-warn"}
                >
                  Two-factor authentication
                </Eyebrow>
              </div>
              <div
                className={cn(
                  "font-display text-[20px] font-semibold leading-none",
                  user.mfa_enabled ? "text-pos" : "text-warn",
                )}
              >
                {user.mfa_enabled ? "Enabled" : "Off"}
              </div>
              <Caption className="mt-1.5 block leading-[1.5]">
                {user.mfa_enabled
                  ? "MFA is active on this account. You'll be prompted for a code each time you sign in."
                  : "Add a second factor to significantly reduce account compromise risk."}
              </Caption>
              <Link
                href="/login/mfa"
                className="mt-3.5 inline-flex h-10 w-full items-center justify-center gap-2 rounded-btn border border-rule-strong bg-transparent text-[13px] font-semibold text-ink hover:bg-surface-sunken"
              >
                Manage devices
              </Link>
            </Card>

            <Card pad="lg">
              <div className="mb-3 flex items-center gap-2.5">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-rule bg-surface-elev text-ink">
                  <KeyRound size={18} />
                </span>
                <Eyebrow>Password</Eyebrow>
              </div>
              <div className="font-display text-[20px] font-semibold leading-none text-ink">
                Last changed
              </div>
              <Caption className="mt-1.5 block leading-[1.5]">
                Send yourself a one-time reset link if you need to update
                your password.
              </Caption>
              <Link
                href="/login/reset-password"
                className="mt-3.5 inline-flex h-10 w-full items-center justify-center gap-2 rounded-btn bg-ink text-[13px] font-semibold text-canvas hover:opacity-90"
              >
                <Mail size={13} />
                Send reset link
              </Link>
            </Card>

            <Card pad="lg">
              <div className="mb-3 flex items-center gap-2.5">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-rule bg-surface-elev text-ink">
                  <Bell size={18} />
                </span>
                <Eyebrow>Notifications</Eyebrow>
              </div>
              <Body className="leading-[1.5]">
                Per-channel email and push notification preferences will
                live here.
              </Body>
              <Caption className="mt-2 block italic">Coming soon.</Caption>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

interface Display {
  initials: string;
  name: string;
  roleLabel: string;
  tenantLabel: string;
}

function deriveDisplay(user: AuthUser): Display {
  const local = user.email?.split("@")[0] ?? "";
  const parts = local.split(/[._-]/).filter(Boolean);
  const name = parts.length
    ? parts
        .slice(0, 2)
        .map((p) => p[0].toUpperCase() + p.slice(1))
        .join(" ")
    : (user.email ?? "—");
  const initials =
    (parts.map((p) => p[0] ?? "").join("").slice(0, 2).toUpperCase() ||
      user.email?.slice(0, 2).toUpperCase()) ?? "—";
  const roleLabel = user.role
    ? user.role.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())
    : "";
  const tenantLabel = user.tenant_id;
  return { initials, name, roleLabel, tenantLabel };
}

function DetailRow({
  label,
  value,
  mono,
  last,
}: {
  label: string;
  value: string;
  mono?: boolean;
  last?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex items-baseline justify-between py-2",
        !last && "border-b border-rule",
      )}
    >
      <span className="text-[11px] text-ink-mute">{label}</span>
      <span
        className={cn(
          "text-[13px] font-semibold text-ink",
          mono && "font-mono",
        )}
      >
        {value}
      </span>
    </div>
  );
}
