import { useMemo, useState } from "react";
import { PhoneCall } from "lucide-react";
import { Breadcrumb } from "@/components/shared/Breadcrumb";
import { EmptyState } from "@/components/shared/EmptyState";
import { Pagination } from "@/components/shared/Pagination";
import { SearchBar } from "@/components/shared/SearchBar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { formatDateTime, formatDuration } from "@/lib/utils";
import type { Call } from "@/types";

const PAGE_SIZE = 8;

export function CallsPage({
  calls,
  loading,
  selected,
  onSelect,
  onBack,
}: {
  calls: Call[];
  loading: boolean;
  selected: Call | null;
  onSelect: (call: Call | null) => void;
  onBack: () => void;
}) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return calls.filter((call) => {
      if (!q) return true;
      return [call.intent, call.outcome, call.summary, call.transcript, call.retell_call_id]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(q));
    });
  }, [calls, query]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const rows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-72" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (selected) {
    return <CallDetail call={selected} onBack={onBack} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Calls"
        description="Review intent, outcomes, transcripts, and booking status across every conversation."
        actions={<SearchBar value={query} onChange={(value) => { setQuery(value); setPage(1); }} className="w-72" />}
      />

      {!filtered.length ? (
        <EmptyState
          icon={PhoneCall}
          title="No matching calls"
          description="Adjust your search or simulate a completed call webhook."
        />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="border-b border-border bg-muted/40 text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Intent</th>
                    <th className="px-4 py-3 font-medium">Duration</th>
                    <th className="px-4 py-3 font-medium">Outcome</th>
                    <th className="px-4 py-3 font-medium">Appointment</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((call) => (
                    <tr
                      key={call.id}
                      className="cursor-pointer border-b border-border/70 transition-colors hover:bg-muted/40"
                      onClick={() => onSelect(call)}
                    >
                      <td className="px-4 py-3 whitespace-nowrap">{formatDateTime(call.started_at)}</td>
                      <td className="px-4 py-3">{call.intent || "Unknown"}</td>
                      <td className="px-4 py-3">{formatDuration(call.duration_seconds)}</td>
                      <td className="px-4 py-3">
                        <Badge variant="secondary">{call.outcome || "Completed"}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        {call.appointment_booked ? (
                          <Badge variant="success">Booked</Badge>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-4">
              <Pagination page={page} pageCount={pageCount} onChange={setPage} />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function CallDetail({ call, onBack }: { call: Call; onBack: () => void }) {
  return (
    <div className="space-y-6">
      <PageHeader
        breadcrumb={
          <Breadcrumb
            items={[
              { label: "Calls", onClick: onBack },
              { label: call.retell_call_id },
            ]}
          />
        }
        title={call.intent || "Call details"}
        description="Transcript, summary, metadata, and appointment outcome for this conversation."
      />

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Transcript</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-[28rem] overflow-y-auto rounded-2xl border border-border bg-muted/30 p-4 text-sm leading-7 whitespace-pre-wrap text-foreground">
              {call.transcript || "No transcript available for this call."}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-6 text-muted-foreground">
              {call.summary || "No summary generated."}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <Meta label="Started" value={formatDateTime(call.started_at)} />
              <Meta label="Duration" value={formatDuration(call.duration_seconds)} />
              <Meta label="Urgency" value={call.urgency || "—"} />
              <Meta label="Outcome" value={call.outcome || "—"} />
              <Meta label="Retell ID" value={call.retell_call_id} />
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">Appointment</span>
                <Badge variant={call.appointment_booked ? "success" : "secondary"}>
                  {call.appointment_booked ? "Booked" : "Not booked"}
                </Badge>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Recording</CardTitle>
            </CardHeader>
            <CardContent>
              {call.recording_url ? (
                <audio controls className="w-full" src={call.recording_url}>
                  Your browser does not support audio playback.
                </audio>
              ) : (
                <p className="text-sm text-muted-foreground">No recording URL attached to this call yet.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="max-w-[60%] text-right font-medium text-foreground break-all">{value}</span>
    </div>
  );
}
