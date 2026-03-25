"use client";

import { useEffect, useState, useMemo } from "react";
import { useDsiStore } from "@/store/dsiStore";
import {
  ShieldAlert, Edit3, Check, X, AlertTriangle, ArrowRight,
  Layers, Eye, Flame, Paperclip, Clock, User,
  ChevronDown, ChevronRight
} from "lucide-react";
import { formatNum } from "@/lib/format";

const ACTION_COLORS: Record<string, { bg: string; text: string }> = {
  modifier:      { bg: 'bg-dsi-info/15', text: 'text-dsi-info' },
  referral:      { bg: 'bg-dsi-warning/15', text: 'text-dsi-warning' },
  refer:         { bg: 'bg-dsi-warning/15', text: 'text-dsi-warning' },
  tier_override: { bg: 'bg-dsi-negative/15', text: 'text-dsi-negative' },
  flag:          { bg: 'bg-dsi-muted/15', text: 'text-dsi-muted' },
  note:          { bg: 'bg-dsi-muted/15', text: 'text-dsi-muted' },
};

export default function ReferralTab() {
  const {
    activeSubmission,
    activeQuote,
    activeVersion,
    activeReferral,
    riskSignals,
    isFetchingRiskSignals,
    fetchRiskSignals,
    submitSignalOverride,
    updateDecision,
    navigateBack
  } = useDsiStore();

  const [overrideModal, setOverrideModal] = useState<{ isOpen: boolean; signal: any } | null>(null);
  const [auditedValue, setAuditedValue] = useState<string>("");
  const [rationale, setRationale] = useState<string>("");
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});

  // G1: Use fetchRiskSignals with version_code instead of broken fetchReferralSignals
  useEffect(() => {
    if (activeVersion?.version_code) {
      fetchRiskSignals(activeVersion.version_code);
    }
  }, [activeVersion?.version_code, fetchRiskSignals]);

  const toggleGroup = (g: string) => setExpandedGroups(p => ({ ...p, [g]: !p[g] }));

  if (!activeSubmission || !activeVersion) return null;

  const handleOverride = async () => {
    if (!overrideModal?.signal) return;
    await submitSignalOverride(
        activeQuote?.quote_code,
        overrideModal.signal.code || overrideModal.signal.signal_id,
        auditedValue,
        rationale
    );
    setOverrideModal(null);
    setAuditedValue("");
    setRationale("");
  };

  const handleFinalDecision = async (decision: string) => {
    if (!activeQuote?.quote_code) return;
    await updateDecision(activeQuote.quote_code, decision);
    navigateBack();
  };

  // Group signals for accordion
  const signalsByGroup = useMemo(() => {
    const map: Record<string, any[]> = {};
    for (const sig of (riskSignals || [])) {
      const g = sig.group_code || 'ungrouped';
      if (!map[g]) map[g] = [];
      map[g].push(sig);
    }
    for (const g of Object.keys(map)) {
      map[g].sort((a: any, b: any) => Math.abs(b.contribution || 0) - Math.abs(a.contribution || 0));
    }
    return map;
  }, [riskSignals]);

  const groupScores = activeVersion?.group_scores || {};
  const groupEntries = Object.entries(groupScores).sort(([, a]: any, [, b]: any) => (b?.risk_contribution || 0) - (a?.risk_contribution || 0));

  // Counts
  const overrideCount = (riskSignals || []).filter((s: any) => s.is_overridden).length;
  const flaggedCount = (riskSignals || []).filter((s: any) => s.is_flagged && !s.is_overridden).length;
  const totalSignals = (riskSignals || []).length;

  // Referral-triggering conditions
  const signalConditions = activeVersion?.signal_conditions || [];
  const queryConditions = activeVersion?.query_conditions || [];
  const referralConditions = useMemo(() => {
    return [...signalConditions, ...queryConditions].filter((c: any) => {
      const action = typeof c.action === 'string' ? c.action.toLowerCase() : (c.action?.value || '');
      return action === 'referral' || action === 'refer';
    });
  }, [signalConditions, queryConditions]);

  const reasons = activeSubmission?.referral_reasons || activeVersion?.referral_reasons || [];

  return (
    <div className="w-full no-scrollbar animate-in fade-in duration-500 pb-12">

      {/* STICKY HEADER */}
      <div className="sticky top-0 z-20 bg-dsi-background pt-3 pb-2">
        <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
          <Paperclip className="icon"/><span className="text-sm">Key Details</span>
        </div>
        <div className="grid grid-cols-[10%_35%_55%] grid-rows-1 border-b-3 border-dsi-contrast-background overflow-x-hidden whitespace-nowrap border-collapse rounded-b-xl bg-dsi-analysis shadow-sm pt-2 pb-2">
          <div className="text-left pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            <span className="text-sm">Status:</span><span className="pl-2 uppercase font-bold">{activeQuote?.status}</span>
          </div>
          <div className="text-center pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
            {(activeQuote?.status === 'draft' || activeQuote?.status === 'ready') && (
              <span>
                <span className="text-sm">Quote Valid From:</span><span className="pl-2 uppercase font-bold">{activeQuote?.valid_from ? new Date(activeQuote.valid_from).toLocaleDateString() : 'N/A'};</span>
                <span className="pl-2 pr-2"> </span>
                <span className="text-sm">Until:</span><span className="pl-2 uppercase font-bold">{activeQuote?.valid_until ? new Date(activeQuote.valid_until).toLocaleDateString() : 'N/A'}</span>
              </span>
            )}
          </div>
          <div className="text-center pl-dsi-pad pr-dsi-pad overflow-x-hidden">
            <span className="text-sm">Submission Code: </span><span className="pl-2 uppercase font-bold">{activeSubmission?.submission_code}</span>
            <span className="pl-6 pr-6">||</span>
            <span className="text-sm">Quote Code: </span><span className="pl-2 uppercase font-bold">{activeQuote?.quote_code}</span>
          </div>
        </div>
      </div>

      {/* REFERRAL CONTEXT HEADER */}
      <div className="flex items-stretch gap-4 rounded-xl border-2 border-dsi-warning/30 bg-dsi-warning/5 px-dsi-pad py-4 mt-2 mb-4">
        <div className="flex items-center gap-3 pr-6 border-r border-dsi-warning/20">
          <ShieldAlert className="w-8 h-8 text-dsi-warning" />
          <div>
            <span className="text-lg font-black uppercase tracking-wider text-dsi-warning">
              {typeof activeReferral === 'object' && activeReferral?.status
                ? activeReferral.status.replace(/_/g, ' ')
                : 'Referred'}
            </span>
            {typeof activeReferral === 'object' && activeReferral?.priority != null && (
              <span className="block text-[10px] opacity-50">Priority: {activeReferral.priority}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-6 px-4">
          <div className="text-center">
            <span className="block text-xl font-black text-dsi-selected">{flaggedCount}</span>
            <span className="block text-[10px] uppercase opacity-50">Flagged</span>
          </div>
          <div className="text-center">
            <span className="block text-xl font-black text-dsi-positive">{overrideCount}</span>
            <span className="block text-[10px] uppercase opacity-50">Audited</span>
          </div>
          <div className="text-center">
            <span className="block text-xl font-black opacity-60">{totalSignals}</span>
            <span className="block text-[10px] uppercase opacity-50">Total Signals</span>
          </div>
        </div>
        <div className="flex items-center gap-4 ml-auto text-xs opacity-50">
          {typeof activeReferral === 'object' && activeReferral?.assigned_to && (
            <span className="flex items-center gap-1"><User className="w-3 h-3" /> {activeReferral.assigned_to}</span>
          )}
          {typeof activeReferral === 'object' && activeReferral?.created_at && (
            <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(activeReferral.created_at).toLocaleDateString()}</span>
          )}
        </div>
      </div>

      {/* TRIGGERS + CONDITIONS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 pt-2 pb-2">
        <div className="flex flex-col">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <ShieldAlert className="icon text-dsi-negative"/><span className="text-sm">Referral Triggers</span>
          </div>
          <div className="flex flex-col flex-1 border-b-3 border-dsi-contrast-background overflow-x-hidden border-collapse rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4">
            {reasons.length > 0 ? (
              <ul className="list-disc pl-10 pr-dsi-pad space-y-1.5 text-sm opacity-80 text-wrap">
                {reasons.map((reason: string, i: number) => (<li key={i}>{reason}</li>))}
              </ul>
            ) : (
              <p className="pl-dsi-pad text-sm opacity-50 italic">Manual Underwriter Referral</p>
            )}
          </div>
        </div>
        <div className="flex flex-col">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <AlertTriangle className="icon text-dsi-warning"/>
            <span className="text-sm">Triggering Conditions ({referralConditions.length})</span>
          </div>
          <div className="flex flex-col flex-1 border-b-3 border-dsi-contrast-background overflow-y-auto border-collapse rounded-b-xl bg-dsi-analysis shadow-sm pt-2 pb-2 max-h-[240px]">
            {referralConditions.length > 0 ? (
              <div className="space-y-0">
                {referralConditions.map((cond: any, idx: number) => {
                  const actionKey = typeof cond.action === 'string' ? cond.action.toLowerCase() : (cond.action?.value || 'note');
                  const colors = ACTION_COLORS[actionKey] || ACTION_COLORS.note;
                  return (
                    <div key={idx} className="flex items-center justify-between px-dsi-pad py-2 border-b border-dsi-outline/10 hover:bg-dsi-background/20 transition-colors">
                      <div className="flex items-center gap-3 min-w-0">
                        <ShieldAlert className={`w-3.5 h-3.5 shrink-0 ${colors.text}`} />
                        <div className="min-w-0">
                          <span className="text-sm block truncate">{cond.note || cond.source_name || 'Condition'}</span>
                          <span className="text-[10px] opacity-40 block">{cond.source_type}: {cond.source_id}</span>
                        </div>
                      </div>
                      <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded shrink-0 ${colors.bg} ${colors.text}`}>
                        {actionKey.replace('_', ' ')}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex items-center justify-center h-20 opacity-50 text-sm italic">No referral-type conditions triggered.</div>
            )}
          </div>
        </div>
      </div>

      {/* G2: SIGNAL AUDIT — GROUP ACCORDION */}
      <div className="flex flex-col pt-2 pb-2">
        <div className="flex justify-between items-center gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pr-dsi-pad pt-2 pb-2">
          <div className="flex items-center gap-dsi-pad">
            <Layers className="icon"/><span className="text-sm">Signal Audit Matrix</span>
            <span className="text-xs opacity-60 ml-2">({totalSignals} signals)</span>
          </div>
        </div>

        <div className="flex flex-col flex-1 border-b-3 border-dsi-contrast-background overflow-x-auto whitespace-nowrap border-collapse rounded-b-xl bg-dsi-analysis shadow-sm pt-2 pb-4">
          {isFetchingRiskSignals ? (
            <div className="flex flex-col items-center justify-center py-10 opacity-50 space-y-4">
              <Layers className="w-6 h-6 animate-spin" />
            </div>
          ) : groupEntries.length === 0 && totalSignals === 0 ? (
            <div className="py-8 text-center opacity-50 text-sm italic">No signal data found for this model version.</div>
          ) : (
            <div className="w-full">
              {/* Column headers */}
              <div className="grid grid-cols-[1fr_70px_70px_70px_70px_70px_80px_100px_60px] gap-0 text-[11px] underline opacity-70 px-dsi-pad py-2">
                <span>Group / Signal</span>
                <span className="text-right">Score</span>
                <span className="text-right">Conf</span>
                <span className="text-right">Weight</span>
                <span className="text-right">Contrib</span>
                <span className="text-center">Absent</span>
                <span className="text-right text-dsi-selected">Audited</span>
                <span className="text-dsi-selected">Rationale</span>
                <span className="text-center">Action</span>
              </div>

              {groupEntries.map(([groupId, gs]: [string, any]) => {
                const isExpanded = expandedGroups[groupId] ?? false;
                const signals = signalsByGroup[groupId] || [];
                const groupFlagged = signals.filter((s: any) => s.is_flagged && !s.is_overridden).length;
                const groupAudited = signals.filter((s: any) => s.is_overridden).length;

                return (
                  <div key={groupId}>
                    {/* GROUP HEADER */}
                    <div
                      onClick={() => toggleGroup(groupId)}
                      className="grid grid-cols-[1fr_70px_70px_70px_70px_70px_80px_100px_60px] gap-0 px-dsi-pad py-2.5 border-t border-dsi-outline/20 cursor-pointer hover:bg-dsi-background/20 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        {isExpanded ? <ChevronDown className="w-3.5 h-3.5 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 shrink-0" />}
                        <span className="font-bold text-sm">{groupId}</span>
                        <span className="text-[10px] opacity-40">({signals.length})</span>
                        {groupFlagged > 0 && (
                          <span className="text-[10px] bg-dsi-warning/10 text-dsi-warning px-1.5 py-0.5 rounded font-bold">{groupFlagged} flagged</span>
                        )}
                        {groupAudited > 0 && (
                          <span className="text-[10px] bg-dsi-positive/10 text-dsi-positive px-1.5 py-0.5 rounded font-bold">{groupAudited} audited</span>
                        )}
                      </div>
                      <span className="text-right text-sm">{formatNum(gs?.risk_score, 1)}</span>
                      <span></span>
                      <span className="text-right text-sm opacity-60">{formatNum(gs?.risk_weight, 2)}</span>
                      <span className="text-right text-sm font-bold">{formatNum(gs?.risk_contribution, 1)}</span>
                      <span></span><span></span><span></span><span></span>
                    </div>

                    {/* SIGNAL ROWS */}
                    {isExpanded && signals.map((sig: any, sidx: number) => {
                      const isHighImpact = Math.abs(sig.contribution || 0) > 10;
                      return (
                        <div
                          key={`${sig.code}-${sidx}`}
                          className={`grid grid-cols-[1fr_70px_70px_70px_70px_70px_80px_100px_60px] gap-0 px-dsi-pad py-1.5 bg-dsi-background/10 hover:bg-dsi-background/20 transition-colors ${sig.is_flagged && !sig.is_overridden ? 'border-l-2 border-l-dsi-warning' : ''} ${sig.is_overridden ? 'border-l-2 border-l-dsi-positive' : ''}`}
                        >
                          <div className="flex items-center gap-2 pl-6">
                            {isHighImpact && <Flame className="w-3 h-3 text-dsi-warning shrink-0" />}
                            {sig.is_flagged && !sig.is_overridden && !isHighImpact && <AlertTriangle className="w-3 h-3 text-dsi-warning shrink-0" />}
                            {sig.is_overridden && <Check className="w-3 h-3 text-dsi-positive shrink-0" />}
                            <span className={`text-sm truncate max-w-[160px] ${isHighImpact ? 'text-dsi-warning font-bold' : ''}`} title={sig.signal_name || sig.code}>
                              {(sig.signal_name || sig.code)?.replace(/_/g, ' ')}
                            </span>
                          </div>
                          <span className={`text-right text-sm ${sig.is_overridden ? 'text-dsi-positive font-bold' : ''}`}>
                            {formatNum(sig.score, 1)}
                          </span>
                          <span className={`text-right text-xs content-center ${(sig.confidence || 0) < 0.7 ? 'text-dsi-warning font-bold' : 'opacity-70'}`}>
                            {sig.confidence != null ? `${(sig.confidence * 100).toFixed(0)}%` : '-'}
                          </span>
                          <span className="text-right text-sm opacity-50">{formatNum(sig.weight, 2)}</span>
                          <span className={`text-right text-sm ${isHighImpact ? 'font-bold text-dsi-warning' : ''}`}>
                            {formatNum(sig.contribution || sig.contribution_to_score, 2)}
                          </span>
                          <span className="text-center text-xs">
                            {sig.was_absent ? <span className="text-dsi-negative font-bold">YES</span> : <span className="opacity-30">NO</span>}
                          </span>
                          <span className="text-right text-sm font-bold text-dsi-positive">
                            {sig.is_overridden ? formatNum(sig.audited_value, 2) : "—"}
                          </span>
                          <span className="text-xs opacity-80 truncate max-w-[90px]" title={sig.override_rationale}>
                            {sig.override_rationale || "—"}
                          </span>
                          <span className="text-center">
                            <button
                              onClick={() => { setOverrideModal({ isOpen: true, signal: sig }); setAuditedValue(sig.inferred_value ?? sig.score ?? ''); }}
                              className="p-1 hover:text-dsi-selected transition-colors"
                              title="Audit Signal"
                            >
                              <Edit3 className="w-3.5 h-3.5" />
                            </button>
                          </span>
                        </div>
                      );
                    })}

                    {isExpanded && signals.length === 0 && (
                      <div className="pl-12 py-2 text-xs opacity-40 italic">No signals in this group.</div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* FINAL DECISION ACTIONS */}
      {(activeSubmission?.decision === "refer" || activeVersion?.decision === "refer") && (
        <div className="flex flex-col pt-2 pb-2">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <Check className="icon"/><span className="text-sm">Final Decision Actions</span>
          </div>
          <div className="flex flex-row items-center justify-between gap-4 border-b-3 border-dsi-contrast-background overflow-x-hidden whitespace-nowrap border-collapse rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 pl-dsi-pad pr-dsi-pad">
            <div className="text-sm opacity-60 text-wrap">
              {overrideCount > 0
                ? `${overrideCount} signal${overrideCount !== 1 ? 's' : ''} audited. ${flaggedCount > 0 ? `${flaggedCount} flagged signal${flaggedCount !== 1 ? 's' : ''} remaining.` : 'All flagged signals addressed.'}`
                : `${flaggedCount} flagged signal${flaggedCount !== 1 ? 's' : ''} pending audit.`}
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleFinalDecision("decline")}
                className="flex items-center gap-2 px-6 py-2 border border-dsi-negative/50 text-dsi-negative rounded font-semibold hover:bg-dsi-negative/10 transition-colors"
              >
                <X className="w-5 h-5" /> Decline Risk
              </button>
              <button
                onClick={() => handleFinalDecision("approve")}
                className="flex items-center gap-2 px-6 py-2 bg-dsi-positive text-white rounded font-semibold hover:bg-dsi-positive transition-colors"
              >
                <Check className="w-5 h-5" /> Approve & Bind
              </button>
            </div>
          </div>
        </div>
      )}

      {/* OVERRIDE MODAL */}
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
                <span>{overrideModal.signal.signal_name || overrideModal.signal.code}</span>
                {overrideModal.signal.confidence != null && (
                  <span className="bg-dsi-selected/10 px-2 rounded">Conf: {(overrideModal.signal.confidence * 100).toFixed(0)}%</span>
                )}
              </div>
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1">
                  <label className="text-xs uppercase tracking-wider opacity-70">Current Score</label>
                  <input type="text" disabled value={overrideModal.signal.score ?? overrideModal.signal.inferred_value ?? ''} className="w-full mt-1 p-2 bg-dsi-background/50 border border-dsi-outline/20 rounded text-dsi-selected opacity-50" />
                </div>
                <ArrowRight className="w-6 h-6 mt-5 opacity-50" />
                <div className="flex-1">
                  <label className="text-xs uppercase tracking-wider opacity-70 text-dsi-selected font-bold">Audited Value</label>
                  <input
                    type="number" autoFocus
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
