"use client";

// v8.1 Phase B — /portal/profile
//
// "Who you are" surface for the client: identity, jurisdiction,
// industry, signal census (what we observe / what we don't yet).
// Builds trust by making the signal apparatus legible.

import { useEffect, useState } from "react";

import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  Circle,
  Eye,
  EyeOff,
  Globe,
  ShieldCheck,
  UserCircle,
} from "lucide-react";

import ViewCanvas from "@/components/ViewCanvas";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  InfoPanel,
  LabelValueList,
  NoData,
  StatsGrid,
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { fetchClientProfile } from "@/lib/portalApi";
import { formatCurrency } from "@/lib/format";
import type { ClientProfileResponse } from "@/types/portal";


export default function ClientProfilePage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [profile, setProfile] = useState<ClientProfileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setActiveMenu("Your Profile"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchClientProfile(accessToken);
        if (!cancelled) setProfile(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken && userRole === "CLIENT") load();
    return () => { cancelled = true; };
  }, [accessToken, userRole]);

  if (userRole !== "CLIENT") {
    return (
      <ViewCanvas>
        <CardGrid cols="grid-cols-1">
          <StandardCard title="Client-only" lucideIcon={AlertTriangle}>
            <NoData message="The Your Profile view is for client users only." />
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }
  if (error) {
    return (
      <ViewCanvas>
        <CardGrid cols="grid-cols-1">
          <StandardCard title="Unable to load" lucideIcon={AlertTriangle}>
            <NoData message={error} />
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }
  if (!profile) {
    return (
      <ViewCanvas>
        <CardGrid cols="grid-cols-1">
          <StandardCard title="Loading" lucideIcon={UserCircle}>
            <NoData message="Loading your profile…" />
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title={profile.entity_name}
          subtitle={
            profile.broker_name
              ? `Insured · Placed by ${profile.broker_name}`
              : "Insured"
          }
          lucideIcon={UserCircle}
        >
          <StatsGrid
            columns={[
              { label: "Industry",        value: profile.industry_label ?? "—", align: "center" },
              { label: "Revenue band",    value: profile.revenue_band ?? "—", align: "center" },
              { label: "Active policies", value: profile.active_coverage_count, align: "center" },
              { label: "Coverage lines",  value: profile.coverage_lines.length, align: "center" },
              {
                label: "Annual revenue",
                value: profile.revenue != null ? formatCurrency(profile.revenue, 0) : "—",
                align: "center",
              },
            ]}
          />
        </SubmissionHeaderCard>

        <CardGrid cols="grid-cols-1 lg:grid-cols-2" className="gap-4">
          <StandardCard title="Identity" lucideIcon={Building2}>
            <LabelValueList
              variant="card"
              rows={[
                { label: "Legal entity", value: profile.entity_name },
                { label: "Domain", value: profile.domain ?? "—" },
                { label: "Country", value: profile.country ?? "—" },
                {
                  label: "NAICS",
                  value: profile.naics_code
                    ? `${profile.naics_code} (${profile.industry_label ?? profile.industry_code})`
                    : "—",
                },
                { label: "Broker", value: profile.broker_name ?? "Not assigned" },
              ]}
            />
          </StandardCard>

          <StandardCard title="Active coverage lines" lucideIcon={ShieldCheck}>
            {profile.coverage_lines.length === 0 ? (
              <NoData message="No active coverages yet." />
            ) : (
              <LabelValueList
                variant="card"
                rows={profile.coverage_lines.map((c) => ({
                  label: c.charAt(0).toUpperCase() + c.slice(1).replace(/_/g, " "),
                  value: <span className="text-generate-text-good">Active</span>,
                }))}
              />
            )}
          </StandardCard>
        </CardGrid>

        <StandardCard
          title="Signal apparatus — what we observe"
          lucideIcon={Globe}
          headerRight={
            <span className="text-xs text-generate-text-placeholder">
              {profile.signal_categories_observed.length} of
              {" "}
              {profile.signal_categories_observed.length + profile.signal_categories_pending.length}
              {" "}
              categories captured
            </span>
          }
        >
          <p className="text-sm py-2">
            DSI builds your signal score from the categories below. Items
            marked <strong>captured</strong> contributed to your current
            quote; items marked <strong>pending</strong> would strengthen
            the picture if data became available.
          </p>
          <CardGrid cols="grid-cols-1 md:grid-cols-2" className="gap-3">
            <InfoPanel label="Captured" aside={`${profile.signal_categories_observed.length} categories`}>
              <ul className="space-y-1 mt-1">
                {profile.signal_categories_observed.map((c) => (
                  <li key={c} className="text-sm flex items-center gap-2 text-generate-text-good">
                    <CheckCircle2 className="generate-app-icon" />
                    {c}
                  </li>
                ))}
                {profile.signal_categories_observed.length === 0 && (
                  <li className="text-xs text-generate-text-placeholder">None captured yet.</li>
                )}
              </ul>
            </InfoPanel>
            <InfoPanel label="Pending" aside={`${profile.signal_categories_pending.length} categories`}>
              <ul className="space-y-1 mt-1">
                {profile.signal_categories_pending.map((c) => (
                  <li key={c} className="text-sm flex items-center gap-2 text-generate-text-placeholder">
                    <Circle className="generate-app-icon" />
                    {c}
                  </li>
                ))}
                {profile.signal_categories_pending.length === 0 && (
                  <li className="text-xs">All categories captured.</li>
                )}
              </ul>
            </InfoPanel>
          </CardGrid>
        </StandardCard>

        <InfoPanel label="Privacy" aside="DSI Operating Principles">
          <p className="text-xs">
            Your DSI profile is built from publicly-observable signals and
            information you've shared through your broker. We do not use
            your data to make decisions affecting other clients, and you
            can request the full audit trail of any signal at any time.
          </p>
        </InfoPanel>

      </CardGrid>
    </ViewCanvas>
  );
}
