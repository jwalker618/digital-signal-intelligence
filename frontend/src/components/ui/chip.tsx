import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const chipVariants = cva(
  "inline-flex items-center gap-1.5 rounded-chip font-medium",
  {
    variants: {
      variant: {
        mute: "bg-surface-sunken text-ink-soft",
        info: "bg-info-soft text-info-deep dark:text-info",
        spot: "bg-spot-soft text-spot-deep dark:text-spot",
        pos: "bg-pos-soft text-pos",
        aux: "bg-aux-soft text-aux",
        warn: "bg-warn-soft text-warn",
        neg: "bg-neg-soft text-neg",
        outline: "border border-rule-strong text-ink-soft",
      },
      size: {
        sm: "px-2 py-0.5 text-[11px]",
        md: "px-2.5 py-1 text-[11.5px]",
      },
    },
    defaultVariants: { variant: "mute", size: "md" },
  },
);

export interface ChipProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof chipVariants> {}

export function Chip({ className, variant, size, ...rest }: ChipProps) {
  return (
    <span className={cn(chipVariants({ variant, size }), className)} {...rest} />
  );
}
