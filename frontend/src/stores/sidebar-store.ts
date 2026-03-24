import { create } from "zustand";

interface SidebarStore {
  collapsed: boolean;
  activeModule: string;
  toggle: () => void;
  setActiveModule: (module: string) => void;
}

export const useSidebarStore = create<SidebarStore>((set) => ({
  collapsed: false,
  activeModule: "",
  toggle: () => set((s) => ({ collapsed: !s.collapsed })),
  setActiveModule: (module) => set({ activeModule: module }),
}));
