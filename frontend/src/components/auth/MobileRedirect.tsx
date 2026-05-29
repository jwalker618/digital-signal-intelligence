"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Phone-viewport redirect. On a coarse-pointer / narrow-width device the
 * authenticated app group bounces the user to the dedicated mobile feed
 * at /m, unless they've explicitly opted into the desktop view.
 *
 *  - `?desktop=1` in the URL persists `dsi-prefers-desktop=1` and stays.
 *  - the mobile companion clears that flag via a "View on desktop" link.
 */
export function MobileRedirect() {
  const router = useRouter();
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.localStorage.getItem("dsi-prefers-desktop") === "1") return;
    const sp = new URLSearchParams(window.location.search);
    if (sp.get("desktop") === "1") {
      window.localStorage.setItem("dsi-prefers-desktop", "1");
      return;
    }
    const isPhone = window.matchMedia(
      "(max-width: 640px), (pointer: coarse)",
    ).matches;
    if (isPhone) router.replace("/m");
  }, [router]);
  return null;
}
