import { useCallback, useEffect, useMemo, useState } from "react";
import { api, getBusinessId } from "@/api/client";
import type { Appointment, Call, KnowledgeEntry, LoadState } from "@/types";

export type DashboardData = {
  businessId: string;
  calls: Call[];
  appointments: Appointment[];
  knowledge: KnowledgeEntry[];
  status: LoadState;
  error: string;
  apiOnline: boolean;
  reload: () => Promise<void>;
};

export function useDashboardData(): DashboardData {
  const businessId = useMemo(() => getBusinessId(), []);
  const [calls, setCalls] = useState<Call[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeEntry[]>([]);
  const [status, setStatus] = useState<LoadState>("idle");
  const [error, setError] = useState("");
  const [apiOnline, setApiOnline] = useState(true);

  const reload = useCallback(async () => {
    if (!businessId) {
      setStatus("error");
      setError("Set VITE_BUSINESS_ID or localStorage key signalflow_business_id to load live data.");
      return;
    }
    setStatus("loading");
    setError("");
    try {
      const [health, nextCalls, nextAppointments, nextKnowledge] = await Promise.all([
        api
          .health()
          .then(() => true)
          .catch(() => false),
        api.calls(businessId),
        api.appointments(businessId),
        api.knowledge(businessId),
      ]);
      setApiOnline(health);
      setCalls(nextCalls);
      setAppointments(nextAppointments);
      setKnowledge(nextKnowledge);
      setStatus("success");
    } catch (err) {
      setApiOnline(false);
      setStatus("error");
      setError(err instanceof Error ? err.message : "Unable to load dashboard data");
    }
  }, [businessId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { businessId, calls, appointments, knowledge, status, error, apiOnline, reload };
}
