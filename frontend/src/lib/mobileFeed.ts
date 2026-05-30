/* ============================================================
 * mobileFeed.ts — adapter that projects desktop API payloads onto
 * the mobile companion's single feed shape.
 *
 *   { org, greeting, brief, climate, score, awaiting[], glance[],
 *     threads[], feed[] }
 *
 * Honesty rule: where the data is genuinely missing, return an empty
 * array / null and let the UI show its empty state. We do NOT fabricate.
 * ============================================================ */

import type {
  BrokerOverviewResponse,
  ClientBookEntry,
  ClientCoverageEntry,
  ClientOverviewResponse,
} from "@/types/portal";
import type { Tone } from "@/components/mobile/primitives";

export type MoverDir = "up" | "down" | "flat";

export interface MobileFeedScore {
  value: number;
  label: string;
  frac: number;
  delta: string;
  dir: MoverDir;
  tone: Tone;
  caption: string;
  spark: number[];
  movers: { text: string; delta: string; dir: MoverDir; tone: Tone }[];
}

export interface MobileFeedAwaiting {
  id: string;
  title: string;
  line: string;
  counterparty: string;
  sub: string;
  age: string;
  cta: string;
}

export interface MobileFeedTile {
  key: string;
  label: string;
  value?: string;
  sub: string;
  tone: Tone;
  icon: string; // lucide name
  kind?: "value" | "tiermix";
  bars?: number[];
}

export interface MobileFeedThread {
  id: string;
  who: string;
  sub: string;
  ask: string;
  age: string;
  awaiting: "broker" | "client" | "carrier" | "resolved";
  label: string;
  tone: Tone;
  messages: MobileFeedMessage[];
}

export interface MobileFeedMessage {
  from: "them" | "me" | "sys";
  who?: string;
  text: string;
  time: string;
}

export interface MobileFeedEvent {
  id: string;
  icon: string;
  tone: Tone;
  title: string;
  text: string;
  time: string;
}

export interface MobileFeed {
  persona: "broker" | "client" | "carrier";
  org: { name: string; sub: string; glyph: string; initials: string };
  greeting: string;
  brief: string;
  climate: { label: string; value: string; tone: Tone };
  score: MobileFeedScore | null;
  awaiting: MobileFeedAwaiting[];
  glance: MobileFeedTile[];
  threads: MobileFeedThread[];
  feed: MobileFeedEvent[];
}

const fmtUsd = (n: number | null | undefined): string => {
  if (n == null || !Number.isFinite(n)) return "—";
  if (n >= 1e6) return "$" + (n / 1e6).toFixed(2) + "M";
  if (n >= 1e3) return "$" + Math.round(n / 1e3) + "k";
  return "$" + n;
};

const scoreFrac = (v: number): number =>
  Math.max(0.04, Math.min(1, (v - 500) / 300));

const scoreBand = (v: number): string =>
  v >= 720 ? "Strong" : v >= 680 ? "Healthy" : v >= 640 ? "Watch" : "Fragile";

const climateTone = (v: number): Tone =>
  v >= 700 ? "pos" : v >= 640 ? "warn" : "neg";

/* Deterministic 14-point sparkline trending to `end`. Visual only —
   real history charts live on the desktop. */
function spark(end: number, swing = 22, n = 14): number[] {
  const out: number[] = [];
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1);
    const wobble = Math.sin(i * 1.7) * swing * 0.28 * (1 - t);
    out.push(Math.round(end - swing * (1 - t) + wobble));
  }
  out[n - 1] = end;
  return out;
}

function firstName(s: string | null | undefined): string {
  if (!s) return "there";
  const t = s.trim();
  if (!t) return "there";
  return t.split(/\s+/)[0];
}

function timeGreet(): string {
  const h = new Date().getHours();
  return h < 5
    ? "Good evening"
    : h < 12
      ? "Good morning"
      : h < 18
        ? "Good afternoon"
        : "Good evening";
}

function initials(name: string): string {
  return name
    .split(/[\s·]+/)
    .slice(0, 2)
    .map((w) => w[0] || "")
    .join("")
    .toUpperCase();
}

// ──────────────────────────────────────────────────────── BROKER

export function buildBrokerFeed(
  data: BrokerOverviewResponse,
  userName: string | null,
): MobileFeed {
  const clients = data.clients ?? [];

  const scored = clients
    .map((c) => c.composite_score)
    .filter((s): s is number => typeof s === "number");
  const avg = scored.length
    ? Math.round(scored.reduce((s, n) => s + n, 0) / scored.length)
    : 0;

  const totalPrem = clients.reduce(
    (s, c) => s + (c.recommended_premium ?? 0),
    0,
  );
  const distinctEntities = new Set(clients.map((c) => c.entity_name));

  const tierBuckets = [1, 2, 3, 4, 5].map(
    (t) => clients.filter((c) => c.tier === t).length,
  );

  const onYou = clients.filter(
    (c) => c.awaiting_party && /broker/i.test(c.awaiting_party),
  );

  const top = [...clients]
    .filter((c) => typeof c.composite_score === "number")
    .sort(
      (a, b) => (b.composite_score ?? 0) - (a.composite_score ?? 0),
    );
  const bestMover = top[0];
  const worstMover = top[top.length - 1];

  const movers: MobileFeedScore["movers"] = [];
  if (bestMover) {
    movers.push({
      text: `${bestMover.entity_name} leads on ${bestMover.coverage}`,
      delta: String(bestMover.composite_score ?? ""),
      dir: "up",
      tone: "pos",
    });
  }
  if (worstMover && worstMover !== bestMover) {
    movers.push({
      text: `${worstMover.entity_name} trails on ${worstMover.coverage}`,
      delta: String(worstMover.composite_score ?? ""),
      dir: "down",
      tone: "neg",
    });
  }

  return {
    persona: "broker",
    org: {
      name: data.broker?.name ?? "Broker",
      sub: "Book of business",
      glyph: "briefcase",
      initials: initials(data.broker?.name ?? "BR"),
    },
    greeting: `${timeGreet()}, ${firstName(userName)}`,
    brief:
      onYou.length > 0
        ? `${onYou.length} ${onYou.length === 1 ? "client is" : "clients are"} waiting on you across ${distinctEntities.size} ${distinctEntities.size === 1 ? "account" : "accounts"}.`
        : `Your book is quiet — ${clients.length} policies in force across ${distinctEntities.size} accounts.`,
    climate: avg
      ? { label: "Book climate", value: scoreBand(avg), tone: climateTone(avg) }
      : { label: "Book climate", value: "—", tone: "warn" },
    score: avg
      ? {
          value: avg,
          label: "Book signal",
          frac: scoreFrac(avg),
          delta: "",
          dir: "flat",
          tone: climateTone(avg),
          caption: `Average across ${clients.length} ${clients.length === 1 ? "policy" : "policies"} · ${distinctEntities.size} ${distinctEntities.size === 1 ? "client" : "clients"}`,
          spark: spark(avg, 22),
          movers,
        }
      : null,
    awaiting: onYou.map((c) => ({
      id: c.submission_code,
      title: c.entity_name,
      line: c.coverage,
      counterparty: c.referral_state ?? "Open referral",
      sub:
        c.referral_state ??
        `Referral on ${c.coverage} — your input needed before placement moves.`,
      age: relTime(c.updated_at),
      cta: "Action",
    })),
    glance: [
      {
        key: "prem",
        label: "Aggregate premium",
        value: fmtUsd(totalPrem),
        sub: "annual, in force",
        tone: "info",
        icon: "layers",
      },
      {
        key: "pol",
        label: "Policies in force",
        value: String(clients.length),
        sub: `${distinctEntities.size} ${distinctEntities.size === 1 ? "client" : "clients"}`,
        tone: "ink",
        icon: "shield-check",
      },
      {
        key: "open",
        label: "Awaiting you",
        value: String(onYou.length),
        sub: onYou.length
          ? [...new Set(onYou.map((c) => c.entity_name))].slice(0, 3).join(" · ")
          : "All clear",
        tone: "spot",
        icon: "bell-ring",
      },
      {
        key: "tier",
        label: "Tier mix",
        kind: "tiermix",
        bars: tierBuckets,
        sub: `${tierBuckets[0] + tierBuckets[1]} preferred`,
        tone: "aux",
        icon: "bar-chart-3",
      },
    ],
    threads: clients
      .filter((c) => c.referral_state)
      .slice(0, 6)
      .map((c) => threadFromClient(c)),
    feed: clients
      .slice(0, 5)
      .map((c, i) => bookEventFromClient(c, i)),
  };
}

function threadFromClient(c: ClientBookEntry): MobileFeedThread {
  const onBroker = c.awaiting_party && /broker/i.test(c.awaiting_party);
  const onClient = c.awaiting_party && /client/i.test(c.awaiting_party);
  const tone: Tone = onBroker ? "spot" : onClient ? "info" : "pos";
  const label = onBroker
    ? "awaiting you"
    : onClient
      ? "awaiting client"
      : "with carrier";
  const ask =
    c.referral_state ??
    `${c.coverage} — referral open since ${relTime(c.updated_at)}.`;
  return {
    id: c.submission_code,
    who: c.entity_name,
    sub: `${c.coverage} · ${c.submission_code}`,
    ask,
    age: relTime(c.updated_at),
    awaiting: onBroker ? "broker" : onClient ? "client" : "carrier",
    label,
    tone,
    messages: [
      { from: "them", who: c.entity_name, text: ask, time: relTime(c.updated_at) },
    ],
  };
}

function bookEventFromClient(c: ClientBookEntry, i: number): MobileFeedEvent {
  const score = c.composite_score ?? 0;
  const tone: Tone =
    score >= 720 ? "pos" : score >= 640 ? "info" : score > 0 ? "warn" : "ink";
  return {
    id: `f-${c.submission_code}-${i}`,
    icon: score >= 720 ? "trending-up" : score >= 640 ? "activity" : "trending-down",
    tone,
    title: `${c.entity_name} · ${c.coverage}`,
    text: `Tier ${c.tier ?? "—"} · signal ${score || "—"} · ${fmtUsd(c.recommended_premium ?? null)}`,
    time: relTime(c.updated_at),
  };
}

// ──────────────────────────────────────────────────────── CLIENT

export function buildClientFeed(
  data: ClientOverviewResponse,
  userName: string | null,
): MobileFeed {
  const covs = data.active_coverages ?? [];

  const scored = covs
    .map((c) => c.composite_score)
    .filter((s): s is number => typeof s === "number");
  const avg = scored.length
    ? Math.round(scored.reduce((s, n) => s + n, 0) / scored.length)
    : 0;

  const totalPrem = covs.reduce(
    (s, c) => s + (c.recommended_premium ?? 0),
    0,
  );

  const movers: MobileFeedScore["movers"] = [];
  for (const c of covs) {
    const cur = c.composite_score ?? null;
    const prev = c.previous_composite_score ?? null;
    if (cur == null || prev == null) continue;
    const delta = cur - prev;
    if (Math.abs(delta) < 1) continue;
    movers.push({
      text: `${c.coverage} ${delta > 0 ? "rebound" : "drift"}`,
      delta: `${delta > 0 ? "+" : ""}${Math.round(delta)}`,
      dir: delta > 0 ? "up" : "down",
      tone: delta > 0 ? "pos" : "neg",
    });
    if (movers.length >= 3) break;
  }

  const renewals = covs
    .map((c) => c.expires_at)
    .filter((d): d is string => !!d)
    .map((d) => daysUntil(d))
    .filter((d): d is number => d != null);
  const nextRenewal = renewals.length ? Math.min(...renewals) : null;

  const percentile = covs.find((c) => c.peer_percentile_rank != null)
    ?.peer_percentile_rank;

  return {
    persona: "client",
    org: {
      name: data.entity_name,
      sub: data.broker?.name ?? "Your broker",
      glyph: "bot",
      initials: initials(data.entity_name),
    },
    greeting: `${timeGreet()}, ${firstName(userName)}`,
    brief: avg
      ? `Your signal sits at ${avg}${nextRenewal != null ? `, with renewal in ${nextRenewal} days` : ""}. ${covs.length} ${covs.length === 1 ? "coverage" : "coverages"} active across your programme.`
      : `${covs.length} ${covs.length === 1 ? "coverage" : "coverages"} active. Your broker will keep this page current.`,
    climate: avg
      ? { label: "Your standing", value: scoreBand(avg), tone: climateTone(avg) }
      : { label: "Your standing", value: "—", tone: "warn" },
    score: avg
      ? {
          value: avg,
          label: "Your signal",
          frac: scoreFrac(avg),
          delta: "",
          dir: "flat",
          tone: climateTone(avg),
          caption: percentile != null
            ? `${Math.round(percentile)}th percentile among peers`
            : `Across ${covs.length} ${covs.length === 1 ? "coverage" : "coverages"}`,
          spark: spark(avg, 28),
          movers,
        }
      : null,
    awaiting: covs
      .filter((c) => c.referral_state && /client/i.test(c.referral_state))
      .map((c) => ({
        id: c.submission_code,
        title: `${c.coverage} submission`,
        line: c.coverage,
        counterparty: data.broker?.name ?? "Broker",
        sub: c.referral_state ?? "",
        age: relTime(c.updated_at),
        cta: "Provide",
      })),
    glance: [
      {
        key: "prem",
        label: "Total premium",
        value: fmtUsd(totalPrem),
        sub: `across ${covs.length} ${covs.length === 1 ? "policy" : "policies"}`,
        tone: "info",
        icon: "layers",
      },
      {
        key: "cov",
        label: "Active coverages",
        value: String(covs.length),
        sub: covs.slice(0, 3).map((c) => c.coverage).join(" · ") || "—",
        tone: "ink",
        icon: "shield-check",
      },
      {
        key: "renew",
        label: "Renewal in",
        value: nextRenewal != null ? `${nextRenewal}d` : "—",
        sub: nextRenewal != null ? "earliest line" : "no expiry on file",
        tone: "spot",
        icon: "calendar-clock",
      },
      {
        key: "peer",
        label: "Peer standing",
        value: percentile != null ? `${Math.round(percentile)}th` : "—",
        sub: percentile != null ? "percentile" : "no cohort data",
        tone: "aux",
        icon: "trending-up",
      },
    ],
    threads: covs
      .filter((c) => c.referral_state)
      .slice(0, 6)
      .map((c) => threadFromCoverage(c, data.broker?.name ?? "Broker")),
    feed: clientFeedFromCoverages(covs),
  };
}

function threadFromCoverage(
  c: ClientCoverageEntry,
  brokerName: string,
): MobileFeedThread {
  const onClient = c.referral_state && /client/i.test(c.referral_state);
  const tone: Tone = onClient ? "spot" : "info";
  const ask = c.referral_state ?? `Open referral on ${c.coverage}.`;
  return {
    id: c.submission_code,
    who: `${c.coverage} · ${brokerName}`,
    sub: c.submission_code,
    ask,
    age: relTime(c.updated_at),
    awaiting: onClient ? "client" : "broker",
    label: onClient ? "awaiting you" : "with broker",
    tone,
    messages: [
      { from: "them", who: brokerName, text: ask, time: relTime(c.updated_at) },
    ],
  };
}

function clientFeedFromCoverages(covs: ClientCoverageEntry[]): MobileFeedEvent[] {
  const out: MobileFeedEvent[] = [];
  for (const c of covs) {
    const cur = c.composite_score ?? null;
    const prev = c.previous_composite_score ?? null;
    if (cur == null) continue;
    const delta = prev != null ? cur - prev : 0;
    const tone: Tone = delta > 0 ? "pos" : delta < 0 ? "warn" : "info";
    out.push({
      id: `cf-${c.submission_code}`,
      icon: delta > 0 ? "trending-up" : delta < 0 ? "trending-down" : "activity",
      tone,
      title: `${c.coverage} signal`,
      text:
        delta !== 0
          ? `${c.coverage} moved ${delta > 0 ? "+" : ""}${Math.round(delta)} to ${cur}.`
          : `${c.coverage} signal holds at ${cur}.`,
      time: relTime(c.updated_at),
    });
    if (out.length >= 5) break;
  }
  return out;
}

// ──────────────────────────────────────────────────────── CARRIER

export function buildCarrierFeed(
  submissions: Array<Record<string, unknown>>,
  userName: string | null,
): MobileFeed {
  const subs = (submissions ?? []).map((s) => ({
    code: String(s.code ?? s.submission_code ?? ""),
    entity: String(s.entity_name ?? s.entity ?? "—"),
    coverage: String(s.coverage ?? s.line ?? "—"),
    broker: String(s.broker_name ?? s.broker ?? "—"),
    premium: Number(s.recommended_premium ?? s.premium ?? 0),
    score: Number(s.composite_score ?? s.score ?? 0),
    tier: Number(s.tier ?? 0) || null,
    decision: String(s.decision ?? s.referral_state ?? "—"),
    received: relTime(s.received_at ?? s.created_at ?? null),
  }));

  const scored = subs.map((s) => s.score).filter((n) => n > 0);
  const avg = scored.length
    ? Math.round(scored.reduce((s, n) => s + n, 0) / scored.length)
    : 0;
  const pipelinePrem = subs.reduce((s, x) => s + x.premium, 0);
  const refer = subs.filter((s) => /refer/i.test(s.decision));
  const ready = subs.filter((s) => /approve|quote|bound/i.test(s.decision));

  return {
    persona: "carrier",
    org: {
      name: "Carrier desk",
      sub: "Underwriting",
      glyph: "building-2",
      initials: "UW",
    },
    greeting: `${timeGreet()}, ${firstName(userName)}`,
    brief:
      refer.length > 0
        ? `${refer.length} ${refer.length === 1 ? "submission is" : "submissions are"} referred for your decision. Pipeline carries ${fmtUsd(pipelinePrem)} across ${subs.length} risks.`
        : `Pipeline is clear — ${subs.length} live submissions worth ${fmtUsd(pipelinePrem)}.`,
    climate: avg
      ? { label: "Pipeline", value: scoreBand(avg), tone: climateTone(avg) }
      : { label: "Pipeline", value: "—", tone: "warn" },
    score: avg
      ? {
          value: avg,
          label: "Pipeline signal",
          frac: scoreFrac(avg),
          delta: "",
          dir: "flat",
          tone: climateTone(avg),
          caption: `Mean across ${subs.length} inbound submissions`,
          spark: spark(avg, 26),
          movers: [],
        }
      : null,
    awaiting: refer.slice(0, 5).map((s) => ({
      id: s.code,
      title: s.entity,
      line: s.coverage,
      counterparty: s.broker,
      sub: `${fmtUsd(s.premium)} · Tier ${s.tier ?? "—"} · signal ${s.score || "—"}`,
      age: s.received,
      cta: "Decide",
    })),
    glance: [
      {
        key: "pipe",
        label: "Pipeline premium",
        value: fmtUsd(pipelinePrem),
        sub: `${subs.length} submissions`,
        tone: "info",
        icon: "layers",
      },
      {
        key: "refer",
        label: "Referred to you",
        value: String(refer.length),
        sub: "need a decision",
        tone: "spot",
        icon: "user-round-search",
      },
      {
        key: "ready",
        label: "Cleared",
        value: String(ready.length),
        sub: "ready to quote / bound",
        tone: "pos",
        icon: "circle-check",
      },
      {
        key: "score",
        label: "Mean signal",
        value: avg ? String(avg) : "—",
        sub: avg ? scoreBand(avg) : "no data",
        tone: "aux",
        icon: "activity",
      },
    ],
    threads: refer.slice(0, 6).map((s) => ({
      id: s.code,
      who: s.entity,
      sub: `${s.broker} · ${s.coverage}`,
      ask: `${fmtUsd(s.premium)} at Tier ${s.tier ?? "—"} — awaiting your decision.`,
      age: s.received,
      awaiting: "carrier" as const,
      label: "referred",
      tone: "spot" as const,
      messages: [
        {
          from: "them",
          who: s.broker,
          text: `${s.entity} — ${s.coverage}. Signal ${s.score}, Tier ${s.tier ?? "—"}. ${fmtUsd(s.premium)} premium.`,
          time: s.received,
        },
      ],
    })),
    feed: subs.slice(0, 5).map((s, i) => ({
      id: `cs-${s.code}-${i}`,
      icon: /refer/i.test(s.decision)
        ? "user-round-search"
        : /approve|quote|bound/i.test(s.decision)
          ? "circle-check"
          : "activity",
      tone: /refer/i.test(s.decision)
        ? ("spot" as const)
        : /approve|quote|bound/i.test(s.decision)
          ? ("pos" as const)
          : ("info" as const),
      title: `${s.entity} · ${s.coverage}`,
      text: `${s.decision} — ${fmtUsd(s.premium)}, signal ${s.score || "—"}.`,
      time: s.received,
    })),
  };
}

// ──────────────────────────────────────────────────────── helpers

function relTime(when: unknown): string {
  if (!when) return "—";
  const d = new Date(String(when));
  if (Number.isNaN(d.getTime())) return "—";
  const diff = Date.now() - d.getTime();
  const m = Math.round(diff / 60_000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h`;
  const days = Math.round(h / 24);
  if (days < 7) return `${days}d`;
  const w = Math.round(days / 7);
  if (w < 5) return `${w}w`;
  return d.toLocaleDateString();
}

function daysUntil(when: string): number | null {
  const d = new Date(when);
  if (Number.isNaN(d.getTime())) return null;
  return Math.max(0, Math.round((d.getTime() - Date.now()) / 86_400_000));
}
