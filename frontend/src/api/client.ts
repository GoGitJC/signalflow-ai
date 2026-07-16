import type { Appointment, AuditEvent, Call, Caller, KnowledgeEntry, KnowledgeVersion, VoiceAgent, AnalyticsSummary } from "@/types";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function getBusinessId(): string {
  return import.meta.env.VITE_BUSINESS_ID ?? localStorage.getItem("signalflow_business_id") ?? "";
}

export function setBusinessId(id: string) {
  localStorage.setItem("signalflow_business_id", id);
}

export type SessionUser = {
  id: string;
  business_id: string;
  name: string;
  email: string;
  role: string;
  email_verified: boolean;
  created_at?: string;
};

export type SessionResponse = {
  user_id: string;
  business_id: string;
  role: string;
  email: string;
  name: string;
  email_verified: boolean;
  expires_in: number;
};

type RequestOptions = RequestInit & { skipAuthRefresh?: boolean };

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API}/api/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    })
      .then((response) => response.ok)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

async function request<T>(path: string, options?: RequestOptions): Promise<T> {
  const { skipAuthRefresh, ...init } = options ?? {};
  const response = await fetch(`${API}${path}`, {
    credentials: "include",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
  });

  if (response.status === 401 && !skipAuthRefresh && !path.startsWith("/api/auth/")) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return request<T>(path, { ...options, skipAuthRefresh: true });
    }
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    const error = new Error(
      typeof body.detail === "string" ? body.detail : response.statusText,
    ) as Error & { status?: number };
    error.status = response.status;
    throw error;
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

export type Invitation = {
  id: string;
  business_id: string;
  email: string;
  role: string;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
  invite_token?: string | null;
};

export const api = {
  health: () => request<{ status: string; service: string }>("/health", { skipAuthRefresh: true }),

  register: (payload: {
    business_name: string;
    name: string;
    email: string;
    password: string;
    remember_me?: boolean;
  }) =>
    request<SessionResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
      skipAuthRefresh: true,
    }),

  login: (payload: { email: string; password: string; remember_me?: boolean }) =>
    request<SessionResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
      skipAuthRefresh: true,
    }),

  refresh: () =>
    request<SessionResponse>("/api/auth/refresh", {
      method: "POST",
      skipAuthRefresh: true,
    }),

  logout: () =>
    request<{ detail: string }>("/api/auth/logout", {
      method: "POST",
      skipAuthRefresh: true,
    }),

  me: () => request<SessionUser>("/api/auth/me", { skipAuthRefresh: true }),

  forgotPassword: (email: string) =>
    request<{ detail: string; reset_token?: string }>("/api/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
      skipAuthRefresh: true,
    }),

  resetPassword: (token: string, password: string) =>
    request<{ detail: string }>("/api/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, password }),
      skipAuthRefresh: true,
    }),

  verifyEmail: (token: string) =>
    request<{ detail: string }>("/api/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),

  listUsers: () => request<SessionUser[]>("/api/auth/users"),

  listInvitations: () => request<Invitation[]>("/api/auth/invitations"),

  createInvitation: (payload: { email: string; role: string }) =>
    request<Invitation>("/api/auth/invitations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  acceptInvitation: (payload: { token: string; name: string; password: string }) =>
    request<SessionResponse>("/api/auth/invitations/accept", {
      method: "POST",
      body: JSON.stringify(payload),
      skipAuthRefresh: true,
    }),

  calls: (businessId: string) => request<Call[]>(`/api/businesses/${businessId}/calls`),
  call: (callId: string, businessId: string) =>
    request<Call>(`/api/calls/${callId}?business_id=${businessId}`),
  appointments: (businessId: string) =>
    request<Appointment[]>(`/api/businesses/${businessId}/appointments`),
  callers: (businessId: string) => request<Caller[]>(`/api/businesses/${businessId}/callers`),
  updateCaller: (
    id: string,
    payload: Partial<Pick<Caller, "name" | "email" | "notes" | "tags" | "status">>,
  ) =>
    request<Caller>(`/api/callers/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
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
    request<void>(`/api/knowledge-base/${id}`, { method: "DELETE" }),
  knowledgeVersions: (entryId: string) =>
    request<KnowledgeVersion[]>(`/api/knowledge-base/${entryId}/versions`),
  bulkKnowledge: (businessId: string, entries: Array<Omit<KnowledgeEntry, "id">>) =>
    request<{ created: number; ids: string[] }>(`/api/businesses/${businessId}/knowledge-base/bulk`, {
      method: "POST",
      body: JSON.stringify({ entries }),
    }),
  analyticsSummary: (businessId: string, range: string) =>
    request<AnalyticsSummary>(`/api/businesses/${businessId}/analytics/summary?range=${range}`),
  voiceAgents: (businessId: string) =>
    request<VoiceAgent[]>(`/api/businesses/${businessId}/voice-agents`),
  updateVoiceAgent: (id: string, payload: Partial<VoiceAgent>) =>
    request<VoiceAgent>(`/api/voice-agents/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  auditEvents: (businessId: string) =>
    request<AuditEvent[]>(`/api/businesses/${businessId}/audit-events`),
  retellStatus: (businessId: string) =>
    request<RetellIntegrationStatus>("/api/integrations/retell/status"),
  saveRetell: (
    businessId: string,
    payload: { api_key: string; agent_id?: string; agent_name?: string; confirm_replace?: boolean },
  ) =>
    request<RetellIntegrationStatus>("/api/integrations/retell", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  testRetell: (businessId: string) =>
    request<ConnectionTestResult>("/api/integrations/retell/test", { method: "POST" }),
  calcomStatus: (businessId: string) =>
    request<CalComIntegrationStatus>("/api/integrations/calcom/status"),
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
      body: JSON.stringify(payload),
    }),
  testCalcom: (businessId: string) =>
    request<ConnectionTestResult>("/api/integrations/calcom/test", { method: "POST" }),
};
