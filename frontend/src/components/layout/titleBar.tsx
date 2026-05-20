"use client";

/**
 * TitleBar — the main area's top banner: breadcrumb + quick-action slot +
 * optional page-actions ellipsis trigger. Reads everything it needs from
 * the store.
 *
 * Clicking the info icon next to the entity name opens KeyDetailsModal,
 * which surfaces status / dates / codes that used to live in the now-
 * deleted KeyDetailsBar.
 */

import { useState } from "react";
import { Info, MoreVertical, Paperclip } from "lucide-react";

import Modal from "@/components/base/modal";
import { LabelValueList } from "@/components/base/content/primatives";
import { useDsiStore } from "@/store/dsiStore";
import { useAuthStore } from "@/store/authStore";
import { formatDate, formatText } from "@/lib/format";

export default function TitleBar() {
  const activeSubmission = useDsiStore((s) => s.activeSubmission);
  const activeQuote = useDsiStore((s) => s.activeQuote);
  const activeMenu = useDsiStore((s) => s.activeMenu);
  const previousMenu = useDsiStore((s) => s.previousMenu);
  const pageQuickAction = useDsiStore((s) => s.pageQuickAction);
  const hasPageActions = useDsiStore((s) => s.hasPageActions);
  const sessionWarning = useAuthStore((s) => s.sessionWarning);

  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sub = activeSubmission as any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const quote = activeQuote as any;
  const status: string | undefined = quote?.status;
  const isQuote = status === "draft" || status === "ready";
  const isBound = status === "bound";

  const detailRows = [
    { label: "Status", value: formatText(status, "upper", "N/A") },
    ...(isQuote
      ? [
          { label: "Quote Valid From", value: formatDate(quote?.valid_from, "en-GB", "N/A") },
          { label: "Quote Valid Until", value: formatDate(quote?.valid_until, "en-GB", "N/A") },
        ]
      : []),
    ...(isBound
      ? [
          { label: "Bound Date", value: formatDate(quote?.bound_at, "en-GB", "N/A") },
          { label: "Policy Reference", value: quote?.policy_number || "Pending" },
        ]
      : []),
    { label: "Submission Code", value: sub?.submission_code || "—" },
    { label: "Quote Code", value: quote?.quote_code || "—" },
  ];

  return (
    <div
      className="
        flex
        border-b-3 border-generate-text-outline
        items-center justify-between
        px-generate-main"
        style={{
          height: "var(--cw)"
        }}
    >
      <h1 className="font-inter text-2xl tracking-wide flex items-center gap-4">
        <span className="flex items-center gap-4">
          <span className="font-light">/</span>
          {activeSubmission ? previousMenu : activeMenu}
        </span>

        {activeSubmission && (
          <span className="flex items-center gap-4">
            <span className="font-light">/</span>
            <span className="flex items-center gap-2">
              <span className="font-bold">{sub?.entity_name}</span>
              <button
                onClick={() => setIsDetailsOpen(true)}
                aria-label="Submission key details"
                className="text-generate-text-placeholder hover:text-generate-text-input"
              >
                <Info className="generate-app-icon" />
              </button>
            </span>
            <span className="font-light">/</span>
            <span>{activeMenu}</span>
          </span>
        )}
      </h1>

      <div className="flex items-center gap-2 px-generate-main">
        {/* Session expiry warning (driven by SessionGuard → authStore) */}
        {sessionWarning && (
          <div
            className="
              absolute left-[75%]
              generate-light-notificationpill"
          >
            {sessionWarning}
          </div>
        )}

        {/* Quick action slot (optional, page-provided) */}
        {pageQuickAction}

        {/* Ellipsis trigger (optional, page-provided) */}
        {hasPageActions && (
          <button
            onClick={() => useDsiStore.getState().setPageActionsOpen(true)}
            className="p-1.5 rounded-md text-generate-text-placeholder hover:bg-generate-light-input hover:text-generate-text-input"
            title="Page Actions"
          >
            <MoreVertical className="generate-app-icon" />
          </button>
        )}
      </div>

      <Modal
        isOpen={isDetailsOpen}
        onClose={() => setIsDetailsOpen(false)}
        title="Key Details"
        icon={Paperclip}
      >
        <LabelValueList rows={detailRows} variant="modal" />
      </Modal>
    </div>
  );
}
