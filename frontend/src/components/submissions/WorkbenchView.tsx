"use client";

import { useState } from "react";
import { useDsiStore } from "@/store/dsiStore";
import ViewCanvas from "@/components/ViewCanvas";
import { Download, FileText, MoreVertical, Calendar, Hash } from "lucide-react";

import SummaryTab from "@/components/submissions/workbench/SummaryTab";
import PricingTab from "@/components/submissions/workbench/PricingTab";
import RiskTab from "@/components/submissions/workbench/RiskTab";
import LossTab from "@/components/submissions/workbench/LossTab";
import ExposureTab from "@/components/submissions/workbench/ExposureTab";
import ReferralTab from "@/components/submissions/workbench/ReferralTab";
import ModelVersionsTab from "@/components/submissions/workbench/ModelVersionsTab";

export default function WorkbenchView() {
  const { activeMenu, activeSubmission, activeQuote } = useDsiStore();
  const [isActionsOpen, setIsActionsOpen] = useState(false);

  if (!activeSubmission) return null;

  // 1. DYNAMIC TOP CONTEXT (Title, Status + Context Actions)
  const TopContext = (
    <div className="w-full h-full flex justify-between pt-2">
      
      {/* LEFT: Title & Status Info */}
      <div className="flex flex-col">
        <h2 className="flex gap-3">
          <span className="">/</span> 
          {activeMenu}
        </h2>
        
        {/* Dynamic Quote Analysis (Stacked under the title) */}
        {activeQuote && (
          <div className="flex items-center gap-1 pt-4">
            <span>Status: </span>
            <span className="uppercase font-bold">
              {activeQuote.status}
            </span>

            {/* Show Validity Dates if DRAFT OR READY (TO BE APPROVED / DECLINED) */}
            {(activeQuote.status === 'draft' || activeQuote.status === 'ready') && (
              <span className="flex items-center gap-6 pl-6">
                <span>Valid From: {new Date(activeQuote.valid_from).toLocaleDateString()}</span>
                <span>Valid Until: {activeQuote.valid_until ? new Date(activeQuote.valid_until).toLocaleDateString() : 'TBD'}</span>
              </span>
            )}

            {/* Show Binding info if BOUND */}
            {activeQuote.status === 'bound' && (
              <span className="flex items-center gap-6 pl-6">
                  <span>Bound Date: {activeQuote.bound_at ? new Date(activeQuote.bound_at).toLocaleDateString() : 'N/A'}</span>
                  <span>Policy Reference: {activeQuote.policy_number || 'Pending'}</span>
              </span>
            )}
          </div>
        )}
      </div>

      {/* RIGHT: Expandable Context Actions */}
      <div className="flex items-start ">

        <div className="flex pt-2">

          {isActionsOpen && (
            <div className="flex gap-2 animate-in slide-in-from-right-4 fade-in duration-200">
              {activeMenu === "Summary" && (
                <button className="flex items-center gap-2 hover:text-dsi-selected">
                  <FileText className="icon" /> Export PDF
                </button>
              )}
              {activeMenu === "Audit Log" && (
                <button className="flex items-center gap-2 hover:text-dsi-selected">
                  <Download className="icon" /> Export CSV
                </button>
              )}
              {activeMenu !== "Summary" && activeMenu !== "Audit Log" && (
                <div className="flex items-center gap-2 text-xs italic">
                  No actions available
                </div>
              )}
            </div>
          )}

          <button
            onClick={() => setIsActionsOpen(!isActionsOpen)}
            className={`${
              isActionsOpen
                ? "ml-3 pl-dsi-pad border-l-3 border-dsi-outline/20 text-dsi-selected hover:text-dsi-contrast-background"
                : "hover:text-dsi-selected"
            }`}
            title="Context Actions"
          >
            <MoreVertical className="icon" />
          </button>
        </div>
      </div>
    </div>
  );

  // 2. DYNAMIC BOTTOM CONTEXT (Creation Date & Identifiers)
  const BottomContext = (
    <div className="w-full h-full flex justify-between pt-2">
      
      {/* LEFT: Creation Date */}
      <div className="flex">
        Submission Created: {new Date(activeSubmission.created_at).toLocaleString()}
      </div>
      
      {/* RIGHT: Stacked Reference Codes */}
      <div className="flex text-right gap-6">
        <span>Submission Code: {activeSubmission.submission_code}</span>
        <span>||</span>
        <span>Quote Code: {activeQuote?.quote_code || 'Pending'}</span>
      </div>

    </div>
  );

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
    <ViewCanvas topContext={TopContext} bottomContext={BottomContext} unstyledMain={true}>
      {renderContent()}
    </ViewCanvas>
  );
}