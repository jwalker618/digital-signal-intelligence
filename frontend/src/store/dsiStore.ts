import { create } from 'zustand';

export interface DsiState {
  // Navigation & Context State
  activeMenu: string;
  setActiveMenu: (menu: string) => void;
  dateFilter: string;
  setDateFilter: (filter: string) => void;

  // Data State
  submissions: any[];
  activeSubmission: string | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setActiveSubmission: (id: string | null) => void;
  fetchSubmissions: () => Promise<void>;
}

export const useDsiStore = create<DsiState>((set) => ({
  // Navigation Defaults
  activeMenu: "Referral Pipeline",
  setActiveMenu: (menu) => set({ activeMenu: menu }),
  dateFilter: "Including all submissions from 25th February 2026",
  setDateFilter: (filter) => set({ dateFilter: filter }),

  // Data Defaults
  submissions: [],
  activeSubmission: null,
  isLoading: false,
  error: null,

  setActiveSubmission: (id) => set({ activeSubmission: id }),

// 1. Fetch the lightweight list for the tables
  fetchSubmissions: async () => {
    set({ isLoading: true, error: null });
    
    try {
      // Pointing to your custom raw SQL endpoint!
      const res = await fetch("http://localhost:8000/api/v1/workbench-data");
      if (!res.ok) throw new Error(`Failed to fetch: ${res.statusText}`);
      
      const data = await res.json();
      set({ submissions: data, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  // 2. Fetch the MASSIVE payload when a row is clicked
  fetchSubmissionDetail: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      // Pointing to the FastAPI router endpoint that returns the deep detail
      const res = await fetch(`http://localhost:8000/api/v1/submissions/${id}`);
      if (!res.ok) throw new Error("Failed to fetch deep submission details");
      
      const deepData = await res.json();
      
      set({ 
        activeSubmission: deepData, 
        activeMenu: "Workbench", // Automatically switches the screen!
        isLoading: false 
      });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  }
}));