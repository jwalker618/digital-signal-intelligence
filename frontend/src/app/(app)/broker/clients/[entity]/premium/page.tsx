"use client";

import { Building2, Calculator } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
import { LabelRow } from "@/components/ui/label-row";
import { formatCurrency } from "@/lib/format";
import { useClientWorkbench } from "../_lib/context";
import { pct } from "../_lib/helpers";

export default function PremiumBuildupPage() {
  const cw = useClientWorkbench();
  if (!cw) return null;

  // Featured line = first coverage.
  const c = cw.coverages[0];
  if (!c) {
    return (
      <WorkArea>
        <Card pad="lg">
          <Body className="italic">No coverages to price.</Body>
        </Card>
      </WorkArea>
    );
  }

  const base = c.base_premium;
  const technical = c.premium;
  const brokeragePct =
    c.total_commission != null && c.net_premium != null && c.net_premium > 0
      ? c.total_commission / c.net_premium
      : null;

  const chain: Array<{ label: string; value: number | null; bold?: boolean; tone?: string }> = [
    { label: "Base premium", value: base, bold: true },
    { label: "Technical premium", value: technical, bold: true, tone: "info" },
  ];

  return (
    <WorkArea className="lg:grid-cols-[1.6fr_1fr]">
      <Card
        header={`Premium build-up · ${c.line}`}
        icon={Calculator}
        pad="md"
        headerRight={<Chip variant="default" size="sm">{c.code}</Chip>}
      >
        {base != null && technical != null ? (
          <>
            {chain.map((row) => (
              <div
                key={row.label}
                className="grid grid-cols-[1.4fr_120px] items-center gap-2.5 border-b border-rule py-2.5"
              >
                <span className={`text-[13px] ${row.bold ? "font-bold" : ""}`}>{row.label}</span>
                <span
                  className={`text-right font-mono text-[13px] font-bold tabular-nums ${
                    row.tone === "info" ? "text-info-deep dark:text-info" : ""
                  }`}
                >
                  {formatCurrency(row.value!)}
                </span>
              </div>
            ))}
            <div className="mt-1 grid grid-cols-[1.4fr_120px] gap-2.5 pt-3">
              <span className="text-[14px] font-bold">Modifier impact</span>
              <span className="text-right font-mono text-[15px] font-bold tabular-nums">
                {base > 0 ? `${technical >= base ? "+" : ""}${pct((technical - base) / base, 1)}` : "—"}
              </span>
            </div>
          </>
        ) : (
          <Body className="italic">Premium build-up not available for this line.</Body>
        )}
      </Card>

      <Card header="Commercial" icon={Building2} pad="md">
        <LabelRow
          label="Technical premium"
          value={technical != null ? <span className="font-mono font-semibold">{formatCurrency(technical)}</span> : "—"}
        />
        <LabelRow label="Brokerage" value={brokeragePct != null ? pct(brokeragePct, 1) : "—"} />
        <LabelRow
          label="Net premium"
          value={c.net_premium != null ? <span className="font-mono">{formatCurrency(c.net_premium)}</span> : "—"}
        />
        <LabelRow
          label="Gross premium"
          value={c.gross_premium != null ? <span className="font-mono font-semibold">{formatCurrency(c.gross_premium)}</span> : "—"}
        />
        <LabelRow
          label="Offered premium"
          value={c.offered_premium != null ? <span className="font-mono font-semibold text-info">{formatCurrency(c.offered_premium)}</span> : "—"}
        />
        <LabelRow
          label="Total commission"
          value={c.total_commission != null ? <span className="font-mono">{formatCurrency(c.total_commission)}</span> : "—"}
        />
        <Micro className="mt-3 block border-t border-rule pt-3">
          {c.line} line shown. Other lines follow the same chain with
          line-specific factors.
        </Micro>
      </Card>
    </WorkArea>
  );
}
