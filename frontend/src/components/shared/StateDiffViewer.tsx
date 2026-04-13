// FE: Side-by-side JSON before/after diff. Used in the audit log viewer,
// config diff, and recalibration proposal detail.
//
// Lightweight: renders each key, highlights added / changed / removed.
// Not a full tree diff -- shallow key-level diff is enough for the
// state objects we emit.

"use client";

type Json = unknown;

function keysOf(obj: Json): string[] {
  if (obj && typeof obj === "object" && !Array.isArray(obj)) {
    return Object.keys(obj as Record<string, unknown>);
  }
  return [];
}

function valueOf(obj: Json, key: string): Json {
  if (obj && typeof obj === "object" && !Array.isArray(obj)) {
    return (obj as Record<string, unknown>)[key];
  }
  return undefined;
}

function formatValue(v: Json): string {
  if (v === undefined) return "—";
  if (v === null) return "null";
  if (typeof v === "string") return v;
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return String(v);
  }
}

export function StateDiffViewer({
  before,
  after,
}: {
  before: Json;
  after: Json;
}) {
  const keys = Array.from(new Set([...keysOf(before), ...keysOf(after)])).sort();

  if (keys.length === 0) {
    return (
      <pre className="text-xs bg-dsi-background border border-dsi-outline/30 rounded p-2 overflow-auto">
        {formatValue(after ?? before)}
      </pre>
    );
  }

  return (
    <table className="w-full text-xs font-mono border-collapse">
      <thead>
        <tr className="opacity-60 text-left">
          <th className="py-1 pr-2">Key</th>
          <th className="py-1 pr-2">Before</th>
          <th className="py-1">After</th>
        </tr>
      </thead>
      <tbody>
        {keys.map((k) => {
          const b = valueOf(before, k);
          const a = valueOf(after, k);
          const changed = JSON.stringify(b) !== JSON.stringify(a);
          return (
            <tr
              key={k}
              className={`border-t border-dsi-outline/20 ${
                changed ? "bg-amber-500/5" : ""
              }`}
            >
              <td className="py-1 pr-2 align-top">{k}</td>
              <td className="py-1 pr-2 align-top whitespace-pre-wrap opacity-70">
                {formatValue(b)}
              </td>
              <td
                className={`py-1 align-top whitespace-pre-wrap ${
                  changed ? "text-dsi-selected" : ""
                }`}
              >
                {formatValue(a)}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
