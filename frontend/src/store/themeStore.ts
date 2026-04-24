// Theme store (Zustand)
//
// Tracks dark-mode preference and persists it to localStorage so the
// choice made on /login carries into the authenticated shell and
// survives refreshes. The single point that applies the `dark` class
// on <html> lives in app/layout.tsx.

"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface ThemeState {
  isDark: boolean;
  toggleDark: () => void;
  setDark: (v: boolean) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      isDark: false,
      toggleDark: () => set((s) => ({ isDark: !s.isDark })),
      setDark: (v) => set({ isDark: v }),
    }),
    {
      name: "generate-theme",
      storage: createJSONStorage(() => {
        if (typeof window === "undefined") {
          // SSR safe stub
          return {
            getItem: () => null,
            setItem: () => undefined,
            removeItem: () => undefined,
          } as Storage;
        }
        return window.localStorage;
      }),
    },
  ),
);
