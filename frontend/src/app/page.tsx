"use client";

import { useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useDsiStore } from "@/store/dsiStore";
import { ShieldAlert, Activity, GitGraph, Loader2 } from "lucide-react";

export default function DSIDashboard() {
  const { submissions, activeSubmission, isLoading, error, fetchSubmissions, setActiveSubmission } = useDsiStore();

  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  if (error) return <div className="p-6 text-red-500 bg-slate-950 h-screen">Backend Error: {error}</div>;

  // Safely extract the nested quote/model_version from the active submission
  const entityName = activeSubmission?.entity_name || "Pending...";
  const quote = activeSubmission?.quotes?.[0] || {};
  const modelVersion = activeSubmission?.model_versions?.[0] || activeSubmission?.model_version || {};
  
  const premium = quote.recommended_premium || modelVersion.final_premium || 0;
  const decision = quote.decision || modelVersion.decision || activeSubmission?.status || "pending";
  const tier = quote.tier || modelVersion.final_tier || "?";
  const signals = modelVersion.signal_conditions || [];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-6 flex flex-col">
      <header className="mb-6 flex justify-between items-center border-b border-slate-800 pb-4">
        <h1 className="text-3xl font-bold tracking-tight text-blue-500">DSI Platform</h1>
        <Badge variant="outline" className="text-slate-400 border-slate-700">Production Build</Badge>
      </header>

      <Tabs defaultValue="workbench" className="flex-grow flex flex-col">
        <TabsList className="grid w-full max-w-md grid-cols-3 mb-6 bg-slate-900">
          <TabsTrigger value="workbench"><Activity className="w-4 h-4 mr-2"/> Workbench</TabsTrigger>
          <TabsTrigger value="world-model"><GitGraph className="w-4 h-4 mr-2"/> World Model</TabsTrigger>
          <TabsTrigger value="retuning"><ShieldAlert className="w-4 h-4 mr-2"/> Retuning</TabsTrigger>
        </TabsList>

        <TabsContent value="workbench" className="flex-grow flex flex-col md:flex-row gap-6">
          
          <div className="w-full md:w-1/3 flex flex-col gap-4">
            <Card className="bg-slate-900 border-slate-800 text-white flex-grow">
              <CardHeader><CardTitle>Active Pipeline</CardTitle></CardHeader>
              <CardContent className="flex flex-col gap-2">
                {isLoading && submissions.length === 0 ? <Loader2 className="animate-spin text-blue-500 mx-auto" /> : 
                 submissions.length === 0 ? <p className="text-slate-500 text-center">No submissions in pipeline.</p> : 
                  submissions.map((sub: any) => {
                    const id = sub.id || sub.submission_id;
                    const nestedQuote = sub.quotes?.[0] || {};
                    const nestedMv = sub.model_versions?.[0] || {};
                    const displayTier = nestedQuote.tier || nestedMv.final_tier || '?';
                    const displayDecision = nestedQuote.decision || nestedMv.decision || sub.status;

                    return (
                      <div key={id} onClick={() => setActiveSubmission(id)}
                        className={`p-3 rounded cursor-pointer border ${activeSubmission?.id === id ? 'border-blue-500 bg-slate-800' : 'border-slate-800 hover:bg-slate-800/50'}`}>
                        <div className="flex justify-between items-center">
                          <span className="font-semibold">{sub.entity_name}</span>
                          <Badge variant={displayDecision === 'approve' ? 'default' : displayDecision === 'refer' ? 'secondary' : 'destructive'}>
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

          <div className="w-full md:w-2/3 flex flex-col gap-4">
            {activeSubmission && (
              <Card className="bg-slate-900 border-slate-800 text-white h-full">
                <CardHeader>
                  <CardTitle className="flex justify-between items-center">
                    <span>Signal Cascade: {entityName}</span>
                    <span className="text-xl text-green-400 font-mono">Premium: ${premium.toLocaleString()}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="p-4 bg-slate-950 rounded border border-slate-800 mb-4">
                    <h3 className="text-sm text-slate-400 uppercase tracking-wider mb-2">Decision Engine</h3>
                    <span className={`text-lg font-bold uppercase ${decision === 'approve' ? 'text-green-500' : 'text-yellow-500'}`}>
                      {decision}
                    </span>
                  </div>

                  <h3 className="text-lg font-semibold mb-3 border-b border-slate-800 pb-2">Extracted Signals</h3>
                  <ul className="space-y-3">
                    {signals.length === 0 ? <p className="text-slate-500 italic">No signals attached.</p> :
                      (typeof signals === 'string' ? JSON.parse(signals) : signals).map((sig: any, i: number) => (
                       <li key={i} className="flex justify-between bg-slate-800/50 p-3 rounded">
                         <span className="text-slate-200">{sig.note}</span>
                         <Badge variant="outline">{sig.applied_modifier}</Badge>
                       </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}