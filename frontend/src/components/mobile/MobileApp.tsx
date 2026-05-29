"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactElement,
} from "react";
import {
  ArrowUp,
  Bot,
  Briefcase,
  Building2,
  Check,
  Moon,
  Sparkles,
  Sun,
  Layers,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { useThemeStore } from "@/store/themeStore";
import { fetchOverview } from "@/lib/portalApi";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import type {
  BrokerOverviewResponse,
  ClientOverviewResponse,
  OverviewResponse,
} from "@/types/portal";
import {
  buildBrokerFeed,
  buildClientFeed,
  buildCarrierFeed,
  type MobileFeed,
  type MobileFeedAwaiting,
  type MobileFeedThread,
} from "@/lib/mobileFeed";
import { Section, TONE_BASE, type Tone } from "./primitives";
import { SignalHero } from "./SignalHero";
import {
  AwaitingRail,
  GlanceGrid,
  SignalFeed,
  ThreadList,
} from "./FeedSections";
import { ReplySheet, type SheetState } from "./ReplySheet";

type Persona = "broker" | "client" | "carrier";

const PERSONAS: Array<{ key: Persona; label: string; icon: typeof Briefcase }> =
  [
    { key: "broker", label: "Broker", icon: Briefcase },
    { key: "client", label: "Client", icon: Bot },
    { key: "carrier", label: "Carrier", icon: Building2 },
  ];

function personasFor(role: string | null | undefined): Persona[] {
  if (role === "BROKER") return ["broker"];
  if (role === "CLIENT") return ["client"];
  // Admins / staff / multi-role accounts can see everything.
  return ["broker", "client", "carrier"];
}

function climateTone(t: Tone): string {
  return TONE_BASE[t];
}

export function MobileApp() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const isDark = useThemeStore((s) => s.isDark);
  const toggleTheme = useThemeStore((s) => s.toggleDark);

  const accessible = useMemo(() => personasFor(user?.role), [user?.role]);
  const [persona, setPersona] = useState<Persona>(accessible[0] ?? "broker");

  // If the role narrows after mount (e.g. session refresh), keep persona valid.
  useEffect(() => {
    if (!accessible.includes(persona)) setPersona(accessible[0] ?? "broker");
  }, [accessible, persona]);

  // ── Data fetches: only run for accessible personas ──
  const overview = useRoleScopedFetch<OverviewResponse>({
    fetcher: () => fetchOverview(accessToken),
    enabled: !!accessToken && (accessible.includes("broker") || accessible.includes("client")),
    deps: [accessToken],
  });

  // Carrier submissions come from the carrier pipeline endpoint. Fetched only
  // when carrier persona is accessible (admin / staff today).
  const [carrierSubs, setCarrierSubs] = useState<Array<Record<string, unknown>>>(
    [],
  );
  useEffect(() => {
    if (!accessible.includes("carrier")) return;
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const days = 90;
    const isoDate = new Date(Date.now() - days * 86400_000).toISOString();
    fetch(`${apiBase}/api/v1/frontend/pipeline?created_after=${isoDate}`)
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setCarrierSubs(Array.isArray(d) ? d : []))
      .catch(() => setCarrierSubs([]));
  }, [accessible]);

  // ── Feed projection ──
  const feed: MobileFeed | null = useMemo(() => {
    const name = user?.email ?? null;
    if (persona === "broker" && overview.data?.role === "BROKER") {
      return buildBrokerFeed(overview.data as BrokerOverviewResponse, name);
    }
    if (persona === "client" && overview.data?.role === "CLIENT") {
      return buildClientFeed(overview.data as ClientOverviewResponse, name);
    }
    if (persona === "carrier") {
      return buildCarrierFeed(carrierSubs, name);
    }
    return null;
  }, [persona, overview.data, carrierSubs, user?.email]);

  // ── Sheet + toast ──
  const [sheet, setSheet] = useState<SheetState>(null);
  const [toast, setToast] = useState<string>("");
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flash = useCallback((msg: string) => {
    setToast(msg);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(""), 2200);
  }, []);
  const onSend = useCallback(() => {
    setSheet(null);
    flash("Reply sent · signal attached");
  }, [flash]);

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const switchPersona = useCallback(
    (p: Persona) => {
      setPersona(p);
      setSheet(null);
      scrollRef.current?.scrollTo({ top: 0, behavior: "smooth" });
    },
    [],
  );

  if (!user) {
    return (
      <div className="dsi-mobile">
        <div
          style={{
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--color-ink-mute)",
            fontSize: 14,
          }}
        >
          Signing in…
        </div>
      </div>
    );
  }

  if (overview.loading && !feed) {
    return (
      <div className="dsi-mobile">
        <Skeleton />
      </div>
    );
  }

  if (!feed) {
    return (
      <div className="dsi-mobile">
        <div
          style={{
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--color-ink-mute)",
            fontSize: 14,
            padding: 24,
            textAlign: "center",
          }}
        >
          No data available for the {persona} view yet.
        </div>
      </div>
    );
  }

  const climate = feed.climate;

  return (
    <div className="dsi-mobile">
      <div className="dsi-scroll" ref={scrollRef}>
        {/* ── glass header ── */}
        <div className="dsi-top">
          <div className="dsi-top-row">
            <div className="dsi-org-av" aria-hidden>
              {personaGlyph(feed.persona)}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="dsi-greet">{feed.greeting}</div>
              <div className="dsi-org">{feed.org.name}</div>
            </div>
            <button
              type="button"
              className="dsi-iconbtn"
              onClick={toggleTheme}
              aria-label={isDark ? "Switch to light" : "Switch to dark"}
            >
              {isDark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>

          {accessible.length > 1 && (
            <div className="dsi-seg">
              {PERSONAS.filter((p) => accessible.includes(p.key)).map((p) => {
                const Ic = p.icon;
                return (
                  <button
                    key={p.key}
                    type="button"
                    className={"dsi-seg-b" + (persona === p.key ? " on" : "")}
                    onClick={() => switchPersona(p.key)}
                  >
                    <Ic size={15} />
                    {p.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* ── feed body ── */}
        <div className="dsi-pad" style={{ paddingBottom: 132 }} key={persona}>
          <div
            className="dsi-climate dsi-rise"
            style={{ animationDelay: "0ms" }}
          >
            <span
              className="dsi-climate-dot"
              style={{ background: climateTone(climate.tone) }}
            />
            <span className="dsi-climate-lbl">{climate.label}</span>
            <span
              style={{
                fontSize: 12.5,
                fontWeight: 700,
                color: climateTone(climate.tone),
              }}
            >
              {climate.value}
            </span>
          </div>

          <div
            className="dsi-brief dsi-rise"
            style={{ marginTop: 14, animationDelay: "40ms" }}
          >
            {renderBrief(feed.brief)}
          </div>

          {feed.score && (
            <div
              className="dsi-rise"
              style={{ marginTop: 22, animationDelay: "90ms" }}
            >
              <SignalHero score={feed.score} />
            </div>
          )}

          {feed.awaiting.length > 0 && (
            <div className="dsi-rise" style={{ animationDelay: "140ms" }}>
              <Section
                title="Awaiting you"
                link={`${feed.awaiting.length} open`}
              />
              <AwaitingRail
                items={feed.awaiting}
                onAct={(it: MobileFeedAwaiting) =>
                  setSheet({ kind: "await", data: it })
                }
              />
            </div>
          )}

          <div className="dsi-rise" style={{ animationDelay: "180ms" }}>
            <Section title="At a glance" />
            <GlanceGrid tiles={feed.glance} />
          </div>

          {feed.threads.length > 0 && (
            <div className="dsi-rise" style={{ animationDelay: "220ms" }}>
              <Section title="Conversations" link="Inbox" onLink={() => {}} />
              <ThreadList
                threads={feed.threads}
                onOpen={(th: MobileFeedThread) =>
                  setSheet({ kind: "thread", data: th })
                }
              />
            </div>
          )}

          {feed.feed.length > 0 && (
            <div className="dsi-rise" style={{ animationDelay: "260ms" }}>
              <Section title="Signal feed" />
              <SignalFeed events={feed.feed} />
            </div>
          )}

          <div
            style={{
              marginTop: 40,
              textAlign: "center",
              fontSize: 12.5,
              color: "var(--color-ink-mute)",
            }}
          >
            <button
              type="button"
              onClick={() => {
                if (typeof window !== "undefined") {
                  window.localStorage.setItem("dsi-prefers-desktop", "1");
                  window.location.href = "/?desktop=1";
                }
              }}
              style={{
                background: "transparent",
                border: 0,
                color: "var(--color-ink-soft)",
                fontWeight: 600,
                fontSize: 12.5,
                cursor: "pointer",
              }}
            >
              View on desktop →
            </button>
          </div>
        </div>
      </div>

      {/* floating Ask pill */}
      {!sheet && (
        <button
          type="button"
          className="dsi-ask"
          onClick={() => flash("Ask DSI — coming soon")}
        >
          <Sparkles size={19} style={{ opacity: 0.85 }} />
          <span className="dsi-ask-tx">
            Ask anything about your {askLabel(feed.persona)}…
          </span>
          <span className="dsi-ask-send">
            <ArrowUp size={19} />
          </span>
        </button>
      )}

      <ReplySheet
        sheet={sheet}
        onClose={() => setSheet(null)}
        onSend={onSend}
      />

      <div className={"dsi-toast" + (toast ? " on" : "")}>
        <Check size={16} />
        {toast}
      </div>
    </div>
  );
}

function personaGlyph(p: Persona) {
  if (p === "broker") return <Briefcase size={21} />;
  if (p === "client") return <Bot size={21} />;
  return <Building2 size={21} />;
}

function askLabel(p: Persona): string {
  if (p === "carrier") return "pipeline";
  if (p === "client") return "coverage";
  return "book";
}

/* Render the brief as React nodes, bolding the leading count and any
   capitalised multi-word entity. No innerHTML — entity names come from
   user-provided fields and must not be parsed as markup. */
function renderBrief(s: string): ReactElement[] {
  const re = /(^\d+\s+\w+)|([A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+){1,3})/g;
  const out: ReactElement[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = re.exec(s)) !== null) {
    if (m.index > last) {
      out.push(<span key={`t${i}`}>{s.slice(last, m.index)}</span>);
    }
    out.push(<b key={`b${i}`}>{m[0]}</b>);
    last = m.index + m[0].length;
    i++;
  }
  if (last < s.length) out.push(<span key={`t${i}`}>{s.slice(last)}</span>);
  return out;
}

function Skeleton() {
  return (
    <div style={{ padding: "calc(env(safe-area-inset-top, 12px) + 60px) 20px 20px" }}>
      <div
        style={{
          height: 22,
          width: "55%",
          borderRadius: 6,
          background: "var(--color-surface-sunken)",
          marginBottom: 12,
        }}
      />
      <div
        style={{
          height: 14,
          width: "85%",
          borderRadius: 6,
          background: "var(--color-surface-sunken)",
          marginBottom: 26,
        }}
      />
      <div
        style={{
          height: 200,
          borderRadius: 22,
          background: "var(--color-surface-sunken)",
          marginBottom: 24,
        }}
      />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 13 }}>
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              height: 122,
              borderRadius: 20,
              background: "var(--color-surface-sunken)",
            }}
          />
        ))}
      </div>
      <div style={{ marginTop: 36, color: "var(--color-ink-mute)", fontSize: 13 }}>
        <Layers
          size={14}
          style={{ display: "inline-block", verticalAlign: "-2px", marginRight: 6 }}
        />
        Loading your signal…
      </div>
    </div>
  );
}
