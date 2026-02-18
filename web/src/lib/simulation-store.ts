import { create } from "zustand";
import type { SimulationProgress } from "@/types/simulation";

interface SimulationStore {
  activeSimulationId: string | null;
  progress: SimulationProgress | null;
  status: "idle" | "connecting" | "running" | "completed" | "failed";
  setActiveSimulation: (id: string) => void;
  updateProgress: (progress: SimulationProgress) => void;
  setStatus: (status: SimulationStore["status"]) => void;
  reset: () => void;
}

export const useSimulationStore = create<SimulationStore>((set) => ({
  activeSimulationId: null,
  progress: null,
  status: "idle",
  setActiveSimulation: (id) =>
    set({ activeSimulationId: id, status: "connecting", progress: null }),
  updateProgress: (progress) =>
    set({
      progress,
      status:
        progress.status === "completed"
          ? "completed"
          : progress.status === "failed" || progress.status === "cancelled"
            ? "failed"
            : "running",
    }),
  setStatus: (status) => set({ status }),
  reset: () =>
    set({ activeSimulationId: null, progress: null, status: "idle" }),
}));
