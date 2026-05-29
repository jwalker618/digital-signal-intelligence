"use client";

import Link from "next/link";
import { memo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, Caption } from "@/components/ui/typography";
import { cn } from "@/lib/utils";

export interface AwaitingItem {
  ask: string;
  line: string;
  age: string;
  href: string;
}

export const AwaitingCard = memo(function AwaitingCard({
  items,
}: {
  items: AwaitingItem[];
}) {
  const [idx, setIdx] = useState(0);
  if (items.length === 0) {
    return (
      <Card pad="lg" className="flex flex-col">
        <Eyebrow className="text-spot-deep dark:text-spot">Awaiting you</Eyebrow>
        <p className="mt-3 text-[15px] font-semibold text-ink">
          Nothing waiting on you right now.
        </p>
        <Caption className="mt-1">
          New requests from carriers or your broker will appear here.
        </Caption>
      </Card>
    );
  }

  const item = items[idx]!;
  const next = items[(idx + 1) % items.length]!;
  const canBack = idx > 0;
  const canFwd = idx < items.length - 1;
  const showNextPreview = items.length > 1 && canFwd;

  return (
    <Card variant="spot" pad="lg" className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <Eyebrow className="text-spot-deep dark:text-spot">Awaiting you</Eyebrow>
        <div className="flex items-center gap-1">
          <button
            type="button"
            aria-label="Previous query"
            onClick={() => canBack && setIdx(idx - 1)}
            disabled={!canBack}
            className={cn(
              "flex h-[22px] w-[22px] items-center justify-center rounded border border-spot text-spot-deep transition-opacity dark:text-spot",
              !canBack && "opacity-30",
            )}
          >
            <ChevronLeft size={14} />
          </button>
          <Chip variant="spot" size="sm" className="min-w-[50px] justify-center">
            {idx + 1} of {items.length}
          </Chip>
          <button
            type="button"
            aria-label="Next query"
            onClick={() => canFwd && setIdx(idx + 1)}
            disabled={!canFwd}
            className={cn(
              "flex h-[22px] w-[22px] items-center justify-center rounded border border-spot text-spot-deep transition-opacity dark:text-spot",
              !canFwd && "opacity-30",
            )}
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
      <div>
        <p className="text-[16px] font-semibold leading-snug text-ink">
          {item.ask}
        </p>
        <Caption className="mt-1">
          {item.age} · {item.line}
        </Caption>
      </div>
      <div className="mt-auto flex gap-2">
        <Link
          href={item.href}
          className="inline-flex h-10 items-center justify-center rounded-btn bg-spot px-4 text-[13px] font-semibold text-white hover:opacity-90"
        >
          Open thread
        </Link>
        <Button variant="ghost">Snooze</Button>
      </div>
      {showNextPreview && (
        <button
          type="button"
          onClick={() => setIdx(idx + 1)}
          className="mt-1 flex items-center gap-2 border-t border-dashed border-spot pt-2.5 text-left text-[12px] text-spot-deep dark:text-spot"
        >
          <span className="opacity-70">Next →</span>
          <span className="flex-1 overflow-hidden text-ellipsis whitespace-nowrap">
            {next.ask}
          </span>
        </button>
      )}
    </Card>
  );
});
