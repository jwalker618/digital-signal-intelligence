"use client";

import SubmissionDetailView from "@/components/portal/views/SubmissionDetailView";

export default function Page(props: { params: Promise<{ code: string }> }) {
  return <SubmissionDetailView {...props} />;
}
