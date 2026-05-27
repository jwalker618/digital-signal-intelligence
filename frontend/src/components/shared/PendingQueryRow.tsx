"use client";

// Shared between BrokerOverview and ClientOverview -- renders an
// alert-toned card for an open underwriter query, showing the
// excerpt and routing into Communications on click.

import { ArrowRight } from "lucide-react";

import type { CommunicationItem } from "@/types/portal";


export default function PendingQueryRow({
  query, onClick,
}: {
  query: CommunicationItem;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="
        w-full text-left
        border border-generate-text-maybe/30 bg-generate-text-maybe/5
        rounded-lg p-3
        hover:border-generate-text-input
        group"
    >
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-sm font-bold">
          {query.policy_label ?? formatCoverageLabel(query.coverage)}
        </span>
        <span className="text-xs text-generate-text-placeholder group-hover:text-generate-text-input">
          Open in Communications <ArrowRight className="generate-app-icon inline-block ml-1" />
        </span>
      </div>
      {query.last_message_excerpt && (
        <p className="text-sm italic">"{query.last_message_excerpt}"</p>
      )}
      {query.request_signal_evidence && (
        <div className="text-xs mt-2">
          <span className="text-generate-text-placeholder">Evidence requested: </span>
          <code className="text-generate-text-comment">{query.request_signal_evidence}</code>
        </div>
      )}
    </button>
  );
}


export function formatCoverageLabel(c: string): string {
  return c.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}
