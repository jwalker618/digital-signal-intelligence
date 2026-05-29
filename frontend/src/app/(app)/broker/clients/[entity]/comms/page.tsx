"use client";

import Link from "next/link";
import { ChevronRight, MessagesSquare } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { useClientWorkbench } from "../_lib/context";

export default function CommunicationsPage() {
  const cw = useClientWorkbench();
  if (!cw) return null;

  // Per-coverage referral state derived from the workbench payload.
  const awaitingYou = cw.coverages.filter((c) => c.awaiting === "broker");
  const awaitingClient = cw.coverages.filter((c) => c.awaiting === "client");
  const threads = cw.coverages.filter((c) => c.awaiting != null);

  return (
    <WorkArea>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card pad="sm">
          <KpiSnug label="Open threads" value={threads.length} tone="info" />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Awaiting you" value={awaitingYou.length} tone="spot" />
        </Card>
        <Card pad="sm">
          <KpiSnug
            label="Avg response"
            value={cw.avg_response_hours != null ? `${cw.avg_response_hours}h` : "—"}
          />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Last activity" value={cw.last_message ?? "—"} />
        </Card>
      </div>

      <Card
        header="Referral threads"
        icon={MessagesSquare}
        pad="md"
        headerRight={
          <Chip variant="spot" size="sm">
            {awaitingYou.length} on you
          </Chip>
        }
      >
        {threads.length === 0 ? (
          <Body className="italic">No open referral threads for this client.</Body>
        ) : (
          <div className="flex flex-col gap-2.5">
            {threads.map((c) => (
              <Link
                key={c.code}
                href={`/broker/communications/${c.code}`}
                className="flex items-center gap-2.5 rounded-card border border-rule bg-surface-elev px-3.5 py-3 hover:bg-surface-sunken"
              >
                <Chip variant="default" size="sm">
                  {c.line}
                </Chip>
                <span className="flex-1 text-[13px] font-medium">
                  {c.carrier ?? "Carrier"} · {c.code}
                </span>
                <Chip variant={c.awaiting === "broker" ? "spot" : "info"} size="sm">
                  {c.awaiting === "broker" ? "on you" : "on client"}
                </Chip>
                <ChevronRight size={16} className="text-ink-mute" />
              </Link>
            ))}
          </div>
        )}
        {awaitingClient.length > 0 && (
          <Micro className="mt-3 block border-t border-rule pt-3">
            {awaitingClient.length} thread{awaitingClient.length === 1 ? "" : "s"} awaiting
            the client.
          </Micro>
        )}
      </Card>
    </WorkArea>
  );
}
