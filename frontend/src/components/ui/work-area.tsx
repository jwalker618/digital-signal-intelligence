import { cn } from "@/lib/utils";

/**
 * Standard page-content wrapper used by every persona/workbench page.
 *
 * Matches the design-pack `.work` area:
 *   - outer padding 28px 36px (`py-7 px-9`)
 *   - gap between sections (14px default; pages override via className)
 *   - content fills the available width (no max-width / centring) so the
 *     left and right margins are uniform and the page fills the screen
 *
 * Use this in place of bespoke `<div className="flex-1 overflow-y-auto px-9 py-7">`
 * wrappers so spacing stays uniform across pages.
 */
export function WorkArea({
  children,
  className,
  maxWidth = null,
}: {
  children: React.ReactNode;
  className?: string;
  /** Optional max content width. Defaults to null — content fills the width. */
  maxWidth?: number | null;
}) {
  return (
    <div className="flex-1 overflow-y-auto px-9 py-7">
      <div
        className={cn("grid gap-3.5", maxWidth && "mx-auto", className)}
        style={maxWidth ? { maxWidth: `${maxWidth}px` } : undefined}
      >
        {children}
      </div>
    </div>
  );
}
