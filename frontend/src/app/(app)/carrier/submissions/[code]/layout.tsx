"use client";

import { use, useEffect, type ReactNode } from "react";
import { WorkbenchSidebar } from "@/components/chrome/workbench-sidebar";
import { useDsiStore } from "@/store/dsiStore";

/**
 * Submission Workbench shell. Renders the drill-down sidebar (replacing the
 * carrier persona sidebar) and primes dsiStore with the active submission
 * so every tab below reads from the same data.
 */
export default function WorkbenchLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ code: string }>;
}) {
  const { code } = use(params);
  const submissions = useDsiStore((s) => s.submissions);
  const activeCode = useDsiStore(
    (s) => s.activeSubmission?.submission_code as string | undefined,
  );
  const fetchSubmissions = useDsiStore((s) => s.fetchSubmissions);
  const fetchCore = useDsiStore((s) => s.fetchCoreSubmissionDetail);

  // Make sure the pipeline list is loaded, then activate this submission.
  // fetchCoreSubmissionDetail() owns setting `activeSubmission` internally.
  useEffect(() => {
    if (activeCode === code) return;
    let cancelled = false;
    (async () => {
      let pool = submissions;
      if (pool.length === 0) {
        try {
          await fetchSubmissions();
          pool = useDsiStore.getState().submissions;
        } catch {
          return;
        }
      }
      if (cancelled) return;
      const row = pool.find((s) => s.submission_code === code);
      if (row) {
        try {
          await fetchCore(row);
        } catch {
          /* tab pages render their own empty/error state */
        }
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code]);

  return (
    <>
      <WorkbenchSidebar submissionCode={code} />
      <main className="flex h-full flex-1 flex-col overflow-hidden bg-canvas">
        {children}
      </main>
    </>
  );
}
