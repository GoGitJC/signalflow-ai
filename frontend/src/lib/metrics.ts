import type { Appointment, Call } from "@/types";

function dayKey(value: string | null | undefined) {
  if (!value) return null;
  return new Date(value).toDateString();
}

export function computeMetrics(calls: Call[], appointments: Appointment[]) {
  const today = new Date().toDateString();
  const todayCalls = calls.filter((call) => dayKey(call.started_at) === today);
  const booked = appointments.length;
  const leads = calls.filter(
    (call) => call.intent === "book_appointment" || call.outcome?.includes("lead") || call.appointment_booked,
  ).length;
  const avgDuration = todayCalls.length
    ? Math.round(todayCalls.reduce((sum, call) => sum + (call.duration_seconds || 0), 0) / todayCalls.length)
    : 0;
  const missed = calls.filter((call) => call.outcome === "missed" || call.outcome === "no_answer").length;
  const conversion = calls.length ? leads / calls.length : 0;
  const revenueOpportunity = leads * 185;

  const last7 = Array.from({ length: 7 }, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() - (6 - index));
    const key = date.toDateString();
    return {
      label: date.toLocaleDateString(undefined, { weekday: "short" }),
      calls: calls.filter((call) => dayKey(call.started_at) === key).length,
      appointments: appointments.filter((item) => dayKey(item.start_time) === key).length,
      leads: calls.filter(
        (call) =>
          dayKey(call.started_at) === key &&
          (call.appointment_booked || call.intent === "book_appointment"),
      ).length,
    };
  });

  return {
    todayCalls: todayCalls.length,
    booked,
    leads,
    avgDuration,
    missed,
    conversion,
    revenueOpportunity,
    upcoming: [...appointments]
      .filter((item) => new Date(item.start_time).getTime() >= Date.now() - 60_000)
      .sort((a, b) => +new Date(a.start_time) - +new Date(b.start_time))
      .slice(0, 5),
    series: last7,
  };
}

export function deriveCustomers(calls: Call[]) {
  const map = new Map<
    string,
    { id: string; calls: number; lastSeen: string | null; intent: string | null; booked: boolean }
  >();
  for (const call of calls) {
    const id = call.caller_id || call.retell_call_id;
    const existing = map.get(id) ?? {
      id,
      calls: 0,
      lastSeen: null,
      intent: null,
      booked: false,
    };
    existing.calls += 1;
    existing.lastSeen = call.started_at;
    existing.intent = call.intent;
    existing.booked = existing.booked || call.appointment_booked;
    map.set(id, existing);
  }
  return [...map.values()].sort((a, b) => +(b.lastSeen || 0) - +(a.lastSeen || 0));
}
