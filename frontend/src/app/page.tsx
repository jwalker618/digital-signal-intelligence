"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import PipelineTable from "@/components/referrals/PipelineTable";

export default function DSIDashboard() {
  const { activeMenu, fetchSubmissions, error } = useDsiStore();

  // Fetch the data on load
  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  if (error) {
    return <div className="text-red-500 font-semibold p-4">Error loading data: {error}</div>;
  }

  // ==========================================
  // VIEW ROUTER
  // ==========================================
  
  if (activeMenu === "Referral Pipeline") {
    return <PipelineTable type="referral" />;
  }

  if (activeMenu === "Full Pipeline") {
    return <PipelineTable type="full" />;
  }

  if (activeMenu === "Workbench") {
    return (
      <div className="text-dsi-selected">
        <h2 className="text-xl font-bold mb-4">Submission Specific Analysis Screen</h2>
        <p>This is where the individual submission details, world model, and retuning engine will go!</p>
      </div>
    );
  }

  return (
    <div className="text-dsi-selected flex h-full items-center justify-center italic opacity-70">
      Select a view from the sidebar.
    </div>
  );
}