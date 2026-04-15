/**
 * KeyValueList — object→list convenience wrapper over LabelValueList.
 *
 * Used when the source is a raw `Record<string, V>` rather than a
 * pre-structured rows array (modal bodies like Submission Data / Discovery
 * Output). Delegates all rendering to LabelValueList so styling stays in one
 * place.
 */

import "@/app/globals.css";
import LabelValueList, { LabelValueVariant } from "./labelValueList";

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
  /** Visual variant — defaults to "modal" (divided font-mono rows). */
  variant?: LabelValueVariant;
}

export default function KeyValueList<V = unknown>({
  data,
  filter,
  renderLabel = (k) => k,
  renderValue = (v) => String(v),
  valueClassName,
  emptyMessage = "No data available.",
  variant = "modal",
}: KeyValueListProps<V>) {
  const rows = Object.entries(data ?? {})
    .filter(([k]) => !filter || filter(k))
    .map(([k, v]) => ({
      key: k,
      label: renderLabel(k),
      value: renderValue(v as V, k),
      valueClassName,
    }));

  return <LabelValueList rows={rows} variant={variant} emptyMessage={emptyMessage} />;
}
