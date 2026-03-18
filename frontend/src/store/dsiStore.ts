import { create } from 'zustand';
import { ReactNode } from 'react';

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

  // RiskTab
  riskSignals: any[];
  isFetchingRiskSignals: boolean;
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

  // Default Risk Tab
  riskSignals: [],
  isFetchingRiskSignals: false,

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
      const res = await fetch(`http://localhost:8000/api/v1/quotes/${quoteCode}/resolve`, {
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

  fetchRiskSignals: async (versionCode: string) => {
    set({ isFetchingRiskSignals: true });
    try {
      const res = await fetch(`http://localhost:8000/api/v1/frontend/${versionCode}/signals`);
      if (res.ok) {
        const data = await res.json();
        set({ riskSignals: data, isFetchingRiskSignals: false });
      } else {
        set({ riskSignals: [], isFetchingRiskSignals: false });
      }
    } catch (err) {
      console.error("Failed to fetch risk signals:", err);
      set({ riskSignals: [], isFetchingRiskSignals: false });
    }
  },

  fetchLossAnalytics: async (coverage: string, daysFilter = 365) => {
    set({ isFetchingLossAnalytics: true });
    
    try {
      // Calculate the 'created_after' date constraint
      const targetDate = new Date();
      targetDate.setDate(targetDate.getDate() - daysFilter);
      const isoDateString = targetDate.toISOString(); 

      const baseUrl = 'http://localhost:8000/api/v1/analytics/loss';
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
    set({ isFetchingExposureAnalytics: true });
    
    try {
      const targetDate = new Date();
      targetDate.setDate(targetDate.getDate() - daysFilter);
      const isoDateString = targetDate.toISOString(); 

      const baseUrl = 'http://localhost:8000/api/v1/analytics/exposure';
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
    try {
      // Fetch both simultaneously
      const [versionsRes, logsRes] = await Promise.all([
        fetch(`http://localhost:8000/api/v1/submissions/${submissionCode}/model_versions`),
      ]);

      if (versionsRes.ok && logsRes.ok) {
        const versionsData = await versionsRes.json();
        const logsData = await logsRes.json();
        set({ 
          modelVersions: versionsData.versions || [], 
          auditLogs: logsData.logs || [] 
        });
      }
    } catch (err) {
      console.error("Failed to fetch history", err);
    }
  },

  fetchReferralSignals: async (submissionCode: string) => {
    set({ isFetchingSignals: true });
    try {
      const res = await fetch(`http://localhost:8000/api/v1/model_versions/${submissionCode}/submissionshistory/all`);
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
      const res = await fetch(`http://localhost:8000/api/v1/signals/${quoteCode}/override`, {
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
      const quoteRes = await fetch(`http://localhost:8000/api/v1/quotes/${quoteCode}`);
      
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

  fetchSubmissions: async () => {
    set({ isLoading: true, error: null });
    
    try {
      // Calculate the date based on the current filter
      const days = get().daysFilter;
      const targetDate = new Date();
      targetDate.setDate(targetDate.getDate() - days);
      const isoDateString = targetDate.toISOString(); // e.g., 2026-02-03T11:53:00.000Z
      
      const res = await fetch(`http://localhost:8000/api/v1/frontend/pipeline?created_after=${isoDateString}`);
      if (!res.ok) throw new Error(`Failed to fetch: ${res.statusText}`);
      
      const data = await res.json();
      set({ submissions: data, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  fetchCoreSubmissionDetail: async (row: any) => {
    set({ isLoading: true, error: null });
    try {
      
      const safeFetch = (url) => fetch(url).then(res => res.ok ? res.json() : null).catch(() => null);

      // Core fetches that always rely on the submission_code
      const fetchPromises = [
        safeFetch(`http://localhost:8000/api/v1/submissions/${row.submission_code}`),
        safeFetch(`http://localhost:8000/api/v1/modelversion/${row.version_code}/all`),
        safeFetch(`http://localhost:8000/api/v1/quotes/${row.quote_code}`),
      ];

      const referralPromise = row.referral_code 
        ? safeFetch(`http://localhost:8000/api/v1/referrals/${row.referral_code}`)
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