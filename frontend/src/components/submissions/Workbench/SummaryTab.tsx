"use client";

import "@/app/globals.css";
import { StandardCard, PopupCard } from "@/components/base/cards";

import { ShieldCheck, } from "lucide-react";

const dashboardConfig = [
  { id: '01', title: "Loss Metrics", icon: ShieldCheck, span: "col-span-1", content: <p>Block 1</p> },
  { id: '02', title: "Risk Overview", icon: ShieldCheck, span: "col-span-1", content: <p>Block 2</p> },
  { id: '03', title: "Exposure Analysis", icon: ShieldCheck, span: "col-span-1 md:col-span-2 lg:col-span-3", content: <p>Block 3</p> },
  { id: '04', title: "Network Authority", icon: ShieldCheck, span: "col-span-1", content: <p>Block 4</p> },
];

export default function DashboardLayout() {
  return (
    <div className="w-full no-scrollbar animate-in fade-in duration-500">
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-dsi-pad pt-dsi-pad">
        
        {dashboardConfig.map((section) => (
          <StandardCard 
            key={section.id} 
            title={section.title} 
            lucideIcon={section.icon}
            spanClass={section.span}
          >
            {section.content}
          </StandardCard>
        ))}

      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-dsi-pad pt-dsi-pad">
        
        {dashboardConfig.map((section) => (
          <PopupCard 
            key={section.id} 
            title={section.title} 
            spanClass={section.span}
          >
          </PopupCard>
        ))}

      </div>

    </div>

  );
}