import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useAuth } from "@/auth/AuthProvider";
import { businessKeys, useBusinessQuery } from "@/hooks/useBusinessQuery";
import type { Appointment, Call, Caller, KnowledgeEntry, LoadState } from "@/types";

export type DashboardData = {
  businessId: string;
  calls: Call[];
  appointments: Appointment[];
  knowledge: KnowledgeEntry[];
  callers: Caller[];
  status: LoadState;
  error: string;
  apiOnline: boolean;
  reload: () => Promise<void>;
};

export function useDashboardData(): DashboardData {
  const { businessId, status: authStatus } = useAuth();
  const client = useQueryClient();
  const enabled = Boolean(businessId) && authStatus === "authenticated";
  const callsQuery = useBusinessQuery(
    businessKeys.calls(businessId),
    () => api.calls(businessId),
    enabled ? businessId : "",
  );
  const appointmentsQuery = useBusinessQuery(
    businessKeys.appointments(businessId),
    () => api.appointments(businessId),
    enabled ? businessId : "",
  );
  const knowledgeQuery = useBusinessQuery(
    businessKeys.knowledge(businessId),
    () => api.knowledge(businessId),
    enabled ? businessId : "",
  );
  const callersQuery = useBusinessQuery(
    businessKeys.callers(businessId),
    () => api.callers(businessId),
    enabled ? businessId : "",
  );
  const healthQuery = useBusinessQuery(businessKeys.health, api.health, "health");
  const queries = [callsQuery, appointmentsQuery, knowledgeQuery, callersQuery];
  const status: LoadState =
    authStatus === "loading" || !enabled
      ? "loading"
      : queries.some((query) => query.isError)
        ? "error"
        : queries.some((query) => query.isLoading)
          ? "loading"
          : "success";
  const error = queries.find((query) => query.error)?.error instanceof Error
    ? (queries.find((query) => query.error)?.error as Error).message
    : "";
  const reload = useCallback(
    () => client.invalidateQueries({ queryKey: businessKeys.root(businessId) }).then(() => undefined),
    [businessId, client],
  );

  return {
    businessId,
    calls: callsQuery.data ?? [],
    appointments: appointmentsQuery.data ?? [],
    knowledge: knowledgeQuery.data ?? [],
    callers: callersQuery.data ?? [],
    status,
    error,
    apiOnline: !healthQuery.isError,
    reload,
  };
}
