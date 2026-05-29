"use client";

import { Network, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency, formatText } from "@/lib/format";
import { numOrNull, strOrNull } from "@/lib/coerce";

/* ============================================================
 * Distribution — mirrors reim_wb_c.jsx WbDistribution.
 *
 * Two rows:
 *   1. Subscription · this carrier's slice — 4 KPIs
 *   2. Subscription tower — horizontal % bar + table
 *      (only THIS carrier's row when no other-carrier roster exists)
 * ============================================================ */

type TowerRow = {
  carrier: string;
  role: string;
  line: number;
  premium: number | null;
};

export default function DistributionPage() {
  const commercial = useDsiStore((s) => s.activeCommercial) as ApiRecord | null;
  const ver = useDsiStore((s) => s.activeVersion) as ApiRecord | null;

  if (!commercial) {
    return (
      <>
        <PageLoading />
      </>
    );
  }

  const distributionType = strOrNull(commercial.distribution_type);
  const signedLine = numOrNull(commercial.signed_line);
  const role = strOrNull(commercial.role);
  const leadLoading = numOrNull(commercial.lead_loading_factor);
  const grossPremium = numOrNull(commercial.gross_premium);
  const technicalPremium =
    numOrNull(commercial.technical_premium_usd ?? commercial.technical_premium_local) ??
    numOrNull(ver?.final_premium);

  const earningsValue =
    technicalPremium != null && signedLine != null
      ? technicalPremium * signedLine * (leadLoading ?? 1)
      : null;
  const earningsSub =
    technicalPremium != null && signedLine != null
      ? `${(signedLine * 100).toFixed(0)}% × ${formatCurrency(technicalPremium)}${
          leadLoading && leadLoading !== 1 ? ` × ${leadLoading.toFixed(2)}x` : ""
        }`
      : undefined;

  // Roster: subscribed_carriers JSONB may carry other carriers in the tower;
  // when absent, show just this carrier so the tower still has a baseline.
  const rosterRaw = commercial.subscribed_carriers ?? commercial.tower_carriers;
  const roster: TowerRow[] = Array.isArray(rosterRaw)
    ? (rosterRaw as ApiRecord[]).map((r) => ({
        carrier: strOrNull(r.carrier ?? r.name) ?? "—",
        role: strOrNull(r.role) ?? "FOLLOW",
        line: (numOrNull(r.signed_line ?? r.line) ?? 0) * (numOrNull(r.signed_line) != null && r.signed_line! <= 1 ? 100 : 1),
        premium:
          numOrNull(r.premium) ??
          (numOrNull(r.signed_line) != null && technicalPremium != null
            ? technicalPremium * Number(r.signed_line)
            : null),
      }))
    : signedLine != null
      ? [
          {
            carrier: "This carrier",
            role: role ?? "FOLLOW",
            line: signedLine * 100,
            premium: earningsValue,
          },
        ]
      : [];

  return (
    <>
      <WorkArea>
        <Card
          header="Subscription · this carrier's slice"
          icon={Network}
          pad="md"
        >
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <KpiSnug
              label="Signed line"
              value={signedLine != null ? `${(signedLine * 100).toFixed(0)}%` : "—"}
            />
            <KpiSnug
              label="Role"
              value={role ? role.toUpperCase() : "—"}
            />
            <KpiSnug
              label="Lead loading"
              value={leadLoading != null ? `${leadLoading.toFixed(2)}x` : "—"}
            />
            <KpiSnug
              label="This carrier earns"
              value={earningsValue != null ? formatCurrency(earningsValue) : "—"}
              tone="info"
              delta={earningsSub ? <Micro>{earningsSub}</Micro> : undefined}
            />
          </div>
          {distributionType && (
            <Micro className="mt-3 block">
              Distribution type:{" "}
              <strong>{formatText(distributionType, "capitalize")}</strong>
            </Micro>
          )}
        </Card>

        <Card header="Subscription tower" icon={Users} pad="md">
          {roster.length === 0 ? (
            <Body className="italic">No tower data on this submission.</Body>
          ) : (
            <>
              {/* Visual tower */}
              <div className="mb-3.5 flex h-7 overflow-hidden rounded-md border border-rule">
                {roster.map((r, i) => {
                  const isLead = r.role.toUpperCase() === "LEAD";
                  const bg = isLead
                    ? "bg-info"
                    : i === 1
                      ? "bg-info/40"
                      : i === 2
                        ? "bg-info/30"
                        : "bg-info/20";
                  return (
                    <div
                      key={`${r.carrier}-${i}`}
                      className={`flex items-center justify-center text-[11px] font-bold text-canvas ${bg} ${
                        i < roster.length - 1 ? "border-r-2 border-surface" : ""
                      }`}
                      style={{ flex: r.line }}
                    >
                      {r.line.toFixed(0)}%
                    </div>
                  );
                })}
              </div>

              <div className="grid grid-cols-[2fr_110px_90px_110px] border-b border-rule py-2 text-[10.5px] uppercase tracking-wider text-ink-mute">
                {["Carrier", "Role", "Signed line", "Premium"].map((h) => (
                  <span key={h}>{h}</span>
                ))}
              </div>
              {roster.map((r, i) => (
                <div
                  key={`${r.carrier}-${i}`}
                  className={`grid grid-cols-[2fr_110px_90px_110px] items-center py-2.5 text-[13px] ${
                    i < roster.length - 1 ? "border-b border-rule" : ""
                  }`}
                >
                  <span
                    className={
                      r.role.toUpperCase() === "LEAD" ? "font-bold" : "font-medium"
                    }
                  >
                    {r.carrier}
                  </span>
                  <span>
                    {r.role.toUpperCase() === "LEAD" ? (
                      <Chip variant="info" size="sm">
                        LEAD
                      </Chip>
                    ) : (
                      <Micro>{formatText(r.role.toLowerCase(), "capitalize")}</Micro>
                    )}
                  </span>
                  <span className="tabular-nums">{r.line.toFixed(0)}%</span>
                  <span className="font-mono font-semibold tabular-nums">
                    {r.premium != null
                      ? `$${(r.premium / 1000).toFixed(1)}k`
                      : "—"}
                  </span>
                </div>
              ))}
            </>
          )}
        </Card>
      </WorkArea>
    </>
  );
}


