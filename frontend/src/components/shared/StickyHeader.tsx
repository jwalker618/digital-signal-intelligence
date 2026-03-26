"use client";

import { Paperclip } from "lucide-react";

interface StickyHeaderProps {
  status?: string;
  validFrom?: string;
  validUntil?: string;
  boundAt?: string | null;
  policyNumber?: string | null;
  submissionCode?: string;
  quoteCode?: string;
}

export default function StickyHeader({
  status, validFrom, validUntil, boundAt, policyNumber, submissionCode, quoteCode
}: StickyHeaderProps) {
  return (
    <div className="sticky top-0 z-20 bg-dsi-background pt-3 pb-2">
      <div className="flex gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pt-2 pb-2">
        <Paperclip className="icon"/><span className="text-sm">Key Details</span>
      </div>
      <div className="grid grid-cols-[10%_35%_55%] grid-rows-1 border-b-3 border-dsi-contrast-background overflow-x-hidden whitespace-nowrap border-collapse rounded-b-xl bg-dsi-analysis shadow-sm pt-2 pb-2">
        <div className="text-left pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
          <span className="text-sm">Status:</span><span className="pl-2 uppercase font-bold">{status || 'N/A'}</span>
        </div>
        <div className="text-center pl-dsi-pad pr-dsi-pad border-r-1 border-dsi-outline/50 overflow-x-hidden">
          {(status === 'draft' || status === 'ready') && (
            <span>
              <span className="text-sm">Quote Valid From:</span>
              <span className="pl-2 uppercase font-bold">{validFrom ? new Date(validFrom).toLocaleDateString() : 'N/A'};</span>
              <span className="pl-2 pr-2"> </span>
              <span className="text-sm">Until:</span>
              <span className="pl-2 uppercase font-bold">{validUntil ? new Date(validUntil).toLocaleDateString() : 'N/A'}</span>
            </span>
          )}
          {status === 'bound' && (
            <span>
              <span className="text-sm">Bound Date:</span>
              <span className="pl-2 uppercase font-bold">{boundAt ? new Date(boundAt).toLocaleDateString() : 'N/A'}</span>
              <span className="text-sm">Policy Reference:</span>
              <span className="pl-2 uppercase font-bold">{policyNumber || 'Pending'}</span>
            </span>
          )}
        </div>
        <div className="text-center pl-dsi-pad pr-dsi-pad overflow-x-hidden">
          <span className="text-sm">Submission Code: </span><span className="pl-2 uppercase font-bold">{submissionCode || ''}</span>
          <span className="pl-6 pr-6">||</span>
          <span className="text-sm">Quote Code: </span><span className="pl-2 uppercase font-bold">{quoteCode || ''}</span>
        </div>
      </div>
    </div>
  );
}
