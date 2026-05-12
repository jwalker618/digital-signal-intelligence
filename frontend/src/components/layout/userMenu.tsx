"use client";

/**
 * UserMenu — popover anchored to the user icon in the sidebar bottom bar.
 * Shows the signed-in user, role, and Profile / Sign-out actions.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CircleUserRound, LogOut } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { SidebarIconBtn } from "./nav";

export default function UserMenu() {
  const router = useRouter();
  const authUser = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);
  const clearSubmissionContext = useDsiStore((s) => s.clearSubmissionContext);
  const [isOpen, setIsOpen] = useState(false);

  const closeAnd = (fn: () => void | Promise<void>) => async () => {
    setIsOpen(false);
    await fn();
  };

  return (
    <div className="flex items-center gap-6">
      <SidebarIconBtn
        icon={CircleUserRound}
        onClick={() => setIsOpen((v) => !v)}
      />

      {isOpen && (
        <div className="
          absolute bottom-[5vw] left-0 z-40
          flex flex-col 
          min-w-[10rem] 
          p-1.5 gap-1.5 mb-generate-pad
          bg-generate-dark-input 
          text-generate-text-placeholder text-sm
          border-t-1 border-b-1 border-generate-text-outline 
          rounded-md"
          >
          <div className="group">
            <button
              onClick={closeAnd(() => {
                clearSubmissionContext();
                setActiveMenu("Your Profile");
                router.push("/profile");
              })}
              className="flex gap-generate-pad items-center  group-hover:text-generate-text-input"
            >
              <CircleUserRound className="generate-app-icon group-hover:text-generate-text-input" /> Profile
            </button>
          </div>
            
            <div className="group">
              <button
                onClick={closeAnd(async () => {
                  await logout();
                  router.replace("/login");
                })}
                className="flex gap-generate-pad items-center group-hover:text-generate-text-input"
              >
                <LogOut className="generate-app-icon group-hover:text-generate-text-input" /> 
                <span>Sign out</span>
              </button>
            </div>
        </div>
      )}
    </div>
  );
}
