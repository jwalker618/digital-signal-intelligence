// FE: Admin shell layout.
//
// Provides the sub-navigation shared by every /admin/* page.
// Permission-gated links -- hidden entirely when the user lacks
// the backing permission.

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  FileStack,
  Users,
  ShieldCheck,
  History,
  FileX,
  TrendingUpDown,
} from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { PermissionGate } from "@/components/shared/PermissionGate";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  permission: string;
}

const NAV: NavItem[] = [
  { href: "/admin", label: "System Health", icon: Activity, permission: "admin:system" },
  { href: "/admin/configs", label: "Configs", icon: FileStack, permission: "config:read" },
  { href: "/admin/users", label: "Users & Roles", icon: Users, permission: "admin:users" },
  { href: "/admin/audit", label: "Audit Log", icon: History, permission: "admin:audit" },
  { href: "/admin/losses", label: "Loss Register", icon: FileX, permission: "assessment:write" },
  { href: "/admin/recalibration", label: "Recalibration", icon: TrendingUpDown, permission: "recalibration:view" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const anyAccess = NAV.some((n) => hasPermission(n.permission));

  if (!anyAccess) {
    return (
      <main className="p-6">
        <div className="border-2 border-dsi-outline rounded p-4 text-sm opacity-80">
          <ShieldCheck className="icon inline mr-2" />
          You do not have access to any admin section.
        </div>
      </main>
    );
  }

  return (
    <div className="flex h-full">
      <aside className="w-56 border-r-2 border-dsi-outline p-3 overflow-y-auto shrink-0">
        <h2 className="text-xs uppercase tracking-widest opacity-60 mb-2 px-2">
          Admin
        </h2>
        <nav className="flex flex-col gap-0.5">
          {NAV.map((item) => (
            <PermissionGate key={item.href} permission={item.permission}>
              <Link
                href={item.href}
                className={`flex items-center gap-2 px-2 py-1.5 rounded text-sm ${
                  pathname === item.href || pathname?.startsWith(item.href + "/")
                    ? "bg-dsi-outline/20 text-dsi-selected font-semibold"
                    : "hover:bg-dsi-outline/10"
                }`}
              >
                <item.icon className="w-4 h-4 shrink-0" />
                <span className="truncate">{item.label}</span>
              </Link>
            </PermissionGate>
          ))}
        </nav>
      </aside>
      <div className="flex-1 overflow-y-auto">{children}</div>
    </div>
  );
}
