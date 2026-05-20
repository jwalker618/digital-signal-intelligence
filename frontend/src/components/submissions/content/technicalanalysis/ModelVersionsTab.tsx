"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { formatNumber, formatPercent, formatDate } from "@/lib/format";
import {
  GitBranch, GitCommit, Bot, User,
  ArrowDown, MessageSquare,
} from "lucide-react";

import { CardGrid, StandardCard } from "@/components/base/cards";
import { SubmissionStatusPill } from "@/components/base/content/primatives";
import { KEYTERM } from "@/lib/keytermPalette";

const TYPE_LABEL: Record<string, string> = {
  initial: "Initial",
  referral_review: "Referral Review",
  amendment: "Amendment",
};

export default function ModelVersionsTab() {
  const { activeSubmission, modelVersions, fetchHistory } = useDsiStore();

  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const code = (activeSubmission as any)?.submission_code;
    if (code) fetchHistory(code);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  }, [(activeSubmission as any)?.submission_code, fetchHistory]);

  return (
    <div className="w-full pb-12 pt-generate-pad">
      <CardGrid cols="grid-cols-1" className="gap-4">

        <StandardCard
          lucideIcon={GitBranch}
          title={`Version Lineage (${modelVersions.length} version${modelVersions.length !== 1 ? "s" : ""})`}
        >
          <div className="pt-6 pb-6 relative before:absolute before:inset-0 before:ml-6 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-generate-text-outline/20 before:to-transparent">
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {modelVersions.map((mv: any, i: number) => {
              const prevVersion = modelVersions[i + 1] || null;
              const mvScore = mv.pure_composite_score ?? mv.composite_score;
              const prevScore = prevVersion?.pure_composite_score ?? prevVersion?.composite_score;
              const scoreDelta =
                prevVersion && mvScore != null && prevScore != null ? mvScore - prevScore : null;
              const mvTier = mv.final_tier ?? mv.tier;
              const prevTier = prevVersion?.final_tier ?? prevVersion?.tier;
              const tierChanged = prevVersion && mvTier !== prevTier;

              const decision = (mv.decision || "").toLowerCase();
              const versionType = TYPE_LABEL[mv.version_type] || mv.version_type || "Version";

              const condCount = (mv.signal_conditions?.length || 0) + (mv.query_conditions?.length || 0);
              const notesCount = mv.notes?.length || 0;
              const referralCount = mv.referral_reasons?.length || 0;

              return (
                <div key={mv.version_id || i}>
                  <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                    {/* Timeline Node */}
                    <div
                      className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-generate-light-background shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow shadow-generate-light-background ${
                        mv.is_latest
                          ? "bg-generate-text-input text-generate-light-background"
                          : "bg-generate-text-outline/20 text-generate-text-input"
                      }`}
                    >
                      <GitCommit className="w-5 h-5" />
                    </div>

                    {/* Content card */}
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-generate-text-outline/20 bg-generate-light-background/30 hover:bg-generate-text-input/5 transition-colors">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold uppercase tracking-wider opacity-70">
                            Version {mv.version_number}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-generate-text-outline/10 opacity-50">
                            {versionType}
                          </span>
                        </div>
                        {mv.is_latest && (
                          <span className="text-[10px] bg-generate-text-good/10 text-generate-text-good px-2 py-0.5 rounded font-bold uppercase">
                            Active
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-4 mb-3">
                        <div className="flex-1">
                          <div className="text-xs opacity-50 uppercase tracking-wider mb-0.5">Score</div>
                          <div className="flex items-baseline gap-1.5">
                            <span className="text-xl font-bold text-generate-text-input">
                              {mvScore != null ? formatNumber(mvScore, 1) : "N/A"}
                            </span>
                            {scoreDelta != null && Math.abs(scoreDelta) > 0.1 && (
                              <span
                                className={`text-xs font-bold ${
                                  scoreDelta > 0 ? "text-generate-text-bad" : "text-generate-text-good"
                                }`}
                              >
                                {scoreDelta > 0 ? "+" : ""}
                                {formatNumber(scoreDelta, 1)}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex-1">
                          <div className="text-xs opacity-50 uppercase tracking-wider mb-0.5">Tier</div>
                          <div className="flex items-baseline gap-1.5">
                            <span className="text-sm font-bold text-generate-text-input">
                              Tier {mvTier} ({mv.tier_label})
                            </span>
                            {tierChanged && (
                              <span className="text-[10px] text-generate-text-maybe font-bold">
                                was Tier {prevTier}
                              </span>
                            )}
                          </div>
                        </div>
                        {KEYTERM[decision] && <SubmissionStatusPill decision={decision} />}
                      </div>

                      <div className="flex items-center gap-3 text-[10px] opacity-50 mb-3">
                        {mv.confidence != null && <span>Conf: {formatPercent(mv.confidence, 0)}</span>}
                        {mv.signal_coverage != null && <span>Cov: {formatPercent(mv.signal_coverage, 0)}</span>}
                        {condCount > 0 && (
                          <span className="text-generate-text-maybe/70">
                            {condCount} condition{condCount !== 1 ? "s" : ""}
                          </span>
                        )}
                        {referralCount > 0 && (
                          <span className="text-generate-text-bad/70">
                            {referralCount} referral flag{referralCount !== 1 ? "s" : ""}
                          </span>
                        )}
                        {notesCount > 0 && (
                          <span className="flex items-center gap-0.5">
                            <MessageSquare className="w-2.5 h-2.5" /> {notesCount}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-generate-text-outline/10 text-xs opacity-60">
                        <span className="flex items-center gap-1">
                          {mv.created_by === "system" ? <Bot className="w-3 h-3" /> : <User className="w-3 h-3" />}
                          {mv.created_by}
                        </span>
                        <span>{formatDate(mv.created_at)}</span>
                      </div>
                    </div>
                  </div>

                  {i < modelVersions.length - 1 && (
                    <div className="flex justify-center py-1">
                      <ArrowDown className="w-4 h-4 opacity-20" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </StandardCard>

      </CardGrid>
    </div>
  );
}
