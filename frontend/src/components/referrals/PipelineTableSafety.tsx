"use client";

import { useDsiStore } from "@/store/dsiStore";
import { Check, X, Loader2 } from "lucide-react";

export default function PipelineTable({ type }: { type: "full" | "referral" }) {
  const { submissions, isLoading, setActiveMenu, fetchSubmissionDetail } = useDsiStore();

  if (isLoading) {
    return <div className="flex h-full items-center justify-center"><Loader2 className="animate-spin text-dsi-selected w-8 h-8" /></div>;
  }

  // Filter for Referral Pipeline using the new flat 'decision' field
  const displayData = type === "referral" 
    ? submissions.filter(s => s.status === "REFER" || s.decision === "REFER")
    : submissions;

  const handleRowClick = (submissionId: string) => {
    // Triggers the deep fetch for the Workbench using the new submission_id
    fetchSubmissionDetail(submissionId); 
  };

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full text-left border-collapse whitespace-nowrap">
        <thead>
          <tr className="border-b-2 border-dsi-selected text-dsi-selected font-semibold text-sm tracking-wider uppercase">
            <th className="py-3 px-4">Client</th>
            <th className="py-3 px-4">Coverage</th>
            <th className="py-3 px-4 text-wrap">Pure Composite Score</th>
            <th className="py-3 px-4">Tier</th>
            <th className="py-3 px-4 text-right">Gross Premium $</th>
            <th className="py-3 px-4 text-right">Limit $</th>
            <th className="py-3 px-4 text-center">
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
                key={sub.submission_id || index}
                onClick={() => handleRowClick(sub.submission_id)}
                className="
                  cursor-pointer
                  even:bg-dsi-contrast-analysis
                  text-dsi-selected
                  hover:text-dsi-contrast-background"
              >
                <td className="py-3 px-4">{sub.entity_name}</td>
                <td className="py-3 px-4">{sub.coverage_configuration}</td>
                <td className="py-3 px-4 text-right">{sub.pure_composite_score}</td>
                <td className="py-3 px-4 text-right">{sub.final_tier}</td>
                <td className="py-3 px-4 text-right">${premium.toLocaleString()}</td>
                <td className="py-3 px-4 text-right">${limit.toLocaleString()}</td>
                <td className="py-3 px-4">
                  {type === "full" ? 
                  (
                    <span className={`lowercase`}>{sub.decision}</span>
                  ) : (
                    <div className="flex items-center justify-center gap-4">
                      <button className="text-green-600 dark:text-green-400 hover:scale-125" onClick={(e) => e.stopPropagation()}><Check className="icon" /></button>
                      <span className="opacity-50 text-dsi-selected font-light">/</span>
                      <button className="text-red-600 dark:text-red-400 hover:scale-125" onClick={(e) => e.stopPropagation()}><X className="icon" /></button>
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
  );
}