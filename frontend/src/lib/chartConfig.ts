/**
 * Shared chart configuration — decision → colour resolver and the
 * tooltip style object used by `base/charts/primatives.tsx`.
 *
 * All values reference CSS custom properties from globals.css so they
 * adapt to light/dark theme automatically. Recharts accepts CSS var()
 * references in string props (stroke, fill, etc.).
 */

const DECISION_COLORS: Record<string, string> = {
  approve: "var(--generate-approve)",
  refer:   "var(--generate-refer)",
  decline: "var(--generate-decline)",
};

export const getDecisionColor = (decision: string | undefined): string => {
  if (!decision) return "var(--generate-analysis)";
  return DECISION_COLORS[decision.toLowerCase()] || "var(--generate-analysis)";
};

export const tooltipStyle = {
  backgroundColor: "var(--generate-selected)",
  borderColor: "var(--generate-outline)",
  color: "#f8fafc",
  borderRadius: "8px",
  fontSize: "12px",
};
