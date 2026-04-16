"use client";

/**
 * SummaryTab — temporarily repurposed as a TEMPLATE SHOWCASE.
 *
 * Each card here demonstrates one or two reusable primitives in
 * `components/base/*` so styling can be reviewed in isolation before the
 * real workbench tabs are migrated onto them. All data is static / mocked,
 * so this renders without an active submission.
 *
 * When the migration is done, restore the data-driven SummaryTab from git
 * history (or rebuild it from the sections registry — see the comment at
 * the bottom of this file for a reference snippet).
 */

import "@/app/globals.css";
import {
  Activity,
  BarChart3,
  Building2,
  Flag,
  Layers,
  PenLine,
  Scale,
  ShieldCheck,
  TrendingUp,
  User,
  Search,
} from "lucide-react";

/* ── Card shells ─────────────────────────────────────────────────────── */
import {
  CardGrid,
  StandardCard,
  PopupCard,
  SubmissionHeaderCard,

} from "@/components/base/cards";

import SectionCard from "@/components/base/sectionCard";

/* ── Content primitives ──────────────────────────────────────────────── */
import LabelValueList from "@/components/base/labelValueList";
import KeyValueList from "@/components/base/keyValueList";
import StatsGrid from "@/components/base/statsGrid";
import ContributionTable from "@/components/base/contributionTable";
import ExpandableGroupTable from "@/components/base/expandableGroupTable";
import KpiTile from "@/components/base/kpiTile";
import StatusPill from "@/components/base/statusPill";
import ScoreBar from "@/components/base/scoreBar";
import InfoPanel from "@/components/base/infoPanel";
import PeerScatterChart from "@/components/base/charts/PeerScatterChart";
import BenchmarkBarChart from "@/components/base/charts/BenchmarkBarChart";

import { DECISION_PALETTE, ACTION_PALETTE } from "@/lib/statusPalette";

/* ── Tiny helpers used only inside this showcase ─────────────────────── */

function ShowcaseSection({
  title,
  caption,
  spanClass = "col-span-1 md:col-span-2 lg:col-span-3",
  children,
}: {
  title: string;
  caption?: string;
  spanClass?: string;
  children: React.ReactNode;
}) {
  return (
    <StandardCard title={title} lucideIcon={Flag} spanClass={spanClass}>
      {caption && (
        <p className="pl-dsi-pad pr-dsi-pad text-xs opacity-60 mb-3">{caption}</p>
      )}
      <div className="pl-dsi-pad pr-dsi-pad pb-2">{children}</div>
    </StandardCard>
  );
}

/* ── Mock data ───────────────────────────────────────────────────────── */

const mockCommercialRows = [
  { label: "Entity", value: "Acme Underwriting Ltd." },
  { label: "Offered Premium", value: "1,250,000" },
  { label: "Gross Premium", value: "1,400,000" },
  { label: "Currency", value: "USD" },
  { label: "Distribution", value: "Broker" },
];

const mockSubmissionData = {
  limit: 5_000_000,
  retention: 250_000,
  naics_code: "2211",
  annual_revenue: 87_500_000,
  employee_count: 412,
};

const mockContributionRows = [
  { name: "technology", risk_contribution: 42.3 },
  { name: "finance", risk_contribution: 31.7 },
  { name: "operations", risk_contribution: 19.8 },
  { name: "compliance", risk_contribution: 12.1 },
  { name: "geographic", risk_contribution: 8.4 },
];
const mockContributionOther = {
  name: "Other (2)",
  risk_contribution: 20.5,
};

const mockModifierGroups = [
  {
    key: "categorical",
    title: "Categorical",
    items: [
      { name: "High-risk jurisdiction", multiplier: 1.15, impact: 18_750 },
      { name: "Regulated industry", multiplier: 1.08, impact: 10_000 },
    ],
    summary: ["2 items", "$28,750", "$1,278,750"] as React.ReactNode[],
  },
  {
    key: "signal",
    title: "Signal",
    items: [] as Array<{ name: string; multiplier: number; impact: number }>,
    summary: ["0 items", "$0", "$1,278,750"] as React.ReactNode[],
    emptyMessage: "No modifiers applied.",
  },
  {
    key: "direct",
    title: "Direct Query",
    items: [
      { name: "Prior loss history", multiplier: 1.22, impact: 34_500 },
      { name: "Credit score band", multiplier: 0.97, impact: -5_200 },
      { name: "Litigation exposure", multiplier: 1.04, impact: 7_100 },
    ],
    summary: ["3 items", "$36,400", "$1,315,150"] as React.ReactNode[],
  },
];

const mockPeerPoints = Array.from({ length: 60 }).map((_, i) => ({
  x: 10 + Math.random() * 80,
  y: 10 + Math.random() * 80,
  decision: ["approve", "refer", "decline", undefined][i % 4],
}));

const mockBenchmarkData = [
  { cohort: "Tech / SMB", avg_modifier: 1.04, peer_count: 48 },
  { cohort: "Tech / Mid-market", avg_modifier: 1.12, peer_count: 62 },
  { cohort: "Tech / Enterprise", avg_modifier: 1.28, peer_count: 23 },
  { cohort: "Finance / SMB", avg_modifier: 0.98, peer_count: 31 },
  { cohort: "Finance / Enterprise", avg_modifier: 1.35, peer_count: 14 },
];

/* ── Component ───────────────────────────────────────────────────────── */

export default function SummaryTab() {
  return (
    <div className="w-full no-scrollbar animate-in fade-in duration-500">

      <CardGrid>

        {/* ═══════════════════════════════════════════════════════════════
            1. Submission header — banner + hero metrics
            ═══════════════════════════════════════════════════════════════ */}
        <SubmissionHeaderCard
          decision="refer"
          title="refer"
          subtitle="Referred for manual review"
          spanClass="col-span-1 md:col-span-2 lg:col-span-3"
          headerRight={
            <>
              <div>
                <span className="block dsi-analysis-description">Status</span>
                <span className="dsi-analysis-item">DRAFT</span>
              </div>
              <div>
                <span className="block dsi-analysis-description">Valid From</span>
                <span className="dsi-analysis-item">2026-01-01</span>
              </div>
              <div>
                <span className="block dsi-analysis-description">Valid Until</span>
                <span className="dsi-analysis-item">2026-12-31</span>
              </div>
            </>
          }
        >
          <StatsGrid
            columns={[
              { width: "10%", label: "Final Composite Score", value: "612.4" },
              { width: "20%", label: "Final Tier",            value: "T3 (Moderate)" },
              { width: "10%", label: "Currency",              value: "USD" },
              { width: "15%", label: "Recommended Premium",   value: "1,400,000" },
              { width: "15%", label: "Recommended Limit",     value: "5,000,000" },
              { width: "15%", label: "Gross Premium",         value: "1,278,750" },
            ]}
          />
        </SubmissionHeaderCard>

        {/* ═══════════════════════════════════════════════════════════════
            2. Card shells — StandardCard / PopupCard / SectionCard
            ═══════════════════════════════════════════════════════════════ */}
        <StandardCard
          title="StandardCard"
          lucideIcon={ShieldCheck}
          spanClass="col-span-1"
        >
          <p className="pl-dsi-pad pr-dsi-pad text-sm pb-2">
            Default section-container. Header = icon + title; body takes any
            children.
          </p>
        </StandardCard>

        <PopupCard
          title="PopupCard"
          lucideIcon={Search}
          spanClass="col-span-1"
        >
          <p className="text-sm">
            Popup content renders inside a modal when the tile is clicked.
            Focus trap + Escape / click-outside / scroll-lock are handled by
            the base Modal.
          </p>
        </PopupCard>

        <div className="col-span-1">
          <SectionCard section="commercial" spanClass="" />
        </div>

        {/* ═══════════════════════════════════════════════════════════════
            3. LabelValueList — card variant
            ═══════════════════════════════════════════════════════════════ */}
        <StandardCard
          title="LabelValueList (card variant)"
          lucideIcon={Building2}
          spanClass="col-span-1 md:col-span-2 lg:col-span-1"
        >
          <LabelValueList rows={mockCommercialRows} />
        </StandardCard>

        {/* ═══════════════════════════════════════════════════════════════
            4. KeyValueList — modal variant (used as modal body normally)
            ═══════════════════════════════════════════════════════════════ */}
        <StandardCard
          title="KeyValueList (modal variant)"
          lucideIcon={User}
          spanClass="col-span-1 md:col-span-2 lg:col-span-2"
        >
          <div className="pl-dsi-pad pr-dsi-pad pb-2">
            <KeyValueList
              data={mockSubmissionData}
              renderLabel={(k) => k.replace(/_/g, " ")}
            />
          </div>
        </StandardCard>

        {/* ═══════════════════════════════════════════════════════════════
            5. StatsGrid — KPI row with inline grid-template
            ═══════════════════════════════════════════════════════════════ */}
        <ShowcaseSection
          title="StatsGrid"
          caption="Header-over-value column layout. Widths are inline styles — any percentage works."
        >
          <StatsGrid
            columns={[
              { width: "25%", label: "Pure Composite Score", value: "612.4" },
              { width: "25%", label: "Confidence",           value: "78%"   },
              { width: "25%", label: "Signal Coverage",      value: "84%"   },
              { width: "25%", label: "Final Tier",           value: "T3"    },
            ]}
          />
        </ShowcaseSection>

        {/* ═══════════════════════════════════════════════════════════════
            6. KpiTile row — same information, tile style
            ═══════════════════════════════════════════════════════════════ */}
        <ShowcaseSection
          title="KpiTile"
          caption="Drop tiles into a `grid grid-cols-N gap-4` row. Use `variant=\emphasis\` for the hero number."
        >
          <div className="grid grid-cols-2 md:grid-cols-6 gap-6">
            <KpiTile label="Pure Composite" value="612.4" />
            <KpiTile label="Confidence"     value="78%" />
            <KpiTile label="Signal Coverage" value="84%" />
            <KpiTile label="Score-Based Tier" value="T4" />
            <KpiTile label="Final Composite" value="612.4" variant="emphasis" />
            <KpiTile
              label="Final Tier"
              value="T3 (Moderate)"
              subtext="after 2 overrides"
              variant="emphasis"
            />
          </div>
        </ShowcaseSection>

        {/* ═══════════════════════════════════════════════════════════════
            7. StatusPill — decision + action palettes
            ═══════════════════════════════════════════════════════════════ */}
        <ShowcaseSection
          title="StatusPill"
          caption="Use `palette + status` for domain enums, or `tone` for ad-hoc chips."
        >
          <div className="flex flex-wrap gap-2 pb-2">
            <StatusPill palette={DECISION_PALETTE} status="approve">Approve</StatusPill>
            <StatusPill palette={DECISION_PALETTE} status="refer">Refer</StatusPill>
            <StatusPill palette={DECISION_PALETTE} status="decline">Decline</StatusPill>
            <StatusPill palette={DECISION_PALETTE} status="pending">Pending</StatusPill>
          </div>
          <div className="flex flex-wrap gap-2 pb-2">
            <StatusPill palette={ACTION_PALETTE} status="modifier">Modifier</StatusPill>
            <StatusPill palette={ACTION_PALETTE} status="referral">Referral</StatusPill>
            <StatusPill palette={ACTION_PALETTE} status="tier_override">Tier Override</StatusPill>
            <StatusPill palette={ACTION_PALETTE} status="flag">Flag</StatusPill>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusPill tone="positive" size="md">Positive</StatusPill>
            <StatusPill tone="warning" size="md">Warning</StatusPill>
            <StatusPill tone="negative" size="md">Negative</StatusPill>
            <StatusPill tone="info" size="md">Info</StatusPill>
            <StatusPill tone="muted" size="md">Muted</StatusPill>
          </div>
        </ShowcaseSection>

        {/* ═══════════════════════════════════════════════════════════════
            8. ScoreBar — threshold-coloured horizontal bars
            ═══════════════════════════════════════════════════════════════ */}
        <ShowcaseSection
          title="ScoreBar"
          caption="Default thresholds: ≤40 positive, ≤70 warning, else negative. Override `thresholds` to invert or rescale."
        >
          <div className="space-y-2 max-w-md">
            <ScoreBar label="Low"    value={22} />
            <ScoreBar label="Mid"    value={55} />
            <ScoreBar label="High"   value={84} />
            <ScoreBar label="Freq"   value={38} decimals={0} />
            <ScoreBar label="Sev"    value={72} decimals={0} />
          </div>
        </ShowcaseSection>

        {/* ═══════════════════════════════════════════════════════════════
            9. InfoPanel — bordered sub-metric box
            ═══════════════════════════════════════════════════════════════ */}
        <ShowcaseSection
          title="InfoPanel"
          caption="Bordered sub-metric container. Header label + optional right-side aside."
        >
          <div className="grid grid-cols-3 gap-3">
            <InfoPanel label="Band Percentile" aside="weight 0.4">
              <span className="font-bold text-lg">62%</span>
              <span className="text-xs opacity-50 block">from band floor</span>
            </InfoPanel>
            <InfoPanel label="Below Ceiling">
              <span className="font-bold text-lg">$2,150,000</span>
            </InfoPanel>
            <InfoPanel label="Above Floor">
              <span className="font-bold text-lg">$1,850,000</span>
            </InfoPanel>
          </div>
        </ShowcaseSection>

        {/* ═══════════════════════════════════════════════════════════════
            10. ContributionTable — Group + top-3 + Other
            ═══════════════════════════════════════════════════════════════ */}
        <ShowcaseSection
          title="ContributionTable"
          caption="The calculation grid used across the three-pillar assessment."
          spanClass="col-span-1 md:col-span-2 lg:col-span-2"
        >
          <ContributionTable
            columnHeaders={["Contribution"]}
            rows={mockContributionRows}
            otherRow={mockContributionOther}
            fields={["risk_contribution"]}
          />
        </ShowcaseSection>

        {/* ═══════════════════════════════════════════════════════════════
            11. ExpandableGroupTable — PricingTab-style accordion
            ═══════════════════════════════════════════════════════════════ */}
        <ShowcaseSection
          title="ExpandableGroupTable"
          caption="Click a group header to expand. Controls its own open/closed state, or accept `expanded` + `onToggle` to control externally."
        >
          <ExpandableGroupTable
            columns={[
              {
                label: (
                  <>
                    <PenLine className="icon" /> Adjustments
                  </>
                ),
                width: "50%",
                align: "left",
              },
              { label: "Modifier", width: "10%", align: "center" },
              { label: "Impact", width: "20%", align: "right" },
              { label: "Result", width: "20%", align: "right" },
            ]}
            groups={mockModifierGroups}
            renderItemCells={(mod) => [
              mod.name,
              `${mod.multiplier.toFixed(3)}x`,
              mod.impact >= 0 ? `$${mod.impact.toLocaleString()}` : `-$${Math.abs(mod.impact).toLocaleString()}`,
              "-",
            ]}
            defaultExpanded={{ categorical: true }}
          />
        </ShowcaseSection>

        {/* ═══════════════════════════════════════════════════════════════
            12. PeerScatterChart
            ═══════════════════════════════════════════════════════════════ */}
        <ShowcaseSection
          title="PeerScatterChart"
          caption="Peer dots coloured by decision + active-submission star + dashed crosshair."
          spanClass="col-span-1 md:col-span-2 lg:col-span-2"
        >
          <PeerScatterChart
            points={mockPeerPoints}
            subject={{ x: 62, y: 48 }}
            xLabel="Propensity"
            yLabel="Severity"
            xName="Propensity"
            yName="Severity"
            height={340}
          />
        </ShowcaseSection>

        {/* ═══════════════════════════════════════════════════════════════
            13. BenchmarkBarChart
            ═══════════════════════════════════════════════════════════════ */}
        <ShowcaseSection
          title="BenchmarkBarChart"
          caption="Subject-highlighted bar + dashed reference line + per-bar n= annotations."
        >
          <BenchmarkBarChart
            data={mockBenchmarkData}
            categoryKey="cohort"
            valueKey="avg_modifier"
            subjectCategory="Tech / Mid-market"
            subjectValue={1.12}
            peerCountKey="peer_count"
            valueName="Avg Modifier"
            height={260}
          />
        </ShowcaseSection>

        {/* ═══════════════════════════════════════════════════════════════
            14. Additional sections from the registry (live data)
            ═══════════════════════════════════════════════════════════════ */}
        <SectionCard section="riskTerms"   spanClass="col-span-1" />
        <SectionCard section="threePillar" spanClass="col-span-1 md:col-span-2 lg:col-span-2" />
        <SectionCard section="notes"       spanClass="col-span-1 md:col-span-2 lg:col-span-3" />
        <SectionCard section="who"         spanClass="col-span-1" />
        <SectionCard section="discovery"   spanClass="col-span-1" />

        {/* Reference: how the data-driven SummaryTab looks.
        ----------------------------------------------------
        const config: DashboardItem[] = [
          { id: "header",       card: SubmissionHeaderCard, decision,
            title: decision, headerRight: <DecisionStatusFields/>,
            children: <HeroMetricsGrid/>,
            spanClass: "col-span-1 md:col-span-2 lg:col-span-3" },
          section("commercial", "commercial",  "col-span-1"),
          section("riskTerms",  "riskTerms",   "col-span-1 md:col-span-2"),
          section("threePillar","threePillar", "col-span-1 md:col-span-2 lg:col-span-3"),
          section("notes",      "notes",       "col-span-1 md:col-span-2 lg:col-span-3", notesTitle),
        ];
        */}
      </CardGrid>
    </div>
  );
}
