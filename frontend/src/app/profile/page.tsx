// A-3h: User profile page.

"use client";

import { useState, FormEvent } from "react";
import { ShieldCheck, UserRound, KeyRound, LogOut, Bell } from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import { CardGrid, StandardCard } from "@/components/base/cards";

import { useAuthStore } from "@/store/authStore";
import { MFASetup } from "@/components/auth/MFASetup";
import { NotificationPreferences } from "@/components/profile/NotificationPreferences";
import { passwordResetRequest } from "@/lib/authApi";

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [resetSent, setResetSent] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!user) {
    return <main className="p-6 opacity-70">Loading profile…</main>;
  }

  async function requestReset(e: FormEvent) {
    e.preventDefault();
    if (!user?.email) return;
    setBusy(true);
    try {
      await passwordResetRequest(user.email);
      setResetSent(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <ViewCanvas>
      <CardGrid>
        <StandardCard title="Account" lucideIcon={UserRound}>
          <dl className="grid grid-cols-[8rem_1fr] gap-y-1 text-sm">
            <dt className="opacity-60">Email</dt>
            <dd>{user.email ?? "—"}</dd>
            <dt className="opacity-60">User ID</dt>
            <dd className="font-mono text-xs">{user.user_id}</dd>
            <dt className="opacity-60">Tenant</dt>
            <dd className="font-mono text-xs">{user.tenant_id}</dd>
            <dt className="opacity-60">Role</dt>
            <dd>{user.role ?? "—"}</dd>
            <dt className="opacity-60">Permissions</dt>
            <dd className="flex flex-wrap gap-1">
              {user.permissions.map((p) => (
                <span
                  key={p}
                  className="font-mono text-xs px-2 py-0.5 border border-dsi-outline/40 rounded"
                >
                  {p}
                </span>
              ))}
            </dd>
          </dl>
        </StandardCard>

        <StandardCard title="Two-factor authentication" lucideIcon={ShieldCheck}>
          {user.mfa_enabled ? (
            <p className="text-sm text-dsi-selected">
              MFA is enabled on your account.
            </p>
          ) : (
            <MFASetup />
          )}
        </StandardCard>

        <StandardCard title="Password" lucideIcon={KeyRound}>
          {resetSent ? (
            <p className="text-sm">
              A reset link has been sent to <strong>{user.email}</strong>.
            </p>
          ) : (
            <form onSubmit={requestReset}>
              <p className="text-sm opacity-80 mb-2">
                Change your password by sending yourself a reset link.
              </p>
              <button
                type="submit"
                disabled={busy}
                className="dsi-actionbutton"
              >
                {busy ? "Sending…" : "Send reset link"}
              </button>
            </form>
          )}
        </StandardCard>

        <StandardCard title="Notifications" lucideIcon={Bell}>
          <NotificationPreferences />
        </StandardCard>

        <StandardCard title="Session" lucideIcon={LogOut}>
          <button onClick={() => logout()} className="dsi-actionbutton">
            Sign out
          </button>
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}
