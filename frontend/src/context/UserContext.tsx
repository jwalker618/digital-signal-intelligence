"use client";

import { createContext, useContext, ReactNode } from "react";

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
  role: "underwriter",
};

const UserContext = createContext<UserContextType>({ user: defaultUser });

export function UserProvider({ children }: { children: ReactNode }) {
  // TODO: Replace with real auth context (e.g., NextAuth, Clerk, custom SSO)
  // For now, uses a static default user
  const value = { user: defaultUser };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}
