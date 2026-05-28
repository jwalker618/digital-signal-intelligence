"use client";

import CommunicationsThreadView from "@/components/portal/views/CommunicationsThreadView";

export default function Page(props: { params: Promise<{ code: string }> }) {
  return <CommunicationsThreadView {...props} />;
}
