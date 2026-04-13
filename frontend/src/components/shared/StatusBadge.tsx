// FE: Small coloured status pill. Handles health statuses, proposal
// statuses, and generic enums.

"use client";

const COLOURS: Record<string, string> = {
  green: "bg-emerald-600/20 text-emerald-400 border-emerald-600/40",
  healthy: "bg-emerald-600/20 text-emerald-400 border-emerald-600/40",
  ok: "bg-emerald-600/20 text-emerald-400 border-emerald-600/40",
  deployed: "bg-emerald-600/20 text-emerald-400 border-emerald-600/40",
  approved: "bg-emerald-600/20 text-emerald-400 border-emerald-600/40",

  amber: "bg-amber-500/20 text-amber-400 border-amber-500/40",
  warning: "bg-amber-500/20 text-amber-400 border-amber-500/40",
  pending_review: "bg-amber-500/20 text-amber-400 border-amber-500/40",
  validating: "bg-amber-500/20 text-amber-400 border-amber-500/40",
  calibrating: "bg-amber-500/20 text-amber-400 border-amber-500/40",

  red: "bg-red-600/20 text-red-400 border-red-600/40",
  critical: "bg-red-600/20 text-red-400 border-red-600/40",
  rejected: "bg-red-600/20 text-red-400 border-red-600/40",
  locked: "bg-red-600/20 text-red-400 border-red-600/40",
  error: "bg-red-600/20 text-red-400 border-red-600/40",

  info: "bg-blue-500/20 text-blue-400 border-blue-500/40",
  draft: "bg-gray-500/20 text-gray-300 border-gray-500/40",
  archived: "bg-gray-500/20 text-gray-300 border-gray-500/40",
  superseded: "bg-gray-500/20 text-gray-300 border-gray-500/40",
};

export function StatusBadge({ status }: { status: string | null | undefined }) {
  if (!status) return <span className="opacity-60">—</span>;
  const lower = status.toLowerCase();
  const cls =
    COLOURS[lower] ??
    "bg-dsi-outline/10 text-dsi-contrast-background border-dsi-outline/40";
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-mono uppercase tracking-wider ${cls}`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
