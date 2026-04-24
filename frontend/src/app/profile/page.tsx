// A-3h: User profile page.

"use client";

import { useState, FormEvent } from "react";
import { ShieldUser, UserRound, KeyRound, Bell, } from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import { 
  CardGrid, 
  StandardCard 
} from "@/components/base/cards";

import "@/app/globals.css";

import { useAuthStore } from "@/store/authStore";
import { MFASetup } from "@/components/auth/MFASetup";
import { NotificationPreferences } from "@/components/profile/NotificationPreferences";
import { passwordResetRequest } from "@/lib/authApi";

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const [resetSent, setResetSent] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!user) {
    return <main className="generate-user-message">Loading profile…</main>;
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
    <ViewCanvas unstyledMain={true}>
      <div className="w-full no-scrollbar animate-in fade-in duration-500 pb-generate-pad"></div>
      
      <CardGrid cols="grid-cols-[4fr_1fr]">

        <StandardCard
          title="Account"
          lucideIcon={UserRound}
          spanClass="row-span-3"
          >

          <dl className="grid grid-cols-[8rem_1fr] gap-y-1 text-sm">
            
            <dt className="generate-analysis-description">Email</dt>
            <dd className="generate-analysis-item">{user.email ?? "—"}</dd>
            
            <dt className="generate-analysis-description">User ID</dt>
            <dd className="generate-analysis-item">{user.user_id}</dd>
            
            <dt className="generate-analysis-description">Tenant</dt>
            <dd className="generate-analysis-item">{user.tenant_id}</dd>
            
            <dt className="generate-analysis-description">Role</dt>
            <dd className="generate-analysis-item">{user.role ?? "—"}</dd>
            
            <dt className="
              flex
              generate-analysis-description 
              items-start 
              ">Permissions</dt>
            <dd className="flex flex-wrap gap-1">
              {user.permissions.map((p) => (
                <span
                  key={p}
                  className="
                    generate-analysis-item 
                    font-normal text-xs p-1.5
                    border-r border-b border-generate-outline 
                    rounded-sm"
                >
                  {p}
                </span>
              ))}
            </dd>

          </dl>
        
        </StandardCard>

        <StandardCard
          title="Two-factor authentication"
          lucideIcon={ShieldUser}
        >
          {user.mfa_enabled ? (
            <p className="text-sm">
              MFA is enabled on your account.
            </p>
          ) : (
            <MFASetup />
          )}
        </StandardCard>

        <StandardCard
          title="Password"
          lucideIcon={KeyRound}
        >
            {resetSent ? (
              <p className="text-xs pb-2">
                A reset link has been sent to <strong>{user.email}</strong>.
              </p>
            ) : (
              
              <form onSubmit={requestReset} className="flex flex-col">
                
                <p className="text-xs pb-2">
                  Change your password by sending yourself a reset link.
                </p>

                <button
                  type="submit"
                  disabled={busy}
                  className="generate-actionbutton"
                  >{busy ? "Sending…" : "Send Reset Link"}
                </button>

              </form>

            )}

        </StandardCard>

        <StandardCard
          title="Notifications"
          lucideIcon={Bell}
        >
          <NotificationPreferences />

        </StandardCard>

      </CardGrid>
    </ViewCanvas>
  );
}
