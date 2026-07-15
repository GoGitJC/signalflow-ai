import { SimpleAreaChart, SimpleBarChart } from "@/components/shared/Charts";
import { StatCard } from "@/components/shared/StatCard";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { computeMetrics } from "@/lib/metrics";
import { currency, formatPercent } from "@/lib/utils";
import type { Appointment, Call } from "@/types";
import { PhoneCall, Target, TrendingUp } from "lucide-react";

export function AnalyticsPage({
  calls,
  appointments,
  loading,
}: {
  calls: Call[];
  appointments: Appointment[];
  loading: boolean;
}) {
  const metrics = computeMetrics(calls, appointments);

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
        description="Trend lines derived from live call and appointment data in this workspace."
      />
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Total calls" value={calls.length} icon={PhoneCall} />
        <StatCard label="Conversion" value={formatPercent(metrics.conversion)} icon={Target} />
        <StatCard label="Pipeline value" value={currency(metrics.revenueOpportunity)} icon={TrendingUp} />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <SimpleAreaChart
          title="Calls over time"
          data={metrics.series.map((point) => ({ label: point.label, value: point.calls }))}
        />
        <SimpleBarChart
          title="Leads over time"
          data={metrics.series.map((point) => ({ label: point.label, value: point.leads }))}
        />
      </div>
    </div>
  );
}
