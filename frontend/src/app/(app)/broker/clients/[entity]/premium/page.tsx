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

  const technical = c.premium;
  const chain = c.modifier_chain ?? [];

  return (
    <WorkArea className="lg:grid-cols-[1.6fr_1fr]">
      <Card
        header={`Premium build-up · ${c.line}`}
        icon={Calculator}
        pad="md"
        headerRight={<Chip variant="default" size="sm">{c.code}</Chip>}
      >
        {chain.length > 0 ? (
          <>
            {chain.map((row) => {
              const isBase = row.factor == null && row.delta == null;
              return (
                <div
                  key={row.group}
                  className="grid grid-cols-[1.4fr_70px_110px_120px] items-center gap-2.5 border-b border-rule py-2.5"
                >
                  <span className={`text-[13px] ${isBase ? "font-bold" : ""}`}>
                    {row.group}
                  </span>
                  <span className="text-[12px] tabular-nums text-ink-mute">
                    {row.factor != null ? `${row.factor.toFixed(2)}x` : ""}
                  </span>
                  <span
                    className={`text-right font-mono text-[13px] font-semibold tabular-nums ${
                      row.delta == null
                        ? "text-ink-mute"
                        : row.delta < 0
                          ? "text-pos"
                          : "text-neg"
                    }`}
                  >
                    {row.delta == null
                      ? "—"
                      : `${row.delta < 0 ? "−" : "+"}${formatCurrency(Math.abs(row.delta))}`}
                  </span>
                  <span className="text-right font-mono text-[13px] font-bold tabular-nums">
                    {row.running != null ? formatCurrency(row.running) : "—"}
                  </span>
                </div>
              );
            })}
            <div className="mt-1 grid grid-cols-[1.4fr_70px_110px_120px] gap-2.5 pt-3">
              <span className="text-[14px] font-bold">Technical premium</span>
              <span />
              <span />
              <span className="text-right font-mono text-[17px] font-bold text-info-deep tabular-nums dark:text-info">
                {technical != null ? formatCurrency(technical) : "—"}
              </span>
            </div>
          </>
        ) : (
          <Body className="italic">
            Premium build-up not available for this line.
          </Body>
        )}
      </Card>

      <Card header="Commercial" icon={Building2} pad="md">
        <LabelRow
          label="Technical premium"
          value={technical != null ? <span className="font-mono font-semibold">{formatCurrency(technical)}</span> : "—"}
        />
        <LabelRow label="Brokerage" value={c.brokerage_rate != null ? pct(c.brokerage_rate, 1) : "—"} />
        <LabelRow
          label="Net premium"
          value={c.net_premium != null ? <span className="font-mono">{formatCurrency(c.net_premium)}</span> : "—"}
        />
        <LabelRow
          label="Taxes + levies"
          value={c.total_taxes != null ? <span className="font-mono">{formatCurrency(c.total_taxes)}</span> : "—"}
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
        <LabelRow
          label="Distribution"
          value={
            c.distribution_type
              ? `${c.distribution_type}${c.signed_line != null ? ` · signed ${Math.round(c.signed_line * 100)}%` : ""}`
              : "—"
          }
        />
        <LabelRow
          label="Role"
          value={
            c.role
              ? `${c.role}${c.lead_loading_factor != null ? ` · ${c.lead_loading_factor.toFixed(2)}x loading` : ""}`
              : "—"
          }
        />
        <Micro className="mt-3 block border-t border-rule pt-3">
          {c.line} line shown. Other lines follow the same chain with
          line-specific factors.
        </Micro>
      </Card>
    </WorkArea>
  );
}
