import { create } from 'zustand';

export interface DsiState {
  // Navigation & Context State
  activeMenu: string;
  setActiveMenu: (menu: string) => void;
  previousMenu: string;
  updateDecision: (id: string, decision: string) => Promise<void>;
  
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
  fetchSubmissionDetail: (id: string) => Promise<void>;
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

  fetchSubmissionDetail: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`http://localhost:8000/api/v1/submissions/${id}`);
      if (!res.ok) throw new Error("Failed to fetch deep details");
      const deepData = await res.json();
      
      set((state) => ({ 
        activeSubmission: deepData, 
        previousMenu: state.activeMenu, // Remembers Full vs Referral!
        activeMenu: "Workbench", 
        isLoading: false 
      }));
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  updateDecision: async (id: string, decision: string) => {
    try {
      await fetch(`http://localhost:8000/api/v1/submissions/${id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision })
      });
      // Automatically refresh the table data so the row vanishes from the Referral list!
      get().fetchSubmissions(); 
    } catch (err) {
      console.error("Failed to update decision", err);
    }
  }  

}));