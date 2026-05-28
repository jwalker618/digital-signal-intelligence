import { cva, type VariantProps } from "class-variance-authority";
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
        sm: "p-3",
        md: "p-5",
        lg: "p-6",
      },
    },
    defaultVariants: { variant: "default", pad: "md" },
  },
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

export function Card({ className, variant, pad, ...rest }: CardProps) {
  return (
    <div className={cn(cardVariants({ variant, pad }), className)} {...rest} />
  );
}
