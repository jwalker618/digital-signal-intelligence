import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * Small uppercase label. Sits above hero numbers and card titles.
 */
export function Eyebrow({
  className,
  ...rest
}: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "block text-[10.5px] font-semibold uppercase tracking-[0.12em] text-ink-mute",
        className,
      )}
      {...rest}
    />
  );
}

const numVariants = cva("font-semibold text-ink tabular-nums", {
  variants: {
    size: {
      sm: "text-lg leading-none",
      md: "text-[28px] leading-none -tracking-[0.01em]",
      lg: "text-4xl leading-none -tracking-[0.01em]",
      xl: "text-[56px] leading-none -tracking-[0.02em]",
    },
  },
  defaultVariants: { size: "md" },
});

export interface NumProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof numVariants> {}

export function NumDisplay({ className, size, ...rest }: NumProps) {
  return <span className={cn(numVariants({ size }), className)} {...rest} />;
}

/** Mid-weight body text. */
export function Body({
  className,
  ...rest
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-[13.5px] text-ink-soft", className)} {...rest} />
  );
}

/** Small caption text. */
export function Caption({
  className,
  ...rest
}: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className={cn("text-xs text-ink-soft", className)} {...rest} />
  );
}

/** Smallest meta text — secondary metadata, helper text. */
export function Micro({
  className,
  ...rest
}: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className={cn("text-[11px] text-ink-mute", className)} {...rest} />
  );
}
