"use client";

import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { cn } from "@/lib/utils";

interface BackButtonProps {
  /** Defaults to "Back". */
  label?: string;
  className?: string;
}

/**
 * Small inline "← Back" affordance that walks the browser history one step.
 * No href variant — by design. Use a normal `<Link>` for hard navigation.
 */
export function BackButton({ label = "Back", className }: BackButtonProps) {
  const router = useRouter();
  return (
    <button
      type="button"
      onClick={() => router.back()}
      className={cn(
        "inline-flex items-center gap-1 text-sm text-ink-soft transition-colors hover:text-ink",
        className,
      )}
    >
      <ChevronLeft size={16} aria-hidden />
      {label}
    </button>
  );
}
