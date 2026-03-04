"use client";

import { useDsiStore } from "@/store/dsiStore";
import { Check, X, Loader2 } from "lucide-react";

export default function PipelineTable({ type }: { type: "full" | "referral" }) {
  const { submissions, isLoading, setActiveMenu, setActiveSubmission } = useDsiStore();

  if (isLoading) {
    return <div className="flex h-full items-center justify-center"><Loader2 className="animate-spin text-dsi-selected w-8 h-8" /></div>;
  }

  // Filter for Referral Pipeline if needed
  const displayData = type === "referral" 
    ? submissions.filter(s => s.status === "refer" || s.quotes?.[0]?.decision === "refer")
    : submissions;

  const handleRowClick = (submissionId: string) => {
    setActiveSubmission(submissionId);
    setActiveMenu("Workbench"); // Routes to the specific analysis screen
  };

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full text-left border-collapse whitespace-nowrap">
        <thead>
          <tr className="border-b-2 border-dsi-selected text-dsi-selected font-semibold text-sm tracking-wider uppercase">
            <th className="py-3 px-4">Client</th>
            <th className="py-3 px-4">Coverage</th>
            <th className="py-3 px-4">Renewal</th>
            <th className="py-3 px-4">Tier (Of)</th>
            <th className="py-3 px-4 text-right">Gross Premium $</th>
            <th className="py-3 px-4 text-right">Limit $</th>
            <th className="py-3 px-4 text-center">
              {type === "full" ? "Decision" : "Quick Actions"}
            </th>
          </tr>
        </thead>
        <tbody>
          {displayData.map((sub: any, index: number) => {
            const quote = sub.quotes?.[0] || {};
            const tier = quote.tier || "?";
            const decision = quote.decision || sub.status || "pending";
            const premium = quote.recommended_premium || 0;
            const limit = sub.limit_amount || 0
            const coverage = sub.coverage ? sub.coverage.replace("_", " ") : "Unknown";

            return (
              <tr 
                key={sub.id || index}
                onClick={() => handleRowClick(sub.id)}
                className="cursor-pointer transition-colors border-b border-dsi-outline/10 text-dsi-selected hover:bg-dsi-selected hover:text-dsi-background even:bg-dsi-contrast-analysis/20"
              >
                <td className="py-3 px-4 font-medium">{sub.entity_name}</td>
                <td className="py-3 px-4 capitalize">{coverage}</td>
                <td className="py-3 px-4">No</td>
                <td className="py-3 px-4">{tier} (5)</td>
                <td className="py-3 px-4 text-right font-mono">${premium.toLocaleString()}</td>
                <td className="py-3 px-4 text-right font-mono">${limit.toLocaleString()}</td>
                <td className="py-3 px-4 text-center">
                  {type === "full" ? (
                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider ${
                      decision === 'approve' ? 'text-green-600 dark:text-green-400' : 
                      decision === 'refer' ? 'text-yellow-600 dark:text-yellow-400' : 
                      'text-red-600 dark:text-red-400'
                    }`}>
                      {decision}
                    </span>
                  ) : (
                    <div className="flex items-center justify-center gap-4">
                      <button className="text-green-600 dark:text-green-400 hover:scale-125 transition-transform" onClick={(e) => e.stopPropagation()}><Check className="w-5 h-5" /></button>
                      <span className="opacity-50 text-dsi-selected font-light">/</span>
                      <button className="text-red-600 dark:text-red-400 hover:scale-125 transition-transform" onClick={(e) => e.stopPropagation()}><X className="w-5 h-5" /></button>
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