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
        <div className="
          absolute bottom-[5vw] left-0 z-40
          flex flex-col 
          min-w-[10rem] 
          bg-dsi-background 
          text-dsi-contrast-background 
          border-1 border-dsi-outline 
          rounded-md shadow-sm"
          >

          <button
            onClick={closeAnd(() => router.push("/profile"))}
            className="dsi-actiontext"
          >
            <CircleUserRound className="icon" /> Profile
          </button>

          <button
            onClick={closeAnd(async () => {
              await logout();
              router.replace("/login");
            })}
            className="dsi-actiontext"
          >
            <LogOut className="icon" /> Sign out
          </button>
        </div>
      )}
    </div>
  );
}
