"use client";

import "@/app/globals.css";
import {
  StandardCard,
  PopupCard,
  SubmissionHeaderCard,
  BaseCardProps,
  Decision,
} from "@/components/base/cards";

import { ShieldCheck, Search, User } from "lucide-react";

/**
 * Dispatch-by-component config: each item carries the card component it wants
 * to render as, plus that card's props. This keeps the loop type-safe and
 * avoids a string registry.
 */
type DashboardItem =
  | ({ id: string; card: typeof StandardCard } & BaseCardProps)
  | ({ id: string; card: typeof PopupCard } & React.ComponentProps<typeof PopupCard>)
  | ({ id: string; card: typeof SubmissionHeaderCard } & React.ComponentProps<typeof SubmissionHeaderCard>);

// Placeholder decision until wired to the store.
const decision: Decision = "pending";

const dashboardConfig: DashboardItem[] = [
  {
    id: "00",
    card: SubmissionHeaderCard,
    decision,
    title: decision,
    spanClass: "col-span-1 md:col-span-2 lg:col-span-3",
    children: <p className="pt-2 text-sm text-center">Hero metrics go here</p>,
  },
  {
    id: "01",
    card: StandardCard,
    title: "Loss Metrics",
    lucideIcon: ShieldCheck,
    spanClass: "col-span-1",
    children: <p>Block 1</p>,
  },
  {
    id: "02",
    card: StandardCard,
    title: "Risk Overview",
    lucideIcon: ShieldCheck,
    spanClass: "col-span-1",
    children: <p>Block 2</p>,
  },
  {
    id: "03",
    card: StandardCard,
    title: "Exposure Analysis",
    lucideIcon: ShieldCheck,
    spanClass: "col-span-1 md:col-span-2 lg:col-span-3",
    children: <p>Block 3</p>,
  },
  {
    id: "04",
    card: StandardCard,
    title: "Network Authority",
    lucideIcon: ShieldCheck,
    spanClass: "col-span-1",
    children: <p>Block 4</p>,
  },
  {
    id: "05",
    card: PopupCard,
    title: "Who are they?",
    lucideIcon: User,
    spanClass: "col-span-1",
    children: <p>Submission data detail goes here</p>,
  },
  {
    id: "06",
    card: PopupCard,
    title: "Discovery",
    lucideIcon: Search,
    spanClass: "col-span-1",
    children: <p>Discovery output detail goes here</p>,
  },
];

export default function DashboardLayout() {
  return (
    <div className="w-full no-scrollbar animate-in fade-in duration-500">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-dsi-pad pt-dsi-pad">
        {dashboardConfig.map(({ id, card: Card, ...props }) => (
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          <Card key={id} {...(props as any)} />
        ))}
      </div>
    </div>
  );
}
