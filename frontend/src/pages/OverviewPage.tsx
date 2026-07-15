import {
  CalendarDays,
  Clock3,
  PhoneCall,
  PhoneMissed,
  Target,
  TrendingUp,
  Users,
} from "lucide-react";
import { SimpleAreaChart, SimpleBarChart } from "@/components/shared/Charts";
import { EmptyState } from "@/components/shared/EmptyState";
import { StatCard } from "@/components/shared/StatCard";
import { StatusIndicator } from "@/components/shared/StatusIndicator";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { currency, formatDateTime, formatDuration, formatPercent } from "@/lib/utils";
import { computeMetrics } from "@/lib/metrics";
import type { Appointment, Call } from "@/types";

export function OverviewPage({
  calls,
  appointments,
  loading,
  apiOnline,
  onOpenCall,
}: {
  calls: Call[];
  appointments: Appointment[];
  loading: boolean;
  apiOnline: boolean;
  onOpenCall: (call: Call) => void;
}) {
  const metrics = computeMetrics(calls, appointments);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-16 w-80" />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="Executive view of receptionist performance, bookings, and lead flow."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Calls today" value={metrics.todayCalls} icon={PhoneCall} hint="Inbound answered" />
        <StatCard label="Appointments booked" value={metrics.booked} icon={CalendarDays} />
        <StatCard label="Leads" value={metrics.leads} icon={Users} />
        <StatCard
          label="Revenue opportunity"
          value={currency(metrics.revenueOpportunity)}
          icon={TrendingUp}
          hint="$185 estimated per qualified lead"
        />
        <StatCard label="Avg call duration" value={formatDuration(metrics.avgDuration)} icon={Clock3} />
        <StatCard label="Missed calls" value={metrics.missed} icon={PhoneMissed} />
        <StatCard label="Conversion rate" value={formatPercent(metrics.conversion)} icon={Target} />
        <StatCard
          label="Upcoming appointments"
          value={metrics.upcoming.length}
          icon={CalendarDays}
          hint="Next window"
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <SimpleAreaChart
            title="Call volume (7 days)"
            data={metrics.series.map((point) => ({ label: point.label, value: point.calls }))}
          />
        </div>
        <SimpleBarChart
          title="Appointments"
          data={metrics.series.map((point) => ({ label: point.label, value: point.appointments }))}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <SimpleAreaChart
          title="Lead trend"
          color="var(--color-accent)"
          data={metrics.series.map((point) => ({ label: point.label, value: point.leads }))}
        />
        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>System status</CardTitle>
            <StatusIndicator status={apiOnline ? "online" : "offline"} />
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            {[
              ["API", apiOnline ? "Healthy" : "Unavailable"],
              ["Webhooks", "Ready"],
              ["Mock providers", "Enabled"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-border bg-muted/40 p-4">
                <div className="text-xs text-muted-foreground">{label}</div>
                <div className="mt-1 text-sm font-medium">{value}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent calls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {calls.slice(0, 5).map((call) => (
              <button
                key={call.id}
                type="button"
                onClick={() => onOpenCall(call)}
                className="flex w-full items-start justify-between gap-3 rounded-xl border border-border px-4 py-3 text-left transition-colors hover:bg-muted/50"
              >
                <div>
                  <div className="text-sm font-medium">{call.intent || "General inquiry"}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{formatDateTime(call.started_at)}</div>
                </div>
                <Badge variant={call.appointment_booked ? "success" : "secondary"}>
                  {call.appointment_booked ? "Booked" : call.outcome || "Completed"}
                </Badge>
              </button>
            ))}
            {!calls.length ? (
              <EmptyState
                icon={PhoneCall}
                title="No calls yet"
                description="Simulate a Retell call-ended webhook to populate this view."
              />
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Upcoming appointments</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {metrics.upcoming.map((item) => (
              <div
                key={item.id}
                className="flex items-start justify-between gap-3 rounded-xl border border-border px-4 py-3"
              >
                <div>
                  <div className="text-sm font-medium">{item.service}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{formatDateTime(item.start_time)}</div>
                </div>
                <Badge variant="accent">{item.status}</Badge>
              </div>
            ))}
            {!metrics.upcoming.length ? (
              <EmptyState
                icon={CalendarDays}
                title="No upcoming appointments"
                description="Booked appointments from completed calls will appear here."
              />
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
