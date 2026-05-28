"use client";

/**
 * Page-level state shells used by every broker / client page:
 *
 *   <PageLoading message? icon? />
 *   <PageError message />
 *   <RoleGate expected message? />
 *
 * Re-styled against the reimagined design tokens. The API is unchanged so
 * the lifted pages can swap from the old version without callsite edits.
 */

import { AlertTriangle, Loader2, type LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Eyebrow, Body } from "@/components/ui/typography";

interface ShellProps {
  title: string;
  message: string;
  icon: LucideIcon;
}

function Shell({ title, message, icon: Icon }: ShellProps) {
  return (
    <div className="flex h-full w-full items-center justify-center p-10">
      <Card pad="lg" className="flex max-w-md items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-surface-sunken text-ink-soft">
          <Icon size={20} />
        </div>
        <div>
          <Eyebrow>{title}</Eyebrow>
          <Body className="mt-1">{message}</Body>
        </div>
      </Card>
    </div>
  );
}

export function PageLoading({
  message = "Loading…",
  icon = Loader2,
}: {
  message?: string;
  icon?: LucideIcon;
}) {
  return <Shell title="Loading" message={message} icon={icon} />;
}

export function PageError({ message }: { message: string }) {
  return <Shell title="Unable to load" message={message} icon={AlertTriangle} />;
}

export type ExpectedPersona = "broker" | "client" | "carrier";

export function RoleGate({
  expected,
  message,
}: {
  expected: ExpectedPersona;
  message?: string;
}) {
  const title =
    expected === "broker"
      ? "Broker-only"
      : expected === "client"
        ? "Insured-only"
        : "Carrier-only";
  const defaultMessage =
    expected === "broker"
      ? "This view is for broker users only."
      : expected === "client"
        ? "This view is for insured client users only."
        : "This view is for carrier users only.";
  return (
    <Shell title={title} message={message ?? defaultMessage} icon={AlertTriangle} />
  );
}
