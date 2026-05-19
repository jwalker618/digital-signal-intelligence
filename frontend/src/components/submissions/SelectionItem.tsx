"use client";

import { useState, useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import Modal from "@/components/base/modal";
import ViewCanvas from "@/components/ViewCanvas";
import {  FileText, Printer, Settings2 } from "lucide-react";

import SummaryTab from "@/components/submissions/content/summary/SummaryTab";

// Commercial
import CommercialTermsTab from "@/components/submissions/content/commercialterms/CommercialTermsTab";
import PremiumAssemblyTab from "@/components/submissions/content/commercialterms/PremiumAssemblyTab";
import DistributionTab from "@/components/submissions/content/commercialterms/DistributionTab";

// Risk Terms
import DeductibleStructureTab from "@/components/submissions/content/riskterms/DeductibleStructureTab";
import CoverageTermsTab from "@/components/submissions/content/riskterms/CoverageTermsTab";
import SIRWaitingPeriodsTab from "@/components/submissions/content/riskterms/SIRWaitingPeriodsTab";
import AggregateReinstatementTab from "@/components/submissions/content/riskterms/AggregateReinstatementTab";

// Technical Analysis
import PricingTab from "@/components/submissions/content/technicalanalysis/PricingTab";
import RiskTab from "@/components/submissions/content/technicalanalysis/RiskTab";
import LossTab from "@/components/submissions/content/technicalanalysis/LossTab";
import ExposureTab from "@/components/submissions/content/technicalanalysis/ExposureTab";
import ReferralTab from "@/components/submissions/content/technicalanalysis/ReferralTab";
import ScenarioTab from "@/components/submissions/content/technicalanalysis/ScenarioTab";
import ModelVersionsTab from "@/components/submissions/content/technicalanalysis/ModelVersionsTab";

export default function SelectionItem() {
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
      
      case "Summary": return <SummaryTab/>;
      
      // Commercial
      case "Terms Overview": return <CommercialTermsTab/>;
      case "Premium Assembly": return <PremiumAssemblyTab/>;
      case "Distribution": return <DistributionTab/>;
      
      // Risk Terms
      case "Deductible Structure": return <DeductibleStructureTab/>;
      case "Coverage Terms": return <CoverageTermsTab/>;
      case "SIR & Waiting Periods": return <SIRWaitingPeriodsTab/>;
      case "Aggregate & Reinstatement": return <AggregateReinstatementTab/>;
      
      // Technical
      case "Pricing Anatomy": return <PricingTab/>;
      case "Risk Assessment": return <RiskTab/>;
      case "Loss Assessment": return <LossTab/>;
      case "Exposure Assessment": return <ExposureTab/>;
      case "Referral Actions": return <ReferralTab/>;
      case "Scenarios": return <ScenarioTab/>;
      case "Model Versions": return <ModelVersionsTab/>;
      
      default: return <div className="p-4">Select a tab from the sidebar.</div>;
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
        <div className="grid grid-cols-2 gap-2">
          
          <div className="group">
            <button className="generate-light-modalbutton group-hover:bg-generate-light-input group-hover:border border-generate-text-outline group-hover:text-generate-text-input">
              <FileText className="generate-app-icon group-hover:bg-generate-light-input group-hover:text-generate-text-input" />
              <span className="text-sm">Export to PDF</span>
            </button>
          </div>

          <div className="group">
            <button className="generate-light-modalbutton group-hover:bg-generate-light-input group-hover:border border-generate-text-outline group-hover:text-generate-text-input">
              <Printer className="generate-app-icon group-hover:bg-generate-light-input group-hover:text-generate-text-input" />
              <span className="text-sm">Print Analysis</span>
            </button>
          </div>
        </div>

      </Modal>
    </>
  );
}