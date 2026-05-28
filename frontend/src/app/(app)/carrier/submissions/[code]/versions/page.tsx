"use client";

import { use, useEffect, useState } from "react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency, formatDate, formatText } from "@/lib/format";

export default function ModelVersionsPage(props: {
  params: Promise<{ code: string }>;
}) {
  const { code } = use(props.params);
  const fetchHistory = useDsiStore((s) => s.fetchHistory);
  const sub = useDsiStore((s) => s.activeSubmission);
  const modelVersions = useDsiStore((s) => s.modelVersions) as
    | ApiRecord[]
    | undefined;
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setState("loading");
    fetchHistory(code)
      .then(() => setState("ok"))
      .catch((e) => {
        setErr(e instanceof Error ? e.message : String(e));
        setState("error");
      });
  }, [code, fetchHistory]);

  if (!sub)
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Model Versions" />
        <PageLoading />
      </>
    );
  if (state === "loading")
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Model Versions" />
        <PageLoading message="Loading version history…" />
      </>
    );
  if (state === "error")
    return (
      <>
        <WorkbenchTopbar activeTabLabel="Model Versions" />
        <PageError message={err ?? "Unknown error"} />
      </>
    );

  const versions = (modelVersions ?? []) as ApiRecord[];

  return (
    <>
      <WorkbenchTopbar activeTabLabel="Model Versions" />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1280px] gap-6">
          <header>
            <Eyebrow>History</Eyebrow>
            <h1 className="mt-1 font-display text-[28px] font-semibold leading-tight text-ink">
              Model versions
            </h1>
            <Body className="mt-2">
              Every quote version this submission has produced — score,
              decision, premium, and what changed between revisions.
            </Body>
          </header>

          {versions.length === 0 ? (
            <Card pad="lg">
              <Body className="italic">No version history available.</Body>
            </Card>
          ) : (
            <Card pad="md" className="overflow-hidden p-0">
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken text-left">
                    <ColHead width="w-[10%]">Version</ColHead>
                    <ColHead width="w-[18%]">Quote code</ColHead>
                    <ColHead width="w-[12%]">Score</ColHead>
                    <ColHead width="w-[10%]">Tier</ColHead>
                    <ColHead width="w-[14%]">Decision</ColHead>
                    <ColHead width="w-[18%]">Premium</ColHead>
                    <ColHead width="w-[18%]">Created</ColHead>
                  </tr>
                </thead>
                <tbody>
                  {versions.map((v, i) => {
                    const decision = String(v.decision ?? "").toLowerCase();
                    const decisionTone =
                      decision === "approve"
                        ? "pos"
                        : decision === "decline"
                          ? "neg"
                          : decision === "refer"
                            ? "warn"
                            : "mute";
                    return (
                      <tr
                        key={v.version_code ?? v.quote_code ?? i}
                        className="border-b border-rule last:border-0 hover:bg-surface-sunken/40"
                      >
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-ink">
                              v{v.version_number ?? "?"}
                            </span>
                            {i === 0 && (
                              <Chip variant="info" size="sm">
                                Current
                              </Chip>
                            )}
                          </div>
                        </td>
                        <td className="px-5 py-3 font-mono text-[12.5px] text-ink-soft">
                          {v.quote_code ?? "—"}
                        </td>
                        <td className="px-5 py-3 font-semibold tabular-nums text-ink">
                          {v.composite_score != null
                            ? Number(v.composite_score).toFixed(0)
                            : "—"}
                        </td>
                        <td className="px-5 py-3 tabular-nums text-ink">
                          {v.final_tier ?? "—"}
                        </td>
                        <td className="px-5 py-3">
                          {decision ? (
                            <Chip variant={decisionTone} size="sm">
                              {formatText(decision, "capitalize")}
                            </Chip>
                          ) : (
                            <span className="text-ink-mute">—</span>
                          )}
                        </td>
                        <td className="px-5 py-3 font-semibold tabular-nums text-ink">
                          {v.final_premium != null
                            ? formatCurrency(v.final_premium)
                            : "—"}
                        </td>
                        <td className="px-5 py-3 text-ink-soft">
                          {v.created_at ? formatDate(v.created_at) : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function ColHead({
  width,
  children,
}: {
  width: string;
  children: React.ReactNode;
}) {
  return (
    <th
      className={`px-5 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-mute ${width}`}
    >
      {children}
    </th>
  );
}
