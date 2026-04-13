"use client";

// A-3e: Adapter that exposes the auth store via the legacy UserContext
// shape. Existing components that useUser() keep working unchanged --
// new code should read from useAuthStore directly.

import { createContext, useContext, ReactNode, useMemo } from "react";

import { useAuthStore } from "@/store/authStore";

interface UserProfile {
  user_id: string;
  display_name: string;
  role: string;
}

interface UserContextType {
  user: UserProfile;
}

const defaultUser: UserProfile = {
  user_id: "anon",
  display_name: "Anonymous",
  role: "READ_ONLY",
};

const UserContext = createContext<UserContextType>({ user: defaultUser });

export function UserProvider({ children }: { children: ReactNode }) {
  const authUser = useAuthStore((s) => s.user);

  const value = useMemo<UserContextType>(() => {
    if (!authUser) return { user: defaultUser };
    return {
      user: {
        user_id: authUser.user_id,
        display_name: authUser.email ?? authUser.user_id,
        role: authUser.role ?? "READ_ONLY",
      },
    };
  }, [authUser]);

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}
