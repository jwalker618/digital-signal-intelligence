"use client";

import { useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useDsiStore } from "@/store/dsiStore";
import { Activity, GitGraph, ShieldAlert, Loader2 } from "lucide-react";

// Component Imports
import WorldModelGraph from "@/components/world-model/GraphExplorer";
import RetuningEngine from "@/components/scenarios/RetuningEngine";
import ReferralQueue from "@/components/referrals/Queue";
import AuditTrail from "@/components/audit/Trail";
import PortfolioAnalytics from "@/components/portfolio/Analytics";

export default function DSIDashboard() {
  const { 
    submissions, 
    activeSubmission, 
    isLoading, 
    error, 
    fetchSubmissions, 
    setActiveSubmission,
    activeMenu // Pulled from the store, controlled by the Sidebar
  } = useDsiStore();

  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  if (error) return <div className="p-6 text-red-500 h-full">Backend Error: {error}</div>;

  // Safely extract nested data for the Full Pipeline view
  const entityName = activeSubmission?.entity_name || "Pending...";
  const quote = activeSubmission?.quotes?.[0] || {};
  const modelVersion = activeSubmission?.model_versions?.[0] || activeSubmission?.model_version || {};
  
  const premium = quote.recommended_premium || modelVersion.final_premium || 0;
  const decision = quote.decision || modelVersion.decision || activeSubmission?.status || "pending";
  const tier = quote.tier || modelVersion.final_tier || "?";
  const signals = modelVersion.signal_conditions || [];

  // ==========================================================================
  // VIEW 1: REFERRAL PIPELINE (Inbox)
  // ==========================================================================
  if (activeMenu === "Referral Pipeline") {
    return <ReferralQueue />;
  }

  // ==========================================================================
  // VIEW 2: PERFORMANCE METRICS (Analytics)
  // ==========================================================================
  if (activeMenu === "Performance Metrics") {
    return <PortfolioAnalytics />;
  }

  // ==========================================================================
  // VIEW 3: FULL PIPELINE (The core Workbench with inner tabs)
  // ==========================================================================
  if (activeMenu === "Full Pipeline") {
    return (
      <Tabs defaultValue="workbench" className="flex-grow flex flex-col h-full">
        <TabsList className="grid w-full max-w-md grid-cols-3 mb-6 bg-transparent border border-dsi-outline/20">
          <TabsTrigger value="workbench" className="data-[state=active]:bg-dsi-outline/20 data-[state=active]:text-dsi-sub-text text-dsi-sub-text/70"><Activity className="w-4 h-4 mr-2"/> Details</TabsTrigger>
          <TabsTrigger value="world-model" className="data-[state=active]:bg-dsi-outline/20 data-[state=active]:text-dsi-sub-text text-dsi-sub-text/70"><GitGraph className="w-4 h-4 mr-2"/> World Model</TabsTrigger>
          <TabsTrigger value="retuning" className="data-[state=active]:bg-dsi-outline/20 data-[state=active]:text-dsi-sub-text text-dsi-sub-text/70"><ShieldAlert className="w-4 h-4 mr-2"/> Retuning</TabsTrigger>
        </TabsList>

        <TabsContent value="workbench" className="flex-grow flex flex-col md:flex-row gap-6 h-full">
          {/* Left Side: Pipeline List */}
          <div className="w-full md:w-1/3 flex flex-col gap-4">
            <Card className="bg-dsi-sidebar-bg border-dsi-outline/20 text-dsi-sidebar-text flex-grow">
              <CardHeader><CardTitle className="text-dsi-outline">Active Pipeline</CardTitle></CardHeader>
              <CardContent className="flex flex-col gap-2">
                {isLoading && submissions.length === 0 ? <Loader2 className="animate-spin text-dsi-outline mx-auto" /> : 
                 submissions.length === 0 ? <p className="text-center opacity-70">No submissions in pipeline.</p> : 
                  submissions.map((sub: any) => {
                    const id = sub.id || sub.submission_id;
                    const nestedQuote = sub.quotes?.[0] || {};
                    const nestedMv = sub.model_versions?.[0] || {};
                    const displayTier = nestedQuote.tier || nestedMv.final_tier || '?';
                    const displayDecision = nestedQuote.decision || nestedMv.decision || sub.status;

                    return (
                      <div key={id} onClick={() => setActiveSubmission(id)}
                        className={`p-3 rounded cursor-pointer border transition-colors ${activeSubmission?.id === id ? 'border-dsi-outline bg-dsi-outline/10 text-dsi-sidebar-active' : 'border-transparent hover:bg-dsi-outline/5'}`}>
                        <div className="flex justify-between items-center">
                          <span className="font-semibold">{sub.entity_name}</span>
                          <Badge variant="outline" className={`${displayDecision === 'approve' ? 'border-green-500 text-green-500' : displayDecision === 'refer' ? 'border-yellow-500 text-yellow-500' : 'border-red-500 text-red-500'}`}>
                            Tier {displayTier}
                          </Badge>
                        </div>
                      </div>
                    )
                  })
                }
              </CardContent>
            </Card>
          </div>

          {/* Right Side: Details Pane */}
          <div className="w-full md:w-2/3 flex flex-col gap-4">
            {activeSubmission && (
              <Card className="bg-dsi-sidebar-bg border-dsi-outline/20 text-dsi-sidebar-text h-full">
                <CardHeader>
                  <CardTitle className="flex justify-between items-center text-dsi-outline">
                    <span>Signal Cascade: {entityName}</span>
                    <span className="text-xl font-mono">Premium: ${premium.toLocaleString()}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="p-4 bg-dsi-main-bg/50 rounded border border-dsi-outline/10 mb-4">
                    <h3 className="text-sm uppercase tracking-wider mb-2 opacity-70">Decision Engine</h3>
                    <span className={`text-lg font-bold uppercase ${decision === 'approve' ? 'text-green-500' : 'text-yellow-500'}`}>
                      {decision}
                    </span>
                  </div>

                  <h3 className="text-lg font-semibold mb-3 border-b border-dsi-outline/20 pb-2">Extracted Signals</h3>
                  <ul className="space-y-3">
                    {signals.length === 0 ? <p className="italic opacity-70">No signals attached.</p> :
                      (typeof signals === 'string' ? JSON.parse(signals) : signals).map((sig: any, i: number) => (
                       <li key={i} className="flex justify-between bg-dsi-main-bg/30 p-3 rounded border border-dsi-outline/5">
                         <span>{sig.note}</span>
                         <Badge variant="outline" className="border-dsi-outline/50">{sig.applied_modifier}</Badge>
                       </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="world-model" className="flex-grow h-full">
          <WorldModelGraph submission={activeSubmission} />
        </TabsContent>

        <TabsContent value="retuning" className="flex-grow h-full">
          <RetuningEngine submission={activeSubmission} />
        </TabsContent>
      </Tabs>
    );
  }

  // ==========================================================================
  // VIEW 4: FALLBACK / AUDIT TRAIL
  // ==========================================================================
  return <AuditTrail />;
}