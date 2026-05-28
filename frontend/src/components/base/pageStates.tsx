"use client";

// Page-level state shells used by every broker / client page:
//
//   <PageLoading message? icon? />
//   <PageError message />
//   <RoleGate expected message? />
//
// Previously inlined as per-page LoadShell / ErrShell / BrokerOnly /
// ClientOnly mini-components -- pulled here so every page renders
// the same chrome for the same condition and there's one place to
// adjust the visual treatment.

import { AlertTriangle, Loader2, type LucideIcon } from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import { CardGrid, StandardCard } from "@/components/base/cards";
import { NoData } from "@/components/base/content/primatives";


export function PageLoading({
  message = "Loading…",
  icon = Loader2,
}: {
  message?: string;
  icon?: LucideIcon;
}) {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={icon}>
          <NoData message={message} />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}


export function PageError({ message }: { message: string }) {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Unable to load" lucideIcon={AlertTriangle}>
          <NoData message={message} />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}


export type ExpectedPersona = "broker" | "client" | "carrier";


export function RoleGate({
  expected, message,
}: {
  expected: ExpectedPersona;
  message?: string;
}) {
  const title =
    expected === "broker" ? "Broker-only" :
    expected === "client" ? "Insured-only" :
    "Carrier-only";
  const defaultMessage =
    expected === "broker" ? "This view is for broker users only." :
    expected === "client" ? "This view is for insured client users only." :
    "This view is for carrier users only.";
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title={title} lucideIcon={AlertTriangle}>
          <NoData message={message ?? defaultMessage} />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}
