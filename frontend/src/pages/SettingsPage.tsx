import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  api,
  getBusinessId,
  setBusinessId,
  type CalComIntegrationStatus,
  type Invitation,
  type RetellIntegrationStatus,
  type SessionUser,
} from "@/api/client";
import { useAuth } from "@/auth/AuthProvider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/layout/PageHeader";
import { useToast } from "@/hooks/toast-context";
import type { AuditEvent } from "@/types";

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

export function SettingsPage({ businessId: initialBusinessId }: { businessId: string }) {
  const { toast } = useToast();
  const [businessId, setLocalBusinessId] = useState(initialBusinessId || getBusinessId());
  const [retellStatus, setRetellStatus] = useState<RetellIntegrationStatus | null>(null);
  const [calcomStatus, setCalcomStatus] = useState<CalComIntegrationStatus | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [auditQuery, setAuditQuery] = useState("");
  const [auditSource, setAuditSource] = useState<"all" | "auth" | "integration">("all");
  const [exporting, setExporting] = useState<string | null>(null);
  const [profile, setProfile] = useState({
    name: "Verideum Demo Business",
    phone: "",
    forwarding: "",
    timezone: "America/Chicago",
    hours: "Mon–Fri 8:00–17:00",
  });

  const loadAudit = () => {
    if (!businessId) return;
    api
      .auditEvents(businessId, {
        q: auditQuery || undefined,
        source: auditSource === "all" ? undefined : auditSource,
        limit: 100,
      })
      .then(setAuditEvents)
      .catch(() => setAuditEvents([]));
  };

  useEffect(() => {
    if (!businessId) return;
    api.retellStatus(businessId).then(setRetellStatus).catch(() => setRetellStatus(null));
    api.calcomStatus(businessId).then(setCalcomStatus).catch(() => setCalcomStatus(null));
    loadAudit();
  }, [businessId]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Business profile, transfer numbers, and provider configuration for this workspace."
      />
      <p className="text-sm text-muted-foreground">
        New workspace?{" "}
        <Link className="text-primary underline-offset-4 hover:underline" to="/onboarding">
          Open first-run setup
        </Link>
      </p>

      <Tabs defaultValue="business">
        <TabsList>
          <TabsTrigger value="business">Business</TabsTrigger>
          <TabsTrigger value="hours">Hours</TabsTrigger><TabsTrigger value="transfer">Transfer</TabsTrigger>
          <TabsTrigger value="providers">Integrations</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="security">Security & API keys</TabsTrigger>
          <TabsTrigger value="exports">Exports</TabsTrigger>
          <TabsTrigger value="audit">Audit log</TabsTrigger>
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
        <TabsContent value="hours"><Card><CardHeader><CardTitle>Business hours</CardTitle><CardDescription>Set the hours your receptionist uses to qualify urgent transfers.</CardDescription></CardHeader><CardContent><Textarea value={profile.hours} onChange={(event) => setProfile((current) => ({ ...current, hours: event.target.value }))} /></CardContent></Card></TabsContent>
        <TabsContent value="transfer"><Card><CardHeader><CardTitle>Call transfer</CardTitle><CardDescription>Local preference until transfer policy is managed through Voice Agent.</CardDescription></CardHeader><CardContent><Input value={profile.forwarding} onChange={(event) => setProfile((current) => ({ ...current, forwarding: event.target.value }))} placeholder="+1 555…" /></CardContent></Card></TabsContent>

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
              <CardTitle>Session security</CardTitle>
              <CardDescription>
                Access and refresh tokens are stored in HttpOnly cookies. The browser never persists JWTs in
                localStorage. Sessions refresh automatically and revoke on sign-out or password reset.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Permissions</CardTitle>
              <CardDescription>
                Roles: <strong>owner</strong> (full access), <strong>admin</strong> (users, integrations, settings),{" "}
                <strong>member</strong> (read CRM/calls). Invite teammates from the Users tab.
              </CardDescription>
            </CardHeader>
          </Card>
        </TabsContent>
        <TabsContent value="users">
          <UsersInvitesPanel />
        </TabsContent>
        <TabsContent value="exports">
          <Card>
            <CardHeader>
              <CardTitle>CSV exports</CardTitle>
              <CardDescription>Download customer, appointment, and call data for this workspace (owner/admin).</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {(
                [
                  ["customers", "Export customers"],
                  ["appointments", "Export appointments"],
                  ["calls", "Export calls"],
                ] as const
              ).map(([kind, label]) => (
                <Button
                  key={kind}
                  variant="outline"
                  disabled={Boolean(exporting)}
                  onClick={async () => {
                    setExporting(kind);
                    try {
                      await api.exportCsv(businessId, kind);
                      toast({ title: `${label} ready` });
                    } catch (err) {
                      toast({
                        title: "Export failed",
                        description: err instanceof Error ? err.message : "Error",
                        variant: "danger",
                      });
                    } finally {
                      setExporting(null);
                    }
                  }}
                >
                  {exporting === kind ? "Exporting…" : label}
                </Button>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit">
          <Card>
            <CardHeader>
              <CardTitle>Audit log</CardTitle>
              <CardDescription>Searchable security and integration activity.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Input
                  placeholder="Search action, status, detail…"
                  value={auditQuery}
                  onChange={(event) => setAuditQuery(event.target.value)}
                  className="max-w-sm"
                />
                <select
                  className="rounded-md border border-input bg-background px-3 text-sm"
                  value={auditSource}
                  onChange={(event) =>
                    setAuditSource(event.target.value as "all" | "auth" | "integration")
                  }
                >
                  <option value="all">All sources</option>
                  <option value="auth">Auth</option>
                  <option value="integration">Integration</option>
                </select>
                <Button variant="outline" onClick={loadAudit}>
                  Search
                </Button>
              </div>
              {auditEvents.length ? (
                auditEvents.map((event) => (
                  <div
                    key={event.id}
                    className="flex justify-between gap-4 border-b border-border pb-3 text-sm"
                  >
                    <div>
                      <p className="font-medium">{event.action}</p>
                      <p className="text-muted-foreground">
                        {event.detail || event.provider || event.source}
                      </p>
                    </div>
                    <div className="text-right text-muted-foreground">
                      {event.status}
                      <br />
                      {new Date(event.created_at).toLocaleString()}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No audit events available.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function UsersInvitesPanel() {
  const { toast } = useToast();
  const { can } = useAuth();
  const [users, setUsers] = useState<SessionUser[]>([]);
  const [invites, setInvites] = useState<Invitation[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");
  const [inviteLink, setInviteLink] = useState("");
  const [loading, setLoading] = useState(false);

  const reload = async () => {
    const [nextUsers, nextInvites] = await Promise.all([api.listUsers(), api.listInvitations()]);
    setUsers(nextUsers);
    setInvites(nextInvites);
  };

  useEffect(() => {
    if (!can("users:read") && !can("*")) return;
    void reload().catch(() => {
      setUsers([]);
      setInvites([]);
    });
  }, [can]);

  if (!can("users:read") && !can("*")) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
          <CardDescription>You need admin access to manage users and invitations.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Workspace users</CardTitle>
          <CardDescription>People who can access this business.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {users.map((user) => (
            <div key={user.id} className="flex items-center justify-between gap-3 border-b border-border pb-3 text-sm">
              <div>
                <p className="font-medium">{user.name}</p>
                <p className="text-muted-foreground">{user.email}</p>
              </div>
              <span className="capitalize text-muted-foreground">{user.role}</span>
            </div>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Invitations</CardTitle>
          <CardDescription>Invite admins or members by email.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-2">
            <Label htmlFor="invite-email">Email</Label>
            <Input id="invite-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="invite-role">Role</Label>
            <select
              id="invite-role"
              className="h-10 rounded-xl border border-input bg-card px-3 text-sm"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <Button
            disabled={loading || !email}
            onClick={async () => {
              setLoading(true);
              try {
                const invite = await api.createInvitation({ email, role });
                setInviteLink(
                  invite.invite_token
                    ? `${window.location.origin}/accept-invite?token=${encodeURIComponent(invite.invite_token)}`
                    : "",
                );
                setEmail("");
                await reload();
                toast({ title: "Invitation created" });
              } catch (err) {
                toast({
                  title: "Invite failed",
                  description: err instanceof Error ? err.message : "Unable to invite",
                  variant: "danger",
                });
              } finally {
                setLoading(false);
              }
            }}
          >
            {loading ? "Sending…" : "Create invite"}
          </Button>
          {inviteLink ? <p className="break-all text-xs text-muted-foreground">Invite link: {inviteLink}</p> : null}
          {invites.map((invite) => (
            <div key={invite.id} className="flex justify-between gap-3 border-b border-border pb-3 text-sm">
              <div>
                <p className="font-medium">{invite.email}</p>
                <p className="text-muted-foreground capitalize">{invite.role}</p>
              </div>
              <span className="text-muted-foreground">{invite.accepted_at ? "Accepted" : "Pending"}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
