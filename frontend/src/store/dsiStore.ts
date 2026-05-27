import { create } from 'zustand';
import { ReactNode } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

/**
 * Loosely-typed JSON payloads from the carrier API. The API surface is
 * Pydantic-typed server-side, but the frontend treats responses as
 * record objects so individual consumers can read whatever fields
 * they need without rigid TS types per endpoint. Pages still know
 * their shape -- this just removes the `as any` casts that were
 * scattered across components.
 */
export type ApiRecord = Record<string, any>;
export type ApiList = ApiRecord[];

/**
 * Keys used in the unified `loading` map. Add a new key when adding
 * a new fetch action; consumers select with `s.loading[K] ?? false`.
 */
export type LoadingKey =
  | "submissions"
  | "submissionDetail"
  | "riskSignals"
  | "lossAnalytics"
  | "exposureAnalytics"
  | "referralSignals"
  | "history"
  | "limitSelection";


export interface DsiState {
  // -----------------------------------------------------------------
  // Navigation & breadcrumb state
  // -----------------------------------------------------------------
  activeMenu: string;
  setActiveMenu: (menu: string) => void;
  previousMenu: string;
  navigateBack: () => void;
  /** Leave a submission without resetting activeMenu (unlike navigateBack). */
  clearSubmissionContext: () => void;
  /**
   * v8 polish: session-boundary reset. Called by authStore on login,
   * logout, and refresh-failure so navigation state from a previous
   * session can't leak into a new portal session.
   */
  resetNavigation: () => void;

  // -----------------------------------------------------------------
  // Title bar slots
  // -----------------------------------------------------------------
  hasPageActions: boolean;
  setHasPageActions: (hasActions: boolean) => void;
  isPageActionsOpen: boolean;
  setPageActionsOpen: (isOpen: boolean) => void;
  pageQuickAction: ReactNode | null;
  setPageQuickAction: (action: ReactNode | null) => void;

  // -----------------------------------------------------------------
  // Date filter (affects pipeline + analytics queries)
  // -----------------------------------------------------------------
  daysFilter: number;
  setDaysFilter: (days: number) => void;

  // -----------------------------------------------------------------
  // Sidebar category state (drilldown nav)
  // -----------------------------------------------------------------
  activeCategory: string;
  setActiveCategory: (category: string) => void;
  expandedCategories: Record<string, boolean>;
  toggleCategory: (category: string) => void;

  // -----------------------------------------------------------------
  // v8.2 — broker vertical filter (Marsh practice lens)
  // -----------------------------------------------------------------
  verticalFilter: string | null;
  setVerticalFilter: (slug: string | null) => void;

  // -----------------------------------------------------------------
  // Loading state (single source of truth). Consumers select keys:
  //   const isFetching = useDsiStore(s => s.loading.riskSignals);
  // -----------------------------------------------------------------
  loading: Partial<Record<LoadingKey, boolean>>;
  error: string | null;

  // -----------------------------------------------------------------
  // Submission pipeline + active drilldown
  // -----------------------------------------------------------------
  submissions: ApiList;
  activeSubmission: ApiRecord | null;
  activeQuote: ApiRecord | null;
  activeVersion: ApiRecord | null;
  activeCommercial: ApiRecord | null;
  activeRisk: ApiRecord | null;
  activeReferral: ApiRecord | null;

  fetchSubmissions: () => Promise<void>;
  fetchCoreSubmissionDetail: (row: ApiRecord) => Promise<void>;
  updateDecision: (
    quoteCode: string,
    quoteDecision: string,
    referralDecision: string | null,
  ) => Promise<void>;

  // -----------------------------------------------------------------
  // Per-tab analytics caches. Each carries a `*Key` cache identifier
  // so a coverage / version change correctly invalidates the cached
  // data instead of returning stale numbers from a previous selection.
  // -----------------------------------------------------------------
  riskSignals: ApiList;
  riskSignalsKey: string | null;
  fetchRiskSignals: (versionCode: string) => Promise<void>;

  lossCohortBenchmarks: ApiList;
  lossTrendDistribution: ApiList;
  lossScatterData: ApiList;
  lossAnalyticsKey: string | null;
  fetchLossAnalytics: (coverage: string, daysFilter?: number) => Promise<void>;

  exposureBandBenchmarks: ApiList;
  exposureTierDistribution: ApiList;
  exposureScatterData: ApiList;
  exposureAnalyticsKey: string | null;
  fetchExposureAnalytics: (coverage: string, daysFilter?: number) => Promise<void>;

  modelVersions: ApiList;
  auditLogs: ApiList;
  modelVersionsKey: string | null;
  fetchHistory: (submissionCode: string) => Promise<void>;

  referralSignals: ApiList;
  fetchReferralSignals: (versionCode: string) => Promise<void>;
  submitSignalOverride: (
    quoteCode: string,
    signalCode: string,
    auditedValue: number,
    rationale: string,
  ) => Promise<void>;

  // -----------------------------------------------------------------
  // Pricing tab — limit option selection
  // -----------------------------------------------------------------
  selectLimitOption: (
    quoteCode: string,
    selectedLimit: number,
    rationale?: string,
  ) => Promise<void>;

  // -----------------------------------------------------------------
  // Notes
  // -----------------------------------------------------------------
  addNote: (versionCode: string, note: string, source?: string) => Promise<void>;
}


/**
 * Internal: fetch JSON with a graceful fallback on non-2xx / network
 * error. Replaces the inline `safeFetch` definitions that were
 * duplicated in fetchLossAnalytics, fetchExposureAnalytics, and
 * fetchCoreSubmissionDetail.
 */
async function safeJson<T>(url: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(url);
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}


export const useDsiStore = create<DsiState>((set, get) => {
  // ------------------------------------------------------------------
  // Internal: wrap a fetcher with the loading-flag bookkeeping pattern
  // (set true → run → set false; log on throw). Use for every store
  // action that fetches.
  // ------------------------------------------------------------------
  async function withLoading<T>(
    key: LoadingKey,
    fetcher: () => Promise<T>,
  ): Promise<T | null> {
    set((s) => ({ loading: { ...s.loading, [key]: true } }));
    try {
      return await fetcher();
    } catch (err) {
      console.error(`[dsiStore] ${key} fetch failed:`, err);
      return null;
    } finally {
      set((s) => ({ loading: { ...s.loading, [key]: false } }));
    }
  }

  return {
    // -----------------------------------------------------------------
    // Defaults
    // -----------------------------------------------------------------
    activeMenu: "",
    previousMenu: "",
    // v8.1: snapshot the previous menu so the title bar and sidebar
    // "Back to {previousMenu}" labels render with content. Without this
    // a user clicking from "Referral Pipeline" -> a submission saw
    // "/ / SolarWinds / Summary" and "Back to ".
    setActiveMenu: (menu) => set((s) => ({
      activeMenu: menu,
      previousMenu: s.activeMenu && s.activeMenu !== menu ? s.activeMenu : s.previousMenu,
    })),

    hasPageActions: false,
    setHasPageActions: (hasPageActions) => set({ hasPageActions }),
    isPageActionsOpen: false,
    setPageActionsOpen: (isPageActionsOpen) => set({ isPageActionsOpen }),
    pageQuickAction: null,
    setPageQuickAction: (pageQuickAction) => set({ pageQuickAction }),

    daysFilter: 30,
    setDaysFilter: (daysFilter) => {
      set({ daysFilter });
      get().fetchSubmissions();
    },

    activeCategory: "Summary",
    setActiveCategory: (activeCategory) => set({ activeCategory }),
    expandedCategories: { Commercial: false, Risk: false, Technical: true },
    toggleCategory: (category) => set((state) => ({
      expandedCategories: {
        ...state.expandedCategories,
        [category]: !state.expandedCategories[category],
      },
    })),

    // v8.2 vertical filter -- null = no filter / show all.
    verticalFilter: null,
    setVerticalFilter: (slug) => set({ verticalFilter: slug }),

    loading: {},
    error: null,

    submissions: [],
    activeSubmission: null,
    activeQuote: null,
    activeVersion: null,
    activeCommercial: null,
    activeRisk: null,
    activeReferral: null,

    riskSignals: [],
    riskSignalsKey: null,

    lossCohortBenchmarks: [],
    lossTrendDistribution: [],
    lossScatterData: [],
    lossAnalyticsKey: null,

    exposureBandBenchmarks: [],
    exposureTierDistribution: [],
    exposureScatterData: [],
    exposureAnalyticsKey: null,

    modelVersions: [],
    auditLogs: [],
    modelVersionsKey: null,

    referralSignals: [],

    // -----------------------------------------------------------------
    // Navigation actions
    // -----------------------------------------------------------------
    navigateBack: () => {
      set((state) => ({
        activeMenu: state.previousMenu || "Referral Pipeline",
        activeSubmission: null,
        activeQuote: null,
        activeVersion: null,
        activeReferral: null,
      }));
    },

    clearSubmissionContext: () => {
      set({
        activeSubmission: null,
        activeQuote: null,
        activeVersion: null,
        activeReferral: null,
        activeCommercial: null,
        activeRisk: null,
      });
    },

    resetNavigation: () => {
      set({
        activeMenu: "",
        previousMenu: "",
        activeSubmission: null,
        activeQuote: null,
        activeVersion: null,
        activeReferral: null,
        activeCommercial: null,
        activeRisk: null,
        activeCategory: "Summary",
        submissions: [],
        modelVersions: [],
        auditLogs: [],
        modelVersionsKey: null,
        riskSignals: [],
        riskSignalsKey: null,
        lossCohortBenchmarks: [],
        lossTrendDistribution: [],
        lossScatterData: [],
        lossAnalyticsKey: null,
        exposureBandBenchmarks: [],
        exposureTierDistribution: [],
        exposureScatterData: [],
        exposureAnalyticsKey: null,
        referralSignals: [],
        hasPageActions: false,
        isPageActionsOpen: false,
        pageQuickAction: null,
        loading: {},
        error: null,
        verticalFilter: null,
      });
    },

    // -----------------------------------------------------------------
    // Pipeline
    // -----------------------------------------------------------------
    fetchSubmissions: async () => {
      await withLoading("submissions", async () => {
        set({ error: null });
        const days = get().daysFilter;
        const isoDate = new Date(Date.now() - days * 86400_000).toISOString();
        const data = await safeJson<ApiList>(
          `${API_BASE}/api/v1/frontend/pipeline?created_after=${isoDate}`,
          [],
        );
        set({ submissions: data });
      });
    },

    fetchCoreSubmissionDetail: async (row) => {
      await withLoading("submissionDetail", async () => {
        // Clear cached tab data + cache keys when switching submissions
        // so the per-tab fetches refresh against the new submission's
        // coverage / version instead of returning stale data.
        set({
          error: null,
          lossCohortBenchmarks: [],
          lossTrendDistribution: [],
          lossScatterData: [],
          lossAnalyticsKey: null,
          exposureBandBenchmarks: [],
          exposureTierDistribution: [],
          exposureScatterData: [],
          exposureAnalyticsKey: null,
          modelVersions: [],
          auditLogs: [],
          modelVersionsKey: null,
          riskSignals: [],
          riskSignalsKey: null,
        });

        const [subData, versionsData, quoteData, commercialData, riskData, referralData] =
          await Promise.all([
            safeJson<ApiRecord | null>(`${API_BASE}/api/v1/submissions/${row.submission_code}`, null),
            safeJson<ApiRecord | null>(`${API_BASE}/api/v1/modelversion/${row.version_code}/all`, null),
            safeJson<ApiRecord | null>(`${API_BASE}/api/v1/quotes/${row.quote_code}`, null),
            safeJson<ApiRecord | null>(`${API_BASE}/api/v1/commercialterms/${row.version_code}`, null),
            safeJson<ApiRecord | null>(`${API_BASE}/api/v1/riskterms/${row.version_code}`, null),
            row.referral_code
              ? safeJson<ApiRecord | null>(`${API_BASE}/api/v1/referrals/${row.referral_code}`, null)
              : Promise.resolve(null),
          ]);

        if (!subData) {
          set({ error: "Failed to load core submission details." });
          return;
        }

        set({
          activeSubmission: subData,
          activeQuote: quoteData,
          activeVersion: versionsData,
          activeCommercial: commercialData,
          activeRisk: riskData,
          activeReferral: referralData,
          // v8.1: capture previous top-level menu (e.g. "Referral Pipeline")
          // so the breadcrumb + sidebar "Back to {previousMenu}" render
          // correctly when the user enters submission drilldown.
          previousMenu: get().activeMenu || get().previousMenu,
          activeMenu: "Summary",
        });
      });
    },

    updateDecision: async (quoteCode, quoteAction, referralAction) => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/quotes/${quoteCode}/resolve`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            quote_action: quoteAction,
            referral_action: referralAction,
          }),
        });
        if (!res.ok) throw new Error("Failed to update decision");
        get().fetchSubmissions();
      } catch (err) {
        console.error("Failed to update decision", err);
      }
    },

    // -----------------------------------------------------------------
    // Risk signals -- cached per versionCode
    // -----------------------------------------------------------------
    fetchRiskSignals: async (versionCode) => {
      if (get().riskSignalsKey === versionCode) return;
      await withLoading("riskSignals", async () => {
        const data = await safeJson<ApiList>(
          `${API_BASE}/api/v1/frontend/${versionCode}/signals`,
          [],
        );
        set({ riskSignals: data, riskSignalsKey: versionCode });
      });
    },

    // -----------------------------------------------------------------
    // Loss analytics -- cached per (coverage, daysFilter). Critical:
    // a coverage change must invalidate the cache; the previous
    // length-only check returned stale data from the prior coverage.
    // -----------------------------------------------------------------
    fetchLossAnalytics: async (coverage, daysFilter = 365) => {
      const key = `${coverage}:${daysFilter}`;
      if (get().lossAnalyticsKey === key) return;
      await withLoading("lossAnalytics", async () => {
        const isoDate = new Date(Date.now() - daysFilter * 86400_000).toISOString();
        const base = `${API_BASE}/api/v1/analytics/loss`;
        const qs = `?coverage=${encodeURIComponent(coverage)}&created_after=${encodeURIComponent(isoDate)}`;
        const [cohort, trend, scatter] = await Promise.all([
          safeJson<ApiList>(`${base}/cohort-benchmarks${qs}`, []),
          safeJson<ApiList>(`${base}/trend-distribution${qs}`, []),
          safeJson<ApiList>(`${base}/scatter-plot${qs}`, []),
        ]);
        set({
          lossCohortBenchmarks: cohort,
          lossTrendDistribution: trend,
          lossScatterData: scatter,
          lossAnalyticsKey: key,
        });
      });
    },

    // -----------------------------------------------------------------
    // Exposure analytics -- same coverage-aware cache as loss above.
    // -----------------------------------------------------------------
    fetchExposureAnalytics: async (coverage, daysFilter = 365) => {
      const key = `${coverage}:${daysFilter}`;
      if (get().exposureAnalyticsKey === key) return;
      await withLoading("exposureAnalytics", async () => {
        const isoDate = new Date(Date.now() - daysFilter * 86400_000).toISOString();
        const base = `${API_BASE}/api/v1/analytics/exposure`;
        const qs = `?coverage=${encodeURIComponent(coverage)}&created_after=${encodeURIComponent(isoDate)}`;
        const [band, tier, scatter] = await Promise.all([
          safeJson<ApiList>(`${base}/band-benchmarks${qs}`, []),
          safeJson<ApiList>(`${base}/tier-distribution${qs}`, []),
          safeJson<ApiList>(`${base}/scatter-plot${qs}`, []),
        ]);
        set({
          exposureBandBenchmarks: band,
          exposureTierDistribution: tier,
          exposureScatterData: scatter,
          exposureAnalyticsKey: key,
        });
      });
    },

    // -----------------------------------------------------------------
    // Model-version history -- cached per submissionCode so switching
    // submissions correctly re-fetches.
    // -----------------------------------------------------------------
    fetchHistory: async (submissionCode) => {
      if (get().modelVersionsKey === submissionCode) return;
      await withLoading("history", async () => {
        const data = await safeJson<ApiList>(
          `${API_BASE}/api/v1/modelversion/${submissionCode}/submissionshistory/all`,
          [],
        );
        set({
          modelVersions: Array.isArray(data) ? data : [],
          auditLogs: [],
          modelVersionsKey: submissionCode,
        });
      });
    },

    // -----------------------------------------------------------------
    // Referral signals
    // -----------------------------------------------------------------
    fetchReferralSignals: async (submissionCode) => {
      await withLoading("referralSignals", async () => {
        const data = await safeJson<ApiRecord>(
          `${API_BASE}/api/v1/modelversion/${submissionCode}/submissionshistory/all`,
          {},
        );
        set({ referralSignals: Array.isArray(data.signals) ? data.signals : [] });
      });
    },

    submitSignalOverride: async (quoteCode, signalCode, auditedValue, rationale) => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/signals/${quoteCode}/override`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            signal_code: signalCode,
            audited_value: auditedValue,
            rationale,
            underwriter_id: "system",
          }),
        });
        if (!res.ok) throw new Error("Failed to override signal");

        const overrideData = await res.json();
        const newVersionCode = overrideData.new_version_code;

        const quoteData = await safeJson<ApiRecord | null>(
          `${API_BASE}/api/v1/quotes/${quoteCode}`,
          null,
        );

        const activeSub = get().activeSubmission;
        if (activeSub && quoteData) {
          await get().fetchCoreSubmissionDetail({
            submission_code: activeSub.submission_code ?? activeSub.submission_id,
            quote_code: quoteCode,
            referral_code: quoteData.referral_id,
          });
          await get().fetchHistory(
            activeSub.submission_code ?? activeSub.submission_id,
          );
        }

        if (newVersionCode) {
          await get().fetchReferralSignals(newVersionCode);
        }

        get().fetchSubmissions();
      } catch (err) {
        console.error("Signal override failed:", err);
      }
    },

    // -----------------------------------------------------------------
    // Limit option selection (pricing tab)
    // -----------------------------------------------------------------
    selectLimitOption: async (quoteCode, selectedLimit, rationale) => {
      await withLoading("limitSelection", async () => {
        const res = await fetch(`${API_BASE}/api/v1/quotes/${quoteCode}/select-option`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            selected_limit: selectedLimit,
            rationale: rationale ?? null,
            underwriter_id: "system",
          }),
        });
        if (!res.ok) throw new Error("Failed to select limit option");
        const data = await res.json();

        const activeSub = get().activeSubmission;
        if (activeSub) {
          const activeReferralRec = get().activeReferral;
          await get().fetchCoreSubmissionDetail({
            submission_code: activeSub.submission_code ?? activeSub.submission_id,
            quote_code: quoteCode,
            version_code: data.new_version_code,
            referral_code: activeReferralRec?.referral_code ?? null,
          });
        }
        get().fetchSubmissions();
      });
    },

    // -----------------------------------------------------------------
    // Notes
    // -----------------------------------------------------------------
    addNote: async (versionCode, note, source = "underwriter") => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/modelversion/${versionCode}/notes`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ note, source }),
        });
        if (!res.ok) return;
        const data = await res.json();
        const av = get().activeVersion;
        if (av) {
          set({ activeVersion: { ...av, notes: data.notes } });
        }
      } catch (err) {
        console.error("Failed to add note:", err);
      }
    },
  };
});
