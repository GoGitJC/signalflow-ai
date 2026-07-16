import { useMemo, useState } from "react";
import { Users } from "lucide-react";
import { api } from "@/api/client";
import { EmptyState } from "@/components/shared/EmptyState";
import { SearchBar } from "@/components/shared/SearchBar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { formatDateTime } from "@/lib/utils";
import type { Appointment, Call, Caller } from "@/types";

export function CustomersPage({ businessId, callers, calls, appointments, loading }: {
  businessId: string; callers: Caller[]; calls: Call[]; appointments: Appointment[]; loading: boolean;
}) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [selected, setSelected] = useState<Caller | null>(null);
  const filtered = callers.filter((customer) => {
    const q = query.trim().toLowerCase();
    return (!q || [customer.name, customer.phone, customer.email, customer.tags.join(" ")].some((value) => value?.toLowerCase().includes(q))) &&
      (status === "all" || customer.status === status);
  });
  const tags = useMemo(() => [...new Set(callers.flatMap((caller) => caller.tags))], [callers]);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-72" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customers"
        description="Customer history, follow-up context, and booking activity in one place."
        actions={<SearchBar value={query} onChange={setQuery} className="w-72" placeholder="Search callers…" />}
      />
      <div className="flex flex-wrap gap-2">
        {["all", "lead", "customer", "closed"].map((item) => <Badge key={item} className="cursor-pointer capitalize" variant={status === item ? "accent" : "secondary"} onClick={() => setStatus(item)}>{item}</Badge>)}
        {tags.slice(0, 6).map((tag) => <Badge key={tag} variant="secondary">{tag}</Badge>)}
      </div>

      {!filtered.length ? (
        <EmptyState
          icon={Users}
          title="No customers yet"
          description="Completed calls with caller identifiers will populate this directory."
        />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-left text-sm">
                <thead className="border-b border-border bg-muted/40 text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 font-medium">Caller</th>
                    <th className="px-4 py-3 font-medium">Phone</th><th className="px-4 py-3 font-medium">Calls</th>
                    <th className="px-4 py-3 font-medium">Last interaction</th><th className="px-4 py-3 font-medium">Tags</th><th className="px-4 py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((customer) => (
                    <tr key={customer.id} className="cursor-pointer border-b border-border/70 hover:bg-muted/40" onClick={() => setSelected(customer)}>
                      <td className="px-4 py-3 font-medium">{customer.name || "Unknown caller"}<div className="text-xs font-normal text-muted-foreground">{customer.email || "No email"}</div></td>
                      <td className="px-4 py-3">{customer.phone}</td><td className="px-4 py-3">{customer.call_count}</td>
                      <td className="px-4 py-3">{formatDateTime(customer.last_interaction_at)}</td>
                      <td className="px-4 py-3">{customer.tags.map((tag) => <Badge key={tag} variant="secondary" className="mr-1">{tag}</Badge>)}</td>
                      <td className="px-4 py-3"><Badge variant={customer.status === "customer" ? "success" : "secondary"}>{customer.status}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
      {selected && <CustomerDetail caller={selected} calls={calls.filter((call) => call.caller_id === selected.id)} appointments={appointments.filter((item) => item.caller_id === selected.id)} businessId={businessId} onClose={() => setSelected(null)} />}
    </div>
  );
}

function CustomerDetail({ caller, calls, appointments, businessId, onClose }: { caller: Caller; calls: Call[]; appointments: Appointment[]; businessId: string; onClose: () => void }) {
  const [notes, setNotes] = useState(caller.notes ?? "");
  const [tags, setTags] = useState(caller.tags.join(", "));
  const save = async () => { await api.updateCaller(caller.id, { notes, tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean) }, businessId); onClose(); };
  return <Card className="border-primary/30"><CardContent className="space-y-4 p-5">
    <div className="flex justify-between"><div><h2 className="font-semibold">{caller.name || caller.phone}</h2><p className="text-sm text-muted-foreground">{caller.phone}</p></div><button className="text-sm text-muted-foreground" onClick={onClose}>Close</button></div>
    <label className="grid gap-1 text-sm">Notes<textarea className="min-h-24 rounded-xl border border-input bg-card p-3" value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
    <label className="grid gap-1 text-sm">Tags<input className="rounded-xl border border-input bg-card p-3" value={tags} onChange={(event) => setTags(event.target.value)} /></label>
    <button className="rounded-xl bg-primary px-3 py-2 text-sm text-primary-foreground" onClick={() => void save()}>Save customer</button>
    <div className="grid gap-3 md:grid-cols-2"><section><h3 className="mb-2 text-sm font-medium">Recent calls</h3>{calls.map((call) => <p key={call.id} className="py-1 text-sm">{formatDateTime(call.started_at)} · {call.intent || "Conversation"}</p>) || <p className="text-sm text-muted-foreground">No calls yet.</p>}</section><section><h3 className="mb-2 text-sm font-medium">Appointments</h3>{appointments.map((item) => <p key={item.id} className="py-1 text-sm">{formatDateTime(item.start_time)} · {item.service}</p>) || <p className="text-sm text-muted-foreground">No appointments yet.</p>}</section></div>
  </CardContent></Card>;
}
