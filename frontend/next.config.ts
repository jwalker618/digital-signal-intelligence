import type { NextConfig } from "next";

// A-3i: PWA wrapper. `@ducanh2912/next-pwa` is the maintained fork of
// next-pwa and wraps Workbox. It is treated as an optional dependency
// here -- if it isn't installed yet, we fall through with a no-op so
// local dev / CI still build cleanly. Install it with:
//   npm install @ducanh2912/next-pwa
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let withPWA: ((cfg: any) => (next: NextConfig) => NextConfig) | null = null;
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  withPWA = require("@ducanh2912/next-pwa").default;
} catch {
  withPWA = null;
}

const nextConfig: NextConfig = {
  allowedDevOrigins: ['unnamable-sherlene-barratrous.ngrok-free.dev'],
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
    ];
  },
  // Dev compile speed for `lucide-react`. The library's per-icon
  // `dist/esm/icons/*.mjs` files export the icon as `default`, so the
  // naive `modularizeImports` rewrite of named imports → deep paths
  // breaks every `import { Eye, EyeOff } from "lucide-react"` call
  // site. Use Next.js's built-in `optimizePackageImports` instead: it
  // ships with a curated allowlist (lucide-react included) and handles
  // the default-vs-named import shape correctly under the hood.
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
};

// A-3i: Runtime caching strategy
// - Static assets (content-hashed by Next.js): cache-first
// - API calls: network-first with 10s timeout (never serve stale data)
// - Fonts: long-lived cache-first
const pwaConfig = {
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
  // A-4f: extend the generated SW with push + notificationclick handlers.
  customWorkerSrc: "public/custom-sw.js",
  workboxOptions: {
    runtimeCaching: [
      {
        urlPattern: /\/_next\/static\/.*/i,
        handler: "CacheFirst",
        options: {
          cacheName: "static-assets",
          expiration: { maxEntries: 200, maxAgeSeconds: 30 * 24 * 60 * 60 },
        },
      },
      {
        urlPattern: /\/api\/v1\/.*/i,
        handler: "NetworkFirst",
        options: {
          cacheName: "api-responses",
          expiration: { maxEntries: 50, maxAgeSeconds: 5 * 60 },
          networkTimeoutSeconds: 10,
        },
      },
      {
        urlPattern: /\.(?:woff|woff2|ttf|otf)$/i,
        handler: "CacheFirst",
        options: {
          cacheName: "fonts",
          expiration: { maxEntries: 20, maxAgeSeconds: 365 * 24 * 60 * 60 },
        },
      },
    ],
  },
};

export default withPWA ? withPWA(pwaConfig)(nextConfig) : nextConfig;
