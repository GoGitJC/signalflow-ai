import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getBusinessId } from "@/api/client";
import type { KnowledgeEntry } from "@/types";

export const businessKeys = {
  root: (businessId: string) => ["business", businessId] as const,
  calls: (businessId: string) => [...businessKeys.root(businessId), "calls"] as const,
  appointments: (businessId: string) => [...businessKeys.root(businessId), "appointments"] as const,
  knowledge: (businessId: string) => [...businessKeys.root(businessId), "knowledge"] as const,
  callers: (businessId: string) => [...businessKeys.root(businessId), "callers"] as const,
  health: ["health"] as const,
  analytics: (businessId: string, range: string) => [...businessKeys.root(businessId), "analytics", range] as const,
  voiceAgents: (businessId: string) => [...businessKeys.root(businessId), "voice-agents"] as const,
  audit: (businessId: string) => [...businessKeys.root(businessId), "audit"] as const,
};

const enabled = (businessId: string) => Boolean(businessId);

export function useBusinessQuery<T>(key: readonly unknown[], queryFn: () => Promise<T>, businessId = getBusinessId()) {
  return useQuery({ queryKey: key, queryFn, enabled: enabled(businessId), staleTime: 30_000 });
}

export function useInvalidateBusiness(businessId = getBusinessId()) {
  const client = useQueryClient();
  return () => client.invalidateQueries({ queryKey: businessKeys.root(businessId) });
}

export function useKnowledgeMutation(businessId: string) {
  const invalidate = useInvalidateBusiness(businessId);
  return useMutation({
    mutationFn: (entries: Array<Omit<KnowledgeEntry, "id">>) => api.bulkKnowledge(businessId, entries),
    onSuccess: invalidate,
  });
}
