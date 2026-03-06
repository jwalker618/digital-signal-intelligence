"use client";

import { useEffect, useState } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { ShieldAlert, Edit3, Check, X, AlertTriangle, ArrowRight } from "lucide-react";

export default function ReferralTab() {
  const { 
    activeSubmission, 
    referralSignals, 
    fetchReferralSignals, 
    submitSignalOverride,
    updateDecision,
    navigateBack
  } = useDsiStore();

  const [overrideModal, setOverrideModal] = useState<{ isOpen: boolean; signal: any } | null>(null);
  const [auditedValue, setAuditedValue] = useState<string>("");
  const [rationale, setRationale] = useState<string>("");

  // Fetch signals when the tab mounts
  useEffect(() => {
    if (activeSubmission?.referral_id) {
      fetchReferralSignals(activeSubmission.referral_id);
    }
  }, [activeSubmission, fetchReferralSignals]);

  if (!activeSubmission) return null;

  const handleOverrideSubmit = async () => {
    if (!overrideModal || !activeSubmission.referral_id) return;
    await submitSignalOverride(
      activeSubmission.referral_id, 
      overrideModal.signal.signal_id, 
      parseFloat(auditedValue), 
      rationale
    );
    setOverrideModal(null);
    setAuditedValue("");
    setRationale("");
  };

  const handleFinalDecision = async (decision: string) => {
    if (!activeSubmission.referral_id) return;
    await updateDecision(activeSubmission.referral_id, decision);
    navigateBack(); // Pop back out to the pipeline once resolved!
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12 pt-4">
      
      {/* 1. WHY WAS IT REFERRED? */}
      <div className="p-4 border border-red-500/30 bg-red-500/5 rounded-xl flex items-start gap-4">
        <ShieldAlert className="w-6 h-6 text-red-500 shrink-0 mt-1" />
        <div>
          <h3 className="text-lg font-bold text-red-500">Referral Triggers</h3>
          <ul className="list-disc ml-5 mt-2 space-y-1 text-sm font-mono opacity-80">
            {activeSubmission.referral_reasons?.map((reason: string, i: number) => (
              <li key={i}>{reason}</li>
            )) || <li>Manual Underwriter Referral</li>}
          </ul>
        </div>
      </div>

      {/* 2. THE SIGNAL AUDIT GRID */}
      <div className="border border-dsi-outline/20 rounded-xl overflow-hidden bg-dsi-background/30">
        <div className="px-4 py-3 border-b border-dsi-outline/20 bg-dsi-selected/5 flex justify-between items-center">
          <h3 className="font-semibold tracking-wide text-sm uppercase">Signal Audit Matrix</h3>
          <span className="text-xs font-mono opacity-60">Model Version: {activeSubmission.model_version_id}</span>
        </div>
        
        <div className="overflow-x-auto w-full">
          <table className="w-full text-left border-collapse whitespace-nowrap text-sm">
            <thead>
              <tr className="border-b border-dsi-outline/20 text-dsi-selected font-semibold uppercase tracking-wider text-xs bg-dsi-background/50">
                <th className="py-3 px-4">Signal Name</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4 text-right">Inferred Value</th>
                <th className="py-3 px-4 text-right">Audited Value</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody>
              {referralSignals.map((sig: any, idx: number) => (
                <tr key={idx} className={`border-b border-dsi-outline/10 hover:bg-dsi-selected/5 transition-colors ${sig.is_flagged ? 'bg-yellow-500/5' : ''}`}>
                  <td className="py-3 px-4 font-mono">
                    <div className="flex items-center gap-2">
                      {sig.is_flagged && <AlertTriangle className="w-4 h-4 text-yellow-500" />}
                      {sig.signal_name.replace(/_/g, ' ')}
                    </div>
                  </td>
                  <td className="py-3 px-4 opacity-70">{sig.group_name}</td>
                  <td className="py-3 px-4 text-right font-mono text-dsi-selected">{sig.inferred_value}</td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-green-500">
                    {sig.is_overridden ? sig.audited_value : "—"}
                  </td>
                  <td className="py-3 px-4 text-center">
                    {sig.is_overridden 
                      ? <span className="text-xs bg-green-500/10 text-green-500 px-2 py-1 rounded uppercase font-bold">Overridden</span>
                      : sig.is_flagged 
                      ? <span className="text-xs bg-yellow-500/10 text-yellow-500 px-2 py-1 rounded uppercase font-bold">Flagged</span>
                      : <span className="text-xs opacity-50 uppercase tracking-wider">Accepted</span>
                    }
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button 
                      onClick={() => { setOverrideModal({ isOpen: true, signal: sig }); setAuditedValue(sig.inferred_value); }}
                      className="p-1.5 hover:bg-dsi-selected/10 rounded text-dsi-selected transition-colors"
                    >
                      <Edit3 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. FINAL DECISION ACTIONS */}
      {activeSubmission.decision === "refer" && (
        <div className="flex items-center justify-end gap-4 pt-6 border-t border-dsi-outline/20">
          <button 
            onClick={() => handleFinalDecision("decline")}
            className="flex items-center gap-2 px-6 py-2 border border-red-500/50 text-red-500 rounded font-semibold hover:bg-red-500/10 transition-colors"
          >
            <X className="w-5 h-5" /> Decline Risk
          </button>
          <button 
            onClick={() => handleFinalDecision("approve")}
            className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded font-semibold hover:bg-green-500 transition-colors shadow-lg"
          >
            <Check className="w-5 h-5" /> Approve & Bind
          </button>
        </div>
      )}

      {/* 4. OVERRIDE MODAL */}
      {overrideModal?.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-dsi-contrast-background/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-dsi-background border border-dsi-outline rounded-2xl shadow-2xl flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b border-dsi-outline/20 bg-dsi-selected/5">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <Edit3 className="w-5 h-5" /> Audit Signal
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between font-mono text-sm opacity-70 mb-6">
                <span>{overrideModal.signal.signal_name}</span>
                <span className="bg-dsi-selected/10 px-2 rounded">Conf: {(overrideModal.signal.confidence * 100).toFixed(0)}%</span>
              </div>
              
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1">
                  <label className="text-xs uppercase tracking-wider opacity-70">Inferred Value</label>
                  <input type="text" disabled value={overrideModal.signal.inferred_value} className="w-full mt-1 p-2 bg-dsi-background/50 border border-dsi-outline/20 rounded font-mono text-dsi-selected opacity-50" />
                </div>
                <ArrowRight className="w-6 h-6 mt-5 opacity-50" />
                <div className="flex-1">
                  <label className="text-xs uppercase tracking-wider opacity-70 text-dsi-selected font-bold">Audited Value</label>
                  <input 
                    type="number" 
                    autoFocus
                    value={auditedValue} 
                    onChange={(e) => setAuditedValue(e.target.value)} 
                    className="w-full mt-1 p-2 bg-dsi-background border-2 border-dsi-selected/50 rounded font-mono text-dsi-selected focus:outline-none focus:border-dsi-selected" 
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
            
            <div className="px-6 py-4 border-t border-dsi-outline/20 flex items-center justify-end gap-3 bg-dsi-selected/5">
              <button onClick={() => setOverrideModal(null)} className="px-4 py-2 rounded text-sm font-semibold opacity-70 hover:opacity-100">Cancel</button>
              <button 
                onClick={handleOverrideSubmit}
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