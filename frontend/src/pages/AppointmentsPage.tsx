import { CalendarDays } from "lucide-react";
import { EmptyState } from "@/components/shared/EmptyState";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { formatDateTime } from "@/lib/utils";
import type { Appointment } from "@/types";

export function AppointmentsPage({
  appointments,
  loading,
}: {
  appointments: Appointment[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-80" />
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Appointments"
        description="Confirmed and pending bookings captured by your AI receptionist."
      />
      {!appointments.length ? (
        <EmptyState
          icon={CalendarDays}
          title="No appointments yet"
          description="When a call ends with a booking, it will appear here automatically."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {appointments.map((item) => (
            <Card key={item.id}>
              <CardContent className="flex items-start justify-between gap-4 p-5">
                <div>
                  <div className="text-base font-semibold">{item.service}</div>
                  <div className="mt-2 text-sm text-muted-foreground">{formatDateTime(item.start_time)}</div>
                  <div className="mt-3 text-xs text-muted-foreground">Caller {item.caller_id.slice(0, 8)}…</div>
                </div>
                <Badge variant="accent" className="capitalize">
                  {item.status}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
