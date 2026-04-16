"use client";

/**
 * UserMenu — popover anchored to the user icon in the sidebar bottom bar.
 * Shows the signed-in user, role, and Profile / Sign-out actions.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CircleUserRound, LogOut } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { SidebarIconBtn } from "./nav";

export default function UserMenu() {
  const router = useRouter();
  const authUser = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [isOpen, setIsOpen] = useState(false);

  const closeAnd = (fn: () => void | Promise<void>) => async () => {
    setIsOpen(false);
    await fn();
  };

  return (
    <div className="flex items-center gap-6 relative">
      <SidebarIconBtn
        icon={CircleUserRound}
        onClick={() => setIsOpen((v) => !v)}
      />

      {isOpen && (
        <div className="absolute bottom-10 left-0 z-40 min-w-[14rem] bg-dsi-background text-dsi-contrast-background border-2 border-dsi-outline rounded shadow-lg p-2 flex flex-col gap-1">
          <div className="px-2 py-1 text-xs opacity-70 truncate">
            {authUser?.email ?? "Not signed in"}
          </div>

          {authUser?.role && (
            <div className="px-2 py-0.5 text-xs opacity-60">
              {authUser.role}
            </div>
          )}

          <button
            onClick={closeAnd(() => router.push("/profile"))}
            className="text-left px-2 py-1 hover:bg-dsi-outline/10 rounded flex items-center gap-2 text-sm"
          >
            <CircleUserRound className="w-4 h-4" /> Profile
          </button>

          <button
            onClick={closeAnd(async () => {
              await logout();
              router.replace("/login");
            })}
            className="text-left px-2 py-1 hover:bg-dsi-outline/10 rounded flex items-center gap-2 text-sm"
          >
            <LogOut className="w-4 h-4" /> Sign out
          </button>
        </div>
      )}
    </div>
  );
}
