"use client";

import { useState, useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import Modal from "@/components/Modal";
import {
  User, Search, MessageSquare, Plus, Paperclip,
  ShieldCheck, ShieldAlert, AlertTriangle, Layers, Target,
  Building2, Shield, ShieldX, ShieldQuestionMark,
} from "lucide-react";
import { formatNum, formatDollar } from "@/lib/format";

const DECISION_STYLE: Record<string, { bg: string; }> = {
  approve: { 
    bg: 'bg-dsi-approve', 
    },
  refer: { 
    bg: 'bg-dsi-refer', 
    },
  decline: { 
    bg: 'bg-dsi-decline', 
    },
};

export default function SummaryTab() {
  const { activeSubmission, activeQuote, activeVersion, addNote, commercialTerms, riskTerms, fetchCommercialTerms } = useDsiStore();

  const [isWhoOpen, setIsWhoOpen] = useState(false);
  const [isDiscoveryOpen, setIsDiscoveryOpen] = useState(false);
  const [newNoteText, setNewNoteText] = useState("");
  const [isAddingNote, setIsAddingNote] = useState(false);

  useEffect(() => {
    if (activeVersion?.version_code) {
      fetchCommercialTerms(activeVersion.version_code);
    }
  }, [activeVersion?.version_code, fetchCommercialTerms]);

  if (!activeSubmission || !activeVersion) {
    return (
      <div className="flex items-center justify-center h-full text-dsi-selected/50 animate-pulse">
        Loading version details...
      </div>
    );
  }

  const formatKey = (key: string) => key.replace(/_/g, ' ').toUpperCase();

  const handleAddNote = async () => {
    if (!newNoteText.trim() || !activeVersion?.version_code) return;
    setIsAddingNote(true);
    await addNote(activeVersion.version_code, newNoteText.trim(), "underwriter");
    setNewNoteText("");
    setIsAddingNote(false);
  };

  const decision = (activeVersion.decision || 'unknown').toLowerCase();
  const dStyle = DECISION_STYLE[decision] || { bg: 'bg-dsi-muted', border: 'border-dsi-muted' };
  const notes = activeVersion.notes || [];

  return (
    <div className="w-full no-scrollbar border-collapse animate-in fade-in duration-500 pb-12 pt-3">

      {/* ═══════════════════════════════════════════════════════════════════
          DECISION BANNER — incorporates status, dates, policy info
          ═══════════════════════════════════════════════════════════════════ */}
      <div className={`rounded-xl border-b-3 border-dsi-contrast-background ${dStyle.bg} shadow-sm px-dsi-pad py-4 mb-4`}>
        {/* Top row: Decision + status context */}
        
        <div className="flex items-center justify-between mb-3 pb-3 border-b border-dsi-outline/10">
          
          <div className="flex items-center gap-4">
            {decision === 'approve' ? 
              <ShieldCheck className={`w-10 h-10 text-dsi-selected`} /> :
             decision === 'refer' ? 
              <ShieldQuestionMark className={`w-10 h-10 text-dsi-selected`} /> :
              <ShieldX className={`w-10 h-10 text-dsi-selected`} />}
            <div>
              <span className={`text-2xl font-bold uppercase tracking-wider text-dsi-selected`}>
                {activeVersion.decision || 'Pending'}
              </span>
              {activeVersion.auto_approve && (
                <span className="block text-[10px] opacity-50">Auto-approved by engine</span>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-6 text-sm whitespace-nowrap">
            <div>
              <span className="opacity-50 text-xs block">Status</span>
              <span className="font-bold uppercase">{activeQuote?.status || 'N/A'}</span>
            </div>
            {(activeQuote?.status === 'draft' || activeQuote?.status === 'ready') && (
              <>
                <div>
                  <span className="opacity-50 text-xs block">Valid From</span>
                  <span className="font-bold">{activeQuote?.valid_from ? new Date(activeQuote.valid_from).toLocaleDateString() : 'N/A'}</span>
                </div>
                <div>
                  <span className="opacity-50 text-xs block">Valid Until</span>
                  <span className="font-bold">{activeQuote?.valid_until ? new Date(activeQuote.valid_until).toLocaleDateString() : 'N/A'}</span>
                </div>
              </>
            )}
            {activeQuote?.status === 'bound' && (
              <>
                <div>
                  <span className="opacity-50 text-xs block">Bound Date</span>
                  <span className="font-bold">{activeQuote?.bound_at ? new Date(activeQuote.bound_at).toLocaleDateString() : 'N/A'}</span>
                </div>
                <div>
                  <span className="opacity-50 text-xs block">Policy Ref</span>
                  <span className="font-bold">{activeQuote?.policy_number || 'Pending'}</span>
                </div>
              </>
            )}
          </div>

        </div>
        
        {/* Bottom row: Hero numbers */}
        <div className="grid grid-cols-6">

          {/* row 1 */}
          <div className="
            overflow-x-hidden whitespace-nowrap border-collapse
            flex gap-dsi-pad text-sm"
            >Final Composite Score
          </div>
          <div className="
            overflow-x-hidden whitespace-nowrap border-collapse
            flex gap-dsi-pad text-sm 
            border-r-1 border-dsi-outline/50"
            >Final Tier
          </div>
          <div className="
            overflow-x-hidden whitespace-nowrap border-collapse
            flex gap-dsi-pad text-sm 
            border-r-1 border-dsi-outline/50"
            >Currency
          </div>
          <div className="
            overflow-x-hidden whitespace-nowrap border-collapse
            flex gap-dsi-pad text-sm 
            border-r-1 border-dsi-outline/50"
            >Recommended Technical Premium
          </div>
          <div className="
            overflow-x-hidden whitespace-nowrap border-collapse
            flex gap-dsi-pad text-sm 
            border-r-1 border-dsi-outline/50"
            >Recommened Techncial Limit
          </div>
          <div className="
            overflow-x-hidden whitespace-nowrap border-collapse
            flex gap-dsi-pad text-sm 
            border-r-1 border-dsi-outline/50"
            >Gross Premium
          </div>

          <div className="text-2xl font-bold text-dsi-selected">{activeVersion.final_composite_score?.toFixed(1) || "N/A"}</div>
          <div className="text-2xl font-bold text-dsi-selected uppercase">T{activeVersion.final_tier} ({activeVersion.tier_label})</div>
          <div className="text-2xl font-bold text-dsi-selected">
            1
            </div>
          <div className="text-2xl font-bold text-dsi-selected">
              {activeVersion.final_premium ? `${activeVersion.final_premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}`: 0}
            </div>
          <div className="text-2xl font-bold text-dsi-selected">
              {activeQuote?.recommended_limit ? `${activeQuote.recommended_limit.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : 0}
            </div>
          <div className="text-2xl font-bold text-dsi-selected">
              {commercialTerms?.gross_premium ? `${commercialTerms.gross_premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : 0}
            </div>

        </div>          

      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          WHO / DISCOVERY (left stacked) + BASE DETAILS (right, full height)
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-[1fr_2fr] gap-4 mb-4">

        {/* LEFT: Who + Discovery stacked */}
        <div className="flex flex-col gap-4">
          <div onClick={() => setIsWhoOpen(true)} className="group cursor-pointer border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis hover:bg-dsi-background/30 transition-all shadow-sm flex-1">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-bold flex items-center gap-2"><User className="w-4 h-4 text-dsi-selected" /> Who they are</h3>
              <span className="text-xs opacity-50 group-hover:opacity-100 text-dsi-selected">View &rarr;</span>
            </div>
            <p className="text-xs opacity-70 line-clamp-3 text-wrap">
              {activeSubmission.entity_name} &bull; {activeSubmission.submission_data?.industry || 'Unknown Industry'} &bull; {activeSubmission.submission_data?.geography || 'Unknown Geo'}
            </p>
          </div>
          <div onClick={() => setIsDiscoveryOpen(true)} className="group cursor-pointer border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis hover:bg-dsi-background/30 transition-all shadow-sm flex-1">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-bold flex items-center gap-2"><Search className="w-4 h-4 text-dsi-selected" /> Discovery</h3>
              <span className="text-xs opacity-50 group-hover:opacity-100 text-dsi-selected">View &rarr;</span>
            </div>
            <p className="text-xs opacity-70 line-clamp-3 text-wrap">
              {activeVersion.discovery_output?.domain || 'No domain discovered'} &bull; Confidence: {activeVersion.discovery_output?.confidence || 'N/A'}
            </p>
          </div>
        </div>

        {/* RIGHT: Base Details — same height as left two cards */}
        <div className="flex flex-col">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <Paperclip className="icon"/><span className="text-sm">Base Details</span>
          </div>
          <div className="flex-1 border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-3 text-sm text-wrap">
              <div><span className="opacity-50 block text-xs mb-0.5">Submission Code</span><span className="font-bold">{activeSubmission?.submission_code}</span></div>
              <div><span className="opacity-50 block text-xs mb-0.5">Quote Code</span><span className="font-bold">{activeQuote?.quote_code}</span></div>
              <div><span className="opacity-50 block text-xs mb-0.5">Coverage</span><span className="font-semibold">{activeSubmission.coverage}</span></div>
              <div><span className="opacity-50 block text-xs mb-0.5">Configuration</span><span className="font-semibold">{activeSubmission.configuration}</span></div>
              <div><span className="opacity-50 block text-xs mb-0.5">Product Type</span><span className="font-semibold">{activeSubmission.submission_data?.product_type || 'N/A'}</span></div>
              <div><span className="opacity-50 block text-xs mb-0.5">Signal Coverage</span><span className="font-semibold">{((activeVersion.signal_coverage || 0) * 100).toFixed(0)}%</span></div>
              <div><span className="opacity-50 block text-xs mb-0.5">Rec. Premium</span><span className="font-semibold">{activeQuote?.recommended_premium ? `$${activeQuote.recommended_premium.toLocaleString()}` : 'N/A'}</span></div>
              <div><span className="opacity-50 block text-xs mb-0.5">Rec. Limit</span><span className="font-semibold">{activeQuote?.recommended_limit ? `$${activeQuote.recommended_limit.toLocaleString()}` : 'N/A'}</span></div>
              <div>
                <span className="opacity-50 block text-xs mb-0.5">ROL</span>
                <span className="font-semibold">
                  {activeQuote?.recommended_premium && activeQuote?.recommended_limit
                    ? `${((activeQuote.recommended_premium / activeQuote.recommended_limit) * 100).toFixed(2)}%`
                    : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          THREE PILLAR ASSESSMENT — full width
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="flex flex-col pt-2 pb-2">
        <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
          <Layers className="icon"/><span className="text-sm">Three Pillar Assessment</span>
        </div>
        <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* RISK */}
            <div className="border border-dsi-outline/20 rounded-lg p-4 text-wrap">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-dsi-outline/10">
                <Target className="w-4 h-4 text-dsi-selected" />
                <span className="text-xs font-bold uppercase tracking-wider opacity-60">Risk</span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="opacity-60">Composite Score</span><span className="font-bold">{formatNum(activeVersion.pure_composite_score, 1)}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Score-Based Tier</span><span className="font-bold">Tier {activeVersion.score_based_tier || activeVersion.final_tier}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Final Tier</span><span className="font-bold text-dsi-selected">Tier {activeVersion.final_tier} ({activeVersion.tier_label})</span></div>
                <div className="flex justify-between"><span className="opacity-60">Confidence</span><span className="font-bold">{((activeVersion.confidence || 0) * 100).toFixed(0)}%</span></div>
                <div className="flex justify-between"><span className="opacity-60">Signal Coverage</span><span className="font-bold">{((activeVersion.signal_coverage || 0) * 100).toFixed(0)}%</span></div>
              </div>
            </div>
            {/* LOSS */}
            <div className="border border-dsi-outline/20 rounded-lg p-4 text-wrap">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-dsi-outline/10">
                <ShieldAlert className="w-4 h-4 text-dsi-selected" />
                <span className="text-xs font-bold uppercase tracking-wider opacity-60">Loss Propensity</span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="opacity-60">Propensity Band</span><span className="font-bold uppercase">{activeVersion.loss_propensity_band?.replace(/_/g, ' ') || 'N/A'}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Combined Modifier</span><span className="font-bold">{activeVersion.loss_combined_modifier?.toFixed(3) || '1.000'}x</span></div>
                <div className="flex justify-between">
                  <span className="opacity-60">Trend</span>
                  <span className={`font-bold ${activeVersion.loss_trend_direction?.toLowerCase().includes('improv') ? 'text-dsi-positive' : activeVersion.loss_trend_direction?.toLowerCase().includes('deter') ? 'text-dsi-negative' : 'opacity-70'}`}>
                    {activeVersion.loss_trend_direction?.replace(/_/g, ' ') || 'Stable'}
                  </span>
                </div>
                <div className="flex justify-between"><span className="opacity-60">Cohort</span><span className="font-bold text-xs">{activeVersion.loss_cohort_name || 'Unknown'}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Model Confidence</span><span className="font-bold">{activeVersion.loss_confidence != null ? `${(activeVersion.loss_confidence * 100).toFixed(0)}%` : 'N/A'}</span></div>
              </div>
            </div>
            {/* EXPOSURE */}
            <div className="border border-dsi-outline/20 rounded-lg p-4 text-wrap">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-dsi-outline/10">
                <AlertTriangle className="w-4 h-4 text-dsi-selected" />
                <span className="text-xs font-bold uppercase tracking-wider opacity-60">Exposure</span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="opacity-60">Exposure Value</span><span className="font-bold">${(activeVersion.exposure_value || 0).toLocaleString()}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Exposure Band</span><span className="font-bold uppercase">{activeVersion.exposure_band_label || 'N/A'}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Modifier</span><span className="font-bold">{activeVersion.exposure_modifier?.toFixed(3) || '1.000'}x</span></div>
                <div className="flex justify-between"><span className="opacity-60">Size Score</span><span className="font-bold">{formatNum(activeVersion.exposure_size_score, 1)}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Method</span><span className="font-bold text-xs uppercase">{activeVersion.exposure_assessment_method?.replace(/_/g, ' ') || 'N/A'}</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          COMMERCIAL & RISK TERMS SUMMARY
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 pb-2">
        {/* Commercial Summary Card */}
        <div className="flex flex-col">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <Building2 className="icon"/><span className="text-sm">Commercial Summary</span>
          </div>
          <div className="flex-1 border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">
            {commercialTerms ? (
              <div className="space-y-2 text-sm text-wrap">
                <div className="flex justify-between"><span className="opacity-60">Entity</span><span className="font-bold">{commercialTerms.entity_name || "N/A"}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Offered Premium</span><span className="font-bold text-dsi-selected">{formatDollar(commercialTerms.offered_premium)}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Gross Premium</span><span className="font-bold">{formatDollar(commercialTerms.gross_premium)}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Currency</span><span className="font-bold">{commercialTerms.base_currency || "USD"}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Distribution</span><span className="font-bold uppercase">{commercialTerms.distribution_type || "N/A"}</span></div>
              </div>
            ) : (
              <p className="text-xs opacity-50 italic text-center py-4 text-wrap">No commercial terms available</p>
            )}
          </div>
        </div>

        {/* Risk Terms Summary Card */}
        <div className="flex flex-col">
          <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
            <Shield className="icon"/><span className="text-sm">Risk Terms Summary</span>
          </div>
          <div className="flex-1 border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">
            {riskTerms ? (
              <div className="space-y-2 text-sm text-wrap">
                <div className="flex justify-between"><span className="opacity-60">Deductible Type</span><span className="font-bold capitalize">{riskTerms.deductible_type?.replace(/_/g, " ") || "N/A"}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Deductible Amount</span><span className="font-bold">{formatDollar(riskTerms.deductible_amount)}</span></div>
                <div className="flex justify-between"><span className="opacity-60">SIR</span><span className={`font-bold ${riskTerms.sir_applies ? "text-dsi-warning" : ""}`}>{riskTerms.sir_applies ? `Yes — ${formatDollar(riskTerms.sir_amount)}` : "No"}</span></div>
                <div className="flex justify-between"><span className="opacity-60">Aggregate Limit</span><span className="font-bold">{formatDollar(riskTerms.aggregate_limit)}</span></div>
                <div className="flex justify-between">
                  <span className="opacity-60">Coverage Terms</span>
                  <span className="font-bold">
                    {riskTerms.coverage_terms ? `${Object.keys(riskTerms.coverage_terms).length} terms` : "N/A"}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-xs opacity-50 italic text-center py-4 text-wrap">No risk terms available</p>
            )}
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          NOTES — full width, inline add, persisted to DB
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="flex flex-col pt-2 pb-2">
        <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
          <MessageSquare className="icon"/><span className="text-sm">Notes ({notes.length})</span>
        </div>
        <div className="border-b-3 border-dsi-contrast-background rounded-b-xl bg-dsi-analysis shadow-sm pt-4 pb-4 px-dsi-pad">
          {/* Inline add */}
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={newNoteText}
              onChange={(e) => setNewNoteText(e.target.value)}
              placeholder="Add a note..."
              className="flex-1 bg-dsi-background/50 border border-dsi-outline/20 rounded px-3 py-2 text-sm text-dsi-selected outline-none focus:border-dsi-selected"
              onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
              disabled={isAddingNote}
            />
            <button
              onClick={handleAddNote}
              disabled={!newNoteText.trim() || isAddingNote}
              className="bg-dsi-selected text-dsi-background px-4 py-2 rounded flex items-center gap-2 text-sm font-semibold disabled:opacity-50 hover:opacity-90 transition-opacity"
            >
              <Plus className="w-4 h-4" /> {isAddingNote ? 'Saving...' : 'Add'}
            </button>
          </div>
          {/* Notes list — reads from activeVersion.notes (persisted) */}
          {notes.length === 0 ? (
            <p className="text-xs opacity-50 italic text-center py-4 text-wrap">No notes recorded yet. Add one above.</p>
          ) : (
            <div className="space-y-2 max-h-[300px] overflow-y-auto no-scrollbar">
              {[...notes].reverse().map((note: any, i: number) => {
                const text = typeof note === 'object' ? (note.note || note.text) : note;
                const source = typeof note === 'object' ? note.source : "System";
                return (
                  <div key={i} className="bg-dsi-background/30 rounded-lg p-3 border border-dsi-outline/10 text-wrap">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] opacity-50 flex items-center gap-1">
                        <User className="w-2.5 h-2.5" /> {source}
                      </span>
                    </div>
                    <p className="text-xs leading-relaxed">{text}</p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* MODALS — Who + Discovery */}
      <Modal isOpen={isWhoOpen} onClose={() => setIsWhoOpen(false)} title="Submission Data" icon={User}>
        <div className="space-y-3 font-mono text-sm">
          {Object.entries(activeSubmission.submission_data || {})
            .filter(([key]) => key !== 'limit' && key !== 'product_type')
            .map(([key, val]) => (
              <div key={key} className="flex justify-between items-center py-2 border-b border-dsi-outline/5 last:border-0">
                <span className="opacity-60">{formatKey(key)}</span>
                <span className="font-bold text-right">
                  {typeof val === 'number' && key.toLowerCase().includes('revenue') ? `$${val.toLocaleString()}` : String(val)}
                </span>
              </div>
            ))}
          {Object.keys(activeSubmission.submission_data || {}).length === 0 && (
            <div className="text-center opacity-50 italic py-4">No submission data available.</div>
          )}
        </div>
      </Modal>

      <Modal isOpen={isDiscoveryOpen} onClose={() => setIsDiscoveryOpen(false)} title="Discovery Output" icon={Search}>
        <div className="space-y-3 font-mono text-sm">
          {Object.entries(activeVersion.discovery_output || {}).map(([key, val]) => (
            <div key={key} className="flex justify-between items-center py-2 border-b border-dsi-outline/5 last:border-0">
              <span className="opacity-60">{formatKey(key)}</span>
              <span className="font-bold text-right text-dsi-selected">{String(val)}</span>
            </div>
          ))}
          {Object.keys(activeVersion.discovery_output || {}).length === 0 && (
            <div className="text-center opacity-50 italic py-4">No discovery output available.</div>
          )}
        </div>
      </Modal>

    </div>
  );
}


