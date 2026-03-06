import { create } from 'zustand';

export interface DsiState {
  // Navigation & Context State
  activeMenu: string;
  setActiveMenu: (menu: string) => void;
  previousMenu: string;
  updateDecision: (id: string, decision: string) => Promise<void>;
  navigateBack: () => void; 

  // NEW: Date Filter State
  daysFilter: number;
  setDaysFilter: (days: number) => void;

  // Data State
  submissions: any[];
  activeSubmission: string | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchSubmissions: () => Promise<void>;
  fetchSubmissionDetail: (row: any) => Promise<void>;

  // Referral Actions State
  referralSignals: any[];
  isFetchingSignals: boolean;
  fetchReferralSignals: (referralId: string) => Promise<void>;
  submitSignalOverride: (referralId: string, signalId: string, auditedValue: number, rationale: string) => Promise<void>;

}

export const useDsiStore = create<DsiState>((set, get) => ({
  activeMenu: "Referral Pipeline",
  setActiveMenu: (menu) => set({ activeMenu: menu }),
  previousMenu: "Referral Pipeline",

  // Default to 30 days, just like the backend
  daysFilter: 30,
  setDaysFilter: (days) => {
    set({ daysFilter: days });
    // Automatically re-fetch the data from the backend when the filter changes!
    get().fetchSubmissions(); 
  },

  submissions: [],
  activeSubmission: null,
  isLoading: false,
  error: null,
  referralSignals: [],
  isFetchingSignals: false,

// Add the navigateBack action:
  navigateBack: () => {
    set((state) => ({
      activeMenu: state.previousMenu || "Referral Pipeline",
      activeSubmission: null // Clearing this triggers the UI to revert!
    }));
  },  

  updateDecision: async (referralId: string, decision: string) => {
    try {
      // Hits our strict DDD endpoint
      const res = await fetch(`http://localhost:8000/api/v1/referrals/${referralId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        // Strictly matches the ReferralDecision payload in types.py
        body: JSON.stringify({ 
          decision: decision, // "approve" or "decline"
          notes: ["Quick action applied from pipeline"] 
        })
      });
      
      if (!res.ok) throw new Error("Failed to update decision");
      
      // Refresh the table data so the row vanishes from the Referral list instantly
      get().fetchSubmissions(); 
    } catch (err) {
      console.error("Failed to update decision", err);
    }
  }, 

  fetchReferralSignals: async (referralId: string) => {
    set({ isFetchingSignals: true });
    try {
      const res = await fetch(`http://localhost:8000/api/v1/referrals/${referralId}/signals?include_all=true`);
      if (!res.ok) throw new Error("Failed to fetch signals");
      const data = await res.json();
      set({ referralSignals: data.signals || [], isFetchingSignals: false });
    } catch (err) {
      console.error(err);
      set({ isFetchingSignals: false });
    }
  },

  submitSignalOverride: async (referralId: string, signalId: string, auditedValue: number, rationale: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/referrals/${referralId}/signals/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          signal_id: signalId, 
          audited_value: auditedValue, 
          rationale: rationale,
          underwriter_id: "system" // Replace with real auth ID later
        })
      });
      
      if (!res.ok) throw new Error("Failed to override signal");
      
      // 1. Refresh the signals to show the new audited value
      await get().fetchReferralSignals(referralId);
      
      // 2. Refresh the whole submission to pull the NEW Score and Premium (v2+ Model Version)!
      const currentRow = get().activeSubmission;
      if (currentRow) {
        await get().fetchSubmissionDetail(currentRow);
      }
    } catch (err) {
      console.error("Override failed", err);
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
      
      // Pass the date to your backend!
      const res = await fetch(`http://localhost:8000/api/v1/workbench-data?created_after=${isoDateString}`);
      if (!res.ok) throw new Error(`Failed to fetch: ${res.statusText}`);
      
      const data = await res.json();
      set({ submissions: data, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  fetchSubmissionDetail: async (row: any) => {
    set({ isLoading: true, error: null });
    try {
      // Fetch the deep analysis data using the quote_id from the row
      const res = await fetch(`http://localhost:8000/api/v1/quotes/${row.quote_code}`);
      if (!res.ok) throw new Error("Failed to fetch deep details");
      const deepData = await res.json();
      
      set((state) => ({ 
        // Merge the UI row (which has entity_name) with the deep API data
        activeSubmission: { ...row, ...deepData }, 
        previousMenu: state.activeMenu, // Remembers where we came from
        activeMenu: "Summary", 
        isLoading: false 
      }));
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  }

}))
;