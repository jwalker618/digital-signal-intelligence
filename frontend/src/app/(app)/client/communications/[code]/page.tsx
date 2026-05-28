"use client";

import { use } from "react";
import { ThreadView } from "@/components/portal/thread-view";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchCommunicationThread } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import type { CommunicationsThreadResponse } from "@/types/portal";

export default function ClientThreadPage(props: {
  params: Promise<{ code: string }>;
}) {
  const { code } = use(props.params);
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";

  const { data, error, loading, reload } =
    useRoleScopedFetch<CommunicationsThreadResponse>({
      fetcher: () => fetchCommunicationThread(accessToken, code),
      enabled,
      deps: [accessToken, code],
    });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (loading) return <PageLoading />;
  if (error) return <PageError message={error} />;
  if (!data) return <PageLoading />;

  return (
    <ThreadView
      data={data}
      viewerRole="client"
      inboxPath="/client/communications"
      personaCrumb="Client Portal"
      onReplied={reload}
    />
  );
}
