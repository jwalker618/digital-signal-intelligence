/**
 * CardGrid — the dashboard responsive grid wrapper.
 *
 * Encapsulates the `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3
 * gap-dsi-pad pt-dsi-pad` pattern used across the workbench. Consumers pass
 * their rendered cards as children; `cols` overrides the breakpoint count if
 * needed.
 */

import "@/app/globals.css";

interface CardGridProps {
  children: React.ReactNode;
  /** Tailwind grid-cols-* classes (full classes, space-separated). */
  cols?: string;
  /** Extra classes appended to the grid. */
  className?: string;
}

export default function CardGrid({
  children,
  cols = "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
  className = "",
}: CardGridProps) {
  return (
    <div className={`grid ${cols} gap-dsi-pad pt-dsi-pad ${className}`}>
      {children}
    </div>
  );
}
