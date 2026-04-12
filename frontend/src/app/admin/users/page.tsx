// FE: Users & Roles dashboard (B-3).
//
// Two-panel layout: left = users, right = roles. Invite + deactivate
// flows inline. Read-only role permission preview.

"use client";

import { FormEvent, useEffect, useState } from "react";
import { AlertTriangle, Mail, RefreshCw, UserPlus, UserX } from "lucide-react";

import { api, fmtDate } from "@/lib/api";
import { StatusBadge } from "@/components/shared/StatusBadge";
import type { RoleRow, UserRow } from "@/types/admin";

export default function UsersPage() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  // Invite form
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
    <main className="p-6 flex flex-col gap-4">
      <header className="flex items-center gap-3">
        <h1 className="font-inter text-2xl tracking-wide">Users &amp; Roles</h1>
        <button
          onClick={() => void load()}
          disabled={loading}
          className="ml-auto flex items-center gap-1 border-2 border-dsi-outline py-1 px-3 rounded text-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </header>

      {error && (
        <div className="border-2 border-red-500 rounded p-3 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400" /> {error}
        </div>
      )}

      <section className="border-2 border-dsi-outline rounded p-4">
        <h2 className="font-semibold tracking-wider mb-2 flex items-center gap-2">
          <UserPlus className="w-4 h-4" /> Invite user
        </h2>
        <form onSubmit={invite} className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1">
            <span className="text-xs opacity-60">Email</span>
            <input
              type="email"
              required
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              className="border-2 border-dsi-outline bg-dsi-background px-3 py-1 rounded text-sm"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs opacity-60">Role</span>
            <select
              value={inviteRoleId}
              onChange={(e) => setInviteRoleId(e.target.value)}
              className="border-2 border-dsi-outline bg-dsi-background px-2 py-1 rounded text-sm"
            >
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </label>
          <button
            type="submit"
            disabled={busy === "invite"}
            className="bg-dsi-contrast-background text-dsi-background py-1 px-3 rounded text-sm font-semibold flex items-center gap-1 disabled:opacity-50"
          >
            <Mail className="w-4 h-4" />
            Send invite
          </button>
          {inviteResult && (
            <span className="text-xs opacity-80">{inviteResult}</span>
          )}
        </form>
      </section>

      <section className="border-2 border-dsi-outline rounded">
        <h2 className="font-semibold tracking-wider p-3">Users</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs uppercase opacity-60 text-left">
              <th className="py-1 px-3">Email</th>
              <th className="py-1 px-3">Name</th>
              <th className="py-1 px-3">Role</th>
              <th className="py-1 px-3">MFA</th>
              <th className="py-1 px-3">Status</th>
              <th className="py-1 px-3">Last login</th>
              <th className="py-1 px-3"></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t border-dsi-outline/20">
                <td className="py-1 px-3 font-mono text-xs">{u.email}</td>
                <td className="py-1 px-3">{u.full_name ?? "—"}</td>
                <td className="py-1 px-3">{u.role_name ?? "—"}</td>
                <td className="py-1 px-3 text-xs">
                  {u.mfa_enabled ? "on" : "off"}
                </td>
                <td className="py-1 px-3">
                  <StatusBadge
                    status={
                      u.is_locked
                        ? "locked"
                        : u.is_active
                          ? "active"
                          : "inactive"
                    }
                  />
                </td>
                <td className="py-1 px-3 text-xs opacity-80">
                  {fmtDate(u.last_login)}
                </td>
                <td className="py-1 px-3">
                  {u.is_active && (
                    <button
                      onClick={() => void deactivate(u.id)}
                      disabled={busy === `deact:${u.id}`}
                      className="text-xs text-red-400 hover:underline flex items-center gap-1"
                    >
                      <UserX className="w-3 h-3" /> Deactivate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="border-2 border-dsi-outline rounded">
        <h2 className="font-semibold tracking-wider p-3">Roles</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs uppercase opacity-60 text-left">
              <th className="py-1 px-3">Name</th>
              <th className="py-1 px-3">Description</th>
              <th className="py-1 px-3">Users</th>
              <th className="py-1 px-3">Permissions</th>
            </tr>
          </thead>
          <tbody>
            {roles.map((r) => (
              <tr key={r.id} className="border-t border-dsi-outline/20">
                <td className="py-1 px-3 font-semibold">{r.name}</td>
                <td className="py-1 px-3 opacity-80">{r.description ?? "—"}</td>
                <td className="py-1 px-3 tabular-nums">{r.user_count}</td>
                <td className="py-1 px-3">
                  <div className="flex flex-wrap gap-1">
                    {r.permissions.map((p) => (
                      <span
                        key={p}
                        className="text-[10px] font-mono border border-dsi-outline/30 rounded px-1"
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
      </section>
    </main>
  );
}
