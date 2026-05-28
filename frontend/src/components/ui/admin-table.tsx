import { cn } from "@/lib/utils";

export interface AdminTableCol {
  key: string;
  label: string;
  align?: "left" | "right" | "center";
  /** Optional CSS width (e.g. "120px", "1.4fr", "20%"). */
  width?: string;
}

export type AdminTableRow = Record<string, React.ReactNode>;

interface AdminTableProps<T extends AdminTableRow = AdminTableRow> {
  cols: AdminTableCol[];
  rows: T[];
  /** Smaller row height. */
  dense?: boolean;
  /** Table caption rendered above the header row. */
  caption?: string;
  /** Custom row key; falls back to the row index. */
  getRowKey?: (row: T, index: number) => string;
  className?: string;
}

const alignClass: Record<NonNullable<AdminTableCol["align"]>, string> = {
  left: "text-left",
  right: "text-right",
  center: "text-center",
};

/**
 * Semantic table primitive for admin views. Renders a `<table>` with a
 * sunken header strip, hairline row rules matching Card chrome, and a
 * subtle hover highlight. Pass `dense` to tighten row height.
 */
export function AdminTable<T extends AdminTableRow = AdminTableRow>({
  cols,
  rows,
  dense,
  caption,
  getRowKey,
  className,
}: AdminTableProps<T>) {
  const rowPad = dense ? "px-5 py-2" : "px-5 py-3";

  return (
    <table
      className={cn(
        "w-full border-collapse text-[13px] text-ink",
        className,
      )}
    >
      {caption && (
        <caption className="caption-top px-5 py-2 text-left text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-mute">
          {caption}
        </caption>
      )}
      <colgroup>
        {cols.map((c) => (
          <col key={c.key} style={c.width ? { width: c.width } : undefined} />
        ))}
      </colgroup>
      <thead>
        <tr className="border-b border-rule bg-surface-sunken">
          {cols.map((c) => (
            <th
              key={c.key}
              scope="col"
              className={cn(
                "px-5 py-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-mute",
                alignClass[c.align ?? "left"],
              )}
            >
              {c.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => {
          const key = getRowKey ? getRowKey(row, i) : String(i);
          return (
            <tr
              key={key}
              className={cn(
                "transition-colors hover:bg-surface-sunken/60",
                i < rows.length - 1 && "border-b border-rule",
              )}
            >
              {cols.map((c) => (
                <td
                  key={c.key}
                  className={cn(rowPad, alignClass[c.align ?? "left"])}
                >
                  {row[c.key]}
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
