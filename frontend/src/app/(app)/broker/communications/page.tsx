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

export default function BrokerCommunicationsPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "BROKER";

  const { data, error, loading } = useRoleScopedFetch<CommunicationsListResponse>({
    fetcher: () => fetchCommunications(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "BROKER") return <RoleGate expected="broker" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return <CommsBody data={data} />;
}

function CommsBody({ data }: { data: CommunicationsListResponse }) {
  // Broker viewport: split by who's awaiting reply.
  const awaitingMe: CommunicationItem[] = [];
  const awaitingClient: CommunicationItem[] = [];
  const otherOpen: CommunicationItem[] = [];
  const closed: CommunicationItem[] = [];
  for (const item of data.items) {
    if (!item.is_open) closed.push(item);
    else if (item.awaiting_party && /broker|me/i.test(item.awaiting_party)) {
      awaitingMe.push(item);
    } else if (item.awaiting_party && /client|insured/i.test(item.awaiting_party)) {
      awaitingClient.push(item);
    } else otherOpen.push(item);
  }

  return (
    <>
      <Topbar crumbs={["Broker Portal", "Communications"]} />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1100px] gap-6">
          <header className="flex items-end justify-between gap-6">
            <div>
              <Eyebrow>Inbox</Eyebrow>
              <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
                Communications
              </h1>
              <Body className="mt-2">
                Queries from underwriters and follow-ups with your clients.
                Items waiting on you sit at the top.
              </Body>
            </div>
            <div className="text-right">
              <Eyebrow>Open</Eyebrow>
              <p className="mt-1 font-display text-[28px] font-semibold tabular-nums text-ink">
                {data.open_count}
              </p>
            </div>
          </header>

          {awaitingMe.length > 0 && (
            <Section title="Awaiting you" count={awaitingMe.length} accent="spot">
              {awaitingMe.map((it) => (
                <ThreadRow
                  key={it.referral_code}
                  item={it}
                  highlight
                  basePath="/broker/communications"
                />
              ))}
            </Section>
          )}

          {awaitingClient.length > 0 && (
            <Section title="Waiting on client" count={awaitingClient.length}>
              {awaitingClient.map((it) => (
                <ThreadRow
                  key={it.referral_code}
                  item={it}
                  basePath="/broker/communications"
                />
              ))}
            </Section>
          )}

          {otherOpen.length > 0 && (
            <Section title="Other open" count={otherOpen.length}>
              {otherOpen.map((it) => (
                <ThreadRow
                  key={it.referral_code}
                  item={it}
                  basePath="/broker/communications"
                />
              ))}
            </Section>
          )}

          {closed.length > 0 && (
            <Section title="Closed" count={closed.length} muted>
              {closed.map((it) => (
                <ThreadRow
                  key={it.referral_code}
                  item={it}
                  dim
                  basePath="/broker/communications"
                />
              ))}
            </Section>
          )}

          {data.items.length === 0 && (
            <Card pad="lg" className="flex items-center gap-3">
              <MessageSquare size={20} className="text-ink-mute" />
              <div>
                <Eyebrow>No threads</Eyebrow>
                <Body className="mt-1">
                  Your inbox is empty.
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
        <Eyebrow className={accent === "spot" ? "text-spot" : ""}>{title}</Eyebrow>
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
  basePath,
}: {
  item: CommunicationItem;
  highlight?: boolean;
  dim?: boolean;
  basePath: string;
}) {
  const dir = item.last_message_direction;
  const from =
    dir === "uw" || dir === "underwriter"
      ? "Underwriter"
      : dir === "broker"
        ? "You"
        : dir === "client" || dir === "insured"
          ? "Client"
          : "—";
  return (
    <li>
      <Link
        href={`${basePath}/${item.referral_code}`}
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
        />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <p className={cn("font-semibold text-ink", dim && "text-ink-soft")}>
              {item.coverage}
            </p>
            <Micro>{item.entity_name}</Micro>
            <span className="ml-auto flex items-center gap-2">
              {highlight && (
                <Chip variant="spot" size="sm">
                  Awaiting you
                </Chip>
              )}
              {!highlight && item.is_open && item.awaiting_party && (
                <Chip variant="info" size="sm">
                  {formatText(item.awaiting_party, "capitalize")}
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
        </div>
        <ChevronRight
          size={16}
          className="mt-1 shrink-0 text-ink-mute transition group-hover:text-ink"
        />
      </Link>
    </li>
  );
}
