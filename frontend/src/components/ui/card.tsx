import { cva, type VariantProps } from "class-variance-authority";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Tone-driven Card variants. The variant names match the design system's
 * single Tone vocabulary (see lib/types/common.ts).
 *
 * - default: neutral white surface
 * - tinted:  warm off-white, gentle elevation
 * - info:    teal — hero informative facts (score, premium)
 * - spot:    coral — awaiting / urgent action / CTAs
 * - pos:     green — strengths, savings
 * - aux:     blue — secondary informative
 * - warn:    amber — caution
 * - neg:     red — bad
 *
 * Padding scale matches the design-pack tokens:
 *   sm   = 14px (tight rows / chip-style cards)
 *   md   = 22px (the design-pack default — used everywhere unless noted)
 *   lg   = 24px (hero / decision banners with extra breathing room)
 */
const cardVariants = cva(
  "rounded-card border transition-colors",
  {
    variants: {
      variant: {
        default: "bg-surface border-rule",
        tinted: "bg-surface-elev border-rule",
        info: "bg-info-soft border-info",
        spot: "bg-spot-soft border-spot",
        pos: "bg-pos-soft border-pos",
        aux: "bg-aux-soft border-aux",
        warn: "bg-warn-soft border-warn",
        neg: "bg-neg-soft border-neg",
      },
      pad: {
        none: "",
        sm: "p-[14px]",
        md: "p-[22px]",
        lg: "p-6",
      },
    },
    defaultVariants: { variant: "default", pad: "md" },
  },
);

const padToBody: Record<NonNullable<VariantProps<typeof cardVariants>["pad"]>, string> = {
  none: "",
  sm: "p-[14px]",
  md: "p-[22px]",
  lg: "p-6",
};

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  /**
   * Optional header strip title. Renders the header when any of header /
   * icon / headerRight is provided. Named `header` (not `title`) to avoid
   * shadowing the standard HTML `title` tooltip attribute that
   * React.HTMLAttributes already advertises.
   */
  header?: string;
  /** Optional lucide icon shown to the left of the header label. */
  icon?: LucideIcon;
  /** Optional node aligned to the right of the header strip. */
  headerRight?: React.ReactNode;
}

export function Card({
  className,
  variant,
  pad,
  header,
  icon: IconCmp,
  headerRight,
  children,
  ...rest
}: CardProps) {
  const hasHeader = !!(header || IconCmp || headerRight);

  if (!hasHeader) {
    return (
      <div className={cn(cardVariants({ variant, pad }), className)} {...rest}>
        {children}
      </div>
    );
  }

  // When a header strip is requested, drop the wrapper padding and apply
  // it to the body instead so the rule sits flush with the card edges.
  // Header: 12px vertical × 18px horizontal, surface-elev background,
  // 14px semibold title, 15px icon — matches design-pack WbCard atom.
  const bodyPad = padToBody[pad ?? "md"];
  return (
    <div
      className={cn(cardVariants({ variant, pad: "none" }), "overflow-hidden", className)}
      {...rest}
    >
      <div className="flex items-center justify-between gap-3 border-b border-rule bg-surface-elev px-[18px] py-3">
        <div className="flex items-center gap-2.5 text-[14px] font-semibold leading-none text-ink">
          {IconCmp && <IconCmp size={15} className="shrink-0 text-ink-soft" />}
          {header && <span>{header}</span>}
        </div>
        {headerRight && (
          <div className="flex items-center gap-2 text-[12px] text-ink-soft">
            {headerRight}
          </div>
        )}
      </div>
      <div className={bodyPad}>{children}</div>
    </div>
  );
}
