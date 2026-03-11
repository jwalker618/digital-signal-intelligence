"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
// import { ScatterChart, PieChart, BarChart, etc... } from "recharts";

export default function LossTab() {
  const { 
    activeSubmission, 
    activeVersion,
    lossCohortBenchmarks,
    lossTrendDistribution,
    lossScatterData,
    isFetchingLossAnalytics,
    fetchLossAnalytics
  } = useDsiStore();

  // Trigger the fetch when the tab loads or the submission changes
  useEffect(() => {
    if (activeSubmission?.coverage) {
      // Fetch peers for the last 365 days matching this coverage line
      fetchLossAnalytics(activeSubmission.coverage, 365);
    }
  }, [activeSubmission?.coverage, fetchLossAnalytics]);

  if (!activeSubmission || !activeVersion) return null;

  return (
    <div className="w-full max-w-[1400px] mx-auto space-y-6 animate-in fade-in duration-500 pb-12 pt-4">
      
      {/* COMPONENT A: The Subject Profile (Hero KPIs) */}
      <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm">
        {/* Render activeVersion.loss_propensity_band, etc. here */}
      </div>

      {isFetchingLossAnalytics ? (
        <div className="text-center opacity-50 animate-pulse py-12">Calculating peer benchmarks...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* COMPONENT B: Scatter Plot */}
          <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm h-80">
            <h3>Frequency vs. Severity</h3>
            {/* Pass lossScatterData directly to Recharts ScatterChart */}
          </div>

          {/* COMPONENT C: Cohort Benchmarking */}
          <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm h-80">
            <h3>Cohort Performance</h3>
             {/* Pass lossCohortBenchmarks directly to Recharts BarChart */}
          </div>

          {/* COMPONENT D: Trend Distribution */}
          <div className="border border-dsi-outline/20 rounded-xl p-5 bg-dsi-analysis shadow-sm h-80">
            <h3>Trend Distribution</h3>
             {/* Pass lossTrendDistribution directly to Recharts PieChart */}
          </div>

        </div>
      )}
    </div>
  );
}