"use client";

import { useState, useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import Modal from "@/components/Modal";

import {
  User, Search, MessageSquare, Plus, ShieldCheck, Layers, Building2, ShieldX, ShieldQuestionMark, Scale,
  TrendingUpDown, Globe, ChartNoAxesGantt, ArrowUpRight,
} from "lucide-react";

import { formatNumber, formatPercent, formatDate, formatText } from "@/lib/format";
import { getSortedItems, getOtherRow, } from "@/lib/utils";

import "@/app/globals.css";

const DECISION_STYLE: Record<string, { bg: string; }> = {
  approve: { bg: 'bg-dsi-approve', },
  refer: {   bg: 'bg-dsi-refer',   },
  decline: { bg: 'bg-dsi-decline', },
  pending: { bg: 'bg-dsi-muted', },
};

export default function SummaryTab() {
  const { 
    activeSubmission, 
    activeQuote, 
    activeVersion, 
    activeCommercial, 
    activeRisk, 
    addNote,  
  } = useDsiStore();

  const [isWhoOpen, setIsWhoOpen] = useState(false);
  const [isDiscoveryOpen, setIsDiscoveryOpen] = useState(false);
  const [isBaseOpen, setIsBaseOpen] = useState(false);  
  const [newNoteText, setNewNoteText] = useState("");
  const [isAddingNote, setIsAddingNote] = useState(false);

  const riskGroup = getSortedItems(activeVersion.group_scores, "risk_weight");
  const lossGroup = getSortedItems(activeVersion.loss_group_scores, "loss_weight", "_composite");
  const exposureGroup = getSortedItems(activeVersion.exposure_components.group_scores, "exposure_weight", "_composite");

  const riskGroupOther = getOtherRow(riskGroup, ["risk_contribution"]);
  const lossGroupOther = getOtherRow(lossGroup, ["severity_contribution", "frequency_contribution"]);
  const exposureGroupOther = getOtherRow(exposureGroup, ["size_contribution", "complexity_contribution"]);

  const handleAddNote = async () => {
    if (!newNoteText.trim() || !activeVersion?.version_code) return;
    setIsAddingNote(true);
    await addNote(activeVersion.version_code, newNoteText.trim(), "underwriter");
    setNewNoteText("");
    setIsAddingNote(false);
  };

  const decision = (activeVersion.decision || 'pending').toLowerCase();
  const notes = activeVersion.notes || [];

  return (
    <div className="
      w-full no-scrollbar 
      animate-in fade-in duration-500 pb-12"
      >

      {/* ═══════════════════════════════════════════════════════════════════
          DECISION BANNER — incorporates status, dates, policy info
          ═══════════════════════════════════════════════════════════════════ */}
      <div className={`
        sticky top-dsi-pad z-20 mb-24 bottom-12
        pt-3 pb-2
        rounded-xl 
        border-b-3 border-dsi-contrast-background 
        ${DECISION_STYLE[decision].bg} 
        shadow-sm`}>
        
        {/* Top row: Decision + status context */}
        <div className="flex items-center justify-between pb-3 border-b border-dsi-outline/50">
          
          <div className="flex items-center gap-4 pl-dsi-pad">
            {decision === 'approve' ? 
              <ShieldCheck className={`w-10 h-10 text-dsi-selected`} /> :
             decision === 'refer' ? 
              <ShieldQuestionMark className={`w-10 h-10 text-dsi-selected`} /> :
              <ShieldX className={`w-10 h-10 text-dsi-selected`} />}
            <div>
              <span className={`text-2xl font-bold uppercase tracking-wider text-dsi-selected`}>{decision}</span>
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

      <div className="grid grid-cols-[10%_90%] ">
      {/* ═══════════════════════════════════════════════════════════════════
          WHO / DISCOVERY / BASE VERSION
          ═══════════════════════════════════════════════════════════════════ */}      
        <div className="flex flex-col gap-4 group cursor-pointer">
          
          <div onClick={() => setIsWhoOpen(true)}>
            <div className="dsi-popup-header">
              <span className="content-center text-xs">Expand</span>
              <ArrowUpRight className="icon"/>
            </div>
            <div className="dsi-section-analysis pl-dsi-pad font-bold">Who are they?</div>
          </div>

          <div onClick={() => setIsDiscoveryOpen(true)}>
            <div className="dsi-popup-header">
              <span className="content-center text-xs">Expand</span>
              <ArrowUpRight className="icon"/>
            </div>
            <div className="dsi-section-analysis pl-dsi-pad font-bold">Discovery</div> 
          </div>

          <div onClick={() => setIsBaseOpen(true)}>
            <div className="dsi-popup-header">
              <span className="content-center text-xs">Expand</span>
              <ArrowUpRight className="icon"/>
            </div>
            <div className="dsi-section-analysis pl-dsi-pad font-bold">Model Details</div> 
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
              <div className="grid grid-cols-3 gap-dsi-gap">
                
                {/* RISK */}
                <div>
                  <div className="flex gap-2 ml-dsi-pad pt-1">
                    <ChartNoAxesGantt className="icon"/>
                    <span className="text-sm underline">Risk Analysis</span>
                  </div>
                  
                  <div className="grid grid-cols-[50%_20%]">

                    <div className="dsi-analysis-description pt-dsi-pad">Overall Confidence</div>
                    <div className="dsi-analysis-item pt-dsi-pad text-right">{formatPercent(activeVersion.confidence,0)}</div>
                    

                    <div className="dsi-analysis-description">Calculation Overridden</div>
                    <div className="dsi-analysis-item text-left">{activeVersion.tier_overrides.length > 0 ? (<span>Yes</span>) : (<span>No</span>)}</div>
                  
                    <div className="dsi-analysis-description text-xs pt-dsi-pad">Composite Score Calculation</div>
                    <div className="pt-dsi-pad"></div>
                    
                    <div className="dsi-analysis-description text-xs border-b-1 border-dsi-outline/50 ml-dsi-pad pl-0 pb-1">Group</div>
                    <div className="dsi-analysis-description pl-0 pr-0 text-xs text-center border-b-1 border-dsi-outline/50 pb-1">Contribution</div>
                                       
                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(riskGroup[0]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(riskGroup[0]?.risk_contribution,2)}</div>
                    
                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(riskGroup[1]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(riskGroup[1]?.risk_contribution,2)}</div>
                    
                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(riskGroup[2]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(riskGroup[2]?.risk_contribution,2)}</div>

                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(riskGroupOther[0]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(riskGroupOther[0]?.risk_contribution,2)}</div>

                  </div>
                </div>
                
                {/* LOSS */}
                <div>
                  <div className="flex gap-2 ml-dsi-pad pt-1">
                    <TrendingUpDown className="icon" />
                    <span className="text-sm">Loss Propensity</span>
                  </div>
                  
                  <div className="grid grid-cols-[50%_20%_20%]">

                    <div className="dsi-analysis-description pt-dsi-pad">Loss Confidence</div>
                    <div className="dsi-analysis-item pt-dsi-pad text-right">{formatPercent(activeVersion.loss_confidence,0)}</div>
                    <div className="pt-dsi-pad"></div>

                    <div className="dsi-analysis-description">Combined Modifier</div>
                    <div className="dsi-analysis-item text-right">{formatPercent(activeVersion.loss_combined_modifier,0)}</div>
                    <div></div>

                    <div className="dsi-analysis-description text-xs pt-dsi-pad">Loss Propensity Calculation</div>
                    <div className="pt-dsi-pad"></div>
                    <div className="pt-dsi-pad"></div>

                    <div className="dsi-analysis-description text-xs border-b-1 border-dsi-outline/50 ml-dsi-pad pl-0 pb-1">Group</div>
                    <div className="dsi-analysis-description pl-0 pr-0 text-xs text-center border-b-1 border-dsi-outline/50 pb-1">Severity</div>
                    <div className="dsi-analysis-description pl-0 pr-0 text-xs text-center border-b-1 border-dsi-outline/50 pb-1">Frequency</div>

                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(lossGroup[0]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(lossGroup[0]?.severity_contribution,2)}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(lossGroup[0]?.frequency_contribution,2)}</div>

                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(lossGroup[1]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(lossGroup[1]?.severity_contribution,2)}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(lossGroup[1]?.frequency_contribution,2)}</div>

                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(lossGroup[2]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(lossGroup[2]?.severity_contribution,2)}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(lossGroup[2]?.frequency_contribution,2)}</div> 

                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(lossGroupOther[0]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(lossGroupOther[0]?.severity_contribution,2)}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(lossGroupOther[0]?.frequency_contribution,2)}</div> 

                  </div>

                </div>
                
                {/* EXPOSURE */}
                <div>
                  <div className="flex gap-2 ml-dsi-pad pt-1">
                    <Globe className="icon" />
                    <span className="text-sm">Exposure</span>
                  </div>

                  <div className="grid grid-cols-[50%_20%_20%]">

                    <div className="dsi-analysis-description pt-dsi-pad">Exposure Band</div>
                    <div className="dsi-analysis-item pt-dsi-pad text-left">{formatText(activeVersion.exposure_band_label, "upper")}</div>
                    <div className="pt-dsi-pad"></div>

                    <div className="dsi-analysis-description">Combined Modifier</div>
                    <div className="dsi-analysis-item text-right">{formatPercent(activeVersion.exposure_modifier,0)}</div>
                    <div></div>

                    <div className="dsi-analysis-description text-xs pt-dsi-pad">Exposure Calculation</div>
                    <div className="pt-dsi-pad"></div>
                    <div className="pt-dsi-pad"></div>

                    <div className="dsi-analysis-description text-xs border-b-1 border-dsi-outline/50 ml-dsi-pad pl-0 pb-1">Group</div>
                    <div className="dsi-analysis-description pl-0 pr-0 text-xs text-center border-b-1 border-dsi-outline/50 pb-1">Size</div>
                    <div className="dsi-analysis-description pl-0 pr-0 text-xs text-center border-b-1 border-dsi-outline/50 pb-1">Complexity</div>

                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(exposureGroup[0]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(exposureGroup[0]?.size_contribution,2)}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(exposureGroup[0]?.complexity_contribution,2)}</div>

                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(exposureGroup[1]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(exposureGroup[1]?.size_contribution,2)}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(exposureGroup[1]?.complexity_contribution,2)}</div>

                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(exposureGroup[2]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(exposureGroup[2]?.size_contribution,2)}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(exposureGroup[2]?.complexity_contribution,2)}</div> 

                    <div className="dsi-analysis-description text-xs border-r-1 border-dsi-outline/50">{formatText(exposureGroupOther[0]?.name, "capitalize", "n/a")}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(exposureGroupOther[0]?.size_contribution,2)}</div>
                    <div className="dsi-analysis-item text-right">{formatNumber(exposureGroupOther[0]?.complexity_contribution,2)}</div> 

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
              <p className="dsi-user-message">No commercial terms available</p>
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
              <p className="dsi-user-message">No risk terms available</p>
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
              className="
                flex-1
                bg-dsi-contrast-analysis
                border-1 border-dsi-contrast-analysis/30
                pr-dsi-pad pl-dsi-pad ml-2 py-2
                text-sm 
                hover:text-dsi-selected
                hover:border-dsi-outline"
              onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
              disabled={isAddingNote}
            />
            <button
              onClick={handleAddNote}
              disabled={!newNoteText.trim() || isAddingNote}
              className="
                text-dsi-analysis text-sm 
                gap-1             
                bg-dsi-contrast-background
                hover:bg-dsi-selected
                pr-dsi-pad pl-dsi-pad mr-2
                flex items-center"
            >
              {isAddingNote ? 'Saving...' : 'Add'} <Plus className="icon" /> 
            </button>
          </div>
          
          {/* Notes list — reads from activeVersion.notes (persisted) */}
          {notes.length === 0 ? (
            <p className="dsi-user-message">No notes recorded yet. Add one above.</p>
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
                <span className="opacity-60">{formatText(key,"normal")}</span>
                <span className="font-bold text-right">
                  {typeof val === 'number' && key.toLowerCase().includes('revenue') ? `$${val.toLocaleString()}` : String(val)}
                </span>
              </div>
            ))}
          {Object.keys(activeSubmission.submission_data || {}).length === 0 && (
            <div className="dsi-user-message">No submission data available.</div>
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
            <div className="dsi-user-message">No discovery output available.</div>
          )}
        </div>
      </Modal>

    </div>
  );
}


