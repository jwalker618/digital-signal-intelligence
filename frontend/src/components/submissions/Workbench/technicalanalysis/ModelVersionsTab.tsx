"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { formatNumber, formatPercent, formatDate } from "@/lib/format";
import {
  GitBranch, GitCommit, Bot, User, Paperclip,
  ShieldCheck, ShieldAlert, AlertTriangle, ArrowDown, MessageSquare,
  LucideIcon,
} from "lucide-react";

import { StatusPill } from "@/components/base/content/primatives";
import { DECISION_PALETTE } from "@/lib/statusPalette";

const DECISION_ICON: Record<string, LucideIcon> = {
  approve: ShieldCheck,
  refer:   ShieldAlert,
  decline: AlertTriangle,
};

const TYPE_LABEL: Record<string, string> = {
  initial: 'Initial',
  referral_review: 'Referral Review',
  amendment: 'Amendment',
};

export default function ModelVersionsTab() {
  const { activeSubmission, activeQuote, modelVersions, fetchHistory } = useDsiStore();

  useEffect(() => {
    if (activeSubmission?.submission_code) {
      fetchHistory(activeSubmission.submission_code);
    }
  }, [activeSubmission?.submission_code, fetchHistory]);

  return (
    <div className="
      w-full no-scrollbar
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
            {activeQuote?.status === 'bound' && (
              <span>
                  <span className="text-sm">Bound Date:</span><span className="pl-2 uppercase font-bold">{activeQuote?.bound_at ? new Date(activeQuote.bound_at).toLocaleDateString() : 'N/A'}</span>
                  <span className="text-sm">Policy Reference:</span><span className="pl-2 uppercase font-bold">{activeQuote?.policy_number || 'Pending'}</span>
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
          <GitBranch className="icon"/><span className="text-sm">Version Lineage ({modelVersions.length} version{modelVersions.length !== 1 ? 's' : ''})</span>
        </div>
        <div className="
          flex flex-col flex-1
          border-b-3 border-dsi-contrast-background
          overflow-x-hidden border-collapse
          rounded-b-xl
          bg-dsi-analysis shadow-sm
          pt-6 pb-6
        ">
          <div className="pl-dsi-pad pr-dsi-pad space-y-0 relative before:absolute before:inset-0 before:ml-6 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-dsi-outline/20 before:to-transparent">
            {modelVersions.map((mv: any, i: number) => {
              // Compute delta from previous version (next in array since latest is first)
              const prevVersion = modelVersions[i + 1] || null;
              const mvScore = mv.pure_composite_score ?? mv.composite_score;
              const prevScore = prevVersion?.pure_composite_score ?? prevVersion?.composite_score;
              const scoreDelta = prevVersion && mvScore != null && prevScore != null
                ? mvScore - prevScore
                : null;
              const mvTier = mv.final_tier ?? mv.tier;
              const prevTier = prevVersion?.final_tier ?? prevVersion?.tier;
              const tierChanged = prevVersion && mvTier !== prevTier;

              const decision = (mv.decision || '').toLowerCase();
              const versionType = TYPE_LABEL[mv.version_type] || mv.version_type || 'Version';

              // Conditions & notes counts
              const condCount = (mv.signal_conditions?.length || 0) + (mv.query_conditions?.length || 0);
              const notesCount = mv.notes?.length || 0;
              const referralCount = mv.referral_reasons?.length || 0;

              return (
                <div key={mv.version_id || i}>
                  <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">

                    {/* Timeline Node */}
                    <div className={`
                      flex items-center justify-center w-10 h-10 rounded-full border-4 border-dsi-background shrink-0
                      md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2
                      shadow shadow-dsi-background
                      ${mv.is_latest ? 'bg-dsi-selected text-dsi-background' : 'bg-dsi-outline/20 text-dsi-selected'}
                    `}>
                      <GitCommit className="w-5 h-5" />
                    </div>

                    {/* Content Card */}
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-dsi-outline/20 bg-dsi-background/30 hover:bg-dsi-selected/5 transition-colors">

                      {/* Header: version number + type + active badge */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold uppercase tracking-wider opacity-70">
                            Version {mv.version_number}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-dsi-outline/10 opacity-50">
                            {versionType}
                          </span>
                        </div>
                        {mv.is_latest && (
                          <span className="text-[10px] bg-dsi-approve/10 text-dsi-approve px-2 py-0.5 rounded font-bold uppercase">
                            Active
                          </span>
                        )}
                      </div>

                      {/* Score + Tier + Decision row */}
                      <div className="flex items-center gap-4 mb-3">
                        <div className="flex-1">
                          <div className="text-xs opacity-50 uppercase tracking-wider mb-0.5">Score</div>
                          <div className="flex items-baseline gap-1.5">
                            <span className="text-xl font-bold text-dsi-selected">
                              {mvScore != null ? formatNumber(mvScore, 1) : "N/A"}
                            </span>
                            {scoreDelta != null && Math.abs(scoreDelta) > 0.1 && (
                              <span className={`text-xs font-bold ${scoreDelta > 0 ? 'text-dsi-negative' : 'text-dsi-approve'}`}>
                                {scoreDelta > 0 ? '+' : ''}{formatNumber(scoreDelta, 1)}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex-1">
                          <div className="text-xs opacity-50 uppercase tracking-wider mb-0.5">Tier</div>
                          <div className="flex items-baseline gap-1.5">
                            <span className="text-sm font-bold text-dsi-selected">
                              Tier {mvTier} ({mv.tier_label})
                            </span>
                            {tierChanged && (
                              <span className="text-[10px] text-dsi-refer font-bold">
                                was Tier {prevTier}
                              </span>
                            )}
                          </div>
                        </div>
                        {DECISION_PALETTE[decision] && (
                          <div>
                            <StatusPill
                              palette={DECISION_PALETTE}
                              status={decision}
                              lucideIcon={DECISION_ICON[decision]}
                              size="md"
                            >
                              {decision}
                            </StatusPill>
                          </div>
                        )}
                      </div>

                      {/* Stats row: confidence, coverage, conditions, notes */}
                      <div className="flex items-center gap-3 text-[10px] opacity-50 mb-3">
                        {mv.confidence != null && (
                          <span>Conf: {formatPercent(mv.confidence, 0)}</span>
                        )}
                        {mv.signal_coverage != null && (
                          <span>Cov: {formatPercent(mv.signal_coverage, 0)}</span>
                        )}
                        {condCount > 0 && (
                          <span className="text-dsi-refer/70">{condCount} condition{condCount !== 1 ? 's' : ''}</span>
                        )}
                        {referralCount > 0 && (
                          <span className="text-dsi-negative/70">{referralCount} referral flag{referralCount !== 1 ? 's' : ''}</span>
                        )}
                        {notesCount > 0 && (
                          <span className="flex items-center gap-0.5">
                            <MessageSquare className="w-2.5 h-2.5" /> {notesCount}
                          </span>
                        )}
                      </div>

                      {/* Footer: created by + timestamp */}
                      <div className="flex items-center justify-between pt-2 border-t border-dsi-outline/10 text-xs opacity-60">
                        <span className="flex items-center gap-1">
                          {mv.created_by === "system" ? <Bot className="w-3 h-3" /> : <User className="w-3 h-3" />}
                          {mv.created_by}
                        </span>
                        <span>{formatDate(mv.created_at)}</span>
                      </div>
                    </div>

                  </div>

                  {/* Delta connector between versions */}
                  {i < modelVersions.length - 1 && (
                    <div className="flex justify-center py-1">
                      <ArrowDown className="w-4 h-4 opacity-20" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
