/**
 * Shared chart configuration — decision → colour resolver and the
 * tooltip style object used by `base/charts/primatives.tsx`.
 *
 * All values reference CSS custom properties from globals.css so they
 * adapt to light/dark theme automatically. Recharts accepts CSS var()
 * references in string props (stroke, fill, etc.).
 */

const DECISION_COLORS: Record<string, string> = {
  approve: "var(--dsi-approve)",
  refer:   "var(--dsi-refer)",
  decline: "var(--dsi-decline)",
};

export const getDecisionColor = (decision: string | undefined): string => {
  if (!decision) return "var(--dsi-analysis)";
  return DECISION_COLORS[decision.toLowerCase()] || "var(--dsi-analysis)";
};

export const tooltipStyle = {
  backgroundColor: "var(--dsi-selected)",
  borderColor: "var(--dsi-outline)",
  color: "#f8fafc",
  borderRadius: "8px",
  fontSize: "12px",
};
