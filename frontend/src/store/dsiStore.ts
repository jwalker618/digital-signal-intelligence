import { create } from 'zustand';

interface DsiState {
  submissions: any[];
  activeSubmission: any | null;
  isLoading: boolean;
  error: string | null;
  fetchSubmissions: () => Promise<void>;
  setActiveSubmission: (id: string) => void;
}

export const useDsiStore = create<DsiState>((set) => ({
  submissions: [],
  activeSubmission: null,
  isLoading: false,
  error: null,

  fetchSubmissions: async () => {
    set({ isLoading: true, error: null });
    try {
      // Fetch from our new, custom joined endpoint
      const res = await fetch("http://localhost:8000/api/v1/workbench-data");
      if (!res.ok) throw new Error("Failed to fetch workbench data");
      
      const subList = await res.json();
      
      set({ submissions: subList, isLoading: false });
      
      // Auto-select the first item
      if (subList.length > 0) {
        set({ activeSubmission: subList[0] });
      }
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  setActiveSubmission: (id: string) => {
    // Instantly switch the active submission without a network call
    set((state) => ({
      activeSubmission: state.submissions.find(s => s.id === id) || null
    }));
  }
}));