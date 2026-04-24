// FE: Users & Roles dashboard (B-3).
//
// Two stacked sections: users (with invite form) and roles. Invite +
// deactivate flows inline; role panel is read-only.

"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  AlertTriangle,
  Mail,
  RefreshCw,
  ShieldCheck,
  UserPlus,
  UserX,
  Users as UsersIcon,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import { CardGrid, StandardCard } from "@/components/base/cards";
import { api, fmtDate } from "@/lib/api";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { useDsiStore } from "@/store/dsiStore";
import type { RoleRow, UserRow } from "@/types/admin";

export default function UsersPage() {
  const setPageQuickAction = useDsiStore((s) => s.setPageQuickAction);

  const [users, setUsers] = useState<UserRow[]>([]);
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRoleId, setInviteRoleId] = useState<string>("");
  const [inviteResult, setInviteResult] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [u, r] = await Promise.all([
        api.get<{ users: UserRow[] }>("/api/v1/admin/users"),
        api.get<{ roles: RoleRow[] }>("/api/v1/admin/roles"),
      ]);
      setUsers(u.users ?? []);
      setRoles(r.roles ?? []);
      if (!inviteRoleId && r.roles?.length) setInviteRoleId(r.roles[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    setPageQuickAction(
      <button
        onClick={() => void load()}
        disabled={loading}
        className="generate-actiontext disabled:opacity-50"
      >
        <RefreshCw className={`icon ${loading ? "animate-spin" : ""}`} />
        Refresh
      </button>,
    );
    return () => setPageQuickAction(null);
  }, [loading, setPageQuickAction]);

  async function invite(e: FormEvent) {
    e.preventDefault();
    setBusy("invite");
    setInviteResult(null);
    setError(null);
    try {
      const resp = await api.post<{ invitation_id: string; token?: string }>(
        "/api/v1/admin/users/invite",
        { email: inviteEmail.toLowerCase(), role_id: inviteRoleId },
      );
      setInviteResult(
        resp.token
          ? `Invite ${resp.invitation_id.slice(0, 8)}… created (dev token: ${resp.token.slice(0, 12)}…)`
          : `Invite ${resp.invitation_id.slice(0, 8)}… created`,
      );
      setInviteEmail("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invite failed");
    } finally {
      setBusy(null);
    }
  }

  async function deactivate(userId: string) {
    setBusy(`deact:${userId}`);
    setError(null);
    try {
      await api.post(`/api/v1/admin/users/${userId}/deactivate`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deactivate failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <ViewCanvas unstyledMain={true}>
      <div className="w-full h-full overflow-y-auto no-scrollbar bg-generate-background text-generate-contrast-background p-generate-pad animate-in fade-in duration-500 pb-12">

        {error && (
          <div className="generate-notificationpill mb-generate-pad flex items-center gap-2">
            <AlertTriangle className="icon" /> {error}
          </div>
        )}

        <CardGrid cols="grid-cols-1">

          <StandardCard title="Invite user" lucideIcon={UserPlus}>
            <form onSubmit={invite} className="flex flex-wrap items-end gap-2">
              <label className="flex flex-col gap-1">
                <span className="text-xs opacity-60">Email</span>
                <input
                  type="email"
                  required
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="generate-inputbox"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-xs opacity-60">Role</span>
                <select
                  value={inviteRoleId}
                  onChange={(e) => setInviteRoleId(e.target.value)}
                  className="generate-inputbox"
                >
                  {roles.map((r) => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
              </label>
              <button
                type="submit"
                disabled={busy === "invite"}
                className="generate-actionbutton flex items-center gap-1"
              >
                <Mail className="icon" />
                Send invite
              </button>
              {inviteResult && (
                <span className="text-xs opacity-80">{inviteResult}</span>
              )}
            </form>
          </StandardCard>

          <StandardCard title="Users" lucideIcon={UsersIcon}>
            <table className="w-full text-left whitespace-nowrap border-collapse">
              <thead>
                <tr className="generate-grid-table-header text-generate-contrast-background">
                  <th className="p-1.5">Email</th>
                  <th className="p-1.5">Name</th>
                  <th className="p-1.5">Role</th>
                  <th className="p-1.5">MFA</th>
                  <th className="p-1.5">Status</th>
                  <th className="p-1.5">Last login</th>
                  <th className="p-1.5"></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="even:bg-generate-contrast-analysis text-generate-contrast-background">
                    <td className="p-1.5 font-mono text-xs">{u.email}</td>
                    <td className="p-1.5">{u.full_name ?? "—"}</td>
                    <td className="p-1.5">{u.role_name ?? "—"}</td>
                    <td className="p-1.5 text-xs">{u.mfa_enabled ? "on" : "off"}</td>
                    <td className="p-1.5">
                      <StatusBadge
                        status={u.is_locked ? "locked" : u.is_active ? "active" : "inactive"}
                      />
                    </td>
                    <td className="p-1.5 text-xs opacity-80">{fmtDate(u.last_login)}</td>
                    <td className="p-1.5">
                      {u.is_active && (
                        <button
                          onClick={() => void deactivate(u.id)}
                          disabled={busy === `deact:${u.id}`}
                          className="text-xs text-generate-decline hover:underline flex items-center gap-1 disabled:opacity-50"
                        >
                          <UserX className="w-3 h-3" /> Deactivate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {users.length === 0 && !loading && (
              <div className="generate-user-message">No users.</div>
            )}
          </StandardCard>

          <StandardCard title="Roles" lucideIcon={ShieldCheck}>
            <table className="w-full text-left whitespace-nowrap border-collapse">
              <thead>
                <tr className="generate-grid-table-header text-generate-contrast-background">
                  <th className="p-1.5">Name</th>
                  <th className="p-1.5">Description</th>
                  <th className="p-1.5 text-right">Users</th>
                  <th className="p-1.5">Permissions</th>
                </tr>
              </thead>
              <tbody>
                {roles.map((r) => (
                  <tr key={r.id} className="even:bg-generate-contrast-analysis text-generate-contrast-background">
                    <td className="p-1.5 font-semibold">{r.name}</td>
                    <td className="p-1.5 opacity-80">{r.description ?? "—"}</td>
                    <td className="p-1.5 text-right tabular-nums">{r.user_count}</td>
                    <td className="p-1.5">
                      <div className="flex flex-wrap gap-1">
                        {r.permissions.map((p) => (
                          <span
                            key={p}
                            className="text-[10px] font-mono border border-generate-outline/30 rounded px-1"
                          >
                            {p}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {roles.length === 0 && !loading && (
              <div className="generate-user-message">No roles.</div>
            )}
          </StandardCard>

        </CardGrid>
      </div>
    </ViewCanvas>
  );
}
