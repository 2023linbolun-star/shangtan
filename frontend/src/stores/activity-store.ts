import { create } from "zustand";

export interface ActivityEntry {
  id: string;
  timestamp: string;
  module: string;
  moduleName: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
}

interface ActivityStore {
  entries: ActivityEntry[];
  maxEntries: number;

  addEntry: (entry: Omit<ActivityEntry, "id">) => void;
  clear: () => void;
}

export const useActivityStore = create<ActivityStore>((set) => ({
  entries: [],
  maxEntries: 50,

  addEntry: (entry) =>
    set((state) => ({
      entries: [
        { ...entry, id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}` },
        ...state.entries,
      ].slice(0, state.maxEntries),
    })),

  clear: () => set({ entries: [] }),
}));
