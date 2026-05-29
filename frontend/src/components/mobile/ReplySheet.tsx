"use client";

import { ArrowUp, ArrowUpRight, Clock, Sparkles } from "lucide-react";
import { Chip } from "./primitives";
import type {
  MobileFeedAwaiting,
  MobileFeedThread,
} from "@/lib/mobileFeed";

export type SheetState =
  | { kind: "thread"; data: MobileFeedThread }
  | { kind: "await"; data: MobileFeedAwaiting }
  | null;

export function ReplySheet({
  sheet,
  onClose,
  onSend,
}: {
  sheet: SheetState;
  onClose: () => void;
  onSend: () => void;
}) {
  const open = sheet != null;
  const isAwait = sheet?.kind === "await";

  const title = sheet
    ? isAwait
      ? (sheet.data as MobileFeedAwaiting).title
      : (sheet.data as MobileFeedThread).who
    : "";
  const sub = sheet
    ? isAwait
      ? `${(sheet.data as MobileFeedAwaiting).line} · ${(sheet.data as MobileFeedAwaiting).counterparty}`
      : (sheet.data as MobileFeedThread).sub
    : "";
  const age = sheet ? (sheet.data as { age: string }).age : "";

  const messages = !sheet
    ? []
    : sheet.kind === "thread"
      ? sheet.data.messages
      : [
          {
            from: "them" as const,
            who: (sheet.data as MobileFeedAwaiting).counterparty,
            text: (sheet.data as MobileFeedAwaiting).sub,
            time: (sheet.data as MobileFeedAwaiting).age,
          },
        ];

  return (
    <>
      <div
        className={"dsi-scrim" + (open ? " on" : "")}
        onClick={onClose}
        aria-hidden={!open}
      />
      <div
        className={"dsi-sheet" + (open ? " on" : "")}
        role="dialog"
        aria-modal="true"
        aria-hidden={!open}
      >
        <div className="dsi-grab" />
        {sheet && (
          <>
            <div className="dsi-sheet-hd">
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 10,
                }}
              >
                <div style={{ minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: 18,
                      fontWeight: 700,
                      letterSpacing: "-.01em",
                    }}
                  >
                    {title}
                  </div>
                  <div
                    style={{
                      fontSize: 12.5,
                      color: "var(--color-ink-mute)",
                      marginTop: 2,
                    }}
                  >
                    {sub}
                  </div>
                </div>
                <Chip tone="spot" icon={<Clock size={11} />}>
                  {age}
                </Chip>
              </div>
            </div>
            <div className="dsi-sheet-body">
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 12,
                }}
              >
                {messages.map((m, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignSelf:
                        m.from === "me"
                          ? "flex-end"
                          : m.from === "sys"
                            ? "center"
                            : "flex-start",
                      maxWidth: "100%",
                    }}
                  >
                    {m.who && m.from === "them" && (
                      <div className="dsi-msg-who">{m.who}</div>
                    )}
                    <div className={"dsi-bubble " + m.from}>{m.text}</div>
                  </div>
                ))}
              </div>
              <button type="button" className="dsi-prefill" onClick={onSend}>
                <Sparkles size={16} />
                <span style={{ flex: 1, textAlign: "left" }}>
                  Smart reply ready — signal &amp; latest attestation pre-filled
                </span>
                <ArrowUpRight size={16} />
              </button>
            </div>
            <div className="dsi-compose">
              <input
                className="dsi-compose-in"
                placeholder="Type a reply…"
                aria-label="Reply"
              />
              <button
                type="button"
                className="dsi-send dsi-press"
                onClick={onSend}
                aria-label="Send"
              >
                <ArrowUp size={20} />
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}
