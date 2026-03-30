import { create } from 'zustand';
import { ReactNode } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export interface DsiState {
  // Navigation & Context State
  activeMenu: string;
  setActiveMenu: (menu: string) => void;
  previousMenu: string;
  updateDecision: (quoteCode: string, quoteDecision: string, referralDecision: string | null) => Promise<void>;
  navigateBack: () => void; 

  // Title Bar Menu Actions and Quick Action
  hasPageActions: boolean;
  setHasPageActions: (hasActions: boolean) => void;
  isPageActionsOpen: boolean;
  setPageActionsOpen: (isOpen: boolean) => void;
  pageQuickAction: ReactNode | null;
  setPageQuickAction: (action: ReactNode | null) => void;

  // NEW: Date Filter State
  daysFilter: number;
  setDaysFilter: (days: number) => void;

  // Data State
  submissions: any[];
  activeSubmission: string | null;
  activeQuote: string | null;
  activeVersion: string | null;
  activeReferral: string | null;
  isLoading: boolean;
  error: string | null;


  // PricingTab
  isSelectingLimit: boolean;
  selectLimitOption: (quoteCode: string, selectedLimit: number, rationale?: string) => Promise<void>;

  // RiskTab
  riskSignals: any[];
  isFetchingRiskSignals: boolean;
  riskSignalsVersionCode: string | null;  // Cache key
  fetchRiskSignals: (versionCode: string) => Promise<void>;

  // LossTab
  lossCohortBenchmarks: any[];
  lossTrendDistribution: any[];
  lossScatterData: any[];
  isFetchingLossAnalytics: boolean;
  fetchLossAnalytics: (coverage: string, daysFilter?: number) => Promise<void>;

  // ExposureTab
  exposureBandBenchmarks: any[];
  exposureTierDistribution: any[];
  exposureScatterData: any[];
  isFetchingExposureAnalytics: boolean;
  fetchExposureAnalytics: (coverage: string, daysFilter?: number) => Promise<void>;

  // Submission Review State
  modelVersions: any[];
  auditLogs: any[];
  fetchHistory: (submissionCode: string) => Promise<void>;

  // Actions
  fetchSubmissions: () => Promise<void>;
  fetchCoreSubmissionDetail: (row: any) => Promise<void>;

  // Referral Actions State
  referralSignals: any[];
  isFetchingSignals: boolean;
  fetchReferralSignals: (versionCode: string) => Promise<void>;
  submitSignalOverride: (quoteCode: string, signalCode: string, auditedValue: number, rationale: string) => Promise<void>;

  // Notes
  addNote: (versionCode: string, note: string, source?: string) => Promise<void>;

  // Commercial & Risk Terms (Phase 1)
  commercialTerms: any | null;
  riskTerms: any | null;
  isFetchingTerms: boolean;
  commercialTermsVersionCode: string | null;
  fetchCommercialTerms: (versionCode: string) => Promise<void>;

  // Sidebar category state
  activeCategory: string;
  setActiveCategory: (category: string) => void;
  expandedCategories: Record<string, boolean>;
  toggleCategory: (category: string) => void;

}

export const useDsiStore = create<DsiState>((set, get) => ({
  activeMenu: "Referral Pipeline",
  setActiveMenu: (menu) => set({ activeMenu: menu }),
  previousMenu: "Referral Pipeline",

  // Title Bar Menu and Quick Actions
  hasPageActions: false,
  setHasPageActions: (hasActions) => set({ hasPageActions: hasActions }),
  isPageActionsOpen: false,
  setPageActionsOpen: (isOpen) => set({ isPageActionsOpen: isOpen }),
  pageQuickAction: null,
  setPageQuickAction: (action) => set({ pageQuickAction: action }),

  // Default to 30 days, just like the backend
  daysFilter: 30,
  setDaysFilter: (days) => {
    set({ daysFilter: days });
    // Automatically re-fetch the data from the backend when the filter changes!
    get().fetchSubmissions(); 
  },

  submissions: [],
  activeSubmission: null,
  activeQuote: null,
  activeVersion: null,
  activeReferral: null,
  isLoading: false,
  error: null,
  referralSignals: [],
  isFetchingSignals: false,
  isSelectingLimit: false,

  // Commercial & Risk Terms
  commercialTerms: null,
  riskTerms: null,
  isFetchingTerms: false,
  commercialTermsVersionCode: null,

  // Sidebar category state
  activeCategory: "Summary",
  setActiveCategory: (category) => set({ activeCategory: category }),
  expandedCategories: { Commercial: false, Risk: false, Technical: true },
  toggleCategory: (category) => set((state) => ({
    expandedCategories: { ...state.expandedCategories, [category]: !state.expandedCategories[category] }
  })),

  // Default Risk Tab
  riskSignals: [],
  isFetchingRiskSignals: false,
  riskSignalsVersionCode: null,

  // Default Loss Tab
  lossCohortBenchmarks: [],
  lossTrendDistribution: [],
  lossScatterData: [],
  isFetchingLossAnalytics: false,

  // Default Exposure Tab
  exposureBandBenchmarks: [],
  exposureTierDistribution: [],
  exposureScatterData: [],
  isFetchingExposureAnalytics: false,

// Add the navigateBack action:
  navigateBack: () => {
    set((state) => ({
      activeMenu: state.previousMenu || "Referral Pipeline",
      activeSubmission: null, // Clearing this triggers the UI to revert!
      activeQuote: null,
      activeVersion: null,
      activeReferral: null
    }));
  },  

  updateDecision: async (quoteCode: string, quoteAction: string, referralAction: string | null) => {
    try {
      // Hits our strict DDD endpoint
      const res = await fetch(`${API_BASE}/api/v1/quotes/${quoteCode}/resolve`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          quote_action: quoteAction, // "BOUND" or "DECLINED"
          referral_action: referralAction, // "APPROVED", "DECLINED", or null (if no change to referral)
        })
      });
      
      if (!res.ok) throw new Error("Failed to update decision");
      
      // Refresh the table data so the row vanishes from the Referral list instantly
      get().fetchSubmissions(); 
    } catch (err) {
      console.error("Failed to update decision", err);
    }
  }, 

  fetchCommercialTerms: async (versionCode: string) => {
    if (get().commercialTermsVersionCode === versionCode && get().commercialTerms) return;
    set({ isFetchingTerms: true });
    try {
      const safeFetch = (url: string) => fetch(url).then(res => res.ok ? res.json() : null).catch(() => null);

      const [commercialData, riskData] = await Promise.all([
        safeFetch(`${API_BASE}/api/v1/commercialterms/${versionCode}`),
        safeFetch(`${API_BASE}/api/v1/riskterms/${versionCode}`),
      ]);

      set({
        commercialTerms: commercialData,
        riskTerms: riskData,
        isFetchingTerms: false,
        commercialTermsVersionCode: versionCode,
      });
    } catch (err) {
      console.error("Failed to fetch commercial terms:", err);
      set({ commercialTerms: null, riskTerms: null, isFetchingTerms: false, commercialTermsVersionCode: null });
    }
  },

  fetchRiskSignals: async (versionCode: string) => {
    // Skip if already fetched for this version
    if (get().riskSignalsVersionCode === versionCode && get().riskSignals.length > 0) return;
    set({ isFetchingRiskSignals: true });
    try {
      const res = await fetch(`${API_BASE}/api/v1/frontend/${versionCode}/signals`);
      if (res.ok) {
        const data = await res.json();
        set({ riskSignals: data, isFetchingRiskSignals: false, riskSignalsVersionCode: versionCode });
      } else {
        set({ riskSignals: [], isFetchingRiskSignals: false, riskSignalsVersionCode: null });
      }
    } catch (err) {
      console.error("Failed to fetch risk signals:", err);
      set({ riskSignals: [], isFetchingRiskSignals: false, riskSignalsVersionCode: null });
    }
  },

  fetchLossAnalytics: async (coverage: string, daysFilter = 365) => {
    // Skip if already have data for this coverage
    if (get().lossCohortBenchmarks.length > 0) return;
    set({ isFetchingLossAnalytics: true });
    
    try {
      // Calculate the 'created_after' date constraint
      const targetDate = new Date();
      targetDate.setDate(targetDate.getDate() - daysFilter);
      const isoDateString = targetDate.toISOString(); 

      const baseUrl = `${API_BASE}/api/v1/analytics/loss`;
      const params = `?coverage=${encodeURIComponent(coverage)}&created_after=${encodeURIComponent(isoDateString)}`;

      // Helper for safe fetching
      const safeFetch = (url: string) => fetch(url).then(res => res.ok ? res.json() : []).catch(() => []);

      // Execute all three aggregate queries simultaneously
      const [cohortData, trendData, scatterData] = await Promise.all([
        safeFetch(`${baseUrl}/cohort-benchmarks${params}`),
        safeFetch(`${baseUrl}/trend-distribution${params}`),
        safeFetch(`${baseUrl}/scatter-plot${params}`)
      ]);

      // Update the store with the optimized datasets
      set({ 
        lossCohortBenchmarks: cohortData,
        lossTrendDistribution: trendData,
        lossScatterData: scatterData,
        isFetchingLossAnalytics: false 
      });

    } catch (err) {
      console.error("Failed to fetch loss analytics:", err);
      set({ isFetchingLossAnalytics: false });
    }
  },

  fetchExposureAnalytics: async (coverage: string, daysFilter = 365) => {
    // Skip if already have data for this coverage
    if (get().exposureBandBenchmarks.length > 0) return;
    set({ isFetchingExposureAnalytics: true });
    
    try {
      const targetDate = new Date();
      targetDate.setDate(targetDate.getDate() - daysFilter);
      const isoDateString = targetDate.toISOString(); 

      const baseUrl = `${API_BASE}/api/v1/analytics/exposure`;
      const params = `?coverage=${encodeURIComponent(coverage)}&created_after=${encodeURIComponent(isoDateString)}`;

      const safeFetch = (url: string) => fetch(url).then(res => res.ok ? res.json() : []).catch(() => []);

      const [bandData, tierData, scatterData] = await Promise.all([
        safeFetch(`${baseUrl}/band-benchmarks${params}`),
        safeFetch(`${baseUrl}/tier-distribution${params}`),
        safeFetch(`${baseUrl}/scatter-plot${params}`)
      ]);

      set({ 
        exposureBandBenchmarks: bandData,
        exposureTierDistribution: tierData,
        exposureScatterData: scatterData,
        isFetchingExposureAnalytics: false 
      });

    } catch (err) {
      console.error("Failed to fetch exposure analytics:", err);
      set({ isFetchingExposureAnalytics: false });
    }
  },

  modelVersions: [],
  auditLogs: [],

  fetchHistory: async (submissionCode: string) => {
    // Skip if already have versions loaded
    if (get().modelVersions.length > 0) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/modelversion/${submissionCode}/submissionshistory/all`);
      if (res.ok) {
        const data = await res.json();
        // Endpoint returns list[ModelVersionDBRecord]
        const versions = Array.isArray(data) ? data : [];
        set({ modelVersions: versions, auditLogs: [] });
      }
    } catch {
      // Silently fail — endpoint may not be available
    }
  },

  addNote: async (versionCode: string, note: string, source = "underwriter") => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/modelversion/${versionCode}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note, source }),
      });
      if (res.ok) {
        const data = await res.json();
        // Update activeVersion notes in place
        const av = get().activeVersion as any;
        if (av) {
          set({ activeVersion: { ...av, notes: data.notes } });
        }
      }
    } catch (err) {
      console.error("Failed to add note:", err);
    }
  },

  fetchReferralSignals: async (submissionCode: string) => {
    set({ isFetchingSignals: true });
    try {
      const res = await fetch(`${API_BASE}/api/v1/modelversion/${submissionCode}/submissionshistory/all`);
      if (!res.ok) throw new Error("Failed to fetch signals");
      const data = await res.json();
      set({ referralSignals: data.signals || [], isFetchingSignals: false });
    } catch (err) {
      console.error(err);
      set({ isFetchingSignals: false });
    }
  },

  submitSignalOverride: async (quoteCode: string, signalCode: string, auditedValue: number, rationale: string) => {
    try {
      // 1. Send the override request to your new endpoint
      const res = await fetch(`${API_BASE}/api/v1/signals/${quoteCode}/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          signal_code: signalCode,
          audited_value: auditedValue, 
          rationale: rationale,
          underwriter_id: "system"
        })
      });
      
      if (!res.ok) throw new Error("Failed to override signal");
      
      const overrideData = await res.json();
      const newVersionCode = overrideData.new_version_code; // Grab the new is_latest model version

      // 2. Fetch the updated Quote
      // We MUST do this because the backend may have generated a brand new Referral for this Quote!
      const quoteRes = await fetch(`${API_BASE}/api/v1/quotes/${quoteCode}`);
      
      if (quoteRes.ok) {
        const quoteData = await quoteRes.json();
        const activeSub = get().activeSubmission;

        if (activeSub) {
          // 3. Re-hydrate the active view with the fresh data and the NEW referral code
          await get().fetchCoreSubmissionDetail({
            submission_code: activeSub.submission_id || activeSub.submission_code,
            quote_code: quoteCode,
            referral_code: quoteData.referral_id // This is the crucial link to the new referral!
          });

          // 4. Refresh the audit logs and model version history tab
          await get().fetchHistory(activeSub.submission_id || activeSub.submission_code);
        }
      }
      
      // 5. Refresh the signals table to point to the newly generated model version
      if (newVersionCode) {
        await get().fetchReferralSignals(newVersionCode);
      }

      // 6. Refresh the main pipeline grid in the background so scores are updated when you navigate back
      get().fetchSubmissions();

    } catch (err) {
      console.error("Signal override failed:", err);
    }
  },

  selectLimitOption: async (quoteCode: string, selectedLimit: number, rationale?: string) => {
    set({ isSelectingLimit: true });
    try {
      const res = await fetch(`${API_BASE}/api/v1/quotes/${quoteCode}/select-option`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_limit: selectedLimit,
          rationale: rationale || null,
          underwriter_id: "system"
        })
      });

      if (!res.ok) throw new Error("Failed to select limit option");

      const data = await res.json();
      const activeSub = get().activeSubmission;

      if (activeSub) {
        await get().fetchCoreSubmissionDetail({
          submission_code: (activeSub as any).submission_code || (activeSub as any).submission_id,
          quote_code: quoteCode,
          version_code: data.new_version_code,
          referral_code: (get().activeReferral as any)?.referral_code || null
        });
      }

      get().fetchSubmissions();
    } catch (err) {
      console.error("Limit selection failed:", err);
    } finally {
      set({ isSelectingLimit: false });
    }
  },

  fetchSubmissions: async () => {
    set({ isLoading: true, error: null });
    
    try {
      // Calculate the date based on the current filter
      const days = get().daysFilter;
      const targetDate = new Date();
      targetDate.setDate(targetDate.getDate() - days);
      const isoDateString = targetDate.toISOString(); // e.g., 2026-02-03T11:53:00.000Z
      
      const res = await fetch(`${API_BASE}/api/v1/frontend/pipeline?created_after=${isoDateString}`);
      if (!res.ok) throw new Error(`Failed to fetch: ${res.statusText}`);
      
      const data = await res.json();
      set({ submissions: data, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  fetchCoreSubmissionDetail: async (row: any) => {
    // Clear cached tab data when switching submissions
    set({
      isLoading: true, error: null,
      commercialTerms: null, riskTerms: null, commercialTermsVersionCode: null,
      riskSignals: [], riskSignalsVersionCode: null,
      lossCohortBenchmarks: [], lossTrendDistribution: [], lossScatterData: [],
      exposureBandBenchmarks: [], exposureTierDistribution: [], exposureScatterData: [],
      modelVersions: [], auditLogs: [],
    });
    try {
      
      const safeFetch = (url) => fetch(url).then(res => res.ok ? res.json() : null).catch(() => null);

      // Core fetches that always rely on the submission_code
      const fetchPromises = [
        safeFetch(`${API_BASE}/api/v1/submissions/${row.submission_code}`),
        safeFetch(`${API_BASE}/api/v1/modelversion/${row.version_code}/all`),
        safeFetch(`${API_BASE}/api/v1/quotes/${row.quote_code}`),
      ];

      const referralPromise = row.referral_code 
        ? safeFetch(`${API_BASE}/api/v1/referrals/${row.referral_code}`)
        : Promise.resolve(null);

      // 2. Execute all network requests in parallel
      const [subData, versionsData, quoteData, referralData] = await Promise.all(
        [
        ...fetchPromises,
        referralPromise
      ]);

      // 3. Update the global store
      if (subData) {
        set({ 
          activeSubmission: subData, 
          activeQuote: quoteData,
          activeVersion: versionsData,
          activeReferral: referralData,
          isLoading: false,
          activeMenu: "Summary"
        });
      } else {
        set({ error: "Failed to load core submission details.", isLoading: false });
      }

    } catch (err) {
      console.error("Failed to fetch submission details:", err);
      set({ error: err.message || "Network error occurred", isLoading: false });
    }
  }
}));