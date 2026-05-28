import { cn } from "@/lib/utils";

interface AvatarProps {
  /** Initials, max 2 chars. */
  initials: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const SIZES = {
  sm: "h-7 w-7 text-[11px]",
  md: "h-8 w-8 text-[13px]",
  lg: "h-10 w-10 text-sm",
};

export function Avatar({ initials, size = "md", className }: AvatarProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full bg-ink font-semibold text-canvas border border-rule-strong dark:border-0 dark:bg-info",
        SIZES[size],
        className,
      )}
    >
      {initials.slice(0, 2).toUpperCase()}
    </div>
  );
}
