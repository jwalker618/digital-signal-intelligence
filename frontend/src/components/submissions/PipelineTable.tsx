"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import { CircleCheck, CircleX, Loader2, Filter, X } from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import { useDsiStore } from "@/store/dsiStore";
import "@/app/globals.css";

export default function PipelineTable({ type }: { type: "full" | "referral" }) {
  const {
    setPageQuickAction,
    submissions,
    isLoading,
    daysFilter,
    setDaysFilter,
    fetchCoreSubmissionDetail,
    updateDecision
  } = useDsiStore();

  // Column filter state
  const [clientFilter, setClientFilter] = useState("");
  const [coverageFilter, setCoverageFilter] = useState("");
  const [decisionFilter, setDecisionFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState<string | null>(null);

  useEffect(() => {
    setPageQuickAction(
      <select
        value={daysFilter}
        onChange={(e) => setDaysFilter(Number(e.target.value))}
        className="outline-none bg-dsi-background text-dsi-contrast-background hover:text-dsi-selected"
      >
        <option value={7}>Last 7 Days</option>
        <option value={30}>Last 30 Days</option>
        <option value={90}>Last 90 Days</option>
        <option value={365}>Last 1 Year</option>
      </select>
    );
    return () => setPageQuickAction(null);
  }, [daysFilter, setDaysFilter, setPageQuickAction]);

  // Base data: referral pipeline filters to REFER decisions
  const baseData = type === "referral"
    ? submissions.filter(s => s.decision === "REFER")
    : submissions;

  // Apply column filters
  const displayData = useMemo(() => {
    return baseData.filter((sub: any) => {
      if (clientFilter && !(sub.entity_name || '').toLowerCase().includes(clientFilter.toLowerCase())) return false;
      if (coverageFilter && !(sub.coverage_configuration || '').toLowerCase().includes(coverageFilter.toLowerCase())) return false;
      if (decisionFilter && (sub.decision || '').toLowerCase() !== decisionFilter.toLowerCase()) return false;
      return true;
    });
  }, [baseData, clientFilter, coverageFilter, decisionFilter]);

  // Unique values for decision dropdown
  const uniqueDecisions = useMemo(() => {
    const set = new Set<string>();
    baseData.forEach((s: any) => { if (s.decision) set.add(s.decision); });
    return Array.from(set).sort();
  }, [baseData]);

  const hasAnyFilter = clientFilter || coverageFilter || decisionFilter;
  const clearAllFilters = () => { setClientFilter(""); setCoverageFilter(""); setDecisionFilter(""); setActiveFilter(null); };

  const handleRowClick = (sub: any) => fetchCoreSubmissionDetail(sub);

  if (isLoading) {
    return (
      <ViewCanvas unstyledMain={false}>
        <div className="flex h-full items-center justify-center">
          <Loader2 className="animate-spin text-dsi-selected w-8 h-8" />
        </div>
      </ViewCanvas>
    );
  }

  return (
    <ViewCanvas unstyledMain={true}>
      <div className="flex flex-col h-full bg-dsi-background text-dsi-contrast-analysis p-dsi-pad animate-in fade-in duration-500">

        {/* FIXED TOP SECTION */}
        <div className="shrink-0 text-dsi-contrast-background pb-4 text-sm flex items-center justify-between">
          <h1>
            Showing {displayData.length} of {baseData.length} submissions updated within the last{" "}
            <span className="font-bold">{daysFilter} days</span>
            {type !== "full" && " (or status = DRAFT)."}
          </h1>
          {hasAnyFilter && (
            <button onClick={clearAllFilters} className="flex items-center gap-1 text-xs text-dsi-selected hover:opacity-70 transition-opacity">
              <X className="w-3 h-3" /> Clear filters
            </button>
          )}
        </div>

        {/* SCROLLABLE TABLE AREA */}
        <div className="flex-1 overflow-y-auto no-scrollbar pb-12">
          <table className="w-full text-left whitespace-nowrap border-collapse">

            {/* STICKY HEADER WITH FILTER CONTROLS */}
            <thead className="sticky top-0 z-20 bg-dsi-background">
              {/* Column titles */}
              <tr className="text-dsi-contrast-background font-semibold text-sm uppercase underline">
                <th className="py-3">
                  <ColumnFilterHeader
                    label="Client"
                    filterKey="client"
                    activeFilter={activeFilter}
                    setActiveFilter={setActiveFilter}
                    hasValue={!!clientFilter}
                  />
                </th>
                <th className="py-3 px-2">
                  <ColumnFilterHeader
                    label="Coverage"
                    filterKey="coverage"
                    activeFilter={activeFilter}
                    setActiveFilter={setActiveFilter}
                    hasValue={!!coverageFilter}
                  />
                </th>
                <th className="py-3 px-2 text-center text-wrap">Final Composite Score</th>
                <th className="py-3 px-2 text-center text-wrap">Final Tier</th>
                <th className="py-3 px-2 text-center text-wrap">Recommended Technical Premium</th>
                <th className="py-3 px-2 text-center text-wrap">Recommended Technical Limit</th>
                <th className="py-3 px-2 text-center text-wrap">
                  {type === "full" ? (
                    <ColumnFilterHeader
                      label="Decision"
                      filterKey="decision"
                      activeFilter={activeFilter}
                      setActiveFilter={setActiveFilter}
                      hasValue={!!decisionFilter}
                    />
                  ) : "Quick Actions"}
                </th>
              </tr>

              {/* Filter input row — shown when a filter is active */}
              {activeFilter && (
                <tr className="bg-dsi-analysis/40">
                  <td className="py-1 pr-1">
                    {activeFilter === 'client' && (
                      <input
                        autoFocus
                        type="text"
                        value={clientFilter}
                        onChange={(e) => setClientFilter(e.target.value)}
                        placeholder="Search clients..."
                        className="w-full bg-dsi-background border border-dsi-outline/30 rounded px-2 py-1 text-sm outline-none focus:border-dsi-selected text-dsi-contrast-background"
                      />
                    )}
                  </td>
                  <td className="py-1 px-2">
                    {activeFilter === 'coverage' && (
                      <input
                        autoFocus
                        type="text"
                        value={coverageFilter}
                        onChange={(e) => setCoverageFilter(e.target.value)}
                        placeholder="Search coverage..."
                        className="w-full bg-dsi-background border border-dsi-outline/30 rounded px-2 py-1 text-sm outline-none focus:border-dsi-selected text-dsi-contrast-background"
                      />
                    )}
                  </td>
                  <td colSpan={4}></td>
                  <td className="py-1 px-2">
                    {activeFilter === 'decision' && type === 'full' && (
                      <select
                        autoFocus
                        value={decisionFilter}
                        onChange={(e) => setDecisionFilter(e.target.value)}
                        className="w-full bg-dsi-background border border-dsi-outline/30 rounded px-2 py-1 text-sm outline-none focus:border-dsi-selected text-dsi-contrast-background"
                      >
                        <option value="">All</option>
                        {uniqueDecisions.map(d => (
                          <option key={d} value={d}>{d}</option>
                        ))}
                      </select>
                    )}
                  </td>
                </tr>
              )}
            </thead>

            <tbody>
              {displayData.map((sub: any, index: number) => {
                const premium = sub.recommended_premium || 0;
                const limit = sub.recommended_limit || 0;

                return (
                  <tr
                    key={sub.submission_code || index}
                    onClick={() => handleRowClick(sub)}
                    className="cursor-pointer even:bg-dsi-contrast-analysis text-dsi-contrast-background hover:text-dsi-selected"
                  >
                    <td className="py-3 px-1">{sub.entity_name}</td>
                    <td className="py-3 px-2">{sub.coverage_configuration}</td>
                    <td className="py-3 px-2 text-right">{(sub.final_composite_score ?? 0).toFixed(0)}</td>
                    <td className="py-3 px-2 text-right">{sub.final_tier}</td>
                    <td className="py-3 px-2 text-right">{premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                    <td className="py-3 px-2 text-right">{limit.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>

                    <td className="py-3 px-2">
                      {type === "full" ? (
                        <span className="lowercase">{sub.decision}</span>
                      ) : (
                        <div className="flex items-center justify-center gap-4">
                          <button
                            className="hover:scale-150 transition-transform"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (sub.referral_id) updateDecision(sub.quote_code, "BOUND", "APPROVED");
                            }}
                          >
                            <CircleCheck className="icon" />
                          </button>
                          <span className="opacity-50 text-dsi-contrast-background font-light">/</span>
                          <button
                            className="hover:scale-150 transition-transform"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (sub.referral_id) updateDecision(sub.quote_code, "DECLINED", "DECLINED");
                            }}
                          >
                            <CircleX className="icon" />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {displayData.length === 0 && (
            <div className="text-center py-8 text-dsi-selected opacity-70 italic">
              {hasAnyFilter ? 'No submissions match the current filters.' : 'No submissions found.'}
            </div>
          )}
        </div>
      </div>
    </ViewCanvas>
  );
}

// ─── Column Filter Header ────────────────────────────────────────────────────

function ColumnFilterHeader({ label, filterKey, activeFilter, setActiveFilter, hasValue }: {
  label: string;
  filterKey: string;
  activeFilter: string | null;
  setActiveFilter: (key: string | null) => void;
  hasValue: boolean;
}) {
  const isActive = activeFilter === filterKey;

  return (
    <div className="flex items-center gap-1.5">
      <span>{label}</span>
      <button
        onClick={(e) => {
          e.stopPropagation();
          setActiveFilter(isActive ? null : filterKey);
        }}
        className={`p-0.5 rounded transition-colors ${isActive || hasValue ? 'text-dsi-selected' : 'opacity-30 hover:opacity-70'}`}
        title={`Filter by ${label}`}
      >
        <Filter className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
