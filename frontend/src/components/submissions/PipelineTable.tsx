"use client";

import { useEffect } from "react";
import { Check, X, Loader2 } from "lucide-react";

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
    updateDecision } = useDsiStore();

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
    <ViewCanvas unstyledMain={false}>
      <div className="w-full no-scrollbar">
        <div className="text-dsi-contrast-background pb-4 text-sm">
          <h1>
            Showing submissions updated within the last <span className="font-bold">{daysFilter} days</span> (or status = DRAFT).
          </h1> 
        </div>
        <table className="w-full text-left border-collapse whitespace-nowrap">
          <thead className="sticky top-0 z-10 ">
            <tr className="
              border-b-3 border-dsi-contrast-background 
              text-dsi-contrast-background 
              font-semibold text-sm uppercase
              tracking-wider ">
              <th className="py-3">Client</th>
              <th className="py-3 px-2">Coverage</th>
              <th className="py-3 px-2 text-wrap">Pure Composite Score</th>
              <th className="py-3 px-2 text-center">Tier</th>
              <th className="py-3 px-2 text-center">Gross Premium $</th>
              <th className="py-3 px-2 text-center">Limit $</th>
              <th className="py-3 px-2 text-center">
                {type === "full" ? "Decision" : "Quick Actions"}
              </th>
            </tr>
          </thead>
          <tbody>
            {displayData.map((sub: any, index: number) => {
              // Using the new flat properties from your SQL query
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
                  <td className="py-3 px-2 text-right">${premium.toLocaleString()}</td>
                  <td className="py-3 px-2 text-right">${limit.toLocaleString()}</td>

                  <td className="py-3 px-2">
                    {type === "full" ? 
                    (
                      <span className={`lowercase`}>{sub.decision}</span>
                    ) : (
                      <div className="flex items-center justify-center gap-4">
                        <button 
                          className="text-green-600 dark:text-green-400 hover:scale-125" 
                          onClick={(e) => { 
                            e.stopPropagation(); // Stops the row click from firing!
                            if (sub.referral_id) updateDecision(sub.quote_code, "BOUND", "APPROVED"); 
                          }}
                        >
                          <Check className="icon" />
                        </button>

                        <span className="opacity-50 text-dsi-selected font-light">/</span>

                        <button 
                          className="text-red-600 dark:text-red-400 hover:scale-125" 
                          onClick={(e) => { 
                            e.stopPropagation(); 
                            if (sub.referral_id) updateDecision(sub.quote_code, "DECLINED", "DECLINED"); 
                          }}
                        >
                          <X className="icon" />
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
    </ViewCanvas>
  );
}