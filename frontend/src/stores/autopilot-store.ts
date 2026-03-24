import { create } from "zustand";

export type ModuleMode = "auto" | "review";
export type ModuleStatus = "running" | "idle" | "awaiting_review" | "error";

export interface ModuleState {
  id: string;
  name: string;
  mode: ModuleMode;
  status: ModuleStatus;
  statusText: string;
  pendingReviewCount: number;
}

interface AutopilotStore {
  globalMode: ModuleMode;
  modules: ModuleState[];
  isConnected: boolean;

  setGlobalMode: (mode: ModuleMode) => void;
  setModuleMode: (moduleId: string, mode: ModuleMode) => void;
  updateModuleStatus: (moduleId: string, status: Partial<ModuleState>) => void;
  setConnected: (connected: boolean) => void;
}

const DEFAULT_MODULES: ModuleState[] = [
  { id: "discovery", name: "趋势发现", mode: "auto", status: "idle", statusText: "每4小时扫描", pendingReviewCount: 0 },
  { id: "evaluation", name: "市场评估", mode: "auto", status: "idle", statusText: "等待趋势信号", pendingReviewCount: 0 },
  { id: "sourcing", name: "供应链匹配", mode: "review", status: "idle", statusText: "待触发", pendingReviewCount: 0 },
  { id: "content", name: "内容工厂", mode: "review", status: "idle", statusText: "待触发", pendingReviewCount: 0 },
  { id: "publishing", name: "发布引擎", mode: "auto", status: "idle", statusText: "待触发", pendingReviewCount: 0 },
  { id: "customer_service", name: "AI客服", mode: "auto", status: "idle", statusText: "在线", pendingReviewCount: 0 },
  { id: "analytics", name: "数据分析", mode: "auto", status: "idle", statusText: "每日分析", pendingReviewCount: 0 },
];

export const useAutopilotStore = create<AutopilotStore>((set) => ({
  globalMode: "review",
  modules: DEFAULT_MODULES,
  isConnected: false,

  setGlobalMode: (mode) =>
    set((state) => ({
      globalMode: mode,
      modules: state.modules.map((m) => ({ ...m, mode })),
    })),

  setModuleMode: (moduleId, mode) =>
    set((state) => ({
      modules: state.modules.map((m) =>
        m.id === moduleId ? { ...m, mode } : m
      ),
    })),

  updateModuleStatus: (moduleId, status) =>
    set((state) => ({
      modules: state.modules.map((m) =>
        m.id === moduleId ? { ...m, ...status } : m
      ),
    })),

  setConnected: (connected) => set({ isConnected: connected }),
}));
