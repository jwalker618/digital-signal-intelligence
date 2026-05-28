"use client";

import { useEffect } from "react";
import { useThemeStore } from "@/store/themeStore";

/**
 * Syncs the persisted `isDark` flag into the <html class="dark"> class so
 * Tailwind 4's @custom-variant dark + our @theme overrides take effect.
 * An inline pre-hydration script in layout.tsx sets the class synchronously
 * before this hook runs, avoiding a flash of the wrong theme.
 */
export function ThemeBoot() {
  const isDark = useThemeStore((s) => s.isDark);
  useEffect(() => {
    if (typeof document === "undefined") return;
    document.documentElement.classList.toggle("dark", isDark);
    document.documentElement.style.colorScheme = isDark ? "dark" : "light";
  }, [isDark]);
  return null;
}
