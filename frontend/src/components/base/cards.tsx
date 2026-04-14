/**
 * Shared card stylings
 */

import "@/app/globals.css";
import { LucideIcon, ArrowUpRight } from "lucide-react";

/** Used for risk submission cards */
const RISKDECISION_STYLE: Record<string, { bg: string; }> = {
  approve: { bg: 'bg-dsi-approve', },
  refer:   { bg: 'bg-dsi-refer',   },
  decline: { bg: 'bg-dsi-decline', },
  pending: { bg: 'bg-dsi-muted',   },
};


interface AnalysisCardProps {
  lucideIcon: LucideIcon; 
  title: string;
  children: React.ReactNode;
  spanClass?: string; 
}

export const StandardCard = ({ 
  lucideIcon: Icon, 
  title, 
  children, 
  spanClass = "col-span-1" 
}: AnalysisCardProps) => {
  return (
    <div className={`flex flex-col h-full ${spanClass}`}>
      
      <div className="dsi-section-header">
        <Icon className="icon"/> 
        <span className="text-sm">{title}</span>
      </div>
      
      <div className="dsi-section-analysis">
        {children}
      </div>

    </div>
  );
};

export const PopupCard = ({ 
  title, 
  spanClass = "col-span-1" 
}: AnalysisCardProps) => {
  return (
    <div className={`flex flex-col h-full ${spanClass}`}>
 
      <div className="dsi-popup-header">
        <span className="text-xs content-center">Expand</span>
        <ArrowUpRight className="icon"/>
      </div>
      
      <div className="dsi-section-analysis font-bold">{title}</div>

    </div>
  );
};
