import type {
  GenerationJob,
  GenerationRequest,
  ProviderInfo,
  QualityReport,
  SearchResult,
  LocalDataset,
  LocalDatasetDescription,
} from "../types";

const API = import.meta.env.VITE_API_URL ?? "/api";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${url}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!response.ok) {
    const content = await response.json().catch(() => ({ detail: response.statusText }));
    const detail = content.detail;
    throw new Error(Array.isArray(detail)
      ? detail.map((item: { msg?: string }) => item.msg ?? "Dato inválido").join(" · ")
      : detail ?? `Error HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  localDatasets: () => request<{ enabled: boolean; datasets: LocalDataset[] }>("/datasets/local"),
  importDataset: (file: File, description: LocalDatasetDescription) =>
    request<LocalDataset>(`/datasets/local?description=${encodeURIComponent(JSON.stringify(description))}`,
      { method: "POST", body: file, headers: { "Content-Type": "application/octet-stream" } }),
  providers: () => request<ProviderInfo[]>("/providers"),
  search: (query: string) => request<SearchResult[]>(`/search?q=${encodeURIComponent(query)}`),
  createGeneration: (payload: GenerationRequest) =>
    request<GenerationJob>("/generations", { method: "POST", body: JSON.stringify(payload) }),
  generation: (id: string) => request<GenerationJob>(`/generations/${id}`),
  cancel: (id: string) => request<GenerationJob>(`/generations/${id}/cancel`, { method: "POST" }),
  quality: (id: string) => request<QualityReport>(`/generations/${id}/quality`),
  artifactUrl: (id: string, artifact: "model" | "metadata" | "sources" | "quality" | "scene" | "attributions") =>
    `${API}/generations/${id}/${artifact}`,
};

