import { create } from "zustand";

interface PipelineStep {
  id: string;
  type: string;
  order: number;
  status: string;
  output_data: any;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

interface PipelineData {
  id: string;
  name: string;
  keyword: string;
  platforms: string[];
  status: string;
  created_at: string;
  steps: PipelineStep[];
}

interface PipelineStore {
  currentPipeline: PipelineData | null;
  pipelines: PipelineData[];
  isRunning: boolean;

  setCurrentPipeline: (pipeline: PipelineData | null) => void;
  updatePipeline: (pipeline: PipelineData) => void;
  setPipelines: (pipelines: PipelineData[]) => void;
  setRunning: (running: boolean) => void;
}

export const usePipelineStore = create<PipelineStore>((set) => ({
  currentPipeline: null,
  pipelines: [],
  isRunning: false,

  setCurrentPipeline: (pipeline) => set({ currentPipeline: pipeline }),
  updatePipeline: (pipeline) =>
    set((state) => ({
      currentPipeline:
        state.currentPipeline?.id === pipeline.id ? pipeline : state.currentPipeline,
      pipelines: state.pipelines.map((p) =>
        p.id === pipeline.id ? pipeline : p
      ),
    })),
  setPipelines: (pipelines) => set({ pipelines }),
  setRunning: (running) => set({ isRunning: running }),
}));
