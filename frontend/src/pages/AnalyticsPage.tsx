import { useState } from "react";
import { SimpleAreaChart, SimpleBarChart } from "@/components/shared/Charts";
import { StatCard } from "@/components/shared/StatCard";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { api } from "@/api/client";
import { useBusinessQuery, businessKeys } from "@/hooks/useBusinessQuery";
import { formatDuration, formatPercent } from "@/lib/utils";
import type { Appointment, Call } from "@/types";
import { PhoneCall, Target, TrendingUp } from "lucide-react";

export function AnalyticsPage({
  calls,
  appointments,
  businessId,
  loading,
}: {
  calls: Call[];
  appointments: Appointment[];
  businessId: string;
  loading: boolean;
}) {
  const [range, setRange] = useState("7d");
  const summaryQuery = useBusinessQuery(businessKeys.analytics(businessId, range), () => api.analyticsSummary(businessId, range), businessId);
  const summary = summaryQuery.data;

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-72" />
        <div className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics"
        description="Executive performance across calls, bookings, and AI resolution."
        actions={<div className="flex rounded-xl border border-border p-1">{["7d", "30d", "month"].map((item) => <button key={item} className={`rounded-lg px-3 py-1 text-sm ${range === item ? "bg-muted font-medium" : "text-muted-foreground"}`} onClick={() => setRange(item)}>{item}</button>)}</div>}
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Calls today" value={summary?.calls_today ?? calls.length} icon={PhoneCall} />
        <StatCard label="Bookings" value={summary?.bookings ?? appointments.length} icon={Target} />
        <StatCard label="Conversion" value={formatPercent(summary?.conversion_rate ?? 0)} icon={TrendingUp} />
        <StatCard label="Avg. duration" value={formatDuration(summary?.average_duration_seconds ?? 0)} icon={PhoneCall} />
        <StatCard label="Missed calls" value={summary?.missed_calls ?? 0} icon={PhoneCall} />
        <StatCard label="Transfers" value={summary?.transfers ?? 0} icon={PhoneCall} />
        <StatCard label="AI resolution" value={formatPercent(summary?.ai_resolution_rate ?? 0)} icon={Target} />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <SimpleAreaChart
          title="Calls over time"
          data={(summary?.series ?? []).map((point) => ({ label: point.label, value: point.calls }))}
        />
        <SimpleBarChart
          title="Bookings over time"
          data={(summary?.series ?? []).map((point) => ({ label: point.label, value: point.bookings }))}
        />
      </div>
      <div className="grid gap-4 md:grid-cols-2"><SimpleBarChart title="Booking funnel" data={Object.entries(summary?.booking_funnel ?? {}).map(([label, value]) => ({ label, value }))} /><SimpleBarChart title="Lead sources" data={Object.entries(summary?.lead_sources ?? {}).map(([label, value]) => ({ label, value }))} /></div>
    </div>
  );
}
