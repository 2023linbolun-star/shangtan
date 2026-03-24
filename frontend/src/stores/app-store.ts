import { create } from "zustand";

interface AppStore {
  currentStore: string;
  notifications: number;
  setCurrentStore: (store: string) => void;
  setNotifications: (n: number) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  currentStore: "我的店铺",
  notifications: 0,
  setCurrentStore: (store) => set({ currentStore: store }),
  setNotifications: (n) => set({ notifications: n }),
}));
