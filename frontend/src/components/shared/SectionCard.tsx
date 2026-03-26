"use client";

import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

interface SectionCardProps {
  icon: LucideIcon;
  title: string;
  headerRight?: ReactNode;
  children: ReactNode;
  iconClassName?: string;
}

export default function SectionCard({ icon: Icon, title, headerRight, children, iconClassName }: SectionCardProps) {
  return (
    <div className="flex flex-col pt-2 pb-2">
      <div className="flex justify-between items-center gap-dsi-pad rounded-t-xl border-b-1 border-dsi-outline/50 overflow-x-hidden whitespace-nowrap border-collapse bg-dsi-analysis/60 pl-dsi-pad pr-dsi-pad pt-2 pb-2">
        <div className="flex items-center gap-dsi-pad">
          <Icon className={`icon ${iconClassName || ''}`} />
          <span className="text-sm">{title}</span>
        </div>
        {headerRight}
      </div>
      <div className="flex flex-col flex-1 border-b-3 border-dsi-contrast-background overflow-x-hidden border-collapse rounded-b-xl bg-dsi-analysis shadow-sm">
        {children}
      </div>
    </div>
  );
}
