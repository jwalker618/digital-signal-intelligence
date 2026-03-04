"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, Play, ArrowRight } from "lucide-react";

export default function RetuningEngine({ submission }: { submission: any }) {
  const [signals, setSignals] = useState<any[]>([]);
  const [originalPremium, setOriginalPremium] = useState(0);
  const [simulatedPremium, setSimulatedPremium] = useState(0);
  const [isSimulating, setIsSimulating] = useState(false);

  // Load the initial data when the submission changes
  useEffect(() => {
    if (!submission) return;
    
    const quote = submission.quotes?.[0] || {};
    const mv = submission.model_versions?.[0] || {};
    const basePremium = quote.recommended_premium || mv.final_premium || 100000;
    
    setOriginalPremium(basePremium);
    setSimulatedPremium(basePremium);

    const rawSignals = mv.signal_conditions || [];
    const parsed = typeof rawSignals === 'string' ? JSON.parse(rawSignals) : rawSignals;
    
    // Ensure all signals have a baseline modifier we can tweak
    const initializedSignals = parsed.map((sig: any) => ({
      ...sig,
      applied_modifier: sig.applied_modifier || 0,
      original_modifier: sig.applied_modifier || 0
    }));
    
    setSignals(initializedSignals);
  }, [submission]);

  // Handle slider changes
  const handleModifierChange = (index: number, newValue: number[]) => {
    const updated = [...signals];
    updated[index].applied_modifier = newValue[0];
    setSignals(updated);
  };

  // Run a local simulation of the premium based on the new weights
  const runSimulation = () => {
    setIsSimulating(true);
    
    setTimeout(() => {
      // Calculate delta: (New Modifier - Old Modifier) * Base Premium weight
      // This is a simplified frontend simulation for the UI
      let multiplier = 1.0;
      signals.forEach(sig => {
        const diff = sig.applied_modifier - sig.original_modifier;
        multiplier += diff; // e.g., if we add 0.05 penalty, multiplier goes up 5%
      });

      setSimulatedPremium(Math.max(0, originalPremium * multiplier));
      setIsSimulating(false);
    }, 600); // Artificial delay to simulate "engine processing"
  };

  if (!submission) {
    return <div className="flex h-full items-center justify-center text-slate-500">Select an entity to retune its model.</div>;
  }

  const delta = simulatedPremium - originalPremium;

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-full min-h-[600px]">
      
      {/* Left Panel: Signal Weight Controls */}
      <Card className="flex-grow lg:w-2/3 bg-slate-900 border-slate-800 text-white flex flex-col">
        <CardHeader className="border-b border-slate-800 pb-4">
          <CardTitle className="flex justify-between items-center">
            <span>Signal Weight Calibration</span>
            <Button variant="outline" size="sm" onClick={() => setSignals(signals.map(s => ({...s, applied_modifier: s.original_modifier})))} className="text-slate-300 border-slate-700 hover:bg-slate-800">
              <RefreshCw className="w-4 h-4 mr-2" /> Reset Weights
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6 overflow-y-auto flex-grow space-y-6">
          {signals.length === 0 ? (
             <p className="text-slate-500 italic">No tweakable signals found in this model version.</p>
          ) : (
            signals.map((sig, idx) => (
              <div key={idx} className="space-y-3 bg-slate-950 p-4 rounded-lg border border-slate-800">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-slate-200">{sig.note || sig.signal_id || "Unknown Signal"}</span>
                  <Badge variant="outline" className={sig.applied_modifier > 0 ? 'text-red-400 border-red-400' : sig.applied_modifier < 0 ? 'text-green-400 border-green-400' : 'text-slate-400 border-slate-700'}>
                    {(sig.applied_modifier > 0 ? '+' : '') + (sig.applied_modifier * 100).toFixed(1)}% Impact
                  </Badge>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-slate-500 w-12 text-right">-20%</span>
                  <Slider 
                    value={[sig.applied_modifier]} 
                    min={-0.20} 
                    max={0.20} 
                    step={0.01}
                    onValueChange={(val) => handleModifierChange(idx, val)}
                    className="flex-grow"
                  />
                  <span className="text-xs text-slate-500 w-12">-&gt; +20%</span>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* Right Panel: Simulation Results */}
      <Card className="lg:w-1/3 bg-slate-900 border-slate-800 text-white flex flex-col">
        <CardHeader className="border-b border-slate-800 pb-4">
          <CardTitle>Impact Analysis</CardTitle>
        </CardHeader>
        <CardContent className="pt-6 flex flex-col gap-6 flex-grow justify-between">
          
          <div className="space-y-6">
            <div className="bg-slate-950 p-4 rounded border border-slate-800">
              <span className="text-sm text-slate-400 uppercase tracking-wider block mb-1">Current Premium</span>
              <span className="text-2xl font-mono text-slate-200">${originalPremium.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
            </div>

            <div className="flex justify-center">
              <ArrowRight className="text-slate-600 w-8 h-8" />
            </div>

            <div className="bg-slate-950 p-4 rounded border border-slate-800 relative overflow-hidden">
              {isSimulating && (
                <div className="absolute inset-0 bg-slate-900/80 flex items-center justify-center backdrop-blur-sm z-10">
                  <RefreshCw className="w-6 h-6 text-blue-500 animate-spin" />
                </div>
              )}
              <span className="text-sm text-slate-400 uppercase tracking-wider block mb-1">Simulated Premium</span>
              <span className={`text-3xl font-mono font-bold ${delta > 0 ? 'text-red-400' : delta < 0 ? 'text-green-400' : 'text-blue-400'}`}>
                ${simulatedPremium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
              
              {delta !== 0 && !isSimulating && (
                <div className={`mt-2 text-sm ${delta > 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {delta > 0 ? '+' : ''}{delta.toLocaleString(undefined, { maximumFractionDigits: 0 })} ({((delta / originalPremium) * 100).toFixed(1)}%)
                </div>
              )}
            </div>
          </div>

          <Button 
            onClick={runSimulation} 
            disabled={isSimulating || signals.length === 0}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white mt-auto"
          >
            {isSimulating ? "Calculating..." : <><Play className="w-4 h-4 mr-2" /> Run Simulation</>}
          </Button>

        </CardContent>
      </Card>
    </div>
  );
}