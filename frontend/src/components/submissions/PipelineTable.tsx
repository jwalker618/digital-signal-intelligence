"use client";

import { useEffect, useState, useMemo } from "react";
import { CircleCheck, CircleX, Loader2, Filter, X } from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import { useDsiStore } from "@/store/dsiStore";
import { StatusPill, SubmissionStatusPill } from "@/components/base/content/primatives";
import { DECISION_PALETTE } from "@/lib/keytermPalette";
import { 
  formatText,
  formatCurrency, 
  formatNumber 
} from "@/lib/format";

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
        className="
          p-1.5 gap-1.5
          bg-generate-light-input
          text-generate-text-placeholder text-sm
          hover:text-generate-text-input
          border-t-1 border-b-1 border-generate-text-outline 
          rounded-md"
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
          <Loader2 className="generate-app-icon animate-spin" />
        </div>
      </ViewCanvas>
    );
  }

  return (
    <ViewCanvas unstyledMain={true}>
      
      <div className="w-full no-scrollbar animate-in fade-in duration-500 pb-12 pt-generate-pad">

        {/* FIXED TOP SECTION */}
        <div className="shrink-0 text-generate-text-placeholder pb-4 text-sm flex items-center justify-between">
          <h1>
            Showing {displayData.length} of {baseData.length} submissions updated within the last{" "}
            <span className="font-bold text-generate-text-input">{daysFilter} days</span>
            {type !== "full" && " (or status = DRAFT)."}
          </h1>
          {hasAnyFilter && (
            <div className="group">
              <button onClick={clearAllFilters} className="flex generate-actiontext gap-1">
                <span className="group-hover:text-generate-text-input">Clear filters</span> 
                <X className="generate-app-icon group-hover:text-generate-text-input" /> 
              </button>
            </div>
          )}
        </div>

        {/* SCROLLABLE TABLE AREA */}
        <div className="flex-1 overflow-y-auto no-scrollbar pb-12">
          <table className="w-full text-left whitespace-nowrap border-collapse">

            {/* STICKY HEADER WITH FILTER CONTROLS */}
            <thead className="sticky top-0 z-20">
              {/* Column titles */}
              
              <tr className="generate-grid-table-header">
                
                <th className="p-1.5">
                  <ColumnFilterHeader
                    label="Client"
                    filterKey="client"
                    activeFilter={activeFilter}
                    setActiveFilter={setActiveFilter}
                    hasValue={!!clientFilter}
                  />
                </th>

                <th className="p-1.5">
                  <ColumnFilterHeader
                    label="Coverage"
                    filterKey="coverage"
                    activeFilter={activeFilter}
                    setActiveFilter={setActiveFilter}
                    hasValue={!!coverageFilter}
                  />
                </th>
                <th className="p-1.5">Final Composite Score</th>
                <th className="p-1.5">Final Tier</th>
                <th className="p-1.5">Recommended Technical Premium</th>
                <th className="p-1.5">Recommended Technical Limit</th>
                <th className="p-1.5">
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
                <tr className="bg-generate-light-input border-b-2 border-generate-text-outline">
                  
                  <td className="p-1.5">
                    {activeFilter === 'client' && (
                      <input
                        autoFocus
                        type="text"
                        value={clientFilter}
                        onChange={(e) => setClientFilter(e.target.value)}
                        placeholder="Search clients..."
                        className="generate-light-inputbox w-full"
                      />
                    )}
                  </td>

                  <td className="p-1.5">
                    {activeFilter === 'coverage' && (
                      <input
                        autoFocus
                        type="text"
                        value={coverageFilter}
                        onChange={(e) => setCoverageFilter(e.target.value)}
                        placeholder="Search coverage..."
                        className="generate-light-inputbox w-full"
                      />
                    )}
                  </td>

                  <td className="p-1.5" colSpan={4}></td>

                  <td className="p-1.5">
                    {activeFilter === 'decision' && type === 'full' && (
                      <select
                        autoFocus
                        value={decisionFilter}
                        onChange={(e) => setDecisionFilter(e.target.value)}
                        className="generate-light-inputbox w-full"
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
                return (
                  <tr
                    key={sub.submission_code || index}
                    onClick={() => handleRowClick(sub)}
                    className="cursor-pointer even:bg-generate-light-input text-generate-text-placeholder hover:text-generate-text-input"
                  >
                    <td className="p-1.5">{formatText(sub.entity_name,"upper")}</td>
                    <td className="p-1.5">{formatText(sub.coverage_configuration)}</td>
                    <td className="p-1.5 text-right">{formatNumber(sub.final_composite_score)}</td>
                    <td className="p-1.5 text-right">{sub.final_tier}</td>
                    <td className="p-1.5 text-right">{formatCurrency(sub.recommended_premium,0,"USD")}</td>
                    <td className="p-1.5 text-right">{formatCurrency(sub.recommended_limit,0,"USD")}</td>

                    <td className="p-1.5">
                      {type === "full" ? (
                        
                        <SubmissionStatusPill decision={sub.decision}></SubmissionStatusPill>

                      ) : (
                        <div className="flex items-center justify-center gap-4">
                          <button
                            className="hover:scale-150 transition-transform"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (sub.referral_id) updateDecision(sub.quote_code, "BOUND", "APPROVED");
                            }}
                          >
                            <CircleCheck className="generate-app-icon" />
                          </button>
                          <span className="text-generate-text-placeholder font-light">/</span>
                          <button
                            className="hover:scale-150 transition-transform"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (sub.referral_id) updateDecision(sub.quote_code, "DECLINED", "DECLINED");
                            }}
                          >
                            <CircleX className="generate-app-icon" />
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
            <div className="generate-comment-message">
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
        className={`p-0.5 rounded transition-colors ${isActive || hasValue ? 'text-generate-text-input' : 'text-generate-text-placeholder hover:text-generate-text-input'}`}
        title={`Filter by ${label}`}
      >
        <Filter className="generate-app-icon" />
      </button>
    </div>
  );
}
