import type { Appointment, Call, KnowledgeEntry } from "@/types";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const OWNER_TOKEN = import.meta.env.VITE_OWNER_API_TOKEN ?? "";

const ACCESS_TOKEN_KEY = "signalflow_access_token";

export function getBusinessId(): string {
  return import.meta.env.VITE_BUSINESS_ID ?? localStorage.getItem("signalflow_business_id") ?? "";
}

export function setBusinessId(id: string) {
  localStorage.setItem("signalflow_business_id", id);
}

export function getAccessToken(): string {
  return localStorage.getItem(ACCESS_TOKEN_KEY) ?? "";
}

export function setAccessToken(token: string | null) {
  if (token) localStorage.setItem(ACCESS_TOKEN_KEY, token);
  else localStorage.removeItem(ACCESS_TOKEN_KEY);
}

function authHeaders(businessId: string): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Business-Id": businessId,
  };
  const jwt = getAccessToken();
  if (jwt) {
    headers.Authorization = `Bearer ${jwt}`;
  } else if (OWNER_TOKEN) {
    headers["X-Owner-Token"] = OWNER_TOKEN;
  }
  return headers;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body.detail === "string" ? body.detail : response.statusText);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type RetellIntegrationStatus = {
  connected: boolean;
  mode: string;
  agent_name?: string | null;
  agent_id_masked?: string | null;
  webhook_url?: string | null;
  webhook_configured: boolean;
  last_test_at?: string | null;
  last_test_status?: string | null;
  last_test_error?: string | null;
};

export type CalComIntegrationStatus = {
  connected: boolean;
  mode: string;
  event_type_name?: string | null;
  event_type_id?: string | null;
  event_type_slug?: string | null;
  username?: string | null;
  last_test_at?: string | null;
  last_test_status?: string | null;
  last_test_error?: string | null;
};

export type ConnectionTestResult = {
  ok: boolean;
  mocked: boolean;
  message?: string | null;
};

export const api = {
  health: () => request<{ status: string; service: string }>("/health"),
  calls: (businessId: string) =>
    request<Call[]>(`/api/businesses/${businessId}/calls`, {
      headers: authHeaders(businessId),
    }),
  call: (callId: string, businessId: string) =>
    request<Call>(`/api/calls/${callId}?business_id=${businessId}`, {
      headers: authHeaders(businessId),
    }),
  appointments: (businessId: string) =>
    request<Appointment[]>(`/api/businesses/${businessId}/appointments`, {
      headers: authHeaders(businessId),
    }),
  knowledge: (businessId: string) =>
    request<KnowledgeEntry[]>(`/api/businesses/${businessId}/knowledge-base`, {
      headers: authHeaders(businessId),
    }),
  addKnowledge: (businessId: string, payload: Omit<KnowledgeEntry, "id">) =>
    request<KnowledgeEntry>(`/api/businesses/${businessId}/knowledge-base`, {
      method: "POST",
      headers: authHeaders(businessId),
      body: JSON.stringify(payload),
    }),
  updateKnowledge: (id: string, payload: Partial<KnowledgeEntry>, businessId?: string) => {
    const bid = businessId ?? getBusinessId();
    return request<KnowledgeEntry>(`/api/knowledge-base/${id}`, {
      method: "PATCH",
      headers: authHeaders(bid),
      body: JSON.stringify(payload),
    });
  },
  deleteKnowledge: (id: string, businessId?: string) => {
    const bid = businessId ?? getBusinessId();
    return fetch(`${API}/api/knowledge-base/${id}`, {
      method: "DELETE",
      headers: authHeaders(bid),
    }).then((response) => {
      if (!response.ok) throw new Error("Failed to delete knowledge entry");
    });
  },
  retellStatus: (businessId: string) =>
    request<RetellIntegrationStatus>("/api/integrations/retell/status", {
      headers: authHeaders(businessId),
    }),
  saveRetell: (
    businessId: string,
    payload: { api_key: string; agent_id?: string; agent_name?: string; confirm_replace?: boolean },
  ) =>
    request<RetellIntegrationStatus>("/api/integrations/retell", {
      method: "PUT",
      headers: authHeaders(businessId),
      body: JSON.stringify(payload),
    }),
  testRetell: (businessId: string) =>
    request<ConnectionTestResult>("/api/integrations/retell/test", {
      method: "POST",
      headers: authHeaders(businessId),
    }),
  calcomStatus: (businessId: string) =>
    request<CalComIntegrationStatus>("/api/integrations/calcom/status", {
      headers: authHeaders(businessId),
    }),
  saveCalcom: (
    businessId: string,
    payload: {
      api_key: string;
      event_type_id?: string;
      event_type_slug?: string;
      username?: string;
      confirm_replace?: boolean;
    },
  ) =>
    request<CalComIntegrationStatus>("/api/integrations/calcom", {
      method: "PUT",
      headers: authHeaders(businessId),
      body: JSON.stringify(payload),
    }),
  testCalcom: (businessId: string) =>
    request<ConnectionTestResult>("/api/integrations/calcom/test", {
      method: "POST",
      headers: authHeaders(businessId),
    }),
};
