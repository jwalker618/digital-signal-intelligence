import type { Metadata, Viewport } from "next";
import { ThemeBoot } from "@/components/theme-boot";
import "./globals.css";

export const metadata: Metadata = {
  title: "DSI — Digital Signal Intelligence",
  description:
    "Risk, illuminated by signal. Underwriting, broking, and risk insight for commercial insurance.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  userScalable: false,
};

/**
 * Pre-hydration theme script. Reads the persisted zustand store (key
 * `generate-theme`, set by themeStore) and toggles the `dark` class on
 * <html> synchronously so themed surfaces never flash the wrong colors.
 */
const themeBootScript = `(() => {
  try {
    const raw = localStorage.getItem('generate-theme');
    let isDark = matchMedia('(prefers-color-scheme: dark)').matches;
    if (raw) {
      const parsed = JSON.parse(raw);
      if (typeof parsed?.state?.isDark === 'boolean') isDark = parsed.state.isDark;
    }
    if (isDark) document.documentElement.classList.add('dark');
    document.documentElement.style.colorScheme = isDark ? 'dark' : 'light';
  } catch (_) {}
})();`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeBootScript }} />
      </head>
      <body className="min-h-screen bg-canvas text-ink antialiased">
        <ThemeBoot />
        {children}
      </body>
    </html>
  );
}
