"use client";

import { useState, useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import Modal from "@/components/Modal";
import ViewCanvas from "@/components/ViewCanvas";
import { Download, FileText, MoreVertical, Calendar, Hash, Printer, X, Settings2 } from "lucide-react";

import SummaryTab from "@/components/submissions/workbench/SummaryTab";
import PricingTab from "@/components/submissions/workbench/PricingTab";
import RiskTab from "@/components/submissions/workbench/RiskTab";
import LossTab from "@/components/submissions/workbench/LossTab";
import ExposureTab from "@/components/submissions/workbench/ExposureTab";
import ReferralTab from "@/components/submissions/workbench/ReferralTab";
import ModelVersionsTab from "@/components/submissions/workbench/ModelVersionsTab";

export default function WorkbenchView() {
  const { 
    activeMenu, 
    activeSubmission, 
    activeQuote,
    setHasPageActions,
    isPageActionsOpen,
    setPageActionsOpen 
  } = useDsiStore();
  
  // Tell the global layout to render the Ellipsis button while this view is active
  useEffect(() => {
    setHasPageActions(true);
    return () => setHasPageActions(false); // Cleanup when unmounting
  }, [setHasPageActions]);

  const [isActionsOpen, setIsActionsOpen] = useState(false);

  if (!activeSubmission) return null;

  // 1. RENDER TOP CONTEXT

  // 2. RENDER BOTTOM CONTEXT

  // 3. RENDER THE CORRECT TAB CONTENT
  const renderContent = () => {
    switch (activeMenu) {
      case "Summary":
        return <SummaryTab/>;
      case "Pricing Anatomy":
        return <PricingTab/>;
      case "Risk Assessment":
        return <RiskTab/>;
      case "Loss Assessment":
        return <LossTab/>;
      case "Exposure Assessment":
        return <ExposureTab/>;
      case "Referral Actions":
        return <ReferralTab/>;
      case "Model Versions":
        return <ModelVersionsTab/>;
      default:
        return <div className="p-4">Select a tab from the sidebar.</div>;
    }
  };

return (
    <>
      <ViewCanvas unstyledMain={true}>
        {renderContent()}
      </ViewCanvas>

      {/* 4. ENCAPSULATED PAGE ACTIONS MODAL */}
      <Modal 
        isOpen={isPageActionsOpen} 
        onClose={() => setPageActionsOpen(false)} 
        title="Submission Actions" 
        icon={Settings2}
      >
        <div className="space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider opacity-50 border-b border-dsi-outline/10 pb-2">
            Export & Report
          </h4>
          <div className="grid grid-cols-2 gap-3">
            <button className="flex flex-col items-center justify-center gap-2 p-6 bg-dsi-background/30 border border-dsi-outline/10 hover:border-dsi-selected hover:text-dsi-selected rounded-lg transition-all group">
              <FileText className="w-6 h-6 opacity-70 group-hover:opacity-100" />
              <span className="text-sm font-medium">Export to PDF</span>
            </button>
            <button className="flex flex-col items-center justify-center gap-2 p-6 bg-dsi-background/30 border border-dsi-outline/10 hover:border-dsi-selected hover:text-dsi-selected rounded-lg transition-all group">
              <Printer className="w-6 h-6 opacity-70 group-hover:opacity-100" />
              <span className="text-sm font-medium">Print Analysis</span>
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}