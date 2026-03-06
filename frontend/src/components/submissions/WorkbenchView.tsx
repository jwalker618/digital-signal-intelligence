"use client";

import { useDsiStore } from "@/store/dsiStore";
import ViewCanvas from "@/components/ViewCanvas";
import { Download, FileText } from "lucide-react";

import SummaryTab from "@/components/submissions/Workbench/SummaryTab";
import ReferralTab from "@/components/submissions/Workbench/ReferralTab";

export default function WorkbenchView() {
  const { activeMenu, activeSubmission } = useDsiStore();

  if (!activeSubmission) return null;

  // 1. DYNAMIC TOP CONTEXT (Title + Context Actions)
  const TopContext = (
    <div className="w-full h-full flex flex-col justify-between px-2">
      <h2 className="pt-dsi-pad flex relative">
        <span className="">/</span> 
        {activeMenu}
      </h2>

      {/* Context-Sensitive Actions */}
      <div className="hover:text-dsi-selected">
        {activeMenu === "Summary" && (
          <button className="flex gap-2">
            <FileText className="icon" /> export pdf
          </button>
        )}
        {activeMenu === "Audit Log" && (
          <button className="flex gap-2">
            <Download className="icon" /> export csv
          </button>
        )}
      </div>

    </div>
  );

  // 2. DYNAMIC BOTTOM CONTEXT (Creation Date)
  const BottomContext = (
    <div className="w-full h-full flex justify-between px-2">
      <p className="pt-dsi-pad flex relative">
        Submission Created: {new Date(activeSubmission.created_at).toLocaleString()}
      </p>
      <p className="pt-dsi-pad flex relative">
        Submission Code: {activeSubmission.submission_code}
      </p>
    </div>
  );

  // 3. RENDER THE CORRECT TAB CONTENT
  const renderContent = () => {
    switch (activeMenu) {
      case "Summary":
        return <SummaryTab/>;
      case "Referral Actions":
        return <ReferralTab/>;
      case "Model Versions":
        return <div className="p-4">Version History Timeline goes here...</div>;
      case "Audit Log":
        return <div className="p-4">Chronological Ledger goes here...</div>;
      default:
        return <div className="p-4">Select a tab from the sidebar.</div>;
    }
  };

  return (
    <ViewCanvas topContext={TopContext} bottomContext={BottomContext}>
      {renderContent()}
    </ViewCanvas>
  );
}

