"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { GitBranch, GitCommit, Bot, User, Paperclip } from "lucide-react";

export default function ModelVersionsTab() {
  const { activeSubmission, activeQuote, modelVersions, fetchHistory } = useDsiStore();

  useEffect(() => {
    if (activeSubmission?.submission_code) {
      fetchHistory(activeSubmission.submission_code);
    }
  }, [activeSubmission, fetchHistory]);

  return (
    <div className="
      w-full no-scrollbar 
      animate-in fade-in duration-500 pb-12"
      >
      {/* STICKY WRAPPER: Acts as a solid curtain to hide scrolling content */}
      <div className="
        sticky top-0 z-20 
        bg-dsi-background 
        pt-3 pb-2"
        >  

        {/* SECTION HEADER */}
        <div className="
          flex gap-dsi-pad
          rounded-t-xl
          border-b-1 border-dsi-outline/50
          overflow-x-hidden whitespace-nowrap border-collapse
          bg-dsi-analysis/60
          pl-dsi-pad
          pt-2 pb-2    
        "
        >
          <Paperclip className="icon"/><span className="text-sm">Key Details</span>
        </div>

        {/* KEY INFORMATION CARD */}
        <div className="
          grid grid-cols-[10%_35%_55%] grid-rows-1
          border-b-3 border-dsi-contrast-background
          overflow-x-hidden whitespace-nowrap border-collapse
          rounded-b-xl
          bg-dsi-analysis shadow-sm
          pt-2 pb-2" 
        >  
          <div className="text-left pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            <span className="text-sm">Status:</span><span className="pl-2 uppercase font-bold">{activeQuote.status}</span>
          </div>
          
          <div className="text-center pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            {(activeQuote.status === 'draft' || activeQuote.status === 'ready') && (
              <span className="">
                <span className="text-sm">Quote Valid From:</span><span className="pl-2 uppercase font-bold">{new Date(activeQuote.valid_from).toLocaleDateString()};</span>
                <span className="pl-2 pr-2"> </span>
                <span className="text-sm">Until:</span><span className="pl-2 uppercase font-bold">{new Date(activeQuote.valid_until).toLocaleDateString()}</span>
              </span>
            )}
            {activeQuote.status === 'bound' && (
              <span className="">
                  <span className="text-sm">Bound Date:</span><span className="pl-2 uppercase font-bold">{activeQuote.bound_at ? new Date(activeQuote.bound_at).toLocaleDateString() : 'N/A'}</span>
                  <span className="text-sm">Policy Reference:</span><span className="pl-2 uppercase font-bold">{activeQuote.policy_number || 'Pending'}</span>
              </span>
            )}
          </div>
          
          <div className="text-center pl-dsi-pad pr-dsi-pad overflow-x-hidden">
            <span className="text-sm">Submission Code: </span><span className="pl-2 uppercase font-bold">{activeSubmission.submission_code}</span>
            <span className="pl-6 pr-6">||</span>
            <span className="text-sm">Quote Code: </span><span className="pl-2 uppercase font-bold">{activeQuote.quote_code}</span>
          </div>

        </div>
      </div>

      <div className="flex flex-col pt-2 pb-2">
        <div className="
          flex gap-dsi-pad
          rounded-t-xl
          border-b-1 border-dsi-outline/50
          overflow-x-hidden whitespace-nowrap border-collapse
          bg-dsi-analysis/60
          pl-dsi-pad
          pt-2 pb-2    
        ">
          <GitBranch className="icon"/><span className="text-sm">Version Lineage</span>
        </div>
        <div className="
          flex flex-col flex-1
          border-b-3 border-dsi-contrast-background
          overflow-x-hidden border-collapse
          rounded-b-xl
          bg-dsi-analysis shadow-sm
          pt-6 pb-6
        ">
          <div className="pl-dsi-pad pr-dsi-pad space-y-4 relative before:absolute before:inset-0 before:ml-6 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-dsi-outline/20 before:to-transparent">
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
                      <div className="text-xl font-bold text-dsi-selected">{mv.composite_score?.toFixed(1) || "N/A"}</div>
                    </div>
                    <div className="flex-1">
                      <div className="text-xs opacity-50 uppercase tracking-wider mb-1">Tier</div>
                      <div className="text-sm font-bold text-dsi-selected">{mv.tier} ({mv.tier_label})</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-dsi-outline/10 text-xs opacity-60">
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
      </div>
    </div>
  );
}