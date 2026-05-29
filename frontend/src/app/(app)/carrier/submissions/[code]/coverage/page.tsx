"use client";

import { Check, FileCheck, MinusCircle, PlusCircle, X } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { WorkArea } from "@/components/ui/work-area";
import { Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatText } from "@/lib/format";

/* ============================================================
 * Coverage Terms — mirrors reim_wb_b.jsx WbCoverage (section 06).
 *
 * Two rows:
 *   1. Coverage overview — 4 KPIs (Territory / Trigger / #Extensions /
 *      #Exclusions)
 *   2. 2-col: Extensions list (pos) + Exclusions list (neg). Each row is
 *      a tinted dot + name + description.
 * ============================================================ */

type Clause = { name: string; desc?: string };

export default function CoverageTermsPage() {
  const risk = useDsiStore((s) => s.activeRisk) as ApiRecord | null;

  if (!risk) {
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Coverage Terms" />
        <PageLoading message="Loading coverage terms…" />
      </>
    );
  }

  const coverageTerms = (risk.coverage_terms as ApiRecord | undefined) ?? {};
  const territory = strOrNull(coverageTerms.territory);
  const trigger = strOrNull(coverageTerms.trigger);
  const extensions = toClauseList(coverageTerms.extensions);
  const exclusions = toClauseList(coverageTerms.exclusions);

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Coverage Terms" />
      <WorkArea>
        {/* ─── 1. Overview ─────────────────────────────────── */}
        <Card header="Coverage overview" icon={FileCheck} pad="md">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <KpiSnug
              label="Territory"
              value={territory ? formatText(territory, "capitalize") : "—"}
            />
            <KpiSnug
              label="Trigger"
              value={
                trigger ? formatText(trigger.replace(/_/g, "-"), "capitalize") : "—"
              }
            />
            <KpiSnug label="Extensions" value={String(extensions.length)} />
            <KpiSnug label="Exclusions" value={String(exclusions.length)} />
          </div>
        </Card>

        {/* ─── 2. Extensions + Exclusions ─────────────────── */}
        <div className="grid gap-3.5 md:grid-cols-2">
          <Card
            header={`Extensions · ${extensions.length}`}
            icon={PlusCircle}
            pad="md"
          >
            <ClauseList items={extensions} tone="pos" />
          </Card>
          <Card
            header={`Exclusions · ${exclusions.length}`}
            icon={MinusCircle}
            pad="md"
          >
            <ClauseList items={exclusions} tone="neg" />
          </Card>
        </div>
      </WorkArea>
    </>
  );
}

function ClauseList({ items, tone }: { items: Clause[]; tone: "pos" | "neg" }) {
  if (items.length === 0) {
    return <Micro className="italic">None recorded.</Micro>;
  }
  const dotBg = tone === "pos" ? "bg-pos-soft text-pos" : "bg-neg-soft text-neg";
  return (
    <div>
      {items.map((it, i) => (
        <div
          key={`${it.name}-${i}`}
          className={`grid grid-cols-[20px_1fr] gap-3 py-2.5 ${
            i < items.length - 1 ? "border-b border-rule" : ""
          }`}
        >
          <div
            className={`mt-0.5 flex h-5 w-5 items-center justify-center rounded-full ${dotBg}`}
          >
            {tone === "pos" ? <Check size={12} /> : <X size={12} />}
          </div>
          <div>
            <div className="text-[13px] font-medium">{it.name}</div>
            {it.desc && <Micro className="mt-0.5 block">{it.desc}</Micro>}
          </div>
        </div>
      ))}
    </div>
  );
}

function toClauseList(raw: unknown): Clause[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map((item): Clause | null => {
      if (typeof item === "string") {
        return { name: formatText(item.replace(/_/g, " "), "capitalize") };
      }
      if (item && typeof item === "object") {
        const r = item as ApiRecord;
        const name = strOrNull(r.name ?? r.label ?? r.title);
        if (!name) return null;
        return {
          name: formatText(name.replace(/_/g, " "), "capitalize"),
          desc: strOrNull(r.description ?? r.desc ?? r.notes) ?? undefined,
        };
      }
      return null;
    })
    .filter((c): c is Clause => c !== null);
}

function strOrNull(v: unknown): string | null {
  if (v == null) return null;
  const s = String(v).trim();
  return s.length > 0 ? s : null;
}
