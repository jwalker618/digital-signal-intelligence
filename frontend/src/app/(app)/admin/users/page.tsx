// No direct design counterpart; adapted from reim_admin_a.jsx
"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  KeyRound,
  Loader2,
  Search,
  ShieldCheck,
  UserPlus,
  UserX,
  Users as UsersIcon,
  X,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import {
  AdminTable,
  Avatar,
  Body,
  Button,
  Card,
  Chip,
  Eyebrow,
  Micro,
} from "@/components/ui";
import type { AdminTableCol, AdminTableRow } from "@/components/ui";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { api } from "@/lib/api";
import { fmtRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { RoleRow, UserRow } from "@/types/admin";

type UserFilter = "ALL" | "ACTIVE" | "LOCKED" | "INACTIVE";

const USER_FILTERS: { value: UserFilter; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "ACTIVE", label: "Active" },
  { value: "LOCKED", label: "Locked" },
  { value: "INACTIVE", label: "Inactive" },
];

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
  const [filter, setFilter] = useState<UserFilter>("ALL");

  async function load() {
    setState("loading");
    try {
      const [users, roles] = await Promise.all([
        api.get<UserRow[]>("/api/v1/admin/users"),
        api.get<RoleRow[]>("/api/v1/admin/roles"),
      ]);
      setData({ users: users ?? [], roles: roles ?? [] });
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
    let rows = data.users;
    if (filter === "ACTIVE")
      rows = rows.filter((u) => u.is_active && !u.is_locked);
    if (filter === "LOCKED") rows = rows.filter((u) => u.is_locked);
    if (filter === "INACTIVE") rows = rows.filter((u) => !u.is_active);
    if (query) {
      const q = query.toLowerCase();
      rows = rows.filter(
        (u) =>
          u.email.toLowerCase().includes(q) ||
          (u.full_name ?? "").toLowerCase().includes(q) ||
          (u.role_name ?? "").toLowerCase().includes(q),
      );
    }
    return rows;
  }, [data, filter, query]);

  if (state === "loading") return <PageLoading message="Loading users…" />;
  if (state === "error") return <PageError message={err ?? "Unknown error"} />;
  if (!data) return <PageLoading />;

  const userCols: AdminTableCol[] = [
    { key: "email", label: "Email", width: "2fr" },
    { key: "name", label: "Name", width: "1.4fr" },
    { key: "role", label: "Role", width: "1.4fr" },
    { key: "mfa", label: "MFA", align: "center", width: "70px" },
    { key: "status", label: "Status", width: "110px" },
    { key: "lastLogin", label: "Last login", width: "1fr" },
    { key: "actions", label: "", align: "right", width: "120px" },
  ];

  const userRows: AdminTableRow[] = filtered.map((u) => ({
    email: <code className="text-[12px] text-ink">{u.email}</code>,
    name: (
      <div className="flex items-center gap-2">
        <Avatar initials={initialsOf(u)} size="sm" />
        <span className="font-semibold text-ink">
          {u.full_name ?? u.email.split("@")[0]}
        </span>
      </div>
    ),
    role: (
      <code className="font-mono text-[12px] text-ink-soft">
        {u.role_name ?? "—"}
      </code>
    ),
    mfa: u.mfa_enabled ? (
      <span className="inline-flex items-center gap-1 text-[12px] text-pos">
        <ShieldCheck size={11} /> on
      </span>
    ) : (
      <span className="text-[12px] text-warn">off</span>
    ),
    status: <StatusChip user={u} />,
    lastLogin: <Micro>{fmtRelative(u.last_login)}</Micro>,
    actions:
      u.is_active && !u.is_locked ? (
        <button
          type="button"
          disabled={acting === u.id}
          onClick={() => deactivate(u.id)}
          className="inline-flex items-center gap-1.5 text-[12px] text-neg hover:underline disabled:opacity-50"
        >
          {acting === u.id ? (
            <Loader2 size={11} className="animate-spin" />
          ) : (
            <UserX size={11} />
          )}
          Deactivate
        </button>
      ) : (
        <Micro>—</Micro>
      ),
  }));

  const roleCols: AdminTableCol[] = [
    { key: "name", label: "Name", width: "1.6fr" },
    { key: "description", label: "Description", width: "2.5fr" },
    { key: "users", label: "Users", align: "right", width: "80px" },
    { key: "perms", label: "Permissions", align: "right", width: "120px" },
  ];

  const roleRows: AdminTableRow[] = data.roles.map((r) => ({
    name: (
      <span className="font-mono text-[12px] font-bold uppercase text-ink">
        {r.name}
      </span>
    ),
    description: (
      <span className="text-[12.5px] text-ink-soft">
        {r.description ?? "—"}
      </span>
    ),
    users: (
      <span className="tabular-nums font-semibold text-ink">
        {r.user_count}
      </span>
    ),
    perms: (
      <span className="tabular-nums text-ink-soft">
        {r.permissions.length} perms
      </span>
    ),
  }));

  return (
    <>
      <Topbar crumbs={["Admin", "Users & Roles"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1400px] gap-4">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Users & roles</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Identity + access
              </h1>
              <Body className="mt-1.5">
                {data.users.length} user
                {data.users.length === 1 ? "" : "s"} across {data.roles.length}{" "}
                role{data.roles.length === 1 ? "" : "s"}. Manage invitations +
                access from here.
              </Body>
            </div>
            <Button onClick={() => setInviteOpen(true)}>
              <UserPlus size={14} />
              Invite user
            </Button>
          </header>

          <Card
            pad="none"
            icon={UsersIcon}
            header={`Users · ${filtered.length}`}
            headerRight={
              <div className="flex items-center gap-2">
                <div className="flex h-8 items-center gap-2 rounded-btn border border-rule-strong bg-surface px-2.5">
                  <Search size={13} className="text-ink-mute" />
                  <input
                    type="search"
                    placeholder="Name, email, role…"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="w-44 border-0 bg-transparent text-[12.5px] text-ink placeholder:text-ink-mute focus:outline-none"
                  />
                </div>
                {USER_FILTERS.map((f) => (
                  <FilterChip
                    key={f.value}
                    active={filter === f.value}
                    onClick={() => setFilter(f.value)}
                  >
                    {f.label}
                  </FilterChip>
                ))}
              </div>
            }
          >
            <AdminTable cols={userCols} rows={userRows} />
            {filtered.length === 0 && (
              <div className="px-5 py-8 text-center">
                <Body className="italic">No users match the filters.</Body>
              </div>
            )}
          </Card>

          <Card
            pad="none"
            icon={ShieldCheck}
            header={`Roles · ${data.roles.length}`}
          >
            <AdminTable cols={roleCols} rows={roleRows} />
          </Card>
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

function StatusChip({ user }: { user: UserRow }) {
  if (user.is_locked)
    return (
      <Chip size="sm" variant="neg">
        Locked
      </Chip>
    );
  if (!user.is_active)
    return (
      <Chip size="sm" variant="spot">
        Inactive
      </Chip>
    );
  return (
    <Chip size="sm" variant="pos">
      Active
    </Chip>
  );
}

function initialsOf(user: UserRow): string {
  const src = user.full_name ?? user.email;
  return (
    src
      .split(/[@.\s_-]/)
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0] ?? "")
      .join("")
      .toUpperCase() || "??"
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-chip px-2.5 py-1 text-[11.5px] font-medium transition-colors",
        active
          ? "bg-ink text-canvas"
          : "bg-surface-sunken text-ink-soft hover:bg-surface-elev",
      )}
    >
      {children}
    </button>
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
