"use client";

// v8.2 Carrier Intelligence — /broker/carriers
//
// Flagship broker page. Renders the full carrier universe with
// appetite breadth, capacity, commission, pricing tightness, ESG
// stance, and your synthesised hit rate. Clicking a carrier opens
// a modal with the full per-carrier drill.

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Building2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Globe,
  Leaf,
  ShieldCheck,
  Sparkles,
  TrendingUpDown,
  Trophy,
  X,
} from "lucide-react";

import Modal from "@/components/base/modal";
import ViewCanvas from "@/components/ViewCanvas";
import {
  CardGrid,
  StandardCard,
  SubmissionHeaderCard,
} from "@/components/base/cards";
import {
  InfoPanel,
  KpiTile,
  LabelValueList,
  NoData,
  ScoreBar,
  StatsGrid,
} from "@/components/base/content/primatives";
import VerticalFilter from "@/components/broker/VerticalFilter";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { fetchCarriers, fetchCarrierDetail } from "@/lib/portalApi";
import { formatCurrency } from "@/lib/format";
import type {
  AppetiteStance,
  CarrierDetailResponse,
  CarrierSummary,
  EsgStance,
  PricingPosition,
} from "@/types/portal";


type SortField =
  | "name" | "type" | "commission" | "pricing"
  | "win_rate" | "esg" | "capacity" | "appetite_breadth";


export default function CarriersPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [carriers, setCarriers] = useState<CarrierSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<CarrierDetailResponse | null>(null);
  const [sortField, setSortField] = useState<SortField>("win_rate");
  const [sortDesc, setSortDesc] = useState(true);
  const [esgFilter, setEsgFilter] = useState<EsgStance | "all">("all");
  const [pricingFilter, setPricingFilter] = useState<PricingPosition | "all">("all");

  useEffect(() => { setActiveMenu("Carrier Intelligence"); }, [setActiveMenu]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const resp = await fetchCarriers(accessToken);
        if (!cancelled) setCarriers(resp.carriers);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }
    if (accessToken && userRole === "BROKER") load();
    return () => { cancelled = true; };
  }, [accessToken, userRole]);

  const filtered = useMemo(() => {
    if (!carriers) return [];
    return carriers.filter((c) => {
      if (esgFilter !== "all" && c.esg_stance !== esgFilter) return false;
      if (pricingFilter !== "all" && c.pricing_position !== pricingFilter) return false;
      return true;
    });
  }, [carriers, esgFilter, pricingFilter]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    arr.sort((a, b) => {
      const cmp = sortValue(a, sortField) - sortValue(b, sortField);
      return sortDesc ? -cmp : cmp;
    });
    return arr;
  }, [filtered, sortField, sortDesc]);

  if (userRole !== "BROKER") {
    return <BrokerOnly />;
  }
  if (error) return <ErrShell msg={error} />;
  if (!carriers) return <LoadShell />;

  // Roster KPIs
  const leadersCount = carriers.filter((c) => c.esg_stance === "leader").length;
  const tightCount = carriers.filter((c) => c.pricing_position === "tight").length;
  const avgCommission = (carriers.reduce((a, c) => a + c.typical_commission_pct, 0) / carriers.length);
  const avgWinRate = carriers.reduce((a, c) => a + c.win_rate, 0) / carriers.length;

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title="Carrier Intelligence"
          subtitle="The market universe you place into — appetite, capacity, pricing, ESG"
          lucideIcon={Building2}
        >
          <StatsGrid
            columns={[
              { label: "Carriers in universe", value: carriers.length, align: "center" },
              { label: "ESG leaders", value: leadersCount, align: "center" },
              { label: "Tight pricing", value: tightCount, align: "center" },
              { label: "Avg commission", value: `${avgCommission.toFixed(1)}%`, align: "center" },
              { label: "Avg win rate", value: `${(avgWinRate * 100).toFixed(0)}%`, align: "center" },
            ]}
          />
        </SubmissionHeaderCard>

        <VerticalFilter />

        <StandardCard
          title={`Carrier roster (${sorted.length})`}
          lucideIcon={Building2}
          headerRight={
            <div className="flex items-center gap-3 text-xs">
              <span className="text-generate-text-placeholder">ESG:</span>
              <FilterSelect
                value={esgFilter}
                onChange={(v) => setEsgFilter(v as EsgStance | "all")}
                options={[
                  { value: "all", label: "All" },
                  { value: "leader", label: "Leader" },
                  { value: "progressive", label: "Progressive" },
                  { value: "neutral", label: "Neutral" },
                  { value: "restrictive", label: "Restrictive" },
                ]}
              />
              <span className="text-generate-text-placeholder">Pricing:</span>
              <FilterSelect
                value={pricingFilter}
                onChange={(v) => setPricingFilter(v as PricingPosition | "all")}
                options={[
                  { value: "all", label: "All" },
                  { value: "tight", label: "Tight" },
                  { value: "median", label: "Median" },
                  { value: "light", label: "Light" },
                ]}
              />
            </div>
          }
        >
          <CarrierTable
            carriers={sorted}
            sortField={sortField}
            sortDesc={sortDesc}
            onSort={(field) => {
              if (field === sortField) setSortDesc(!sortDesc);
              else { setSortField(field); setSortDesc(true); }
            }}
            onSelect={async (slug) => {
              try {
                const d = await fetchCarrierDetail(accessToken, slug);
                setDetail(d);
              } catch (e) {
                setError(e instanceof Error ? e.message : String(e));
              }
            }}
          />
        </StandardCard>

        <InfoPanel label="How to read this" aside="v8.2 — Marsh-aligned">
          <p className="text-xs">
            Appetite is a four-stance signal per coverage line: <em>leaning in</em>,
            <em> neutral</em>, <em>selective</em>, <em>leaning out</em>. Pricing
            position reflects where the carrier's quoted terms typically sit
            against market median. ESG stance combines public commitments
            (Net-Zero Alliance, coal exit timelines) with observable
            underwriting behaviour. Your win rate is a synthesised
            cohort-relative number for the demo; production wires actual
            broker history.
          </p>
        </InfoPanel>

      </CardGrid>

      <CarrierDetailModal detail={detail} onClose={() => setDetail(null)} />
    </ViewCanvas>
  );
}


// ----------------------------------------------------------------------------
// Roster table
// ----------------------------------------------------------------------------

function CarrierTable({
  carriers, sortField, sortDesc, onSort, onSelect,
}: {
  carriers: CarrierSummary[];
  sortField: SortField;
  sortDesc: boolean;
  onSort: (field: SortField) => void;
  onSelect: (slug: string) => void;
}) {
  const cols = "2fr 1.2fr 80px 90px 110px 70px 100px 90px";
  const headers: { label: string; field: SortField | null }[] = [
    { label: "Carrier", field: "name" },
    { label: "Type", field: "type" },
    { label: "Cmsn", field: "commission" },
    { label: "Pricing", field: "pricing" },
    { label: "Win rate", field: "win_rate" },
    { label: "ESG", field: "esg" },
    { label: "Capacity", field: "capacity" },
    { label: "Appetite", field: "appetite_breadth" },
  ];

  return (
    <div className="grid" style={{ gridTemplateColumns: cols }}>
      {headers.map((h, i) => (
        <div
          key={i}
          onClick={() => h.field && onSort(h.field)}
          className={`
            text-xs text-generate-text-placeholder
            border-b border-generate-text-outline pb-1.5 pt-1.5
            ${h.field ? "cursor-pointer hover:text-generate-text-input" : ""}
            flex items-center gap-1
          `}
        >
          {h.label}
          {h.field === sortField && (
            sortDesc ? <ChevronDown className="generate-app-icon" />
                     : <ChevronUp className="generate-app-icon" />
          )}
        </div>
      ))}
      {carriers.map((c) => (
        <div
          key={c.slug}
          onClick={() => onSelect(c.slug)}
          className="contents cursor-pointer group"
        >
          <div className="text-sm py-2 font-bold group-hover:text-generate-text-input">
            {c.name}
            <div className="text-[10px] font-normal text-generate-text-placeholder mt-0.5">
              {c.specialties.slice(0, 2).join(" · ")}
            </div>
          </div>
          <div className="text-xs py-2 capitalize group-hover:text-generate-text-input">
            {c.type}
          </div>
          <div className="text-sm py-2 font-bold group-hover:text-generate-text-input">
            {c.typical_commission_pct.toFixed(1)}%
          </div>
          <div className="text-xs py-2 group-hover:text-generate-text-input">
            <PricingBadge p={c.pricing_position} />
          </div>
          <div className="text-sm py-2 group-hover:text-generate-text-input">
            <span className="font-bold">{(c.win_rate * 100).toFixed(0)}%</span>
          </div>
          <div className="text-xs py-2">
            <EsgBadge stance={c.esg_stance} />
          </div>
          <div className="text-xs py-2 group-hover:text-generate-text-input">
            {c.capacity_band}
          </div>
          <div className="text-xs py-2">
            <AppetiteBreadthBar appetite={c.appetite_summary} />
          </div>
        </div>
      ))}
    </div>
  );
}


function sortValue(c: CarrierSummary, field: SortField): number {
  switch (field) {
    case "name": return -c.name.charCodeAt(0);
    case "type": return -c.type.charCodeAt(0);
    case "commission": return c.typical_commission_pct;
    case "pricing":
      return c.pricing_position === "tight" ? 3
           : c.pricing_position === "median" ? 2 : 1;
    case "win_rate": return c.win_rate;
    case "esg":
      return c.esg_stance === "leader" ? 4
           : c.esg_stance === "progressive" ? 3
           : c.esg_stance === "neutral" ? 2 : 1;
    case "capacity":
      return c.capacity_band === "Large" ? 3
           : c.capacity_band === "Mid" ? 2 : 1;
    case "appetite_breadth":
      return Object.values(c.appetite_summary)
        .filter((s) => s === "leaning_in" || s === "neutral").length;
  }
}


// ----------------------------------------------------------------------------
// Badges + breadth bar
// ----------------------------------------------------------------------------

function PricingBadge({ p }: { p: PricingPosition }) {
  const tone =
    p === "tight" ? "text-generate-text-good"
    : p === "median" ? "text-generate-text-placeholder"
    : "text-generate-text-bad";
  return <span className={`font-bold capitalize ${tone}`}>{p}</span>;
}

function EsgBadge({ stance }: { stance: EsgStance }) {
  const tone =
    stance === "leader" ? "text-generate-text-good"
    : stance === "progressive" ? "text-generate-text-comment"
    : stance === "neutral" ? "text-generate-text-placeholder"
    : "text-generate-text-bad";
  return (
    <span className={`flex items-center gap-1 font-bold capitalize ${tone}`}>
      <Leaf className="generate-app-icon" /> {stance}
    </span>
  );
}

function AppetiteBreadthBar({ appetite }: { appetite: Record<string, AppetiteStance> }) {
  const lines = Object.entries(appetite);
  return (
    <div className="flex gap-0.5" title={lines.map(([l, s]) => `${l}: ${s.replace(/_/g, " ")}`).join("\n")}>
      {lines.map(([line, stance]) => (
        <span
          key={line}
          className="inline-block h-3 w-2 rounded-sm"
          style={{ backgroundColor: stanceColor(stance) }}
        />
      ))}
    </div>
  );
}

function stanceColor(s: AppetiteStance): string {
  switch (s) {
    case "leaning_in": return "var(--color-generate-text-good)";
    case "neutral": return "var(--color-generate-text-comment)";
    case "selective": return "var(--color-generate-text-maybe)";
    case "leaning_out": return "var(--color-generate-text-bad)";
  }
}


function FilterSelect({
  value, onChange, options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="
        text-xs bg-generate-light-input
        border border-generate-text-outline rounded
        px-2 py-1"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}


// ----------------------------------------------------------------------------
// Carrier detail modal
// ----------------------------------------------------------------------------

function CarrierDetailModal({
  detail, onClose,
}: {
  detail: CarrierDetailResponse | null;
  onClose: () => void;
}) {
  return (
    <Modal
      isOpen={detail !== null}
      onClose={onClose}
      title={detail?.summary.name ?? ""}
      icon={Building2}
    >
      {detail && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <KpiTile
              label="Type"
              value={detail.summary.type}
            />
            <KpiTile
              label="Headquarters"
              value={detail.summary.headquarters}
            />
            <KpiTile
              label="Capacity"
              value={detail.summary.capacity_band}
            />
            <KpiTile
              label="Typical commission"
              value={`${detail.summary.typical_commission_pct.toFixed(1)}%`}
              variant="emphasis"
            />
            <KpiTile
              label="Win rate (market)"
              value={`${(detail.summary.win_rate * 100).toFixed(0)}%`}
            />
            <KpiTile
              label="Your hit rate"
              value={`${detail.your_hit_rate_pct.toFixed(0)}%`}
              subtext={
                detail.your_hit_rate_pct > detail.summary.win_rate * 100
                  ? "Above their market average"
                  : detail.your_hit_rate_pct < detail.summary.win_rate * 100
                  ? "Below their market average"
                  : "On their market average"
              }
              lucideIcon={Trophy}
              variant="emphasis"
            />
          </div>

          <InfoPanel label="Pricing position">
            <p className="text-sm flex items-center gap-2 mt-1">
              <PricingBadge p={detail.summary.pricing_position} />
              <span className="text-xs text-generate-text-placeholder">vs market median</span>
            </p>
          </InfoPanel>

          <InfoPanel label="Appetite" aside={`${detail.appetite.length} lines`}>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {detail.appetite.map((a) => (
                <div key={a.coverage} className="flex items-center gap-2 text-sm">
                  <span
                    className="inline-block h-3 w-3 rounded-sm"
                    style={{ backgroundColor: stanceColor(a.stance) }}
                  />
                  <span className="capitalize">{a.coverage}</span>
                  <span className="text-xs text-generate-text-placeholder capitalize ml-auto">
                    {a.stance.replace(/_/g, " ")}
                  </span>
                </div>
              ))}
            </div>
          </InfoPanel>

          <InfoPanel label="ESG stance" aside={
            <EsgBadge stance={detail.summary.esg_stance} />
          }>
            <p className="text-sm mt-1">{detail.esg_note}</p>
          </InfoPanel>

          <InfoPanel label="Market movement">
            <p className="text-sm mt-1">{detail.movement_note}</p>
          </InfoPanel>

          <InfoPanel label="Specialties">
            <div className="flex flex-wrap gap-2 mt-1">
              {detail.summary.specialties.map((s) => (
                <span
                  key={s}
                  className="
                    text-xs px-2 py-1 rounded-full
                    bg-generate-light-input
                    border border-generate-text-outline
                  "
                >{s}</span>
              ))}
            </div>
          </InfoPanel>

          <InfoPanel label="Your relationship" aside="From the broker's book">
            <LabelValueList
              variant="card"
              rows={[
                {
                  label: "Premium placed (book-weighted)",
                  value: <span className="font-bold">{formatCurrency(detail.your_premium_placed_usd, 0)}</span>,
                },
                {
                  label: "Recent lines",
                  value: detail.your_recent_lines.length > 0
                    ? detail.your_recent_lines.join(", ")
                    : "No recent placements",
                },
              ]}
            />
          </InfoPanel>
        </div>
      )}
    </Modal>
  );
}


// ----------------------------------------------------------------------------
// Shells
// ----------------------------------------------------------------------------

function LoadShell() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Loading" lucideIcon={Building2}>
          <NoData message="Loading carrier intelligence…" />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

function ErrShell({ msg }: { msg: string }) {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Unable to load" lucideIcon={AlertTriangle}>
          <NoData message={msg} />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}

function BrokerOnly() {
  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1">
        <StandardCard title="Broker-only" lucideIcon={AlertTriangle}>
          <NoData message="Carrier Intelligence is for broker users only." />
        </StandardCard>
      </CardGrid>
    </ViewCanvas>
  );
}
