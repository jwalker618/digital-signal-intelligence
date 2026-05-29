"use client";

import { memo } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  Minus,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import {
  SignalRing,
  Sparkline,
  TONE_BASE,
  TONE_BG,
  TONE_FG,
  type Tone,
} from "./primitives";
import type { MobileFeedScore } from "@/lib/mobileFeed";

function DeltaIcon({ dir, size = 14 }: { dir: "up" | "down" | "flat"; size?: number }) {
  if (dir === "up") return <TrendingUp size={size} />;
  if (dir === "down") return <TrendingDown size={size} />;
  return <Minus size={size} />;
}

function MoverArrow({ dir, size = 16 }: { dir: "up" | "down" | "flat"; size?: number }) {
  if (dir === "up") return <ArrowUpRight size={size} />;
  if (dir === "down") return <ArrowDownRight size={size} />;
  return <Minus size={size} />;
}

export const SignalHero = memo(function SignalHero({
  score,
  ringTone,
}: {
  score: MobileFeedScore;
  ringTone?: Tone;
}) {
  const tone = score.tone;
  const ring = ringTone ?? tone;
  return (
    <div className="dsi-card dsi-hero">
      <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
        <SignalRing
          frac={score.frac}
          value={score.value}
          caption="/ 800"
          tone={ring}
        />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="dsi-eyebrow">{score.label}</div>
          {(score.delta || score.dir !== "flat") && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginTop: 8,
              }}
            >
              <span
                className="dsi-delta"
                style={{ background: TONE_BG[tone], color: TONE_FG[tone] }}
              >
                <DeltaIcon dir={score.dir} /> {score.delta || "—"}
              </span>
              <span
                style={{
                  fontSize: 12.5,
                  color: "var(--color-ink-mute)",
                  fontWeight: 600,
                }}
              >
                this week
              </span>
            </div>
          )}
          <div style={{ marginTop: 12 }}>
            <Sparkline data={score.spark} stroke={TONE_BASE[tone]} w={150} h={42} />
          </div>
        </div>
      </div>
      {score.caption && (
        <div
          style={{
            fontSize: 12.5,
            color: "var(--color-ink-mute)",
            marginTop: 4,
            marginBottom: 4,
          }}
        >
          {score.caption}
        </div>
      )}
      {score.movers.length > 0 && (
        <div
          style={{
            marginTop: 10,
            paddingTop: 4,
            borderTop: "1px solid var(--color-rule)",
          }}
        >
          {score.movers.map((m, i) => (
            <div className="dsi-mover" key={i}>
              <div
                className="dsi-mover-dot"
                style={{ background: TONE_BG[m.tone], color: TONE_FG[m.tone] }}
              >
                <MoverArrow dir={m.dir} />
              </div>
              <div className="dsi-mover-tx">{m.text}</div>
              <div
                style={{
                  fontWeight: 700,
                  fontSize: 13.5,
                  color: TONE_FG[m.tone],
                  fontVariantNumeric: "tabular-nums",
                  whiteSpace: "nowrap",
                }}
              >
                {m.delta}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
});
