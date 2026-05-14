"use client";

import { 
  SubmissionStatusPill,
} from "@/components/base/content/primatives";

import { 
  KEYTERM, getPalette 
} from "@/lib/keytermPalette";

import { 
  formatText 
} from "@/lib/format";

export function StatusBadge(
  { status }: { status: string | null | undefined }
) {
  if (!status) return <span className="opacity-60">—</span>;
  
  return (
    <SubmissionStatusPill decision={status}></SubmissionStatusPill>
  );
}
