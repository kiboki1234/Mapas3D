import { create } from "zustand";
import type {
  GenerationJob,
  ProviderInfo,
  QualityReport,
  SelectedFeature,
  ViewerStyle,
} from "../types";

interface AppState {
  job: GenerationJob | null;
  providers: ProviderInfo[];
  quality: QualityReport | null;
  selectedFeature: SelectedFeature | null;
  viewerStyle: ViewerStyle;
  activeView: "map" | "3d";
  setJob: (job: GenerationJob | null) => void;
  setProviders: (providers: ProviderInfo[]) => void;
  setQuality: (quality: QualityReport | null) => void;
  setSelectedFeature: (feature: SelectedFeature | null) => void;
  setViewerStyle: (style: ViewerStyle) => void;
  setActiveView: (view: "map" | "3d") => void;
}

export const useAppStore = create<AppState>((set) => ({
  job: null,
  providers: [],
  quality: null,
  selectedFeature: null,
  viewerStyle: "architectural",
  activeView: "map",
  setJob: (job) => set({ job }),
  setProviders: (providers) => set({ providers }),
  setQuality: (quality) => set({ quality }),
  setSelectedFeature: (selectedFeature) => set({ selectedFeature }),
  setViewerStyle: (viewerStyle) => set({ viewerStyle }),
  setActiveView: (activeView) => set({ activeView }),
}));

