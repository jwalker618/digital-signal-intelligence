"use client";

import { use, useEffect, useState } from "react";
import { GitBranch } from "lucide-react";
import { WorkbenchTopbar } from "@/components/chrome/workbench-topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Body } from "@/components/ui/typography";
import { PageError, PageLoading } from "@/components/base/pageStates";
import { useDsiStore, type ApiRecord } from "@/store/dsiStore";
import { formatCurrency, formatText } from "@/lib/format";

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
          {versions.length === 0 ? (
            <Card header="Version lineage" icon={GitBranch} pad="lg">
              <Body className="italic">No version history available.</Body>
            </Card>
          ) : (
            <Card
              header="Version lineage"
              icon={GitBranch}
              headerRight={
                <Chip variant="mute" size="sm">
                  {versions.length} version{versions.length === 1 ? "" : "s"}
                </Chip>
              }
              pad="none"
              className="overflow-hidden"
            >
              <table className="w-full table-fixed text-[13px]">
                <thead>
                  <tr className="border-b border-rule bg-surface-sunken text-left">
                    {/* quote_code and created_at not exposed by ModelVersionDBRecord; columns omitted */}
                    <ColHead width="w-[20%]">Version</ColHead>
                    <ColHead width="w-[20%]">Score</ColHead>
                    <ColHead width="w-[18%]">Tier</ColHead>
                    <ColHead width="w-[20%]">Decision</ColHead>
                    <ColHead width="w-[22%]">Premium</ColHead>
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
                        key={v.version_code ?? i}
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
                        <td className="px-5 py-3 font-semibold tabular-nums text-ink">
                          {v.final_composite_score != null
                            ? Number(v.final_composite_score).toFixed(0)
                            : v.pure_composite_score != null
                              ? Number(v.pure_composite_score).toFixed(0)
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
                        {/* created_at not exposed by ModelVersionDBRecord; column omitted */}
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
