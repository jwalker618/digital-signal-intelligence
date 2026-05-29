"use client";

import { use } from "react";
import { Bot, GitBranch, GitCommitHorizontal, User } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { PageLoading } from "@/components/base/pageStates";
import { useDsiStore } from "@/store/dsiStore";
import { useEnsureFetched } from "@/store/useEnsureFetched";
import { formatText } from "@/lib/format";
import { fmtRelative } from "@/lib/utils";

/* ============================================================
 * Model Versions — mirrors reim_wb_b.jsx WbVersions (section 08).
 *
 * Single "Version Lineage" card containing a vertical timeline:
 *   - 44px circular marker per version (active = info-fill, others =
 *     surface-elev). Connecting line behind the markers.
 *   - Each card: header row (Version N · type badge · ACTIVE chip),
 *     3-col body (Score with delta · Tier with prev hint · decision
 *     chip), metadata footer (confidence, coverage, conditions, refs,
 *     notes, author · timestamp).
 * ============================================================ */

type Version = {
  version_number?: number;
  version_type?: string;
  final_composite_score?: number;
  previous_composite_score?: number;
  final_tier?: number;
  previous_tier?: number;
  decision?: string;
  author?: string;
  created_by?: string;
  created_at?: string;
  is_latest?: boolean;
  confidence?: number;
  signal_coverage?: number;
  signal_conditions?: unknown[];
  referral_reasons?: unknown[];
  notes_count?: number;
};

export default function ModelVersionsPage(props: {
  params: Promise<{ code: string }>;
}) {
  const { code } = use(props.params);
  const versions = useDsiStore((s) => s.modelVersions) as Version[];
  const fetchHistory = useDsiStore((s) => s.fetchHistory);
  useEnsureFetched(code, fetchHistory);

  if (versions.length === 0) {
    return (
      <>
        <PageLoading message="Loading version history…" />
      </>
    );
  }

  // Sort newest first (latest at top of the timeline).
  const sorted = [...versions].sort(
    (a, b) => (b.version_number ?? 0) - (a.version_number ?? 0),
  );

  return (
    <>
      <WorkArea>
        <Card
          header="Version Lineage"
          icon={GitBranch}
          pad="md"
          headerRight={<Chip variant="default" size="sm">{sorted.length} versions</Chip>}
        >
          {sorted.length === 0 ? (
            <Body className="italic">No versions on this submission.</Body>
          ) : (
            <div className="relative py-2">
              <div
                className="absolute left-[22px] top-7 bottom-7 w-0.5 bg-rule"
                aria-hidden
              />
              {sorted.map((v, i) => (
                <VersionRow
                  key={v.version_number ?? i}
                  v={v}
                  last={i === sorted.length - 1}
                />
              ))}
            </div>
          )}
        </Card>
      </WorkArea>
    </>
  );
}

function VersionRow({ v, last }: { v: Version; last: boolean }) {
  const score = numOrNull(v.final_composite_score);
  const prevScore = numOrNull(v.previous_composite_score);
  const delta = score != null && prevScore != null ? score - prevScore : null;
  const tier = numOrNull(v.final_tier);
  const prevTier = numOrNull(v.previous_tier);
  const tierChanged = tier != null && prevTier != null && tier !== prevTier;

  const decision = String(v.decision ?? "").toLowerCase();
  const decisionTone =
    decision === "approve"
      ? "pos"
      : decision === "decline"
        ? "neg"
        : decision === "refer"
          ? "spot"
          : "default";

  const confidence = numOrNull(v.confidence);
  const coverage = numOrNull(v.signal_coverage);
  const condCount = Array.isArray(v.signal_conditions) ? v.signal_conditions.length : 0;
  const refFlags = Array.isArray(v.referral_reasons) ? v.referral_reasons.length : 0;
  const notes = numOrNull(v.notes_count) ?? 0;

  const author = strOrNull(v.author ?? v.created_by);
  const isBot = author ? /world_engine|system|bot/i.test(author) : false;
  const created = strOrNull(v.created_at);
  const isLatest = !!v.is_latest;

  return (
    <div
      className={`relative flex items-start gap-4 ${
        last ? "" : "mb-4"
      }`}
    >
      {/* Marker */}
      <div
        className={`relative z-10 flex h-11 w-11 shrink-0 items-center justify-center rounded-full border-2 ${
          isLatest
            ? "border-info bg-info text-canvas"
            : "border-rule-strong bg-surface-elev text-ink"
        }`}
      >
        <GitCommitHorizontal size={20} />
      </div>

      {/* Card */}
      <div
        className={`flex-1 rounded-card border p-4 ${
          isLatest ? "border-info bg-info-soft" : "border-rule bg-surface-elev"
        }`}
      >
        <div className="mb-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Eyebrow>Version {v.version_number ?? "—"}</Eyebrow>
            {v.version_type && (
              <Chip variant="default" size="sm">
                {formatText(v.version_type.replace(/_/g, " "), "capitalize")}
              </Chip>
            )}
          </div>
          {isLatest && (
            <Chip variant="info" size="sm">
              ACTIVE
            </Chip>
          )}
        </div>
        <div className="grid grid-cols-[1fr_1fr_auto] items-end gap-4">
          <div>
            <Micro>Score</Micro>
            <div className="flex items-baseline gap-2">
              <span className="font-mono text-[22px] tabular-nums text-info">
                {score != null ? score.toFixed(0) : "—"}
              </span>
              {delta != null && delta !== 0 && (
                <span
                  className={`text-[12px] font-bold ${
                    delta > 0 ? "text-pos" : "text-warn"
                  }`}
                >
                  {delta > 0 ? "+" : ""}
                  {delta.toFixed(0)}
                </span>
              )}
            </div>
          </div>
          <div>
            <Micro>Tier</Micro>
            <div className="flex items-baseline gap-2">
              <span className="text-[15px] font-bold">
                {tier != null ? `T${tier}` : "—"}
              </span>
              {tierChanged && (
                <span className="text-[10.5px] font-bold text-warn">
                  was T{prevTier}
                </span>
              )}
            </div>
          </div>
          {decision && (
            <Chip variant={decisionTone} size="sm">
              {formatText(decision, "capitalize")}
            </Chip>
          )}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-3.5 border-t border-rule pt-2.5 text-[11px] text-ink-soft">
          {confidence != null && (
            <span>Confidence {Math.round(confidence * 100)}%</span>
          )}
          {coverage != null && (
            <span>Coverage {Math.round(coverage * 100)}%</span>
          )}
          {condCount > 0 && (
            <span className="text-warn">
              {condCount} condition{condCount === 1 ? "" : "s"}
            </span>
          )}
          {refFlags > 0 && (
            <span className="text-neg">
              {refFlags} referral flag{refFlags === 1 ? "" : "s"}
            </span>
          )}
          {notes > 0 && (
            <span>
              {notes} note{notes === 1 ? "" : "s"}
            </span>
          )}
          <span className="ml-auto flex items-center gap-1">
            {isBot ? <Bot size={11} /> : <User size={11} />}
            {author && <code className="text-[11px]">{author}</code>}
            {created && <span> · {fmtRelative(created)}</span>}
          </span>
        </div>
      </div>
    </div>
  );
}

function numOrNull(v: unknown): number | null {
  if (v == null) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function strOrNull(v: unknown): string | null {
  if (v == null) return null;
  const s = String(v).trim();
  return s.length > 0 ? s : null;
}
