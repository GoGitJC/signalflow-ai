import type { Appointment, Call, KnowledgeEntry } from "@/types";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function getBusinessId(): string {
  return import.meta.env.VITE_BUSINESS_ID ?? localStorage.getItem("signalflow_business_id") ?? "";
}

export function setBusinessId(id: string) {
  localStorage.setItem("signalflow_business_id", id);
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body.detail === "string" ? body.detail : response.statusText);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; service: string }>("/health"),
  calls: (businessId: string) => request<Call[]>(`/api/businesses/${businessId}/calls`),
  call: (callId: string, businessId: string) =>
    request<Call>(`/api/calls/${callId}?business_id=${businessId}`),
  appointments: (businessId: string) =>
    request<Appointment[]>(`/api/businesses/${businessId}/appointments`),
  knowledge: (businessId: string) =>
    request<KnowledgeEntry[]>(`/api/businesses/${businessId}/knowledge-base`),
  addKnowledge: (businessId: string, payload: Omit<KnowledgeEntry, "id">) =>
    request<KnowledgeEntry>(`/api/businesses/${businessId}/knowledge-base`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateKnowledge: (id: string, payload: Partial<KnowledgeEntry>) =>
    request<KnowledgeEntry>(`/api/knowledge-base/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteKnowledge: (id: string) =>
    fetch(`${API}/api/knowledge-base/${id}`, { method: "DELETE" }).then((response) => {
      if (!response.ok) throw new Error("Failed to delete knowledge entry");
    }),
};
