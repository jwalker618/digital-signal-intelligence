"use client";

import { Paperclip } from "lucide-react";
import { formatDate, formatText } from "@/lib/format";

/** GUIDANCE
 * status:        Quote status string (e.g. "draft", "ready", "bound").
 *                Drives which middle column is rendered.
 * validFrom:     ISO date — shown when status is "draft" or "ready".
 * validUntil:    ISO date — shown when status is "draft" or "ready".
 * boundAt:       ISO date — shown when status is "bound".
 * policyNumber:  Shown when status is "bound". Defaults to "Pending".
 * submissionCode / quoteCode: Right-hand identifiers.
 */
export interface KeyDetailsBarProps {
  status?: string;
  validFrom?: string;
  validUntil?: string;
  boundAt?: string | null;
  policyNumber?: string | null;
  submissionCode?: string;
  quoteCode?: string;
}

/**
 * The sticky 3-column status + dates + codes bar shown at the top of every
 * workbench tab outside SummaryTab. Single source of truth — every tab
 * imports this instead of rebuilding it locally.
 */
export default function KeyDetailsBar({
  status,
  validFrom,
  validUntil,
  boundAt,
  policyNumber,
  submissionCode,
  quoteCode,
}: KeyDetailsBarProps) {
  const isQuote = status === "draft" || status === "ready";
  const isBound = status === "bound";

  return (
    <div className="sticky top-0 z-20 bg-dsi-background pt-3 pb-2">
      <div className="flex gap-dsi-pad rounded-t-xl border-b border-dsi-outline/50 overflow-x-hidden whitespace-nowrap bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
        <Paperclip className="icon" />
        <span className="text-sm">Key Details</span>
      </div>
      <div className="grid grid-cols-[10%_35%_55%] border-b-3 border-dsi-contrast-background overflow-x-hidden whitespace-nowrap rounded-b-xl bg-dsi-analysis shadow-sm pt-2 pb-2">
        <div className="text-left pl-dsi-pad pr-dsi-pad border-r border-dsi-outline/50 overflow-x-hidden">
          <span className="text-sm">Status:</span>
          <span className="pl-2 font-bold">{formatText(status, "upper", "N/A")}</span>
        </div>
        <div className="text-center pl-dsi-pad pr-dsi-pad border-r border-dsi-outline/50 overflow-x-hidden">
          {isQuote && (
            <>
              <span className="text-sm">Quote Valid From:</span>
              <span className="pl-2 uppercase font-bold">{formatDate(validFrom, "en-GB", "N/A")};</span>
              <span className="px-2"> </span>
              <span className="text-sm">Until:</span>
              <span className="pl-2 uppercase font-bold">{formatDate(validUntil, "en-GB", "N/A")}</span>
            </>
          )}
          {isBound && (
            <>
              <span className="text-sm">Bound Date:</span>
              <span className="pl-2 uppercase font-bold">{formatDate(boundAt, "en-GB", "N/A")}</span>
              <span className="text-sm pl-4">Policy Reference:</span>
              <span className="pl-2 uppercase font-bold">{policyNumber || "Pending"}</span>
            </>
          )}
        </div>
        <div className="text-center pl-dsi-pad pr-dsi-pad overflow-x-hidden">
          <span className="text-sm">Submission Code:</span>
          <span className="pl-2 uppercase font-bold">{submissionCode || ""}</span>
          <span className="px-6">||</span>
          <span className="text-sm">Quote Code:</span>
          <span className="pl-2 uppercase font-bold">{quoteCode || ""}</span>
        </div>
      </div>
    </div>
  );
}
