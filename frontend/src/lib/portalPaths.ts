// Shared URL-pattern helpers for the persona-shaped portal architecture.
//
// The app has three persona-shaped URL trees, all under top-level
// dirs (no Next.js route groups -- the dir name IS part of the URL):
//   /carrier, /carrier/*    underwriter workbench + world-engine
//   /broker,  /broker/*     broker portal
//   /client,  /client/*     client portal
//
// Shared portal pages (communications, coverages, submission detail)
// are duplicated under both /broker/* and /client/* so each URL has
// clear persona ownership. The actual view logic lives in shared
// components imported by both wrappers.
//
// The root URL / is a thin role-aware redirect (app/page.tsx) that
// bounces every authenticated user to their persona home.

const CARRIER_PREFIXES = ["/carrier"];
const BROKER_PREFIXES  = ["/broker"];
const CLIENT_PREFIXES  = ["/client"];

function matchesAny(pathname: string, prefixes: string[]): boolean {
  return prefixes.some((prefix) =>
    pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function isCarrierPath(pathname: string | null | undefined): boolean {
  return !!pathname && matchesAny(pathname, CARRIER_PREFIXES);
}

export function isBrokerPath(pathname: string | null | undefined): boolean {
  return !!pathname && matchesAny(pathname, BROKER_PREFIXES);
}

export function isClientPath(pathname: string | null | undefined): boolean {
  return !!pathname && matchesAny(pathname, CLIENT_PREFIXES);
}

/** Portal context = broker tree or client tree (drives sidebar mode). */
export function isPortalPath(pathname: string | null | undefined): boolean {
  return isBrokerPath(pathname) || isClientPath(pathname);
}


/** Where a user should land after login, by role. */
export function homePathForRole(role: string | null | undefined): string {
  if (role === "BROKER") return "/broker";
  if (role === "CLIENT") return "/client";
  // Everyone else (UNDERWRITER, ADMIN, MARSH_ADMIN, etc.) is carrier.
  return "/carrier";
}

/**
 * True for any role that should see carrier-side views. Inverts the
 * portal split: anything that's not BROKER/CLIENT is carrier.
 */
export function isCarrierRole(role: string | null | undefined): boolean {
  if (!role) return true; // unknown role gets carrier home by default
  return role !== "BROKER" && role !== "CLIENT";
}
