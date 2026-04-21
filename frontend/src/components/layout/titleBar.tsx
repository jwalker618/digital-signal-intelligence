"use client";

/**
 * TitleBar — the main area's top banner: breadcrumb + quick-action slot +
 * optional page-actions ellipsis trigger. Reads everything it needs from
 * the store.
 */

import { MoreVertical } from "lucide-react";

import { useDsiStore } from "@/store/dsiStore";
import { useAuthStore } from "@/store/authStore";

export default function TitleBar() {
  const activeSubmission = useDsiStore((s) => s.activeSubmission);
  const activeMenu = useDsiStore((s) => s.activeMenu);
  const previousMenu = useDsiStore((s) => s.previousMenu);
  const pageQuickAction = useDsiStore((s) => s.pageQuickAction);
  const hasPageActions = useDsiStore((s) => s.hasPageActions);
  const sessionWarning = useAuthStore((s) => s.sessionWarning);

  return (
    <div
      className="
        flex
        border-b-3 border-dsi-outline 
        items-center justify-between 
        px-dsi-main"
      style={{ 
        height: "var(--cw)" 
      }}
    >
      <h1 className="font-inter text-2xl tracking-wide flex items-center gap-4">
        <span className="flex items-center gap-4">
          <span className="opacity-50 font-light">/</span>
          {activeSubmission ? previousMenu : activeMenu}
        </span>

        {activeSubmission && (
          <span className="flex items-center gap-4">
            <span className="opacity-50 font-light">/</span>
            <span className="font-bold">
              {(activeSubmission as any).entity_name}
            </span>
            <span className="opacity-50 font-light">/</span>
            <span>{activeMenu}</span>
          </span>
        )}
      </h1>

      <div className="flex items-center gap-2 px-dsi-main">
        {/* Session expiry warning (driven by SessionGuard → authStore) */}
        {sessionWarning && (
          <div
            className="
              p-1.5
              bg-dsi-outline
              border-b-1 border-dsi-selected
              text-dsi-contrast-background text-xs
              rounded-md shadow-sm"
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
            className="p-1.5 rounded text-dsi-contrast-background hover:bg-dsi-outline/10 hover:text-dsi-selected transition-colors"
            title="Page Actions"
          >
            <MoreVertical className="icon" />
          </button>
        )}
      </div>
    </div>
  );
}
