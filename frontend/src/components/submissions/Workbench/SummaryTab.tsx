"use client";

import { useState } from "react";
import { useDsiStore } from "@/store/dsiStore";
import Modal from "@/components/Modal";
import {
  User, Search, MessageSquare, Plus, Paperclip,
  ShieldCheck, ShieldAlert, AlertTriangle, TrendingUp, BarChart3
} from "lucide-react";

const DECISION_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  approve: { bg: 'bg-dsi-positive/10', text: 'text-dsi-positive', border: 'border-dsi-positive/30' },
  refer: { bg: 'bg-dsi-warning/10', text: 'text-dsi-warning', border: 'border-dsi-warning/30' },
  decline: { bg: 'bg-dsi-negative/10', text: 'text-dsi-negative', border: 'border-dsi-negative/30' },
};

export default function SummaryTab() {
  const { activeSubmission, activeQuote, activeVersion } = useDsiStore();

  const [isWhoOpen, setIsWhoOpen] = useState(false);
  const [isDiscoveryOpen, setIsDiscoveryOpen] = useState(false);
  const [isNotesOpen, setIsNotesOpen] = useState(false);
  const [localNotes, setLocalNotes] = useState<any[]>(activeVersion?.notes || []);
  const [newNoteText, setNewNoteText] = useState("");

  if (!activeSubmission || !activeVersion) {
    return (
      <div className="flex items-center justify-center h-full text-dsi-selected/50 animate-pulse">
        Loading version details...
      </div>
    );
  }

  const formatKey = (key: string) => key.replace(/_/g, ' ').toUpperCase();

  const handleAddNote = () => {
    if (!newNoteText.trim()) return;
    const newNote = {
      text: newNoteText,
      source: "Underwriter_UI",
      timestamp: new Date().toISOString()
    };
    setLocalNotes([...localNotes, newNote]);
    setNewNoteText("");
  };

  const decision = (activeVersion.decision || 'unknown').toLowerCase();
  const dStyle = DECISION_STYLE[decision] || { bg: 'bg-dsi-muted/10', text: 'text-dsi-muted', border: 'border-dsi-muted/30' };

  // Guardrails

  // Guardrails
  const guardrails = activeVersion.guardrail_warnings || [];

  return (
    <div className="
      w-full no-scrollbar
      border-collapse whitespace-nowrap
      animate-in fade-in duration-500 pb-12"
    >
      {/* STICKY WRAPPER */}
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
        ">
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
              <span>
                <span className="text-sm">Quote Valid From:</span><span className="pl-2 uppercase font-bold">{new Date(activeQuote.valid_from).toLocaleDateString()};</span>
                <span className="pl-2 pr-2"> </span>
                <span className="text-sm">Until:</span><span className="pl-2 uppercase font-bold">{new Date(activeQuote.valid_until).toLocaleDateString()}</span>
              </span>
            )}
            {activeQuote.status === 'bound' && (
              <span>
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

      {/* =======================================================================
          HERO: DECISION BANNER
          ======================================================================= */}
      <div className={`
        flex items-center justify-between gap-6
        rounded-xl border-2 ${dStyle.border} ${dStyle.bg}
        px-dsi-pad py-5 mt-2 mb-4
      `}>
        {/* Decision badge */}
        <div className="flex items-center gap-4">
          {decision === 'approve' ? <ShieldCheck className={`w-10 h-10 ${dStyle.text}`} /> :
           decision === 'refer' ? <ShieldAlert className={`w-10 h-10 ${dStyle.text}`} /> :
           <AlertTriangle className={`w-10 h-10 ${dStyle.text}`} />}
          <div>
            <span className={`text-2xl font-black uppercase tracking-wider ${dStyle.text}`}>
              {activeVersion.decision || 'Pending'}
            </span>
            {activeVersion.auto_approve && (
              <span className="block text-[10px] opacity-50">Auto-approved by engine</span>
            )}
          </div>
        </div>

        {/* Hero numbers */}
        <div className="flex items-center gap-8">
          <div className="text-right">
            <span className="block text-[10px] uppercase tracking-wider opacity-50">Final Tier</span>
            <span className="text-2xl font-black text-dsi-selected">
              Tier {activeVersion.final_tier}
            </span>
            <span className="block text-[10px] opacity-40 uppercase">{activeVersion.tier_label}</span>
          </div>
          <div className="w-px h-10 bg-dsi-outline/20" />
          <div className="text-right">
            <span className="block text-[10px] uppercase tracking-wider opacity-50">Composite Score</span>
            <span className="text-2xl font-black text-dsi-selected">
              {activeVersion.pure_composite_score?.toFixed(1) || "N/A"}
            </span>
            <span className="block text-[10px] opacity-40">{((activeVersion.confidence || 0) * 100).toFixed(0)}% confidence</span>
          </div>
          <div className="w-px h-10 bg-dsi-outline/20" />
          <div className="text-right">
            <span className="block text-[10px] uppercase tracking-wider opacity-50">Final Premium</span>
            <span className="text-2xl font-black text-dsi-selected">
              {activeVersion.final_premium ? `$${activeVersion.final_premium.toLocaleString()}` :
               activeVersion.premium_after_modifiers ? `$${activeVersion.premium_after_modifiers.toLocaleString()}` :
               'Pending'}
            </span>
            <span className="block text-[10px] opacity-40">
              {activeQuote?.recommended_limit ? `$${activeQuote.recommended_limit.toLocaleString()} limit` : ''}
            </span>
          </div>
        </div>
      </div>

      {/* =======================================================================
          TWO-COLUMN: CONTEXT CARDS + ASSESSMENT SNAPSHOT
          ======================================================================= */}
      <div className="flex flex-col lg:flex-row gap-4">

        {/* LEFT: Context sidebar — compact clickable cards */}
        <div className="w-full lg:w-1/3 flex flex-col gap-3">

          <div
            onClick={() => setIsWhoOpen(true)}
            className="group cursor-pointer border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis hover:bg-dsi-background/30 transition-all shadow-sm"
          >
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <User className="w-4 h-4 text-dsi-selected" /> Who they are
              </h3>
              <span className="text-xs opacity-50 group-hover:opacity-100 text-dsi-selected">View &rarr;</span>
            </div>
            <p className="text-xs opacity-70 line-clamp-2 text-wrap">
              {activeSubmission.entity_name} &bull; {activeSubmission.submission_data?.industry || 'Unknown Industry'} &bull; {activeSubmission.submission_data?.geography || 'Unknown Geo'}
            </p>
          </div>

          <div
            onClick={() => setIsDiscoveryOpen(true)}
            className="group cursor-pointer border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis hover:bg-dsi-background/30 transition-all shadow-sm"
          >
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <Search className="w-4 h-4 text-dsi-selected" /> Discovery
              </h3>
              <span className="text-xs opacity-50 group-hover:opacity-100 text-dsi-selected">View &rarr;</span>
            </div>
            <p className="text-xs opacity-70 line-clamp-2 text-wrap">
              {activeVersion.discovery_output?.domain || 'No domain discovered'} &bull; Confidence: {activeVersion.discovery_output?.confidence || 'N/A'}
            </p>
          </div>

          <div className="border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-dsi-selected" /> Notes ({localNotes.length})
              </h3>
              <button onClick={() => setIsNotesOpen(true)} className="text-xs opacity-50 hover:opacity-100 text-dsi-selected">
                Manage &rarr;
              </button>
            </div>
            {localNotes.length === 0 ? (
              <p className="text-xs opacity-50 italic">No notes recorded.</p>
            ) : (
              <div className="space-y-2">
                {localNotes.slice(-3).map((note: any, i: number) => {
                  const isObj = typeof note === 'object' && note !== null;
                  const text = isObj ? (note.note || note.text) : note;
                  const source = isObj ? note.source : "System";
                  return (
                    <div key={i} className="bg-dsi-background/30 rounded p-2 text-wrap">
                      <span className="text-[10px] opacity-40 block mb-0.5">{source}</span>
                      <span className="text-xs leading-relaxed line-clamp-2">{text}</span>
                    </div>
                  );
                })}
                {localNotes.length > 3 && (
                  <button onClick={() => setIsNotesOpen(true)} className="text-[10px] opacity-40 hover:opacity-70">
                    +{localNotes.length - 3} more...
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Guardrail warnings if any */}
          {guardrails.length > 0 && (
            <div className="border border-dsi-warning/30 bg-dsi-warning/5 rounded-xl p-4">
              <h3 className="text-sm font-bold flex items-center gap-2 text-dsi-warning mb-2">
                <AlertTriangle className="w-4 h-4" /> Guardrail Warnings
              </h3>
              <div className="space-y-1">
                {guardrails.map((g: any, i: number) => (
                  <p key={i} className="text-xs opacity-80 text-wrap">
                    {typeof g === 'object' ? g.note || g.text : g}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: Assessment snapshot */}
        <div className="w-full lg:w-2/3 flex flex-col gap-4">

          {/* Quick context row */}
          <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
            <div className="grid grid-cols-3 md:grid-cols-6 gap-4 text-sm">
              <div>
                <span className="opacity-50 block text-xs mb-1">Coverage</span>
                <span className="font-semibold">{activeSubmission.coverage}</span>
              </div>
              <div>
                <span className="opacity-50 block text-xs mb-1">Configuration</span>
                <span className="font-semibold">{activeSubmission.configuration}</span>
              </div>
              <div>
                <span className="opacity-50 block text-xs mb-1">Product Type</span>
                <span className="font-semibold">{activeSubmission.submission_data?.product_type || 'N/A'}</span>
              </div>
              <div>
                <span className="opacity-50 block text-xs mb-1">Signal Coverage</span>
                <span className="font-semibold">{((activeVersion.signal_coverage || 0) * 100).toFixed(0)}%</span>
              </div>
              <div>
                <span className="opacity-50 block text-xs mb-1">Loss Band</span>
                <span className="font-semibold uppercase">{activeVersion.loss_propensity_band?.replace(/_/g, ' ') || 'N/A'}</span>
              </div>
              <div>
                <span className="opacity-50 block text-xs mb-1">Exposure Band</span>
                <span className="font-semibold uppercase">{activeVersion.exposure_band_label || 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Loss + Exposure summary — condensed single row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis shadow-sm">
              <h3 className="text-xs font-bold flex items-center gap-2 mb-3 opacity-60 uppercase tracking-wider">
                <TrendingUp className="w-3.5 h-3.5 text-dsi-selected" /> Loss Summary
              </h3>
              <div className="flex items-center justify-between text-sm">
                <span className="opacity-60">Combined Modifier</span>
                <span className="font-bold">{activeVersion.loss_combined_modifier?.toFixed(3) || '1.000'}x</span>
              </div>
              <div className="flex items-center justify-between text-sm mt-1">
                <span className="opacity-60">Trend</span>
                <span className={`font-bold ${
                  activeVersion.loss_trend_direction?.toLowerCase().includes('improv') ? 'text-dsi-positive' :
                  activeVersion.loss_trend_direction?.toLowerCase().includes('deter') ? 'text-dsi-negative' : 'opacity-70'
                }`}>
                  {activeVersion.loss_trend_direction?.replace(/_/g, ' ') || 'Stable'}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm mt-1">
                <span className="opacity-60">Cohort</span>
                <span className="font-bold text-xs">{activeVersion.loss_cohort_name || 'Unknown'}</span>
              </div>
            </div>

            <div className="border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis shadow-sm">
              <h3 className="text-xs font-bold flex items-center gap-2 mb-3 opacity-60 uppercase tracking-wider">
                <BarChart3 className="w-3.5 h-3.5 text-dsi-selected" /> Exposure Summary
              </h3>
              <div className="flex items-center justify-between text-sm">
                <span className="opacity-60">Exposure Value</span>
                <span className="font-bold">${(activeVersion.exposure_value || 0).toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between text-sm mt-1">
                <span className="opacity-60">Modifier</span>
                <span className="font-bold">{activeVersion.exposure_modifier?.toFixed(3) || '1.000'}x</span>
              </div>
              <div className="flex items-center justify-between text-sm mt-1">
                <span className="opacity-60">Method</span>
                <span className="font-bold text-xs uppercase">{activeVersion.exposure_assessment_method?.replace(/_/g, ' ') || 'N/A'}</span>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* =======================================================================
          MODALS
          ======================================================================= */}
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

      <Modal isOpen={isNotesOpen} onClose={() => setIsNotesOpen(false)} title="Model Version Notes" icon={MessageSquare}>
        <div className="flex flex-col h-[50vh]">
          <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
            {localNotes.length === 0 ? (
              <div className="text-center opacity-50 italic pt-10">No notes recorded yet.</div>
            ) : (
              localNotes.map((note: any, i: number) => {
                const isObj = typeof note === 'object' && note !== null;
                const text = isObj ? note.text : note;
                const source = isObj ? note.source : "System / Engine";
                return (
                  <div key={i} className="bg-dsi-background/50 rounded-lg p-3 border border-dsi-outline/10 text-sm">
                    <div className="text-xs opacity-50 mb-1.5 flex items-center gap-2">
                      <User className="w-3 h-3" /> {source}
                    </div>
                    <div className="font-mono leading-relaxed">{text}</div>
                  </div>
                );
              })
            )}
          </div>
          <div className="pt-4 border-t border-dsi-outline/10 flex gap-2">
            <input
              type="text"
              value={newNoteText}
              onChange={(e) => setNewNoteText(e.target.value)}
              placeholder="Add a new note..."
              className="flex-1 bg-dsi-background/50 border border-dsi-outline/20 rounded p-2 text-sm text-dsi-selected outline-none focus:border-dsi-selected"
              onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
            />
            <button
              onClick={handleAddNote}
              disabled={!newNoteText.trim()}
              className="bg-dsi-selected text-dsi-background px-3 rounded flex items-center justify-center disabled:opacity-50 hover:opacity-90 transition-opacity"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>
        </div>
      </Modal>

    </div>
  );
}
