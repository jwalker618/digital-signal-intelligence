import { Sparkles } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";

interface ComingSoonProps {
  /** Breadcrumb final segment / page title. */
  title: string;
  /** Sentence describing what this page will do. */
  description: string;
  /** Persona label for the breadcrumb root. */
  persona?: "Client Portal" | "Broker Portal" | "Admin Console";
  /** Entity badge in the topbar. */
  entity?: string;
  /** Optional list of feature bullets the page will ship with. */
  shipsWith?: string[];
}

/**
 * Placeholder for routes whose UI hasn't been ported yet. Shows the topbar
 * (so chrome looks complete) and a single info card explaining what's
 * coming. The card uses `info` variant so it visually reads as
 * "informative", not "broken".
 */
export function ComingSoon({
  title,
  description,
  persona = "Client Portal",
  entity,
  shipsWith,
}: ComingSoonProps) {
  return (
    <>
      <Topbar crumbs={[persona, title]} entity={entity} />
      <div className="flex flex-1 items-start justify-center overflow-y-auto px-9 py-12">
        <Card variant="info" pad="lg" className="max-w-2xl space-y-5">
          <div className="flex items-center gap-2 text-info">
            <Sparkles size={16} />
            <Eyebrow className="text-info">Up next</Eyebrow>
          </div>
          <div>
            <h1 className="font-display text-[28px] font-semibold leading-tight text-ink">
              {title}
            </h1>
            <Body className="mt-2">{description}</Body>
          </div>
          {shipsWith && shipsWith.length > 0 && (
            <ul className="space-y-1.5 border-t border-info/30 pt-4">
              {shipsWith.map((b) => (
                <li key={b} className="flex items-start gap-2 text-[13px] text-ink">
                  <span className="mt-2 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-info" />
                  {b}
                </li>
              ))}
            </ul>
          )}
          <Micro className="block">
            This route is wired into the navigation; the canonical UI ships in
            the next pass.
          </Micro>
        </Card>
      </div>
    </>
  );
}
