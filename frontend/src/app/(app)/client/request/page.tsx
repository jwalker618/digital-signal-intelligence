"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { CheckCircle2, ChevronDown, ShieldPlus, Loader2 } from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import { Button } from "@/components/ui/button";
import { Eyebrow, Body, Micro } from "@/components/ui/typography";
import { PageError, PageLoading, RoleGate } from "@/components/base/pageStates";
import { useRoleScopedFetch } from "@/lib/useRoleScopedFetch";
import { fetchOverview, postCoverageRequest } from "@/lib/portalApi";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";
import type {
  CoverageRequestPayload,
  CoverageRequestResponse,
  OverviewResponse,
} from "@/types/portal";

const SUGGESTED_LINES = [
  "Cyber",
  "Professional Indemnity",
  "Directors & Officers",
  "Property",
  "General Liability",
  "Workers Compensation",
  "Umbrella",
  "Crime",
  "Product Liability",
  "Employment Practices",
];

export default function ClientRequestPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const enabled = !!accessToken && user?.role === "CLIENT";

  const overview = useRoleScopedFetch<OverviewResponse>({
    fetcher: () => fetchOverview(accessToken),
    enabled,
    deps: [accessToken],
  });

  if (!user) return <PageLoading message="Signing in…" />;
  if (user.role && user.role !== "CLIENT") return <RoleGate expected="client" />;
  if (overview.loading) return <PageLoading />;
  if (overview.error) return <PageError message={overview.error} />;
  if (!overview.data || overview.data.role !== "CLIENT")
    return <RoleGate expected="client" />;

  const held = new Set(
    overview.data.active_coverages.map((c) => c.coverage.toLowerCase()),
  );
  const gaps = SUGGESTED_LINES.filter((l) => !held.has(l.toLowerCase()));

  return (
    <RequestBody
      entityName={overview.data.entity_name}
      brokerName={overview.data.broker?.name ?? null}
      gaps={gaps}
    />
  );
}

function RequestBody({
  entityName,
  brokerName,
  gaps,
}: {
  entityName: string;
  brokerName: string | null;
  gaps: string[];
}) {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);

  const [coverage, setCoverage] = useState("");
  const [desiredLimit, setDesiredLimit] = useState("");
  const [effectiveDate, setEffectiveDate] = useState("");
  const [rationale, setRationale] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<CoverageRequestResponse | null>(null);

  const canSubmit = coverage.trim().length > 0 && !submitting;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload: CoverageRequestPayload = {
        coverage: coverage.trim(),
        desired_limit: desiredLimit ? Number(desiredLimit) : null,
        desired_effective_date: effectiveDate || null,
        rationale: rationale.trim() || undefined,
      };
      const resp = await postCoverageRequest(accessToken, payload);
      setSuccess(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't submit request.");
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <>
        <Topbar
          crumbs={["Client Portal", "Request Coverage"]}
          entity={entityName}
        />
        <div className="flex flex-1 items-start justify-center px-9 py-12">
          <Card variant="pos" pad="lg" className="max-w-xl space-y-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-pos text-canvas">
              <CheckCircle2 size={20} />
            </div>
            <div>
              <Eyebrow className="text-pos">Submitted</Eyebrow>
              <h1 className="mt-1 font-display text-[24px] font-semibold text-ink">
                Request {success.request_code} sent
              </h1>
              <Body className="mt-2">
                {brokerName ? brokerName : "Your broker"} will pick this up and
                draft a submission. You can track the conversation in
                Communications.
              </Body>
            </div>
            <div className="flex gap-3">
              <Button
                variant="primary"
                onClick={() =>
                  router.push(`/client/communications/${success.referral_code}`)
                }
              >
                Open thread
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setSuccess(null);
                  setCoverage("");
                  setDesiredLimit("");
                  setEffectiveDate("");
                  setRationale("");
                }}
              >
                Submit another
              </Button>
            </div>
          </Card>
        </div>
      </>
    );
  }

  return (
    <>
      <Topbar
        crumbs={["Client Portal", "Request Coverage"]}
        entity={entityName}
      />
      <div className="flex-1 overflow-y-auto px-9 py-7">
        <div className="mx-auto grid max-w-[1024px] gap-6 lg:grid-cols-[1fr_320px]">
          <Card pad="lg" className="space-y-5">
            <header>
              <Eyebrow>New request</Eyebrow>
              <h1 className="mt-1 font-display text-[28px] font-semibold leading-tight text-ink">
                Request coverage
              </h1>
              <Body className="mt-2">
                We'll forward this to{" "}
                <span className="font-semibold text-ink">
                  {brokerName ?? "your broker"}
                </span>
                . You'll see their reply in Communications.
              </Body>
            </header>

            <form className="space-y-5" onSubmit={onSubmit}>
              <Field id="coverage" label="Coverage line" required>
                <input
                  id="coverage"
                  type="text"
                  required
                  value={coverage}
                  onChange={(e) => setCoverage(e.target.value)}
                  list="suggested-lines"
                  placeholder="e.g. Cyber, D&O, Property…"
                  className={inputClass}
                />
                <datalist id="suggested-lines">
                  {SUGGESTED_LINES.map((l) => (
                    <option key={l} value={l} />
                  ))}
                </datalist>
              </Field>

              <div className="grid gap-5 md:grid-cols-2">
                <Field id="limit" label="Desired limit (USD)">
                  <input
                    id="limit"
                    type="number"
                    inputMode="numeric"
                    min={0}
                    step={100_000}
                    value={desiredLimit}
                    onChange={(e) => setDesiredLimit(e.target.value)}
                    placeholder="5,000,000"
                    className={inputClass}
                  />
                </Field>
                <Field id="effective" label="Effective date">
                  <input
                    id="effective"
                    type="date"
                    value={effectiveDate}
                    onChange={(e) => setEffectiveDate(e.target.value)}
                    className={inputClass}
                  />
                </Field>
              </div>

              <Field
                id="rationale"
                label="Rationale"
                hint="What's driving this — new exposure, growth, peer benchmark, contractual requirement, etc."
              >
                <textarea
                  id="rationale"
                  rows={5}
                  value={rationale}
                  onChange={(e) => setRationale(e.target.value)}
                  placeholder="Optional but speeds up your broker's response."
                  className={cn(inputClass, "h-auto resize-y py-2.5 leading-[1.55]")}
                />
              </Field>

              {error && (
                <div
                  role="alert"
                  className="rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg"
                >
                  {error}
                </div>
              )}

              <div className="flex items-center gap-3">
                <Button type="submit" disabled={!canSubmit} size="lg">
                  {submitting ? (
                    <>
                      <Loader2 size={15} className="animate-spin" />
                      Submitting…
                    </>
                  ) : (
                    <>
                      <ShieldPlus size={15} />
                      Send request
                    </>
                  )}
                </Button>
                <Micro>Posts to /portal/coverage-requests</Micro>
              </div>
            </form>
          </Card>

          <aside className="space-y-5">
            <Card variant="info" pad="md">
              <Eyebrow className="text-info-deep dark:text-info">
                Cohort gaps
              </Eyebrow>
              {gaps.length === 0 ? (
                <Body className="mt-2 italic">
                  Your book already spans every line we typically see for your
                  cohort.
                </Body>
              ) : (
                <>
                  <Body className="mt-1.5 text-ink">
                    Lines your cohort typically holds that you don't:
                  </Body>
                  <ul className="mt-3 flex flex-wrap gap-1.5">
                    {gaps.slice(0, 8).map((g) => (
                      <li key={g}>
                        <button
                          type="button"
                          onClick={() => setCoverage(g)}
                          className="cursor-pointer"
                        >
                          <Chip variant="info" size="sm">
                            + {g}
                          </Chip>
                        </button>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </Card>

            <Card pad="md">
              <Eyebrow>What happens next</Eyebrow>
              <ol className="mt-3 space-y-2 text-[13px] text-ink">
                <Step n={1}>Your broker reviews and shapes the submission.</Step>
                <Step n={2}>They market it; you'll see indicative quotes.</Step>
                <Step n={3}>You bind or pass — terms appear in Coverages.</Step>
              </ol>
            </Card>
          </aside>
        </div>
      </div>
    </>
  );
}

function Field({
  id,
  label,
  hint,
  required,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1.5 flex items-baseline justify-between text-[12.5px] font-medium text-ink-soft"
      >
        <span>
          {label}
          {required && <span className="ml-1 text-spot">*</span>}
        </span>
        {hint && <span className="text-[11.5px] text-ink-mute">{hint}</span>}
      </label>
      {children}
    </div>
  );
}

function Step({ n, children }: { n: number; children: React.ReactNode }) {
  return (
    <li className="flex items-start gap-2.5">
      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-surface-sunken text-[11px] font-semibold text-ink-soft">
        {n}
      </span>
      <span>{children}</span>
    </li>
  );
}

const inputClass =
  "block h-11 w-full rounded-btn border border-rule-strong bg-surface px-3 text-[14px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30";
