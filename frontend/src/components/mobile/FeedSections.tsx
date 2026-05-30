"use client";

import { memo, type ComponentType } from "react";
import {
  Activity,
  ArrowUpRight,
  BarChart3,
  BellRing,
  Bot,
  Briefcase,
  Building2,
  CalendarClock,
  CheckCircle2,
  CircleCheck,
  CloudLightning,
  FileCheck,
  Flame,
  Layers,
  Lightbulb,
  Minus,
  Radar,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  TrendingUp,
  UserRoundSearch,
} from "lucide-react";
import {
  Chip,
  TONE_BASE,
  TONE_BG,
  TONE_FG,
  avatarColor,
  type Tone,
} from "./primitives";
import type {
  MobileFeedAwaiting,
  MobileFeedEvent,
  MobileFeedThread,
  MobileFeedTile,
} from "@/lib/mobileFeed";

/* Map lucide name strings → component refs, so the feed builder can stay
   data-only without forcing the JIT to follow component imports. */
const ICONS: Record<string, ComponentType<{ size?: number }>> = {
  activity: Activity,
  "arrow-up-right": ArrowUpRight,
  "bar-chart-3": BarChart3,
  "bell-ring": BellRing,
  bot: Bot,
  briefcase: Briefcase,
  "building-2": Building2,
  "calendar-clock": CalendarClock,
  "check-circle-2": CheckCircle2,
  "circle-check": CircleCheck,
  "cloud-lightning": CloudLightning,
  "file-check": FileCheck,
  flame: Flame,
  layers: Layers,
  lightbulb: Lightbulb,
  radar: Radar,
  "shield-check": ShieldCheck,
  sparkles: Sparkles,
  "trending-down": TrendingDown,
  "trending-up": TrendingUp,
  "user-round-search": UserRoundSearch,
  minus: Minus,
};

function LucideByName({
  name,
  size = 17,
}: {
  name: string;
  size?: number;
}) {
  const Ic = ICONS[name] ?? Activity;
  return <Ic size={size} />;
}

// ── Awaiting rail ───────────────────────────────────────────────

export const AwaitingRail = memo(function AwaitingRail({
  items,
  onAct,
}: {
  items: MobileFeedAwaiting[];
  onAct: (item: MobileFeedAwaiting) => void;
}) {
  if (items.length === 0) {
    return (
      <div className="dsi-await-empty">
        Nothing awaiting you. New referrals will surface here.
      </div>
    );
  }
  return (
    <div className="dsi-await-rail">
      {items.map((it) => (
        <div className="dsi-await" key={it.id}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <Chip tone="spot" icon={<BellRing size={12} />}>
              awaiting you
            </Chip>
            <span
              style={{
                fontSize: 11.5,
                color: "var(--color-ink-mute)",
                fontWeight: 600,
              }}
            >
              {it.age}
            </span>
          </div>
          <div
            style={{
              fontSize: 16,
              fontWeight: 700,
              letterSpacing: "-.01em",
              marginTop: 11,
              lineHeight: 1.2,
            }}
          >
            {it.title}
          </div>
          <div
            style={{ fontSize: 12, color: "var(--color-ink-mute)", marginTop: 2 }}
          >
            {it.line} · {it.counterparty}
          </div>
          <div
            style={{
              fontSize: 13,
              color: "var(--color-ink-soft)",
              marginTop: 8,
              lineHeight: 1.35,
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            {it.sub}
          </div>
          <button
            type="button"
            className="dsi-await-act dsi-press"
            onClick={() => onAct(it)}
          >
            <ArrowUpRight size={16} /> {it.cta}
          </button>
        </div>
      ))}
    </div>
  );
});

// ── Glance grid ────────────────────────────────────────────────

function TierMix({ bars }: { bars: number[] }) {
  const max = Math.max(...bars, 1);
  const cols: Tone[] = ["pos", "pos", "warn", "neg", "neg"];
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-end",
        gap: 6,
        height: 34,
      }}
    >
      {bars.map((b, i) => (
        <div
          key={i}
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 3,
          }}
        >
          <div
            style={{
              width: "100%",
              height: Math.max(4, (b / max) * 30),
              background: TONE_BASE[cols[i]],
              borderRadius: 3,
              opacity: b ? 1 : 0.25,
            }}
          />
          <span
            style={{
              fontSize: 8.5,
              color: "var(--color-ink-mute)",
              fontWeight: 700,
            }}
          >
            {i + 1}
          </span>
        </div>
      ))}
    </div>
  );
}

const GlanceTile = memo(function GlanceTile({ tile }: { tile: MobileFeedTile }) {
  return (
    <div className="dsi-tile dsi-press">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div
          className="dsi-tile-ic"
          style={{ background: TONE_BG[tile.tone], color: TONE_FG[tile.tone] }}
        >
          <LucideByName name={tile.icon} size={17} />
        </div>
      </div>
      <div>
        {tile.kind === "tiermix" ? (
          <TierMix bars={tile.bars ?? [0, 0, 0, 0, 0]} />
        ) : (
          <div
            className="dsi-tile-val"
            style={{ color: TONE_FG[tile.tone] }}
          >
            {tile.value ?? "—"}
          </div>
        )}
        <div className="dsi-tile-lbl" style={{ marginTop: 7 }}>
          {tile.label}
        </div>
        <div className="dsi-tile-sub">{tile.sub}</div>
      </div>
    </div>
  );
});

export function GlanceGrid({ tiles }: { tiles: MobileFeedTile[] }) {
  return (
    <div className="dsi-glance">
      {tiles.map((t) => (
        <GlanceTile key={t.key} tile={t} />
      ))}
    </div>
  );
}

// ── Threads list ───────────────────────────────────────────────

const ThreadRow = memo(function ThreadRow({
  thread,
  onOpen,
}: {
  thread: MobileFeedThread;
  onOpen: (t: MobileFeedThread) => void;
}) {
  const h = avatarColor(thread.who);
  const inits = thread.who
    .split(/[\s·]+/)
    .slice(0, 2)
    .map((w) => w[0] || "")
    .join("");
  return (
    <div className="dsi-thread" onClick={() => onOpen(thread)}>
      <div
        className="dsi-thread-av"
        style={{
          background: `oklch(0.92 0.05 ${h})`,
          color: `oklch(0.42 0.11 ${h})`,
        }}
      >
        {inits}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 8,
          }}
        >
          <span className="dsi-thread-who">{thread.who}</span>
          <Chip tone={thread.tone}>{thread.label}</Chip>
        </div>
        <div className="dsi-thread-sub">{thread.sub}</div>
        <div className="dsi-thread-ask">{thread.ask}</div>
      </div>
    </div>
  );
});

export function ThreadList({
  threads,
  onOpen,
}: {
  threads: MobileFeedThread[];
  onOpen: (t: MobileFeedThread) => void;
}) {
  if (threads.length === 0) {
    return (
      <div className="dsi-await-empty">
        No conversations open. New referrals will surface here.
      </div>
    );
  }
  return (
    <div className="dsi-card" style={{ overflow: "hidden" }}>
      {threads.map((t) => (
        <ThreadRow key={t.id} thread={t} onOpen={onOpen} />
      ))}
    </div>
  );
}

// ── Signal feed timeline ───────────────────────────────────────

const FeedEvent = memo(function FeedEvent({
  e,
  last,
}: {
  e: MobileFeedEvent;
  last: boolean;
}) {
  return (
    <div className="dsi-evt">
      <div className="dsi-evt-rail">
        <div
          className="dsi-evt-ic"
          style={{ background: TONE_BG[e.tone], color: TONE_FG[e.tone] }}
        >
          <LucideByName name={e.icon} size={18} />
        </div>
        {!last && <div className="dsi-evt-line" />}
      </div>
      <div className="dsi-evt-body">
        <div className="dsi-evt-top">
          <span className="dsi-evt-title">{e.title}</span>
          <span className="dsi-evt-time">{e.time}</span>
        </div>
        <div className="dsi-evt-text">{e.text}</div>
      </div>
    </div>
  );
});

export function SignalFeed({ events }: { events: MobileFeedEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="dsi-await-empty">
        Your signal feed is quiet. Activity will appear here.
      </div>
    );
  }
  return (
    <div style={{ padding: "2px 4px 0" }}>
      {events.map((e, i) => (
        <FeedEvent key={e.id} e={e} last={i === events.length - 1} />
      ))}
    </div>
  );
}
