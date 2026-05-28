"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  KeyRound,
  Loader2,
  Lock,
  Search,
  ShieldCheck,
  UserPlus,
  X,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import { Eyebrow, NumDisplay, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { api } from "@/lib/api";
import { formatDate, formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { RoleRow, UserRow } from "@/types/admin";

export default function AdminUsersPage() {
  return (
    <PermissionGate
      permission="admin:users"
      fallback={<PageError message="You don't have admin:users permission." />}
    >
      <UsersInner />
    </PermissionGate>
  );
}

interface UsersBundle {
  users: UserRow[];
  roles: RoleRow[];
}

function UsersInner() {
  const [data, setData] = useState<UsersBundle | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);
  const [acting, setActing] = useState<string | null>(null);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [query, setQuery] = useState("");

  async function load() {
    setState("loading");
    try {
      const [users, roles] = await Promise.all([
        api.get<{ users: UserRow[] }>("/api/v1/admin/users"),
        api.get<{ roles: RoleRow[] }>("/api/v1/admin/roles"),
      ]);
      setData({ users: users.users ?? [], roles: roles.roles ?? [] });
      setState("ok");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function deactivate(userId: string) {
    setActing(userId);
    try {
      await api.post(`/api/v1/admin/users/${userId}/deactivate`);
      await load();
    } finally {
      setActing(null);
    }
  }

  const filtered = useMemo(() => {
    if (!data) return [] as UserRow[];
    if (!query) return data.users;
    const q = query.toLowerCase();
    return data.users.filter(
      (u) =>
        u.email.toLowerCase().includes(q) ||
        (u.full_name ?? "").toLowerCase().includes(q) ||
        (u.role_name ?? "").toLowerCase().includes(q),
    );
  }, [data, query]);

  if (state === "loading") return <PageLoading message="Loading users…" />;
  if (state === "error") return <PageError message={err ?? "Unknown error"} />;
  if (!data) return <PageLoading />;

  const active = data.users.filter((u) => u.is_active && !u.is_locked).length;
  const locked = data.users.filter((u) => u.is_locked).length;
  const mfa = data.users.filter((u) => u.mfa_enabled).length;

  return (
    <>
      <Topbar crumbs={["Admin", "Users & Roles"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Identity</Eyebrow>
              <h1 className="mt-1 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Users & Roles
              </h1>
              <Body className="mt-2">
                {data.users.length} user{data.users.length === 1 ? "" : "s"} ·{" "}
                {data.roles.length} role{data.roles.length === 1 ? "" : "s"}
              </Body>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 rounded-btn border border-rule-strong bg-surface px-3">
                <Search size={15} className="text-ink-mute" />
                <input
                  type="search"
                  placeholder="Name, email, or role…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="h-10 w-64 border-0 bg-transparent text-[13.5px] text-ink placeholder:text-ink-mute focus:outline-none"
                />
              </div>
              <Button onClick={() => setInviteOpen(true)}>
                <UserPlus size={14} />
                Invite
              </Button>
            </div>
          </header>

          <div className="grid gap-4 sm:grid-cols-3">
            <Stat label="Active" tone="pos">
              {active}
            </Stat>
            <Stat label="Locked" tone={locked > 0 ? "neg" : undefined}>
              {locked}
            </Stat>
            <Stat label="MFA enabled" tone="info" emphasis>
              {mfa} / {data.users.length}
            </Stat>
          </div>

          {/* Users table */}
          <Card pad="md" className="overflow-hidden p-0">
            <header className="flex items-center justify-between border-b border-rule px-5 py-3.5">
              <Eyebrow>Users</Eyebrow>
              <Micro>{filtered.length} shown</Micro>
            </header>
            <table className="w-full table-fixed text-[13px]">
              <thead>
                <tr className="border-b border-rule bg-surface-sunken text-left">
                  <ColHead width="w-[30%]">User</ColHead>
                  <ColHead width="w-[16%]">Role</ColHead>
                  <ColHead width="w-[14%]">Status</ColHead>
                  <ColHead width="w-[12%]">MFA</ColHead>
                  <ColHead width="w-[16%]">Last login</ColHead>
                  <ColHead width="w-[12%]">Actions</ColHead>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u) => (
                  <UserRowView
                    key={u.id}
                    user={u}
                    isActing={acting === u.id}
                    onDeactivate={() => deactivate(u.id)}
                  />
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="px-5 py-8 text-center">
                <Body className="italic">No users match "{query}".</Body>
              </div>
            )}
          </Card>

          {/* Roles */}
          <section>
            <Eyebrow className="mb-3">Roles ({data.roles.length})</Eyebrow>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {data.roles.map((r) => (
                <RoleCard key={r.id} role={r} />
              ))}
            </div>
          </section>
        </div>
      </div>

      {inviteOpen && (
        <InviteModal
          roles={data.roles}
          onClose={() => setInviteOpen(false)}
          onSent={() => {
            setInviteOpen(false);
            void load();
          }}
        />
      )}
    </>
  );
}

function UserRowView({
  user,
  isActing,
  onDeactivate,
}: {
  user: UserRow;
  isActing: boolean;
  onDeactivate: () => void;
}) {
  const initials =
    (user.full_name ?? user.email)
      .split(/[@.\s_-]/)
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0] ?? "")
      .join("")
      .toUpperCase() || "??";
  return (
    <tr className="border-b border-rule last:border-0 hover:bg-surface-sunken/40">
      <td className="px-5 py-3">
        <div className="flex items-center gap-3">
          <Avatar initials={initials} size="sm" />
          <div className="min-w-0">
            <p className="truncate font-medium text-ink">
              {user.full_name ?? user.email}
            </p>
            {user.full_name && (
              <Micro className="block truncate">{user.email}</Micro>
            )}
          </div>
        </div>
      </td>
      <td className="px-5 py-3 text-ink-soft">{user.role_name ?? "—"}</td>
      <td className="px-5 py-3">
        {user.is_locked ? (
          <Chip variant="neg" size="sm">
            <Lock size={10} />
            Locked
          </Chip>
        ) : user.is_active ? (
          <Chip variant="pos" size="sm">
            Active
          </Chip>
        ) : (
          <Chip variant="mute" size="sm">
            Inactive
          </Chip>
        )}
      </td>
      <td className="px-5 py-3">
        {user.mfa_enabled ? (
          <span className="inline-flex items-center gap-1 text-[12.5px] text-pos">
            <ShieldCheck size={12} /> on
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-[12.5px] text-ink-mute">
            off
          </span>
        )}
      </td>
      <td className="px-5 py-3 text-ink-soft">
        {fmtRelative(user.last_login)}
      </td>
      <td className="px-5 py-3">
        {user.is_active && !user.is_locked && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={isActing}
            onClick={onDeactivate}
          >
            {isActing ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Lock size={12} />
            )}
            Deactivate
          </Button>
        )}
      </td>
    </tr>
  );
}

function RoleCard({ role }: { role: RoleRow }) {
  return (
    <Card pad="md" className="space-y-3">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-[15px] font-semibold text-ink">{role.name}</h3>
          {role.description && (
            <Micro className="mt-0.5 block">{role.description}</Micro>
          )}
        </div>
        {role.is_system && (
          <Chip variant="info" size="sm">
            System
          </Chip>
        )}
      </header>
      <div className="flex items-baseline justify-between text-[12.5px]">
        <span className="text-ink-soft">Users</span>
        <span className="font-semibold tabular-nums text-ink">
          {role.user_count}
        </span>
      </div>
      {role.permissions.length > 0 && (
        <div className="space-y-1.5">
          <Micro>Permissions ({role.permissions.length})</Micro>
          <div className="flex flex-wrap gap-1">
            {role.permissions.slice(0, 6).map((p) => (
              <Chip key={p} variant="mute" size="sm">
                {p}
              </Chip>
            ))}
            {role.permissions.length > 6 && (
              <Chip variant="mute" size="sm">
                +{role.permissions.length - 6}
              </Chip>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}

function InviteModal({
  roles,
  onClose,
  onSent,
}: {
  roles: RoleRow[];
  onClose: () => void;
  onSent: () => void;
}) {
  const [email, setEmail] = useState("");
  const [roleId, setRoleId] = useState(roles[0]?.id ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/api/v1/admin/users/invite", { email, role_id: roleId });
      setSuccess(true);
      setTimeout(onSent, 900);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't send invite.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div onClick={(e) => e.stopPropagation()} className="w-full max-w-md">
        <Card pad="lg" className="space-y-4">
          <header className="flex items-start justify-between gap-3">
            <div>
              <Eyebrow>Invite</Eyebrow>
              <h2 className="mt-1 font-display text-[20px] font-semibold text-ink">
                Invite a teammate
              </h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-md text-ink-mute hover:bg-surface-sunken"
              aria-label="Close"
            >
              <X size={16} />
            </button>
          </header>
          {success ? (
            <div className="flex items-center gap-3 rounded-card border border-pos bg-pos-soft px-4 py-3 text-pos">
              <CheckCircle2 size={18} />
              <span className="text-[13.5px] font-medium">Invitation sent.</span>
            </div>
          ) : (
            <form className="space-y-4" onSubmit={onSubmit}>
              <Field id="invite-email" label="Email">
                <input
                  id="invite-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block h-11 w-full rounded-btn border border-rule-strong bg-surface px-3 text-[14px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
                />
              </Field>
              <Field id="invite-role" label="Role">
                <select
                  id="invite-role"
                  value={roleId}
                  onChange={(e) => setRoleId(e.target.value)}
                  className="block h-11 w-full rounded-btn border border-rule-strong bg-surface px-3 text-[14px] text-ink focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30"
                >
                  {roles.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </Field>
              {error && (
                <div className="rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg">
                  {error}
                </div>
              )}
              <div className="flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={onClose}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      Sending…
                    </>
                  ) : (
                    <>
                      <KeyRound size={14} />
                      Send invite
                    </>
                  )}
                </Button>
              </div>
            </form>
          )}
        </Card>
      </div>
    </div>
  );
}

function Field({
  id,
  label,
  children,
}: {
  id: string;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1.5 block text-[12.5px] font-medium text-ink-soft"
      >
        {label}
      </label>
      {children}
    </div>
  );
}

function Stat({
  label,
  tone,
  emphasis,
  children,
}: {
  label: string;
  tone?: "pos" | "neg" | "info";
  emphasis?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Card pad="md" variant={emphasis ? "info" : "default"}>
      <Micro
        className={cn(
          tone === "pos" && "text-pos",
          tone === "neg" && "text-neg",
          tone === "info" && emphasis && "text-info-deep dark:text-info",
        )}
      >
        {label}
      </Micro>
      <div className="mt-2">
        <NumDisplay size={emphasis ? "lg" : "md"}>{children}</NumDisplay>
      </div>
    </Card>
  );
}

function ColHead({
  width,
  children,
}: {
  width: string;
  children: React.ReactNode;
}) {
  return (
    <th
      className={`px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute ${width}`}
    >
      {children}
    </th>
  );
}
