"use client";

import { useEffect, useState } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { ShieldAlert, Edit3, Check, X, AlertTriangle, ArrowRight, Layers, Eye, Flame, Paperclip } from "lucide-react";

export default function ReferralTab() {
  const {
    activeSubmission,
    activeQuote,
    activeVersion,
    activeReferral,
    referralSignals,
    fetchReferralSignals,
    submitSignalOverride,
    updateDecision,
    navigateBack
  } = useDsiStore();

  const [overrideModal, setOverrideModal] = useState<{ isOpen: boolean; signal: any } | null>(null);
  const [auditedValue, setAuditedValue] = useState<string>("");
  const [rationale, setRationale] = useState<string>("");
  const [showAllSignals, setShowAllSignals] = useState(false);

  useEffect(() => {
    if (activeSubmission?.model_version_id) {
      fetchReferralSignals(activeSubmission.model_version_id);
    }
  }, [activeSubmission, fetchReferralSignals]);

  if (!activeSubmission) return null;

  const handleOverride = async () => {
    // Make sure we have the required IDs before submitting
    if (!overrideModal?.signal) return;
    await submitSignalOverride(
        activeQuote.quote_id,      
        overrideModal.signal.signal_id,  
        auditedValue, 
        rationale
    );
    setOverrideModal(null); // Close modal on success
  };

  const handleFinalDecision = async (decision: string) => {
    if (!activeSubmission.referral_id) return;
    await updateDecision(activeSubmission.referral_id, decision);
    navigateBack(); 
  };

  const modelSignals = referralSignals.filter((s: any) => s.in_model !== false);
  const cacheOnlySignals = referralSignals.filter((s: any) => s.in_model === false);
  const displayedSignals = showAllSignals ? referralSignals : modelSignals;

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

      {/* 1. WHY WAS IT REFERRED? */}
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
          <ShieldAlert className="icon text-rose-500"/><span className="text-sm">Referral Triggers</span>
        </div>
        <div className="
          flex flex-col flex-1
          border-b-3 border-dsi-contrast-background
          overflow-x-hidden whitespace-nowrap border-collapse
          rounded-b-xl
          bg-dsi-analysis shadow-sm
          pt-4 pb-4
        ">
          <ul className="list-disc pl-10 pr-dsi-pad space-y-1 text-sm opacity-80 text-wrap">
            {activeSubmission.referral_reasons?.map((reason: string, i: number) => (
              <li key={i}>{reason}</li>
            )) || <li>Manual Underwriter Referral</li>}
          </ul>
        </div>
      </div>

      {/* 2. THE SIGNAL AUDIT GRID */}
      <div className="flex flex-col pt-2 pb-2">
        <div className="
          flex justify-between items-center gap-dsi-pad
          rounded-t-xl
          border-b-1 border-dsi-outline/50
          overflow-x-hidden whitespace-nowrap border-collapse
          bg-dsi-analysis/60
          pl-dsi-pad pr-dsi-pad
          pt-2 pb-2    
        ">
          <div className="flex items-center gap-dsi-pad">
            <Layers className="icon"/><span className="text-sm">Signal Audit Matrix</span>
            <span className="text-xs opacity-60 ml-4">
              ({modelSignals.length} in model)
            </span>
          </div>
          
          {cacheOnlySignals.length > 0 && (
            <button
              onClick={() => setShowAllSignals(!showAllSignals)}
              className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded transition-colors ${
                showAllSignals
                  ? "bg-dsi-selected/20 text-dsi-selected"
                  : "opacity-50 hover:opacity-80"
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              {showAllSignals ? "Showing all signals" : "Show all cached signals"}
            </button>
          )}
        </div>

        <div className="
          flex flex-col flex-1
          border-b-3 border-dsi-contrast-background
          overflow-x-auto whitespace-nowrap border-collapse
          rounded-b-xl
          bg-dsi-analysis shadow-sm
          pt-2 pb-4
        ">
          <table className="w-full text-left border-collapse whitespace-nowrap text-sm">
            <thead>
              <tr className="text-center text-sm underline opacity-70">
                <th colSpan={3} className="font-normal border-r border-dsi-outline/10 py-2">Signal Identification</th>
                <th colSpan={4} className="font-normal border-r border-dsi-outline/10 py-2">Machine Inferred (Cache)</th>
                <th colSpan={4} className="font-normal py-2 text-dsi-selected">Underwriter Audit (Phase 8)</th>
              </tr>
              <tr className="border-b-1 border-dsi-outline/50 text-xs opacity-70">
                <th className="py-2 pl-dsi-pad pr-dsi-pad font-normal text-left">Signal Name</th>
                <th className="py-2 px-2 font-normal text-center">Proxy Tier</th>
                <th className="py-2 px-2 font-normal text-center border-r border-dsi-outline/10">Absent</th>
                
                <th className="py-2 px-2 font-normal text-right">Inferred Val</th>
                <th className="py-2 px-2 font-normal text-right">Conf</th>
                <th className="py-2 px-2 font-normal text-right">Weight</th>
                <th className="py-2 px-2 font-normal text-right border-r border-dsi-outline/10">Contrib</th>

                <th className="py-2 px-2 font-normal text-right">Audited Val</th>
                <th className="py-2 pl-dsi-pad pr-dsi-pad font-normal">Rationale</th>
                <th className="py-2 px-2 font-normal text-center">Impact</th>
                <th className="py-2 px-2 font-normal text-center">Action</th>
              </tr>
            </thead>
            
            <tbody>
              {displayedSignals.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-8 text-center text-dsi-selected opacity-50 text-sm">
                    No signal data found for this model version.
                  </td>
                </tr>
              ) : (
                [...displayedSignals]
                  .sort((a, b) => Math.abs(b.contribution_to_score || 0) - Math.abs(a.contribution_to_score || 0))
                  .map((sig: any, idx: number) => {
                    const isHighImpact = idx < 3 && Math.abs(sig.contribution_to_score) > 10;

                    return (
                      <tr key={idx} className={`border-b border-dsi-outline/5 hover:bg-dsi-background/20 transition-colors ${sig.is_flagged && !sig.is_overridden ? 'bg-rose-500/5' : ''} ${sig.is_overridden ? 'bg-emerald-500/5' : ''}`}>
                        
                        <td className="py-2 pl-dsi-pad pr-dsi-pad text-sm">
                          <div className="flex items-center gap-2">
                            {isHighImpact && <Flame className="w-3.5 h-3.5 text-orange-500 shrink-0" title="High Impact Signal" />}
                            {sig.is_flagged && !sig.is_overridden && !isHighImpact && <AlertTriangle className="w-3.5 h-3.5 text-yellow-500 shrink-0" />}
                            {sig.is_overridden && <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" />}
                            <span className={`truncate max-w-[180px] ${isHighImpact ? 'text-orange-400 font-bold' : ''}`} title={sig.signal_name}>
                              {sig.signal_name.replace(/_/g, ' ')}
                            </span>
                          </div>
                        </td>
                        <td className="py-2 px-2 text-center text-xs opacity-70">{sig.proxy_tier || "—"}</td>
                        <td className="py-2 px-2 text-center border-r border-dsi-outline/10">
                          {sig.was_absent ? <span className="text-rose-400 font-bold">YES</span> : <span className="opacity-30">NO</span>}
                        </td>

                        <td className="py-2 px-2 text-right flex flex-col items-end">
                          <span className={`font-bold ${sig.is_overridden ? 'text-emerald-500' : ''}`}>
                            {sig.score?.toFixed(2)}
                          </span>
                          {sig.is_overridden && (
                            <span className="text-[10px] line-through opacity-50">
                              {sig.inferred_value?.toFixed(2)}
                            </span>
                          )}
                        </td>
                        <td className={`py-2 px-2 text-right text-xs ${sig.confidence < 0.7 ? 'text-yellow-500 font-bold' : 'opacity-70'}`}>
                          {(sig.confidence * 100).toFixed(0)}%
                        </td>
                        
                        <td className={`py-2 px-2 text-right text-xs ${isHighImpact ? 'font-bold' : 'opacity-70'}`}>
                          {sig.weight?.toFixed(2)}
                        </td>
                        <td className={`py-2 px-2 text-right text-xs border-r border-dsi-outline/10 ${isHighImpact ? 'font-bold text-orange-400' : 'opacity-70'}`}>
                          {sig.contribution_to_score > 0 ? '+' : ''}{sig.contribution_to_score?.toFixed(1)}
                        </td>

                        <td className="py-2 px-2 text-right font-bold text-emerald-500">
                          {sig.is_overridden ? sig.audited_value?.toFixed(2) : "—"}
                        </td>
                        <td className="py-2 pl-dsi-pad pr-dsi-pad text-xs opacity-80 truncate max-w-[150px]" title={sig.override_rationale}>
                          {sig.override_rationale || "—"}
                        </td>
                        <td className="py-2 px-2 text-center text-xs">
                          {sig.score_impact ? (
                            <span className={`px-1.5 py-0.5 rounded font-bold ${sig.score_impact > 0 ? 'bg-rose-500/10 text-rose-500' : 'bg-emerald-500/10 text-emerald-500'}`}>
                              {sig.score_impact > 0 ? '+' : ''}{sig.score_impact.toFixed(1)}
                            </span>
                          ) : "—"}
                        </td>
                        <td className="py-2 px-2 text-center">
                          <button 
                            onClick={() => { setOverrideModal({ isOpen: true, signal: sig }); setAuditedValue(sig.inferred_value); }}
                            className="p-1 hover:text-dsi-selected transition-colors"
                            title="Audit Signal"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. FINAL DECISION ACTIONS */}
      {activeSubmission.decision === "refer" && (
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
            <Check className="icon"/><span className="text-sm">Final Decision Actions</span>
          </div>
          <div className="
            flex flex-row items-center justify-end gap-4
            border-b-3 border-dsi-contrast-background
            overflow-x-hidden whitespace-nowrap border-collapse
            rounded-b-xl
            bg-dsi-analysis shadow-sm
            pt-4 pb-4 pl-dsi-pad pr-dsi-pad
          ">
            <button
              onClick={() => handleFinalDecision("decline")}
              className="flex items-center gap-2 px-6 py-2 border border-rose-500/50 text-rose-500 rounded font-semibold hover:bg-rose-500/10 transition-colors"
            >
              <X className="w-5 h-5" /> Decline Risk
            </button>
            <button
              onClick={() => handleFinalDecision("approve")}
              className="flex items-center gap-2 px-6 py-2 bg-emerald-600 text-white rounded font-semibold hover:bg-emerald-500 transition-colors"
            >
              <Check className="w-5 h-5" /> Approve & Bind
            </button>
          </div>
        </div>
      )}

      {/* OVERRIDE MODAL (Kept identical layout but ensuring z-index stays high) */}
      {overrideModal?.isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-dsi-contrast-background/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-dsi-background border border-dsi-outline rounded-2xl shadow-2xl flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b border-dsi-outline/20 bg-dsi-analysis/60">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <Edit3 className="w-5 h-5" /> Audit Signal
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between text-sm opacity-70 mb-6">
                <span>{overrideModal.signal.signal_name}</span>
                <span className="bg-dsi-selected/10 px-2 rounded">Conf: {(overrideModal.signal.confidence * 100).toFixed(0)}%</span>
              </div>

              <div className="flex items-center justify-between gap-4">
                <div className="flex-1">
                  <label className="text-xs uppercase tracking-wider opacity-70">Inferred Value</label>
                  <input type="text" disabled value={overrideModal.signal.inferred_value} className="w-full mt-1 p-2 bg-dsi-background/50 border border-dsi-outline/20 rounded text-dsi-selected opacity-50" />
                </div>
                <ArrowRight className="w-6 h-6 mt-5 opacity-50" />
                <div className="flex-1">
                  <label className="text-xs uppercase tracking-wider opacity-70 text-dsi-selected font-bold">Audited Value</label>
                  <input
                    type="number"
                    autoFocus
                    value={auditedValue}
                    onChange={(e) => setAuditedValue(e.target.value)}
                    className="w-full mt-1 p-2 bg-dsi-background border-2 border-dsi-selected/50 rounded text-dsi-selected focus:outline-none focus:border-dsi-selected"
                  />
                </div>
              </div>

              <div className="pt-4">
                <label className="text-xs uppercase tracking-wider opacity-70">Audit Rationale</label>
                <textarea
                  rows={3}
                  value={rationale}
                  onChange={(e) => setRationale(e.target.value)}
                  placeholder="Required: Provide context or evidence reference for this change..."
                  className="w-full mt-1 p-2 bg-dsi-background border border-dsi-outline/30 rounded text-sm text-dsi-selected focus:outline-none focus:border-dsi-selected resize-none"
                />
              </div>
            </div>

            <div className="px-6 py-4 border-t border-dsi-outline/20 flex items-center justify-end gap-3 bg-dsi-analysis/60">
              <button onClick={() => setOverrideModal(null)} className="px-4 py-2 rounded text-sm font-semibold opacity-70 hover:opacity-100">Cancel</button>
              <button
                onClick={handleOverride}
                disabled={!auditedValue || !rationale}
                className="px-4 py-2 bg-dsi-selected text-dsi-background rounded text-sm font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Apply Override
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}