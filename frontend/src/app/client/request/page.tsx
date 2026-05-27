"use client";

// v8.1 Phase E — /client/request
//
// Lightweight "I'd like a quote for X" intent form. Submits to the
// /portal/coverage-requests endpoint which creates a placeholder
// Submission + Referral + initial thread message. The broker sees
// the request immediately in their Communications inbox.

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AlertTriangle,
  CheckCircle2,
  PlusCircle,
  Send,
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
} from "@/components/base/content/primatives";

import { useAuthStore } from "@/store/authStore";
import { useDsiStore } from "@/store/dsiStore";
import { postCoverageRequest } from "@/lib/portalApi";


const COVERAGE_OPTIONS = [
  { id: "cyber",     label: "Cyber" },
  { id: "pi",        label: "Professional Indemnity (E&O)" },
  { id: "do",        label: "Directors & Officers" },
  { id: "property",  label: "Property" },
  { id: "casualty",  label: "General Liability" },
  { id: "prodlib",   label: "Product Liability" },
  { id: "medprof",   label: "Medical Professional Liability" },
];


export default function RequestCoveragePage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const userRole = useAuthStore((s) => s.user?.role ?? null);
  const setActiveMenu = useDsiStore((s) => s.setActiveMenu);

  const [coverage, setCoverage] = useState<string>("cyber");
  const [desiredLimit, setDesiredLimit] = useState<string>("");
  const [effectiveDate, setEffectiveDate] = useState<string>("");
  const [rationale, setRationale] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState<{
    referralCode: string;
    submissionCode: string;
  } | null>(null);

  useEffect(() => { setActiveMenu("Request Coverage"); }, [setActiveMenu]);

  if (userRole !== "CLIENT") {
    return (
      <ViewCanvas>
        <CardGrid cols="grid-cols-1">
          <StandardCard title="Client-only" lucideIcon={AlertTriangle}>
            <NoData message="The Request Coverage form is for client users only." />
          </StandardCard>
        </CardGrid>
      </ViewCanvas>
    );
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true); setError(null);
    try {
      const result = await postCoverageRequest(accessToken, {
        coverage,
        desired_limit: desiredLimit ? Number(desiredLimit) : undefined,
        desired_effective_date: effectiveDate || undefined,
        rationale,
      });
      setSubmitted({
        referralCode: result.referral_code,
        submissionCode: result.submission_code,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <ViewCanvas>
      <CardGrid cols="grid-cols-1" className="gap-4">

        <SubmissionHeaderCard
          decision="approve"
          title="Request a new coverage"
          subtitle="We'll send this to your broker to start the conversation. No commitment, no obligation."
          lucideIcon={PlusCircle}
        />

        {submitted ? (
          <StandardCard title="Request submitted" lucideIcon={CheckCircle2}>
            <div className="space-y-3 py-2">
              <p className="text-sm">
                Thanks — your broker has been notified and will follow up via
                Communications.
              </p>
              <LabelValueList
                variant="card"
                rows={[
                  { label: "Reference", value: submitted.referralCode },
                  { label: "Submission code", value: submitted.submissionCode },
                ]}
              />
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => router.push("/communications")}
                  className="
                    bg-generate-dark-background text-generate-text-input
                    rounded-md px-4 py-2 text-sm font-bold
                    hover:opacity-90"
                >
                  Open Communications
                </button>
                <button
                  onClick={() => {
                    setSubmitted(null);
                    setCoverage("cyber");
                    setDesiredLimit("");
                    setEffectiveDate("");
                    setRationale("");
                  }}
                  className="
                    border border-generate-text-outline
                    rounded-md px-4 py-2 text-sm
                    hover:bg-generate-light-input"
                >
                  Request another
                </button>
              </div>
            </div>
          </StandardCard>
        ) : (
          <StandardCard title="What would you like to explore?" lucideIcon={PlusCircle}>
            <form onSubmit={onSubmit} className="space-y-4 py-2">
              <div>
                <label className="block text-xs text-generate-text-placeholder mb-1">
                  Coverage line
                </label>
                <select
                  value={coverage}
                  onChange={(e) => setCoverage(e.target.value)}
                  className="
                    w-full text-sm
                    bg-generate-light-input
                    border border-generate-text-outline
                    rounded-md p-2"
                >
                  {COVERAGE_OPTIONS.map((o) => (
                    <option key={o.id} value={o.id}>{o.label}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-generate-text-placeholder mb-1">
                    Desired limit (optional)
                  </label>
                  <input
                    type="number"
                    value={desiredLimit}
                    onChange={(e) => setDesiredLimit(e.target.value)}
                    placeholder="e.g. 10000000"
                    className="
                      w-full text-sm
                      bg-generate-light-input
                      border border-generate-text-outline
                      rounded-md p-2"
                  />
                </div>
                <div>
                  <label className="block text-xs text-generate-text-placeholder mb-1">
                    Preferred effective date (optional)
                  </label>
                  <input
                    type="date"
                    value={effectiveDate}
                    onChange={(e) => setEffectiveDate(e.target.value)}
                    className="
                      w-full text-sm
                      bg-generate-light-input
                      border border-generate-text-outline
                      rounded-md p-2"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs text-generate-text-placeholder mb-1">
                  Why are you exploring this? (optional)
                </label>
                <textarea
                  value={rationale}
                  onChange={(e) => setRationale(e.target.value)}
                  rows={3}
                  placeholder="Examples: new contract requires it, growing exposure, recent industry incident."
                  className="
                    w-full text-sm
                    bg-generate-light-input
                    border border-generate-text-outline
                    rounded-md p-2"
                />
              </div>

              {error && <p className="text-xs text-generate-text-bad">{error}</p>}

              <button
                type="submit"
                disabled={submitting}
                className="
                  flex items-center gap-2
                  bg-generate-dark-background text-generate-text-input
                  rounded-md px-4 py-2 text-sm font-bold
                  hover:opacity-90 disabled:opacity-50"
              >
                <Send className="generate-app-icon" />
                {submitting ? "Sending…" : "Send to broker"}
              </button>
            </form>
          </StandardCard>
        )}

        <InfoPanel label="What happens next">
          <p className="text-xs">
            Submitting this form notifies your broker — there's no commitment.
            They'll review and reply via Communications, where you can refine
            the request together before any formal submission goes to market.
          </p>
        </InfoPanel>

      </CardGrid>
    </ViewCanvas>
  );
}
