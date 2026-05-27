// Shared URL-pattern helpers for the post-v8.2 portal architecture.
//
// The app has three persona-shaped URL trees:
//   /                   carrier home
//   /world-engine       carrier
//   /broker, /broker/*  broker portal
//   /client, /client/*  client portal
// plus shared portal surfaces:
//   /communications, /coverages, /submissions
//
// Chrome (sidebar, titleBar) needs to know "is this a portal-context
// path" to render the right menus and decoration. SessionGuard +
// login need to route a freshly-authenticated user to their persona
// home.

const PORTAL_PREFIXES = [
  "/broker",
  "/client",
  "/communications",
  "/coverages",
  "/submissions",
];

export function isPortalPath(pathname: string | null | undefined): boolean {
  if (!pathname) return false;
  return PORTAL_PREFIXES.some((prefix) =>
    pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function isBrokerPath(pathname: string | null | undefined): boolean {
  if (!pathname) return false;
  return pathname === "/broker" || pathname.startsWith("/broker/");
}

export function isClientPath(pathname: string | null | undefined): boolean {
  if (!pathname) return false;
  return pathname === "/client" || pathname.startsWith("/client/");
}


/** Where a user should land after login, by role. */
export function homePathForRole(role: string | null | undefined): string {
  if (role === "BROKER") return "/broker";
  if (role === "CLIENT") return "/client";
  return "/";   // carrier (UNDERWRITER, ADMIN, etc.)
}
