"use client";

import { useEffect } from "react";
import { CircleCheck, CircleX, Loader2 } from "lucide-react";

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

  useEffect(() => {
    // Inject a quick filter dropdown into the global Title Bar
    setPageQuickAction(
      <select 
        value={daysFilter}
        onChange={(e) => setDaysFilter(Number(e.target.value))}
        className="
          outline-none
          bg-dsi-background
          text-dsi-contrast-background
          hover:text-dsi-selected"
      >
        <option value={7}>Last 7 Days</option>
        <option value={30}>Last 30 Days</option>
        <option value={90}>Last 90 Days</option>
        <option value={365}>Last 1 Year</option>
      </select>
    );

    // Cleanup when the user leaves the pipeline page
    return () => setPageQuickAction(null);
  }, [daysFilter, setDaysFilter, setPageQuickAction]);

  if (isLoading) {
    return (
      <ViewCanvas unstyledMain={false}>
        <div className="flex h-full items-center justify-center">
          <Loader2 className="animate-spin text-dsi-selected w-8 h-8" />
        </div>
      </ViewCanvas>
    );
  }

  // Filter for Referral Pipeline using the new flat 'decision' field
  const displayData = type === "referral" 
    ? submissions.filter(s => s.decision === "REFER") : submissions;

  const handleRowClick = (sub: any) => {
    fetchCoreSubmissionDetail(sub); 
  };

  return (
    // 1. Switch to unstyledMain so we can control the flex layout directly
    <ViewCanvas unstyledMain={true}>
      
      {/* 2. Parent Flex Column */}
      <div className="
        flex flex-col h-full 
        bg-dsi-background 
        text-dsi-contrast-analysis 
        p-dsi-pad 
        animate-in fade-in duration-500">
        
        {/* 3. FIXED TOP SECTION (Doesn't scroll at all) */}
        <div className="shrink-0 text-dsi-contrast-background pb-4 text-sm">
          <h1>
              Showing submissions updated within the last{" "}
              <span className="font-bold">{daysFilter} days</span>
              {type !== "full" && " (or status = DRAFT)."}
          </h1>
        </div>
        
        {/* 4. SCROLLABLE TABLE AREA */}
        <div className="flex-1 overflow-y-auto no-scrollbar pb-12">
          <table className="w-full text-left whitespace-nowrap border-collapse">
            
            {/* 5. STICKY HEADER WITH SOLID BACKGROUND */}
            <thead className="
              sticky top-0 z-20 
              bg-dsi-background"
              >
              <tr className="
                text-dsi-contrast-background font-semibold text-sm uppercase underline"
                >
                <th className="py-3">Client</th>
                <th className="py-3 px-2">Coverage</th>
                <th className="py-3 px-2 text-wrap">Pure Composite Score</th>
                <th className="py-3 px-2 text-center">Tier</th>
                <th className="py-3 px-2 text-center">Gross Premium</th>
                <th className="py-3 px-2 text-center">Limit</th>
                <th className="py-3 px-2 text-center">
                  {type === "full" ? "Decision" : "Quick Actions"}
                </th>
              </tr>
            </thead>
            
            <tbody>
              {displayData.map((sub: any, index: number) => {
                const premium = sub.recommended_premium || 0;
                const limit = sub.recommended_limit || 0;

                return (
                  <tr 
                    key={sub.submission_code || index}
                    onClick={() => handleRowClick(sub)}
                    className="
                      cursor-pointer
                      even:bg-dsi-contrast-analysis
                      text-dsi-contrast-background 
                      hover:text-dsi-selected"
                  >
                    <td className="py-3 px-1">{sub.entity_name}</td>
                    <td className="py-3 px-2">{sub.coverage_configuration}</td>
                    <td className="py-3 px-2 text-right">{sub.pure_composite_score.toFixed(0)}</td>
                    <td className="py-3 px-2 text-right">{sub.final_tier}</td>
                    <td className="py-3 px-2 text-right">{premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                    <td className="py-3 px-2 text-right">{limit.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>

                    <td className="py-3 px-2">
                      {type === "full" ? 
                      (
                        <span className={`lowercase`}>{sub.decision}</span>
                      ) : (
                        <div className="flex items-center justify-center gap-4">
                          <button 
                            className= "hover:scale-150 transition-transform" 
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
            <div className="text-center py-8 text-dsi-selected opacity-70 italic">No submissions found.</div>
          )}
        </div>
      </div>
    </ViewCanvas>
  );
}