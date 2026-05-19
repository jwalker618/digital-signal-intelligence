"use client";

/**
 * Right-hand slot for SubmissionHeaderCard — shows quote status and the
 * date/policy fields relevant to the current quote.status.
 */

import { useDsiStore } from "@/store/dsiStore";
import { formatDate, formatText } from "@/lib/format";

export default function DecisionStatusFields() {
  const { activeQuote } = useDsiStore() as any;

  if (!activeQuote) return null;

  const status = activeQuote.status;

  return (
    <>
      <div className="flex flex-col items-center">
        <span className="text-sm">Status</span>
        <span className="font-bold hover:text-generate-text-input">{formatText(status, "upper")}</span>
      </div>

      {(status === "draft" || status === "ready") && (
        <>
          <div className="flex flex-col items-center">
            <span className="text-sm">Valid From</span>
            <span className="font-bold hover:text-generate-text-input">{formatDate(activeQuote.valid_from)}</span>
          </div>
          
          <div className="flex flex-col items-center">
            <span className="text-sm">Valid Until</span>
            <span className="font-bold hover:text-generate-text-input">{formatDate(activeQuote.valid_until)}</span>
          </div>
        </>
      )}

      {status === "bound" && (
        <>
          <div className="flex flex-col items-center">
            <span className="text-sm">Bound Date</span>
            <span className="font-bold hover:text-generate-text-input">{formatDate(activeQuote.bound_at)}</span>
          </div>
          
          <div className="flex flex-col items-center">
            <span className="text-sm">Policy Ref</span>
            <span className="font-bold hover:text-generate-text-input">
              {formatText(activeQuote.policy_number, "upper", "pending")}
            </span>
          </div>
        </>
      )}
    </>
  );
}
