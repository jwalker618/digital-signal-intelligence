"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import {
  CheckCircle2,
  ChevronDown,
  Info,
  Loader2,
  Send,
  UploadCloud,
} from "lucide-react";
import { Topbar } from "@/components/chrome/topbar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Eyebrow, NumDisplay, Body, Micro, Caption } from "@/components/ui/typography";
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

const inputClass =
  "block h-11 w-full rounded-btn border border-rule-strong bg-surface-elev px-3.5 text-[14px] text-ink placeholder:text-ink-mute focus:border-info focus:outline-none focus:ring-2 focus:ring-info/30";

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

  return (
    <RequestBody
      entityName={overview.data.entity_name}
      brokerName={overview.data.broker?.name ?? null}
    />
  );
}

function RequestBody({
  entityName,
  brokerName,
}: {
  entityName: string;
  brokerName: string | null;
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
                {brokerName ?? "Your broker"} will pick this up and draft a
                submission. You can track the conversation in Communications.
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
        <div className="grid gap-5">
          <div>
            <Eyebrow>Request coverage</Eyebrow>
            <h1 className="mt-1.5 font-display text-[32px] font-semibold leading-none tracking-tight text-ink">
              Tell your broker what you&apos;d like to explore
            </h1>
            <Body className="mt-2 max-w-[640px]">
              No commitment, no obligation. Submitting this notifies your
              broker — they&apos;ll review and reply in Communications, where
              you can refine the request together before any formal submission
              goes to market.
            </Body>
          </div>

          <form
            onSubmit={onSubmit}
            className="grid gap-5 lg:grid-cols-[1.4fr_1fr]"
          >
            <Card pad="lg">
              <div className="flex flex-col gap-5">
                <Field label="Coverage line" required>
                  <div className="relative">
                    <input
                      type="text"
                      required
                      value={coverage}
                      onChange={(e) => setCoverage(e.target.value)}
                      list="suggested-lines"
                      placeholder="e.g. Cyber, D&O, Property…"
                      className={cn(inputClass, "pr-10")}
                    />
                    <ChevronDown
                      size={16}
                      className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-ink-mute"
                    />
                    <datalist id="suggested-lines">
                      {SUGGESTED_LINES.map((l) => (
                        <option key={l} value={l} />
                      ))}
                    </datalist>
                  </div>
                </Field>

                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="Desired limit" optional>
                    <input
                      type="number"
                      inputMode="numeric"
                      min={0}
                      step={100_000}
                      value={desiredLimit}
                      onChange={(e) => setDesiredLimit(e.target.value)}
                      placeholder="$25,000,000"
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Preferred effective date" optional>
                    <input
                      type="date"
                      value={effectiveDate}
                      onChange={(e) => setEffectiveDate(e.target.value)}
                      className={inputClass}
                    />
                  </Field>
                </div>

                <Field label="Why are you exploring this?" optional>
                  <textarea
                    rows={5}
                    value={rationale}
                    onChange={(e) => setRationale(e.target.value)}
                    placeholder="New manufacturing line, contractual requirement, peer benchmark…"
                    className={cn(inputClass, "h-auto resize-y py-2.5 leading-[1.55]")}
                  />
                </Field>

                <Field label="Attachments" optional>
                  <div className="flex items-center gap-3 rounded-card border border-dashed border-rule-strong px-4 py-4 text-ink-soft">
                    <UploadCloud size={20} />
                    <span className="text-[13px]">
                      Drop COPE summary, valuation reports, or anything else
                      relevant here.
                    </span>
                  </div>
                </Field>

                {error && (
                  <div
                    role="alert"
                    className="rounded-btn border border-neg bg-neg-soft px-3 py-2 text-[13px] text-neg"
                  >
                    {error}
                  </div>
                )}

                <div className="flex items-center justify-between gap-3 border-t border-rule pt-4">
                  <Caption>
                    Your broker{brokerName ? ` (${brokerName})` : ""} will see
                    this first.
                  </Caption>
                  <div className="flex gap-2">
                    <Button type="button" variant="ghost" disabled>
                      Save draft
                    </Button>
                    <Button type="submit" variant="spot" disabled={!canSubmit}>
                      {submitting ? (
                        <>
                          <Loader2 size={14} className="animate-spin" />
                          Submitting…
                        </>
                      ) : (
                        <>
                          <Send size={14} />
                          Send to broker
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            </Card>

            <aside className="flex flex-col gap-3.5">
              <Card variant="info" pad="lg">
                <Eyebrow className="text-info-deep dark:text-info">
                  What happens next
                </Eyebrow>
                <ol className="mt-3 flex flex-col gap-2.5">
                  {[
                    [
                      "Your broker receives the request",
                      "Reviews fit + appetite, may ask clarifying questions in Communications.",
                    ],
                    [
                      "DSI estimates the cost",
                      "Indicative range based on your cohort and current signals.",
                    ],
                    [
                      "You decide whether to go to market",
                      "Nothing leaves the building until you say so.",
                    ],
                  ].map(([title, body], i) => (
                    <li key={i} className="flex items-start gap-3">
                      <span className="flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full bg-info text-[12px] font-bold text-white">
                        {i + 1}
                      </span>
                      <div className="min-w-0">
                        <p className="text-[13px] font-semibold text-ink">{title}</p>
                        <Caption className="mt-0.5 block leading-relaxed">
                          {body}
                        </Caption>
                      </div>
                    </li>
                  ))}
                </ol>
              </Card>

              <Card pad="lg">
                <Eyebrow>Indicative range</Eyebrow>
                <div className="mt-2 flex items-baseline gap-2">
                  <NumDisplay size="md">$70k</NumDisplay>
                  <Caption>to</Caption>
                  <NumDisplay size="md">$220k</NumDisplay>
                </div>
                <Caption className="mt-1 block">
                  Pricing is set by your carrier at placement.
                </Caption>
                <div className="mt-3 flex items-start gap-2.5 rounded-card bg-surface-sunken px-3 py-2.5">
                  <Info size={14} className="mt-0.5 shrink-0 text-ink-soft" />
                  <Caption className="leading-relaxed">
                    Final pricing depends on COPE detail, valuation, and broader
                    signal context.
                  </Caption>
                </div>
              </Card>
            </aside>
          </form>
        </div>
      </div>
    </>
  );
}

function Field({
  label,
  required,
  optional,
  children,
}: {
  label: string;
  required?: boolean;
  optional?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 flex items-baseline gap-2">
        <span className="text-[13px] font-semibold text-ink">{label}</span>
        {required && (
          <span className="text-[10px] font-semibold text-spot">required</span>
        )}
        {optional && <Micro className="text-[10px]">optional</Micro>}
      </label>
      {children}
    </div>
  );
}
