import type {
  GenerationJob,
  GenerationRequest,
  ProviderInfo,
  QualityReport,
  SearchResult,
} from "../types";

const API = import.meta.env.VITE_API_URL ?? "/api";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${url}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!response.ok) {
    const content = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(content.detail ?? `Error HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
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

