"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import SelectionTable from "@/components/submissions/SelectionTable";
import SelectionItem from "@/components/submissions/SelectionItem";

export default function Home() {
  const {
    activeMenu,
    setActiveMenu,
    activeSubmission,
    fetchSubmissions,
  } = useDsiStore();

  // CRITICAL: Fetch the pipeline data when the app loads
  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  // v8 polish: the carrier home is the Referral Pipeline view by
  // default. Set activeMenu so the title bar reads correctly on
  // first mount (after dsiStore's empty default / a session reset).
  useEffect(() => {
    if (!activeMenu) setActiveMenu("Referral Pipeline");
  }, [activeMenu, setActiveMenu]);

  // If we have an active submission, ALWAYS show the Workbench wrapper
  if (activeSubmission) {
    return <SelectionItem />;
  }

  // Otherwise, route the top-level menus
  switch (activeMenu) {
    case "Referral Pipeline": return <SelectionTable type="referral" />;
    case "Full Pipeline": return <SelectionTable type="full" />;
    case "Performance Metrics": return <div>Analytics Dashboard Under Construction</div>;
    
    default: return <SelectionTable type="referral" />;
  }
}