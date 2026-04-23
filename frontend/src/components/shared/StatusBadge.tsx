"use client";

import { 
  StatusPill 
} from "@/components/base/content/primatives";

import { 
  HEALTH_PALETTE 
} from "@/lib/statusPalette";

import { 
  formatText 
} from "@/lib/format";

export function StatusBadge(
  { status }: { status: string | null | undefined }
) {
  if (!status) return <span className="opacity-60">—</span>;
  
  return (
    <StatusPill palette={HEALTH_PALETTE} status={status}>
      {formatText(status, "upper")}
    </StatusPill>
  );
}
