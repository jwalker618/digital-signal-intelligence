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
      <div>
        <span className="block generate-analysis-description">Status</span>
        <span className="generate-analysis-item">{formatText(status, "upper")}</span>
      </div>

      {(status === "draft" || status === "ready") && (
        <>
          <div>
            <span className="block generate-analysis-description">Valid From</span>
            <span className="generate-analysis-item">{formatDate(activeQuote.valid_from)}</span>
          </div>
          <div>
            <span className="block generate-analysis-description">Valid Until</span>
            <span className="generate-analysis-item">{formatDate(activeQuote.valid_until)}</span>
          </div>
        </>
      )}

      {status === "bound" && (
        <>
          <div>
            <span className="block generate-analysis-description">Bound Date</span>
            <span className="generate-analysis-item">{formatDate(activeQuote.bound_at)}</span>
          </div>
          <div>
            <span className="block generate-analysis-description">Policy Ref</span>
            <span className="generate-analysis-item">
              {formatText(activeQuote.policy_number, "upper", "pending")}
            </span>
          </div>
        </>
      )}
    </>
  );
}
