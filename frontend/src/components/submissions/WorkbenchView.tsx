"use client";

import { useDsiStore } from "@/store/dsiStore";
import ViewCanvas from "@/components/ViewCanvas";
import { Download, FileText, AlertCircle, Calendar, Clock, ShieldAlert, X } from "lucide-react";

import SummaryTab from "@/components/submissions/workbench/SummaryTab";
import ReferralTab from "@/components/submissions/workbench/ReferralTab";
import ModelVersionsTab from "@/components/submissions/workbench/ModelVersionsTab";
import AuditLogTab from "@/components/submissions/workbench/AuditLogTab";

export default function WorkbenchView() {
  const { activeMenu, activeSubmission } = useDsiStore();

  if (!activeSubmission) return null;

  // 1. DYNAMIC TOP CONTEXT (Title + Context Actions)
  const TopContext = activeSubmission ? (
    <div className="flex flex-col bg-dsi-background text-dsi-selected font-ibm shrink-0">
      
      {/* 1. TOP NAVIGATION BAR (Breadcrumbs & Global Controls) */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-dsi-outline/20">
        <h1 className="text-xl font-medium tracking-tight">
          Workbench <span className="opacity-40 mx-2">/</span> {activeMenu}
        </h1>
        <button 
          onClick={() => setActiveSubmission(null)}
          className="flex items-center gap-2 text-sm font-semibold opacity-60 hover:opacity-100 hover:bg-dsi-outline/10 px-3 py-1.5 rounded transition-all"
        >
          <X className="w-4 h-4" />
          Close Workspace
        </button>
      </div>

      {/* 2. CONTEXT TOOLBAR (Entity Details Left, Context Actions Right) */}
      <div className="flex items-center justify-between px-6 py-4 bg-dsi-contrast-background/30 border-b border-dsi-outline/10">
        
        {/* LEFT: Entity Details & Constraints */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-3">
            <span className="bg-dsi-selected/10 px-2 py-0.5 rounded text-xs font-mono text-dsi-selected">
              {activeSubmission.submission_id}
            </span>
            <span className="text-lg font-bold">{activeSubmission.entity_name}</span>
            
            {/* Referral Alert Badge (Only shows if there are reasons) */}
            {activeSubmission.referral_reasons && activeSubmission.referral_reasons.length > 0 && (
              <div className="flex items-center gap-1.5 bg-red-500/10 text-red-500 px-2.5 py-0.5 rounded text-xs font-semibold ml-2">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Referred</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-4 text-xs font-mono opacity-70">
            <span className="flex items-center gap-1.5 uppercase tracking-wider">
              <Clock className="w-3.5 h-3.5"/> 
              Coverage: {activeSubmission.coverage}
            </span>
            
            {/* Validity Dates (Only shows if valid_until exists) */}
            {activeSubmission.valid_until && (
              <span className="flex items-center gap-1.5 text-yellow-500 font-bold">
                <Calendar className="w-3.5 h-3.5"/> 
                Valid Until: {new Date(activeSubmission.valid_until).toLocaleDateString()}
              </span>
            )}

            {/* Expanded Referral Reasons */}
            {activeSubmission.referral_reasons && activeSubmission.referral_reasons.length > 0 && (
              <span className="text-red-400 truncate max-w-xl ml-2 border-l border-red-500/30 pl-4">
                {activeSubmission.referral_reasons.join(", ")}
              </span>
            )}
          </div>
        </div>

        {/* RIGHT: Context-Sensitive Buttons */}
        <div className="flex items-center gap-3">
          {activeMenu === "Referral Actions" && (
            <>
              <button className="px-4 py-2 bg-dsi-selected text-dsi-background text-sm font-bold rounded hover:opacity-90 transition-opacity">
                Approve
              </button>
              <button className="px-4 py-2 bg-dsi-outline/10 text-dsi-selected text-sm font-bold rounded hover:bg-dsi-outline/20 transition-colors">
                Decline
              </button>
            </>
          )}
        </div>
      </div>

    </div>
  ) : null;

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
        return <ModelVersionsTab/>;
      case "Audit Log":
        return <AuditLogTab/>;
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

