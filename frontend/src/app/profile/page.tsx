// A-3h: User profile page.
//
// Modular section layout so A-4 (Push Notifications) can add a
// preferences section without restructuring.

"use client";

import { useState, FormEvent } from "react";
import { ShieldCheck, UserRound, KeyRound, LogOut, Bell } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { MFASetup } from "@/components/auth/MFASetup";
import { passwordResetRequest } from "@/lib/authApi";

function Section({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <section className="border-2 border-dsi-outline rounded p-4 flex flex-col gap-3">
      <header className="flex items-center gap-2 text-dsi-selected">
        <Icon className="icon" />
        <span className="font-semibold tracking-wider">{title}</span>
      </header>
      {children}
    </section>
  );
}

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [resetSent, setResetSent] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!user) {
    return (
      <main className="p-6 opacity-70">Loading profile…</main>
    );
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
    <main className="p-6 overflow-y-auto h-full">
      <h1 className="font-inter text-2xl tracking-wide mb-6">Your profile</h1>
      <div className="grid gap-4 max-w-3xl">
        <Section title="Account" icon={UserRound}>
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
        </Section>

        <Section title="Two-factor authentication" icon={ShieldCheck}>
          {user.mfa_enabled ? (
            <p className="text-sm text-dsi-selected">
              MFA is enabled on your account.
            </p>
          ) : (
            <MFASetup />
          )}
        </Section>

        <Section title="Password" icon={KeyRound}>
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
                className="bg-dsi-contrast-background text-dsi-background py-2 px-4 rounded font-semibold disabled:opacity-50"
              >
                {busy ? "Sending…" : "Send reset link"}
              </button>
            </form>
          )}
        </Section>

        {/* Placeholder slot so A-4 can drop a preferences section here
            without restructuring. */}
        <Section title="Notifications" icon={Bell}>
          <p className="text-sm opacity-70">
            Push notification preferences will appear here once enabled.
          </p>
        </Section>

        <Section title="Session" icon={LogOut}>
          <button
            onClick={() => logout()}
            className="self-start border-2 border-dsi-outline py-2 px-4 rounded hover:bg-dsi-outline/10"
          >
            Sign out
          </button>
        </Section>
      </div>
    </main>
  );
}
