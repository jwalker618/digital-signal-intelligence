# V7 Phase 15: Frontend (Workbench + Calibration UI)

> **Last phase**. Every other phase deliberately defers UI work here so this phase can land independently after `frontend/` styling/refactor is complete. Pre-condition: Phase 14 endpoints exist and return the documented shapes.

## Depends on
- Phase 14 (every endpoint this UI calls is shipped).
- Parallel frontend styling / `generateweb` preparation work — must be merged into the base before Phase 15 starts.

## Blocks
- Nothing in V7.

## Scope

Land every `frontend/**` change required to surface V7 data in the Workbench and to give underwriters a calibration queue. Strict additive policy: no existing tab, route, or shared component changes shape — only extensions and new files. The aim is for this phase to merge cleanly on top of in-flight frontend work without rebase friction.

Three workstreams, one phase because they share consumers:

1. **Visual primitives** — `EvidenceBadge`, `ConfidenceBar`, `ReproducibilityChip`. Three independent axes, three distinct visual idioms.
2. **Workbench extensions** — `EvidenceTab`, `CompositeEvidencePanel`, `PrimitiveHeatmap`, `ProCounterCard`, `MechanismDrawer`, `DisclosurePacketButton`. Plumbed into existing `WorkbenchView.tsx` via an additive tab.
3. **Calibration page** — new `/calibration` route with queue + decision form + stats.

## Decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Grade visual | Coloured badge: `inferred`=grey, `observed`=blue, `corroborated`=teal, `structured_attested`=green, `behaviourally_validated`=emerald. Label always rendered |
| D2 | Confidence visual | Greyscale continuous bar. **Never** the same colour ramp as grade — forces independent reading |
| D3 | Reproducibility visual | Outlined pill chip: `stable`=outline-green, `flaky`=outline-amber, `unstable`=outline-red, `unknown`=outline-grey |
| D4 | Composite panel | Min-grade prominently displayed; distribution bar showing weight share per grade; weighted-mean grade in small print with "display only" tooltip |
| D5 | Primitive heatmap | One row per `primitive_type` × one column per grade. Cell intensity = share of weight at that intersection |
| D6 | Pro/counter card | Side-by-side panels under the signal detail drawer: pro on left, counter on right, tie-breaker below |
| D7 | Calibration page | New route `/calibration`. Scoped to user's coverage. One-click decision via radio + note |
| D8 | Mechanism drawer | Right-side drawer reachable from the validator card; shows recalled mechanisms with summary + tags |
| D9 | Disclosure button | Only visible on referred submissions; POSTs to disclosure endpoint, shows Markdown in a modal with copy buttons |
| D10 | Additive policy | No existing tab/route/shared-component **shape** changes. New files plus minimal additive edits to `WorkbenchView.tsx` and `frontend/src/types/dsi.ts` |
| D11 | Test fixtures | Tests prefer in-memory mocks of the Phase 14 endpoint shapes to keep the frontend test runner offline |
| D12 | Style system | Re-uses the existing Tailwind tokens. No new design-system entries, no new icon-set imports, no new fonts |
| D13 | Pre-merge gate | A `git diff --stat HEAD~1 HEAD -- frontend/` summary is reviewed before merge to confirm the additive policy held |

## Files

### Create
- `frontend/src/types/evidence.ts`
- `frontend/src/components/submissions/Workbench/EvidenceBadge.tsx`
- `frontend/src/components/submissions/Workbench/ConfidenceBar.tsx`
- `frontend/src/components/submissions/Workbench/ReproducibilityChip.tsx`
- `frontend/src/components/submissions/Workbench/EvidenceTab.tsx`
- `frontend/src/components/submissions/Workbench/CompositeEvidencePanel.tsx`
- `frontend/src/components/submissions/Workbench/PrimitiveHeatmap.tsx`
- `frontend/src/components/submissions/Workbench/ProCounterCard.tsx`
- `frontend/src/components/submissions/Workbench/MechanismDrawer.tsx`
- `frontend/src/components/submissions/Workbench/DisclosurePacketButton.tsx`
- `frontend/src/components/submissions/Workbench/SignalRowEvidence.tsx` — encapsulates the three-axis row (badge + bar + chip) so it can be slotted in without restructuring the existing ledger row
- `frontend/src/app/calibration/page.tsx`
- `frontend/src/components/calibration/CalibrationQueue.tsx`
- `frontend/src/components/calibration/DecisionForm.tsx`
- `frontend/src/components/calibration/CalibrationStats.tsx`
- `frontend/src/lib/api/evidence.ts` — typed fetchers
- `frontend/src/lib/api/calibration.ts`
- `frontend/src/lib/api/disclosure.ts`
- `frontend/src/lib/api/mechanism.ts`
- `frontend/src/__tests__/EvidenceBadge.test.tsx`
- `frontend/src/__tests__/ConfidenceBar.test.tsx`
- `frontend/src/__tests__/ReproducibilityChip.test.tsx`
- `frontend/src/__tests__/CompositeEvidencePanel.test.tsx`
- `frontend/src/__tests__/CalibrationQueue.test.tsx`
- `frontend/src/__tests__/visual_independence.test.tsx` — asserts grade vs confidence are visually distinct

### Modify (additive only)
- `frontend/src/types/dsi.ts` — append: extra Optional fields on `ModelVersion`, `SignalCondition`; new `EvidenceGrade`, `Reproducibility` type aliases re-exported from `evidence.ts`
- `frontend/src/components/submissions/Workbench/WorkbenchView.tsx` — register a new `<EvidenceTab />` in the existing tab list. No other change

### Explicitly NOT modified
- Any layout primitive, theme file, or top-level shell component
- Any existing tab content
- Any auth / routing / store wiring beyond the new `/calibration` route entry

## Types

`frontend/src/types/evidence.ts`:

```typescript
export type EvidenceGrade =
  | "inferred"
  | "observed"
  | "corroborated"
  | "structured_attested"
  | "behaviourally_validated";

export type Reproducibility = "stable" | "flaky" | "unstable" | "unknown";

export type AbsenceSubType =
  | "absence_failed_fetch"
  | "absence_authoritative_empty"
  | null;

export interface EvidenceSource {
  source_id: string;
  kind: string;
  ref: string;
  fetched_at: string;
  response_hash?: string | null;
  notes?: string;
}

export interface SignalEvidence {
  signal_id: string;
  score?: number | null;
  category?: string | null;
  confidence: number;
  evidence_grade?: EvidenceGrade | null;
  evidence_basis?: string | null;
  evidence_sources: EvidenceSource[];
  evidence_pro?: string | null;
  evidence_counter?: string | null;
  evidence_tie_breaker?: string | null;
  absence_sub_type?: AbsenceSubType;
  primitive_type?: string | null;
  reproducibility?: Reproducibility | null;
  variant_of?: string | null;
  cluster_id?: string | null;
}

export interface GradeRollup {
  min_grade: EvidenceGrade | null;
  weighted_mean_grade: number | null;
  distribution: Partial<Record<EvidenceGrade, number>>;
}

export interface CompositeEvidence {
  composite: GradeRollup;
  per_group: Record<string, GradeRollup>;
  per_primitive: Record<string, GradeRollup>;
  grade_referral_reasons: string[];
}

export interface CalibrationSample {
  id: string;
  submission_id: string;
  coverage: string;
  signal_id: string;
  signal_weight: number;
  extractor_grade: EvidenceGrade;
  validator_grade: EvidenceGrade | null;
  sampling_reason: "high_weight_referred" | "stratified_random";
  created_at: string;
  expires_at: string;
  state: "pending" | "decided" | "expired";
}

export interface Mechanism {
  id: string;
  summary: string;
  primitive_type: string;
  sector_tags: string[];
  tags: string[];
  what_made_it_high_grade: string;
  recall_count: number;
}
```

`frontend/src/types/dsi.ts` — append (do not edit existing exports):

```typescript
// V7 additions — additive only.
export type { EvidenceGrade, Reproducibility } from "./evidence";

// Existing `ModelVersion` — extend via interface declaration merging if needed,
// or update its definition in-place to add the V7 optional fields. The set:
//   composite_min_grade?: EvidenceGrade | null;
//   composite_weighted_mean_grade?: number | null;
//   composite_grade_distribution?: Partial<Record<EvidenceGrade, number>>;
// All Optional — no consumer breaks.
```

## API fetchers

`frontend/src/lib/api/evidence.ts`:

```typescript
import type { CompositeEvidence, SignalEvidence } from "@/types/evidence";

const BASE = "/api/v1/model-versions";

export async function fetchCompositeEvidence(mvId: string): Promise<CompositeEvidence> {
  const res = await fetch(`${BASE}/${mvId}/evidence`, { credentials: "include" });
  if (!res.ok) throw new Error(`composite evidence fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchSignalEvidence(mvId: string, signalId: string): Promise<SignalEvidence> {
  const res = await fetch(`${BASE}/${mvId}/signals/${encodeURIComponent(signalId)}`,
                          { credentials: "include" });
  if (!res.ok) throw new Error(`signal evidence fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchSignalHistory(mvId: string, signalId: string, limit = 50) {
  const res = await fetch(
    `${BASE}/${mvId}/signals/${encodeURIComponent(signalId)}/history?limit=${limit}`,
    { credentials: "include" },
  );
  if (!res.ok) throw new Error(`history fetch failed: ${res.status}`);
  return res.json();
}
```

`frontend/src/lib/api/calibration.ts`:

```typescript
import type { CalibrationSample } from "@/types/evidence";

const BASE = "/api/v1/calibration";

export async function fetchPending(coverage?: string, limit = 50): Promise<CalibrationSample[]> {
  const qs = new URLSearchParams();
  if (coverage) qs.set("coverage", coverage);
  qs.set("limit", String(limit));
  const res = await fetch(`${BASE}/pending?${qs}`, { credentials: "include" });
  if (!res.ok) throw new Error(`pending fetch failed: ${res.status}`);
  return res.json();
}

export async function submitDecision(sampleId: string, humanGrade: string, note = "") {
  const res = await fetch(`${BASE}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ sample_id: sampleId, human_grade: humanGrade, note }),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`decision submit failed: ${res.status} ${t}`);
  }
}

export async function fetchStats(coverage?: string, windowDays: number | null = 30) {
  const qs = new URLSearchParams();
  if (coverage) qs.set("coverage", coverage);
  if (windowDays != null) qs.set("window_days", String(windowDays));
  const res = await fetch(`${BASE}/stats?${qs}`, { credentials: "include" });
  if (!res.ok) throw new Error(`stats fetch failed: ${res.status}`);
  return res.json();
}
```

`frontend/src/lib/api/disclosure.ts`:

```typescript
export async function generatePacket(mvId: string, format: "json" | "md" = "json") {
  const res = await fetch(
    `/api/v1/model-versions/${mvId}/disclosure-packet?format=${format}`,
    { method: "POST", credentials: "include" },
  );
  if (!res.ok) throw new Error(`packet generation failed: ${res.status}`);
  if (format === "md") return { markdown: await res.text(), payload: null as any };
  return res.json() as Promise<{ markdown: string; payload: any }>;
}
```

`frontend/src/lib/api/mechanism.ts`:

```typescript
import type { Mechanism } from "@/types/evidence";

export async function fetchMechanismsForSignal(mvId: string, signalId: string): Promise<Mechanism[]> {
  const res = await fetch(
    `/api/v1/model-versions/${mvId}/signals/${encodeURIComponent(signalId)}/mechanisms`,
    { credentials: "include" },
  );
  if (!res.ok) throw new Error(`mechanism fetch failed: ${res.status}`);
  return res.json();
}
```

## Visual primitives

`EvidenceBadge.tsx`:

```tsx
import type { EvidenceGrade } from "@/types/evidence";

const COLOURS: Record<EvidenceGrade, string> = {
  inferred:                "bg-zinc-200 text-zinc-700",
  observed:                "bg-blue-200 text-blue-900",
  corroborated:            "bg-teal-200 text-teal-900",
  structured_attested:     "bg-green-300 text-green-900",
  behaviourally_validated: "bg-emerald-400 text-emerald-950",
};

export function EvidenceBadge({ grade }: { grade?: EvidenceGrade | null }) {
  if (!grade) return <span data-testid="evidence-badge-empty" className="text-zinc-400 text-xs">—</span>;
  return (
    <span
      data-testid="evidence-badge"
      data-grade={grade}
      className={`px-2 py-0.5 rounded-md text-xs font-mono ${COLOURS[grade]}`}
    >
      {grade.replace(/_/g, " ")}
    </span>
  );
}
```

`ConfidenceBar.tsx`:

```tsx
export function ConfidenceBar({ value }: { value: number }) {
  // Deliberately greyscale — never colour. Forces the user to read grade
  // and confidence as independent axes (Phase 15 D2).
  const pct = Math.round(Math.min(1, Math.max(0, value)) * 100);
  return (
    <div
      data-testid="confidence-bar"
      data-value={pct}
      className="w-24 h-2 bg-zinc-100 rounded overflow-hidden"
      title={`${pct}% confidence`}
    >
      <div className="h-full bg-zinc-600" style={{ width: `${pct}%` }} />
    </div>
  );
}
```

`ReproducibilityChip.tsx`:

```tsx
import type { Reproducibility } from "@/types/evidence";

const RING: Record<Reproducibility, string> = {
  stable:   "ring-green-500 text-green-700",
  flaky:    "ring-amber-500 text-amber-700",
  unstable: "ring-red-500 text-red-700",
  unknown:  "ring-zinc-400 text-zinc-500",
};

export function ReproducibilityChip({ value }: { value?: Reproducibility | null }) {
  const v = value ?? "unknown";
  return (
    <span
      data-testid="reproducibility-chip"
      data-value={v}
      className={`px-1.5 py-0.5 text-[10px] uppercase tracking-wide font-semibold rounded-full bg-transparent ring-1 ${RING[v]}`}
    >
      {v}
    </span>
  );
}
```

## Composite panel

`CompositeEvidencePanel.tsx`:

```tsx
import { EvidenceBadge } from "./EvidenceBadge";
import type { CompositeEvidence, EvidenceGrade } from "@/types/evidence";

const ORDER: EvidenceGrade[] = [
  "behaviourally_validated", "structured_attested", "corroborated", "observed", "inferred",
];

export function CompositeEvidencePanel({ data }: { data: CompositeEvidence }) {
  return (
    <section data-testid="composite-evidence" className="border rounded-lg p-4 space-y-3">
      <header className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Composite evidence</h3>
        <EvidenceBadge grade={data.composite.min_grade} />
      </header>
      <div className="space-y-1">
        {ORDER.map((g) => {
          const w = (data.composite.distribution[g] ?? 0) * 100;
          if (w <= 0) return null;
          return (
            <div key={g} className="flex items-center gap-2">
              <div className="w-32 text-xs"><EvidenceBadge grade={g} /></div>
              <div className="flex-1 h-3 bg-zinc-100 rounded overflow-hidden">
                <div className="h-full bg-zinc-600" style={{ width: `${w}%` }} />
              </div>
              <div className="w-10 text-right text-xs tabular-nums">{Math.round(w)}%</div>
            </div>
          );
        })}
      </div>
      {data.grade_referral_reasons.length > 0 && (
        <ul className="text-xs text-amber-700 list-disc ml-4">
          {data.grade_referral_reasons.map((r) => <li key={r}>{r}</li>)}
        </ul>
      )}
      {data.composite.weighted_mean_grade != null && (
        <p
          className="text-[10px] text-zinc-400"
          title="Cardinal arithmetic over an ordinal taxonomy. Display only."
        >
          weighted mean (display only): {data.composite.weighted_mean_grade.toFixed(2)}
        </p>
      )}
    </section>
  );
}
```

## Pro/counter card

`ProCounterCard.tsx`:

```tsx
import type { SignalEvidence } from "@/types/evidence";

export function ProCounterCard({ sig }: { sig: SignalEvidence }) {
  if (!sig.evidence_pro && !sig.evidence_counter) return null;
  return (
    <div data-testid="pro-counter-card" className="grid grid-cols-2 gap-3 my-3">
      <div className="border border-green-200 rounded-lg p-3 bg-green-50">
        <h4 className="text-xs font-bold text-green-800 uppercase tracking-wide mb-1">Pro</h4>
        <p className="text-sm whitespace-pre-wrap">{sig.evidence_pro ?? "—"}</p>
      </div>
      <div className="border border-red-200 rounded-lg p-3 bg-red-50">
        <h4 className="text-xs font-bold text-red-800 uppercase tracking-wide mb-1">Counter</h4>
        <p className="text-sm whitespace-pre-wrap">{sig.evidence_counter ?? "—"}</p>
      </div>
      {sig.evidence_tie_breaker && (
        <div className="col-span-2 border border-zinc-200 rounded-lg p-3 bg-zinc-50">
          <h4 className="text-xs font-bold text-zinc-700 uppercase tracking-wide mb-1">Tie-breaker</h4>
          <p className="text-sm whitespace-pre-wrap">{sig.evidence_tie_breaker}</p>
        </div>
      )}
    </div>
  );
}
```

## Signal-row encapsulation

`SignalRowEvidence.tsx`:

```tsx
import { EvidenceBadge } from "./EvidenceBadge";
import { ConfidenceBar } from "./ConfidenceBar";
import { ReproducibilityChip } from "./ReproducibilityChip";
import type { SignalEvidence } from "@/types/evidence";

export function SignalRowEvidence({ sig }: { sig: SignalEvidence }) {
  return (
    <div className="flex items-center gap-2" data-testid="signal-row-evidence">
      <EvidenceBadge grade={sig.evidence_grade} />
      <ConfidenceBar value={sig.confidence} />
      <ReproducibilityChip value={sig.reproducibility} />
    </div>
  );
}
```

Existing signal-ledger rows opt in by slotting `<SignalRowEvidence sig={…} />` into their existing layout — no row restructuring required.

## Workbench tab

`EvidenceTab.tsx`:

```tsx
import { useEffect, useState } from "react";
import { fetchCompositeEvidence } from "@/lib/api/evidence";
import type { CompositeEvidence } from "@/types/evidence";
import { CompositeEvidencePanel } from "./CompositeEvidencePanel";
import { PrimitiveHeatmap } from "./PrimitiveHeatmap";

export function EvidenceTab({ modelVersionId }: { modelVersionId: string }) {
  const [data, setData] = useState<CompositeEvidence | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchCompositeEvidence(modelVersionId)
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(String(e)));
    return () => { cancelled = true; };
  }, [modelVersionId]);

  if (error) return <p className="text-red-700 text-sm">{error}</p>;
  if (!data) return <p className="text-zinc-500 text-sm">Loading…</p>;

  return (
    <div className="space-y-4">
      <CompositeEvidencePanel data={data} />
      <PrimitiveHeatmap perPrimitive={data.per_primitive} />
    </div>
  );
}
```

`PrimitiveHeatmap.tsx`:

```tsx
import type { GradeRollup, EvidenceGrade } from "@/types/evidence";

const GRADES: EvidenceGrade[] = [
  "inferred", "observed", "corroborated", "structured_attested", "behaviourally_validated",
];

export function PrimitiveHeatmap({ perPrimitive }: { perPrimitive: Record<string, GradeRollup> }) {
  const primitives = Object.keys(perPrimitive).sort();
  if (!primitives.length) return null;
  return (
    <section data-testid="primitive-heatmap" className="border rounded-lg p-4">
      <h3 className="text-sm font-semibold mb-3">Grade by risk primitive</h3>
      <table className="w-full text-xs">
        <thead>
          <tr>
            <th className="text-left font-medium">primitive</th>
            {GRADES.map((g) => <th key={g} className="text-center font-mono">{g.replace(/_/g, " ")}</th>)}
          </tr>
        </thead>
        <tbody>
          {primitives.map((p) => {
            const r = perPrimitive[p];
            return (
              <tr key={p}>
                <td className="py-1">{p}</td>
                {GRADES.map((g) => {
                  const w = (r.distribution[g] ?? 0) * 100;
                  const intensity = Math.min(100, Math.round(w));
                  return (
                    <td key={g} className="px-1">
                      <div
                        className="h-5 rounded"
                        style={{ background: `rgba(20, 83, 45, ${intensity / 100})` }}
                        title={`${p} · ${g}: ${Math.round(w)}%`}
                      />
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
```

## Mechanism drawer

`MechanismDrawer.tsx`:

```tsx
import { useEffect, useState } from "react";
import { fetchMechanismsForSignal } from "@/lib/api/mechanism";
import type { Mechanism } from "@/types/evidence";

export function MechanismDrawer({ open, mvId, signalId, onClose }:
  { open: boolean; mvId: string; signalId: string; onClose: () => void }) {
  const [items, setItems] = useState<Mechanism[]>([]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    fetchMechanismsForSignal(mvId, signalId)
      .then((d) => !cancelled && setItems(d))
      .catch(() => !cancelled && setItems([]));
    return () => { cancelled = true; };
  }, [open, mvId, signalId]);

  if (!open) return null;
  return (
    <aside data-testid="mechanism-drawer" className="fixed right-0 top-0 h-full w-96 bg-white border-l shadow-lg p-4 overflow-y-auto">
      <header className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-semibold">Mechanism priors</h3>
        <button onClick={onClose} className="text-xs underline">close</button>
      </header>
      {items.length === 0 && <p className="text-xs text-zinc-500">no priors recalled</p>}
      <ul className="space-y-3">
        {items.map((m) => (
          <li key={m.id} className="border rounded p-2 text-xs">
            <p className="font-medium">{m.summary}</p>
            <p className="text-zinc-500 mt-1">{m.tags.join(", ")}</p>
            <p className="text-zinc-400 mt-1">recall_count: {m.recall_count}</p>
          </li>
        ))}
      </ul>
    </aside>
  );
}
```

## Disclosure button

`DisclosurePacketButton.tsx`:

```tsx
import { useState } from "react";
import { generatePacket } from "@/lib/api/disclosure";

export function DisclosurePacketButton({ mvId }: { mvId: string }) {
  const [open, setOpen] = useState(false);
  const [md, setMd] = useState<string>("");

  async function onClick() {
    const { markdown } = await generatePacket(mvId, "json");
    setMd(markdown);
    setOpen(true);
  }

  function copy() { navigator.clipboard.writeText(md).catch(() => undefined); }

  return (
    <>
      <button onClick={onClick} className="px-3 py-1 text-xs border rounded hover:bg-zinc-50">
        Generate disclosure packet
      </button>
      {open && (
        <div data-testid="disclosure-modal" className="fixed inset-0 bg-black/40 flex items-center justify-center p-6">
          <div className="bg-white max-w-3xl w-full rounded-lg p-4 max-h-[80vh] overflow-auto">
            <header className="flex justify-between items-center mb-2">
              <h3 className="font-semibold text-sm">Disclosure packet</h3>
              <div className="flex gap-2">
                <button onClick={copy} className="text-xs underline">copy markdown</button>
                <button onClick={() => setOpen(false)} className="text-xs underline">close</button>
              </div>
            </header>
            <pre className="text-xs whitespace-pre-wrap font-mono">{md}</pre>
          </div>
        </div>
      )}
    </>
  );
}
```

## Calibration page

`frontend/src/app/calibration/page.tsx`:

```tsx
import { CalibrationQueue } from "@/components/calibration/CalibrationQueue";
import { CalibrationStats } from "@/components/calibration/CalibrationStats";

export default function CalibrationPage() {
  return (
    <main className="p-6 space-y-6 max-w-4xl mx-auto">
      <h1 className="text-lg font-semibold">Calibration queue</h1>
      <CalibrationStats />
      <CalibrationQueue />
    </main>
  );
}
```

`CalibrationQueue.tsx`:

```tsx
"use client";
import { useEffect, useState } from "react";
import { fetchPending } from "@/lib/api/calibration";
import type { CalibrationSample } from "@/types/evidence";
import { DecisionForm } from "./DecisionForm";

export function CalibrationQueue() {
  const [items, setItems] = useState<CalibrationSample[]>([]);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      setItems(await fetchPending());
    } catch (e) {
      setErr(String(e));
    }
  }
  useEffect(() => { load(); }, []);

  if (err) return <p className="text-red-700 text-sm">{err}</p>;
  if (!items.length) return <p className="text-zinc-500 text-sm">queue empty</p>;

  return (
    <div className="space-y-3">
      {items.map((s) => (
        <article key={s.id} className="border rounded-lg p-3" data-testid="calibration-sample">
          <header className="flex justify-between text-xs text-zinc-600 mb-2">
            <span><code>{s.signal_id}</code> · {s.coverage}</span>
            <span>weight {(s.signal_weight * 100).toFixed(0)}%</span>
          </header>
          <p className="text-xs mb-2">
            extractor: <strong>{s.extractor_grade}</strong>
            {s.validator_grade && <> · validator: <strong>{s.validator_grade}</strong></>}
            <> · reason: <em>{s.sampling_reason}</em></>
          </p>
          <DecisionForm sample={s} onDecided={load} />
        </article>
      ))}
    </div>
  );
}
```

`DecisionForm.tsx`:

```tsx
"use client";
import { useState } from "react";
import { submitDecision } from "@/lib/api/calibration";
import type { CalibrationSample, EvidenceGrade } from "@/types/evidence";

const GRADES: EvidenceGrade[] = [
  "inferred", "observed", "corroborated", "structured_attested", "behaviourally_validated",
];

export function DecisionForm({ sample, onDecided }:
  { sample: CalibrationSample; onDecided: () => void }) {
  const [grade, setGrade] = useState<EvidenceGrade | "">("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!grade) return;
    setBusy(true); setError(null);
    try {
      await submitDecision(sample.id, grade, note);
      onDecided();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {GRADES.map((g) => (
          <label key={g} className={`px-2 py-0.5 text-xs border rounded cursor-pointer ${grade === g ? "bg-zinc-900 text-white" : ""}`}>
            <input
              type="radio" name={`grade-${sample.id}`} value={g}
              checked={grade === g} onChange={() => setGrade(g)} className="hidden"
            />
            {g.replace(/_/g, " ")}
          </label>
        ))}
      </div>
      <textarea
        value={note} onChange={(e) => setNote(e.target.value)}
        className="w-full border rounded p-1 text-xs" rows={2} placeholder="optional note"
      />
      <button
        disabled={!grade || busy}
        onClick={submit}
        className="px-3 py-1 text-xs border rounded disabled:opacity-50"
      >
        {busy ? "submitting…" : "submit decision"}
      </button>
      {error && <p className="text-red-700 text-xs">{error}</p>}
    </div>
  );
}
```

`CalibrationStats.tsx`:

```tsx
"use client";
import { useEffect, useState } from "react";
import { fetchStats } from "@/lib/api/calibration";

export function CalibrationStats() {
  const [s, setS] = useState<any>(null);
  useEffect(() => { fetchStats().then(setS).catch(() => setS(null)); }, []);
  if (!s) return null;
  return (
    <section data-testid="calibration-stats" className="border rounded-lg p-3 text-xs grid grid-cols-3 gap-3">
      <div><strong>decided (30d)</strong>: {s.decided}</div>
      <div><strong>exact (extractor)</strong>: {(s.exact_match_extractor_rate * 100).toFixed(1)}%</div>
      <div><strong>within-1</strong>: {(s.within_one_extractor_rate * 100).toFixed(1)}%</div>
    </section>
  );
}
```

## Workbench integration

`WorkbenchView.tsx` — the only edit:

```tsx
// Register the new tab. Do not change other tabs.
import { EvidenceTab } from "./EvidenceTab";

const TABS = [
  // … existing tabs …
  { id: "evidence", label: "Evidence", render: (props) => <EvidenceTab modelVersionId={props.mvId} /> },
];
```

In the per-signal drawer the existing code already opens, add (additive only):

```tsx
import { ProCounterCard } from "./ProCounterCard";
import { MechanismDrawer } from "./MechanismDrawer";
import { DisclosurePacketButton } from "./DisclosurePacketButton";

// inside the existing drawer body:
<ProCounterCard sig={signalEvidence} />
<DisclosurePacketButton mvId={mvId} />
<MechanismDrawer open={drawerOpen} mvId={mvId} signalId={sig.signal_id} onClose={() => setDrawerOpen(false)} />
```

## Visual-independence test

`__tests__/visual_independence.test.tsx`:

```tsx
import { render } from "@testing-library/react";
import { EvidenceBadge } from "@/components/submissions/Workbench/EvidenceBadge";
import { ConfidenceBar } from "@/components/submissions/Workbench/ConfidenceBar";
import { ReproducibilityChip } from "@/components/submissions/Workbench/ReproducibilityChip";

test("grade and confidence render with distinct test-ids and different element kinds", () => {
  const { getByTestId } = render(
    <div>
      <EvidenceBadge grade="observed" />
      <ConfidenceBar value={0.75} />
      <ReproducibilityChip value="stable" />
    </div>,
  );
  const badge = getByTestId("evidence-badge");
  const bar   = getByTestId("confidence-bar");
  const chip  = getByTestId("reproducibility-chip");
  expect(badge).not.toBe(bar);
  expect(badge).not.toBe(chip);
  expect(bar).not.toBe(chip);
  expect(badge.tagName).toBe("SPAN");
  expect(bar.tagName).toBe("DIV");
  expect(chip.tagName).toBe("SPAN");
  expect(badge.getAttribute("data-grade")).toBe("observed");
  expect(bar.getAttribute("data-value")).toBe("75");
  expect(chip.getAttribute("data-value")).toBe("stable");
});
```

## Steps

### 15.1 — Types and fetchers
**Files**: `frontend/src/types/evidence.ts`, `frontend/src/lib/api/{evidence,calibration,disclosure,mechanism}.ts`.
**Action**: Drop in code. Run `tsc --noEmit`.

### 15.2 — Visual primitives + unit tests
**Files**: `EvidenceBadge.tsx`, `ConfidenceBar.tsx`, `ReproducibilityChip.tsx`, the three unit tests, and `visual_independence.test.tsx`.
**Action**: Confirm three distinct test-ids and three distinct DOM elements.

### 15.3 — Composite + primitive panels
**Files**: `CompositeEvidencePanel.tsx`, `PrimitiveHeatmap.tsx`, their tests.

### 15.4 — Drawer pieces
**Files**: `ProCounterCard.tsx`, `MechanismDrawer.tsx`, `DisclosurePacketButton.tsx`, `SignalRowEvidence.tsx`.

### 15.5 — Evidence tab + WorkbenchView edits
**Files**: `EvidenceTab.tsx`, additive edits to `WorkbenchView.tsx`.

### 15.6 — Calibration page
**Files**: `app/calibration/page.tsx`, `CalibrationQueue.tsx`, `DecisionForm.tsx`, `CalibrationStats.tsx`, `CalibrationQueue.test.tsx`.

### 15.7 — Type-extension on `dsi.ts`
**File**: `frontend/src/types/dsi.ts`.
**Action**: Append the `EvidenceGrade` / `Reproducibility` re-exports and the optional V7 fields on `ModelVersion`. **Do not delete or rename any existing export.**

### 15.8 — Pre-merge additive-policy check
**Action**: Before merging, run:
```bash
git diff --stat $BASE..HEAD -- frontend/ | tee /tmp/phase15-frontend-diff.txt
# Manual review: no existing file other than dsi.ts + WorkbenchView.tsx should
# appear with changes. Net additions only, except for those two files.
```

## Test gates

```bash
cd frontend
npm test -- --runInBand
npm run build

# Bundle-size smoke (no new design-system entries)
ls -la dist || true

# Confirm no shared shell / theme / store file changed
git diff --name-only $BASE..HEAD -- \
  frontend/src/styles/ frontend/src/lib/auth frontend/src/store frontend/src/app/layout.tsx \
  | wc -l
# Expected: 0
```

## Done when

- [ ] Three visual primitives render with three distinct test-ids and three different element types.
- [ ] `EvidenceTab` registered alongside existing Workbench tabs; existing tabs unchanged.
- [ ] `/calibration` route renders queue, decision form, and stats.
- [ ] Pro/counter card, mechanism drawer, disclosure button reachable from the existing signal drawer.
- [ ] `frontend` test suite green; `npm run build` green.
- [ ] Pre-merge additive-policy check: no shared shell / theme / store / layout file changed.

## Out of scope

- New design-system tokens, fonts, icon imports, or theme entries.
- Mobile responsiveness tuning beyond default flex/grid behaviour.
- Portfolio-wide disclosure export. → V8.
- A/B testing alternate grade encodings. → V8.

## Invariants

1. No file outside `frontend/src/{types/dsi.ts, components/submissions/Workbench/WorkbenchView.tsx}` that existed pre-V7 is modified — only created.
2. Grade and confidence render as visually independent elements with distinct DOM types.
3. Reproducibility renders as a third, distinct chip.
4. The weighted-mean grade is rendered only as supplementary text with a "display only" cue.
5. No theme, layout, or store file is touched.
