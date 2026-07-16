import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type ReadinessSnapshot } from "@/api/client";
import { useAuth } from "@/auth/AuthProvider";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingScreen } from "@/components/shared/LoadingScreen";

function statusClass(status: string) {
  if (status === "ok") return "text-emerald-700 dark:text-emerald-400";
  if (status === "fail") return "text-red-700 dark:text-red-400";
  return "text-amber-700 dark:text-amber-400";
}

export function AcceptancePage() {
  const { businessId } = useAuth();
  const [data, setData] = useState<ReadinessSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const httpsOk = typeof window !== "undefined" && window.location.protocol === "https:";
  const isLocal =
    typeof window !== "undefined" &&
    (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");

  const load = () => {
    setError(null);
    api
      .readiness(businessId)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load readiness"));
  };

  useEffect(() => {
    load();
  }, [businessId]);

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader title="Final Acceptance" description="Closed-beta readiness status." />
        <Card>
          <CardContent className="p-6 text-sm text-danger">{error}</CardContent>
        </Card>
      </div>
    );
  }

  if (!data) return <LoadingScreen label="Checking readiness…" />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Final Acceptance Checklist"
        description="Readiness for the first closed-beta customer. Keep live booking off until every critical item is green."
      />

      <Card>
        <CardHeader>
          <CardTitle>Score {data.score}/100</CardTitle>
          <CardDescription>
            Environment: {data.environment} · Mode: {data.integration_mode} · Live booking:{" "}
            {data.allow_live_booking ? "ON" : "OFF"}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button onClick={load}>Refresh</Button>
          <Button asChild variant="outline">
            <Link to="/onboarding">Onboarding</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/settings">Settings</Link>
          </Button>
          <Button asChild variant="secondary">
            <Link to="/help">Help</Link>
          </Button>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Integrations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>Retell: {data.retell_connected ? "connected" : "not connected"}</p>
            <p>Cal.com: {data.calcom_connected ? "connected" : "not connected"}</p>
            <p>Twilio: {data.twilio_configured ? "configured" : "placeholder / not set"}</p>
            <p>
              CRM: {data.callers_count} customers · {data.calls_count} calls ·{" "}
              {data.appointments_count} appointments · {data.knowledge_count} KB
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Deployment (browser)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p className={httpsOk || isLocal ? "text-emerald-700 dark:text-emerald-400" : "text-amber-700"}>
              HTTPS: {httpsOk ? "yes" : isLocal ? "local HTTP OK for beta" : "use HTTPS in production"}
            </p>
            <p>Origin: {typeof window !== "undefined" ? window.location.origin : "—"}</p>
            <p>Production build: served via Vite/nginx per deploy target</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Checks</CardTitle>
          <CardDescription>Server-side readiness snapshot for this business.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.checks.map((check) => (
            <div key={check.id} className="flex justify-between gap-4 border-b border-border pb-3 text-sm">
              <div>
                <p className="font-medium">{check.label}</p>
                <p className="text-muted-foreground">{check.detail}</p>
              </div>
              <p className={`shrink-0 font-medium uppercase ${statusClass(check.status)}`}>
                {check.status}
              </p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
