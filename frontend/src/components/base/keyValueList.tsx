/**
 * KeyValueList — renders a key/value object as a divided list.
 *
 * Used for modal bodies like Submission Data / Discovery Output where the
 * layout is identical and only the label/value formatting differs.
 */

import "@/app/globals.css";

export interface KeyValueListProps<V = unknown> {
  data: Record<string, V> | null | undefined;
  /** Predicate filter on keys. */
  filter?: (key: string) => boolean;
  /** Label cell renderer. Defaults to the raw key. */
  renderLabel?: (key: string) => React.ReactNode;
  /** Value cell renderer. Defaults to `String(value)`. */
  renderValue?: (value: V, key: string) => React.ReactNode;
  /** Tailwind classes appended to the value `<span>`. */
  valueClassName?: string;
  emptyMessage?: string;
}

export default function KeyValueList<V = unknown>({
  data,
  filter,
  renderLabel = (k) => k,
  renderValue = (v) => String(v),
  valueClassName = "",
  emptyMessage = "No data available.",
}: KeyValueListProps<V>) {
  const entries = Object.entries(data ?? {}).filter(([k]) => !filter || filter(k));

  if (entries.length === 0) {
    return <div className="dsi-user-message">{emptyMessage}</div>;
  }

  return (
    <div className="space-y-3 font-mono text-sm">
      {entries.map(([key, value]) => (
        <div
          key={key}
          className="flex justify-between items-center py-2 border-b border-dsi-outline/5 last:border-0"
        >
          <span className="opacity-60">{renderLabel(key)}</span>
          <span className={`font-bold text-right ${valueClassName}`}>
            {renderValue(value as V, key)}
          </span>
        </div>
      ))}
    </div>
  );
}
