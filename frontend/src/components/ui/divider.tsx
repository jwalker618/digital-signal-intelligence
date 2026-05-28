import { cn } from "@/lib/utils";

export function Divider({
  orientation = "horizontal",
  className,
}: {
  orientation?: "horizontal" | "vertical";
  className?: string;
}) {
  return (
    <div
      role="separator"
      className={cn(
        orientation === "horizontal"
          ? "h-px w-full bg-rule"
          : "w-px self-stretch bg-rule",
        className,
      )}
    />
  );
}
