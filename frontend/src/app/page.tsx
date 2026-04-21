"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import PipelineTable from "@/components/submissions/PipelineTable";
import WorkbenchView from "@/components/submissions/WorkbenchView";

export default function Home() {
  const {
    activeMenu,
    activeSubmission,
    fetchSubmissions,
    isLoading
  } = useDsiStore();

  // CRITICAL: Fetch the pipeline data when the app loads
  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  // If we have an active submission, ALWAYS show the Workbench wrapper
  if (activeSubmission) {
    return <WorkbenchView />;
  }

  // Otherwise, route the top-level menus
  switch (activeMenu) {
    case "Referral Pipeline":
      return <PipelineTable type="referral" />;
    case "Full Pipeline":
      return <PipelineTable type="full" />;
    case "Performance Metrics":
      return <div className="p-8 text-dsi-selected">Analytics Dashboard Under Construction</div>;
    default:
      return <PipelineTable type="referral" />;
  }
}