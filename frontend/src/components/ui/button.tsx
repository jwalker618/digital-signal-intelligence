import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 font-semibold rounded-btn transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-info focus-visible:ring-offset-1 ring-offset-canvas disabled:opacity-50 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        primary: "bg-ink text-canvas hover:opacity-90",
        spot: "bg-spot text-white hover:opacity-90",
        info: "bg-info text-white hover:opacity-90",
        ghost: "bg-transparent text-ink border border-rule-strong hover:bg-surface-sunken",
        link: "bg-transparent text-info hover:underline px-0",
      },
      size: {
        sm: "h-8 px-3 text-[12px]",
        md: "h-10 px-4 text-[13px]",
        lg: "h-12 px-5 text-[14px]",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, type = "button", ...rest }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(buttonVariants({ variant, size }), className)}
      {...rest}
    />
  ),
);
Button.displayName = "Button";
