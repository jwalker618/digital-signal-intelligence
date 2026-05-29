"use client";

import { MessagesSquare } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { WorkArea } from "@/components/ui/work-area";
import { Body, Micro } from "@/components/ui/typography";
import { KpiSnug } from "@/components/ui/kpi-snug";
import { fmtRelative } from "@/lib/utils";
import { useClientWorkbench } from "../_lib/context";

export default function CommunicationsPage() {
  const cw = useClientWorkbench();
  if (!cw) return null;

  const threads = cw.threads ?? [];
  const awaitingYou = threads.filter((t) => t.awaiting === "broker").length;

  return (
    <WorkArea>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card pad="sm">
          <KpiSnug label="Open threads" value={threads.length} tone="info" />
        </Card>
        <Card pad="sm">
          <KpiSnug label="Awaiting you" value={awaitingYou} tone="spot" />
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
            {awaitingYou} on you
          </Chip>
        }
      >
        {threads.length === 0 ? (
          <Body className="italic">No referral threads for this client.</Body>
        ) : (
          <div className="flex flex-col gap-3.5">
            {threads.map((t) => (
              <div
                key={t.referral_code}
                className="overflow-hidden rounded-card border border-rule"
              >
                {/* Thread header */}
                <div className="flex items-center gap-2.5 border-b border-rule bg-surface-elev px-3.5 py-2.5">
                  <Chip variant="default" size="sm">
                    {t.line}
                  </Chip>
                  {t.ask && (
                    <span className="truncate text-[13px] font-semibold">{t.ask}</span>
                  )}
                  <span className="flex-1" />
                  <Chip variant={t.awaiting === "broker" ? "spot" : "info"} size="sm">
                    {t.awaiting === "broker" ? "on you" : "on client"}
                  </Chip>
                </div>
                {/* Message bubbles */}
                <div className="flex flex-col gap-2.5 p-3.5">
                  {t.messages.map((m, i) => {
                    const mine = m.direction === "broker";
                    return (
                      <div
                        key={i}
                        className={`flex ${mine ? "justify-end" : "justify-start"}`}
                      >
                        <div className="max-w-[74%]">
                          <div
                            className={`rounded-[10px] border border-rule px-3 py-2 text-[12.5px] leading-relaxed text-ink ${
                              mine ? "bg-info-soft" : "bg-surface-sunken"
                            }`}
                          >
                            {m.body}
                          </div>
                          <Micro
                            className={`mt-1 block ${mine ? "text-right" : "text-left"}`}
                          >
                            {m.who}
                            {m.at ? ` · ${fmtRelative(m.at)}` : ""}
                          </Micro>
                          {m.signal && (
                            <div className={`mt-1 ${mine ? "text-right" : "text-left"}`}>
                              <Chip variant="info" size="sm">
                                <span className="font-mono text-[10.5px]">{m.signal}</span>
                              </Chip>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </WorkArea>
  );
}
