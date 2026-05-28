"use client";

import { useEffect, useState } from "react";
import { PageLoading, PageError, RoleGate } from "@/components/base/pageStates";
import { CarrierShell } from "@/components/chrome/carrier-shell";
import { isCarrierRole } from "@/lib/portalPaths";
import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { PipelineBody } from "../page";

export default function FullPipelinePage() {
  const user = useAuthStore((s) => s.user);
  const submissions = useDsiStore((s) => s.submissions);
  const fetchSubmissions = useDsiStore((s) => s.fetchSubmissions);
  const [state, setState] = useState<"idle" | "loading" | "ok" | "error">(
    submissions.length > 0 ? "ok" : "loading",
  );
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchSubmissions()
      .then(() => !cancelled && setState("ok"))
      .catch((e) => {
        if (cancelled) return;
        setErr(e instanceof Error ? e.message : String(e));
        setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [fetchSubmissions]);

  const inner =
    !user ? (
      <PageLoading message="Signing in…" />
    ) : user.role && !isCarrierRole(user.role) ? (
      <RoleGate expected="carrier" />
    ) : state === "loading" ? (
      <PageLoading message="Loading pipeline…" />
    ) : state === "error" ? (
      <PageError message={err ?? "Unknown error"} />
    ) : (
      <PipelineBody submissions={submissions} mode="full" />
    );

  return <CarrierShell>{inner}</CarrierShell>;
}
