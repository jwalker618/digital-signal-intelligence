"use client";

// v8.2 — Marsh practice vertical filter
//
// Renders as a horizontal row of chips at the top of every broker
// surface. Selection persists in dsiStore.verticalFilter so it
// follows the broker across pages.

import { useEffect, useState } from "react";
import { X } from "lucide-react";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { fetchVerticals } from "@/lib/portalApi";
import type { VerticalSummary } from "@/types/portal";


export default function VerticalFilter() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const verticalFilter = useDsiStore((s) => s.verticalFilter);
  const setVerticalFilter = useDsiStore((s) => s.setVerticalFilter);

  const [verticals, setVerticals] = useState<VerticalSummary[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchVerticals(accessToken);
        if (!cancelled) setVerticals(resp.verticals);
      } catch {
        if (!cancelled) setVerticals([]);
      }
    }
    if (accessToken) load();
    return () => { cancelled = true; };
  }, [accessToken]);

  if (!verticals || verticals.length === 0) return null;

  // Only show verticals that have at least one client in the broker's book
  const visible = verticals.filter((v) => v.client_count > 0 || v.slug === verticalFilter);
  if (visible.length === 0) return null;

  return (
    <div className="flex items-center gap-2 flex-wrap pb-2">
      <span className="text-xs text-generate-text-placeholder mr-1">
        Filter by Marsh practice:
      </span>
      <VerticalChip
        label="All"
        active={verticalFilter == null}
        onClick={() => setVerticalFilter(null)}
      />
      {visible.map((v) => (
        <VerticalChip
          key={v.slug}
          label={v.name}
          count={v.client_count}
          active={verticalFilter === v.slug}
          onClick={() => setVerticalFilter(v.slug)}
        />
      ))}
      {verticalFilter != null && (
        <button
          onClick={() => setVerticalFilter(null)}
          className="
            ml-2 flex items-center gap-1
            text-xs text-generate-text-placeholder
            hover:text-generate-text-input
          "
        >
          <X className="generate-app-icon" /> Clear
        </button>
      )}
    </div>
  );
}


function VerticalChip({
  label, count, active, onClick,
}: {
  label: string;
  count?: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        text-xs px-3 py-1 rounded-full
        border transition-colors
        ${active
          ? "bg-generate-dark-background text-generate-text-input border-generate-text-outline font-bold"
          : "border-generate-text-outline text-generate-text-placeholder hover:text-generate-text-input"}
      `}
    >
      {label}
      {count !== undefined && count > 0 && (
        <span className={`ml-1.5 text-[10px] ${active ? "opacity-80" : "opacity-60"}`}>
          {count}
        </span>
      )}
    </button>
  );
}


/**
 * Helper hook -- returns the current vertical filter slug and a
 * predicate any broker page can use to filter its own per-client
 * lists consistently.
 */
export function useVerticalFilter() {
  const slug = useDsiStore((s) => s.verticalFilter);
  return {
    slug,
    matches: (verticalSlug: string | null | undefined) =>
      slug == null || slug === verticalSlug,
  };
}
