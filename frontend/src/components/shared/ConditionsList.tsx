"use client";

import { ShieldAlert } from "lucide-react";

const ACTION_COLORS: Record<string, { bg: string; text: string }> = {
  modifier:      { bg: 'bg-dsi-info/15', text: 'text-dsi-info' },
  referral:      { bg: 'bg-dsi-warning/15', text: 'text-dsi-warning' },
  refer:         { bg: 'bg-dsi-warning/15', text: 'text-dsi-warning' },
  tier_override: { bg: 'bg-dsi-negative/15', text: 'text-dsi-negative' },
  flag:          { bg: 'bg-dsi-muted/15', text: 'text-dsi-muted' },
  note:          { bg: 'bg-dsi-muted/15', text: 'text-dsi-muted' },
};

interface ConditionsListProps {
  conditions: any[];
  emptyMessage?: string;
}

export default function ConditionsList({ conditions, emptyMessage = "No conditions triggered." }: ConditionsListProps) {
  if (conditions.length === 0) {
    return (
      <div className="flex items-center justify-center h-24 opacity-50 text-sm italic">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {conditions.map((cond: any, idx: number) => {
        const actionKey = typeof cond.action === 'string' ? cond.action.toLowerCase() : (cond.action?.value || 'note');
        const colors = ACTION_COLORS[actionKey] || ACTION_COLORS.note;
        return (
          <div key={idx} className="flex items-center justify-between px-dsi-pad py-2 border-b border-dsi-outline/10 hover:bg-dsi-background/20 transition-colors">
            <div className="flex items-center gap-3 min-w-0">
              <ShieldAlert className={`w-3.5 h-3.5 shrink-0 ${colors.text}`} />
              <div className="min-w-0">
                <span className="text-sm block truncate">{cond.note || cond.source_name || 'Condition'}</span>
                <span className="text-[10px] opacity-40 block">{cond.source_type}: {cond.source_id}</span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0 ml-2">
              <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${colors.bg} ${colors.text}`}>
                {actionKey.replace('_', ' ')}
              </span>
              {cond.action_value != null && typeof cond.action_value === 'number' && (
                <span className="text-xs font-bold opacity-70 w-16 text-right">
                  {actionKey === 'modifier' ? `${(cond.action_value * 100).toFixed(0)}%` :
                   actionKey === 'tier_override' ? `→ T${cond.action_value}` :
                   cond.action_value}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export { ACTION_COLORS };
