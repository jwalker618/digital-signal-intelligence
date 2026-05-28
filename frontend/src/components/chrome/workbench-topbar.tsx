"use client";

import { Building2, Moon, Sun } from "lucide-react";
import { Chip } from "@/components/ui/chip";
import { cn } from "@/lib/utils";
import { useDsiStore } from "@/store/dsiStore";
import { useThemeStore } from "@/store/themeStore";
import { formatCurrency, formatText } from "@/lib/format";
import { portalToneToTone } from "@/lib/design-tokens";

/**
 * Workbench-specific top bar. Shows submission identity + decision/tier
 * chips so the underwriter always knows which submission they're looking
 * at as they tab between deep panes.
 */
export function WorkbenchTopbar({ activeTabLabel }: { activeTabLabel: string }) {
  const sub = useDsiStore((s) => s.activeSubmission);
  const ver = useDsiStore((s) => s.activeVersion);
  const isDark = useThemeStore((s) => s.isDark);
  const toggle = useThemeStore((s) => s.toggleDark);

  const composite = ver?.composite_score ?? sub?.composite_score ?? null;
  const decision = String(ver?.decision ?? sub?.decision ?? "").toLowerCase();
  const tier = ver?.final_tier ?? sub?.final_tier ?? null;
  const premium =
    ver?.final_premium ??
    sub?.final_premium ??
    sub?.recommended_premium ??
    null;

  const decisionTone =
    decision === "approve"
      ? "pos"
      : decision === "decline"
        ? "neg"
        : decision === "refer"
          ? "warn"
          : "mute";

  return (
    <header className="flex h-[68px] items-center justify-between border-b border-rule bg-canvas px-8">
      <div className="flex min-w-0 items-center gap-4">
        {sub?.entity_name && (
          <Building2 size={16} className="shrink-0 text-ink-mute" />
        )}
        <div className="min-w-0">
          <div className="flex items-baseline gap-2">
            <h1 className="truncate text-[15px] font-semibold text-ink">
              {sub?.entity_name ?? "Loading submission…"}
            </h1>
            {sub?.coverage && (
              <span className="truncate text-[13px] text-ink-soft">
                · {sub.coverage}
              </span>
            )}
          </div>
          <div className="mt-0.5 flex items-center gap-2 text-[11.5px] text-ink-mute">
            <span className="font-mono">{sub?.submission_code ?? "—"}</span>
            <span>/</span>
            <span className="font-semibold text-ink-soft">{activeTabLabel}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {composite != null && (
          <div className="text-right">
            <span className="block text-[11px] uppercase tracking-[0.08em] text-ink-mute">
              Score
            </span>
            <span className="font-semibold tabular-nums text-ink">
              {Number(composite).toFixed(0)}
            </span>
          </div>
        )}
        {tier != null && (
          <Chip variant="info" size="sm">
            Tier {tier}
          </Chip>
        )}
        {decision && (
          <Chip variant={decisionTone} size="sm">
            {formatText(decision, "capitalize")}
          </Chip>
        )}
        {premium != null && (
          <div className="text-right">
            <span className="block text-[11px] uppercase tracking-[0.08em] text-ink-mute">
              Premium
            </span>
            <span className="font-semibold tabular-nums text-ink">
              {formatCurrency(Number(premium))}
            </span>
          </div>
        )}
        <button
          type="button"
          onClick={toggle}
          aria-label="Toggle dark mode"
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-full text-ink-soft hover:bg-surface-sunken",
          )}
        >
          {isDark ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  );
}
