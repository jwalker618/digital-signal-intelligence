/**
 * Shared chart configuration — colours, tooltip styles, decision palettes.
 *
 * All values reference CSS custom properties from globals.css so they
 * adapt to light/dark theme automatically. Recharts accepts CSS var()
 * references in string props (stroke, fill, etc.).
 */

export const DECISION_COLORS: Record<string, string> = {
  approve: 'var(--dsi-approve)',
  refer: 'var(--dsi-refer)',
  decline: 'var(--dsi-decline)',
};

export const getDecisionColor = (decision: string | undefined): string => {
  if (!decision) return 'var(--dsi-chart-peer)';
  return DECISION_COLORS[decision.toLowerCase()] || 'var(--dsi-chart-peer)';
};

export const tooltipStyle = {
  backgroundColor: 'var(--dsi-chart-tooltip-bg)',
  borderColor: 'var(--dsi-chart-tooltip-border)',
  color: '#f8fafc',
  borderRadius: '8px',
  fontSize: '12px',
};

export const CHART_GRID_COLOR = 'var(--dsi-chart-grid)';
export const CHART_AXIS_COLOR = 'var(--dsi-chart-axis)';
export const CHART_SUBJECT_COLOR = 'var(--dsi-chart-subject)';
export const CHART_PEER_COLOR = 'var(--dsi-chart-peer)';
