"use client";

import { useState } from "react";
import { useDsiStore } from "@/store/dsiStore";
import Modal from "@/components/Modal";
import { 
  Activity, Shield, Calculator, BarChart3, TrendingUp, 
  X, User, Search, MessageSquare, Plus 
} from "lucide-react";

export default function SummaryTab() {
  const { activeSubmission, activeQuote, activeVersion } = useDsiStore();

  // Modal States
  const [isWhoOpen, setIsWhoOpen] = useState(false);
  const [isDiscoveryOpen, setIsDiscoveryOpen] = useState(false);
  const [isNotesOpen, setIsNotesOpen] = useState(false);
  
  // Local Notes State (to handle UI updates before backend saves)
  const [localNotes, setLocalNotes] = useState<any[]>(activeVersion?.notes || []);
  const [newNoteText, setNewNoteText] = useState("");

  if (!activeSubmission || !activeVersion) {
    return (
      <div className="flex items-center justify-center h-full text-dsi-selected/50 animate-pulse">
        Loading version details...
      </div>
    );
  }

  // --- HELPERS ---
  const formatKey = (key: string) => key.replace(/_/g, ' ').toUpperCase();
  
  const handleAddNote = () => {
    if (!newNoteText.trim()) return;
    const newNote = {
      text: newNoteText,
      source: "Underwriter_UI", // In production, grab active user ID from auth context
      timestamp: new Date().toISOString()
    };
    setLocalNotes([...localNotes, newNote]);
    setNewNoteText("");
    // TODO: Dispatch a store action here to save the note to the backend
  };

  return (
    <div className="
      pt-4
      w-full no-scrollbar
      animate-in fade-in duration-500"
    >
      
      {/* KEY INFORMATION */}
      <div className="
        grid grid-cols-1 grid-rows-4
        sticky top-5 z-5
        border-b-3 border-dsi-contrast-background
        rounded-xl
        overflow-hidden
        bg-dsi-analysis shadow-sm
        pt-2 pb-2 pl-4 gap-1"
      >  
        <div className="underline font-bold">
          Key Information
        </div>
        <div className="content-center">
          <span>Status: </span><span className="uppercase font-bold">{activeQuote.status}</span>
        </div>
        
        <div className="content-center">
          {(activeQuote.status === 'draft' || activeQuote.status === 'ready') && (
            <span className="gap-6 ">
              <span>Quote Valid From: {new Date(activeQuote.valid_from).toLocaleDateString()}; Until: {new Date(activeQuote.valid_until).toLocaleDateString()}</span>
            </span>
          )}
          {activeQuote.status === 'bound' && (
            <span className="gap-6 ">
                <span>Bound Date: {activeQuote.bound_at ? new Date(activeQuote.bound_at).toLocaleDateString() : 'N/A'}</span>
                <span>Policy Reference: {activeQuote.policy_number || 'Pending'}</span>
            </span>
          )}
        </div>
        
        <div className="content-center">
          <span>Submission Code: </span><span className="uppercase font-bold">{activeSubmission.submission_code}</span>
          <span> || </span>
          <span>Quote Code: </span><span className="uppercase font-bold">{activeQuote.quote_code}</span>
        </div>

      </div>
      
      {/* TWO-COLUMN LAYOUT */}
      <div className="flex flex-col lg:flex-row gap-6">
        
        {/* =======================================================================
            LEFT COLUMN: CONTEXT SIDEBAR (Who they are, Discovery, Notes)
            ======================================================================= */}
        <div className="w-full lg:w-1/3 flex flex-col gap-4">
          
          {/* Who They Are */}
          <div 
            onClick={() => setIsWhoOpen(true)}
            className="group cursor-pointer border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis hover:bg-dsi-background/30 transition-all shadow-sm"
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold tracking-wide flex items-center gap-2">
                <User className="w-4 h-4 text-dsi-selected" /> Who they are
              </h3>
              <span className="text-xs opacity-50 group-hover:opacity-100 transition-opacity text-dsi-selected">View Details &rarr;</span>
            </div>
            <p className="text-xs opacity-70 line-clamp-2">
              {activeSubmission.entity_name} • {activeSubmission.submission_data?.industry || 'Unknown Industry'} • {activeSubmission.submission_data?.geography || 'Unknown Geo'}
            </p>
          </div>

          {/* Discovery */}
          <div 
            onClick={() => setIsDiscoveryOpen(true)}
            className="group cursor-pointer border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis hover:bg-dsi-background/30 transition-all shadow-sm"
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold tracking-wide flex items-center gap-2">
                <Search className="w-4 h-4 text-dsi-selected" /> Discovery
              </h3>
              <span className="text-xs opacity-50 group-hover:opacity-100 transition-opacity text-dsi-selected">View Output &rarr;</span>
            </div>
            <p className="text-xs opacity-70 line-clamp-2">
              {activeVersion.discovery_output?.domain || 'No domain discovered'} • Confidence: {activeVersion.discovery_output?.confidence || 'N/A'}
            </p>
          </div>

          {/* Notes */}
          <div 
            onClick={() => setIsNotesOpen(true)}
            className="group cursor-pointer border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis hover:bg-dsi-background/30 transition-all shadow-sm"
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold tracking-wide flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-dsi-selected" /> Notes
              </h3>
              <span className="text-xs opacity-50 group-hover:opacity-100 transition-opacity text-dsi-selected">Manage Notes &rarr;</span>
            </div>
            <p className="text-xs opacity-70">
              {localNotes.length} Note(s) recorded on this version.
            </p>
          </div>

        </div>

        {/* =======================================================================
            RIGHT COLUMN: ANALYTICAL NARRATIVE
            ======================================================================= */}
        <div className="w-full lg:w-2/3 flex flex-col gap-6">

          {/* 1. SUBMISSION AT A GLANCE */}
          <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
            <h3 className="text-xs font-semibold uppercase tracking-wider opacity-50 mb-4 border-b border-dsi-outline/10 pb-2">
              Submission at a Glance
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4 text-sm">
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
                <span className="opacity-50 block text-xs mb-1">Rec. Premium</span>
                <span className="font-mono font-semibold text-dsi-selected">
                  {activeQuote?.recommended_premium ? `$${activeQuote.recommended_premium.toLocaleString()}` : 'Pending'}
                </span>
              </div>
              <div>
                <span className="opacity-50 block text-xs mb-1">Rec. Limit</span>
                <span className="font-mono font-semibold">
                  {activeQuote?.recommended_limit ? `$${activeQuote.recommended_limit.toLocaleString()}` : 'Pending'}
                </span>
              </div>
              <div>
                <span className="opacity-50 block text-xs mb-1">Decision</span>
                <span className="uppercase font-bold tracking-wider">{activeVersion.decision}</span>
              </div>
            </div>
          </div>

          {/* 2. KEY METRICS GRID */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis flex flex-col justify-between shadow-sm">
              <span className="text-xs font-semibold uppercase tracking-wider opacity-50 mb-2">Confidence</span>
              <span className="text-2xl font-mono font-bold text-dsi-selected">{((activeVersion.confidence || 0) * 100).toFixed(0)}%</span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis flex flex-col justify-between shadow-sm">
              <span className="text-xs font-semibold uppercase tracking-wider opacity-50 mb-2">Signal Coverage</span>
              <span className="text-2xl font-mono font-bold text-dsi-selected">{((activeVersion.signal_coverage || 0) * 100).toFixed(0)}%</span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis flex flex-col justify-between shadow-sm">
              <span className="text-xs font-semibold uppercase tracking-wider opacity-50 mb-2">Composite Score</span>
              <span className="text-2xl font-mono font-bold text-dsi-selected">{activeVersion.pure_composite_score?.toFixed(1) || "N/A"}</span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis flex flex-col justify-between shadow-sm">
              <span className="text-xs font-semibold uppercase tracking-wider opacity-50 mb-2">Score-Based Tier</span>
              <span className="text-2xl font-mono font-bold text-dsi-selected">Tier {activeVersion.score_based_tier || activeVersion.final_tier}</span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis flex flex-col justify-between shadow-sm">
              <span className="text-xs font-semibold uppercase tracking-wider opacity-50 mb-2">Final Tier</span>
              <span className="text-2xl font-mono font-bold text-dsi-selected">Tier {activeVersion.final_tier}</span>
            </div>
            <div className="border border-dsi-outline/20 rounded-xl p-4 bg-dsi-analysis flex flex-col justify-between shadow-sm">
              <span className="text-xs font-semibold uppercase tracking-wider opacity-50 mb-2">Tier Label</span>
              <span className="text-lg font-bold text-dsi-selected uppercase truncate" title={activeVersion.tier_label}>{activeVersion.tier_label}</span>
            </div>
          </div>

          {/* 3. LOSS & EXPOSURE */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
              <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
                <TrendingUp className="w-4 h-4 text-dsi-selected" /> Loss Propensity
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="opacity-50 block text-xs">Cohort ID</span>
                  <span className="font-mono font-semibold">{activeVersion.loss_cohort_name || "Unknown"}</span>
                </div>
                <div>
                  <span className="opacity-50 block text-xs">Propensity Band</span>
                  <span className="font-mono font-semibold text-dsi-selected">{activeVersion.loss_propensity_band || "N/A"}</span>
                </div>
                <div>
                  <span className="opacity-50 block text-xs">Cohort Confidence</span>
                  <span className="font-mono font-semibold">
                    {((activeVersion.loss_confidence || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div>
                  <span className="opacity-50 block text-xs">Score Velocity</span>
                  <span className={`font-mono font-bold ${activeVersion.loss_score_velocity > 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {activeVersion.loss_score_velocity > 0 ? '+' : ''}{activeVersion.loss_score_velocity || 0}
                  </span>
                </div>
              </div>
            </div>

            <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
              <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
                <BarChart3 className="w-4 h-4 text-dsi-selected" /> Exposure Assessment
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="opacity-50 block text-xs">Exposure Value (TIV/Rev)</span>
                  <span className="font-mono font-semibold">${(activeVersion.exposure_value || 0).toLocaleString()}</span>
                </div>
                <div>
                  <span className="opacity-50 block text-xs">Band Label</span>
                  <span className="font-mono font-semibold text-dsi-selected">{activeVersion.exposure_band_label || "N/A"}</span>
                </div>
                <div className="col-span-2">
                  <span className="opacity-50 block text-xs">Calculated Modifier</span>
                  <span className="font-mono font-semibold">{activeVersion.exposure_modifier?.toFixed(3) || "1.000"}x</span>
                </div>
              </div>
            </div>
          </div>

          {/* 4. SIGNAL GROUPS */}
          <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
            <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
              <Activity className="w-4 h-4 text-dsi-selected" /> Signal Group Breakdown
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
              {Object.entries(activeVersion.group_scores || {}).length === 0 ? (
                <div className="text-xs opacity-50 italic col-span-2">No group score data available.</div>
              ) : (
                Object.entries(activeVersion.group_scores).map(([group, groupData]: any) => {
                  const displayScore = groupData?.risk_score || groupData?.loss_score || 0;
                  return (
                    <div key={group} className="w-full">
                      <div className="flex justify-between text-xs font-semibold mb-1">
                        <span className="uppercase tracking-wider">{group.replace(/_/g, ' ')}</span>
                        <span className="font-mono">{displayScore.toFixed(1)}</span>
                      </div>
                      <div className="w-full bg-dsi-outline/10 rounded-full h-1.5 overflow-hidden">
                        <div 
                          className="bg-dsi-selected h-1.5 rounded-full" 
                          style={{ width: `${Math.min(100, displayScore)}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* 5. PRICING ANATOMY */}
          <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
            <h3 className="text-sm font-bold tracking-wide flex items-center gap-2 mb-4 border-b border-dsi-outline/10 pb-2">
              <Calculator className="w-4 h-4 text-dsi-selected" /> Pricing Anatomy
            </h3>
            
            <div className="flex flex-col md:flex-row gap-8">
              {/* Modifiers Table */}
              <div className="flex-1">
                <h4 className="text-xs uppercase tracking-wider opacity-50 mb-2">Applied Modifiers</h4>
                {activeVersion.modifiers_applied?.length > 0 ? (
                  <table className="w-full text-sm font-mono text-left">
                    <tbody>
                      {activeVersion.modifiers_applied.map((mod: any, idx: number) => (
                        <tr key={idx} className="border-b border-dsi-outline/5">
                          <td className="py-2 opacity-80">{mod.note || mod.source}</td>
                          <td className="py-2 text-right">
                            {Number(mod.applied ?? 1.0).toFixed(3)}x
                          </td>
                        </tr>
                      ))}
                      <tr className="bg-dsi-selected/5 font-bold">
                        <td className="py-2 px-2">Base Premium</td>
                        <td className="py-2 px-2 text-right">${activeVersion.base_premium?.toLocaleString()}</td>
                      </tr>
                      <tr className="bg-dsi-selected/10 font-bold text-dsi-selected">
                        <td className="py-2 px-2">Final Premium</td>
                        <td className="py-2 px-2 text-right">${activeVersion.premium_after_modifiers?.toLocaleString()}</td>
                      </tr>
                    </tbody>
                  </table>
                ) : (
                  <div className="text-xs opacity-50 italic">No modifiers applied.</div>
                )}
              </div>

              {/* Premium Options */}
              <div className="flex-1 border-t md:border-t-0 md:border-l border-dsi-outline/10 pt-4 md:pt-0 md:pl-8">
                <h4 className="text-xs uppercase tracking-wider opacity-50 mb-2">Limit Options</h4>
                {Object.keys(activeVersion.limit_premiums || {}).length > 0 ? (
                  <div className="space-y-2 font-mono text-sm">
                    {Object.entries(activeVersion.limit_premiums).map(([limit, premium]: any) => (
                      <div key={limit} className="flex justify-between p-2 rounded hover:bg-dsi-selected/5">
                        <span>${parseInt(limit).toLocaleString()} Limit</span>
                        <span className="font-bold text-dsi-selected">${premium.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs opacity-50 italic">No alternative limit options generated.</div>
                )}
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* =======================================================================
          MODALS
          ======================================================================= */}
      
      {/* 1. Who They Are Modal */}
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

      {/* 2. Discovery Modal */}
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

      {/* 3. Notes Modal */}
      <Modal isOpen={isNotesOpen} onClose={() => setIsNotesOpen(false)} title="Model Version Notes" icon={MessageSquare}>
        <div className="flex flex-col h-[50vh]">
          {/* Notes List */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
            {localNotes.length === 0 ? (
              <div className="text-center opacity-50 italic pt-10">No notes recorded yet.</div>
            ) : (
              localNotes.map((note: any, i: number) => {
                // Handle raw backend string format vs UI object format
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

          {/* Add Note Input */}
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