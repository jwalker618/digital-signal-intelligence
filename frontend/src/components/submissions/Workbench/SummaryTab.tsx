"use client";

import { useState, useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import Modal from "@/components/Modal";

import {
  User, Search, MessageSquare, Plus, 
  ShieldCheck, Layers, 
  Building2, ShieldX, ShieldQuestionMark, Scale,
  TrendingUpDown, Globe,
  ChartNoAxesGantt,
} from "lucide-react";

import { formatNum, formatNumber, formatPercent, formatDate, formatText } from "@/lib/format";
import "@/app/globals.css";

const DECISION_STYLE: Record<string, { bg: string; }> = {
  approve: { bg: 'bg-dsi-approve', },
  refer: {   bg: 'bg-dsi-refer',   },
  decline: { bg: 'bg-dsi-decline', },
};

export default function SummaryTab() {
  const { activeSubmission, activeQuote, activeVersion, activeCommercial, activeRisk, addNote,  } = useDsiStore();

  const [isWhoOpen, setIsWhoOpen] = useState(false);
  const [isDiscoveryOpen, setIsDiscoveryOpen] = useState(false);
  const [isBaseOpen, setIsBaseOpen] = useState(false);  
  const [newNoteText, setNewNoteText] = useState("");
  const [isAddingNote, setIsAddingNote] = useState(false);

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
      <div className={`rounded-xl border-b-3 border-dsi-contrast-background ${dStyle.bg} shadow-sm py-4 mb-4`}>
        {/* Top row: Decision + status context */}
        
        <div className="flex items-center justify-between pb-3 border-b border-dsi-outline/50">
          
          <div className="flex items-center gap-4 pl-dsi-pad">
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
                <span className="block text-xs">Auto-approved by engine</span>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-6 pr-dsi-gap">
            <div>
              <span className="block dsi-analysis-description">Status</span>
              <span className="dsi-analysis-item">{formatText(activeQuote.status, "upper")}</span>
            </div>
            {(activeQuote?.status === 'draft' || activeQuote?.status === 'ready') && (
              <>
                <div>
                  <span className="block dsi-analysis-description">Valid From</span>
                  <span className="dsi-analysis-item">{formatDate(activeQuote.valid_from)}</span>
                </div>
                <div>
                  <span className="block dsi-analysis-description">Valid Until</span>
                  <span className="dsi-analysis-item">{formatDate(activeQuote.valid_until)}</span>
                </div>
              </>
            )}
            {activeQuote?.status === 'bound' && (
              <>
                <div>
                  <span className="block dsi-analysis-description">Bound Date</span>
                  <span className="dsi-analysis-item">{formatDate(activeQuote.bound_at)}</span>
                </div>
                <div>
                  <span className="block dsi-analysis-description">Policy Ref</span>
                  <span className="dsi-analysis-item">{formatText(activeQuote.policy_number, "upper", "pending")}</span>
                </div>
              </>
            )}
          </div>

        </div>
        
        {/* Bottom row: Hero numbers */}
        <div className="grid grid-cols-[10%_20%_10%_15%_15%_15%]">

          {/* row 1 */}
          <div className="dsi-grid-table-header">Final Composite Score</div>
          <div className="dsi-grid-table-header">Final Tier</div>
          <div className="dsi-grid-table-header">Currency</div>
          <div className="dsi-grid-table-header">Recommended Technical Premium</div>
          <div className="dsi-grid-table-header">Recommended Technical Limit</div>
          <div className="dsi-grid-table-header border-r-0">Gross Premium</div>
          
          {/* row 2 */}
          <div className="dsi-grid-table-item">{formatNumber(activeVersion.final_composite_score, 1)}</div>
          <div className="dsi-grid-table-item">T{activeVersion.final_tier} ({activeVersion.tier_label})</div>
          <div className="dsi-grid-table-item">{formatText(activeCommercial.base_currency, "upper", "tbc")}</div>
          <div className="dsi-grid-table-item">{formatNumber(activeQuote.recommended_premium, 0)}</div>
          <div className="dsi-grid-table-item">{formatNumber(activeQuote.recommended_limit, 0)}</div>
          <div className="dsi-grid-table-item border-r-0">{formatNumber(activeCommercial.gross_premium, 0)}</div>

        </div>          

      </div>

      <div className="grid grid-cols-[10%_90%]">
      {/* ═══════════════════════════════════════════════════════════════════
          WHO / DISCOVERY / BASE VERSION
          ═══════════════════════════════════════════════════════════════════ */}      
        <div className="flex flex-col gap-4 group cursor-pointer">
          
          <div onClick={() => setIsWhoOpen(true)} className="dsi-section-analysis rounded-xl">
            <div className="dsi-analysis-item text-left">
              <span className="block">Who are they</span>
              <span className="block font-normal text-xs hover:text-dsi-selected">View &rarr;</span>
            </div>  
          </div>

          <div onClick={() => setIsDiscoveryOpen(true)} className="dsi-section-analysis rounded-xl">
            <div className="dsi-analysis-item text-left">
              <span className="block">Discovery</span>
              <span className="block font-normal text-xs hover:text-dsi-selected">View &rarr;</span>
            </div>  
          </div>

          <div onClick={() => setIsBaseOpen(true)} className="dsi-section-analysis rounded-xl">
            <div className="dsi-analysis-item text-left">
              <span className="block">Model details</span>
              <span className="block font-normal text-xs hover:text-dsi-selected">View &rarr;</span>
            </div>  
          </div>

        </div>

        {/* ═══════════════════════════════════════════════════════════════════
            THREE PILLAR ASSESSMENT
            ═══════════════════════════════════════════════════════════════════ */}
        <div className="flex flex-col ml-dsi-pad">
          <div className="dsi-section-header">
            <Layers className="icon"/>
            <span className="text-sm">Three Pillar Assessment</span>
          </div>

          <div className="dsi-section-analysis">
            <div className="grid grid-cols-1 md:grid-cols-3">
              
              {/* RISK */}
              <div className="border-r-1 border-dsi-outline/50">
                <div className="flex gap-2 ml-dsi-pad pt-1 pb-1">
                  <ChartNoAxesGantt className="icon"/>
                  <span className="text-sm">Risk</span>
                </div>
                <div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Final Composite Score</span>
                    <span className="dsi-analysis-item">{formatNumber(activeVersion.final_composite_score, 1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Score-Based Tier</span>
                    <span className="dsi-analysis-item">T{activeVersion.score_based_tier}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Final Tier</span>
                    <span className="dsi-analysis-item">T{activeVersion.final_tier} ({activeVersion.tier_label})</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Confidence</span>
                    <span className="dsi-analysis-item">{((activeVersion.confidence || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Signal Coverage</span>
                    <span className="dsi-analysis-item">{((activeVersion.signal_coverage || 0) * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
              
              {/* LOSS */}
              <div className="border-r-1 border-dsi-outline/50">
                <div className="flex gap-2 ml-dsi-pad pt-1 pb-1">
                  <TrendingUpDown className="icon" />
                  <span className="text-sm">Loss Propensity</span>
                </div>
                <div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Propensity Band</span>
                    <span className="dsi-analysis-item">{activeVersion.loss_propensity_band?.replace(/_/g, ' ') || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Combined Modifier</span>
                    <span className="dsi-analysis-item">{activeVersion.loss_combined_modifier?.toFixed(3) || '1.000'}x</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Trend</span>
                    <span className={`font-bold ${activeVersion.loss_trend_direction?.toLowerCase().includes('improv') ? 'text-dsi-positive' : activeVersion.loss_trend_direction?.toLowerCase().includes('deter') ? 'text-dsi-negative' : 'opacity-70'}`}>
                      {activeVersion.loss_trend_direction?.replace(/_/g, ' ') || 'Stable'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Cohort</span>
                    <span className="dsi-analysis-item">{activeVersion.loss_cohort_name || 'Unknown'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Model Confidence</span>
                    <span className="dsi-analysis-item">{activeVersion.loss_confidence != null ? `${(activeVersion.loss_confidence * 100).toFixed(0)}%` : 'N/A'}</span>
                  </div>
                </div>
              </div>
              
              {/* EXPOSURE */}
              <div>
                <div className="flex gap-2 ml-dsi-pad pt-1 pb-1">
                  <Globe className="icon" />
                  <span className="text-sm">Exposure</span>
                </div>
                <div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Exposure Value</span>
                    <span className="dsi-analysis-item">{formatNumber(activeVersion.exposure_value, 0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Exposure Band</span>
                    <span className="dsi-analysis-item">{activeVersion.exposure_band_label || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Modifier</span>
                    <span className="dsi-analysis-item">{activeVersion.exposure_modifier?.toFixed(3) || '1.000'}x</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Size Score</span>
                    <span className="dsi-analysis-item">{formatNum(activeVersion.exposure_size_score, 1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="dsi-analysis-description">Method</span>
                    <span className="dsi-analysis-item ">{activeVersion.exposure_assessment_method?.replace(/_/g, ' ') || 'N/A'}</span>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>

      </div>

      {/* ═══════════════════════════════════════════════════════════════════
          COMMERCIAL & RISK TERMS SUMMARY
          ═══════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 pb-4">  
        
        <div className="flex flex-col">
          <div className="dsi-section-header">
            <Building2 className="icon"/>
            <span className="text-sm">Commercial Summary</span>
          </div>

          <div className="dsi-section-analysis">
            {activeCommercial ? (
              <div>
                <div className="flex justify-between">
                  <span className="dsi-analysis-description">Entity</span>
                  <span className="dsi-analysis-item">{activeCommercial.entity_name || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="dsi-analysis-description">Offered Premium</span>
                  <span className="dsi-analysis-item">{formatNumber(activeCommercial.offered_premium, 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="dsi-analysis-description">Gross Premium</span>
                  <span className="dsi-analysis-item">{formatNumber(activeCommercial.gross_premium, 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="dsi-analysis-description">Currency</span>
                  <span className="dsi-analysis-item">{activeCommercial.base_currency || "USD"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="dsi-analysis-description">Distribution</span>
                  <span className="dsi-analysis-item">{activeCommercial.distribution_type || "N/A"}</span>
                </div>
              </div>
            ) : (
              <p className="text-xs opacity-50 italic text-center py-4 text-wrap">No commercial terms available</p>
            )}
          </div>

        </div>

        {/* Risk Terms Summary Card */}
        <div className="flex flex-col">
          <div className="dsi-section-header">
            <Scale className="icon"/>
            <span className="text-sm">Risk Terms Summary</span>
          </div>

          <div className="dsi-section-analysis">
            {activeRisk ? (
              <div>
                <div className="flex justify-between">
                  <span className="dsi-analysis-description">Deductible Type</span>
                  <span className="dsi-analysis-item">{activeRisk.deductible_type || "N/A"}</span>
                  </div>
                <div className="flex justify-between">
                  <span className="dsi-analysis-description">Deductible Amount</span>
                  <span className="dsi-analysis-item">{formatNumber(activeRisk.deductible_amount, 0)}</span>
                  </div>
                <div className="flex justify-between">
                  <span className="dsi-analysis-description">SIR</span>
                  <span className="dsi-analysis-item">{formatNumber(activeRisk.sir_amount, 0, 'n/a')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="dsi-analysis-description">Aggregate Limit</span>
                  <span className="dsi-analysis-item">{formatNumber(activeRisk.aggregate_limit, 0, 'n/a')}</span>
                  </div>
                <div className="flex justify-between">
                  <span className="dsi-analysis-description">Coverage Terms</span>
                  <span className="dsi-analysis-item">
                    {activeRisk.coverage_terms ? `${Object.keys(activeRisk.coverage_terms).length} terms` : "N/A"}
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
        
        <div className="dsi-section-header">
          <MessageSquare className="icon"/>
          <span className="text-sm">Notes ({notes.length})</span>
        </div>

        <div className="dsi-section-analysis">

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


