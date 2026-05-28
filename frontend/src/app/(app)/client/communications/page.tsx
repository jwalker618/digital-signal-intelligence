"use client";

import Link from "next/link";
import { ChevronRight, MessageSquare } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchCommunications } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { fmtRelative } from "@/lib/utils";
import { formatText } from "@/lib/format";
import { cn } from "@/lib/utils";
import type {
  CommunicationItem,
  CommunicationsListResponse,
} from "@/types/portal";

export default function ClientCommunicationsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";

  const { data, error, loading } = useRoleScopedFetch<CommunicationsListResponse>({
    fetcher: () => fetchCommunications(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <CommsBody data={data} />;
}

function CommsBody({ data }: { data: CommunicationsListResponse }) {
  // Split: awaiting-you (urgent), open (waiting on UW/broker), closed
  const awaitingYou: CommunicationItem[] = [];
  const otherOpen: CommunicationItem[] = [];
  const closed: CommunicationItem[] = [];
  for (const item of data.items) {
    if (!item.is_open) closed.push(item);
    else if (item.awaiting_party && /client|insured|you/i.test(item.awaiting_party)) {
      awaitingYou.push(item);
    } else otherOpen.push(item);
  }

  return (
    <>
      <Topbar crumbs={["Client Portal", "Communications"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1100px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Inbox</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Communications
              </h1>
              <Body className="mt-2">
                Queries from your broker and underwriters. Items awaiting your
                input are pinned to the top.
              </Body>
            </div>
            <div className="text-right">
              <Eyebrow>Open</Eyebrow>
              <p className="mt-1 font-display text-[28px] font-semibold tabular-nums text-ink">
                {data.open_count}
              </p>
            </div>
          </header>

          {awaitingYou.length > 0 && (
            <Section
              title="Awaiting your response"
              count={awaitingYou.length}
              accent="spot"
            >
              {awaitingYou.map((it) => (
                <ThreadRow key={it.referral_code} item={it} highlight />
              ))}
            </Section>
          )}

          {otherOpen.length > 0 && (
            <Section title="Open — others responding" count={otherOpen.length}>
              {otherOpen.map((it) => (
                <ThreadRow key={it.referral_code} item={it} />
              ))}
            </Section>
          )}

          {closed.length > 0 && (
            <Section title="Closed" count={closed.length} muted>
              {closed.map((it) => (
                <ThreadRow key={it.referral_code} item={it} dim />
              ))}
            </Section>
          )}

          {data.items.length === 0 && (
            <Card pad="lg" className="flex items-center gap-3">
              <MessageSquare size={20} className="text-ink-mute" />
              <div>
                <Eyebrow>No threads</Eyebrow>
                <Body className="mt-1">
                  Nothing in your inbox — your placements are quiet right now.
                </Body>
              </div>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}

function Section({
  title,
  count,
  accent,
  muted,
  children,
}: {
  title: string;
  count: number;
  accent?: "spot";
  muted?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section>
      <header className="mb-2.5 flex items-center justify-between">
        <Eyebrow className={accent === "spot" ? "text-spot" : muted ? "" : ""}>
          {title}
        </Eyebrow>
        <Micro>{count}</Micro>
      </header>
      <Card pad="md" className={cn("space-y-0 p-0", muted && "opacity-80")}>
        <ul className="divide-y divide-rule">{children}</ul>
      </Card>
    </section>
  );
}

function ThreadRow({
  item,
  highlight,
  dim,
}: {
  item: CommunicationItem;
  highlight?: boolean;
  dim?: boolean;
}) {
  const dir = item.last_message_direction;
  const from =
    dir === "uw" || dir === "underwriter"
      ? "Underwriter"
      : dir === "broker"
        ? "Broker"
        : dir === "client" || dir === "you"
          ? "You"
          : "—";

  return (
    <li>
      <Link
        href={`/client/communications/${item.referral_code}`}
        className={cn(
          "group flex items-start gap-4 px-4 py-4 transition hover:bg-surface-sunken/40",
          dim && "text-ink-soft",
        )}
      >
        <div
          className={cn(
            "mt-1 h-2 w-2 shrink-0 rounded-full",
            highlight ? "bg-spot" : item.is_open ? "bg-info" : "bg-ink-mute/40",
          )}
          aria-hidden
        />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <p className={cn("font-semibold text-ink", dim && "text-ink-soft")}>
              {item.coverage}
            </p>
            <Micro>{item.entity_name}</Micro>
            {item.policy_label && <Micro>· {item.policy_label}</Micro>}
            <span className="ml-auto flex items-center gap-2">
              {highlight && (
                <Chip variant="spot" size="sm">
                  Awaiting you
                </Chip>
              )}
              {!highlight && item.is_open && (
                <Chip variant="info" size="sm">
                  {formatText(item.status, "capitalize")}
                </Chip>
              )}
              {!item.is_open && (
                <Chip variant="mute" size="sm">
                  Closed
                </Chip>
              )}
              <Micro>{fmtRelative(item.last_message_at)}</Micro>
            </span>
          </div>
          {item.last_message_excerpt && (
            <p
              className={cn(
                "mt-1.5 line-clamp-2 text-[13px] text-ink-soft",
                dim && "text-ink-mute",
              )}
            >
              <span className="font-medium text-ink-soft">{from}:</span>{" "}
              {item.last_message_excerpt}
            </p>
          )}
          {item.request_signal_evidence && (
            <p className="mt-1.5 text-[12px] italic text-spot-deep dark:text-spot">
              Evidence requested: {item.request_signal_evidence}
            </p>
          )}
        </div>
        <ChevronRight
          size={16}
          className="mt-1 shrink-0 text-ink-mute transition group-hover:text-ink"
        />
      </Link>
    </li>
  );
}
