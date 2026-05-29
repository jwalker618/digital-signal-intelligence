import { cn } from "@/lib/utils";

/**
 * Standard page-content wrapper used by every persona/workbench page.
 *
 * Locks the three things the design-pack treats as page-level invariants:
 *   - outer padding (24px)        — `padding: 24` on the templates' .work area
 *   - gap between sections (14px) — gap: 14 between page-level cards/blocks
 *   - max content width (1280px)  — visual centre line for the page grid
 *
 * Use this in place of bespoke `<div className="flex-1 overflow-y-auto px-9 py-7">`
 * wrappers so spacing stays uniform across pages.
 */
export function WorkArea({
  children,
  className,
  maxWidth = 1280,
}: {
  children: React.ReactNode;
  className?: string;
  /** Override the max content width (defaults to 1280). Pass `null` to disable. */
  maxWidth?: number | null;
}) {
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div
        className={cn("mx-auto grid gap-3.5", className)}
        style={maxWidth ? { maxWidth: `${maxWidth}px` } : undefined}
      >
        {children}
      </div>
    </div>
  );
}
