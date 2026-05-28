import { icons, type LucideProps } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Render a lucide icon by string name. Saves us from importing every icon
 * at every callsite; nav configs and inventory tables can pass icon names
 * as data.
 */
interface IconProps extends Omit<LucideProps, "ref"> {
  name: string;
}

export function Icon({ name, className, size = 18, ...rest }: IconProps) {
  const Cmp = (icons as Record<string, React.ComponentType<LucideProps>>)[name];
  if (!Cmp) {
    if (process.env.NODE_ENV !== "production") {
      console.warn(`<Icon name="${name}" /> — no such lucide icon.`);
    }
    return null;
  }
  return <Cmp size={size} className={cn("shrink-0", className)} {...rest} />;
}
