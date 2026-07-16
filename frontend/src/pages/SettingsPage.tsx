import { useEffect, useState } from "react";
import {
  api,
  getBusinessId,
  setBusinessId,
  type CalComIntegrationStatus,
  type RetellIntegrationStatus,
} from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/layout/PageHeader";
import { useToast } from "@/hooks/toast-context";

type IntegrationCardProps = {
  title: string;
  description: string;
  businessId: string;
  connected: boolean;
  lastTestAt?: string | null;
  lastTestStatus?: string | null;
  lastTestError?: string | null;
  details: Array<{ label: string; value?: string | null }>;
  onSave: (apiKey: string, confirmReplace: boolean) => Promise<void>;
  onTest: () => Promise<void>;
  extraFields?: React.ReactNode;
};

function IntegrationCard({
  title,
  description,
  connected,
  lastTestAt,
  lastTestStatus,
  lastTestError,
  details,
  onSave,
  onTest,
  extraFields,
}: IntegrationCardProps) {
  const [apiKey, setApiKey] = useState("");
  const [confirmReplace, setConfirmReplace] = useState(false);
  const [loading, setLoading] = useState<"save" | "test" | null>(null);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Connection</span>
          <span className={connected ? "text-emerald-400" : "text-amber-400"}>
            {connected ? "Connected" : "Not configured"}
          </span>
        </div>
        {details.map((item) => (
          <div key={item.label} className="flex items-center justify-between gap-3 text-sm">
            <span className="text-muted-foreground">{item.label}</span>
            <span className="truncate font-mono text-xs">{item.value || "—"}</span>
          </div>
        ))}
        {lastTestAt && (
          <p className="text-xs text-muted-foreground">
            Last test: {new Date(lastTestAt).toLocaleString()} ({lastTestStatus})
          </p>
        )}
        {lastTestError && <p className="text-xs text-red-400">{lastTestError}</p>}
        {extraFields}
        <Input
          type="password"
          placeholder="API key"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
        />
        {connected && (
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={confirmReplace}
              onChange={(event) => setConfirmReplace(event.target.checked)}
            />
            Replace existing credentials
          </label>
        )}
        <div className="flex gap-2">
          <Button
            variant="outline"
            className="flex-1"
            disabled={!apiKey || loading !== null}
            onClick={async () => {
              setLoading("save");
              try {
                await onSave(apiKey, confirmReplace);
                setApiKey("");
                setConfirmReplace(false);
              } finally {
                setLoading(null);
              }
            }}
          >
            {loading === "save" ? "Saving…" : `Save ${title}`}
          </Button>
          <Button
            className="flex-1"
            disabled={loading !== null}
            onClick={async () => {
              setLoading("test");
              try {
                await onTest();
              } finally {
                setLoading(null);
              }
            }}
          >
            {loading === "test" ? "Testing…" : "Test Connection"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function SettingsPage() {
  const { toast } = useToast();
  const [businessId, setLocalBusinessId] = useState(getBusinessId());
  const [retellStatus, setRetellStatus] = useState<RetellIntegrationStatus | null>(null);
  const [calcomStatus, setCalcomStatus] = useState<CalComIntegrationStatus | null>(null);
  const [profile, setProfile] = useState({
    name: "SignalFlow Demo Business",
    phone: "",
    forwarding: "",
    timezone: "America/Chicago",
    hours: "Mon–Fri 8:00–17:00",
  });

  useEffect(() => {
    if (!businessId) return;
    api.retellStatus(businessId).then(setRetellStatus).catch(() => setRetellStatus(null));
    api.calcomStatus(businessId).then(setCalcomStatus).catch(() => setCalcomStatus(null));
  }, [businessId]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Business profile, transfer numbers, and provider configuration for this workspace."
      />

      <Tabs defaultValue="business">
        <TabsList>
          <TabsTrigger value="business">Business</TabsTrigger>
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="security">API & users</TabsTrigger>
        </TabsList>

        <TabsContent value="business" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Business profile</CardTitle>
              <CardDescription>Workspace identity used by the dashboard in this MVP phase.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-2 sm:col-span-2">
                <Label htmlFor="biz-id">Business ID</Label>
                <div className="flex gap-2">
                  <Input
                    id="biz-id"
                    value={businessId}
                    onChange={(event) => setLocalBusinessId(event.target.value)}
                    placeholder="UUID from POST /api/businesses"
                  />
                  <Button
                    onClick={() => {
                      setBusinessId(businessId.trim());
                      toast({ title: "Business ID saved", description: "Reload the page to refresh tenant data." });
                    }}
                  >
                    Save
                  </Button>
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="biz-name">Name</Label>
                <Input
                  id="biz-name"
                  value={profile.name}
                  onChange={(event) => setProfile((current) => ({ ...current, name: event.target.value }))}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="biz-tz">Timezone</Label>
                <Input
                  id="biz-tz"
                  value={profile.timezone}
                  onChange={(event) => setProfile((current) => ({ ...current, timezone: event.target.value }))}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="biz-phone">Primary phone</Label>
                <Input
                  id="biz-phone"
                  value={profile.phone}
                  onChange={(event) => setProfile((current) => ({ ...current, phone: event.target.value }))}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="biz-forward">Transfer number</Label>
                <Input
                  id="biz-forward"
                  value={profile.forwarding}
                  onChange={(event) => setProfile((current) => ({ ...current, forwarding: event.target.value }))}
                />
              </div>
              <div className="grid gap-2 sm:col-span-2">
                <Label htmlFor="biz-hours">Business hours</Label>
                <Textarea
                  id="biz-hours"
                  value={profile.hours}
                  onChange={(event) => setProfile((current) => ({ ...current, hours: event.target.value }))}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="providers" className="grid gap-4 lg:grid-cols-2">
          <IntegrationCard
            title="Retell AI"
            description="Voice agent webhooks and live call orchestration."
            businessId={businessId}
            connected={Boolean(retellStatus?.connected)}
            lastTestAt={retellStatus?.last_test_at}
            lastTestStatus={retellStatus?.last_test_status}
            lastTestError={retellStatus?.last_test_error}
            details={[
              { label: "Mode", value: retellStatus?.mode },
              { label: "Agent name", value: retellStatus?.agent_name },
              { label: "Agent ID", value: retellStatus?.agent_id_masked },
              { label: "Webhook URL", value: retellStatus?.webhook_url },
            ]}
            onSave={async (apiKey, confirmReplace) => {
              const status = await api.saveRetell(businessId, {
                api_key: apiKey,
                agent_name: "Universal_Demo",
                confirm_replace: confirmReplace,
              });
              setRetellStatus(status);
              toast({ title: "Retell credentials saved" });
            }}
            onTest={async () => {
              const result = await api.testRetell(businessId);
              setRetellStatus(await api.retellStatus(businessId));
              toast({
                title: result.ok ? "Retell connection OK" : "Retell test failed",
                description: result.message ?? undefined,
              });
            }}
          />
          <IntegrationCard
            title="Cal.com"
            description="Availability lookup and appointment booking."
            businessId={businessId}
            connected={Boolean(calcomStatus?.connected)}
            lastTestAt={calcomStatus?.last_test_at}
            lastTestStatus={calcomStatus?.last_test_status}
            lastTestError={calcomStatus?.last_test_error}
            details={[
              { label: "Mode", value: calcomStatus?.mode },
              { label: "Event type", value: calcomStatus?.event_type_name },
              { label: "Event type ID", value: calcomStatus?.event_type_id },
              { label: "Slug", value: calcomStatus?.event_type_slug },
              { label: "Username", value: calcomStatus?.username },
            ]}
            onSave={async (apiKey, confirmReplace) => {
              const status = await api.saveCalcom(businessId, { api_key: apiKey, confirm_replace: confirmReplace });
              setCalcomStatus(status);
              toast({ title: "Cal.com credentials saved" });
            }}
            onTest={async () => {
              const result = await api.testCalcom(businessId);
              setCalcomStatus(await api.calcomStatus(businessId));
              toast({
                title: result.ok ? "Cal.com connection OK" : "Cal.com test failed",
                description: result.message ?? undefined,
              });
            }}
          />
        </TabsContent>

        <TabsContent value="security" className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Owner API token</CardTitle>
              <CardDescription>
                Integration settings use Bearer JWT (preferred) or <code>X-Owner-Token</code> from{" "}
                <code>VITE_OWNER_API_TOKEN</code>. Dashboard API calls send the same auth headers. API keys are
                never stored in the browser.
              </CardDescription>
            </CardHeader>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
