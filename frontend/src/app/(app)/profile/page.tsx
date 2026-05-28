"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut, ShieldCheck, KeyRound, Bell } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import { PageLoading } from "@/components/base/pageStates";
import { useAuthStore } from "@/store/authStore";

/**
 * Account / "Your Profile" surface. Shows identity, permissions, MFA
 * status, and lets the user start MFA setup or sign out.
 */
export default function ProfilePage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  if (!user) return <PageLoading />;

  const initials =
    (user.email?.split("@")[0]?.split(/[._-]/)
      .map((p) => p[0] ?? "")
      .join("")
      .slice(0, 2)
      .toUpperCase() ||
      user.email?.slice(0, 2).toUpperCase()) ?? "—";

  async function onSignOut() {
    await logout();
    router.replace("/login");
  }

  return (
    <div className="flex h-full flex-1 flex-col overflow-hidden">
      <Topbar crumbs={["Account", "Your Profile"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-3xl gap-6">
          <Card pad="lg" className="flex items-center gap-5">
            <Avatar initials={initials} size="lg" />
            <div className="flex-1">
              <Eyebrow>Signed in</Eyebrow>
              <p className="mt-1 text-[20px] font-semibold leading-tight text-ink">
                {user.email ?? "—"}
              </p>
              <Body className="mt-1">
                Role:{" "}
                <span className="font-semibold text-ink">
                  {user.role?.toLowerCase() ?? "—"}
                </span>{" "}
                · Tenant{" "}
                <span className="font-mono text-[12px] text-ink-soft">
                  {user.tenant_id}
                </span>
              </Body>
            </div>
            <Button variant="ghost" onClick={onSignOut}>
              <LogOut size={15} />
              Sign out
            </Button>
          </Card>

          <Card pad="lg" className="space-y-4">
            <header className="flex items-center justify-between">
              <div>
                <Eyebrow>Security</Eyebrow>
                <h2 className="mt-1 font-display text-[20px] font-semibold text-ink">
                  Two-factor authentication
                </h2>
              </div>
              <Chip variant={user.mfa_enabled ? "pos" : "warn"}>
                <ShieldCheck size={12} />
                {user.mfa_enabled ? "Enabled" : "Off"}
              </Chip>
            </header>
            <Body>
              {user.mfa_enabled
                ? "MFA is active on this account. You'll be prompted for a code each time you sign in."
                : "Add a second factor — significantly reduces account compromise from password reuse."}
            </Body>
            <div className="flex gap-3">
              <Link
                href="/login/mfa"
                className="inline-flex items-center gap-1.5 text-[13px] font-medium text-info hover:underline"
              >
                <KeyRound size={14} /> Manage MFA
              </Link>
            </div>
          </Card>

          <Card pad="lg" className="space-y-4">
            <header>
              <Eyebrow>Permissions</Eyebrow>
              <h2 className="mt-1 font-display text-[20px] font-semibold text-ink">
                What you can access
              </h2>
            </header>
            {user.permissions.length === 0 ? (
              <Body className="italic">No permissions assigned.</Body>
            ) : (
              <ul className="flex flex-wrap gap-2">
                {user.permissions.map((p) => (
                  <li key={p}>
                    <Chip variant="mute" size="sm">
                      {p}
                    </Chip>
                  </li>
                ))}
              </ul>
            )}
            <Micro>Contact your administrator if you need additional scopes.</Micro>
          </Card>

          <Card pad="lg" className="space-y-3">
            <header className="flex items-center gap-2">
              <Bell size={16} className="text-ink-soft" />
              <Eyebrow>Notifications</Eyebrow>
            </header>
            <Body>
              Per-channel email and push notification preferences will live
              here. Coming soon.
            </Body>
          </Card>
        </div>
      </div>
    </div>
  );
}
