"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { GitBranch, GitCommit, Bot, User } from "lucide-react";

export default function ModelVersionsTab() {
  const { activeSubmission, modelVersions, fetchHistory } = useDsiStore();

  useEffect(() => {
    if (activeSubmission?.submission_code) {
      fetchHistory(activeSubmission.submission_code);
    }
  }, [activeSubmission, fetchHistory]);

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12 pt-4">
      <div className="flex items-center gap-3 border-b border-dsi-outline/20 pb-4">
        <GitBranch className="w-5 h-5 text-dsi-selected" />
        <h2 className="text-lg font-bold tracking-wide">Version Lineage</h2>
      </div>

      <div className="space-y-4 relative before:absolute before:inset-0 before:ml-6 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-dsi-outline/20 before:to-transparent">
        {modelVersions.map((mv, i) => (
          <div key={mv.version_id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
            
            {/* Timeline Node */}
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-dsi-background shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow shadow-dsi-background ${mv.is_latest ? 'bg-dsi-selected text-dsi-background' : 'bg-dsi-outline/20 text-dsi-selected'}`}>
              <GitCommit className="w-5 h-5" />
            </div>

            {/* Content Card */}
            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-dsi-outline/20 bg-dsi-background/30 hover:bg-dsi-selected/5 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider opacity-70">Version {mv.version_number}</span>
                {mv.is_latest && <span className="text-[10px] bg-green-500/10 text-green-500 px-2 py-0.5 rounded font-bold uppercase">Active</span>}
              </div>
              
              <div className="flex items-center gap-4 mb-4">
                <div className="flex-1">
                  <div className="text-xs opacity-50 uppercase tracking-wider mb-1">Score</div>
                  <div className="text-xl font-mono font-bold text-dsi-selected">{mv.composite_score?.toFixed(1) || "N/A"}</div>
                </div>
                <div className="flex-1">
                  <div className="text-xs opacity-50 uppercase tracking-wider mb-1">Tier</div>
                  <div className="text-sm font-bold font-mono text-dsi-selected">{mv.tier} ({mv.tier_label})</div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-dsi-outline/10 text-xs font-mono opacity-60">
                <span className="flex items-center gap-1">
                  {mv.created_by === "system" ? <Bot className="w-3 h-3" /> : <User className="w-3 h-3" />}
                  {mv.created_by}
                </span>
                <span>{new Date(mv.created_at).toLocaleString()}</span>
              </div>
            </div>

          </div>
        ))}
      </div>
    </div>
  );
}