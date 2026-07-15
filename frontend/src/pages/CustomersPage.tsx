import { useMemo, useState } from "react";
import { Users } from "lucide-react";
import { EmptyState } from "@/components/shared/EmptyState";
import { SearchBar } from "@/components/shared/SearchBar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { deriveCustomers } from "@/lib/metrics";
import { formatDateTime } from "@/lib/utils";
import type { Call } from "@/types";

export function CustomersPage({ calls, loading }: { calls: Call[]; loading: boolean }) {
  const [query, setQuery] = useState("");
  const customers = useMemo(() => deriveCustomers(calls), [calls]);
  const filtered = customers.filter((customer) => {
    const q = query.trim().toLowerCase();
    if (!q) return true;
    return customer.id.toLowerCase().includes(q) || (customer.intent || "").toLowerCase().includes(q);
  });

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
        description="Callers inferred from conversation history. Dedicated CRM records arrive with auth."
        actions={<SearchBar value={query} onChange={setQuery} className="w-72" placeholder="Search callers…" />}
      />

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
                    <th className="px-4 py-3 font-medium">Calls</th>
                    <th className="px-4 py-3 font-medium">Last seen</th>
                    <th className="px-4 py-3 font-medium">Latest intent</th>
                    <th className="px-4 py-3 font-medium">Lead</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((customer) => (
                    <tr key={customer.id} className="border-b border-border/70">
                      <td className="px-4 py-3 font-medium">{customer.id.slice(0, 12)}…</td>
                      <td className="px-4 py-3">{customer.calls}</td>
                      <td className="px-4 py-3">{formatDateTime(customer.lastSeen)}</td>
                      <td className="px-4 py-3">{customer.intent || "—"}</td>
                      <td className="px-4 py-3">
                        <Badge variant={customer.booked ? "success" : "secondary"}>
                          {customer.booked ? "Booked" : "Open"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
