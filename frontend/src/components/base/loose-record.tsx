"use client";

import { Card } from "@/components/ui/card";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { formatCurrency, formatDate, formatPercent, formatText } from "@/lib/format";

/**
 * `activeCommercial`, `activeRisk`, `activeReferral` are typed as
 * Record<string, any> in dsiStore because the carrier endpoints return
 * loose payloads that vary by coverage. This component renders a known
 * subset of fields with smart formatting and falls back gracefully when
 * the record is null or missing fields.
 */

export interface FieldSpec {
  key: string;
  label: string;
  /** How to format the raw value. */
  kind?: "currency" | "percent" | "date" | "text" | "factor" | "monospace";
  /** Hide the row if the value is empty/null. */
  hideIfEmpty?: boolean;
}

interface LooseRecordCardProps {
  title: string;
  subtitle?: string;
  data: Record<string, unknown> | null | undefined;
  fields: FieldSpec[];
  /** When true, render every other key in the record below the known fields. */
  showRest?: boolean;
  emptyMessage?: string;
  /** Card variant. */
  variant?: "default" | "info" | "spot" | "warn" | "neg" | "pos" | "aux";
}

export function LooseRecordCard({
  title,
  subtitle,
  data,
  fields,
  showRest = false,
  emptyMessage = "No data returned for this submission.",
  variant = "default",
}: LooseRecordCardProps) {
  if (!data) {
    return (
      <Card pad="md" variant={variant}>
        <Eyebrow>{title}</Eyebrow>
        <Body className="mt-2 italic">{emptyMessage}</Body>
      </Card>
    );
  }

  const known = new Set(fields.map((f) => f.key));
  const rows = fields
    .map((f) => ({ spec: f, value: data[f.key] }))
    .filter((r) => !(r.spec.hideIfEmpty && isEmpty(r.value)));

  const rest = showRest
    ? Object.entries(data).filter(
        ([k, v]) => !known.has(k) && !isEmpty(v) && !isComplex(v),
      )
    : [];

  return (
    <Card pad="md" variant={variant} className="space-y-2">
      <header>
        <Eyebrow>{title}</Eyebrow>
        {subtitle && <Micro className="mt-0.5 block">{subtitle}</Micro>}
      </header>
      {rows.length === 0 && rest.length === 0 ? (
        <Body className="italic">{emptyMessage}</Body>
      ) : (
        <>
          {rows.map((r) => (
            <LabelRow
              key={r.spec.key}
              label={r.spec.label}
              value={formatValue(r.value, r.spec.kind)}
            />
          ))}
          {rest.length > 0 && (
            <>
              {rows.length > 0 && (
                <Micro className="mt-2 block uppercase tracking-[0.08em]">
                  Other fields
                </Micro>
              )}
              {rest.map(([k, v]) => (
                <LabelRow
                  key={k}
                  label={formatText(k, "capitalize")}
                  value={formatValue(v, undefined)}
                />
              ))}
            </>
          )}
        </>
      )}
    </Card>
  );
}

function isEmpty(v: unknown): boolean {
  return v == null || v === "" || (Array.isArray(v) && v.length === 0);
}

function isComplex(v: unknown): boolean {
  if (Array.isArray(v)) return v.some((x) => typeof x === "object");
  if (typeof v === "object" && v !== null) return true;
  return false;
}

function formatValue(value: unknown, kind: FieldSpec["kind"]): React.ReactNode {
  if (value == null || value === "") return <span className="text-ink-mute">—</span>;
  switch (kind) {
    case "currency":
      return formatCurrency(Number(value));
    case "percent":
      return formatPercent(Number(value), 1);
    case "date":
      return formatDate(String(value));
    case "factor":
      return `×${Number(value).toFixed(3)}`;
    case "monospace":
      return <span className="font-mono text-[12.5px]">{String(value)}</span>;
    default:
      if (typeof value === "boolean") return value ? "Yes" : "No";
      if (typeof value === "number")
        return <span className="tabular-nums">{value.toLocaleString()}</span>;
      return String(value);
  }
}
