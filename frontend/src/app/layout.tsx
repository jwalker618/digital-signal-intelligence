"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { IBM_Plex_Sans, Inter } from "next/font/google";

import { SessionGuard } from "@/components/auth/SessionGuard";
import { NotificationToastHost } from "@/components/shared/NotificationToast";
import { useThemeStore } from "@/store/themeStore";

import Sidebar from "@/components/layout/sidebar";
import TitleBar from "@/components/layout/titleBar";

import "./globals.css";

const ibmPlex = IBM_Plex_Sans({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-ibm",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const isDark = useThemeStore((s) => s.isDark);

  const pathname = usePathname();
  const isPublicAuthPage =
    pathname?.startsWith("/login") ||
    pathname?.startsWith("/reset-password") ||
    pathname?.startsWith("/sso/callback");

  const sidebarRef = useRef<HTMLElement>(null);
  const [collapsedWidthPx, setCollapsedWidthPx] = useState<number | null>(null);

  // Measure sidebar width from the parent DOM. Re-runs after the aside
  // mounts (e.g. navigating from /login to /): without `isPublicAuthPage`
  // in the deps, the effect fired once on /login while sidebarRef was
  // still null and never re-ran.
  useEffect(() => {
    if (!sidebarRef.current || !sidebarRef.current.parentElement) return;

    const measure = () => {
      const parentWidth = sidebarRef.current?.parentElement?.getBoundingClientRect()
        .width;
      if (parentWidth) setCollapsedWidthPx(parentWidth * 0.05);
    };

    const observer = new ResizeObserver(measure);
    observer.observe(sidebarRef.current.parentElement);
    measure();

    return () => observer.disconnect();
  }, [isPublicAuthPage]);

  useEffect(() => {
    const html = document.documentElement;
    if (isDark) html.classList.add("dark");
    else html.classList.remove("dark");
  }, [isDark]);

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#000000" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
      </head>
      <body
        className={`${ibmPlex.variable} ${inter.variable} font-ibm h-screen w-screen overflow-hidden`}
      >
        <SessionGuard>
          <NotificationToastHost />

          {isPublicAuthPage ? (
            children
          ) : (
            <div className="relative h-full w-full">
              <Sidebar
                sidebarRef={sidebarRef}
                isOpen={isOpen}
                onToggleOpen={() => setIsOpen(!isOpen)}
                collapsedWidthPx={collapsedWidthPx}
              />

              <main
                className="
                  absolute top-0 right-0 h-full 
                  bg-generate-light-background 
                  text-generate-text-placeholder 
                  overflow-hidden 
                  flex flex-col 
                  transition-none"
                style={
                  {
                    left: collapsedWidthPx ? `${collapsedWidthPx}px` : "5%",
                    "--cw": collapsedWidthPx
                      ? `${collapsedWidthPx}px`
                      : "80px",
                  } as React.CSSProperties
                }
              >
                <TitleBar />

                <div className="relative flex-1 overflow-hidden">
                  {children}
                </div>
              </main>
            </div>
          )}
        </SessionGuard>
      </body>
    </html>
  );
}
